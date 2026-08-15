from __future__ import annotations

from pathlib import Path

from fermion.mes import Variant, probe_roundtrip


def test_reports_exact_roundtrip(tmp_path: Path) -> None:
    fake_juice = tmp_path / "juice"
    fake_juice.write_text(
        """#!/bin/sh
output=""
input=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o) output="$2"; shift 2 ;;
    -d|-c|-f) shift ;;
    *) input="$1"; shift ;;
  esac
done
cp "$input" "$output"
"""
    )
    fake_juice.chmod(0o755)
    source = tmp_path / "MAIN.MES"
    source.write_bytes(b"scenario")

    [result] = probe_roundtrip(
        source,
        fake_juice,
        tmp_path / "output",
        variants=(Variant("test", ()),),
    )

    assert result.decompile_returncode == 0
    assert result.compile_returncode == 0
    assert result.output_size == len(b"scenario")
    assert result.exact
