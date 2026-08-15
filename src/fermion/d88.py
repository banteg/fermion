"""Read D88 floppy images and convert them to flat sector images."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

D88_HEADER_SIZE = 0x2B0
D88_TRACK_COUNT = 164
D88_SECTOR_HEADER_SIZE = 16


class D88Error(ValueError):
    """Raised when a D88 image is malformed or unsupported."""


@dataclass(frozen=True, order=True)
class SectorAddress:
    cylinder: int
    head: int
    record: int


@dataclass(frozen=True)
class Sector:
    address: SectorAddress
    size_code: int
    data: bytes


def read_d88(data: bytes) -> list[Sector]:
    """Return sectors from a D88 image in cylinder/head/record order."""
    if len(data) < D88_HEADER_SIZE:
        raise D88Error(f"image is shorter than the {D88_HEADER_SIZE}-byte D88 header")

    declared_size = struct.unpack_from("<I", data, 0x1C)[0]
    if declared_size not in (0, len(data)):
        raise D88Error(f"header declares {declared_size} bytes, file contains {len(data)}")

    offsets = struct.unpack_from(f"<{D88_TRACK_COUNT}I", data, 0x20)
    sectors: dict[SectorAddress, Sector] = {}

    for track_index, track_offset in enumerate(offsets):
        if track_offset == 0:
            continue
        if not D88_HEADER_SIZE <= track_offset <= len(data) - D88_SECTOR_HEADER_SIZE:
            raise D88Error(f"track {track_index} has invalid offset {track_offset:#x}")

        position = track_offset
        sector_count = struct.unpack_from("<H", data, position + 4)[0]
        if sector_count == 0:
            raise D88Error(f"track {track_index} declares zero sectors")

        for sector_index in range(sector_count):
            if position + D88_SECTOR_HEADER_SIZE > len(data):
                raise D88Error(f"track {track_index} sector {sector_index} header is truncated")
            cylinder, head, record, size_code = data[position : position + 4]
            count = struct.unpack_from("<H", data, position + 4)[0]
            data_size = struct.unpack_from("<H", data, position + 14)[0]
            if count != sector_count:
                raise D88Error(
                    f"track {track_index} has inconsistent sector counts "
                    f"({sector_count} then {count})"
                )
            position += D88_SECTOR_HEADER_SIZE
            end = position + data_size
            if end > len(data):
                raise D88Error(f"track {track_index} sector {sector_index} data is truncated")
            address = SectorAddress(cylinder, head, record)
            if address in sectors:
                raise D88Error(f"duplicate sector address {address}")
            sectors[address] = Sector(address, size_code, data[position:end])
            position = end

    if not sectors:
        raise D88Error("image contains no tracks")
    return [sectors[address] for address in sorted(sectors)]


def d88_to_raw(data: bytes) -> bytes:
    """Flatten a D88 image by concatenating sectors in C/H/R order."""
    return b"".join(sector.data for sector in read_d88(data))


def convert_file(source: Path, destination: Path) -> None:
    """Convert one D88 image to a flat raw-sector image."""
    raw = d88_to_raw(source.read_bytes())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
