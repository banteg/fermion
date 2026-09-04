import re
from pathlib import Path

from fermion.translation import TranslationCatalog


def test_locked_translation_policy_contracts() -> None:
    catalog_path = Path(__file__).parents[1] / "translations" / "fermion.toml"
    catalog = TranslationCatalog.from_file(catalog_path)
    items = (*catalog.entries, *catalog.composites)
    by_id = {item.id: item for item in items}
    by_anchor = {
        (anchor.file, anchor.offset): item for item in items for anchor in item.anchors
    }

    exact_anchors = {
        ("DISKA/F0000.MES", 0x0645): (
            "I couldn't go against her. I couldn't refuse Dr. Kanzaki's request."
        ),
        ("DISKA/F0001.MES", 0x0799): (
            "For this mission, I've also been granted Time Patrol authority."
        ),
        ("DISKA/F0001.MES", 0x221B): "[Connie] (Space-time oscillation system: running smoothly.)",
        ("DISKA/F0003.MES", 0x1E44): (
            "[Connie] (A still-developing organism. Human. Child. Female... "
            "About sixteen years old.)"
        ),
        ("DISKB/F0006.MES", 0x0B51): (
            "On my third birthday (about sixteen in human terms), Dr. Kanzaki "
            "gave me cologne and lipstick."
        ),
        ("DISKB/F0007.MES", 0x3A88): (
            '[⟦name:mother⟧] "I-- ah! Aahhhhhhh!"'
        ),
        ("DISKB/F0009.MES", 0x1DC1): (
            "Looking at her like this, she really does look younger than her age..."
        ),
        ("DISKB/F0009.MES", 0x1E15): (
            '[⟦name:dear-person⟧] "Connie... haaah..."'
        ),
        ("DISKB/F0010L.MES", 0x2031): (
            '[Connie] "In human terms, about seventeen. But I\'m a mutant, '
            'so I\'ve only been alive for three years."'
        ),
        ("DISKB/F0010R.MES", 0x11A6): (
            '[Connie] "Miss ⟦name:mother⟧... you\'re very forward..."'
        ),
        ("DISKB/F0010R.MES", 0x11D1): (
            '[⟦name:mother⟧] "Just ⟦name:mother⟧... I\'m surprised myself '
            'that having you touch me gets me this excited..."'
        ),
        ("DISKC/F0020.MES", 0x16FB): (
            '[Connie] "⟦name:dear-person⟧... You\'re so sen-si-tive too..."'
        ),
        ("DISKC/F0030.MES", 0x141F): (
            "[Connie] (Anesthetic... a tranquilizer gun...?)"
        ),
        ("DISKC/F0030.MES", 0x1438): (
            "I used a parasite gun to capture mutants. This is the same smell."
        ),
        ("DISKD/F003410.MES", 0x1077): (
            "[Connie] (It was definitely this room... This room...)"
        ),
        ("DISKD/F0039.MES", 0x16CB): (
            "Knowing it's a tranquilizer gun, I tense every muscle to leap at her."
        ),
        ("DISKD/F0039.MES", 0x2499): "[Connie] (Cryo... sleep...!!!)",
        ("DISKD/F0040.MES", 0x403F): (
            '[Doctor] "⟦name:dear-person⟧, you\'ve been in '
            'cryosleep--suspended animation--since 1996..."'
        ),
        ("DISKD/F0040.MES", 0x4093): (
            '[Doctor] "You were set to awaken in an era whose technology '
            'could perform your operation."'
        ),
        ("DISKD/F0040.MES", 0x40C8): (
            '[Doctor] "That year is now--2288... You\'re in a world... '
            'about 280 years after you fell asleep."'
        ),
        ("DISKD/F0041.MES", 0x0F95): (
            '[Kanzaki] "Why hesitate? You also bear the duties of a temporal inspector. '
            'Arrest those who used time travel unlawfully."'
        ),
        ("DISKD/F0042.MES", 0x1BF7): (
            "Kaori Kanzaki and Marie Procyon analyze the genetic material they brought back,"
        ),
        ("DISKD/F0042.MES", 0x1EB5): "Dear Connie Kanzaki,",
    }
    for anchor, expected in exact_anchors.items():
        assert by_anchor[anchor].translation == expected, anchor

    exact_ids = {
        "f0007-0b7f-an-image-of-name-holding-a-girl-who": (
            "⟦name:mother⟧... an image of her holding a girl who looks just "
            "like ⟦name:mother⟧."
        ),
        "f0007-0c13-it-is-an-image-of-name-holding-her": (
            "⟦name:mother⟧... an image of her holding her younger sister."
        ),
    }
    for item_id, expected in exact_ids.items():
        assert by_id[item_id].translation == expected, item_id

    fixed_speaker_tags = set()
    dynamic_speaker_tags = set()
    for item in items:
        source_tag = re.match(r"^【([^】]+)】[「（]", item.source)
        if source_tag is None:
            continue
        translated_tag = re.match(r"^\[([^]\n]+)\]", item.translation)
        assert translated_tag is not None, item.id
        tag = translated_tag.group(1)
        if tag.startswith("⟦name:"):
            dynamic_speaker_tags.add(tag)
        else:
            fixed_speaker_tags.add(tag)

    assert fixed_speaker_tags == {
        "Butterfly",
        "Connie",
        "Doctor",
        "Girl",
        "Kanzaki",
        "Marie",
        "Marna",
        "Miki",
        "Nanase",
        "Nurse",
        "Operator",
        "Remia",
        "Teacher",
        "Ventilation System",
        "Woman",
        "Woman's Voice",
        "Yoshimi",
    }
    assert dynamic_speaker_tags == {
        "⟦name:dear-person⟧",
        "⟦name:friend-1⟧",
        "⟦name:friend-2⟧",
        "⟦name:mother⟧",
        "⟦name:older-sister⟧",
    }

    assert "⟦name:friend-2⟧ Nanase" in by_anchor[
        ("DISKB/F0019.MES", 0x067B)
    ].translation
    assert "⟦name:friend-1⟧ Hayami" in by_anchor[
        ("DISKC/F0025R.MES", 0x131A)
    ].translation

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
    assert by_id["opening-terminal-target-progress-prefix"].translation == (
        "Target time input"
    )
    assert by_id["opening-terminal-target-entered"].translation == " complete."

    connie_kanzaki_entries = [
        item.id for item in items if "Connie Kanzaki" in item.translation
    ]
    assert connie_kanzaki_entries == ["f0042-1eb5-dear-connie-kanzaki"]

    cold_sleep_entries = [
        item
        for item in items
        if "コールド" in item.source and "スリープ" in item.source
    ]
    assert cold_sleep_entries
    for item in cold_sleep_entries:
        translation = item.translation.lower()
        assert "cold" not in translation, item.id
        assert "cryo" in translation and "sleep" in translation, item.id

    suspended_animation_entries = [item for item in items if "冷凍睡眠" in item.source]
    assert suspended_animation_entries
    for item in suspended_animation_entries:
        assert "suspended animation" in item.translation.lower(), item.id

    locked_terms = {
        "時空トンネル": "time tunnel",
        "タイムパトロール": "Time Patrol",
        "時空監察官": "temporal inspector",
        "パラサイト銃": "parasite gun",
        "麻酔銃": "tranquilizer gun",
        "対ミュータント用捕獲薬": "anti-mutant capture drug",
    }
    for source_term, english_term in locked_terms.items():
        matching = [item for item in items if source_term in item.source]
        assert matching, source_term
        for item in matching:
            assert english_term.lower() in item.translation.lower(), item.id

    forbidden_metadata = (
        "adult-aged",
        "adult dr. kanzaki",
        "adult experimental subject",
        "adult guard",
        "adult loved one",
        "adult marna",
        "adult mother",
        "adult mutant",
        "adult older sister",
        "adult patient",
        "adult sisters",
        "adult student",
        "adult woman",
        "adult women",
        "as separate evidence",
        "blanket consent",
        "coercively framed",
        "coercive sequence remains documented",
        "converted into a non-lexical cry",
        "does not convert",
        "does not reinterpret this as assent",
        "every spoken no",
        "freely given consent",
        "not an objective consent",
        "not softened into",
        "objective consent statement",
        "remain distinct in english",
        "remain explicit while",
        "remains an explicit no",
        "refusal remains literal",
        "refusals remain",
        "retroactively establish consent",
        "rewrite the preceding refusals",
        "treated as consent",
        "treated as free assent",
        "treating arousal as assent",
        "treating pleasure as assent",
        "turning the refusal into consent",
    )
    metadata_records = (
        *((item.id, f"{item.context}\n{item.notes}") for item in items),
        *((scene.id, scene.context) for scene in catalog.scenes),
    )
    for item_id, metadata in metadata_records:
        lowered = metadata.lower()
        for phrase in forbidden_metadata:
            assert phrase not in lowered, f"{item_id}: {phrase}"

    for item in items:
        token_initial_dash = re.match(r"^⟦[^⟧]+⟧[^\n]*--I\b", item.translation)
        assert token_initial_dash is None, f"{item.id}: token-initial dash workaround"


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
