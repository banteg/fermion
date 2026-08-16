from __future__ import annotations

import hashlib
import struct

import pytest

from fermion.gm import GMFile
from fermion.translation import (
    TranslationCatalog,
    TranslationEntry,
    TranslationError,
    _patch_gm_source,
)


def write_catalog(tmp_path, source_hash: str, *, translation: str = "Hello world"):
    catalog = tmp_path / "catalog.toml"
    catalog.write_text(
        f'''version = 2
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{source_hash}"

[[entries]]
id = "scene-0001"
file = "DISKA/SCENE.MES"
offset = 0x0002
source_mode = 2
target_mode = 2
source = "Original"
translation = "{translation}"
status = "draft"
box_width = 8
notes = "A useful note."
'''
    )
    return catalog


def test_loads_wraps_and_verifies_catalog_source(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Original\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest())

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)

    [entry] = catalog.entries
    assert entry.wrapped_translation == ("Hello", "world")
    assert entry.notes == "A useful note."
    [catalog_file] = catalog.files
    assert (catalog_file.archive, catalog_file.name) == ("DISKA", "SCENE.MES")


def test_rejects_changed_source_anchor(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Changed\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest())

    with pytest.raises(TranslationError, match="source text changed"):
        TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)


def test_rejects_non_ascii_mode_two_translation(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, translation="café")

    with pytest.raises(TranslationError, match="cannot be encoded"):
        TranslationCatalog.from_file(catalog_path)


def test_rejects_case_insensitive_duplicate_catalog_files(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64)
    catalog_path.write_text(
        catalog_path.read_text()
        + '''

[[files]]
file = "diska/scene.mes"
source = "disk-a/other.mes"
sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
'''
    )

    with pytest.raises(TranslationError, match="duplicate file names"):
        TranslationCatalog.from_file(catalog_path)


def test_patches_lime_juice_source_by_original_offset() -> None:
    original = GMFile.from_bytes(
        struct.pack("<H", 2) + b"\x4a\x02Original\x00\x4a\x02Other\x00\x00"
    )
    entry = TranslationEntry(
        id="scene-0001",
        file="DISKA/SCENE.MES",
        offset=2,
        source_mode=2,
        target_mode=2,
        source="Original",
        translation='He said "hello"',
        status="draft",
        notes="Test",
    )
    source = '''(mes
 (gm-text 2 "Original")
 (gm-text 2 "Other")
 (raw 0))
'''

    patched = _patch_gm_source(source, original, (entry,))

    assert '(gm-text 2 "He said \\"hello\\"")' in patched
    assert '(gm-text 2 "Other")' in patched
