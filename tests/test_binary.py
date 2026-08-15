from __future__ import annotations

import pytest

from fermion.binary import BinaryPatchError, replace_exact


def test_replaces_one_unique_same_sized_blob(tmp_path) -> None:
    image = tmp_path / "input.hdi"
    original = tmp_path / "original.mes"
    replacement = tmp_path / "replacement.mes"
    output = tmp_path / "output.hdi"
    image.write_bytes(b"prefix-ORIGINAL-suffix")
    original.write_bytes(b"ORIGINAL")
    replacement.write_bytes(b"REPLACED")

    result = replace_exact(image, original, replacement, output)

    assert (result.offset, result.size) == (7, 8)
    assert output.read_bytes() == b"prefix-REPLACED-suffix"
    assert image.read_bytes() == b"prefix-ORIGINAL-suffix"


@pytest.mark.parametrize(
    ("image", "original", "replacement", "message"),
    [
        (b"no match", b"needle", b"change", "does not occur"),
        (b"xx", b"x", b"y", "ambiguous"),
        (b"x", b"x", b"longer", "size differs"),
    ],
)
def test_rejects_unsafe_replacements(
    tmp_path, image: bytes, original: bytes, replacement: bytes, message: str
) -> None:
    image_path = tmp_path / "input.hdi"
    original_path = tmp_path / "original.mes"
    replacement_path = tmp_path / "replacement.mes"
    output_path = tmp_path / "output.hdi"
    image_path.write_bytes(image)
    original_path.write_bytes(original)
    replacement_path.write_bytes(replacement)

    with pytest.raises(BinaryPatchError, match=message):
        replace_exact(image_path, original_path, replacement_path, output_path)
