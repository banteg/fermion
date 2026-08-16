"""Read and rebuild the simple file archives consumed by Fermion's installer."""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePath

DIRECTORY_ENTRY_SIZE = 19
FILENAME_SIZE = 13


class ArchiveError(ValueError):
    """Raised when a Silky's installer archive is malformed."""


@dataclass(frozen=True)
class ArchiveEntry:
    name: str
    size: int
    offset: int
    raw_name: bytes


class InstallerArchive:
    """A validated view of a DISKA/DISKB/DISKC/DISKD payload."""

    def __init__(self, data: bytes):
        if len(data) < 2:
            raise ArchiveError("archive is too short to contain a file count")
        self.data = data
        count = struct.unpack_from("<H", data)[0]
        directory_end = 2 + count * DIRECTORY_ENTRY_SIZE
        if directory_end > len(data):
            raise ArchiveError(
                f"directory for {count} files ends at {directory_end}, beyond the archive"
            )

        entries = []
        names: set[str] = set()
        for index in range(count):
            position = 2 + index * DIRECTORY_ENTRY_SIZE
            raw_name = data[position : position + FILENAME_SIZE]
            name_bytes = raw_name.split(b"\0", 1)[0]
            if not name_bytes:
                raise ArchiveError(f"entry {index} has an empty filename")
            name = name_bytes.decode("cp932")
            name_key = name.casefold()
            if name_key in names:
                raise ArchiveError(f"archive contains duplicate filename {name!r}")
            if PurePath(name).name != name or name in (".", ".."):
                raise ArchiveError(f"entry {index} has unsafe filename {name!r}")
            size = struct.unpack_from("<H", data, position + FILENAME_SIZE)[0]
            offset = struct.unpack_from("<I", data, position + FILENAME_SIZE + 2)[0]
            if offset < directory_end or offset + size > len(data):
                raise ArchiveError(
                    f"entry {name!r} points outside the archive: offset={offset}, size={size}"
                )
            entries.append(
                ArchiveEntry(name=name, size=size, offset=offset, raw_name=raw_name)
            )
            names.add(name_key)
        self.entries = entries

    @classmethod
    def from_file(cls, path: Path) -> InstallerArchive:
        return cls(path.read_bytes())

    def read(self, entry: ArchiveEntry) -> bytes:
        return self.data[entry.offset : entry.offset + entry.size]

    def entry(self, name: str) -> ArchiveEntry:
        """Return one archive entry by case-insensitive DOS filename."""
        matches = [entry for entry in self.entries if entry.name.casefold() == name.casefold()]
        if not matches:
            raise ArchiveError(f"archive does not contain {name!r}")
        if len(matches) > 1:
            raise ArchiveError(f"archive filename is ambiguous: {name!r}")
        return matches[0]

    def rebuild(self, replacements: Mapping[str, bytes]) -> bytes:
        """Repack the archive in its original order with selected payloads replaced."""
        by_name = {entry.name.casefold(): entry for entry in self.entries}
        normalized: dict[str, bytes] = {}
        for name, payload in replacements.items():
            key = name.casefold()
            if key in normalized:
                raise ArchiveError(f"duplicate replacement filename {name!r}")
            if key not in by_name:
                raise ArchiveError(f"archive does not contain {name!r}")
            if len(payload) > 0xFFFF:
                raise ArchiveError(
                    f"replacement {name!r} is too large for the archive: {len(payload)} bytes"
                )
            normalized[key] = payload

        directory_size = 2 + len(self.entries) * DIRECTORY_ENTRY_SIZE
        directory = bytearray(struct.pack("<H", len(self.entries)))
        payloads = bytearray()
        for entry in self.entries:
            payload = normalized.get(entry.name.casefold(), self.read(entry))
            directory.extend(entry.raw_name)
            directory.extend(struct.pack("<H", len(payload)))
            directory.extend(struct.pack("<I", directory_size + len(payloads)))
            payloads.extend(payload)

        rebuilt = bytes(directory + payloads)
        verified = InstallerArchive(rebuilt)
        if [entry.name for entry in verified.entries] != [entry.name for entry in self.entries]:
            raise ArchiveError("rebuilt archive changed directory ordering")
        return rebuilt

    def extract(self, destination: Path) -> list[Path]:
        destination.mkdir(parents=True, exist_ok=True)
        written = []
        for entry in self.entries:
            target = destination / entry.name
            payload = self.read(entry)
            if target.exists() and target.read_bytes() != payload:
                raise ArchiveError(f"refusing to overwrite different file: {target}")
            if not target.exists():
                target.write_bytes(payload)
            written.append(target)
        return written
