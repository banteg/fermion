"""Conservative compatibility checks for opaque NP2debug save states."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from pathlib import PurePosixPath

from fermion.hdi import HDIImage

_DOS_COMPONENT = re.compile(r"^[A-Za-z0-9_$~!#%&'()@^`{}-]+$")
_SFT_NAME_OFFSET = 0x20
_SFT_ATTRIBUTE_OFFSET = 0x04
_SFT_SIZE_OFFSET = 0x11
_SFT_POSITION_OFFSET = 0x15


class NP2DebugStateError(ValueError):
    """Raised when an NP2debug state cannot safely be paired with an image."""


@dataclass(frozen=True)
class NP2DebugArchiveState:
    """The DOS system-file-table metadata serialized by NP2debug."""

    name: str
    sft_offset: int
    cached_size: int
    position: int


@dataclass(frozen=True)
class NP2DebugStateCheck:
    """A successful archive-size comparison between a state and mounted image."""

    archive_path: PurePosixPath
    state: NP2DebugArchiveState
    image_size: int


def inspect_np2debug_archive_state(
    state: bytes,
    archive_name: str = "DISKA",
) -> NP2DebugArchiveState:
    """Locate one open DOS archive in an opaque NP2debug save state."""
    encoded_name = _dos_name_field(archive_name)
    candidates: list[NP2DebugArchiveState] = []
    search_from = 0
    while True:
        name_offset = state.find(encoded_name, search_from)
        if name_offset < 0:
            break
        search_from = name_offset + 1
        sft_offset = name_offset - _SFT_NAME_OFFSET
        if sft_offset < 0:
            continue

        reference_count = struct.unpack_from("<H", state, sft_offset)[0]
        attributes = state[sft_offset + _SFT_ATTRIBUTE_OFFSET]
        cached_size = struct.unpack_from("<I", state, sft_offset + _SFT_SIZE_OFFSET)[0]
        position = struct.unpack_from("<I", state, sft_offset + _SFT_POSITION_OFFSET)[0]
        if reference_count == 0:
            continue
        if attributes & 0xD8:
            # Exclude volume labels, directories, and bytes outside the DOS
            # attribute field. This rejects the directory-cache copy of DISKA.
            continue
        if cached_size == 0 or position > cached_size:
            continue
        candidates.append(
            NP2DebugArchiveState(
                name=archive_name.upper(),
                sft_offset=sft_offset,
                cached_size=cached_size,
                position=position,
            )
        )

    if not candidates:
        raise NP2DebugStateError(
            f"NP2debug state contains no open DOS SFT entry for {archive_name!r}"
        )
    if len(candidates) > 1:
        offsets = ", ".join(f"0x{candidate.sft_offset:x}" for candidate in candidates)
        raise NP2DebugStateError(
            f"NP2debug state contains ambiguous open DOS SFT entries for "
            f"{archive_name!r} at {offsets}"
        )
    return candidates[0]


def verify_np2debug_state_image(
    state: bytes,
    image: HDIImage,
    archive_path: str | PurePosixPath = "FERM/DISKA",
) -> NP2DebugStateCheck:
    """Reject a state whose cached archive length differs from the mounted image."""
    path = _validated_image_path(archive_path)
    archive_state = inspect_np2debug_archive_state(state, path.name)
    image_size = len(image.read_file(path))
    if archive_state.cached_size != image_size:
        difference = abs(archive_state.cached_size - image_size)
        relation = "smaller" if image_size < archive_state.cached_size else "larger"
        raise NP2DebugStateError(
            f"NP2debug state caches {path} at 0x{archive_state.cached_size:x} bytes, "
            f"but the image contains 0x{image_size:x} bytes ({difference} bytes {relation}); "
            "boot the current image fresh and create a new NP2debug state"
        )
    return NP2DebugStateCheck(path, archive_state, image_size)


def _dos_name_field(name: str) -> bytes:
    parts = name.split(".")
    if len(parts) > 2:
        raise NP2DebugStateError(f"archive name is not DOS 8.3: {name!r}")
    base = parts[0]
    extension = parts[1] if len(parts) == 2 else ""
    if (
        not 1 <= len(base) <= 8
        or len(extension) > 3
        or (len(parts) == 2 and not extension)
        or not _DOS_COMPONENT.fullmatch(base)
        or (extension and not _DOS_COMPONENT.fullmatch(extension))
    ):
        raise NP2DebugStateError(f"archive name is not DOS 8.3: {name!r}")
    return f"{base.upper():<8}{extension.upper():<3}".encode("ascii")


def _validated_image_path(path: str | PurePosixPath) -> PurePosixPath:
    parsed = PurePosixPath(path)
    if (
        parsed.is_absolute()
        or not parsed.parts
        or any(part in ("", ".", "..") for part in parsed.parts)
    ):
        raise NP2DebugStateError(f"archive path must be a safe relative HDI path: {path!r}")
    _dos_name_field(parsed.name)
    return parsed
