"""Structural walker for the General Message bytecode used by Fermion."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path


class GMError(ValueError):
    """Raised when a General Message container or instruction is malformed."""


@dataclass(frozen=True)
class GMExpression:
    end: int
    literal_value: int | None = None
    literal_offset: int | None = None
    literal_width: int | None = None


@dataclass(frozen=True)
class GMRelocation:
    instruction_offset: int
    field_offset: int
    target: int
    purpose: str
    required_local: bool


@dataclass(frozen=True)
class GMInstruction:
    offset: int
    end: int
    opcode: int
    relocations: tuple[GMRelocation, ...] = ()


@dataclass(frozen=True)
class GMText:
    offset: int
    end: int
    mode: int
    payload: bytes
    text: str | None

    @property
    def ascii_text(self) -> str | None:
        return self.text if self.mode == 2 else None


@dataclass(frozen=True)
class GMSpeaker:
    id: str
    source: str
    default_name: str | None = None


@dataclass(frozen=True)
class GMAttributedText:
    record: GMText
    speaker: GMSpeaker | None


@dataclass(frozen=True)
class GMTransition:
    offset: int
    opcode: int
    target: str

    @property
    def kind(self) -> str:
        return "replace" if self.opcode == 0x6D else "nested"


@dataclass(frozen=True)
class GMInterpolation:
    start: int
    end: int
    token: str
    slot: int

    @property
    def marker(self) -> str:
        return f"⟦{self.token}⟧"


@dataclass(frozen=True)
class GMAudit:
    instructions: tuple[GMInstruction, ...]
    relocations: tuple[GMRelocation, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class GMFile:
    data: bytes
    code_start: int
    dictionary: tuple[bytes, ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> GMFile:
        if len(data) < 2:
            raise GMError("GM file is too small")
        code_start = struct.unpack_from("<H", data)[0]
        if code_start < 2 or code_start > len(data):
            raise GMError(f"invalid GM code start: 0x{code_start:04x}")
        if (code_start - 2) % 2:
            raise GMError(f"GM dictionary has odd byte length: {code_start - 2}")
        dictionary = tuple(data[pos : pos + 2] for pos in range(2, code_start, 2))
        return cls(data=data, code_start=code_start, dictionary=dictionary)

    @classmethod
    def from_file(cls, path: Path) -> GMFile:
        return cls.from_bytes(path.read_bytes())

    def audit(self) -> GMAudit:
        instructions: list[GMInstruction] = []
        pos = self.code_start
        while pos < len(self.data):
            instruction = _read_instruction(self.data, pos)
            if instruction.end <= pos:
                raise GMError(f"instruction at 0x{pos:04x} did not advance")
            instructions.append(instruction)
            pos = instruction.end

        boundaries = {instruction.offset for instruction in instructions}
        relocations = tuple(
            relocation
            for instruction in instructions
            for relocation in instruction.relocations
        )
        issues: list[str] = []
        for relocation in relocations:
            is_local = self.code_start <= relocation.target < len(self.data)
            if relocation.required_local and not is_local:
                issues.append(
                    f"0x{relocation.field_offset:04x}: {relocation.purpose} target "
                    f"0x{relocation.target:04x} is outside the MES code"
                )
            elif is_local and relocation.target not in boundaries:
                issues.append(
                    f"0x{relocation.field_offset:04x}: {relocation.purpose} target "
                    f"0x{relocation.target:04x} is not an instruction boundary"
                )
        return GMAudit(tuple(instructions), relocations, tuple(issues))

    def text_records(self) -> tuple[GMText, ...]:
        return tuple(
            GMText(
                offset=instruction.offset,
                end=instruction.end,
                mode=self.data[instruction.offset + 1],
                payload=self.data[instruction.offset + 2 : instruction.end - 1],
                text=_decode_text(
                    self.data[instruction.offset + 1],
                    self.data[instruction.offset + 2 : instruction.end - 1],
                    self.dictionary,
                ),
            )
            for instruction in self.audit().instructions
            if instruction.opcode == 0x4A
        )

    def attributed_text_records(self) -> tuple[GMAttributedText, ...]:
        """Attach only speaker identities encoded in the rendered text stream."""
        instructions = self.audit().instructions
        records = {record.offset: record for record in self.text_records()}
        attributed: list[GMAttributedText] = []
        active_speaker: GMSpeaker | None = None

        for index, instruction in enumerate(instructions):
            if instruction.opcode in {0x00, 0x50}:
                active_speaker = None
                continue
            record = records.get(instruction.offset)
            if record is None:
                continue

            speaker = _inline_speaker(record.text)
            if speaker is None:
                speaker = _dynamic_speaker(self.data, instructions, records, index)
            if speaker is not None:
                active_speaker = speaker
            attributed.append(GMAttributedText(record, speaker or active_speaker))

        return tuple(attributed)

    def transitions(self) -> tuple[GMTransition, ...]:
        """Return literal scenario loads in bytecode order."""
        return tuple(
            GMTransition(
                instruction.offset,
                instruction.opcode,
                _literal_transition_target(self.data, instruction),
            )
            for instruction in self.audit().instructions
            if instruction.opcode in {0x6D, 0x6F}
        )

    def interpolations(self) -> tuple[GMInterpolation, ...]:
        """Return exact customizable-name and terminology render spans."""
        instructions = self.audit().instructions
        found = []
        for copy, render in pairwise(instructions):
            interpolation = _interpolation_at(self.data, copy, render)
            if interpolation is not None:
                found.append(interpolation)
        return tuple(found)


_INLINE_SPEAKER = re.compile(r"^【([^】]+)】")

_NAME_SLOT_SPEAKERS = {
    0x03E8: GMSpeaker("name-slot:mother", "name-slot", "由貴"),
    0x03F6: GMSpeaker("name-slot:older-sister", "name-slot", "瑠璃"),
    0x0404: GMSpeaker("name-slot:dear-person", "name-slot", "加奈子"),
    0x0412: GMSpeaker("name-slot:friend-1", "name-slot", "陽子"),
    0x0420: GMSpeaker("name-slot:friend-2", "name-slot", "弘子"),
}

_INTERPOLATION_TOKENS = {
    0x03E8: "name:mother",
    0x03F6: "name:older-sister",
    0x0404: "name:dear-person",
    0x0412: "name:friend-1",
    0x0420: "name:friend-2",
    0x042E: "term:slot-1",
    0x043E: "term:slot-2",
}


def interpolation_token_for_slot(slot: int) -> str | None:
    """Return the authoring token rendered from a known runtime string slot."""
    return _INTERPOLATION_TOKENS.get(slot)


def _inline_speaker(text: str | None) -> GMSpeaker | None:
    if text is None:
        return None
    match = _INLINE_SPEAKER.match(text)
    if match is None:
        return None
    speaker = match.group(1)
    return GMSpeaker(speaker, "inline-label", speaker)


def _dynamic_speaker(
    data: bytes,
    instructions: tuple[GMInstruction, ...],
    records: dict[int, GMText],
    index: int,
) -> GMSpeaker | None:
    """Recognize Fermion's rendered `【<custom name>】` prefix sequence."""
    record = records[instructions[index].offset]
    if record.text is None or not record.text.startswith("【") or "】" in record.text:
        return None
    if index + 3 >= len(instructions):
        return None
    copy, render, suffix = instructions[index + 1 : index + 4]
    if (copy.opcode, render.opcode, suffix.opcode) != (0x45, 0x4B, 0x4A):
        return None

    interpolation = _interpolation_at(data, copy, render)
    suffix_record = records.get(suffix.offset)
    if (
        interpolation is None
        or suffix_record is None
        or suffix_record.text is None
        or not suffix_record.text.startswith("】")
    ):
        return None
    return _NAME_SLOT_SPEAKERS.get(interpolation.slot)


def _interpolation_at(
    data: bytes, copy: GMInstruction, render: GMInstruction
) -> GMInterpolation | None:
    if copy.opcode != 0x45 or render.opcode != 0x4B:
        return None
    copy_data = data[copy.offset : copy.end]
    render_data = data[render.offset : render.end]
    if (
        len(copy_data) != 9
        or copy_data[:6] != b"\x45\x0e\xe0\x00\xff\x0c"
        or copy_data[8] != 0
        or render_data != b"\x4b\x0e\xe0\x00\x00\x00"
    ):
        return None
    slot = int.from_bytes(copy_data[6:8], "little")
    token = interpolation_token_for_slot(slot)
    if token is None:
        return None
    return GMInterpolation(copy.offset, render.end, token, slot)


def _literal_transition_target(data: bytes, instruction: GMInstruction) -> str:
    pos = instruction.offset + 1
    if pos >= instruction.end or data[pos] != 0x11:
        raise _error(pos, f"opcode 0x{instruction.opcode:02x} target is not a literal string")
    end = data.find(b"\0", pos + 1, instruction.end)
    if end < 0:
        raise _error(pos, f"opcode 0x{instruction.opcode:02x} target is unterminated")
    try:
        target = data[pos + 1 : end].decode("ascii")
    except UnicodeDecodeError as error:
        raise _error(pos + 1, f"opcode 0x{instruction.opcode:02x} target is not ASCII") from error
    if not target:
        raise _error(pos + 1, f"opcode 0x{instruction.opcode:02x} target is empty")
    return target


def _decode_text(mode: int, payload: bytes, dictionary: tuple[bytes, ...]) -> str | None:
    if mode == 2:
        if not all(byte == 0x04 or 0x20 <= byte <= 0x7E for byte in payload):
            return None
        return payload.replace(b"\x04", b"\n").decode("ascii")

    decoded: list[str] = []
    pos = 0
    while pos < len(payload):
        byte = payload[pos]
        if byte == 0x04:
            decoded.append("\n")
            pos += 1
            continue

        if 0x18 <= byte <= 0x7F:
            index = byte - 0x18
            pos += 1
        elif 0xA0 <= byte <= 0xDF:
            index = byte - 0x38
            pos += 1
        else:
            if pos + 1 >= len(payload):
                return None
            pair = payload[pos : pos + 2]
            pos += 2
            char = _decode_sjis_pair(pair)
            if char is None:
                return None
            decoded.append(char)
            continue

        if index >= len(dictionary):
            return None
        char = _decode_sjis_pair(dictionary[index])
        if char is None:
            return None
        decoded.append(char)

    return "".join(decoded)


def _decode_sjis_pair(pair: bytes) -> str | None:
    if len(pair) == 2:
        lead, trail = pair
        row_offset = int(trail > 0x9E)
        if 0x81 <= lead <= 0x9F:
            row = row_offset + lead * 2 - 257
        elif 0xE0 <= lead <= 0xEF:
            row = row_offset + lead * 2 - 385
        else:
            row = 0

        if row % 2 == 1 and 0x40 <= trail <= 0x7E:
            column = trail - 63
        elif row % 2 == 1 and 0x80 <= trail <= 0x9E:
            column = trail - 64
        elif row and row % 2 == 0 and 0x9F <= trail <= 0xFC:
            column = trail - 158
        else:
            column = 0

        if row == 12 and 4 <= column <= 79:
            return chr(0x2500 + column - 4)

    try:
        return pair.decode("cp932")
    except UnicodeDecodeError:
        return None


def _error(pos: int, message: str) -> GMError:
    return GMError(f"0x{pos:04x}: {message}")


def _require(data: bytes, pos: int, size: int, what: str) -> None:
    if pos < 0 or pos + size > len(data):
        raise _error(pos, f"truncated {what}")


def _u16(data: bytes, pos: int) -> int:
    _require(data, pos, 2, "16-bit operand")
    return struct.unpack_from("<H", data, pos)[0]


def _expect_zero(data: bytes, pos: int, what: str) -> int:
    _require(data, pos, 1, what)
    if data[pos] != 0:
        raise _error(pos, f"expected zero {what}, found 0x{data[pos]:02x}")
    return pos + 1


def _read_reference(data: bytes, pos: int) -> int:
    _require(data, pos, 3, "reference")
    token = data[pos]
    if token < 5:
        raise _error(pos, f"invalid reference token 0x{token:02x}")
    pos += 3
    if token <= 0x0A:
        pos = _read_expression(data, pos).end
    return pos


def _read_operand(data: bytes, pos: int, *, initial: bool) -> tuple[int, int | None, int | None]:
    _require(data, pos, 1, "expression operand")
    token = data[pos]
    if initial and token == 0x32:
        _require(data, pos, 5, "random-range operand")
        return pos + 5, None, None
    if 1 <= token <= 4:
        _require(data, pos + 1, token, "literal operand")
        value = int.from_bytes(data[pos + 1 : pos + 1 + token], "little")
        return pos + 1 + token, value, token
    if token >= 5:
        return _read_reference(data, pos), None, None
    raise _error(pos, "zero is not an expression operand")


def _read_expression(data: bytes, pos: int) -> GMExpression:
    start = pos
    _require(data, pos, 1, "expression")
    if data[pos] == 0:
        return GMExpression(pos + 1)

    pos, literal_value, literal_width = _read_operand(data, pos, initial=True)
    pure_literal = literal_value is not None
    literal_offset = start + 1 if pure_literal else None

    while True:
        _require(data, pos, 1, "expression terminator")
        token = data[pos]
        if token == 0:
            return GMExpression(
                pos + 1,
                literal_value if pure_literal else None,
                literal_offset if pure_literal else None,
                literal_width if pure_literal else None,
            )
        pure_literal = False
        if token >= 0x20:
            pos += 1
        else:
            pos, _, _ = _read_operand(data, pos, initial=False)


def _read_params(data: bytes, pos: int) -> int:
    while True:
        _require(data, pos, 1, "parameter list")
        token = data[pos]
        if token == 0:
            return pos + 1
        if token == 0x11:
            end = data.find(b"\0", pos + 1)
            if end < 0:
                raise _error(pos, "unterminated literal-string parameter")
            pos = end + 1
        elif token == 0x0F:
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after reference parameter")
        else:
            pos = _read_expression(data, pos).end


def _read_reference_list(data: bytes, pos: int) -> int:
    while True:
        _require(data, pos, 1, "reference list")
        if data[pos] == 0:
            return pos + 1
        pos = _read_reference(data, pos)
        pos = _expect_zero(data, pos, "after reference")


def _relocation(
    data: bytes,
    instruction_offset: int,
    field_offset: int,
    purpose: str,
    *,
    required_local: bool,
) -> GMRelocation:
    return GMRelocation(
        instruction_offset=instruction_offset,
        field_offset=field_offset,
        target=_u16(data, field_offset),
        purpose=purpose,
        required_local=required_local,
    )


def _read_assignment(data: bytes, pos: int) -> int:
    pos = _read_reference(data, pos)
    while True:
        if data[pos] == 0x0E:
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after string reference")
        else:
            pos = _read_expression(data, pos).end

        while data[pos] == 0x31:
            _require(data, pos, 2, "assignment stride")
            pos += 2
        if data[pos] == 0:
            return pos + 1
        if data[pos] == 0x30:
            pos = _read_reference(data, pos + 1)
            return _expect_zero(data, pos, "after assignment range")


def _read_3a(
    data: bytes, instruction_offset: int, pos: int
) -> tuple[int, tuple[GMRelocation, ...]]:
    _require(data, pos, 1, "opcode 0x3a subtype")
    subtype = data[pos]
    pos += 1
    relocations: list[GMRelocation] = []

    if subtype == 1:
        selector = _read_expression(data, pos)
        pos = selector.end
        pos = _read_expression(data, pos).end
        if selector.literal_value == 1:
            for field in range(6):
                value = _read_expression(data, pos)
                if field == 4 and value.literal_offset is not None and value.literal_width == 2:
                    relocations.append(
                        GMRelocation(
                            instruction_offset,
                            value.literal_offset,
                            value.literal_value,
                            "0x3a callback",
                            True,
                        )
                    )
                pos = value.end
    elif subtype in {2, 3, 6}:
        pos = _read_reference(data, pos)
        pos = _expect_zero(data, pos, "after 0x3a reference")
    elif subtype == 4:
        for _ in range(9):
            pos = _read_expression(data, pos).end
    elif subtype == 5:
        for _ in range(3):
            pos = _read_expression(data, pos).end
        for _ in range(2):
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after 0x3a reference")
    elif subtype in {7, 8, 9}:
        pos = _read_expression(data, pos).end
    elif subtype == 10:
        selector = _read_expression(data, pos)
        pos = selector.end
        count = 7 if selector.literal_value == 0 else 6
        for _ in range(count):
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after 0x3a subtype 10 reference")
        if selector.literal_value is None and data[pos] != 0:
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after 0x3a subtype 10 reference")
    elif subtype not in {11, 12, 13}:
        raise _error(pos - 1, f"unknown opcode 0x3a subtype 0x{subtype:02x}")

    pos = _expect_zero(data, pos, "after opcode 0x3a")
    return pos, tuple(relocations)


def _read_instruction(data: bytes, start: int) -> GMInstruction:
    _require(data, start, 1, "opcode")
    opcode = data[start]
    pos = start + 1
    relocations: list[GMRelocation] = []

    if opcode == 0:
        return GMInstruction(start, pos, opcode)
    if not 0x30 <= opcode <= 0x7F:
        raise _error(start, f"invalid GM opcode 0x{opcode:02x}")

    no_operands = {
        0x30, 0x36, 0x38, 0x3D, 0x41, 0x42, 0x50, 0x56, 0x57,
        0x66, 0x69, 0x70, 0x7C, 0x7F,
    }
    generic_params = {
        0x46, 0x47, 0x48, 0x49, 0x4C, 0x4D, 0x4E, 0x4F,
        0x51, 0x52, 0x53, 0x54, 0x55, 0x58, 0x59, 0x5A,
        0x5B, 0x5C, 0x5D, 0x5E, 0x5F, 0x60, 0x61, 0x63,
        0x67, 0x6C, 0x6D, 0x6E, 0x6F, 0x74, 0x75, 0x78,
        0x7A, 0x7D,
    }

    if opcode in no_operands:
        pass
    elif opcode == 0x31:
        _require(data, pos, 4, "opcode 0x31 operands")
        relocations.append(_relocation(data, start, pos + 2, "loop target", required_local=True))
        pos = _read_expression(data, pos + 4).end
    elif opcode == 0x32:
        _require(data, pos, 4, "opcode 0x32 operands")
        relocations.append(_relocation(data, start, pos + 2, "loop target", required_local=True))
        pos += 4
    elif opcode in {0x33, 0x34}:
        relocations.append(_relocation(data, start, pos, "control target", required_local=True))
        pos = _read_expression(data, pos + 2).end
    elif opcode == 0x35:
        relocations.append(_relocation(data, start, pos, "control target", required_local=True))
        pos += 2
        while data[pos] != 0:
            pos = _read_expression(data, pos).end
        pos += 1
    elif opcode == 0x37:
        pos = _read_expression(data, pos).end
    elif opcode in {0x39, 0x3F, 0x40}:
        _require(data, pos, 4, f"opcode 0x{opcode:02x} targets")
        relocations.append(_relocation(data, start, pos, "fallthrough target", required_local=True))
        relocations.append(
            _relocation(data, start, pos + 2, "call target", required_local=False)
        )
        pos = _read_expression(data, pos + 4).end
    elif opcode == 0x3A:
        pos, found = _read_3a(data, start, pos)
        relocations.extend(found)
    elif opcode == 0x3B:
        pos = _read_expression(data, pos).end
        pos = _expect_zero(data, pos, "after opcode 0x3b")
    elif opcode == 0x3C:
        _require(data, pos, 5, "opcode 0x3c payload")
        pos += 5
    elif opcode == 0x3E:
        _require(data, pos, 1, "opcode 0x3e mode")
        pos = _expect_zero(data, pos + 1, "after opcode 0x3e")
    elif opcode == 0x43:
        pos = _read_assignment(data, pos)
    elif opcode == 0x44:
        pos = _read_reference(data, pos)
        field_offset = pos
        target = _u16(data, field_offset)
        pos += 2
        if data[pos] == 0x0F:
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after opcode 0x44 reference")
        else:
            relocations.append(
                GMRelocation(start, field_offset, target, "inline-data skip", True)
            )
            if target <= pos or target > len(data):
                raise _error(field_offset, f"invalid opcode 0x44 skip target 0x{target:04x}")
            pos = target
    elif opcode == 0x45:
        pos = _read_reference(data, pos)
        _require(data, pos, 2, "opcode 0x45 source")
        if data[pos + 1] >= 5:
            pos = _read_reference(data, pos + 1)
            pos = _expect_zero(data, pos, "after opcode 0x45 reference")
        else:
            end = data.find(b"\0", pos)
            if end < 0:
                raise _error(pos, "unterminated opcode 0x45 inline source")
            _require(data, end + 1, 1, "opcode 0x45 trailing byte")
            pos = end + 2
    elif opcode == 0x4A:
        _require(data, pos, 1, "opcode 0x4a mode")
        if data[pos] not in {1, 2}:
            raise _error(pos, f"invalid opcode 0x4a mode {data[pos]}")
        end = data.find(b"\0", pos + 1)
        if end < 0:
            raise _error(pos, "unterminated opcode 0x4a text")
        pos = end + 1
    elif opcode == 0x4B:
        pos = _read_reference(data, pos)
        _require(data, pos, 2, "opcode 0x4b terminators")
        pos += 2
    elif opcode in generic_params:
        pos = _read_params(data, pos)
    elif opcode == 0x62:
        pos = _expect_zero(data, pos, "after opcode 0x62")
    elif opcode == 0x64:
        pos = _read_reference(data, pos)
        pos = _expect_zero(data, pos, "after opcode 0x64 reference")
        pos = _expect_zero(data, pos, "after opcode 0x64")
    elif opcode in {0x65, 0x68, 0x6A}:
        pos = _read_reference_list(data, pos)
    elif opcode == 0x6B:
        selector = _read_expression(data, pos)
        pos = selector.end
        if selector.literal_value in {0, 1, 7, 8}:
            pos = _expect_zero(data, pos, "after opcode 0x6b")
        elif selector.literal_value in {2, 3}:
            pos = _read_reference_list(data, pos)
        elif selector.literal_value in {4, 5, 6, 9}:
            pos = _read_params(data, pos)
        else:
            raise _error(start, "opcode 0x6b selector is not a literal from 0 through 9")
    elif opcode == 0x71:
        selector = _read_expression(data, pos)
        pos = selector.end
        if selector.literal_value == 0:
            pos = _read_reference(data, pos)
            pos = _expect_zero(data, pos, "after opcode 0x71 reference")
            pos = _expect_zero(data, pos, "after opcode 0x71")
        elif selector.literal_value == 1:
            pos = _read_expression(data, pos).end
            pos = _expect_zero(data, pos, "after opcode 0x71")
        elif selector.literal_value == 2:
            pos = _read_params(data, pos)
        else:
            raise _error(start, "opcode 0x71 selector is not a literal 0, 1, or 2")
    elif opcode in {0x72, 0x73, 0x7E}:
        pos = _read_expression(data, pos).end
        pos = _read_reference(data, pos)
        pos = _expect_zero(data, pos, "after reference")
        pos = _read_expression(data, pos).end
        pos = _expect_zero(data, pos, f"after opcode 0x{opcode:02x}")
    elif opcode in {0x76, 0x77}:
        pos = _read_expression(data, pos).end
        pos = _read_expression(data, pos).end
        pos = _expect_zero(data, pos, f"after opcode 0x{opcode:02x}")
    elif opcode == 0x79:
        pos = _read_expression(data, pos).end
        pos = _read_reference_list(data, pos)
    elif opcode == 0x7B:
        pos = _read_reference(data, pos)
        pos = _expect_zero(data, pos, "after opcode 0x7b reference")
        pos = _read_params(data, pos)
    else:
        raise _error(start, f"unsupported GM opcode 0x{opcode:02x}")

    return GMInstruction(start, pos, opcode, tuple(relocations))
