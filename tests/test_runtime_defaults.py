from pathlib import Path

from fermion.runtime_defaults import seed_runtime_token_defaults
from fermion.translation import TranslationCatalog

_SLOTS = (
    ("name:mother", 1000, 1014),
    ("name:older-sister", 1014, 1028),
    ("name:dear-person", 1028, 1042),
    ("name:friend-1", 1042, 1056),
    ("name:friend-2", 1056, 1070),
    ("term:slot-1", 1070, 1086),
    ("term:slot-2", 1086, 1102),
)
_GLOBAL_DATA_OFFSET = 0x1002
_LEGACY_FULLWIDTH = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-'",
    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
    "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ－＇",
)


def _catalog() -> TranslationCatalog:
    return TranslationCatalog.from_file(Path(__file__).parents[1] / "translations" / "fermion.toml")


def _source_bank(catalog: TranslationCatalog) -> bytes:
    tokens = {token.id: token for token in catalog.tokens}
    bank = bytearray(0x1B20)
    for token_id, slot, next_slot in _SLOTS:
        start = _GLOBAL_DATA_OFFSET + slot
        bank[start - 2 : start] = b"\xff\x01"
        payload_size = next_slot - slot - 2
        source = tokens[token_id].source.encode("cp932")
        bank[start : start + payload_size] = source.ljust(payload_size, b"\0")
    return bytes(bank)


def test_seeds_english_runtime_defaults_without_changing_slots() -> None:
    catalog = _catalog()
    tokens = {token.id: token for token in catalog.tokens}
    source = _source_bank(catalog)

    result = seed_runtime_token_defaults(catalog, source)

    assert result.seeded == tuple(token_id for token_id, _slot, _end in _SLOTS)
    assert result.already_english == ()
    assert result.preserved_custom == ()
    for token_id, slot, next_slot in _SLOTS:
        start = _GLOBAL_DATA_OFFSET + slot
        payload_size = next_slot - slot - 2
        expected = tokens[token_id].translation.encode("ascii") + b"\0"
        assert result.data[start : start + payload_size] == expected.ljust(payload_size, b"\0")
        assert result.data[start - 2 : start] == b"\xff\x02"


def test_preserves_custom_values_and_is_idempotent() -> None:
    catalog = _catalog()
    source = bytearray(_source_bank(catalog))
    start = _GLOBAL_DATA_OFFSET + 1000
    custom = "Ａｌｉｃｅ".encode("cp932")
    source[start : start + 12] = custom.ljust(12, b"\0")

    first = seed_runtime_token_defaults(catalog, bytes(source))
    second = seed_runtime_token_defaults(catalog, first.data)

    assert first.preserved_custom == ("name:mother",)
    assert first.data[start : start + 12] == custom.ljust(12, b"\0")
    assert first.data[start - 2 : start] == b"\xff\x01"
    assert second.seeded == ()
    assert second.preserved_custom == ("name:mother",)
    assert second.already_english == tuple(token_id for token_id, _slot, _end in _SLOTS[1:])


def test_migrates_superseded_fullwidth_english_defaults() -> None:
    catalog = _catalog()
    tokens = {token.id: token for token in catalog.tokens}
    source = bytearray(_source_bank(catalog))
    for token_id, slot, next_slot in _SLOTS:
        start = _GLOBAL_DATA_OFFSET + slot
        payload_size = next_slot - slot - 2
        legacy = tokens[token_id].translation.translate(_LEGACY_FULLWIDTH).encode("cp932")
        source[start : start + payload_size] = legacy.ljust(payload_size, b"\0")

    result = seed_runtime_token_defaults(catalog, bytes(source))

    assert result.seeded == tuple(token_id for token_id, _slot, _end in _SLOTS)
    assert result.already_english == ()
    assert result.preserved_custom == ()
    for token_id, slot, next_slot in _SLOTS:
        start = _GLOBAL_DATA_OFFSET + slot
        payload_size = next_slot - slot - 2
        expected = tokens[token_id].translation.encode("ascii") + b"\0"
        assert result.data[start - 2 : start] == b"\xff\x02"
        assert result.data[start : start + payload_size] == expected.ljust(payload_size, b"\0")
