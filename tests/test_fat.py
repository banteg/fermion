from __future__ import annotations

import struct

from fermion.fat import FAT12


def make_fat12() -> bytes:
    sector_size = 512
    image = bytearray(12 * sector_size)
    image[:3] = b"\xeb\x3c\x90"
    image[3:11] = b"FERMION "
    struct.pack_into("<H", image, 11, sector_size)
    image[13] = 1  # sectors per cluster
    struct.pack_into("<H", image, 14, 1)  # reserved sectors
    image[16] = 2  # FAT count
    struct.pack_into("<H", image, 17, 16)  # root entries (one sector)
    struct.pack_into("<H", image, 19, 12)  # total sectors
    image[21] = 0xF8
    struct.pack_into("<H", image, 22, 1)  # sectors per FAT

    for fat in (sector_size, 2 * sector_size):
        image[fat : fat + 5] = b"\xf8\xff\xff\xff\x0f"  # cluster 2 ends the chain

    root = 3 * sector_size
    image[root : root + 11] = b"MAIN    MES"
    image[root + 11] = 0x20
    struct.pack_into("<H", image, root + 26, 2)
    struct.pack_into("<I", image, root + 28, 5)

    data = 4 * sector_size
    image[data : data + 5] = b"hello"
    return bytes(image)


def test_lists_and_reads_root_file() -> None:
    filesystem = FAT12(make_fat12())

    [entry] = filesystem.entries()
    assert str(entry.path) == "MAIN.MES"
    assert filesystem.read_file(entry) == b"hello"


def test_extracts_file(tmp_path) -> None:
    filesystem = FAT12(make_fat12())

    assert filesystem.extract(tmp_path) == [tmp_path / "MAIN.MES"]
    assert (tmp_path / "MAIN.MES").read_bytes() == b"hello"


def test_replaces_file_with_longer_cluster_chain() -> None:
    original = make_fat12()
    filesystem = FAT12(original)
    replacement = b"translated" * 80

    rebuilt = filesystem.replace_files({"main.mes": replacement})
    result = FAT12(rebuilt)

    assert result.read_file(result.entry("MAIN.MES")) == replacement
    assert result.entry("MAIN.MES").size == len(replacement)
    assert rebuilt != original
    assert filesystem.read_file(filesystem.entry("MAIN.MES")) == b"hello"
    sector_size = filesystem.geometry.bytes_per_sector
    assert rebuilt[sector_size : 2 * sector_size] == rebuilt[
        2 * sector_size : 3 * sector_size
    ]
