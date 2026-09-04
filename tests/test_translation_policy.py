import re
from pathlib import Path

from fermion.translation import TranslationCatalog


def test_catalog_preserves_speaker_tags_and_original_terminal_english() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    items = (*catalog.entries, *catalog.composites)
    by_id = {item.id: item for item in items}
    by_anchor = {
        (anchor.file, anchor.offset): item for item in items for anchor in item.anchors
    }

    # Speaker labels and editable names are presentation structure. The prose
    # around them is reviewed against the Japanese, not frozen in this test.
    for item in items:
        source_tag = re.match(r"^【([^】]+)】[「（]", item.source)
        if source_tag is None:
            continue
        translated_tag = re.match(r"^\[([^]\n]+)\]", item.translation)
        assert translated_tag is not None, item.id
        if source_tag.group(1).startswith("⟦name:"):
            assert translated_tag.group(1) == source_tag.group(1), item.id

    # Original English is itself source material. Keep these exact checks,
    # including the full-width glyphs and separately timed terminal records.
    source_english_locks = {
        "opening-terminal-fermion-status-label": "　",
        "opening-terminal-fermion-status": "ＯＫ．",
        "opening-terminal-time-quake-i": "ｉ",
        "opening-terminal-time-quake-status": "ＯＫ．",
        "opening-terminal-all-systems-heading": "Ａｌｌ　ｓｙｓｔｅｍ",
        "opening-terminal-all-systems-status": "ＯＫ．",
        "opening-terminal-shutdown-heading": "・・Ｓｙｓｔｅｍ　Ｃｌｏｓｅ・・",
        "opening-terminal-power-off": "Ｓｙｓｔｅｍ　Ｐｏｗｅｒ　ｏｆｆ",
    }
    for entry_id, expected in source_english_locks.items():
        entry = by_id[entry_id]
        assert entry.target_mode == 1, entry_id
        assert entry.translation == entry.source == expected, entry_id

    target_heading_offsets = (
        0x0A87,
        0x0A91,
        0x0A9B,
        0x0AA5,
        0x0AB0,
        0x0ABA,
        0x0AC4,
        0x0ACE,
        0x0AD9,
        0x0AE3,
        0x0AED,
        0x0AF7,
        0x0B01,
        0x0B0B,
        0x0B15,
        0x0B1F,
        0x0B29,
        0x0B33,
        0x0B3D,
        0x0B47,
        0x0B51,
        0x0B5C,
        0x0B66,
        0x0B70,
        0x0B7A,
        0x0B84,
        0x0B8E,
        0x0B98,
        0x0BA2,
        0x0BAC,
    )
    target_heading = [
        by_anchor[("DISKA/FOP.MES", offset)] for offset in target_heading_offsets
    ]
    assert all(entry.target_mode == 1 for entry in target_heading)
    assert "".join(entry.translation for entry in target_heading) == (
        "Ｔａｒｇｅｔ　Ｄｉｍｅｎｔｉｏｎ　Ｓｐａｃｅ・・ｉｎｐｕｔ．"
    )
    assert all(entry.translation == entry.source for entry in target_heading)


def test_catalog_stays_within_declared_surface_limits() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    files = {item.file: item for item in catalog.files}
    tokens = {item.id: item for item in catalog.tokens}

    for entry in catalog.entries:
        layouts = {
            (
                entry.box_width
                if entry.box_width is not None
                else files[anchor.file].box_width,
                entry.box_rows
                if entry.box_rows is not None
                else files[anchor.file].box_rows,
                entry.wrap_mode
                if entry.wrap_mode is not None
                else files[anchor.file].wrap_mode,
            )
            for anchor in entry.anchors
        }
        for width, row_limit, wrap_mode in layouts:
            if width is None:
                continue
            assert row_limit is not None, f"{entry.id}: missing row limit"
            rows = entry.wrapped_translation_for(width, wrap_mode)
            assert len(rows) <= row_limit, (
                f"{entry.id}: {len(rows)} rows exceeds {row_limit}"
            )

    for entry in catalog.composites:
        layouts = {
            (
                entry.box_width
                if entry.box_width is not None
                else files[occurrence.file].box_width,
                entry.box_rows
                if entry.box_rows is not None
                else files[occurrence.file].box_rows,
                entry.wrap_mode
                if entry.wrap_mode is not None
                else files[occurrence.file].wrap_mode,
            )
            for occurrence in entry.occurrences
        }
        for width, row_limit, wrap_mode in layouts:
            if width is None:
                continue
            assert row_limit is not None, f"{entry.id}: missing row limit"
            wrapped = entry.compiled_translation(width, tokens, wrap_mode)
            rows = wrapped.split("\n")
            assert len(rows) <= row_limit, (
                f"{entry.id}: {len(rows)} rows exceeds {row_limit}"
            )


def test_silky_vertical_card_uses_character_cells() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    by_anchor = {
        (anchor.file, anchor.offset): entry
        for entry in catalog.entries
        for anchor in entry.anchors
    }

    koi_offsets = (
        0x195F,
        0x1995,
        0x19CA,
        0x1A07,
        0x1A60,
        0x1A85,
        0x1ADE,
        0x1B0A,
        0x1B62,
        0x1B90,
        0x1BC6,
        0x1C19,
        0x1C4D,
        0x1C7A,
    )
    for offset in koi_offsets:
        entry = by_anchor[("DISKA/SILK.MES", offset)]
        assert (entry.box_width, entry.box_rows, entry.wrap_mode) == (
            2,
            24,
            "characters",
        )


def test_adjacent_silky_records_fit_their_shared_windows() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    files = {item.file: item for item in catalog.files}
    by_anchor = {
        (anchor.file, anchor.offset): entry
        for entry in catalog.entries
        for anchor in entry.anchors
    }
    file = "DISKA/SILK.MES"

    # These text opcodes share a window without an intervening message end.
    # The limits come from the corresponding text-window instructions in
    # SILK.MES; a newline on an earlier record deliberately advances the next
    # record to a fresh row.
    surface_sequences = (
        (2, (0x0CEE, 0x0D14)),
        (2, (0x0D2E, 0x0D46)),
        (2, (0x0D8B, 0x0DA9)),
        (2, (0x0DD0, 0x0DEC)),
        (3, (0x1153, 0x1196)),
        (3, (0x129F, 0x12B7)),
        (3, (0x12DB, 0x12ED)),
        (3, (0x130D, 0x1329, 0x133F)),
        (3, (0x1401, 0x1440)),
        (3, (0x1486, 0x14A4, 0x14C9)),
        (3, (0x14E6, 0x14FE, 0x1516)),
        (3, (0x1526, 0x1542)),
        (3, (0x1562, 0x157E)),
        (2, (0x1846, 0x185E)),
        (2, (0x1D81, 0x1D8E)),
        (2, (0x1DB2, 0x1DD7)),
        (2, (0x1DFD, 0x1E14)),
        (2, (0x1E30, 0x1E53)),
        (4, (0x2048, 0x2074)),
        (4, (0x20BE, 0x20D6, 0x20F2)),
        (3, (0x21B2, 0x21CB)),
        (3, (0x21F5, 0x220F)),
        (3, (0x22A1, 0x22BD)),
        (3, (0x22E9, 0x231B)),
        (3, (0x2333, 0x234B, 0x2369)),
    )

    for row_limit, offsets in surface_sequences:
        rendered = "".join(
            by_anchor[(file, offset)].compiled_translation(
                files[file].box_width,
                files[file].wrap_mode,
            )
            for offset in offsets
        ).rstrip("\n")
        rows = rendered.split("\n") if rendered else [""]
        assert len(rows) <= row_limit, (
            f"SILK.MES {', '.join(f'0x{offset:04x}' for offset in offsets)}: "
            f"{len(rows)} rows exceeds {row_limit}"
        )
