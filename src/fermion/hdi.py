"""Anex86 HDI and PC-98 partition access for filesystem-aware patching."""

from __future__ import annotations

import struct
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fermion.fat import FAT12, Entry, FATError

PARTITION_ENTRY_SIZE = 32
PARTITION_COUNT = 16


class HDIError(ValueError):
    """Raised when an HDI image or requested filesystem operation is unsafe."""


@dataclass(frozen=True)
class HDIGeometry:
    header_size: int
    disk_size: int
    sector_size: int
    sectors_per_track: int
    heads: int
    cylinders: int


@dataclass(frozen=True)
class Partition:
    index: int
    name: str
    start_offset: int


class HDIImage:
    """A validated Anex86 HDI with discoverable FAT12 partitions."""

    def __init__(self, data: bytes):
        self.data = data
        self.geometry = _read_geometry(data)
        self.partitions = _read_partitions(data, self.geometry)

    @classmethod
    def from_file(cls, path: Path) -> HDIImage:
        return cls(path.read_bytes())

    def entries(self) -> list[tuple[Partition, Entry]]:
        """Return every visible entry from every FAT12 partition."""
        result = []
        for partition, filesystem, _size in self._filesystems():
            result.extend((partition, entry) for entry in filesystem.entries())
        return result

    def read_file(self, path: str | PurePosixPath) -> bytes:
        matches = self._find(path)
        if not matches:
            raise HDIError(f"HDI does not contain {str(path)!r}")
        if len(matches) > 1:
            raise HDIError(f"HDI path is ambiguous across partitions: {str(path)!r}")
        _partition, filesystem, entry, _size = matches[0]
        return filesystem.read_file(entry)

    def replace_files(self, replacements: Mapping[str | PurePosixPath, bytes]) -> HDIImage:
        """Return a new HDI with selected FAT files replaced and the input untouched."""
        normalized: dict[tuple[str, ...], tuple[str | PurePosixPath, bytes]] = {}
        for path, payload in replacements.items():
            key = _path_key(path)
            if key in normalized:
                raise HDIError(f"duplicate HDI replacement path: {str(path)!r}")
            normalized[key] = (path, payload)

        groups: dict[int, tuple[Partition, int, dict[str | PurePosixPath, bytes]]] = {}
        for path, payload in normalized.values():
            matches = self._find(path)
            if not matches:
                raise HDIError(f"HDI does not contain {str(path)!r}")
            if len(matches) > 1:
                raise HDIError(f"HDI path is ambiguous across partitions: {str(path)!r}")
            partition, _filesystem, _entry, volume_size = matches[0]
            if partition.index not in groups:
                groups[partition.index] = (partition, volume_size, {})
            groups[partition.index][2][path] = payload

        output = bytearray(self.data)
        for partition, volume_size, files in groups.values():
            start = partition.start_offset
            filesystem = FAT12(bytes(output[start : start + volume_size]))
            rebuilt = filesystem.replace_files(files)
            output[start : start + volume_size] = rebuilt

        result = HDIImage(bytes(output))
        for path, payload in normalized.values():
            if result.read_file(path) != payload:
                raise HDIError(f"HDI replacement verification failed for {str(path)!r}")
        return result

    def _filesystems(self) -> list[tuple[Partition, FAT12, int]]:
        filesystems = []
        for partition in self.partitions:
            try:
                probe = FAT12(self.data[partition.start_offset :])
            except FATError:
                continue
            volume_size = probe.geometry.total_sectors * probe.geometry.bytes_per_sector
            end = partition.start_offset + volume_size
            if end > len(self.data):
                raise HDIError(f"partition {partition.name!r} extends beyond the HDI")
            filesystems.append(
                (partition, FAT12(self.data[partition.start_offset:end]), volume_size)
            )
        if not filesystems:
            raise HDIError("HDI contains no supported FAT12 partition")
        return filesystems

    def _find(self, path: str | PurePosixPath) -> list[tuple[Partition, FAT12, Entry, int]]:
        key = _path_key(path)
        matches = []
        for partition, filesystem, volume_size in self._filesystems():
            for entry in filesystem.entries():
                if _path_key(entry.path) == key:
                    matches.append((partition, filesystem, entry, volume_size))
        return matches


def write_replaced_hdi(
    image_path: Path,
    replacements: Mapping[str | PurePosixPath, bytes],
    output_path: Path,
) -> HDIImage:
    """Patch a copied HDI, refusing in-place or pre-existing output."""
    if output_path.resolve() == image_path.resolve():
        raise HDIError("output must differ from the input image")
    if output_path.exists():
        raise HDIError(f"output already exists: {output_path}")
    result = HDIImage.from_file(image_path).replace_files(replacements)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.data)
    return result


def _read_geometry(data: bytes) -> HDIGeometry:
    if len(data) < 32:
        raise HDIError("HDI is too short to contain an Anex86 header")
    header_size, disk_size, sector_size, sectors, heads, cylinders = struct.unpack_from(
        "<6I", data, 8
    )
    if header_size < 32 or header_size > len(data):
        raise HDIError(f"invalid HDI header size: {header_size}")
    if sector_size not in (128, 256, 512, 1024, 2048, 4096):
        raise HDIError(f"unsupported HDI physical sector size: {sector_size}")
    if not all((disk_size, sectors, heads, cylinders)):
        raise HDIError("HDI header contains incomplete geometry")
    geometry_size = sector_size * sectors * heads * cylinders
    if geometry_size != disk_size:
        raise HDIError(
            f"HDI geometry declares {geometry_size} bytes but header declares {disk_size}"
        )
    if header_size + disk_size > len(data):
        raise HDIError("HDI disk payload is truncated")
    return HDIGeometry(header_size, disk_size, sector_size, sectors, heads, cylinders)


def _read_partitions(data: bytes, geometry: HDIGeometry) -> tuple[Partition, ...]:
    table = geometry.header_size + geometry.sector_size
    table_end = table + PARTITION_COUNT * PARTITION_ENTRY_SIZE
    if table_end > geometry.header_size + geometry.disk_size:
        raise HDIError("HDI is too short to contain a PC-98 partition table")
    partitions = []
    for index in range(PARTITION_COUNT):
        offset = table + index * PARTITION_ENTRY_SIZE
        raw = data[offset : offset + PARTITION_ENTRY_SIZE]
        if raw[0] == 0:
            continue
        start_sector = raw[8]
        start_head = raw[9]
        start_cylinder = struct.unpack_from("<H", raw, 10)[0]
        if (
            start_sector >= geometry.sectors_per_track
            or start_head >= geometry.heads
            or start_cylinder >= geometry.cylinders
        ):
            raise HDIError(f"partition {index} has an invalid start address")
        logical_sector = (
            (start_cylinder * geometry.heads + start_head) * geometry.sectors_per_track
            + start_sector
        )
        start = geometry.header_size + logical_sector * geometry.sector_size
        name_bytes = raw[16:32].split(b"\0", 1)[0].rstrip(b" ")
        try:
            name = name_bytes.decode("cp932") or f"partition-{index}"
        except UnicodeDecodeError as error:
            raise HDIError(f"partition {index} has an invalid CP932 name") from error
        partitions.append(Partition(index, name, start))
    if not partitions:
        raise HDIError("HDI partition table contains no entries")
    return tuple(partitions)


def _path_key(path: str | PurePosixPath) -> tuple[str, ...]:
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or not parsed.parts or any(part in ("", ".", "..") for part in parsed.parts):
        raise HDIError(f"unsafe HDI path: {str(path)!r}")
    return tuple(part.casefold() for part in parsed.parts)
