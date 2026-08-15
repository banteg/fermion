from __future__ import annotations

import struct

import pytest

from fermion.gm import GMError, GMFile


def gm_file(code: bytes, dictionary: bytes = b"") -> bytes:
    return struct.pack("<H", 2 + len(dictionary)) + dictionary + code


def test_rejects_invalid_container() -> None:
    with pytest.raises(GMError, match="too small"):
        GMFile.from_bytes(b"")
    with pytest.raises(GMError, match="odd byte length"):
        GMFile.from_bytes(b"\x03\x00x")


def test_walks_fixed_targets_and_text() -> None:
    data = gm_file(
        b"\x40\x08\x00\x12\x79\x00"
        b"\x4a\x02A\x00"
        b"\x00"
    )

    audit = GMFile.from_bytes(data).audit()

    assert [(item.offset, item.end, item.opcode) for item in audit.instructions] == [
        (2, 8, 0x40),
        (8, 12, 0x4A),
        (12, 13, 0),
    ]
    assert [(item.field_offset, item.target) for item in audit.relocations] == [
        (3, 8),
        (5, 0x7912),
    ]
    assert audit.issues == ()
    assert [
        (record.offset, record.end, record.mode, record.payload, record.ascii_text)
        for record in GMFile.from_bytes(data).text_records()
    ] == [(8, 12, 2, b"A", "A")]


def test_mode_one_text_is_exposed_as_raw_tokens() -> None:
    record = GMFile.from_bytes(gm_file(b"\x4a\x01\x18\x04\x00\x00")).text_records()[0]

    assert (record.mode, record.payload, record.ascii_text) == (1, b"\x18\x04", None)


def test_walks_opcode_44_inline_data_to_its_skip_target() -> None:
    data = gm_file(b"\x44\x0f\x00\x00\x0b\x00\x11x\x00\x00")

    audit = GMFile.from_bytes(data).audit()

    assert [(item.offset, item.end, item.opcode) for item in audit.instructions] == [
        (2, 11, 0x44),
        (11, 12, 0),
    ]
    assert [(item.field_offset, item.target) for item in audit.relocations] == [(6, 11)]
    assert audit.issues == ()


def test_finds_callback_literal_inside_opcode_3a() -> None:
    data = gm_file(
        b"\x3a\x01"
        b"\x01\x01\x00"
        b"\x01\x01\x00"
        + b"\x01\x00\x00" * 4
        + b"\x02\x1e\x00\x00"
        + b"\x01\x00\x00"
        + b"\x00\x00"
    )

    audit = GMFile.from_bytes(data).audit()

    assert [(item.offset, item.end, item.opcode) for item in audit.instructions] == [
        (2, 30, 0x3A),
        (30, 31, 0),
    ]
    assert [(item.field_offset, item.target, item.purpose) for item in audit.relocations] == [
        (23, 30, "0x3a callback")
    ]
    assert audit.issues == ()


def test_walks_expression_selected_subdispatch_payloads() -> None:
    data = gm_file(
        b"\x6b\x01\x05\x00\x01\xa0\x00\x00"
        b"\x71\x01\x00\x00\x0b\x34\x12\x00\x00"
        b"\x00"
    )

    audit = GMFile.from_bytes(data).audit()

    assert [(item.offset, item.end, item.opcode) for item in audit.instructions] == [
        (2, 10, 0x6B),
        (10, 19, 0x71),
        (19, 20, 0),
    ]
    assert audit.issues == ()
