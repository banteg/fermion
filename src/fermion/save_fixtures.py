"""Portable sparse save-slot fixtures for Fermion HDI images."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fermion.hdi import HDIImage

_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SCENARIO_OFFSET = 0x1B10


class SaveFixtureError(ValueError):
    """Raised when a save fixture is malformed or does not match its source."""


@dataclass(frozen=True)
class SaveHunk:
    offset: int
    before: bytes
    data: bytes


@dataclass(frozen=True)
class SaveFixture:
    name: str
    description: str
    scenario: str
    template_path: PurePosixPath
    template_sha256: str
    target_path: PurePosixPath
    target_sha256: str
    result_sha256: str
    hunks: tuple[SaveHunk, ...]

    def build_slot(self, template: bytes) -> bytes:
        """Apply the sparse delta to its hash-pinned template slot."""
        actual = hashlib.sha256(template).hexdigest()
        if actual != self.template_sha256:
            raise SaveFixtureError(
                f"fixture {self.name!r} expects template SHA-256 "
                f"{self.template_sha256}, got {actual}"
            )

        result = bytearray(template)
        for hunk in self.hunks:
            end = hunk.offset + len(hunk.data)
            if end > len(result):
                raise SaveFixtureError(
                    f"fixture {self.name!r} hunk at 0x{hunk.offset:x} exceeds "
                    f"the {len(result)}-byte template"
                )
            actual_before = bytes(result[hunk.offset:end])
            if actual_before != hunk.before:
                raise SaveFixtureError(
                    f"fixture {self.name!r} hunk at 0x{hunk.offset:x} expects "
                    f"{hunk.before.hex()}, got {actual_before.hex()}"
                )
            result[hunk.offset:end] = hunk.data

        built = bytes(result)
        actual = hashlib.sha256(built).hexdigest()
        if actual != self.result_sha256:
            raise SaveFixtureError(
                f"fixture {self.name!r} produced SHA-256 {actual}, "
                f"expected {self.result_sha256}"
            )
        return built

    def apply(self, image: HDIImage) -> HDIImage:
        """Install the fixture into a copied image, refusing a non-pristine target slot."""
        template = image.read_file(self.template_path)
        target = image.read_file(self.target_path)
        actual_target = hashlib.sha256(target).hexdigest()
        if actual_target != self.target_sha256:
            raise SaveFixtureError(
                f"fixture {self.name!r} expects target SHA-256 "
                f"{self.target_sha256}, got {actual_target}"
            )
        built = self.build_slot(template)
        if len(built) != len(target):
            raise SaveFixtureError(
                f"fixture {self.name!r} builds {len(built)} bytes for a "
                f"{len(target)}-byte target slot"
            )
        return image.replace_files({self.target_path: built})


@dataclass(frozen=True)
class SaveCapture:
    """A fixture recovered from a live global segment in an emulator state."""

    fixture: SaveFixture
    state_offset: int

    @property
    def changed_bytes(self) -> int:
        return sum(len(hunk.data) for hunk in self.fixture.hunks)


@dataclass(frozen=True)
class SaveFixtureManifest:
    fixtures: tuple[SaveFixture, ...]

    @classmethod
    def from_file(cls, path: Path) -> SaveFixtureManifest:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise SaveFixtureError(f"cannot read save fixture manifest {path}: {error}") from error
        if data.get("version") != 1:
            raise SaveFixtureError("save fixture manifest version must be 1")
        raw_fixtures = data.get("fixtures")
        if not isinstance(raw_fixtures, list) or not raw_fixtures:
            raise SaveFixtureError(
                "save fixture manifest must contain at least one [[fixtures]] table"
            )
        fixtures = tuple(
            _parse_fixture(value, index) for index, value in enumerate(raw_fixtures, 1)
        )
        names = [fixture.name for fixture in fixtures]
        if len(names) != len(set(names)):
            raise SaveFixtureError("save fixture manifest contains duplicate fixture names")
        return cls(fixtures)

    def fixture(self, name: str) -> SaveFixture:
        for fixture in self.fixtures:
            if fixture.name == name:
                return fixture
        choices = ", ".join(fixture.name for fixture in self.fixtures)
        raise SaveFixtureError(f"unknown save fixture {name!r}; choose one of: {choices}")


def write_fixture_hdi(
    fixture: SaveFixture,
    image_path: Path,
    output_path: Path,
) -> HDIImage:
    """Apply one sparse fixture while preserving the source image."""
    if output_path.resolve() == image_path.resolve():
        raise SaveFixtureError("output must differ from the input image")
    if output_path.exists():
        raise SaveFixtureError(f"output already exists: {output_path}")
    result = fixture.apply(HDIImage.from_file(image_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.data)
    return result


def capture_save_fixture(
    image: HDIImage,
    state: bytes,
    *,
    name: str,
    description: str,
    scenario: str,
    template_path: str | PurePosixPath = "FERM/REG_00",
    target_path: str | PurePosixPath = "FERM/REG_01",
    state_offset: int | None = None,
) -> SaveCapture:
    """Recover a sparse, portable save fixture from an NP2kai state."""
    if not _SAFE_NAME.fullmatch(name):
        raise SaveFixtureError("fixture name must use lowercase letters, digits, and hyphens")
    if not description:
        raise SaveFixtureError("fixture description must not be empty")
    encoded_scenario = _encoded_scenario(scenario)
    template_path = _validated_image_path(template_path, "template_path")
    target_path = _validated_image_path(target_path, "target_path")
    if template_path == target_path:
        raise SaveFixtureError("template_path and target_path must differ")

    template = image.read_file(template_path)
    target = image.read_file(target_path)
    if len(template) != len(target):
        raise SaveFixtureError(
            f"template and target slots differ in size: {len(template)} != {len(target)}"
        )
    if SCENARIO_OFFSET + len(encoded_scenario) + 1 > len(template):
        raise SaveFixtureError(
            f"scenario {scenario!r} does not fit in the {len(template)}-byte slot"
        )

    offset, snapshot = extract_global_segment(
        state,
        template,
        scenario,
        state_offset=state_offset,
    )
    hunks = sparse_hunks(template, snapshot)
    fixture = SaveFixture(
        name=name,
        description=description,
        scenario=scenario,
        template_path=template_path,
        template_sha256=hashlib.sha256(template).hexdigest(),
        target_path=target_path,
        target_sha256=hashlib.sha256(target).hexdigest(),
        result_sha256=hashlib.sha256(snapshot).hexdigest(),
        hunks=hunks,
    )
    fixture.build_slot(template)
    return SaveCapture(fixture, offset)


def extract_global_segment(
    state: bytes,
    template: bytes,
    scenario: str,
    *,
    state_offset: int | None = None,
) -> tuple[int, bytes]:
    """Locate the live slot-sized global segment in a serialized NP2kai state."""
    encoded_scenario = _encoded_scenario(scenario)
    needle = encoded_scenario.lower() + b"\0"

    if state_offset is not None:
        if state_offset < 0 or state_offset + len(template) > len(state):
            raise SaveFixtureError(
                f"state offset 0x{state_offset:x} does not contain a complete "
                f"{len(template)}-byte slot"
            )
        snapshot = state[state_offset : state_offset + len(template)]
        actual = snapshot[SCENARIO_OFFSET : SCENARIO_OFFSET + len(needle)].lower()
        if actual != needle:
            raise SaveFixtureError(
                f"state offset 0x{state_offset:x} does not contain scenario {scenario!r}"
            )
        if snapshot == template:
            raise SaveFixtureError(
                f"state offset 0x{state_offset:x} is an unchanged template copy"
            )
        return state_offset, snapshot

    candidates: dict[bytes, tuple[int, int]] = {}
    lowered_state = state.lower()
    search_from = 0
    exact_copies = 0
    while True:
        found = lowered_state.find(needle, search_from)
        if found < 0:
            break
        search_from = found + 1
        offset = found - SCENARIO_OFFSET
        if offset < 0 or offset + len(template) > len(state):
            continue
        snapshot = state[offset : offset + len(template)]
        changed = sum(before != after for before, after in zip(template, snapshot, strict=True))
        if changed == 0:
            # Save states also contain static disk/template copies. They are not
            # runtime checkpoints, even when their scenario string matches.
            exact_copies += 1
            continue
        if changed > len(template) // 2:
            continue
        previous = candidates.get(snapshot)
        if previous is None or offset < previous[1]:
            candidates[snapshot] = (changed, offset)

    if not candidates:
        detail = f" ({exact_copies} unchanged template copies ignored)" if exact_copies else ""
        raise SaveFixtureError(
            f"could not locate a live {scenario!r} global segment in emulator state{detail}"
        )

    ranked = sorted((changed, offset, snapshot) for snapshot, (changed, offset) in candidates.items())
    best_changed = ranked[0][0]
    equally_close = [candidate for candidate in ranked if candidate[0] == best_changed]
    if len(equally_close) > 1:
        offsets = ", ".join(f"0x{candidate[1]:x}" for candidate in equally_close)
        raise SaveFixtureError(
            f"ambiguous live {scenario!r} global segments with {best_changed} changed bytes "
            f"at {offsets}; pass --state-offset"
        )
    _changed, offset, snapshot = ranked[0]
    return offset, snapshot


def verify_state_scenario(state: bytes, scenario: str, state_offset: int) -> None:
    """Verify the scenario marker in a known live-global state segment."""
    encoded = _encoded_scenario(scenario) + b"\0"
    marker = state_offset + SCENARIO_OFFSET
    if state_offset < 0 or marker + len(encoded) > len(state):
        raise SaveFixtureError(
            f"state offset 0x{state_offset:x} does not contain scenario marker {scenario!r}"
        )
    actual = state[marker : marker + len(encoded)]
    if actual.lower() != encoded.lower():
        display = actual.split(b"\0", 1)[0].decode("ascii", errors="replace")
        raise SaveFixtureError(
            f"state offset 0x{state_offset:x} contains scenario {display!r}, "
            f"expected {scenario!r}"
        )


def sparse_hunks(template: bytes, snapshot: bytes) -> tuple[SaveHunk, ...]:
    """Return maximal contiguous changed ranges between equal-sized slots."""
    if len(template) != len(snapshot):
        raise SaveFixtureError(
            f"template and snapshot differ in size: {len(template)} != {len(snapshot)}"
        )
    hunks: list[SaveHunk] = []
    start: int | None = None
    for offset, (before, after) in enumerate(zip(template, snapshot, strict=True)):
        if before != after and start is None:
            start = offset
        if before == after and start is not None:
            hunks.append(SaveHunk(start, template[start:offset], snapshot[start:offset]))
            start = None
    if start is not None:
        hunks.append(SaveHunk(start, template[start:], snapshot[start:]))
    if not hunks:
        raise SaveFixtureError("emulator state global segment is identical to the template")
    return tuple(hunks)


def render_save_fixture_manifest(fixtures: tuple[SaveFixture, ...]) -> str:
    """Render fixtures as deterministic TOML accepted by SaveFixtureManifest."""
    if not fixtures:
        raise SaveFixtureError("cannot render an empty save fixture manifest")
    lines = ["version = 1"]
    for fixture in fixtures:
        lines.extend(
            [
                "",
                "[[fixtures]]",
                f"name = {_toml_string(fixture.name)}",
                f"description = {_toml_string(fixture.description)}",
                f"scenario = {_toml_string(fixture.scenario)}",
                f"template_path = {_toml_string(str(fixture.template_path))}",
                f'template_sha256 = "{fixture.template_sha256}"',
                f"target_path = {_toml_string(str(fixture.target_path))}",
                f'target_sha256 = "{fixture.target_sha256}"',
                f'result_sha256 = "{fixture.result_sha256}"',
                "hunks = [",
            ]
        )
        for hunk in fixture.hunks:
            lines.append(
                f'  {{ offset = 0x{hunk.offset:04x}, before = "{hunk.before.hex()}", '
                f'data = "{hunk.data.hex()}" }},'
            )
        lines.append("]")
    return "\n".join(lines) + "\n"


def write_save_fixture_manifest(fixtures: tuple[SaveFixture, ...], output_path: Path) -> None:
    """Write a new fixture manifest without replacing an existing artifact."""
    if output_path.exists():
        raise SaveFixtureError(f"output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_save_fixture_manifest(fixtures))


def _parse_fixture(value: object, index: int) -> SaveFixture:
    context = f"fixtures[{index}]"
    if not isinstance(value, dict):
        raise SaveFixtureError(f"{context} must be a table")
    name = _string(value, "name", context)
    if not _SAFE_NAME.fullmatch(name):
        raise SaveFixtureError(
            f"{context}.name must use lowercase letters, digits, and hyphens"
        )
    description = _string(value, "description", context)
    scenario = _string(value, "scenario", context)
    try:
        scenario.encode("ascii")
    except UnicodeEncodeError as error:
        raise SaveFixtureError(f"{context}.scenario must be ASCII") from error
    template_path = _image_path(value, "template_path", context)
    target_path = _image_path(value, "target_path", context)
    if template_path == target_path:
        raise SaveFixtureError(f"{context} template_path and target_path must differ")

    raw_hunks = value.get("hunks")
    if not isinstance(raw_hunks, list) or not raw_hunks:
        raise SaveFixtureError(f"{context}.hunks must be a non-empty array of tables")
    hunks = tuple(
        _parse_hunk(item, hunk_index, context)
        for hunk_index, item in enumerate(raw_hunks, 1)
    )
    previous_end = 0
    for hunk in hunks:
        if hunk.offset < previous_end:
            raise SaveFixtureError(f"{context}.hunks must be sorted and non-overlapping")
        previous_end = hunk.offset + len(hunk.data)

    return SaveFixture(
        name=name,
        description=description,
        scenario=scenario,
        template_path=template_path,
        template_sha256=_hash(value, "template_sha256", context),
        target_path=target_path,
        target_sha256=_hash(value, "target_sha256", context),
        result_sha256=_hash(value, "result_sha256", context),
        hunks=hunks,
    )


def _parse_hunk(value: object, index: int, fixture_context: str) -> SaveHunk:
    context = f"{fixture_context}.hunks[{index}]"
    if not isinstance(value, dict):
        raise SaveFixtureError(f"{context} must be a table")
    offset = _integer(value, "offset", context)
    if offset < 0:
        raise SaveFixtureError(f"{context}.offset must not be negative")
    before = _hex_bytes(value, "before", context)
    data = _hex_bytes(value, "data", context)
    if not data:
        raise SaveFixtureError(f"{context}.data must not be empty")
    if len(before) != len(data):
        raise SaveFixtureError(f"{context}.before and data must have the same length")
    if before == data:
        raise SaveFixtureError(f"{context} does not change any bytes")
    return SaveHunk(offset, before, data)


def _string(table: dict[str, object], key: str, context: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise SaveFixtureError(f"{context}.{key} must be a non-empty string")
    return value


def _integer(table: dict[str, object], key: str, context: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SaveFixtureError(f"{context}.{key} must be an integer")
    return value


def _hash(table: dict[str, object], key: str, context: str) -> str:
    value = _string(table, key, context).lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise SaveFixtureError(f"{context}.{key} must contain 64 hexadecimal characters")
    return value


def _hex_bytes(table: dict[str, object], key: str, context: str) -> bytes:
    value = _string(table, key, context)
    if len(value) % 2 or any(char not in "0123456789abcdefABCDEF" for char in value):
        raise SaveFixtureError(f"{context}.{key} must contain an even number of hex digits")
    return bytes.fromhex(value)


def _image_path(table: dict[str, object], key: str, context: str) -> PurePosixPath:
    return _validated_image_path(_string(table, key, context), f"{context}.{key}")


def _validated_image_path(value: str | PurePosixPath, context: str) -> PurePosixPath:
    value = PurePosixPath(value)
    if (
        value.is_absolute()
        or not value.parts
        or any(part in ("", ".", "..") for part in value.parts)
    ):
        raise SaveFixtureError(f"{context} must be a safe relative HDI path")
    return value


def _encoded_scenario(scenario: str) -> bytes:
    if not scenario or "\0" in scenario:
        raise SaveFixtureError("scenario must be a non-empty, zero-free ASCII string")
    try:
        return scenario.encode("ascii")
    except UnicodeEncodeError as error:
        raise SaveFixtureError("scenario must be ASCII") from error


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
