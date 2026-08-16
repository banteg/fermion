from __future__ import annotations

import struct

import pytest

from fermion.gm import GMError, GMFile


def gm_file(code: bytes, dictionary: bytes = b"") -> bytes:
    return struct.pack("<H", 2 + len(dictionary)) + dictionary + code


def gm_text(text: str) -> bytes:
    return b"\x4a\x01" + text.encode("cp932") + b"\x00"


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
        (record.offset, record.end, record.mode, record.payload, record.text)
        for record in GMFile.from_bytes(data).text_records()
    ] == [(8, 12, 2, b"A", "A")]


def test_mode_one_text_decodes_dictionary_tokens_newlines_and_sjis() -> None:
    record = GMFile.from_bytes(
        gm_file(b"\x4a\x01\x18\x04\x82\xa2\x00\x00", dictionary=b"\x82\xa0")
    ).text_records()[0]

    assert (record.mode, record.payload, record.text, record.ascii_text) == (
        1,
        b"\x18\x04\x82\xa2",
        "あ\nい",
        None,
    )


def test_mode_two_text_decodes_newline_control() -> None:
    record = GMFile.from_bytes(gm_file(b"\x4a\x02A\x04B\x00\x00")).text_records()[0]

    assert (record.mode, record.payload, record.text, record.ascii_text) == (
        2,
        b"A\x04B",
        "A\nB",
        "A\nB",
    )


def test_mode_one_text_decodes_pc98_box_drawing_dictionary_entries() -> None:
    record = GMFile.from_bytes(
        gm_file(b"\x4a\x01\x18\x00\x00", dictionary=b"\x86\xa2")
    ).text_records()[0]

    assert record.text == "─"


def test_recovers_literal_scenario_transitions() -> None:
    gm = GMFile.from_bytes(
        gm_file(
            b"\x6d\x11f0000.mes\x00\x00"
            b"\x6f\x11name.mes\x00\x00"
            b"\x00"
        )
    )

    assert [
        (transition.offset, transition.kind, transition.target)
        for transition in gm.transitions()
    ] == [
        (2, "replace", "f0000.mes"),
        (15, "nested", "name.mes"),
    ]


def test_rejects_computed_scenario_transition_target() -> None:
    gm = GMFile.from_bytes(gm_file(b"\x6d\x01\x01\x00\x00\x00"))

    with pytest.raises(GMError, match="target is not a literal string"):
        gm.transitions()


def test_attributes_literal_speaker_label() -> None:
    gm = GMFile.from_bytes(gm_file(gm_text("【コニー】「はい。」") + b"\x50\x00"))

    [attributed] = gm.attributed_text_records()

    assert attributed.record.text == "【コニー】「はい。」"
    assert attributed.speaker is not None
    assert (
        attributed.speaker.id,
        attributed.speaker.source,
        attributed.speaker.default_name,
    ) == ("コニー", "inline-label", "コニー")


@pytest.mark.parametrize(
    ("slot", "speaker", "default_name"),
    [
        (0x03E8, "name-slot:mother", "由貴"),
        (0x03F6, "name-slot:older-sister", "瑠璃"),
        (0x0404, "name-slot:dear-person", "加奈子"),
        (0x0412, "name-slot:friend-1", "陽子"),
        (0x0420, "name-slot:friend-2", "弘子"),
    ],
)
def test_attributes_customizable_speaker_render_sequence(
    slot: int, speaker: str, default_name: str
) -> None:
    copy_name = b"\x45\x0e\xe0\x00\xff\x0c" + struct.pack("<H", slot) + b"\x00"
    render_name = b"\x4b\x0e\xe0\x00\x00\x00"
    gm = GMFile.from_bytes(
        gm_file(
            gm_text("【")
            + copy_name
            + render_name
            + gm_text("】「はい。」")
            + b"\x50\x00"
        )
    )

    attributed = gm.attributed_text_records()

    assert [item.record.text for item in attributed] == ["【", "】「はい。」"]
    assert [item.speaker.id if item.speaker else None for item in attributed] == [
        speaker,
        speaker,
    ]
    assert attributed[0].speaker is not None
    assert attributed[0].speaker.source == "name-slot"
    assert attributed[0].speaker.default_name == default_name


def test_does_not_guess_speaker_from_quote_style_or_previous_message() -> None:
    gm = GMFile.from_bytes(
        gm_file(
            gm_text("【医師】「こちらです。」")
            + b"\x50\x00"
            + gm_text("『わかりました。』")
            + b"\x50\x00"
        )
    )

    attributed = gm.attributed_text_records()

    assert attributed[0].speaker is not None
    assert attributed[0].speaker.id == "医師"
    assert attributed[1].speaker is None


def test_does_not_attribute_partial_bracket_without_exact_name_sequence() -> None:
    gm = GMFile.from_bytes(
        gm_file(gm_text("【") + gm_text("】「はい。」") + b"\x50\x00")
    )

    assert [item.speaker for item in gm.attributed_text_records()] == [None, None]


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
