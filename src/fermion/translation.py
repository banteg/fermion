"""Checked-in translation catalog parsing and source verification."""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import textwrap
import tomllib
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path, PurePosixPath

from fermion.gm import GMError, GMFile, interpolation_token_for_slot

_GM_TEXT = re.compile(
    r"\((?:gm-text\s+(?P<legacy_mode>[12])|"
    r"text(?P<semantic_mode>\s+#:mode\s+[12])?)\s+"
    r'"(?P<text>(?:\\.|[^"\\])*)"\)',
    re.DOTALL,
)
_TOKEN_ID = re.compile(r"^(?:name|term):[a-z0-9]+(?:-[a-z0-9]+)*$")
_TOKEN_MARKER = re.compile(r"⟦((?:name|term):[a-z0-9]+(?:-[a-z0-9]+)*)⟧")


class TranslationError(ValueError):
    """Raised when a translation catalog or its source anchors are invalid."""


@dataclass(frozen=True)
class TranslationFile:
    file: str
    source: str
    sha256: str
    box_width: int | None = None

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
class TranslationTokenInitializer:
    file: str
    offset: int
    slot: int


@dataclass(frozen=True)
class TranslationToken:
    id: str
    source: str
    translation: str
    max_width: int
    initializers: tuple[TranslationTokenInitializer, ...] = ()

    @property
    def marker(self) -> str:
        return f"⟦{self.id}⟧"


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
        return self.wrapped_translation_for()

    def wrapped_translation_for(self, default_box_width: int | None = None) -> tuple[str, ...]:
        box_width = self.box_width if self.box_width is not None else default_box_width
        if box_width is None:
            return (self.translation,)
        return _wrap_text(self.translation, box_width)

    def compiled_translation(self, default_box_width: int | None = None) -> str:
        return "\n".join(self.wrapped_translation_for(default_box_width))


@dataclass(frozen=True)
class CompositeTextSegment:
    anchor: TranslationAnchor
    source_mode: int
    source: str


@dataclass(frozen=True)
class CompositeTokenSegment:
    token: str
    start: int
    end: int
    sha256: str


CompositeSegment = CompositeTextSegment | CompositeTokenSegment


@dataclass(frozen=True)
class CompositeOccurrence:
    file: str
    segments: tuple[CompositeSegment, ...]

    @property
    def start(self) -> int:
        first = self.segments[0]
        if isinstance(first, CompositeTextSegment):
            return first.anchor.offset
        return first.start

    @property
    def anchors(self) -> tuple[TranslationAnchor, ...]:
        return tuple(
            segment.anchor for segment in self.segments if isinstance(segment, CompositeTextSegment)
        )


@dataclass(frozen=True)
class CompositeTranslationEntry:
    id: str
    occurrences: tuple[CompositeOccurrence, ...]
    target_mode: int
    source: str
    translation: str
    speaker: str
    context: str
    status: str
    notes: str
    box_width: int | None = None

    @property
    def anchors(self) -> tuple[TranslationAnchor, ...]:
        return tuple(anchor for occurrence in self.occurrences for anchor in occurrence.anchors)

    def compiled_translation(
        self,
        default_box_width: int | None,
        tokens: dict[str, TranslationToken],
    ) -> str:
        box_width = self.box_width if self.box_width is not None else default_box_width
        if box_width is None:
            return self.translation
        return _wrap_composite(self.translation, box_width, tokens)


@dataclass(frozen=True)
class PhysicalTranslation:
    id: str
    anchor: TranslationAnchor
    source_mode: int
    target_mode: int
    source: str
    translation: str


@dataclass(frozen=True)
class TranslationCatalog:
    version: int
    game: str
    files: tuple[TranslationFile, ...]
    tokens: tuple[TranslationToken, ...]
    entries: tuple[TranslationEntry, ...]
    composites: tuple[CompositeTranslationEntry, ...]

    @classmethod
    def from_file(cls, path: Path) -> TranslationCatalog:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise TranslationError(f"cannot read translation catalog {path}: {error}") from error

        version = data.get("version")
        if version not in (4, 5):
            raise TranslationError("translation catalog version must be 4 or 5")
        game = _string(data, "game")
        raw_files = data.get("files")
        raw_entries = data.get("entries", [])
        raw_tokens = data.get("tokens", [])
        raw_composites = data.get("composites", [])
        if not isinstance(raw_files, list) or not raw_files:
            raise TranslationError("translation catalog must contain at least one [[files]] table")
        if not isinstance(raw_entries, list):
            raise TranslationError("translation catalog [[entries]] must be an array of tables")
        if not isinstance(raw_tokens, list):
            raise TranslationError("translation catalog [[tokens]] must be an array of tables")
        if not isinstance(raw_composites, list):
            raise TranslationError("translation catalog [[composites]] must be an array of tables")
        if version == 4 and (raw_tokens or raw_composites):
            raise TranslationError("translation catalog version 4 cannot contain schema-5 tables")
        if not raw_entries and not raw_composites:
            raise TranslationError(
                "translation catalog must contain at least one entry or composite"
            )

        files = tuple(_parse_file(item, index) for index, item in enumerate(raw_files, 1))
        tokens = tuple(_parse_token(item, index) for index, item in enumerate(raw_tokens, 1))
        entries = tuple(_parse_entry(item, index) for index, item in enumerate(raw_entries, 1))
        composites = tuple(
            _parse_composite(item, index) for index, item in enumerate(raw_composites, 1)
        )
        _validate_catalog(files, tokens, entries, composites)
        return cls(version, game, files, tokens, entries, composites)

    def verify_sources(self, directory: Path) -> None:
        """Verify file hashes and every entry's original offset, mode, and text."""
        by_name: dict[str, GMFile] = {}
        speakers_by_name: dict[str, dict[int, str | None]] = {}
        interpolations_by_name = {}
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
            interpolations_by_name[file.file] = {
                (item.start, item.end): item for item in by_name[file.file].interpolations()
            }

        for token in self.tokens:
            for initializer in token.initializers:
                _verify_token_initializer_source(by_name[initializer.file], token, initializer)

        for entry in self.entries:
            for anchor in entry.anchors:
                records = {record.offset: record for record in by_name[anchor.file].text_records()}
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

        for composite in self.composites:
            for occurrence in composite.occurrences:
                records = {
                    record.offset: record for record in by_name[occurrence.file].text_records()
                }
                resolved_spans: list[tuple[int, int]] = []
                for segment in occurrence.segments:
                    if isinstance(segment, CompositeTextSegment):
                        record = records.get(segment.anchor.offset)
                        location = f"{occurrence.file}:0x{segment.anchor.offset:04x}"
                        if record is None:
                            raise TranslationError(f"{composite.id}: no text record at {location}")
                        if record.mode != segment.source_mode:
                            raise TranslationError(
                                f"{composite.id}: source mode changed at {location}: "
                                f"expected {segment.source_mode}, got {record.mode}"
                            )
                        if record.text != segment.source:
                            raise TranslationError(
                                f"{composite.id}: source text changed at {location}"
                            )
                        resolved_spans.append((record.offset, record.end))
                        encoded_speaker = speakers_by_name[occurrence.file].get(
                            segment.anchor.offset
                        )
                        if encoded_speaker is not None and encoded_speaker != composite.speaker:
                            raise TranslationError(
                                f"{composite.id}: encoded speaker at {location} is "
                                f"{encoded_speaker!r}, catalog has {composite.speaker!r}"
                            )
                        continue
                    interpolation = interpolations_by_name[occurrence.file].get(
                        (segment.start, segment.end)
                    )
                    location = f"{occurrence.file}:0x{segment.start:04x}-0x{segment.end:04x}"
                    if interpolation is None or interpolation.token != segment.token:
                        raise TranslationError(
                            f"{composite.id}: interpolation changed at {location}"
                        )
                    resolved_spans.append((segment.start, segment.end))
                    data = by_name[occurrence.file].data[segment.start : segment.end]
                    actual_hash = hashlib.sha256(data).hexdigest()
                    if actual_hash != segment.sha256:
                        raise TranslationError(
                            f"{composite.id}: interpolation SHA-256 mismatch at {location}: "
                            f"expected {segment.sha256}, got {actual_hash}"
                        )
                for before, after in pairwise(resolved_spans):
                    if before[1] != after[0]:
                        raise TranslationError(
                            f"{composite.id}: occurrence contains a gap between "
                            f"0x{before[1]:04x} and 0x{after[0]:04x}"
                        )

    @property
    def anchor_count(self) -> int:
        return sum(len(entry.anchors) for entry in self.entries) + sum(
            len(entry.anchors) for entry in self.composites
        )

    @property
    def entry_count(self) -> int:
        return len(self.entries) + len(self.composites)

    def physical_translations(self, *, compiled: bool = False) -> tuple[PhysicalTranslation, ...]:
        files = {file.file: file for file in self.files}
        tokens = {token.id: token for token in self.tokens}
        physical = []
        for entry in self.entries:
            for anchor in entry.anchors:
                translation = (
                    entry.compiled_translation(files[anchor.file].box_width)
                    if compiled
                    else entry.translation
                )
                physical.append(
                    PhysicalTranslation(
                        entry.id,
                        anchor,
                        entry.source_mode,
                        entry.target_mode,
                        entry.source,
                        translation,
                    )
                )
        for entry in self.composites:
            for occurrence in entry.occurrences:
                translation = entry.compiled_translation(
                    files[occurrence.file].box_width if compiled else None,
                    tokens,
                )
                translation_parts = _composite_parts(translation)
                text_chunks = [value for kind, value in translation_parts if kind == "text"]
                text_segments = [
                    segment
                    for segment in occurrence.segments
                    if isinstance(segment, CompositeTextSegment)
                ]
                for segment, chunk in zip(text_segments, text_chunks, strict=True):
                    physical.append(
                        PhysicalTranslation(
                            entry.id,
                            segment.anchor,
                            segment.source_mode,
                            entry.target_mode,
                            segment.source,
                            chunk,
                        )
                    )
        return tuple(physical)


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
    physical_translations = catalog.physical_translations(compiled=True)
    entries_by_file = {
        file.file: tuple(
            (entry.anchor.offset, entry)
            for entry in physical_translations
            if entry.anchor.file == file.file
        )
        for file in catalog.files
    }
    token_initializers_by_file = {
        file.file: tuple(
            (token, initializer)
            for token in catalog.tokens
            for initializer in token.initializers
            if initializer.file == file.file
        )
        for file in catalog.files
    }
    built = []
    for file in catalog.files:
        entries = entries_by_file[file.file]
        token_initializers = token_initializers_by_file[file.file]
        if not entries and not token_initializers:
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
        if token_initializers:
            edited = _patch_token_initializer_source(edited, original, token_initializers)
        rkt_path.write_text(edited)
        _run_juice(
            executable,
            ["-c", "-f", "-o", str(output_path), str(rkt_path)],
            output_path,
        )
        compiled = GMFile.from_file(output_path)
        _verify_compiled_file(
            file,
            original,
            compiled,
            entries,
            token_initializers,
        )
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


def _patch_token_initializer_source(
    source: str,
    original: GMFile,
    initializers: tuple[tuple[TranslationToken, TranslationTokenInitializer], ...],
) -> str:
    """Edit semantic string-copy nodes so Lime Juice can relocate the result."""
    string_copy_instructions = tuple(
        instruction for instruction in original.audit().instructions if instruction.opcode == 0x45
    )
    forms = _rkt_list_spans(source, "string-copy")
    if len(forms) != len(string_copy_instructions):
        raise TranslationError(
            "lime-juice string-copy node count diverged from the original bytecode"
        )
    form_by_offset = {
        instruction.offset: form
        for instruction, form in zip(string_copy_instructions, forms, strict=True)
    }
    edits: list[tuple[int, int, str]] = []
    for token, initializer in sorted(
        initializers,
        key=lambda item: item[1].offset,
    ):
        _verify_token_initializer_source(original, token, initializer)
        form = form_by_offset.get(initializer.offset)
        if form is None:
            raise TranslationError(
                f"{token.id}: lime-juice omitted initializer at 0x{initializer.offset:04x}"
            )
        start, end, text = form
        match = re.fullmatch(
            r"\(string-copy\s+\(ref\s+(\d+)\s+(\d+)\)\s+"
            r"\(inline-source\s+(\d+)((?:\s+\d+)+)\)\)",
            text,
            re.DOTALL,
        )
        if match is None:
            raise TranslationError(
                f"{token.id}: initializer is not a semantic inline string-copy node"
            )
        reference_token = int(match.group(1))
        reference_slot = int(match.group(2))
        trailing = int(match.group(3))
        payload = tuple(int(value) for value in match.group(4).split())
        expected = (14, 224, 0, 255, 1, *token.source.encode("cp932"))
        actual = (reference_token, reference_slot, trailing, *payload)
        if actual != expected:
            raise TranslationError(
                f"{token.id}: lime-juice initializer source changed at 0x{initializer.offset:04x}"
            )
        translated_payload = (255, 1, *token.translation.encode("ascii"))
        replacement = (
            f"(string-copy (ref {reference_token} {reference_slot}) "
            f"(inline-source {trailing} "
            + " ".join(str(value) for value in translated_payload)
            + "))"
        )
        edits.append((start, end, replacement))
    patched = source
    for start, end, replacement in reversed(edits):
        patched = patched[:start] + replacement + patched[end:]
    return patched


def _rkt_list_spans(source: str, tag: str) -> tuple[tuple[int, int, str], ...]:
    """Return balanced list spans beginning with the requested tag."""
    needle = f"({tag}"
    spans = []
    position = 0
    while True:
        start = source.find(needle, position)
        if start < 0:
            break
        after_tag = start + len(needle)
        if after_tag < len(source) and not source[after_tag].isspace():
            position = after_tag
            continue
        depth = 0
        in_string = False
        escaped = False
        for end in range(start, len(source)):
            character = source[end]
            if in_string:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_string = False
                continue
            if character == '"':
                in_string = True
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    spans.append((start, end + 1, source[start : end + 1]))
                    position = end + 1
                    break
        else:
            raise TranslationError(f"unterminated ({tag} ...) node in lime-juice source")
    return tuple(spans)


def _patch_gm_source(
    source: str,
    original: GMFile,
    entries: tuple[tuple[int, PhysicalTranslation], ...],
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
        mode = (
            int(match.group("legacy_mode"))
            if match.group("legacy_mode") is not None
            else int(match.group("semantic_mode").split()[-1])
            if match.group("semantic_mode") is not None
            else 1
        )
        text = _unescape_rkt_string(match.group("text"))
        if mode != record.mode or text != record.text:
            raise TranslationError(
                f"lime-juice text order diverged at source offset 0x{record.offset:04x}"
            )
        entry = edits.get(record.offset)
        if entry is None:
            chunks.append(match.group(0))
        else:
            escaped = _escape_rkt_string(entry.translation)
            if match.group("legacy_mode") is not None:
                chunks.append(f'(gm-text {entry.target_mode} "{escaped}")')
            elif entry.target_mode == 1:
                chunks.append(f'(text "{escaped}")')
            else:
                chunks.append(f'(text #:mode {entry.target_mode} "{escaped}")')
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
    entries: tuple[tuple[int, PhysicalTranslation], ...],
    token_initializers: tuple[tuple[TranslationToken, TranslationTokenInitializer], ...] = (),
) -> None:
    original_audit = original.audit()
    compiled_audit = compiled.audit()
    if original_audit.issues:
        raise TranslationError(f"{file.file}: pristine structural audit failed")
    original_opcodes = tuple(instruction.opcode for instruction in original_audit.instructions)
    compiled_opcodes = tuple(instruction.opcode for instruction in compiled_audit.instructions)
    if original_opcodes != compiled_opcodes:
        raise TranslationError(f"{file.file}: compiled instruction sequence changed")
    _verify_translated_token_initializers(original, compiled, token_initializers)
    if len(original_audit.relocations) != len(compiled_audit.relocations):
        raise TranslationError(f"{file.file}: compiled relocation count changed")
    known_external_fields = {
        after.field_offset
        for before, after in zip(
            original_audit.relocations,
            compiled_audit.relocations,
            strict=True,
        )
        if not original.code_start <= before.target < len(original.data)
    }
    compiled_audit = compiled.audit(known_external_fields=known_external_fields)
    if compiled_audit.issues:
        raise TranslationError(
            f"{file.file}: compiled structural audit has {len(compiled_audit.issues)} issue(s)"
        )
    for before, after in zip(original_audit.relocations, compiled_audit.relocations, strict=True):
        external = not original.code_start <= before.target < len(original.data)
        if external and after.target != before.target:
            raise TranslationError(
                f"{file.file}: external target changed from 0x{before.target:04x} "
                f"to 0x{after.target:04x}"
            )
    original_interpolations = tuple((item.token, item.slot) for item in original.interpolations())
    compiled_interpolations = tuple((item.token, item.slot) for item in compiled.interpolations())
    if compiled_interpolations != original_interpolations:
        raise TranslationError(f"{file.file}: compiled interpolation sequence changed")

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


def _token_initializer_sequence(
    token: TranslationToken,
    initializer: TranslationTokenInitializer,
    *,
    translated: bool,
) -> bytes:
    source = token.source.encode("cp932")
    value = token.translation.encode("ascii") if translated else source
    return (
        b"\x45\x0e\xe0\x00\xff\x01"
        + value
        + b"\x00\x00"
        + b"\x43\x0c"
        + initializer.slot.to_bytes(2, "little")
        + b"\x0e\xe0\x00\x00\x00"
    )


def _verify_translated_token_initializers(
    original: GMFile,
    compiled: GMFile,
    initializers: tuple[tuple[TranslationToken, TranslationTokenInitializer], ...],
) -> None:
    original_instruction_indexes = {
        instruction.offset: index for index, instruction in enumerate(original.audit().instructions)
    }
    compiled_instructions = compiled.audit().instructions
    for token, initializer in sorted(
        initializers,
        key=lambda item: item[1].offset,
    ):
        instruction_index = original_instruction_indexes[initializer.offset]
        compiled_offset = compiled_instructions[instruction_index].offset
        sequence = _token_initializer_sequence(token, initializer, translated=True)
        actual = compiled.data[compiled_offset : compiled_offset + len(sequence)]
        if actual != sequence:
            raise TranslationError(
                f"{token.id}: compiled initializer mismatch at instruction "
                f"{instruction_index} (0x{compiled_offset:04x})"
            )


def _verify_token_initializer_source(
    gm: GMFile,
    token: TranslationToken,
    initializer: TranslationTokenInitializer,
) -> None:
    expected = _token_initializer_sequence(token, initializer, translated=False)
    actual = gm.data[initializer.offset : initializer.offset + len(expected)]
    location = f"{initializer.file}:0x{initializer.offset:04x}"
    if initializer.offset not in {instruction.offset for instruction in gm.audit().instructions}:
        raise TranslationError(f"{token.id}: token initializer is not an instruction at {location}")
    if actual != expected:
        raise TranslationError(f"{token.id}: token initializer changed at {location}")


def _string(table: dict[str, object], key: str, *, context: str = "catalog") -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise TranslationError(f"{context}.{key} must be a non-empty string")
    return value


def _optional_string(table: dict[str, object], key: str, *, context: str = "catalog") -> str:
    value = table.get(key)
    if value is None:
        return ""
    if not isinstance(value, str) or not value:
        raise TranslationError(f"{context}.{key} must be omitted or a non-empty string")
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
    box_width_value = value.get("box_width")
    if box_width_value is not None and (
        not isinstance(box_width_value, int)
        or isinstance(box_width_value, bool)
        or box_width_value < 1
    ):
        raise TranslationError(f"{context}.box_width must be a positive integer")
    return TranslationFile(file, source, sha256, box_width_value)


def _parse_token(value: object, index: int) -> TranslationToken:
    context = f"tokens[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    token_id = _string(value, "id", context=context)
    if not _TOKEN_ID.fullmatch(token_id):
        raise TranslationError(f"{context}.id has invalid token grammar")
    source = _string(value, "source", context=context)
    translation = _string(value, "translation", context=context)
    max_width = _integer(value, "max_width", context=context)
    raw_initializers = value.get("initializers", [])
    if not isinstance(raw_initializers, list):
        raise TranslationError(f"{context}.initializers must be an array of tables")
    initializers = tuple(
        _parse_token_initializer(item, item_index, context)
        for item_index, item in enumerate(raw_initializers, 1)
    )
    if max_width < 1 or max_width < len(translation):
        raise TranslationError(f"{context}.max_width must fit the default translation")
    if any(character in source + translation for character in "⟦⟧\n\x00"):
        raise TranslationError(
            f"{context} source and translation must be single-line literal values"
        )
    try:
        source.encode("cp932")
        translation.encode("ascii")
    except UnicodeEncodeError as error:
        raise TranslationError(
            f"{context} source must be CP932 and translation must be ASCII"
        ) from error
    return TranslationToken(token_id, source, translation, max_width, initializers)


def _parse_token_initializer(
    value: object, index: int, parent_context: str
) -> TranslationTokenInitializer:
    context = f"{parent_context}.initializers[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    file = _relative_path(_string(value, "file", context=context), f"{context}.file")
    offset = _integer(value, "offset", context=context)
    slot = _integer(value, "slot", context=context)
    if offset < 0:
        raise TranslationError(f"{context}.offset must not be negative")
    if not 0 <= slot <= 0xFFFF:
        raise TranslationError(f"{context}.slot must fit an unsigned 16-bit value")
    return TranslationTokenInitializer(file, offset, slot)


def _parse_composite(value: object, index: int) -> CompositeTranslationEntry:
    context = f"composites[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    target_mode = _integer(value, "target_mode", context=context)
    if target_mode not in (1, 2):
        raise TranslationError(f"{context}.target_mode must be 1 or 2")
    raw_occurrences = value.get("occurrences")
    if not isinstance(raw_occurrences, list) or not raw_occurrences:
        raise TranslationError(
            f"{context} must contain at least one [[composites.occurrences]] table"
        )
    occurrences = tuple(
        _parse_composite_occurrence(item, item_index, context)
        for item_index, item in enumerate(raw_occurrences, 1)
    )
    box_width_value = value.get("box_width")
    if box_width_value is not None and (
        not isinstance(box_width_value, int)
        or isinstance(box_width_value, bool)
        or box_width_value < 1
    ):
        raise TranslationError(f"{context}.box_width must be a positive integer")
    entry = CompositeTranslationEntry(
        id=_string(value, "id", context=context),
        occurrences=occurrences,
        target_mode=target_mode,
        source=_string(value, "source", context=context),
        translation=_string(value, "translation", context=context),
        speaker=_string(value, "speaker", context=context),
        context=_string(value, "context", context=context),
        status=_string(value, "status", context=context),
        notes=_optional_string(value, "notes", context=context),
        box_width=box_width_value,
    )
    for field, text in (("source", entry.source), ("translation", entry.translation)):
        try:
            _composite_parts(text)
        except TranslationError as error:
            raise TranslationError(f"{context}.{field}: {error}") from error
    return entry


def _parse_composite_occurrence(
    value: object, index: int, parent_context: str
) -> CompositeOccurrence:
    context = f"{parent_context}.occurrences[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    file = _relative_path(_string(value, "file", context=context), f"{context}.file")
    raw_segments = value.get("segments")
    if not isinstance(raw_segments, list) or not raw_segments:
        raise TranslationError(f"{context}.segments must be a non-empty array of tables")
    segments = tuple(
        _parse_composite_segment(item, item_index, file, context)
        for item_index, item in enumerate(raw_segments, 1)
    )
    if not any(isinstance(item, CompositeTextSegment) for item in segments):
        raise TranslationError(f"{context} must contain a text segment")
    if not any(isinstance(item, CompositeTokenSegment) for item in segments):
        raise TranslationError(f"{context} must contain a token segment")
    positions = [
        item.anchor.offset if isinstance(item, CompositeTextSegment) else item.start
        for item in segments
    ]
    if positions != sorted(set(positions)):
        raise TranslationError(f"{context} segments must be strictly ordered")
    return CompositeOccurrence(file, segments)


def _parse_composite_segment(
    value: object,
    index: int,
    file: str,
    parent_context: str,
) -> CompositeSegment:
    context = f"{parent_context}.segments[{index}]"
    if not isinstance(value, dict):
        raise TranslationError(f"{context} must be a table")
    kind = _string(value, "kind", context=context)
    if kind == "text":
        offset = _integer(value, "offset", context=context)
        source_mode = _integer(value, "source_mode", context=context)
        if offset < 0:
            raise TranslationError(f"{context}.offset must not be negative")
        if source_mode not in (1, 2):
            raise TranslationError(f"{context}.source_mode must be 1 or 2")
        return CompositeTextSegment(
            TranslationAnchor(file, offset),
            source_mode,
            _string(value, "source", context=context),
        )
    if kind == "token":
        token = _string(value, "token", context=context)
        if not _TOKEN_ID.fullmatch(token):
            raise TranslationError(f"{context}.token has invalid token grammar")
        start = _integer(value, "start", context=context)
        end = _integer(value, "end", context=context)
        if start < 0 or end <= start:
            raise TranslationError(f"{context} token span must be non-empty")
        sha256 = _string(value, "sha256", context=context).lower()
        if len(sha256) != 64 or any(character not in "0123456789abcdef" for character in sha256):
            raise TranslationError(f"{context}.sha256 must contain 64 hexadecimal characters")
        return CompositeTokenSegment(token, start, end, sha256)
    raise TranslationError(f"{context}.kind must be 'text' or 'token'")


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
        notes=_optional_string(value, "notes", context=context),
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


def _parse_anchors(table: dict[str, object], context: str) -> tuple[TranslationAnchor, ...]:
    raw_anchors = table.get("anchors")
    has_single = "file" in table or "offset" in table
    if raw_anchors is not None and has_single:
        raise TranslationError(f"{context} must use either file/offset or anchors, not both")
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


def _wrap_text(value: str, box_width: int) -> tuple[str, ...]:
    lines: list[str] = []
    for paragraph in value.splitlines() or [""]:
        lines.extend(
            textwrap.wrap(
                paragraph,
                width=box_width,
                break_long_words=False,
                break_on_hyphens=False,
                replace_whitespace=False,
            )
            or [""]
        )
    return tuple(lines)


def _composite_parts(value: str) -> tuple[tuple[str, str], ...]:
    parts: list[tuple[str, str]] = []
    position = 0
    for match in _TOKEN_MARKER.finditer(value):
        literal = value[position : match.start()]
        if any(character in literal for character in "⟦⟧"):
            raise TranslationError("contains malformed authoring token")
        if literal:
            parts.append(("text", literal))
        parts.append(("token", match.group(1)))
        position = match.end()
    literal = value[position:]
    if any(character in literal for character in "⟦⟧"):
        raise TranslationError("contains malformed authoring token")
    if literal:
        parts.append(("text", literal))
    if not any(kind == "token" for kind, _ in parts):
        raise TranslationError("must contain at least one authoring token")
    return tuple(parts)


def _composite_pattern(parts: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    return tuple(value if kind == "token" else "text" for kind, value in parts)


def _wrap_composite(
    value: str,
    box_width: int,
    tokens: dict[str, TranslationToken],
) -> str:
    replacements: list[tuple[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        token_id = match.group(1)
        token = tokens.get(token_id)
        if token is None:
            raise TranslationError(f"unknown authoring token {token_id!r}")
        placeholder = chr(0xE000 + len(replacements)) * token.max_width
        replacements.append((placeholder, match.group(0)))
        return placeholder

    temporary = _TOKEN_MARKER.sub(replace, value)
    wrapped = "\n".join(_wrap_text(temporary, box_width))
    for placeholder, marker in replacements:
        wrapped = wrapped.replace(placeholder, marker)
    return wrapped


def _composite_visual_length(value: str, tokens: dict[str, TranslationToken]) -> int:
    return len(
        _TOKEN_MARKER.sub(
            lambda match: "x" * tokens[match.group(1)].max_width,
            value,
        )
    )


def _validate_catalog(
    files: tuple[TranslationFile, ...],
    tokens: tuple[TranslationToken, ...],
    entries: tuple[TranslationEntry, ...],
    composites: tuple[CompositeTranslationEntry, ...],
) -> None:
    file_names = [file.file for file in files]
    if len(file_names) != len({name.casefold() for name in file_names}):
        raise TranslationError("translation catalog contains duplicate file names")
    known_files = set(file_names)
    files_by_name = {file.file: file for file in files}
    token_ids = [token.id for token in tokens]
    if len(token_ids) != len(set(token_ids)):
        raise TranslationError("translation catalog contains duplicate token IDs")
    tokens_by_id = {token.id: token for token in tokens}
    initializer_anchors: set[tuple[str, int]] = set()
    for token in tokens:
        for initializer in token.initializers:
            slot_token = interpolation_token_for_slot(initializer.slot)
            if slot_token != token.id:
                raise TranslationError(
                    f"{token.id}: initializer slot 0x{initializer.slot:04x} "
                    f"renders {slot_token or 'no known token'}"
                )
            if initializer.file not in known_files:
                raise TranslationError(f"{token.id}: unknown initializer file {initializer.file}")
            anchor = (initializer.file, initializer.offset)
            if anchor in initializer_anchors:
                raise TranslationError(
                    f"duplicate token initializer: {initializer.file}:0x{initializer.offset:04x}"
                )
            initializer_anchors.add(anchor)
    ids: set[str] = set()
    anchors: set[tuple[str, int]] = set()
    for entry in entries:
        if entry.id in ids:
            raise TranslationError(f"duplicate translation ID: {entry.id}")
        ids.add(entry.id)
        for entry_anchor in entry.anchors:
            if entry_anchor.file not in known_files:
                raise TranslationError(f"{entry.id}: unknown source file {entry_anchor.file}")
            anchor = (entry_anchor.file, entry_anchor.offset)
            if anchor in anchors:
                raise TranslationError(
                    f"duplicate translation anchor: {entry_anchor.file}:0x{entry_anchor.offset:04x}"
                )
            anchors.add(anchor)
        effective_widths = {
            entry.box_width
            if entry.box_width is not None
            else files_by_name[entry_anchor.file].box_width
            for entry_anchor in entry.anchors
        }
        for box_width in effective_widths:
            if box_width is None:
                continue
            for line in entry.wrapped_translation_for(box_width):
                if len(line) > box_width:
                    raise TranslationError(
                        f"{entry.id}: word longer than box width {box_width}: {line!r}"
                    )

    interpolation_spans: set[tuple[str, int, int]] = set()
    for entry in composites:
        if entry.id in ids:
            raise TranslationError(f"duplicate translation ID: {entry.id}")
        ids.add(entry.id)
        source_parts = _composite_parts(entry.source)
        translation_parts = _composite_parts(entry.translation)
        source_pattern = _composite_pattern(source_parts)
        if _composite_pattern(translation_parts) != source_pattern:
            raise TranslationError(
                f"{entry.id}: translation token/text structure differs from source"
            )
        for kind, value in source_parts:
            if kind == "token" and value not in tokens_by_id:
                raise TranslationError(f"{entry.id}: unknown authoring token {value!r}")
        encoding = "ascii" if entry.target_mode == 2 else "cp932"
        for kind, value in translation_parts:
            if kind != "text":
                continue
            try:
                encoded = value.encode(encoding)
            except UnicodeEncodeError as error:
                raise TranslationError(
                    f"{entry.id}: translation cannot be encoded in mode "
                    f"{entry.target_mode} ({encoding})"
                ) from error
            if entry.target_mode == 2 and not all(
                byte == 0x0A or 0x20 <= byte <= 0x7E for byte in encoded
            ):
                raise TranslationError(
                    f"{entry.id}: mode 2 translation must contain printable ASCII or newlines"
                )
            if entry.target_mode == 1 and any(
                ord(character) < 0x20 and character != "\n" for character in value
            ):
                raise TranslationError(
                    f"{entry.id}: mode 1 translation contains an unsupported control"
                )

        for occurrence in entry.occurrences:
            if occurrence.file not in known_files:
                raise TranslationError(f"{entry.id}: unknown source file {occurrence.file}")
            occurrence_parts = tuple(
                ("text", segment.source)
                if isinstance(segment, CompositeTextSegment)
                else ("token", segment.token)
                for segment in occurrence.segments
            )
            if _composite_pattern(occurrence_parts) != source_pattern:
                raise TranslationError(
                    f"{entry.id}: occurrence structure differs from canonical source"
                )
            if occurrence_parts != source_parts:
                raise TranslationError(f"{entry.id}: occurrence text differs from canonical source")
            for segment in occurrence.segments:
                if isinstance(segment, CompositeTextSegment):
                    anchor = (segment.anchor.file, segment.anchor.offset)
                    if anchor in anchors:
                        raise TranslationError(
                            "duplicate translation anchor: "
                            f"{segment.anchor.file}:0x{segment.anchor.offset:04x}"
                        )
                    anchors.add(anchor)
                    continue
                if segment.token not in tokens_by_id:
                    raise TranslationError(f"{entry.id}: unknown authoring token {segment.token!r}")
                span = (occurrence.file, segment.start, segment.end)
                if span in interpolation_spans:
                    raise TranslationError(
                        f"duplicate interpolation span: {occurrence.file}:"
                        f"0x{segment.start:04x}-0x{segment.end:04x}"
                    )
                interpolation_spans.add(span)

        effective_widths = {
            entry.box_width
            if entry.box_width is not None
            else files_by_name[occurrence.file].box_width
            for occurrence in entry.occurrences
        }
        for box_width in effective_widths:
            if box_width is None:
                continue
            wrapped = _wrap_composite(entry.translation, box_width, tokens_by_id)
            for line in wrapped.splitlines() or [""]:
                if _composite_visual_length(line, tokens_by_id) > box_width:
                    raise TranslationError(
                        f"{entry.id}: word longer than box width {box_width}: {line!r}"
                    )


def _relative_path(value: str, context: str) -> str:
    parts = value.split("/")
    if "\\" in value or any(part in ("", ".", "..") for part in parts):
        raise TranslationError(f"{context} must be a safe relative path")
    return PurePosixPath(*parts).as_posix()
