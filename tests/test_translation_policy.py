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
        ("DISKA/F0001.MES", 0x0799): (
            "For this mission, I've also been granted Time Patrol authority."
        ),
        ("DISKA/F0001.MES", 0x221B): "[CONNIE] (Time Quake system: nominal.)",
        ("DISKA/F0003.MES", 0x1E44): (
            "[CONNIE] (A still-developing organism. Human. Child. Female... "
            "About sixteen years old.)"
        ),
        ("DISKB/F0006.MES", 0x0B51): (
            "On my third birthday (about sixteen in human terms), Dr. Kanzaki "
            "gave me cologne and lipstick."
        ),
        ("DISKB/F0009.MES", 0x1DC1): (
            "Looking at her like this, she really does look younger than her age..."
        ),
        ("DISKB/F0010L.MES", 0x2031): (
            '[CONNIE] "In human terms, about seventeen. But I\'m a mutant, '
            'so I\'ve only been alive for three years."'
        ),
        ("DISKC/F0030.MES", 0x141F): (
            "[CONNIE] (Anesthetic... a tranquilizer gun...?)"
        ),
        ("DISKC/F0030.MES", 0x1438): (
            "I used a capture gun to hunt mutants. This is the same smell."
        ),
        ("DISKD/F0039.MES", 0x16CB): (
            "Knowing it's a tranquilizer gun, I tense every muscle to leap at her."
        ),
        ("DISKD/F0039.MES", 0x2499): "[CONNIE] (Cryo... sleep...!!!)",
        ("DISKD/F0040.MES", 0x403F): (
            '[DOCTOR] "⟦name:dear-person⟧, you\'ve been in '
            'cryosleep--suspended animation--since 1996..."'
        ),
        ("DISKD/F0040.MES", 0x4093): (
            '[DOCTOR] "You were set to awaken in an era whose technology '
            'could perform your operation."'
        ),
        ("DISKD/F0040.MES", 0x40C8): (
            '[DOCTOR] "That year is now--2288... You\'re in a world... '
            'about 280 years after you fell asleep."'
        ),
        ("DISKD/F0041.MES", 0x0F95): (
            '[KANZAKI] "Why hesitate? You also bear the duties of a temporal inspector. '
            'Arrest those who used time travel unlawfully."'
        ),
        ("DISKD/F0042.MES", 0x1BF7): (
            "Kaori Kanzaki and Marie Procyon analyze the genetic material they brought back,"
        ),
        ("DISKD/F0042.MES", 0x1EB5): "Dear Connie Kanzaki,",
    }
    for anchor, expected in exact_anchors.items():
        assert by_anchor[anchor].translation == expected, anchor

    assert "⟦name:friend-2⟧ Nanase" in by_anchor[
        ("DISKB/F0019.MES", 0x067B)
    ].translation
    assert "⟦name:friend-1⟧ Hayami" in by_anchor[
        ("DISKC/F0025R.MES", 0x131A)
    ].translation

    terminal_locks = {
        "opening-terminal-fermion-status-label": " STATUS ",
        "opening-terminal-fermion-status": " NOMINAL",
        "opening-terminal-instruments-nominal": "All instruments nominal.",
        "opening-terminal-shutdown-heading": "-- SYSTEM SHUTDOWN --",
        "opening-terminal-power-off": "SYSTEM POWER OFF",
    }
    for entry_id, expected in terminal_locks.items():
        assert by_id[entry_id].translation == expected, entry_id

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

    for item in items:
        if "時空震動" in item.source and item.speaker in {"Connie", "コニー"}:
            assert "space-time oscillation" not in item.translation.lower(), item.id

    locked_terms = {
        "時空トンネル": "time tunnel",
        "タイムパトロール": "Time Patrol",
        "時空監察官": "temporal inspector",
        "パラサイト銃": "capture gun",
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
    )
    for item in items:
        metadata = f"{item.context}\n{item.notes}".lower()
        for phrase in forbidden_metadata:
            assert phrase not in metadata, f"{item.id}: {phrase}"

        token_initial_dash = re.match(r"^⟦[^⟧]+⟧[^\n]*--I\b", item.translation)
        assert token_initial_dash is None, f"{item.id}: token-initial dash workaround"
