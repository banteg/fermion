"""Corpus diagnostics for spotting translation-register drift."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import median

from fermion.translation import TranslationCatalog

_TOKEN_MARKER = re.compile(r"⟦(?:name|term):[a-z0-9]+(?:-[a-z0-9]+)*⟧")
_LEADING_SPEAKER = re.compile(r"^\s*\[[^]]+\]\s*")
_SENTENCE = re.compile(r"[^.!?]+(?:[.!?]+|$)")
_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_CONTRACTION = re.compile(
    r"\b(?:"
    r"i'm|you're|we're|they're|he's|she's|it's|that's|there's|what's|who's|"
    r"i've|you've|we've|they've|i'd|you'd|he'd|she'd|we'd|they'd|"
    r"i'll|you'll|he'll|she'll|it'll|we'll|they'll|"
    r"aren't|can't|couldn't|didn't|doesn't|don't|hadn't|hasn't|haven't|"
    r"isn't|mustn't|shouldn't|wasn't|weren't|won't|wouldn't|let's"
    r")\b",
    re.IGNORECASE,
)
_STIFF_FORM = re.compile(
    r"\b(?:"
    r"i am|you are|we are|they are|he is|she is|it is|that is|there is|"
    r"what is|who is|i have|you have|we have|they have|"
    r"i will|you will|we will|they will|he will|she will|it will|"
    r"am not|are not|is not|was not|were not|"
    r"do not|does not|did not|can not|cannot|could not|would not|"
    r"should not|will not|have not|has not|had not|must not"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TranslationDriftRow:
    """Register diagnostics for one catalog file and speaker."""

    file: str
    speaker: str
    records: int
    sentences: int
    contraction_rate: float
    stiff_form_rate: float
    mean_sentence_words: float
    repeated_opening_rate: float
    top_openings: tuple[tuple[str, int], ...]
    flags: tuple[str, ...] = ()


@dataclass
class _Accumulator:
    records: int = 0
    sentences: int = 0
    words: int = 0
    contractions: int = 0
    stiff_forms: int = 0
    openings: Counter[str] | None = None

    def __post_init__(self) -> None:
        if self.openings is None:
            self.openings = Counter()


def _clean_translation(text: str) -> str:
    without_label = _LEADING_SPEAKER.sub("", text)
    return _TOKEN_MARKER.sub("Name", without_label)


def _add_translation(accumulator: _Accumulator, text: str) -> None:
    clean = _clean_translation(text)
    words = _WORD.findall(clean)
    if not words:
        return
    sentence_words = [
        found
        for sentence in _SENTENCE.findall(clean)
        if (found := _WORD.findall(sentence))
    ]
    accumulator.records += 1
    accumulator.sentences += len(sentence_words)
    accumulator.words += sum(len(found) for found in sentence_words)
    accumulator.contractions += len(_CONTRACTION.findall(clean))
    accumulator.stiff_forms += len(_STIFF_FORM.findall(clean))
    opening = " ".join(word.casefold() for word in words[:2])
    assert accumulator.openings is not None
    accumulator.openings[opening] += 1


def _raw_drift_rows(catalog: TranslationCatalog) -> tuple[TranslationDriftRow, ...]:
    groups: dict[tuple[str, str], _Accumulator] = defaultdict(_Accumulator)
    for entry in catalog.entries:
        for file in {anchor.file for anchor in entry.anchors}:
            _add_translation(groups[(file, entry.speaker)], entry.translation)
    for entry in catalog.composites:
        for file in {occurrence.file for occurrence in entry.occurrences}:
            _add_translation(groups[(file, entry.speaker)], entry.translation)

    file_order = {file.file: index for index, file in enumerate(catalog.files)}
    rows = []
    for (file, speaker), accumulator in groups.items():
        if not accumulator.records or not accumulator.sentences:
            continue
        assert accumulator.openings is not None
        top_openings = tuple(
            (opening, count)
            for opening, count in accumulator.openings.most_common(3)
            if count > 1
        )
        repeated = top_openings[0][1] if top_openings else 0
        rows.append(
            TranslationDriftRow(
                file=file,
                speaker=speaker,
                records=accumulator.records,
                sentences=accumulator.sentences,
                contraction_rate=100 * accumulator.contractions / accumulator.sentences,
                stiff_form_rate=100 * accumulator.stiff_forms / accumulator.sentences,
                mean_sentence_words=accumulator.words / accumulator.sentences,
                repeated_opening_rate=100 * repeated / accumulator.records,
                top_openings=top_openings,
            )
        )
    rows.sort(key=lambda row: (file_order[row.file], row.speaker.casefold(), row.speaker))
    return tuple(rows)


def _outlier_direction(value: float, population: list[float], floor: float) -> int:
    center = median(population)
    deviations = [abs(item - center) for item in population]
    threshold = max(3 * median(deviations), floor)
    delta = value - center
    if not delta or abs(delta) < threshold:
        return 0
    return 1 if delta > 0 else -1


def analyze_translation_drift(
    catalog: TranslationCatalog,
    *,
    min_records: int = 10,
) -> tuple[TranslationDriftRow, ...]:
    """Measure per-file speaker register and flag robust corpus outliers.

    Baselines use the same speaker when at least three qualifying file groups
    exist, and otherwise fall back to all qualifying groups. Rates are counts
    per 100 sentences; repeated openings use the most common two-word opening.
    """
    if min_records < 1:
        raise ValueError("min_records must be positive")
    raw_rows = _raw_drift_rows(catalog)
    eligible = [row for row in raw_rows if row.records >= min_records]
    by_speaker: dict[str, list[TranslationDriftRow]] = defaultdict(list)
    for row in eligible:
        by_speaker[row.speaker].append(row)

    analyzed = []
    for row in raw_rows:
        flags: list[str] = []
        if row.records >= min_records and len(eligible) >= 3:
            baseline = by_speaker[row.speaker]
            if len(baseline) < 3:
                baseline = eligible
            metrics = (
                (
                    "contractions",
                    row.contraction_rate,
                    [item.contraction_rate for item in baseline],
                    5.0,
                    True,
                ),
                (
                    "stiff-forms",
                    row.stiff_form_rate,
                    [item.stiff_form_rate for item in baseline],
                    5.0,
                    True,
                ),
                (
                    "sentence-length",
                    row.mean_sentence_words,
                    [item.mean_sentence_words for item in baseline],
                    2.0,
                    True,
                ),
                (
                    "opening-repeat",
                    row.repeated_opening_rate,
                    [item.repeated_opening_rate for item in baseline],
                    15.0,
                    False,
                ),
            )
            for name, value, population, floor, flag_low in metrics:
                direction = _outlier_direction(value, population, floor)
                if direction > 0:
                    flags.append(f"{name}-high")
                elif direction < 0 and flag_low:
                    flags.append(f"{name}-low")
        analyzed.append(
            TranslationDriftRow(
                file=row.file,
                speaker=row.speaker,
                records=row.records,
                sentences=row.sentences,
                contraction_rate=row.contraction_rate,
                stiff_form_rate=row.stiff_form_rate,
                mean_sentence_words=row.mean_sentence_words,
                repeated_opening_rate=row.repeated_opening_rate,
                top_openings=row.top_openings,
                flags=tuple(flags),
            )
        )
    return tuple(analyzed)
