from __future__ import annotations

import struct

import pytest

from fermion.archive import ArchiveError, InstallerArchive


def make_archive(files: list[tuple[str, bytes]]) -> bytes:
    directory_size = 2 + len(files) * 19
    directory = bytearray(struct.pack("<H", len(files)))
    payload = bytearray()
    for name, data in files:
        encoded = name.encode("cp932")
        directory.extend(encoded + bytes(13 - len(encoded)))
        directory.extend(struct.pack("<H", len(data)))
        directory.extend(struct.pack("<I", directory_size + len(payload)))
        payload.extend(data)
    return bytes(directory + payload)


def test_lists_and_reads_files() -> None:
    archive = InstallerArchive(make_archive([("MAIN.MES", b"main"), ("TITLE.GP4", b"image")]))

    assert [(entry.name, entry.size) for entry in archive.entries] == [
        ("MAIN.MES", 4),
        ("TITLE.GP4", 5),
    ]
    assert archive.read(archive.entries[0]) == b"main"


def test_extracts_files(tmp_path) -> None:
    archive = InstallerArchive(make_archive([("MAIN.MES", b"main")]))

    assert archive.extract(tmp_path) == [tmp_path / "MAIN.MES"]
    assert (tmp_path / "MAIN.MES").read_bytes() == b"main"


def test_rejects_payload_outside_archive() -> None:
    data = bytearray(make_archive([("MAIN.MES", b"main")]))
    struct.pack_into("<I", data, 2 + 15, len(data) + 1)

    with pytest.raises(ArchiveError, match="outside the archive"):
        InstallerArchive(bytes(data))


def test_refuses_to_overwrite_changed_file(tmp_path) -> None:
    archive = InstallerArchive(make_archive([("MAIN.MES", b"original")]))
    (tmp_path / "MAIN.MES").write_bytes(b"translation")

    with pytest.raises(ArchiveError, match="refusing to overwrite"):
        archive.extract(tmp_path)
