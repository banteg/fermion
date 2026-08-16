from __future__ import annotations

import struct
from pathlib import Path

from fermion.script import (
    collect_mes_files,
    render_script,
    script_groups,
    script_lines,
    story_mes_files,
)


def gm_file(code: bytes, dictionary: bytes = b"") -> bytes:
    return struct.pack("<H", 2 + len(dictionary)) + dictionary + code


def test_script_lines_skip_empty_and_mode_two_records(tmp_path: Path) -> None:
    path = tmp_path / "F0001.MES"
    path.write_bytes(
        gm_file(b"\x4a\x01\x18\x04\x19\x00" + b"\x4a\x01\x00" + b"\x4a\x02OK\x00" + b"\x00",
                dictionary=b"\x82\xa0\x82\xa2")
    )

    assert script_lines(path) == [(2 + 4, None, "あ\\nい")]


def test_script_lines_include_encoded_speaker(tmp_path: Path) -> None:
    path = tmp_path / "F0001.MES"
    text = "【コニー】「はい。」".encode("cp932")
    path.write_bytes(gm_file(b"\x4a\x01" + text + b"\x00\x50\x00"))

    assert script_lines(path) == [(2, "コニー", "【コニー】「はい。」")]


def test_render_script_anchors_offsets_in_stream_order(tmp_path: Path) -> None:
    path = tmp_path / "F0001.MES"
    path.write_bytes(
        gm_file(b"\x4a\x02A\x04B\x00" + b"\x4a\x01\x18\x00\x00", dictionary=b"\x82\xa6")
    )

    rendered = render_script([path])
    assert rendered == (
        "<!-- 1 unique MES files, 1 mode-1 text records -->\n"
        "\n## F0001\n[F0001:000a] え\n"
    )


def test_collect_deduplicates_identical_files(tmp_path: Path) -> None:
    (tmp_path / "disk-a").mkdir()
    (tmp_path / "disk-b").mkdir()
    data = gm_file(b"\x4a\x01\x18\x00\x00", dictionary=b"\x82\xa0")
    first = tmp_path / "disk-a" / "F0001.MES"
    first.write_bytes(data)
    (tmp_path / "disk-b" / "F0001.MES").write_bytes(data)

    assert collect_mes_files(tmp_path) == [first]


def test_collect_preserves_physical_extraction_order(tmp_path: Path) -> None:
    (tmp_path / "disk-a").mkdir()
    (tmp_path / "disk-b").mkdir()
    first = tmp_path / "disk-a" / "F0010.MES"
    second = tmp_path / "disk-b" / "F0002.MES"
    first.write_bytes(gm_file(b"\x00", dictionary=b"\x82\xa0"))
    second.write_bytes(gm_file(b"\x00"))

    assert collect_mes_files(tmp_path) == [first, second]


def test_story_files_follow_literal_transitions_and_exclude_terminal(tmp_path: Path) -> None:
    fop = tmp_path / "FOP.MES"
    scene = tmp_path / "F0000.MES"
    main = tmp_path / "MAIN.MES"
    name = tmp_path / "NAME.MES"
    fop.write_bytes(gm_file(b"\x6d\x11f0000.mes\x00\x00\x00"))
    scene.write_bytes(gm_file(b"\x6d\x11main.mes\x00\x00\x00"))
    main.write_bytes(gm_file(b"\x00"))
    name.write_bytes(gm_file(b"\x00", dictionary=b"\x82\xa0"))

    assert story_mes_files([main, name, scene, fop]) == [fop, scene]


def test_script_groups_flag_duplicates_speaker_variants_and_unresolved(tmp_path: Path) -> None:
    connie = "【コニー】「はい。」"
    first = tmp_path / "F0001.MES"
    second = tmp_path / "F0002.MES"
    third = tmp_path / "F0003.MES"
    fourth = tmp_path / "F0004.MES"
    first.write_bytes(gm_file(b"\x4a\x01" + connie.encode("cp932") + b"\x00\x50\x00"))
    second.write_bytes(gm_file(b"\x4a\x01" + connie.encode("cp932") + b"\x00\x50\x00"))
    copy_mother = b"\x45\x0e\xe0\x00\xff\x0c\xe8\x03\x00"
    render_name = b"\x4b\x0e\xe0\x00\x00\x00"
    third.write_bytes(
        gm_file(
            b"\x4a\x01\x81y\x00"
            + copy_mother
            + render_name
            + b"\x4a\x01\x81z\x81u\x82\xcd\x82\xa2\x81B\x81v\x00"
            + b"\x50"
            + b"\x4a\x01\x92n\x82\xcc\x95\xb6\x00"
            + b"\x50\x00"
        )
    )
    copy_sister = b"\x45\x0e\xe0\x00\xff\x0c\xf6\x03\x00"
    fourth.write_bytes(
        gm_file(
            b"\x4a\x01\x81y\x00"
            + copy_sister
            + render_name
            + b"\x4a\x01\x81z\x81u\x82\xcd\x82\xa2\x81B\x81v\x00"
            + b"\x50\x00"
        )
    )

    groups = script_groups([first, second, third, fourth])
    repeated = next(group for group in groups if group.japanese == connie)
    suffix = next(
        group
        for group in groups
        if group.japanese == "】「はい。」" and group.speaker == "name-slot:mother"
    )
    unresolved = next(group for group in groups if group.japanese == "地の文")

    assert repeated.speaker == "コニー"
    assert repeated.status == "review-context"
    assert repeated.flags == ("multi-anchor",)
    assert len(repeated.anchors) == 2
    assert suffix.speaker == "name-slot:mother"
    assert suffix.status == "review-context"
    assert suffix.flags == ("speaker-variant",)
    assert unresolved.speaker is None
    assert unresolved.status == "needs-speaker"
    assert unresolved.flags == ("unresolved-speaker",)
