"""Parse DOS MZ executables and expose their in-memory load image."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


class MZError(ValueError):
    """Raised when a DOS MZ executable is malformed."""


@dataclass(frozen=True)
class MZImage:
    data: bytes
    header_size: int
    initial_ip: int
    initial_cs: int

    @classmethod
    def from_bytes(cls, data: bytes) -> MZImage:
        if len(data) < 28 or data[:2] != b"MZ":
            raise MZError("input is not a DOS MZ executable")
        header_paragraphs = struct.unpack_from("<H", data, 8)[0]
        header_size = header_paragraphs * 16
        if header_size < 28 or header_size > len(data):
            raise MZError(f"invalid MZ header size: {header_size}")
        initial_ip = struct.unpack_from("<H", data, 20)[0]
        initial_cs = struct.unpack_from("<H", data, 22)[0]
        return cls(
            data=data,
            header_size=header_size,
            initial_ip=initial_ip,
            initial_cs=initial_cs,
        )

    @classmethod
    def from_file(cls, path: Path) -> MZImage:
        return cls.from_bytes(path.read_bytes())

    @property
    def load_image(self) -> bytes:
        return self.data[self.header_size :]

    @property
    def entry_offset(self) -> int:
        """Return the linear entry offset relative to the load image."""
        return self.initial_cs * 16 + self.initial_ip

    def extract(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.load_image)
