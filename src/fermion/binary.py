"""Conservative exact-blob replacement for copied binary media."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class BinaryPatchError(ValueError):
    """Raised when an exact binary replacement would be ambiguous or destructive."""


@dataclass(frozen=True)
class ExactReplacement:
    offset: int
    size: int
    output: Path


def replace_exact(
    image_path: Path,
    original_path: Path,
    replacement_path: Path,
    output_path: Path,
) -> ExactReplacement:
    """Replace one unique, same-sized byte sequence in a copied image."""
    if output_path.resolve() == image_path.resolve():
        raise BinaryPatchError("output must differ from the input image")
    if output_path.exists():
        raise BinaryPatchError(f"output already exists: {output_path}")

    image = image_path.read_bytes()
    original = original_path.read_bytes()
    replacement = replacement_path.read_bytes()

    if not original:
        raise BinaryPatchError("original blob is empty")
    if len(original) != len(replacement):
        raise BinaryPatchError(
            f"replacement size differs: {len(original)} -> {len(replacement)} bytes"
        )

    first = image.find(original)
    if first < 0:
        raise BinaryPatchError("original blob does not occur in the input image")
    second = image.find(original, first + 1)
    if second >= 0:
        raise BinaryPatchError(
            f"original blob is ambiguous; matches at 0x{first:x} and 0x{second:x}"
        )

    patched = image[:first] + replacement + image[first + len(original) :]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(patched)
    return ExactReplacement(first, len(original), output_path)
