"""Materialize verified working disks from the preservation archive."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

from fermion.d88 import d88_to_raw


@dataclass(frozen=True)
class ExpectedDisk:
    letter: str
    sha1: str


EXPECTED_DISKS = (
    ExpectedDisk("A", "b5af3375766b6a685c5f51bd7d1289f0d0fd38ad"),
    ExpectedDisk("B", "8a62c5191d1f093793e75e29d0595427bfa0caf8"),
    ExpectedDisk("C", "6d252df7645d9357a9d2d258fa983382583d9d2e"),
    ExpectedDisk("D", "b5e38ad283b79cff0605152f3de6f53e0baf8379"),
)


class DiskVerificationError(ValueError):
    """Raised when preservation media does not match the source of record."""


def _disk_letter(member: str) -> str | None:
    match = re.search(r"\(Disk ([A-D])\)\.d88$", member, re.IGNORECASE)
    return match.group(1).upper() if match else None


def materialize(archive: Path, output_dir: Path) -> list[Path]:
    """Convert all four archived D88 images to verified HDM images."""
    expected = {disk.letter: disk.sha1 for disk in EXPECTED_DISKS}
    converted: dict[str, bytes] = {}

    with ZipFile(archive) as source:
        for member in source.namelist():
            letter = _disk_letter(member)
            if letter is None or not member.lower().startswith("d88/"):
                continue
            if letter in converted:
                raise DiskVerificationError(f"archive contains duplicate Disk {letter} D88 images")
            converted[letter] = d88_to_raw(source.read(member))

    missing = sorted(set(expected) - set(converted))
    if missing:
        raise DiskVerificationError(f"archive is missing D88 disk(s): {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for letter in sorted(converted):
        raw = converted[letter]
        digest = hashlib.sha1(raw).hexdigest()
        if digest != expected[letter]:
            raise DiskVerificationError(
                f"Disk {letter} SHA-1 mismatch: expected {expected[letter]}, got {digest}"
            )
        destination = output_dir / f"fermion-{letter.lower()}.hdm"
        destination.write_bytes(raw)
        results.append(destination)
    return results
