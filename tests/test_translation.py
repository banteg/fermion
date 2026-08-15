from __future__ import annotations

import hashlib
import struct

import pytest

from fermion.translation import TranslationCatalog, TranslationError


def write_catalog(tmp_path, source_hash: str, *, translation: str = "Hello world"):
    catalog = tmp_path / "catalog.toml"
    catalog.write_text(
        f'''version = 1
game = "Test"

[[files]]
name = "SCENE.MES"
sha256 = "{source_hash}"

[[entries]]
id = "scene-0001"
file = "SCENE.MES"
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
    source_dir.mkdir()
    (source_dir / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest())

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)

    [entry] = catalog.entries
    assert entry.wrapped_translation == ("Hello", "world")
    assert entry.notes == "A useful note."


def test_rejects_changed_source_anchor(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Changed\x00\x00"
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest())

    with pytest.raises(TranslationError, match="source text changed"):
        TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)


def test_rejects_non_ascii_mode_two_translation(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, translation="café")

    with pytest.raises(TranslationError, match="cannot be encoded"):
        TranslationCatalog.from_file(catalog_path)
