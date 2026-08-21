from fermion.cli import build_parser
from fermion.drift import analyze_translation_drift
from fermion.translation import (
    TranslationAnchor,
    TranslationCatalog,
    TranslationEntry,
    TranslationFile,
)


def _entry(file: str, offset: int, translation: str) -> TranslationEntry:
    return TranslationEntry(
        id=f"{file}-{offset}",
        anchors=(TranslationAnchor(file, offset),),
        source_mode=1,
        target_mode=2,
        source="原文",
        translation=translation,
        speaker="Connie",
        attribution="inferred",
        context="Synthetic drift corpus.",
        status="translated",
        notes="",
    )


def _catalog(files: tuple[str, ...], entries: tuple[TranslationEntry, ...]) -> TranslationCatalog:
    catalog_files = tuple(
        TranslationFile(file, f"source/{file.replace('/', '-')}", "0" * 64)
        for file in files
    )
    return TranslationCatalog(5, "Test", catalog_files, (), entries, ())


def test_drift_flags_stiff_outlier_against_same_speaker_baseline() -> None:
    files = tuple(f"DISKA/F000{index}.MES" for index in range(1, 5))
    entries = []
    for file in files[:3]:
        entries.extend(
            _entry(file, index, '[CONNIE] "I don\'t know. I\'m ready."')
            for index in range(10)
        )
    entries.extend(
        _entry(files[3], index, '[CONNIE] "I do not know. I am ready."')
        for index in range(10)
    )

    rows = analyze_translation_drift(_catalog(files, tuple(entries)))
    by_file = {row.file: row for row in rows}

    natural = by_file[files[0]]
    assert natural.contraction_rate == 100
    assert natural.stiff_form_rate == 0
    assert natural.top_openings == (("i don't", 10),)
    assert natural.flags == ()

    stiff = by_file[files[3]]
    assert stiff.contraction_rate == 0
    assert stiff.stiff_form_rate == 100
    assert "contractions-low" in stiff.flags
    assert "stiff-forms-high" in stiff.flags


def test_drift_counts_canonical_record_once_per_file() -> None:
    files = ("DISKA/F0001.MES", "DISKA/F0002.MES")
    entry = _entry(files[0], 2, "I know the answer.")
    entry = TranslationEntry(
        id=entry.id,
        anchors=(
            TranslationAnchor(files[0], 2),
            TranslationAnchor(files[0], 20),
            TranslationAnchor(files[1], 2),
        ),
        source_mode=entry.source_mode,
        target_mode=entry.target_mode,
        source=entry.source,
        translation=entry.translation,
        speaker=entry.speaker,
        attribution=entry.attribution,
        context=entry.context,
        status=entry.status,
        notes=entry.notes,
    )

    rows = analyze_translation_drift(_catalog(files, (entry,)), min_records=1)

    assert [(row.file, row.records) for row in rows] == [
        ("DISKA/F0001.MES", 1),
        ("DISKA/F0002.MES", 1),
    ]


def test_translation_drift_command_is_registered() -> None:
    args = build_parser().parse_args(
        ["translation", "drift", "translations/fermion.toml", "--only-flagged"]
    )

    assert args.translation_command == "drift"
    assert args.only_flagged is True
