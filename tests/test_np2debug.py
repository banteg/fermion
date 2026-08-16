from __future__ import annotations

from pathlib import PurePosixPath

import pytest

from fermion.np2debug import (
    NP2DebugStateError,
    inspect_np2debug_archive_state,
    verify_np2debug_state_image,
)


def np2debug_state(
    cached_size: int,
    *,
    position: int = 0x1234,
    sft_offset: int = 0x40,
) -> bytes:
    state = bytearray(0x180)
    state[sft_offset : sft_offset + 2] = (1).to_bytes(2, "little")
    state[sft_offset + 4] = 0x20
    state[sft_offset + 0x11 : sft_offset + 0x15] = cached_size.to_bytes(4, "little")
    state[sft_offset + 0x15 : sft_offset + 0x19] = position.to_bytes(4, "little")
    state[sft_offset + 0x20 : sft_offset + 0x2B] = b"DISKA      "

    # NP2debug also serializes a FAT directory-cache copy. Its preceding bytes
    # are not an SFT entry and must not create an ambiguous match.
    state[0x100:0x120] = b"README  TXT" + bytes(21)
    state[0x120:0x12B] = b"DISKA      "
    return bytes(state)


class Image:
    def __init__(self, archive: bytes):
        self.archive = archive

    def read_file(self, path: PurePosixPath) -> bytes:
        assert path == PurePosixPath("FERM/DISKA")
        return self.archive


def test_inspects_open_sft_entry_and_ignores_directory_cache_copy() -> None:
    archive = inspect_np2debug_archive_state(np2debug_state(0x4000))

    assert archive.name == "DISKA"
    assert archive.sft_offset == 0x40
    assert archive.cached_size == 0x4000
    assert archive.position == 0x1234


def test_verifies_np2debug_cached_archive_size() -> None:
    check = verify_np2debug_state_image(
        np2debug_state(0x4000),
        Image(bytes(0x4000)),  # type: ignore[arg-type]
    )

    assert check.archive_path == PurePosixPath("FERM/DISKA")
    assert check.image_size == 0x4000


def test_rejects_np2debug_state_from_different_archive_size() -> None:
    with pytest.raises(
        NP2DebugStateError,
        match=r"caches FERM/DISKA at 0x4007 bytes.*0x4000 bytes \(7 bytes smaller\)",
    ):
        verify_np2debug_state_image(
            np2debug_state(0x4007),
            Image(bytes(0x4000)),  # type: ignore[arg-type]
        )


def test_rejects_ambiguous_open_sft_entries() -> None:
    state = bytearray(np2debug_state(0x4000))
    second = 0xC0
    state[second : second + 2] = (1).to_bytes(2, "little")
    state[second + 4] = 0x20
    state[second + 0x11 : second + 0x15] = (0x4000).to_bytes(4, "little")
    state[second + 0x15 : second + 0x19] = (0x2000).to_bytes(4, "little")
    state[second + 0x20 : second + 0x2B] = b"DISKA      "

    with pytest.raises(NP2DebugStateError, match="ambiguous open DOS SFT entries"):
        inspect_np2debug_archive_state(bytes(state))
