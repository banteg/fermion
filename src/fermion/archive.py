"""Read the simple file archives consumed by Fermion's installer."""

from __future__ import annotations

import struct
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


class InstallerArchive:
    """A read-only view of a DISKA/DISKB/DISKC/DISKD payload."""

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
        names = set()
        for index in range(count):
            position = 2 + index * DIRECTORY_ENTRY_SIZE
            name_bytes = data[position : position + FILENAME_SIZE].split(b"\0", 1)[0]
            if not name_bytes:
                raise ArchiveError(f"entry {index} has an empty filename")
            name = name_bytes.decode("cp932")
            if name in names:
                raise ArchiveError(f"archive contains duplicate filename {name!r}")
            if PurePath(name).name != name or name in (".", ".."):
                raise ArchiveError(f"entry {index} has unsafe filename {name!r}")
            size = struct.unpack_from("<H", data, position + FILENAME_SIZE)[0]
            offset = struct.unpack_from("<I", data, position + FILENAME_SIZE + 2)[0]
            if offset < directory_end or offset + size > len(data):
                raise ArchiveError(
                    f"entry {name!r} points outside the archive: offset={offset}, size={size}"
                )
            entries.append(ArchiveEntry(name=name, size=size, offset=offset))
            names.add(name)
        self.entries = entries

    @classmethod
    def from_file(cls, path: Path) -> InstallerArchive:
        return cls(path.read_bytes())

    def read(self, entry: ArchiveEntry) -> bytes:
        return self.data[entry.offset : entry.offset + entry.size]

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
