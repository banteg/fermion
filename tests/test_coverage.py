from __future__ import annotations

import hashlib
import struct

import pytest

from fermion.coverage import CoverageManifest, analyze_coverage
from fermion.translation import TranslationCatalog, TranslationError


def write_fixture(tmp_path, *, translate_both: bool = False):
    source = (
        struct.pack("<H", 2)
        + b"\x4a\x02Repeated\x00"
        + b"\x4a\x02Repeated\x00"
        + b"\x4a\x02Unique\x00"
        + b"\x00"
    )
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    anchors = (
        '[{ file = "DISKA/SCENE.MES", offset = 0x0002 }, '
        '{ file = "DISKA/SCENE.MES", offset = 0x000d }]'
        if translate_both
        else None
    )
    single_anchor = (
        f"anchors = {anchors}" if anchors is not None else 'file = "DISKA/SCENE.MES"\noffset = 0x0002'
    )
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 3
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[entries]]
id = "repeated"
{single_anchor}
source_mode = 2
target_mode = 2
source = "Repeated"
translation = "Shared"
status = "draft"
notes = "Canonical duplicate."
'''
    )
    coverage_path = tmp_path / "coverage.toml"
    coverage_path.write_text(
        '''version = 1

[[scopes]]
id = "opening"
description = "Synthetic opening."

[[scopes.ranges]]
file = "DISKA/SCENE.MES"
start = 0x0002
end = 0x0018

[[scopes.exclusions]]
id = "technical-unique"
file = "DISKA/SCENE.MES"
offset = 0x0018
source_mode = 2
source = "Unique"
reason = "Synthetic non-player-facing text."
'''
    )
    return catalog_path, coverage_path, source_dir


def test_groups_pending_duplicate_anchors_under_existing_canonical_entry(tmp_path) -> None:
    catalog_path, coverage_path, source_dir = write_fixture(tmp_path)

    [report] = analyze_coverage(
        TranslationCatalog.from_file(catalog_path),
        CoverageManifest.from_file(coverage_path),
        source_dir,
    )

    assert len(report.texts) == 3
    assert len(report.translated_anchors) == 1
    assert len(report.excluded_anchors) == 1
    assert report.canonical_line_count == 2
    assert report.duplicate_line_count == 1
    assert report.pending_anchor_count == 1
    [pending] = report.pending_groups
    assert pending.source == "Repeated"
    assert pending.translated_ids == ("repeated",)
    assert pending.anchors[0].offset == 13


def test_multi_anchor_translation_completes_scope(tmp_path) -> None:
    catalog_path, coverage_path, source_dir = write_fixture(
        tmp_path, translate_both=True
    )

    [report] = analyze_coverage(
        TranslationCatalog.from_file(catalog_path),
        CoverageManifest.from_file(coverage_path),
        source_dir,
    )

    assert report.complete
    assert len(report.translated_anchors) == 2
    assert report.pending_anchor_count == 0
    assert report.managed_line_count == 2


def test_rejects_overlapping_coverage_ranges(tmp_path) -> None:
    _catalog_path, coverage_path, _source_dir = write_fixture(tmp_path)
    coverage_path.write_text(
        coverage_path.read_text()
        + '''
[[scopes.ranges]]
file = "DISKA/SCENE.MES"
start = 0x0010
end = 0x0020
'''
    )

    with pytest.raises(TranslationError, match="overlapping ranges"):
        CoverageManifest.from_file(coverage_path)
