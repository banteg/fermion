"""Minimal read-only FAT12 support for the original PC-98 floppy images."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class FATError(ValueError):
    """Raised when a FAT image is malformed or unsupported."""


@dataclass(frozen=True)
class Geometry:
    bytes_per_sector: int
    sectors_per_cluster: int
    reserved_sectors: int
    fat_count: int
    root_entries: int
    total_sectors: int
    sectors_per_fat: int

    @property
    def root_sectors(self) -> int:
        size = self.root_entries * 32
        return (size + self.bytes_per_sector - 1) // self.bytes_per_sector

    @property
    def first_root_sector(self) -> int:
        return self.reserved_sectors + self.fat_count * self.sectors_per_fat

    @property
    def first_data_sector(self) -> int:
        return self.first_root_sector + self.root_sectors

    @property
    def cluster_size(self) -> int:
        return self.bytes_per_sector * self.sectors_per_cluster


@dataclass(frozen=True)
class Entry:
    path: PurePosixPath
    attributes: int
    first_cluster: int
    size: int

    @property
    def is_directory(self) -> bool:
        return bool(self.attributes & 0x10)


class FAT12:
    """A small, read-only FAT12 filesystem reader."""

    def __init__(self, data: bytes):
        self.data = data
        self.geometry = _read_geometry(data)
        expected_size = self.geometry.total_sectors * self.geometry.bytes_per_sector
        if len(data) < expected_size:
            raise FATError(f"filesystem declares {expected_size} bytes, image has {len(data)}")
        fat_start = self.geometry.reserved_sectors * self.geometry.bytes_per_sector
        fat_size = self.geometry.sectors_per_fat * self.geometry.bytes_per_sector
        self._fat = data[fat_start : fat_start + fat_size]

    @classmethod
    def from_file(cls, path: Path) -> FAT12:
        return cls(path.read_bytes())

    def entries(self) -> list[Entry]:
        """Return all visible files and directories recursively."""
        root_start = self.geometry.first_root_sector * self.geometry.bytes_per_sector
        root_size = self.geometry.root_sectors * self.geometry.bytes_per_sector
        return self._read_directory(self.data[root_start : root_start + root_size], PurePosixPath())

    def read_file(self, entry: Entry) -> bytes:
        if entry.is_directory:
            raise FATError(f"{entry.path} is a directory")
        return self._read_chain(entry.first_cluster)[: entry.size]

    def extract(self, destination: Path) -> list[Path]:
        """Extract all visible files, preserving the on-disk hierarchy."""
        written = []
        for entry in self.entries():
            target = destination.joinpath(*entry.path.parts)
            if entry.is_directory:
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.read_file(entry))
            written.append(target)
        return written

    def _read_directory(self, data: bytes, parent: PurePosixPath) -> list[Entry]:
        entries = []
        for offset in range(0, len(data), 32):
            raw = data[offset : offset + 32]
            if len(raw) < 32 or raw[0] == 0x00:
                break
            if raw[0] == 0xE5 or raw[11] == 0x0F:
                continue
            attributes = raw[11]
            if attributes & 0x08:  # volume label
                continue
            name = _decode_name(raw[:8], raw[8:11])
            if name in (".", ".."):
                continue
            entry = Entry(
                path=parent / name,
                attributes=attributes,
                first_cluster=struct.unpack_from("<H", raw, 26)[0],
                size=struct.unpack_from("<I", raw, 28)[0],
            )
            entries.append(entry)
            if entry.is_directory:
                entries.extend(
                    self._read_directory(self._read_chain(entry.first_cluster), entry.path)
                )
        return entries

    def _read_chain(self, first_cluster: int) -> bytes:
        if first_cluster < 2:
            return b""
        chunks = []
        seen = set()
        cluster = first_cluster
        while cluster < 0xFF8:
            if cluster in seen:
                raise FATError(f"cluster chain loops at {cluster}")
            if cluster == 0xFF7:
                raise FATError("cluster chain contains a bad cluster")
            seen.add(cluster)
            sector = self.geometry.first_data_sector + (
                cluster - 2
            ) * self.geometry.sectors_per_cluster
            offset = sector * self.geometry.bytes_per_sector
            end = offset + self.geometry.cluster_size
            if end > len(self.data):
                raise FATError(f"cluster {cluster} points beyond the image")
            chunks.append(self.data[offset:end])
            cluster = self._next_cluster(cluster)
        return b"".join(chunks)

    def _next_cluster(self, cluster: int) -> int:
        offset = cluster + cluster // 2
        if offset + 2 > len(self._fat):
            raise FATError(f"cluster {cluster} has no FAT entry")
        value = struct.unpack_from("<H", self._fat, offset)[0]
        return (value >> 4) & 0xFFF if cluster & 1 else value & 0xFFF


def _read_geometry(data: bytes) -> Geometry:
    if len(data) < 36:
        raise FATError("image is too short to contain a DOS boot sector")
    bytes_per_sector = struct.unpack_from("<H", data, 11)[0]
    sectors_per_cluster = data[13]
    reserved_sectors = struct.unpack_from("<H", data, 14)[0]
    fat_count = data[16]
    root_entries = struct.unpack_from("<H", data, 17)[0]
    total_16 = struct.unpack_from("<H", data, 19)[0]
    sectors_per_fat = struct.unpack_from("<H", data, 22)[0]
    total_32 = struct.unpack_from("<I", data, 32)[0]
    total_sectors = total_16 or total_32

    if bytes_per_sector not in (128, 256, 512, 1024, 2048, 4096):
        raise FATError(f"unsupported bytes per sector: {bytes_per_sector}")
    if not all((sectors_per_cluster, reserved_sectors, fat_count, total_sectors, sectors_per_fat)):
        raise FATError("boot sector contains incomplete FAT geometry")
    return Geometry(
        bytes_per_sector=bytes_per_sector,
        sectors_per_cluster=sectors_per_cluster,
        reserved_sectors=reserved_sectors,
        fat_count=fat_count,
        root_entries=root_entries,
        total_sectors=total_sectors,
        sectors_per_fat=sectors_per_fat,
    )


def _decode_name(stem: bytes, suffix: bytes) -> str:
    name = stem.rstrip(b" ").decode("cp932")
    extension = suffix.rstrip(b" ").decode("cp932")
    return f"{name}.{extension}" if extension else name
