"""English defaults for Fermion's persistent runtime name and term slots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from fermion.translation import (
    _EDITOR_LAYOUTS,
    TranslationCatalog,
    TranslationError,
    _runtime_token_bytes,
)

RUNTIME_DEFAULT_BANK_PATH = PurePosixPath("FERM/REG_00")
_RUNTIME_GLOBAL_DATA_OFFSET = 0x1002
_MODE_1_HEADER = b"\xff\x01"
_MODE_2_HEADER = b"\xff\x02"


@dataclass(frozen=True)
class RuntimeDefaultSeed:
    """Catalog defaults migrated into a serialized persistent global bank."""

    data: bytes
    seeded: tuple[str, ...]
    already_english: tuple[str, ...]
    preserved_custom: tuple[str, ...]


def seed_runtime_token_defaults(
    catalog: TranslationCatalog,
    bank: bytes,
) -> RuntimeDefaultSeed:
    """Seed untouched runtime names and terms without replacing player edits."""
    expected_ids = {
        str(token_id)
        for layout in _EDITOR_LAYOUTS.values()
        for token_id, _slot in tuple(layout["destinations"])
    }
    tokens = {token.id: token for token in catalog.tokens if token.id in expected_ids}
    if not tokens:
        return RuntimeDefaultSeed(bank, (), (), ())
    missing = expected_ids - tokens.keys()
    if missing:
        raise TranslationError(
            "runtime default seeding requires every fixed token: " + ", ".join(sorted(missing))
        )

    result = bytearray(bank)
    seeded = []
    already_english = []
    preserved_custom = []
    for layout in _EDITOR_LAYOUTS.values():
        destinations = tuple(layout["destinations"])
        boundaries = (*destinations[1:], (None, int(layout["slot_end"])))
        for (token_id, slot), (_next_token_id, end) in zip(destinations, boundaries, strict=True):
            token = tokens[str(token_id)]
            initializer_slots = {initializer.slot for initializer in token.initializers}
            if initializer_slots != {int(slot)}:
                raise TranslationError(
                    f"{token.id}: runtime default initializer must target slot {slot}"
                )

            start = _RUNTIME_GLOBAL_DATA_OFFSET + int(slot)
            payload_size = int(end) - int(slot) - 2
            stop = start + payload_size
            if start < 2 or payload_size < 1 or stop > len(result):
                raise TranslationError(f"{token.id}: REG_00 does not contain runtime slot {slot}")

            source = token.source.encode("cp932")
            target = _runtime_token_bytes(token.translation)
            serialized_target = target + b"\0"
            if len(serialized_target) > payload_size:
                raise TranslationError(
                    f"{token.id}: translated default exceeds its serialized REG_00 payload"
                )
            header = bytes(result[start - 2 : start])
            current = bytes(result[start:stop])
            if header == _MODE_2_HEADER and _serialized_runtime_value_matches(current, target):
                already_english.append(token.id)
                continue
            legacy_target = _legacy_mode_one_bytes(token.translation)
            migratable_mode_one = header == _MODE_1_HEADER and (
                _serialized_runtime_value_matches(current, source)
                or _serialized_runtime_value_matches(current, legacy_target)
            )
            if not (migratable_mode_one or not current.strip(b"\0")):
                preserved_custom.append(token.id)
                continue
            result[start - 2 : start] = _MODE_2_HEADER
            result[start:stop] = serialized_target.ljust(payload_size, b"\0")
            seeded.append(token.id)

    return RuntimeDefaultSeed(
        bytes(result),
        tuple(seeded),
        tuple(already_english),
        tuple(preserved_custom),
    )


def _serialized_runtime_value_matches(region: bytes, value: bytes) -> bool:
    if not region.startswith(value):
        return False
    return len(region) == len(value) or region[len(value)] == 0


def _legacy_mode_one_bytes(value: str) -> bytes:
    """Encode defaults written by the superseded full-width Latin build."""
    converted = []
    punctuation = {" ": "　", "-": "－", "'": "＇"}
    for character in value:
        converted.append(punctuation.get(character, chr(ord(character) + 0xFEE0)))
    return "".join(converted).encode("cp932")
