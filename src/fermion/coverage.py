"""Checked-in translation coverage scopes and duplicate-aware backlog reports."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path, PurePosixPath

from fermion.gm import GMError, GMFile
from fermion.translation import (
    TranslationAnchor,
    TranslationCatalog,
    TranslationError,
)


@dataclass(frozen=True)
class CoverageRange:
    file: str
    start: int
    end: int

    def contains(self, anchor: TranslationAnchor) -> bool:
        return anchor.file == self.file and self.start <= anchor.offset <= self.end


@dataclass(frozen=True)
class CoverageExclusion:
    id: str
    anchors: tuple[TranslationAnchor, ...]
    source_mode: int
    source: str
    reason: str


@dataclass(frozen=True)
class CoverageScope:
    id: str
    description: str
    ranges: tuple[CoverageRange, ...]
    exclusions: tuple[CoverageExclusion, ...]


@dataclass(frozen=True)
class CoverageManifest:
    scopes: tuple[CoverageScope, ...]

    @classmethod
    def from_file(cls, path: Path) -> CoverageManifest:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise TranslationError(f"cannot read coverage manifest {path}: {error}") from error
        if data.get("version") != 1:
            raise TranslationError("coverage manifest version must be 1")
        raw_scopes = data.get("scopes")
        if not isinstance(raw_scopes, list) or not raw_scopes:
            raise TranslationError("coverage manifest must contain at least one [[scopes]] table")
        scopes = tuple(_parse_scope(item, index) for index, item in enumerate(raw_scopes, 1))
        ids = [scope.id for scope in scopes]
        if len(ids) != len(set(ids)):
            raise TranslationError("coverage manifest contains duplicate scope IDs")
        return cls(scopes)

    def select(self, scope_id: str | None) -> tuple[CoverageScope, ...]:
        if scope_id is None:
            return self.scopes
        for scope in self.scopes:
            if scope.id == scope_id:
                return (scope,)
        choices = ", ".join(scope.id for scope in self.scopes)
        raise TranslationError(f"unknown coverage scope {scope_id!r}; choose one of: {choices}")


@dataclass(frozen=True)
class CoverageText:
    anchor: TranslationAnchor
    source_mode: int
    source: str


@dataclass(frozen=True)
class CoverageGroup:
    source_mode: int
    source: str
    anchors: tuple[TranslationAnchor, ...]
    translated_ids: tuple[str, ...]


@dataclass(frozen=True)
class CoverageReport:
    scope: CoverageScope
    texts: tuple[CoverageText, ...]
    translated_anchors: tuple[TranslationAnchor, ...]
    excluded_anchors: tuple[TranslationAnchor, ...]
    pending_groups: tuple[CoverageGroup, ...]
    canonical_line_count: int
    managed_line_count: int
    duplicate_line_count: int
    contextual_split_count: int

    @property
    def pending_anchor_count(self) -> int:
        return sum(len(group.anchors) for group in self.pending_groups)

    @property
    def complete(self) -> bool:
        return not self.pending_groups


def analyze_coverage(
    catalog: TranslationCatalog,
    manifest: CoverageManifest,
    source_directory: Path,
    *,
    scope_id: str | None = None,
) -> tuple[CoverageReport, ...]:
    """Validate sources and classify every decoded text anchor in selected scopes."""
    catalog.verify_sources(source_directory)
    known_files = {file.file: file for file in catalog.files}
    records_by_file = {}
    for logical_name, catalog_file in known_files.items():
        source = source_directory.joinpath(*PurePosixPath(catalog_file.source).parts)
        try:
            records_by_file[logical_name] = GMFile.from_file(source).text_records()
        except GMError as error:
            raise TranslationError(f"{logical_name}: {error}") from error

    translated: dict[tuple[str, int], str] = {}
    translated_source_ids: dict[tuple[int, str], set[str]] = {}
    for entry in catalog.entries:
        translated_source_ids.setdefault((entry.source_mode, entry.source), set()).add(entry.id)
        for anchor in entry.anchors:
            translated[(anchor.file, anchor.offset)] = entry.id

    reports = []
    for scope in manifest.select(scope_id):
        for item in scope.ranges:
            if item.file not in known_files:
                raise TranslationError(f"{scope.id}: unknown coverage file {item.file}")

        texts: list[CoverageText] = []
        for item in scope.ranges:
            for record in records_by_file[item.file]:
                if not item.start <= record.offset <= item.end:
                    continue
                if record.text is None:
                    raise TranslationError(
                        f"{scope.id}: undecodable text at {item.file}:0x{record.offset:04x}"
                    )
                texts.append(
                    CoverageText(
                        TranslationAnchor(item.file, record.offset),
                        record.mode,
                        record.text,
                    )
                )
        texts.sort(key=lambda item: (item.anchor.file, item.anchor.offset))
        text_by_anchor = {
            (item.anchor.file, item.anchor.offset): item for item in texts
        }

        excluded: dict[tuple[str, int], str] = {}
        for exclusion in scope.exclusions:
            for anchor in exclusion.anchors:
                key = (anchor.file, anchor.offset)
                text = text_by_anchor.get(key)
                if text is None:
                    raise TranslationError(
                        f"{exclusion.id}: exclusion anchor falls outside scope {scope.id}: "
                        f"{anchor.file}:0x{anchor.offset:04x}"
                    )
                if text.source_mode != exclusion.source_mode or text.source != exclusion.source:
                    raise TranslationError(
                        f"{exclusion.id}: exclusion source changed at "
                        f"{anchor.file}:0x{anchor.offset:04x}"
                    )
                if key in translated:
                    raise TranslationError(
                        f"{exclusion.id}: anchor is both translated and excluded: "
                        f"{anchor.file}:0x{anchor.offset:04x}"
                    )
                if key in excluded:
                    raise TranslationError(
                        f"duplicate coverage exclusion anchor: "
                        f"{anchor.file}:0x{anchor.offset:04x}"
                    )
                excluded[key] = exclusion.id

        all_groups: dict[tuple[int, str], list[CoverageText]] = {}
        pending: dict[tuple[int, str], list[CoverageText]] = {}
        translated_anchors: list[TranslationAnchor] = []
        excluded_anchors: list[TranslationAnchor] = []
        for text in texts:
            source_key = (text.source_mode, text.source)
            all_groups.setdefault(source_key, []).append(text)
            anchor_key = (text.anchor.file, text.anchor.offset)
            if anchor_key in translated:
                translated_anchors.append(text.anchor)
            elif anchor_key in excluded:
                excluded_anchors.append(text.anchor)
            else:
                pending.setdefault(source_key, []).append(text)

        pending_groups = tuple(
            CoverageGroup(
                source_mode=key[0],
                source=key[1],
                anchors=tuple(item.anchor for item in items),
                translated_ids=tuple(sorted(translated_source_ids.get(key, set()))),
            )
            for key, items in sorted(
                pending.items(), key=lambda item: _anchor_sort_key(item[1][0].anchor)
            )
        )
        contextual_splits = sum(
            len(translated_source_ids.get(key, set())) > 1 for key in all_groups
        )
        duplicate_lines = sum(len(items) > 1 for items in all_groups.values())
        reports.append(
            CoverageReport(
                scope=scope,
                texts=tuple(texts),
                translated_anchors=tuple(translated_anchors),
                excluded_anchors=tuple(excluded_anchors),
                pending_groups=pending_groups,
                canonical_line_count=len(all_groups),
                managed_line_count=len(all_groups) - len(pending_groups),
                duplicate_line_count=duplicate_lines,
                contextual_split_count=contextual_splits,
            )
        )
    return tuple(reports)


def _anchor_sort_key(anchor: TranslationAnchor) -> tuple[str, int]:
    return anchor.file, anchor.offset


def _parse_scope(value: object, index: int) -> CoverageScope:
    context = f"scopes[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    scope_id = _string(value, "id", context)
    description = _string(value, "description", context)
    raw_ranges = value.get("ranges")
    if not isinstance(raw_ranges, list) or not raw_ranges:
        raise TranslationError(f"{context} must contain at least one [[scopes.ranges]] table")
    ranges = tuple(_parse_range(item, item_index, context) for item_index, item in enumerate(raw_ranges, 1))
    _validate_nonoverlapping_ranges(ranges, context)

    raw_exclusions = value.get("exclusions", [])
    if not isinstance(raw_exclusions, list):
        raise TranslationError(f"{context}.exclusions must be an array of tables")
    exclusions = tuple(
        _parse_exclusion(item, item_index, context)
        for item_index, item in enumerate(raw_exclusions, 1)
    )
    exclusion_ids = [item.id for item in exclusions]
    if len(exclusion_ids) != len(set(exclusion_ids)):
        raise TranslationError(f"{context} contains duplicate exclusion IDs")
    return CoverageScope(scope_id, description, ranges, exclusions)


def _parse_range(value: object, index: int, scope_context: str) -> CoverageRange:
    context = f"{scope_context}.ranges[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    file = _string(value, "file", context)
    start = _integer(value, "start", context)
    end = _integer(value, "end", context)
    if start < 0 or end < start:
        raise TranslationError(f"{context} must use 0 <= start <= end")
    return CoverageRange(file, start, end)


def _parse_exclusion(value: object, index: int, scope_context: str) -> CoverageExclusion:
    context = f"{scope_context}.exclusions[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    mode = _integer(value, "source_mode", context)
    if mode not in (1, 2):
        raise TranslationError(f"{context}.source_mode must be 1 or 2")
    return CoverageExclusion(
        id=_string(value, "id", context),
        anchors=_parse_anchors(value, context),
        source_mode=mode,
        source=_string(value, "source", context),
        reason=_string(value, "reason", context),
    )


def _parse_anchors(
    table: dict[str, object], context: str
) -> tuple[TranslationAnchor, ...]:
    raw_anchors = table.get("anchors")
    has_single = "file" in table or "offset" in table
    if raw_anchors is not None and has_single:
        raise TranslationError(f"{context} must use either file/offset or anchors, not both")
    if raw_anchors is None:
        file = _string(table, "file", context)
        offset = _integer(table, "offset", context)
        if offset < 0:
            raise TranslationError(f"{context}.offset must not be negative")
        return (TranslationAnchor(file, offset),)
    if not isinstance(raw_anchors, list) or not raw_anchors:
        raise TranslationError(f"{context}.anchors must be a non-empty array of tables")
    anchors = []
    for index, raw_anchor in enumerate(raw_anchors, 1):
        anchor_context = f"{context}.anchors[{index}]"
        if not isinstance(raw_anchor, dict):
            raise TranslationError(f"{anchor_context} must be a table")
        offset = _integer(raw_anchor, "offset", anchor_context)
        if offset < 0:
            raise TranslationError(f"{anchor_context}.offset must not be negative")
        anchors.append(
            TranslationAnchor(_string(raw_anchor, "file", anchor_context), offset)
        )
    return tuple(anchors)


def _validate_nonoverlapping_ranges(
    ranges: tuple[CoverageRange, ...], context: str
) -> None:
    by_file: dict[str, list[CoverageRange]] = {}
    for item in ranges:
        by_file.setdefault(item.file, []).append(item)
    for file, items in by_file.items():
        ordered = sorted(items, key=lambda item: item.start)
        for before, after in pairwise(ordered):
            if after.start <= before.end:
                raise TranslationError(f"{context} contains overlapping ranges for {file}")


def _string(table: dict[str, object], key: str, context: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise TranslationError(f"{context}.{key} must be a non-empty string")
    return value


def _integer(table: dict[str, object], key: str, context: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TranslationError(f"{context}.{key} must be an integer")
    return value
