"""Checked-in translation catalog parsing and source verification."""

from __future__ import annotations

import hashlib
import textwrap
import tomllib
from dataclasses import dataclass
from pathlib import Path

from fermion.gm import GMError, GMFile


class TranslationError(ValueError):
    """Raised when a translation catalog or its source anchors are invalid."""


@dataclass(frozen=True)
class TranslationFile:
    name: str
    sha256: str


@dataclass(frozen=True)
class TranslationEntry:
    id: str
    file: str
    offset: int
    source_mode: int
    target_mode: int
    source: str
    translation: str
    status: str
    notes: str
    box_width: int | None = None

    @property
    def wrapped_translation(self) -> tuple[str, ...]:
        if self.box_width is None:
            return (self.translation,)
        lines: list[str] = []
        for paragraph in self.translation.splitlines() or [""]:
            lines.extend(
                textwrap.wrap(
                    paragraph,
                    width=self.box_width,
                    break_long_words=False,
                    break_on_hyphens=False,
                    replace_whitespace=False,
                )
                or [""]
            )
        return tuple(lines)


@dataclass(frozen=True)
class TranslationCatalog:
    game: str
    files: tuple[TranslationFile, ...]
    entries: tuple[TranslationEntry, ...]

    @classmethod
    def from_file(cls, path: Path) -> TranslationCatalog:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise TranslationError(f"cannot read translation catalog {path}: {error}") from error

        if data.get("version") != 1:
            raise TranslationError("translation catalog version must be 1")
        game = _string(data, "game")
        raw_files = data.get("files")
        raw_entries = data.get("entries")
        if not isinstance(raw_files, list) or not raw_files:
            raise TranslationError("translation catalog must contain at least one [[files]] table")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise TranslationError("translation catalog must contain at least one [[entries]] table")

        files = tuple(_parse_file(item, index) for index, item in enumerate(raw_files, 1))
        entries = tuple(_parse_entry(item, index) for index, item in enumerate(raw_entries, 1))
        _validate_catalog(files, entries)
        return cls(game, files, entries)

    def verify_sources(self, directory: Path) -> None:
        """Verify file hashes and every entry's original offset, mode, and text."""
        by_name: dict[str, GMFile] = {}
        for file in self.files:
            source = directory / file.name
            if not source.is_file():
                raise TranslationError(f"catalog source does not exist: {source}")
            data = source.read_bytes()
            actual_hash = hashlib.sha256(data).hexdigest()
            if actual_hash != file.sha256:
                raise TranslationError(
                    f"{file.name}: SHA-256 mismatch: expected {file.sha256}, got {actual_hash}"
                )
            try:
                by_name[file.name] = GMFile.from_bytes(data)
            except GMError as error:
                raise TranslationError(f"{file.name}: {error}") from error

        for entry in self.entries:
            records = {record.offset: record for record in by_name[entry.file].text_records()}
            record = records.get(entry.offset)
            if record is None:
                raise TranslationError(
                    f"{entry.id}: no text record at {entry.file}:0x{entry.offset:04x}"
                )
            if record.mode != entry.source_mode:
                raise TranslationError(
                    f"{entry.id}: source mode changed at {entry.file}:0x{entry.offset:04x}: "
                    f"expected {entry.source_mode}, got {record.mode}"
                )
            if record.text != entry.source:
                raise TranslationError(
                    f"{entry.id}: source text changed at {entry.file}:0x{entry.offset:04x}"
                )


def _string(table: dict[str, object], key: str, *, context: str = "catalog") -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise TranslationError(f"{context}.{key} must be a non-empty string")
    return value


def _integer(table: dict[str, object], key: str, *, context: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TranslationError(f"{context}.{key} must be an integer")
    return value


def _parse_file(value: object, index: int) -> TranslationFile:
    context = f"files[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    name = _string(value, "name", context=context)
    if Path(name).name != name:
        raise TranslationError(f"{context}.name must be a basename")
    sha256 = _string(value, "sha256", context=context).lower()
    if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
        raise TranslationError(f"{context}.sha256 must contain 64 hexadecimal characters")
    return TranslationFile(name, sha256)


def _parse_entry(value: object, index: int) -> TranslationEntry:
    context = f"entries[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    source_mode = _integer(value, "source_mode", context=context)
    target_mode = _integer(value, "target_mode", context=context)
    if source_mode not in (1, 2) or target_mode not in (1, 2):
        raise TranslationError(f"{context} modes must be 1 or 2")
    offset = _integer(value, "offset", context=context)
    if offset < 0:
        raise TranslationError(f"{context}.offset must not be negative")
    box_width_value = value.get("box_width")
    if box_width_value is not None and (
        not isinstance(box_width_value, int)
        or isinstance(box_width_value, bool)
        or box_width_value < 1
    ):
        raise TranslationError(f"{context}.box_width must be a positive integer")

    entry = TranslationEntry(
        id=_string(value, "id", context=context),
        file=_string(value, "file", context=context),
        offset=offset,
        source_mode=source_mode,
        target_mode=target_mode,
        source=_string(value, "source", context=context),
        translation=_string(value, "translation", context=context),
        status=_string(value, "status", context=context),
        notes=_string(value, "notes", context=context),
        box_width=box_width_value,
    )
    if "\x00" in entry.translation:
        raise TranslationError(f"{context}.translation must not contain NUL")
    encoding = "ascii" if entry.target_mode == 2 else "cp932"
    try:
        entry.translation.encode(encoding)
    except UnicodeEncodeError as error:
        raise TranslationError(
            f"{entry.id}: translation cannot be encoded in mode {entry.target_mode} ({encoding})"
        ) from error
    if entry.box_width is not None:
        for line in entry.wrapped_translation:
            if len(line) > entry.box_width:
                raise TranslationError(
                    f"{entry.id}: word longer than box width {entry.box_width}: {line!r}"
                )
    return entry


def _validate_catalog(
    files: tuple[TranslationFile, ...], entries: tuple[TranslationEntry, ...]
) -> None:
    file_names = [file.name for file in files]
    if len(file_names) != len(set(file_names)):
        raise TranslationError("translation catalog contains duplicate file names")
    known_files = set(file_names)
    ids: set[str] = set()
    anchors: set[tuple[str, int]] = set()
    for entry in entries:
        if entry.id in ids:
            raise TranslationError(f"duplicate translation ID: {entry.id}")
        ids.add(entry.id)
        if entry.file not in known_files:
            raise TranslationError(f"{entry.id}: unknown source file {entry.file}")
        anchor = (entry.file, entry.offset)
        if anchor in anchors:
            raise TranslationError(
                f"duplicate translation anchor: {entry.file}:0x{entry.offset:04x}"
            )
        anchors.add(anchor)
