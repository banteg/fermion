from __future__ import annotations

import hashlib
import struct
from pathlib import Path

import pytest

from fermion.gm import GMFile
from fermion.translation import (
    PhysicalTranslation,
    TranslationAnchor,
    TranslationCatalog,
    TranslationEntry,
    TranslationError,
    TranslationFile,
    TranslationToken,
    _patch_editor_preset_source,
    _patch_gm_source,
    _patch_token_initializer_source,
    _runtime_token_bytes,
    _verify_compiled_file,
    _wrap_text,
)


def test_editor_preset_patch_uses_mode_one_safe_fullwidth_strings() -> None:
    presets = {
        "name:mother": ("Yuki", "May", "Helen", "Olivia"),
        "name:older-sister": ("Ruri", "Ruby", "Alice", "Chloe"),
        "name:dear-person": ("Kanako", "Kana", "Sarah", "Emma"),
        "name:friend-1": ("Yoko", "Yuna", "Maria", "Ava"),
        "name:friend-2": ("Hiroko", "Hina", "Erika", "Mia"),
    }
    tokens = tuple(
        TranslationToken(token_id, "source", choices[0], 12, choices)
        for token_id, choices in presets.items()
    )
    source = """prefix
(label 2531)
               (switch (local-address 2723) (ref 11 2002))
               (case (local-address 2723) 200)
               (label 2723)
               (next))
suffix
"""

    patched = _patch_editor_preset_source(source, "NAME.MES", tokens)

    yuki = " ".join(str(byte) for byte in _runtime_token_bytes("Yuki"))
    assert f"(inline-source 0 255 1 {yuki})" in patched
    assert patched.count("(string-copy (ref 14 160)") == 20
    assert "legacy" not in patched


def test_runtime_token_bytes_are_fullwidth_cp932() -> None:
    assert _runtime_token_bytes("Hiroko") == "Ｈｉｒｏｋｏ".encode("cp932")


def test_wrap_text_preserves_whitespace_only_layout_records() -> None:
    assert _wrap_text("  ", 61) == ("  ",)


def write_catalog(
    tmp_path,
    source_hash: str,
    *,
    translation: str = "Hello world",
    file_box_width: int | None = None,
    entry_box_width: int | None = 8,
    notes: str | None = "A useful note.",
):
    catalog = tmp_path / "catalog.toml"
    file_width = f"box_width = {file_box_width}\n" if file_box_width is not None else ""
    entry_width = f"box_width = {entry_box_width}\n" if entry_box_width is not None else ""
    entry_notes = f'notes = "{notes}"\n' if notes is not None else ""
    catalog.write_text(
        f'''version = 4
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{source_hash}"
{file_width}

[[entries]]
id = "scene-0001"
file = "DISKA/SCENE.MES"
offset = 0x0002
source_mode = 2
target_mode = 2
source = "Original"
translation = "{translation}"
speaker = "narrator"
context = "Synthetic scene."
status = "draft"
{entry_width}{entry_notes}
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
    assert (entry.speaker, entry.context) == ("narrator", "Synthetic scene.")
    assert entry.anchors == (TranslationAnchor("DISKA/SCENE.MES", 2),)
    [catalog_file] = catalog.files
    assert (catalog_file.archive, catalog_file.name) == ("DISKA", "SCENE.MES")


def test_notes_may_be_omitted_from_simple_entry(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Original\x00\x00"
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest(), notes=None)

    catalog = TranslationCatalog.from_file(catalog_path)

    assert catalog.entries[0].notes == ""


def test_opening_exposition_reveal_ticks_do_not_split_words() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    crawl = [entry for entry in catalog.entries if entry.id.startswith("opening-exposition-")]

    assert crawl
    for entry in crawl:
        text = entry.translation.rstrip("\n")
        assert len(text) <= 72, f"{entry.id} exceeds two 36-character reveals"
        for boundary in range(36, len(text), 36):
            assert not (text[boundary - 1].isalnum() and text[boundary].isalnum()), (
                f"{entry.id} splits a word at reveal boundary {boundary}"
            )


def test_file_width_is_the_compile_default(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Original\x00\x00"
    catalog_path = write_catalog(
        tmp_path,
        hashlib.sha256(source).hexdigest(),
        file_box_width=8,
        entry_box_width=None,
    )

    catalog = TranslationCatalog.from_file(catalog_path)
    [entry] = catalog.entries
    [catalog_file] = catalog.files

    assert catalog_file.box_width == 8
    assert entry.wrapped_translation == ("Hello world",)
    assert entry.compiled_translation(catalog_file.box_width) == "Hello\nworld"
    [physical] = catalog.physical_translations(compiled=True)
    assert physical.translation == "Hello\nworld"


def test_rejects_changed_source_anchor(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Changed\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest())

    with pytest.raises(TranslationError, match="source text changed"):
        TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)


def test_rejects_catalog_speaker_conflicting_with_encoded_label(tmp_path) -> None:
    japanese = "【コニー】「はい。」"
    source = struct.pack("<H", 2) + b"\x4a\x01" + japanese.encode("cp932") + b"\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 4
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[entries]]
id = "wrong-speaker"
file = "DISKA/SCENE.MES"
offset = 0x0002
source_mode = 1
target_mode = 2
source = "{japanese}"
translation = "[CONNIE] Yes."
speaker = "神崎"
context = "Synthetic dialogue."
status = "draft"
notes = "Must agree with an encoded label."
'''
    )

    with pytest.raises(TranslationError, match="encoded speaker"):
        TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)


def test_rejects_non_ascii_mode_two_translation(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, translation="café")

    with pytest.raises(TranslationError, match="cannot be encoded"):
        TranslationCatalog.from_file(catalog_path)


def test_rejects_case_insensitive_duplicate_catalog_files(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64)
    catalog_path.write_text(
        catalog_path.read_text()
        + """

[[files]]
file = "diska/scene.mes"
source = "disk-a/other.mes"
sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
"""
    )

    with pytest.raises(TranslationError, match="duplicate file names"):
        TranslationCatalog.from_file(catalog_path)


def test_patches_lime_juice_source_by_original_offset() -> None:
    original = GMFile.from_bytes(
        struct.pack("<H", 2) + b"\x4a\x02Original\x00\x4a\x02Other\x00\x00"
    )
    entry = TranslationEntry(
        id="scene-0001",
        anchors=(TranslationAnchor("DISKA/SCENE.MES", 2),),
        source_mode=2,
        target_mode=2,
        source="Original",
        translation='He said "hello"',
        speaker="narrator",
        context="Synthetic scene.",
        status="draft",
        notes="Test",
    )
    source = """(mes
 (gm-text 2 "Original")
 (gm-text 2 "Other")
 (raw 0))
"""

    patched = _patch_gm_source(source, original, ((2, entry),))

    assert '(gm-text 2 "He said \\"hello\\"")' in patched
    assert '(gm-text 2 "Other")' in patched


def test_patch_uses_precompiled_physical_translation() -> None:
    original = GMFile.from_bytes(struct.pack("<H", 2) + b"\x4a\x02Original\x00\x00")
    entry = PhysicalTranslation(
        id="scene-0001",
        anchor=TranslationAnchor("DISKA/SCENE.MES", 2),
        source_mode=2,
        target_mode=2,
        source="Original",
        translation="Hello world\nagain",
    )
    source = """(mes
 (gm-text 2 "Original")
 (raw 0))
"""

    patched = _patch_gm_source(source, original, ((2, entry),))

    assert '(gm-text 2 "Hello world\\nagain")' in patched


def test_schema_five_composite_splits_around_immutable_token(tmp_path) -> None:
    prefix = b"\x4a\x02Hello \x00"
    copy_name = b"\x45\x0e\xe0\x00\xff\x0c\x04\x04\x00"
    render_name = b"\x4b\x0e\xe0\x00\x00\x00"
    suffix = b"\x4a\x02!\x00"
    source = struct.pack("<H", 2) + prefix + copy_name + render_name + suffix + b"\x00"
    token_start = 2 + len(prefix)
    token_end = token_start + len(copy_name) + len(render_name)
    suffix_offset = token_end
    token_hash = hashlib.sha256(source[token_start:token_end]).hexdigest()
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 5
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"
box_width = 8

[[tokens]]
id = "name:dear-person"
source = "加奈子"
translation = "Kanako"
max_width = 6

[[composites]]
id = "scene-greeting"
target_mode = 2
source = "Hello ⟦name:dear-person⟧!"
translation = "Hi ⟦name:dear-person⟧!"
speaker = "narrator"
context = "Synthetic composite greeting."
status = "draft"

[[composites.occurrences]]
file = "DISKA/SCENE.MES"
segments = [
  {{ kind = "text", offset = 0x0002, source_mode = 2, source = "Hello " }},
  {{ kind = "token", token = "name:dear-person", start = 0x{token_start:04x}, end = 0x{token_end:04x}, sha256 = "{token_hash}" }},
  {{ kind = "text", offset = 0x{suffix_offset:04x}, source_mode = 2, source = "!" }},
]
'''
    )

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)

    assert (catalog.entry_count, catalog.anchor_count) == (1, 2)
    assert catalog.composites[0].translation == "Hi ⟦name:dear-person⟧!"
    assert catalog.composites[0].notes == ""
    physical = catalog.physical_translations(compiled=True)
    assert [(item.anchor.offset, item.translation) for item in physical] == [
        (2, "Hi\n"),
        (suffix_offset, "!"),
    ]

    rkt = f"""(mes
 (gm-text 2 "Hello ")
 (raw {" ".join(str(byte) for byte in copy_name + render_name)})
 (gm-text 2 "!")
 (raw 0))
"""
    patched = _patch_gm_source(
        rkt,
        GMFile.from_bytes(source),
        tuple((item.anchor.offset, item) for item in physical),
    )
    assert '(gm-text 2 "Hi\\n")' in patched
    assert f"(raw {' '.join(str(byte) for byte in copy_name + render_name)})" in patched


def test_schema_five_rejects_missing_translation_token(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64)
    text = catalog_path.read_text().replace("version = 4", "version = 5")
    text += """

[[tokens]]
id = "name:dear-person"
source = "加奈子"
translation = "Kanako"
max_width = 6

[[composites]]
id = "broken"
target_mode = 2
source = "Hello ⟦name:dear-person⟧!"
translation = "Hello!"
speaker = "narrator"
context = "Synthetic broken composite."
status = "draft"
notes = "Must be rejected."

[[composites.occurrences]]
file = "DISKA/SCENE.MES"
segments = [
  { kind = "text", offset = 0x0010, source_mode = 2, source = "Hello " },
  { kind = "token", token = "name:dear-person", start = 0x0020, end = 0x002f, sha256 = "0000000000000000000000000000000000000000000000000000000000000000" },
  { kind = "text", offset = 0x0030, source_mode = 2, source = "!" },
]
"""
    catalog_path.write_text(text)

    with pytest.raises(TranslationError, match="must contain at least one authoring token"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_five_verifies_and_patches_same_size_token_initializer(tmp_path) -> None:
    source_name = "加奈子".encode("cp932")
    initializer = b"\x45\x0e\xe0\x00\xff\x01" + source_name + b"\x00\x00"
    assignment = b"\x43\x0c\x04\x04\x0e\xe0\x00\x00\x00"
    text = b"\x4a\x02Original\x00"
    source = (
        struct.pack("<H", 2) + initializer + assignment + text + initializer + assignment + b"\x00"
    )
    text_offset = 2 + len(initializer) + len(assignment)
    second_initializer_offset = text_offset + len(text)
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 5
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[tokens]]
id = "name:dear-person"
source = "加奈子"
translation = "Kanako"
max_width = 6
initializers = [
  {{ file = "DISKA/SCENE.MES", offset = 0x0002, slot = 0x0404 }},
  {{ file = "DISKA/SCENE.MES", offset = 0x{second_initializer_offset:04x}, slot = 0x0404 }},
]

[[entries]]
id = "scene-line"
file = "DISKA/SCENE.MES"
offset = 0x{text_offset:04x}
source_mode = 2
target_mode = 2
source = "Original"
translation = "Translated"
speaker = "narrator"
context = "Synthetic scene."
status = "draft"
notes = "Keeps the catalog non-empty."
'''
    )

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)
    [token] = catalog.tokens
    token_initializers = tuple((token, item) for item in token.initializers)
    source_values = " ".join(str(byte) for byte in source_name)
    rkt = f"""(mes
 (string-copy (ref 14 224) (inline-source 0 255 1 {source_values}))
 (assign (ref 12 1028) (string-value (ref 14 224)))
 (text #:mode 2 "Original")
 (string-copy (ref 14 224) (inline-source 0 255 1 {source_values}))
 (assign (ref 12 1028) (string-value (ref 14 224)))
 (end))
"""
    patched = _patch_token_initializer_source(rkt, GMFile.from_bytes(source), token_initializers)

    translated_values = " ".join(str(byte) for byte in _runtime_token_bytes("Kanako"))
    assert source_values not in patched
    assert patched.count(f"(inline-source 0 255 1 {translated_values})") == 2


def test_schema_five_relocates_shorter_token_initializer(tmp_path) -> None:
    source_term = "おま○こ".encode("cp932")
    initializer = b"\x45\x0e\xe0\x00\xff\x01" + source_term + b"\x00\x00"
    assignment = b"\x43\x0c\x2e\x04\x0e\xe0\x00\x00\x00"
    text = b"\x4a\x02Original\x00"
    text_offset = 2 + len(initializer) + len(assignment)
    source = struct.pack("<H", 2) + initializer + assignment + text + b"\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 5
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[tokens]]
id = "term:slot-1"
source = "おま○こ"
translation = "cat"
max_width = 3
initializers = [
  {{ file = "DISKA/SCENE.MES", offset = 0x0002, slot = 0x042e }},
]

[[entries]]
id = "scene-line"
file = "DISKA/SCENE.MES"
offset = 0x{text_offset:04x}
source_mode = 2
target_mode = 2
source = "Original"
translation = "Original"
speaker = "narrator"
context = "Synthetic scene."
status = "draft"
'''
    )

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)
    [token] = catalog.tokens
    token_initializers = tuple((token, item) for item in token.initializers)
    original = GMFile.from_bytes(source)
    translated_term = _runtime_token_bytes("cat")
    translated_initializer = b"\x45\x0e\xe0\x00\xff\x01" + translated_term + b"\x00\x00"
    compiled = GMFile.from_bytes(
        struct.pack("<H", 2) + translated_initializer + assignment + text + b"\x00"
    )

    assert len(compiled.data) < len(source)
    assert source_term not in compiled.data
    assert translated_term + b"\x00\x00\x43\x0c\x2e\x04" in compiled.data
    assert compiled.audit().issues == ()
    _verify_compiled_file(
        catalog.files[0],
        original,
        compiled,
        (),
        token_initializers,
    )


def test_schema_five_relocates_initializer_translation_longer_than_source(
    tmp_path,
) -> None:
    source_name = "弘子".encode("cp932")
    initializer = b"\x45\x0e\xe0\x00\xff\x01" + source_name + b"\x00\x00"
    assignment = b"\x43\x0c\x20\x04\x0e\xe0\x00\x00\x00"
    text = b"\x4a\x02Original\x00"
    text_offset = 2 + len(initializer) + len(assignment)
    source = struct.pack("<H", 2) + initializer + assignment + text + b"\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 5
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[tokens]]
id = "name:friend-2"
source = "弘子"
translation = "Hiroko"
max_width = 6
initializers = [
  {{ file = "DISKA/SCENE.MES", offset = 0x0002, slot = 0x0420 }},
]

[[entries]]
id = "scene-line"
file = "DISKA/SCENE.MES"
offset = 0x{text_offset:04x}
source_mode = 2
target_mode = 2
source = "Original"
translation = "Original"
speaker = "narrator"
context = "Synthetic scene."
status = "draft"
'''
    )

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)
    [token] = catalog.tokens
    token_initializers = tuple((token, item) for item in token.initializers)
    original = GMFile.from_bytes(source)
    translated_name = _runtime_token_bytes("Hiroko")
    translated_initializer = b"\x45\x0e\xe0\x00\xff\x01" + translated_name + b"\x00\x00"
    compiled = GMFile.from_bytes(
        struct.pack("<H", 2) + translated_initializer + assignment + text + b"\x00"
    )

    assert len(compiled.data) > len(source)
    assert translated_name + b"\x00\x00\x43\x0c\x20\x04" in compiled.data
    _verify_compiled_file(
        catalog.files[0],
        original,
        compiled,
        (),
        token_initializers,
    )


def test_schema_five_rejects_initializer_for_the_wrong_token_slot(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Original\x00\x00"
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 5
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[tokens]]
id = "name:dear-person"
source = "加奈子"
translation = "Kanako"
max_width = 6
initializers = [
  {{ file = "DISKA/SCENE.MES", offset = 0x0002, slot = 0x03f6 }},
]

[[entries]]
id = "scene-line"
file = "DISKA/SCENE.MES"
offset = 0x0002
source_mode = 2
target_mode = 2
source = "Original"
translation = "Translated"
speaker = "narrator"
context = "Synthetic scene."
status = "draft"
notes = "Keeps the catalog non-empty."
'''
    )

    with pytest.raises(TranslationError, match="renders name:older-sister"):
        TranslationCatalog.from_file(catalog_path)


def test_compiled_file_rejects_changed_interpolation_slot() -> None:
    prefix = b"\x45\x0e\xe0\x00\xff\x0c"
    suffix = b"\x00\x4b\x0e\xe0\x00\x00\x00\x00"
    original = GMFile.from_bytes(struct.pack("<H", 2) + prefix + b"\x04\x04" + suffix)
    compiled = GMFile.from_bytes(struct.pack("<H", 2) + prefix + b"\xf6\x03" + suffix)
    catalog_file = TranslationFile(
        "DISKA/SCENE.MES",
        "disk-a/SCENE.MES",
        hashlib.sha256(original.data).hexdigest(),
    )

    with pytest.raises(TranslationError, match="interpolation sequence changed"):
        _verify_compiled_file(catalog_file, original, compiled, ())


def test_one_canonical_entry_can_cover_several_physical_anchors(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Repeated\x00\x4a\x02Repeated\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = tmp_path / "catalog.toml"
    catalog_path.write_text(
        f'''version = 4
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{hashlib.sha256(source).hexdigest()}"

[[entries]]
id = "shared-line"
anchors = [
  {{ file = "DISKA/SCENE.MES", offset = 0x0002 }},
  {{ file = "DISKA/SCENE.MES", offset = 0x000d }},
]
source_mode = 2
target_mode = 2
source = "Repeated"
translation = "Shared"
speaker = "narrator"
context = "Synthetic repeated line."
status = "draft"
notes = "One canonical translation in two contexts."
'''
    )

    catalog = TranslationCatalog.from_file(catalog_path)
    catalog.verify_sources(source_dir)

    assert catalog.anchor_count == 2
    assert catalog.entries[0].anchors == (
        TranslationAnchor("DISKA/SCENE.MES", 2),
        TranslationAnchor("DISKA/SCENE.MES", 13),
    )
