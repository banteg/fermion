"""Minimal FAT12 support for PC-98 floppy and hard-disk filesystems."""

from __future__ import annotations

import struct
from collections.abc import Iterator, Mapping
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

    @property
    def data_clusters(self) -> int:
        data_sectors = self.total_sectors - self.first_data_sector
        return data_sectors // self.sectors_per_cluster


@dataclass(frozen=True)
class Entry:
    path: PurePosixPath
    attributes: int
    first_cluster: int
    size: int
    directory_offset: int

    @property
    def is_directory(self) -> bool:
        return bool(self.attributes & 0x10)


class FAT12:
    """A small FAT12 reader with conservative whole-file replacement."""

    def __init__(self, data: bytes):
        self.data = data
        self.geometry = _read_geometry(data)
        expected_size = self.geometry.total_sectors * self.geometry.bytes_per_sector
        if len(data) < expected_size:
            raise FATError(f"filesystem declares {expected_size} bytes, image has {len(data)}")
        fat_start = self.geometry.reserved_sectors * self.geometry.bytes_per_sector
        fat_size = self.geometry.sectors_per_fat * self.geometry.bytes_per_sector
        self._fat_offsets = tuple(fat_start + index * fat_size for index in range(self.geometry.fat_count))
        fats = tuple(data[offset : offset + fat_size] for offset in self._fat_offsets)
        if any(len(fat) != fat_size for fat in fats):
            raise FATError("filesystem contains a truncated FAT")
        if any(fat != fats[0] for fat in fats[1:]):
            raise FATError("FAT copies do not match")
        if self.geometry.data_clusters >= 4085:
            raise FATError(
                f"filesystem has {self.geometry.data_clusters} clusters and is not FAT12"
            )
        self._fat = fats[0]

    @classmethod
    def from_file(cls, path: Path) -> FAT12:
        return cls(path.read_bytes())

    def entries(self) -> list[Entry]:
        """Return all visible files and directories recursively."""
        root_start = self.geometry.first_root_sector * self.geometry.bytes_per_sector
        root_size = self.geometry.root_sectors * self.geometry.bytes_per_sector
        slots = self._contiguous_slots(root_start, root_size)
        return self._read_directory(slots, PurePosixPath(), set())

    def entry(self, path: str | PurePosixPath) -> Entry:
        """Return one entry by case-insensitive DOS path."""
        key = _path_key(path)
        matches = [entry for entry in self.entries() if _path_key(entry.path) == key]
        if not matches:
            raise FATError(f"filesystem does not contain {str(path)!r}")
        if len(matches) > 1:
            raise FATError(f"filesystem path is ambiguous: {str(path)!r}")
        return matches[0]

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

    def replace_files(self, replacements: Mapping[str | PurePosixPath, bytes]) -> bytes:
        """Return a same-sized image with selected files replaced and reallocated."""
        all_entries = self.entries()
        owners: dict[int, PurePosixPath] = {}
        for entry in all_entries:
            chain = self._cluster_chain(entry.first_cluster)
            if not entry.is_directory:
                required = (
                    entry.size + self.geometry.cluster_size - 1
                ) // self.geometry.cluster_size
                if len(chain) < required:
                    raise FATError(
                        f"{entry.path} needs {required} clusters but its chain has {len(chain)}"
                    )
            for cluster in chain:
                owner = owners.get(cluster)
                if owner is not None:
                    raise FATError(
                        f"cluster {cluster} is shared by {owner} and {entry.path}"
                    )
                owners[cluster] = entry.path

        normalized: dict[tuple[str, ...], tuple[Entry, bytes]] = {}
        for path, payload in replacements.items():
            key = _path_key(path)
            if key in normalized:
                raise FATError(f"duplicate replacement path: {str(path)!r}")
            key_matches = [entry for entry in all_entries if _path_key(entry.path) == key]
            if not key_matches:
                raise FATError(f"filesystem does not contain {str(path)!r}")
            if len(key_matches) > 1:
                raise FATError(f"filesystem path is ambiguous: {str(path)!r}")
            entry = key_matches[0]
            if entry.is_directory:
                raise FATError(f"cannot replace directory: {entry.path}")
            normalized[key] = (entry, payload)

        if not normalized:
            return self.data

        plans: list[tuple[Entry, bytes, list[int]]] = []
        target_clusters: set[int] = set()
        for entry, payload in normalized.values():
            chain = self._cluster_chain(entry.first_cluster)
            plans.append((entry, payload, chain))
            target_clusters.update(chain)

        free = {
            cluster
            for cluster in range(2, self.geometry.data_clusters + 2)
            if self._fat_value(cluster) == 0
        }
        available = free | target_clusters
        requirements: list[tuple[Entry, bytes, int, list[int]]] = []
        for entry, payload, old_chain in sorted(plans, key=lambda item: _path_key(item[0].path)):
            count = (len(payload) + self.geometry.cluster_size - 1) // self.geometry.cluster_size
            selected = old_chain[:count]
            available.difference_update(selected)
            requirements.append((entry, payload, count, selected))

        allocations: list[tuple[Entry, bytes, list[int]]] = []
        for entry, payload, count, preferred in requirements:
            selected = list(preferred)
            needed = count - len(selected)
            if needed:
                candidates = sorted(available)
                if len(candidates) < needed:
                    raise FATError(
                        f"not enough free clusters to replace {entry.path}: "
                        f"need {needed}, have {len(candidates)}"
                    )
                extra = candidates[:needed]
                selected.extend(extra)
                available.difference_update(extra)
            allocations.append((entry, payload, selected))

        output = bytearray(self.data)
        for cluster in target_clusters:
            self._set_fat_value(output, cluster, 0)
        for entry, payload, chain in allocations:
            for index, cluster in enumerate(chain):
                next_cluster = chain[index + 1] if index + 1 < len(chain) else 0xFFF
                self._set_fat_value(output, cluster, next_cluster)
                start = self._cluster_offset(cluster)
                end = start + self.geometry.cluster_size
                output[start:end] = bytes(self.geometry.cluster_size)
                chunk = payload[
                    index * self.geometry.cluster_size : (index + 1) * self.geometry.cluster_size
                ]
                output[start : start + len(chunk)] = chunk
            first_cluster = chain[0] if chain else 0
            struct.pack_into("<H", output, entry.directory_offset + 26, first_cluster)
            struct.pack_into("<I", output, entry.directory_offset + 28, len(payload))

        rebuilt = bytes(output)
        verified = FAT12(rebuilt)
        for entry, payload, _chain in allocations:
            if verified.read_file(verified.entry(entry.path)) != payload:
                raise FATError(f"replacement verification failed for {entry.path}")
        return rebuilt

    def _read_directory(
        self,
        slots: Iterator[tuple[bytes, int]],
        parent: PurePosixPath,
        seen_directories: set[int],
    ) -> list[Entry]:
        entries = []
        for raw, directory_offset in slots:
            if raw[0] == 0x00:
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
                directory_offset=directory_offset,
            )
            entries.append(entry)
            if entry.is_directory:
                if entry.first_cluster in seen_directories:
                    raise FATError(f"directory tree reuses cluster {entry.first_cluster}")
                seen_directories.add(entry.first_cluster)
                entries.extend(self._read_directory(self._cluster_slots(entry.first_cluster), entry.path, seen_directories))
        return entries

    def _read_chain(self, first_cluster: int) -> bytes:
        return b"".join(
            self.data[self._cluster_offset(cluster) : self._cluster_offset(cluster) + self.geometry.cluster_size]
            for cluster in self._cluster_chain(first_cluster)
        )

    def _cluster_chain(self, first_cluster: int) -> list[int]:
        if first_cluster < 2:
            return []
        chain = []
        seen = set()
        cluster = first_cluster
        maximum = self.geometry.data_clusters + 1
        while cluster < 0xFF8:
            if cluster == 0xFF7:
                raise FATError("cluster chain contains a bad cluster")
            if cluster < 2 or cluster > maximum:
                raise FATError(f"cluster chain points outside the data area: {cluster}")
            if cluster in seen:
                raise FATError(f"cluster chain loops at {cluster}")
            seen.add(cluster)
            chain.append(cluster)
            cluster = self._fat_value(cluster)
            if cluster == 0:
                raise FATError("allocated cluster chain terminates in a free cluster")
        return chain

    def _cluster_offset(self, cluster: int) -> int:
        sector = self.geometry.first_data_sector + (
            cluster - 2
        ) * self.geometry.sectors_per_cluster
        offset = sector * self.geometry.bytes_per_sector
        end = offset + self.geometry.cluster_size
        if cluster < 2 or end > len(self.data):
            raise FATError(f"cluster {cluster} points beyond the image")
        return offset

    def _contiguous_slots(self, start: int, size: int) -> Iterator[tuple[bytes, int]]:
        for offset in range(start, start + size, 32):
            raw = self.data[offset : offset + 32]
            if len(raw) < 32:
                raise FATError("directory entry is truncated")
            yield raw, offset

    def _cluster_slots(self, first_cluster: int) -> Iterator[tuple[bytes, int]]:
        for cluster in self._cluster_chain(first_cluster):
            start = self._cluster_offset(cluster)
            yield from self._contiguous_slots(start, self.geometry.cluster_size)

    def _fat_value(self, cluster: int) -> int:
        offset = cluster + cluster // 2
        if offset + 2 > len(self._fat):
            raise FATError(f"cluster {cluster} has no FAT entry")
        value = struct.unpack_from("<H", self._fat, offset)[0]
        return (value >> 4) & 0xFFF if cluster & 1 else value & 0xFFF

    def _set_fat_value(self, output: bytearray, cluster: int, value: int) -> None:
        if not 0 <= value <= 0xFFF:
            raise FATError(f"FAT12 value is out of range: {value}")
        relative = cluster + cluster // 2
        for fat_start in self._fat_offsets:
            offset = fat_start + relative
            current = struct.unpack_from("<H", output, offset)[0]
            if cluster & 1:
                updated = (current & 0x000F) | (value << 4)
            else:
                updated = (current & 0xF000) | value
            struct.pack_into("<H", output, offset, updated)


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


def _path_key(path: str | PurePosixPath) -> tuple[str, ...]:
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or not parsed.parts or any(part in ("", ".", "..") for part in parsed.parts):
        raise FATError(f"unsafe filesystem path: {str(path)!r}")
    return tuple(part.casefold() for part in parsed.parts)
