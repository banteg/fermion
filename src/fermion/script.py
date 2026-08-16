"""Compact full-script extraction for offline translation and analysis."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fermion.gm import GMFile


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
