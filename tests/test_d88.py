from __future__ import annotations

import struct

import pytest

from fermion.d88 import D88_HEADER_SIZE, D88Error, d88_to_raw, read_d88


def make_d88(sectors: list[tuple[int, bytes]]) -> bytes:
    track = bytearray()
    for record, data in sectors:
        size_code = {128: 0, 256: 1, 512: 2, 1024: 3}[len(data)]
        track.extend(bytes((0, 0, record, size_code)))
        track.extend(struct.pack("<H", len(sectors)))
        track.extend(bytes(8))
        track.extend(struct.pack("<H", len(data)))
        track.extend(data)

    image = bytearray(D88_HEADER_SIZE)
    image[:9] = b"TEST D88\0"
    struct.pack_into("<I", image, 0x20, D88_HEADER_SIZE)
    image.extend(track)
    struct.pack_into("<I", image, 0x1C, len(image))
    return bytes(image)


def test_flattens_sectors_in_record_order() -> None:
    image = make_d88([(2, b"B" * 128), (1, b"A" * 128)])

    assert d88_to_raw(image) == b"A" * 128 + b"B" * 128
    assert [sector.address.record for sector in read_d88(image)] == [1, 2]


def test_rejects_declared_size_mismatch() -> None:
    image = bytearray(make_d88([(1, b"A" * 128)]))
    struct.pack_into("<I", image, 0x1C, len(image) + 1)

    with pytest.raises(D88Error, match="header declares"):
        read_d88(bytes(image))
