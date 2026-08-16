from __future__ import annotations

import struct
from pathlib import Path

from fermion.script import collect_mes_files, render_script, script_lines


def gm_file(code: bytes, dictionary: bytes = b"") -> bytes:
    return struct.pack("<H", 2 + len(dictionary)) + dictionary + code


def test_script_lines_skip_empty_and_mode_two_records(tmp_path: Path) -> None:
    path = tmp_path / "F0001.MES"
    path.write_bytes(
        gm_file(b"\x4a\x01\x18\x04\x19\x00" + b"\x4a\x01\x00" + b"\x4a\x02OK\x00" + b"\x00",
                dictionary=b"\x82\xa0\x82\xa2")
    )

    assert script_lines(path) == [(2 + 4, "あ\\nい")]


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
