from __future__ import annotations

import hashlib
import struct
from pathlib import Path

import pytest

from fermion.gm import GMFile
from fermion.translation import (
    _LATIN_EDITOR_CELLS,
    PhysicalTranslation,
    TranslationAnchor,
    TranslationCatalog,
    TranslationEntry,
    TranslationError,
    TranslationFile,
    TranslationScene,
    _latin_editor_row,
    _patch_editor_latin_source,
    _patch_gm_source,
    _patch_token_initializer_source,
    _runtime_glyph_word,
    _runtime_token_bytes,
    _verify_compiled_file,
    _wrap_text,
)


@pytest.mark.parametrize(
    (
        "filename",
        "roles",
        "draw_label",
        "mapping_label",
        "special_label",
        "source_limit",
        "target_limit",
        "save_base",
        "save_length",
        "destinations",
    ),
    (
        (
            "NAME.MES",
            5,
            8889,
            14673,
            16675,
            5,
            6,
            1000,
            35,
            (1000, 1014, 1028, 1042, 1056),
        ),
        ("MONO.MES", 2, 7751, 13535, 15537, 6, 7, 1070, 16, (1070, 1086)),
    ),
)
def test_editor_latin_patch_reuses_free_form_storage_and_control_flow(
    filename: str,
    roles: int,
    draw_label: int,
    mapping_label: int,
    special_label: int,
    source_limit: int,
    target_limit: int,
    save_base: int,
    save_length: int,
    destinations: tuple[int, ...],
) -> None:
    role_transitions = "\n".join(
        f"(assign (ref 11 3013) {role})\n(assign (ref 12 1244) 2)" for role in range(1, roles + 1)
    )
    storage = "\n".join(
        f"(assign (ref 12 {destination}) (string-value (ref 14 160)))"
        for destination in destinations
    )
    source = f"""prefix
(file-load-range 0 (ref 12 {save_base}) {save_length})
{role_transitions}
(for-start 9 (local-address 3026) (== (ref 12 1244) 3))
(assign (ref 12 1244) 2)
(assign (ref 12 1244) 2)
(for-start 17 (local-address 3520) (> (ref 11 3012) {source_limit}))
(next)
(for-start 18 (local-address 5285) (== (ref 12 1244) 4))
{storage}
(file-save-range 0 (ref 12 {save_base}) {save_length})
(label {mapping_label})
(assign (ref 12 1274) 41090)
(return)
(label {special_label})
(return)
suffix
"""

    patched = _patch_editor_latin_source(source, filename)

    assert patched.count(f"(call (local-address {draw_label}))") == roles
    assert patched.count("(assign (ref 12 1246) 1)") == roles
    assert patched.count("(assign (ref 11 3011) 1)") == roles
    assert patched.count("(assign (ref 12 1244) 3)") == roles
    assert patched.count("(assign (ref 12 1244) 1)") == 2
    assert f"(> (ref 11 3012) {source_limit})" not in patched
    assert f"(> (ref 11 3012) {target_limit})" in patched
    assert f"(label {mapping_label})" in patched
    assert f"(label {special_label})" in patched
    assert f"(assign (ref 12 1274) {_runtime_glyph_word('A')})" in patched
    assert f"(assign (ref 12 1274) {_runtime_glyph_word('z')})" in patched
    assert "(case (local-address" in patched
    assert "(assign (ref 12 1274) 2)" in patched
    assert "(assign (ref 12 1274) 1)" in patched
    assert "(assign (ref 12 1274) 0)" in patched
    assert "(label 60002)\n (next)\n (label 60001)" in patched
    assert f"(label 60000)\n (next)\n (return)\n (label {special_label})" in patched


def test_latin_editor_palette_matches_fullwidth_mapping() -> None:
    assert len(_LATIN_EDITOR_CELLS) == 54
    assert _latin_editor_row(176) == "ＡＢＣＤＥ　ＦＧＨＩＪ　　　　　　"
    assert _latin_editor_row(208) == "ＵＶＷＸＹ　Ｚ　　　　　　　　　　"
    assert _latin_editor_row(240) == "ａｂｃｄｅ　ｆｇｈｉｊ　　　　　　"
    assert _latin_editor_row(272) == "ｐｑｒｓｔ　ｕｖｗｘｙ　ｚ－＇　　"
    assert _latin_editor_row(336) == "　　　　　　　　　"
    for _x, _y, character in _LATIN_EDITOR_CELLS:
        assert _runtime_glyph_word(character) == int.from_bytes(
            _runtime_token_bytes(character), "little"
        )


def test_catalog_editor_palette_matches_generated_rows() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    physical = {
        (entry.anchor.file, entry.anchor.offset): entry for entry in catalog.physical_translations()
    }
    layouts = {
        "NAME.MES": (
            0x22D8,
            0x22FA,
            0x231C,
            0x233E,
            0x2360,
            0x2382,
            0x23A4,
            0x23E8,
            0x240A,
            0x242C,
            0x244E,
        ),
        "MONO.MES": (
            0x1E66,
            0x1E88,
            0x1EAA,
            0x1ECC,
            0x1EEE,
            0x1F10,
            0x1F32,
            0x1F76,
            0x1F98,
            0x1FBA,
            0x1FDC,
        ),
    }
    rows = (176, 192, 208, 224, 240, 256, 272, 288, 304, 320, 336)
    for filename, offsets in layouts.items():
        for archive in ("DISKA", "DISKB"):
            for y, offset in zip(rows, offsets, strict=True):
                entry = physical[(f"{archive}/{filename}", offset)]
                assert entry.target_mode == 1
                assert entry.translation == _latin_editor_row(y)


def test_runtime_token_bytes_are_fullwidth_cp932() -> None:
    assert _runtime_token_bytes("Hiroko") == "Ｈｉｒｏｋｏ".encode("cp932")


def write_token_catalog(
    tmp_path,
    *,
    token_id: str = "name:mother",
    translation: str = "Yuki",
    presets: tuple[str, ...] | None = None,
):
    preset_line = ""
    if presets is not None:
        encoded = ", ".join(f'"{preset}"' for preset in presets)
        preset_line = f"presets = [{encoded}]\n"
    catalog_path = tmp_path / "token-catalog.toml"
    catalog_path.write_text(
        f'''version = 5
game = "Test"

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{"0" * 64}"

[[tokens]]
id = "{token_id}"
source = "由貴"
translation = "{translation}"
{preset_line}
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
'''
    )
    return catalog_path


def test_catalog_derives_token_display_width_from_runtime_encoding(tmp_path) -> None:
    catalog_path = write_token_catalog(tmp_path)

    [token] = TranslationCatalog.from_file(catalog_path).tokens

    assert token.max_width == 8


def test_catalog_rejects_token_default_exceeding_runtime_slot(tmp_path) -> None:
    catalog_path = write_token_catalog(tmp_path, translation="Bartholomew")

    with pytest.raises(TranslationError, match="exceeds the 14-byte runtime slot"):
        TranslationCatalog.from_file(catalog_path)


def test_catalog_rejects_invented_token_presets(tmp_path) -> None:
    catalog_path = write_token_catalog(tmp_path, presets=("Yuki", "May"))

    with pytest.raises(TranslationError, match="runtime editors are free-form"):
        TranslationCatalog.from_file(catalog_path)


def test_wrap_text_preserves_whitespace_only_layout_records() -> None:
    assert _wrap_text("  ", 61) == ("  ",)


def test_wrap_text_preserves_authored_trailing_newline() -> None:
    assert _wrap_text("First record.\n", 61) == ("First record.", "")


def write_catalog(
    tmp_path,
    source_hash: str,
    *,
    version: int = 4,
    source: str = "Original",
    translation: str = "Hello world",
    source_mode: int = 2,
    target_mode: int = 2,
    speaker: str = "narrator",
    attribution: str | None = None,
    scene_id: str | None = None,
    scene_context: str = "Synthetic scene.",
    status: str = "draft",
    file_box_width: int | None = None,
    file_box_rows: int | None = None,
    file_wrap_mode: str | None = None,
    entry_box_width: int | None = 8,
    entry_box_rows: int | None = None,
    entry_wrap_mode: str | None = None,
    notes: str | None = "A useful note.",
):
    catalog = tmp_path / "catalog.toml"
    file_width = f"box_width = {file_box_width}\n" if file_box_width is not None else ""
    file_rows = f"box_rows = {file_box_rows}\n" if file_box_rows is not None else ""
    file_wrap = f'wrap_mode = "{file_wrap_mode}"\n' if file_wrap_mode is not None else ""
    entry_width = f"box_width = {entry_box_width}\n" if entry_box_width is not None else ""
    entry_rows = f"box_rows = {entry_box_rows}\n" if entry_box_rows is not None else ""
    entry_wrap = f'wrap_mode = "{entry_wrap_mode}"\n' if entry_wrap_mode is not None else ""
    entry_notes = f'notes = "{notes}"\n' if notes is not None else ""
    entry_attribution = (
        f'attribution = "{attribution}"\n' if attribution is not None else ""
    )
    scene_table = (
        f'''\n[[scenes]]
id = "{scene_id}"
context = "{scene_context}"
'''
        if scene_id is not None
        else ""
    )
    entry_scene = (
        f'scene = "{scene_id}"\n'
        if scene_id is not None
        else 'context = "Synthetic scene."\n'
    )
    catalog.write_text(
        f'''version = {version}
game = "Test"
{scene_table}

[[files]]
file = "DISKA/SCENE.MES"
source = "disk-a/SCENE.MES"
sha256 = "{source_hash}"
{file_width}{file_rows}{file_wrap}

[[entries]]
id = "scene-0001"
file = "DISKA/SCENE.MES"
offset = 0x0002
source_mode = {source_mode}
target_mode = {target_mode}
source = "{source}"
translation = "{translation}"
speaker = "{speaker}"
{entry_attribution}{entry_scene}
status = "{status}"
{entry_width}{entry_rows}{entry_wrap}{entry_notes}
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
    assert (entry.speaker, entry.attribution, entry.context) == (
        "narrator",
        "inferred",
        "Synthetic scene.",
    )
    assert entry.anchors == (TranslationAnchor("DISKA/SCENE.MES", 2),)
    [catalog_file] = catalog.files
    assert (catalog_file.archive, catalog_file.name) == ("DISKA", "SCENE.MES")


def test_notes_may_be_omitted_from_simple_entry(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Original\x00\x00"
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest(), notes=None)

    catalog = TranslationCatalog.from_file(catalog_path)

    assert catalog.entries[0].notes == ""


@pytest.mark.parametrize(
    "status",
    ("draft", "translated", "reviewed", "runtime-verified"),
)
def test_accepts_defined_translation_statuses(tmp_path, status: str) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, status=status)

    [entry] = TranslationCatalog.from_file(catalog_path).entries

    assert entry.status == status


def test_rejects_ambiguous_legacy_translation_status(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, status="qa-ready")

    with pytest.raises(TranslationError, match="status must be one of"):
        TranslationCatalog.from_file(catalog_path)


def test_pure_silence_uses_fixed_ascii_ellipsis(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        source="・・・・・・・・。",
        translation="...",
    )

    [entry] = TranslationCatalog.from_file(catalog_path).entries

    assert entry.translation == "..."


def test_rejects_variable_length_pure_silence(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        source="・・・・・・・・。",
        translation="........",
    )

    with pytest.raises(TranslationError, match=r"pure silent beat as '\.\.\.'"):
        TranslationCatalog.from_file(catalog_path)


def test_terminal_progress_glyph_is_not_treated_as_story_silence(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, source="・", translation=".")

    [entry] = TranslationCatalog.from_file(catalog_path).entries

    assert entry.translation == "."


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


def test_file_row_limit_is_the_validation_default(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        translation="one two three",
        file_box_width=5,
        file_box_rows=3,
        entry_box_width=None,
    )

    catalog = TranslationCatalog.from_file(catalog_path)

    [catalog_file] = catalog.files
    assert (catalog_file.box_width, catalog_file.box_rows) == (5, 3)


def test_rejects_translation_exceeding_effective_row_limit(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        translation="one two three four",
        file_box_width=5,
        file_box_rows=3,
        entry_box_width=None,
    )

    with pytest.raises(TranslationError, match="needs 4 rows, but the box allows 3"):
        TranslationCatalog.from_file(catalog_path)


def test_character_wrap_validates_narrow_vertical_surface(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        translation="Eight letters",
        entry_box_width=2,
        entry_box_rows=7,
        entry_wrap_mode="characters",
    )

    [entry] = TranslationCatalog.from_file(catalog_path).entries

    assert entry.compiled_translation() == "Ei\ngh\nt\nle\ntt\ner\ns"


def test_file_character_wrap_is_the_compile_default(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        translation="Eight letters",
        file_box_width=2,
        file_box_rows=7,
        file_wrap_mode="characters",
        entry_box_width=None,
    )

    catalog = TranslationCatalog.from_file(catalog_path)

    [physical] = catalog.physical_translations(compiled=True)
    assert physical.translation == "Ei\ngh\nt\nle\ntt\ner\ns"


def test_rejects_unknown_wrap_mode(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        entry_wrap_mode="columns",
    )

    with pytest.raises(TranslationError, match="wrap_mode must be one of"):
        TranslationCatalog.from_file(catalog_path)


def test_rejects_nonpositive_row_limit(tmp_path) -> None:
    catalog_path = write_catalog(tmp_path, "0" * 64, entry_box_rows=0)

    with pytest.raises(TranslationError, match="box_rows must be a positive integer"):
        TranslationCatalog.from_file(catalog_path)


def test_rejects_changed_source_anchor(tmp_path) -> None:
    source = struct.pack("<H", 2) + b"\x4a\x02Changed\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(tmp_path, hashlib.sha256(source).hexdigest())

    with pytest.raises(TranslationError, match="source text changed"):
        TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)


def test_schema_six_verifies_proven_canonical_speaker(tmp_path) -> None:
    japanese = "【コニー】「はい。」"
    source = struct.pack("<H", 2) + b"\x4a\x01" + japanese.encode("cp932") + b"\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(
        tmp_path,
        hashlib.sha256(source).hexdigest(),
        version=6,
        source=japanese,
        translation="[Connie] Yes.",
        source_mode=1,
        speaker="connie",
        attribution="proven",
        entry_box_width=61,
    )

    [entry] = TranslationCatalog.from_file(catalog_path).entries
    TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)

    assert (entry.speaker, entry.attribution) == ("connie", "proven")


def test_schema_six_rejects_proven_speaker_mismatch(tmp_path) -> None:
    japanese = "【コニー】「はい。」"
    source = struct.pack("<H", 2) + b"\x4a\x01" + japanese.encode("cp932") + b"\x00\x00"
    source_dir = tmp_path / "source"
    (source_dir / "disk-a").mkdir(parents=True)
    (source_dir / "disk-a" / "SCENE.MES").write_bytes(source)
    catalog_path = write_catalog(
        tmp_path,
        hashlib.sha256(source).hexdigest(),
        version=6,
        source=japanese,
        translation="[Kanzaki] Yes.",
        source_mode=1,
        speaker="kanzaki",
        attribution="proven",
        entry_box_width=61,
    )

    with pytest.raises(TranslationError, match="encoded speaker.*connie.*kanzaki"):
        TranslationCatalog.from_file(catalog_path).verify_sources(source_dir)


def test_schema_six_requires_attribution(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=6,
        speaker="narrator",
    )

    with pytest.raises(TranslationError, match="attribution must be a non-empty string"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_six_requires_canonical_speaker_id(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=6,
        speaker="コニー",
        attribution="proven",
    )

    with pytest.raises(TranslationError, match="canonical lowercase speaker ID"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_seven_resolves_shared_scene_context(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=7,
        speaker="narrator",
        attribution="inferred",
        scene_id="synthetic-scene",
    )

    catalog = TranslationCatalog.from_file(catalog_path)

    assert catalog.scenes == (TranslationScene("synthetic-scene", "Synthetic scene."),)
    [entry] = catalog.entries
    assert (entry.scene, entry.context) == ("synthetic-scene", "Synthetic scene.")


def test_schema_seven_requires_scene_catalog(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=7,
        speaker="narrator",
        attribution="inferred",
    )

    with pytest.raises(TranslationError, match=r"must contain \[\[scenes\]\]"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_seven_rejects_unknown_entry_scene(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=7,
        speaker="narrator",
        attribution="inferred",
        scene_id="synthetic-scene",
    )
    catalog_path.write_text(
        catalog_path.read_text().replace(
            'scene = "synthetic-scene"',
            'scene = "missing-scene"',
        )
    )

    with pytest.raises(TranslationError, match="references unknown scene"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_seven_rejects_entry_context_copy(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=7,
        speaker="narrator",
        attribution="inferred",
        scene_id="synthetic-scene",
    )
    catalog_path.write_text(
        catalog_path.read_text().replace(
            'scene = "synthetic-scene"',
            'scene = "synthetic-scene"\ncontext = "Duplicated context."',
        )
    )

    with pytest.raises(TranslationError, match="context must be stored once"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_seven_rejects_duplicate_scene_context(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=7,
        speaker="narrator",
        attribution="inferred",
        scene_id="synthetic-scene",
    )
    catalog_path.write_text(
        catalog_path.read_text()
        + '''
[[scenes]]
id = "duplicate-context"
context = "Synthetic scene."
'''
    )

    with pytest.raises(TranslationError, match="duplicate scene contexts"):
        TranslationCatalog.from_file(catalog_path)


def test_schema_seven_rejects_unused_scene(tmp_path) -> None:
    catalog_path = write_catalog(
        tmp_path,
        "0" * 64,
        version=7,
        speaker="narrator",
        attribution="inferred",
        scene_id="synthetic-scene",
    )
    catalog_path.write_text(
        catalog_path.read_text()
        + '''
[[scenes]]
id = "unused-scene"
context = "An unused scene."
'''
    )

    with pytest.raises(TranslationError, match="contains unused scenes: unused-scene"):
        TranslationCatalog.from_file(catalog_path)


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
        attribution="inferred",
        scene="",
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
box_width = 14

[[tokens]]
id = "name:dear-person"
source = "加奈子"
translation = "Kanako"

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
