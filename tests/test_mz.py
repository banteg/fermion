from __future__ import annotations

import struct

import pytest

from fermion.mz import MZError, MZImage


def make_mz() -> bytes:
    image = bytearray(32)
    image[:2] = b"MZ"
    struct.pack_into("<H", image, 8, 2)  # 32-byte header
    struct.pack_into("<H", image, 20, 0x1234)
    struct.pack_into("<H", image, 22, 2)
    image.extend(b"load image")
    return bytes(image)


def test_extracts_load_image_and_linear_entry() -> None:
    image = MZImage.from_bytes(make_mz())

    assert image.load_image == b"load image"
    assert image.entry_offset == 0x1254


def test_rejects_non_mz_input() -> None:
    with pytest.raises(MZError, match="not a DOS MZ"):
        MZImage.from_bytes(b"not an executable")
