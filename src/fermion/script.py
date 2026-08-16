"""Compact full-script extraction for offline translation and analysis."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from fermion.gm import GMError, GMFile


@dataclass(frozen=True)
class ScriptAnchor:
    file: str
    offset: int


@dataclass(frozen=True)
class ScriptGroup:
    id: str
    anchors: tuple[ScriptAnchor, ...]
    mode: int
    speaker: str | None
    attribution: str
    default_name: str | None
    japanese: str
    status: str
    flags: tuple[str, ...]


def collect_mes_files(source: Path) -> list[Path]:
    """Return MES files under a file or directory, deduplicated by content hash."""
    candidates = (
        sorted(path for path in source.rglob("*") if path.suffix.upper() == ".MES")
        if source.is_dir()
        else [source]
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for path in candidates:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest not in seen:
            seen.add(digest)
            unique.append(path)
    return unique


def story_mes_files(
    files: list[Path], *, root: str = "FOP.MES", terminals: tuple[str, ...] = ("MAIN.MES",)
) -> list[Path]:
    """Return the scenario files reachable from the story root, excluding terminals."""
    by_name: dict[str, Path] = {}
    for path in files:
        name = path.name.upper()
        if name in by_name:
            raise GMError(f"multiple content-unique MES files are named {path.name}")
        by_name[name] = path

    root_name = root.upper()
    if root_name not in by_name:
        raise GMError(f"story root {root} is not present in the MES corpus")
    terminal_names = {name.upper() for name in terminals}
    reachable: set[str] = set()
    pending = [root_name]
    while pending:
        name = pending.pop()
        if name in reachable or name in terminal_names:
            continue
        path = by_name.get(name)
        if path is None:
            raise GMError(f"scenario transition targets missing MES file {name}")
        reachable.add(name)
        for transition in GMFile.from_file(path).transitions():
            pending.append(transition.target.upper())

    ordered_names = [root_name, *sorted(reachable - {root_name})]
    return [by_name[name] for name in ordered_names]


def script_groups(files: list[Path]) -> list[ScriptGroup]:
    """Group exact decoded text by mode and proven speaker across unique files."""
    grouped: dict[tuple[int, str | None, str], list[ScriptAnchor]] = defaultdict(list)
    metadata: dict[tuple[int, str | None, str], tuple[str, str | None]] = {}
    speakers_by_text: dict[tuple[int, str], set[str | None]] = defaultdict(set)

    for path in files:
        for item in GMFile.from_file(path).attributed_text_records():
            record = item.record
            if record.text is None or not record.text.strip():
                continue
            speaker = item.speaker.id if item.speaker else None
            key = (record.mode, speaker, record.text)
            grouped[key].append(ScriptAnchor(path.name.upper(), record.offset))
            speakers_by_text[(record.mode, record.text)].add(speaker)
            metadata[key] = (
                item.speaker.source if item.speaker else "unresolved",
                item.speaker.default_name if item.speaker else None,
            )

    groups = []
    ids: dict[str, tuple[int, str | None, str]] = {}
    for key, anchors in grouped.items():
        mode, speaker, japanese = key
        identity = f"{mode}\0{speaker or ''}\0{japanese}".encode()
        digest = hashlib.sha256(identity).hexdigest()[:16]
        line_id = f"gm-{digest}"
        if (previous := ids.get(line_id)) and previous != key:
            raise GMError(f"script inventory ID collision for {line_id}")
        ids[line_id] = key

        flags = []
        if speaker is None:
            flags.append("unresolved-speaker")
        if len(anchors) > 1:
            flags.append("multi-anchor")
        if len(speakers_by_text[(mode, japanese)]) > 1:
            flags.append("speaker-variant")
        status = (
            "needs-speaker"
            if speaker is None
            else "review-context"
            if flags
            else "pending"
        )
        attribution, default_name = metadata[key]
        groups.append(
            ScriptGroup(
                line_id,
                tuple(anchors),
                mode,
                speaker,
                attribution,
                default_name,
                japanese,
                status,
                tuple(flags),
            )
        )
    return groups


def script_lines(path: Path) -> list[tuple[int, str | None, str]]:
    """Return compact attributed mode-1 lines in stream order."""
    gm = GMFile.from_file(path)
    lines = []
    for item in gm.attributed_text_records():
        record = item.record
        if record.mode != 1 or record.text is None or not record.text.strip():
            continue
        escaped = record.text.replace("\\", "\\\\").replace("\n", "\\n")
        speaker = item.speaker.id if item.speaker else None
        lines.append((record.offset, speaker, escaped))
    return lines


def render_script(files: list[Path]) -> str:
    """Render unique MES files as one compact Markdown document."""
    chunks = []
    total = 0
    for path in files:
        stem = path.stem
        lines = script_lines(path)
        total += len(lines)
        chunks.append(f"## {stem}")
        chunks.extend(
            f"[{stem}:{offset:04x}{f' speaker={speaker}' if speaker else ''}] {text}"
            for offset, speaker, text in lines
        )
        chunks.append("")
    total_files = len(files)
    header = [
        f"<!-- {total_files} unique MES files, {total} mode-1 text records -->\n"
    ]
    return "\n".join(header + chunks)
