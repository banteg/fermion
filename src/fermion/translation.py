"""Checked-in translation catalog parsing and source verification."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import textwrap
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fermion.gm import GMError, GMFile

_GM_TEXT = re.compile(r'\(gm-text\s+([12])\s+"((?:\\.|[^"\\])*)"\)', re.DOTALL)


class TranslationError(ValueError):
    """Raised when a translation catalog or its source anchors are invalid."""


@dataclass(frozen=True)
class TranslationFile:
    file: str
    source: str
    sha256: str

    @property
    def archive(self) -> str:
        return self.file.split("/", 1)[0]

    @property
    def name(self) -> str:
        return self.file.split("/", 1)[1]


@dataclass(frozen=True)
class TranslationAnchor:
    file: str
    offset: int


@dataclass(frozen=True)
class TranslationEntry:
    id: str
    anchors: tuple[TranslationAnchor, ...]
    source_mode: int
    target_mode: int
    source: str
    translation: str
    speaker: str
    context: str
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

        if data.get("version") != 4:
            raise TranslationError("translation catalog version must be 4")
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
        speakers_by_name: dict[str, dict[int, str | None]] = {}
        for file in self.files:
            source = directory.joinpath(*PurePosixPath(file.source).parts)
            if not source.is_file():
                raise TranslationError(f"catalog source does not exist: {source}")
            data = source.read_bytes()
            actual_hash = hashlib.sha256(data).hexdigest()
            if actual_hash != file.sha256:
                raise TranslationError(
                    f"{file.file}: SHA-256 mismatch: expected {file.sha256}, got {actual_hash}"
                )
            try:
                by_name[file.file] = GMFile.from_bytes(data)
            except GMError as error:
                raise TranslationError(f"{file.file}: {error}") from error
            speakers_by_name[file.file] = {
                item.record.offset: item.speaker.id if item.speaker else None
                for item in by_name[file.file].attributed_text_records()
            }

        for entry in self.entries:
            for anchor in entry.anchors:
                records = {
                    record.offset: record for record in by_name[anchor.file].text_records()
                }
                record = records.get(anchor.offset)
                location = f"{anchor.file}:0x{anchor.offset:04x}"
                if record is None:
                    raise TranslationError(f"{entry.id}: no text record at {location}")
                if record.mode != entry.source_mode:
                    raise TranslationError(
                        f"{entry.id}: source mode changed at {location}: "
                        f"expected {entry.source_mode}, got {record.mode}"
                    )
                if record.text != entry.source:
                    raise TranslationError(f"{entry.id}: source text changed at {location}")
                encoded_speaker = speakers_by_name[anchor.file].get(anchor.offset)
                if encoded_speaker is not None and encoded_speaker != entry.speaker:
                    raise TranslationError(
                        f"{entry.id}: encoded speaker at {location} is "
                        f"{encoded_speaker!r}, catalog has {entry.speaker!r}"
                    )

    @property
    def anchor_count(self) -> int:
        return sum(len(entry.anchors) for entry in self.entries)


@dataclass(frozen=True)
class BuiltTranslationFile:
    catalog_file: TranslationFile
    source_path: Path
    rkt_path: Path
    output_path: Path
    source_size: int
    output_size: int
    output_sha256: str


def build_translation_files(
    catalog: TranslationCatalog,
    source_directory: Path,
    output_directory: Path,
    juice: Path,
) -> tuple[BuiltTranslationFile, ...]:
    """Decompile, catalog-edit, compile, and structurally verify every translated MES."""
    catalog.verify_sources(source_directory)
    executable = _resolve_executable(juice)
    entries_by_file = {
        file.file: tuple(
            (anchor.offset, entry)
            for entry in catalog.entries
            for anchor in entry.anchors
            if anchor.file == file.file
        )
        for file in catalog.files
    }
    built = []
    for file in catalog.files:
        entries = entries_by_file[file.file]
        if not entries:
            continue
        source_path = source_directory.joinpath(*PurePosixPath(file.source).parts)
        rkt_path = output_directory / "rkt" / file.archive / Path(file.name).with_suffix(".rkt")
        output_path = output_directory / "mes" / file.archive / file.name
        rkt_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        _run_juice(
            executable,
            ["-d", "-e", "GM", "-f", "-o", str(rkt_path), str(source_path)],
            rkt_path,
        )
        original = GMFile.from_file(source_path)
        edited = _patch_gm_source(rkt_path.read_text(), original, entries)
        rkt_path.write_text(edited)
        _run_juice(
            executable,
            ["-c", "-f", "-o", str(output_path), str(rkt_path)],
            output_path,
        )
        compiled = GMFile.from_file(output_path)
        _verify_compiled_file(file, original, compiled, entries)
        output_data = output_path.read_bytes()
        built.append(
            BuiltTranslationFile(
                file,
                source_path,
                rkt_path,
                output_path,
                len(original.data),
                len(output_data),
                hashlib.sha256(output_data).hexdigest(),
            )
        )
    return tuple(built)


def _patch_gm_source(
    source: str,
    original: GMFile,
    entries: tuple[tuple[int, TranslationEntry], ...],
) -> str:
    records = original.text_records()
    matches = list(_GM_TEXT.finditer(source))
    if len(matches) != len(records):
        raise TranslationError(
            f"lime-juice emitted {len(matches)} editable text nodes for "
            f"{len(records)} decoded records"
        )
    edits = dict(entries)
    used: set[int] = set()
    chunks = []
    position = 0
    for match, record in zip(matches, records, strict=True):
        chunks.append(source[position : match.start()])
        mode = int(match.group(1))
        text = _unescape_rkt_string(match.group(2))
        if mode != record.mode or text != record.text:
            raise TranslationError(
                f"lime-juice text order diverged at source offset 0x{record.offset:04x}"
            )
        entry = edits.get(record.offset)
        if entry is None:
            chunks.append(match.group(0))
        else:
            chunks.append(
                f'(gm-text {entry.target_mode} "{_escape_rkt_string(entry.translation)}")'
            )
            used.add(record.offset)
        position = match.end()
    chunks.append(source[position:])
    missing = sorted(set(edits) - used)
    if missing:
        raise TranslationError(
            "lime-juice source omitted catalog offset(s): "
            + ", ".join(f"0x{offset:04x}" for offset in missing)
        )
    return "".join(chunks)


def _verify_compiled_file(
    file: TranslationFile,
    original: GMFile,
    compiled: GMFile,
    entries: tuple[tuple[int, TranslationEntry], ...],
) -> None:
    original_audit = original.audit()
    compiled_audit = compiled.audit()
    if original_audit.issues:
        raise TranslationError(f"{file.file}: pristine structural audit failed")
    if compiled_audit.issues:
        raise TranslationError(
            f"{file.file}: compiled structural audit has {len(compiled_audit.issues)} issue(s)"
        )
    original_opcodes = tuple(instruction.opcode for instruction in original_audit.instructions)
    compiled_opcodes = tuple(instruction.opcode for instruction in compiled_audit.instructions)
    if original_opcodes != compiled_opcodes:
        raise TranslationError(f"{file.file}: compiled instruction sequence changed")
    if len(original_audit.relocations) != len(compiled_audit.relocations):
        raise TranslationError(f"{file.file}: compiled relocation count changed")
    for before, after in zip(
        original_audit.relocations, compiled_audit.relocations, strict=True
    ):
        external = not original.code_start <= before.target < len(original.data)
        if external and after.target != before.target:
            raise TranslationError(
                f"{file.file}: external target changed from 0x{before.target:04x} "
                f"to 0x{after.target:04x}"
            )

    edits = dict(entries)
    original_records = original.text_records()
    compiled_records = compiled.text_records()
    if len(original_records) != len(compiled_records):
        raise TranslationError(f"{file.file}: compiled text-record count changed")
    for before, after in zip(original_records, compiled_records, strict=True):
        entry = edits.get(before.offset)
        if entry is not None:
            expected = (entry.target_mode, entry.translation)
            actual = (after.mode, after.text)
            if actual != expected:
                raise TranslationError(
                    f"{entry.id}: compiled text mismatch: expected {expected!r}, got {actual!r}"
                )
        elif (after.mode, after.text, after.payload) != (
            before.mode,
            before.text,
            before.payload,
        ):
            raise TranslationError(
                f"{file.file}: unrelated text changed after source offset 0x{before.offset:04x}"
            )


def _resolve_executable(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.parent != Path(".") or expanded.is_absolute():
        if not expanded.is_file():
            raise TranslationError(f"lime-juice executable does not exist: {expanded}")
        return expanded.resolve()
    resolved = shutil.which(str(expanded))
    if resolved is None:
        raise TranslationError(f"lime-juice executable is not on PATH: {expanded}")
    return Path(resolved)


def _run_juice(executable: Path, arguments: list[str], output: Path) -> None:
    output.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            [str(executable), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise TranslationError(f"cannot execute lime-juice: {error}") from error
    if result.returncode != 0 or not output.is_file() or output.stat().st_size == 0:
        details = result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise TranslationError(f"lime-juice failed to create {output}: {details}")


def _escape_rkt_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def _unescape_rkt_string(value: str) -> str:
    output = []
    position = 0
    escapes = {'"': '"', "\\": "\\", "n": "\n", "t": "\t"}
    while position < len(value):
        if value[position] != "\\" or position + 1 >= len(value):
            output.append(value[position])
            position += 1
            continue
        escaped = value[position + 1]
        if escaped in escapes:
            output.append(escapes[escaped])
        else:
            output.extend(("\\", escaped))
        position += 2
    return "".join(output)


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
    file = _relative_path(_string(value, "file", context=context), f"{context}.file")
    if len(PurePosixPath(file).parts) != 2:
        raise TranslationError(f"{context}.file must use ARCHIVE/FILENAME")
    source = _relative_path(_string(value, "source", context=context), f"{context}.source")
    sha256 = _string(value, "sha256", context=context).lower()
    if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
        raise TranslationError(f"{context}.sha256 must contain 64 hexadecimal characters")
    return TranslationFile(file, source, sha256)


def _parse_entry(value: object, index: int) -> TranslationEntry:
    context = f"entries[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    source_mode = _integer(value, "source_mode", context=context)
    target_mode = _integer(value, "target_mode", context=context)
    if source_mode not in (1, 2) or target_mode not in (1, 2):
        raise TranslationError(f"{context} modes must be 1 or 2")
    anchors = _parse_anchors(value, context)
    box_width_value = value.get("box_width")
    if box_width_value is not None and (
        not isinstance(box_width_value, int)
        or isinstance(box_width_value, bool)
        or box_width_value < 1
    ):
        raise TranslationError(f"{context}.box_width must be a positive integer")

    entry = TranslationEntry(
        id=_string(value, "id", context=context),
        anchors=anchors,
        source_mode=source_mode,
        target_mode=target_mode,
        source=_string(value, "source", context=context),
        translation=_string(value, "translation", context=context),
        speaker=_string(value, "speaker", context=context),
        context=_string(value, "context", context=context),
        status=_string(value, "status", context=context),
        notes=_string(value, "notes", context=context),
        box_width=box_width_value,
    )
    if "\x00" in entry.translation:
        raise TranslationError(f"{context}.translation must not contain NUL")
    encoding = "ascii" if entry.target_mode == 2 else "cp932"
    try:
        encoded_translation = entry.translation.encode(encoding)
    except UnicodeEncodeError as error:
        raise TranslationError(
            f"{entry.id}: translation cannot be encoded in mode {entry.target_mode} ({encoding})"
        ) from error
    if entry.target_mode == 2 and not all(
        byte == 0x0A or 0x20 <= byte <= 0x7E for byte in encoded_translation
    ):
        raise TranslationError(
            f"{entry.id}: mode 2 translation must contain printable ASCII or newlines"
        )
    if entry.target_mode == 1 and any(
        ord(character) < 0x20 and character != "\n" for character in entry.translation
    ):
        raise TranslationError(f"{entry.id}: mode 1 translation contains an unsupported control")
    if entry.box_width is not None:
        for line in entry.wrapped_translation:
            if len(line) > entry.box_width:
                raise TranslationError(
                    f"{entry.id}: word longer than box width {entry.box_width}: {line!r}"
                )
    return entry


def _parse_anchors(
    table: dict[str, object], context: str
) -> tuple[TranslationAnchor, ...]:
    raw_anchors = table.get("anchors")
    has_single = "file" in table or "offset" in table
    if raw_anchors is not None and has_single:
        raise TranslationError(
            f"{context} must use either file/offset or anchors, not both"
        )
    if raw_anchors is None:
        file = _string(table, "file", context=context)
        offset = _integer(table, "offset", context=context)
        if offset < 0:
            raise TranslationError(f"{context}.offset must not be negative")
        return (TranslationAnchor(file, offset),)
    if not isinstance(raw_anchors, list) or not raw_anchors:
        raise TranslationError(f"{context}.anchors must be a non-empty array of tables")

    anchors: list[TranslationAnchor] = []
    for index, raw_anchor in enumerate(raw_anchors, 1):
        anchor_context = f"{context}.anchors[{index}]"
        if not isinstance(raw_anchor, dict):
            raise TranslationError(f"{anchor_context} must be a table")
        file = _string(raw_anchor, "file", context=anchor_context)
        offset = _integer(raw_anchor, "offset", context=anchor_context)
        if offset < 0:
            raise TranslationError(f"{anchor_context}.offset must not be negative")
        anchors.append(TranslationAnchor(file, offset))
    return tuple(anchors)


def _validate_catalog(
    files: tuple[TranslationFile, ...], entries: tuple[TranslationEntry, ...]
) -> None:
    file_names = [file.file for file in files]
    if len(file_names) != len({name.casefold() for name in file_names}):
        raise TranslationError("translation catalog contains duplicate file names")
    known_files = set(file_names)
    ids: set[str] = set()
    anchors: set[tuple[str, int]] = set()
    for entry in entries:
        if entry.id in ids:
            raise TranslationError(f"duplicate translation ID: {entry.id}")
        ids.add(entry.id)
        for entry_anchor in entry.anchors:
            if entry_anchor.file not in known_files:
                raise TranslationError(
                    f"{entry.id}: unknown source file {entry_anchor.file}"
                )
            anchor = (entry_anchor.file, entry_anchor.offset)
            if anchor in anchors:
                raise TranslationError(
                    "duplicate translation anchor: "
                    f"{entry_anchor.file}:0x{entry_anchor.offset:04x}"
                )
            anchors.add(anchor)


def _relative_path(value: str, context: str) -> str:
    parts = value.split("/")
    if "\\" in value or any(part in ("", ".", "..") for part in parts):
        raise TranslationError(f"{context} must be a safe relative path")
    return PurePosixPath(*parts).as_posix()
