from __future__ import annotations

import struct

from fermion.hdi import HDIImage


def set_root_entry(
    image: bytearray,
    offset: int,
    name: bytes,
    attributes: int,
    cluster: int,
    size: int,
) -> None:
    image[offset : offset + 11] = name
    image[offset + 11] = attributes
    struct.pack_into("<H", image, offset + 26, cluster)
    struct.pack_into("<I", image, offset + 28, size)


def make_volume() -> bytes:
    sector_size = 512
    image = bytearray(16 * sector_size)
    image[:3] = b"\xeb\x3c\x90"
    image[3:11] = b"FERMION "
    struct.pack_into("<H", image, 11, sector_size)
    image[13] = 1
    struct.pack_into("<H", image, 14, 1)
    image[16] = 2
    struct.pack_into("<H", image, 17, 16)
    struct.pack_into("<H", image, 19, 16)
    image[21] = 0xF8
    struct.pack_into("<H", image, 22, 1)
    for fat in (sector_size, 2 * sector_size):
        image[fat : fat + 6] = b"\xf8\xff\xff\xff\xff\xff"

    root = 3 * sector_size
    set_root_entry(image, root, b"FERM       ", 0x10, 2, 0)
    directory = 4 * sector_size
    set_root_entry(image, directory, b"DISKA      ", 0x20, 3, 4)
    image[5 * sector_size : 5 * sector_size + 4] = b"data"
    return bytes(image)


def make_hdi() -> bytes:
    header_size = 4096
    physical_sector = 256
    sectors = 8
    heads = 2
    cylinders = 8
    disk_size = physical_sector * sectors * heads * cylinders
    image = bytearray(header_size + disk_size)
    struct.pack_into(
        "<6I",
        image,
        8,
        header_size,
        disk_size,
        physical_sector,
        sectors,
        heads,
        cylinders,
    )
    partition = header_size + physical_sector
    image[partition] = 0xA1
    image[partition + 1] = 0x81
    struct.pack_into("<H", image, partition + 10, 1)
    image[partition + 16 : partition + 21] = b"Test\0"
    volume_start = header_size + physical_sector * sectors * heads
    volume = make_volume()
    image[volume_start : volume_start + len(volume)] = volume
    return bytes(image)


def test_reads_and_grows_nested_file_in_hdi() -> None:
    original = make_hdi()
    image = HDIImage(original)
    replacement = b"translated" * 80

    result = image.replace_files({"ferm/diska": replacement})

    assert image.read_file("FERM/DISKA") == b"data"
    assert result.read_file("FERM/DISKA") == replacement
    assert len(result.data) == len(original)
