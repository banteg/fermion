from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

import pytest

from fermion.save_fixtures import SaveFixtureError, SaveFixtureManifest


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_manifest(
    path: Path,
    template: bytes,
    target: bytes,
    result: bytes,
    *,
    hunks: str = '{ offset = 0x1, before = "1122", data = "aabb" }',
) -> Path:
    path.write_text(
        f'''version = 1

[[fixtures]]
name = "checkpoint"
description = "Synthetic checkpoint"
scenario = "scene.mes"
template_path = "FERM/REG_00"
template_sha256 = "{sha256(template)}"
target_path = "FERM/REG_01"
target_sha256 = "{sha256(target)}"
result_sha256 = "{sha256(result)}"
hunks = [{hunks}]
'''
    )
    return path


def test_parses_and_builds_sparse_save_fixture(tmp_path: Path) -> None:
    template = b"\x00\x11\x22\x33"
    target = b"\xff" * 4
    result = b"\x00\xaa\xbb\x33"
    manifest = SaveFixtureManifest.from_file(
        write_manifest(tmp_path / "fixtures.toml", template, target, result)
    )

    fixture = manifest.fixture("checkpoint")

    assert fixture.scenario == "scene.mes"
    assert fixture.template_path == PurePosixPath("FERM/REG_00")
    assert fixture.target_path == PurePosixPath("FERM/REG_01")
    assert fixture.build_slot(template) == result


def test_rejects_wrong_template_hash(tmp_path: Path) -> None:
    manifest = SaveFixtureManifest.from_file(
        write_manifest(
            tmp_path / "fixtures.toml",
            b"\x00\x11\x22\x33",
            b"\xff" * 4,
            b"\x00\xaa\xbb\x33",
        )
    )

    with pytest.raises(SaveFixtureError, match="template SHA-256"):
        manifest.fixture("checkpoint").build_slot(b"different")


def test_rejects_overlapping_hunks(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "fixtures.toml",
        b"\x00\x11\x22\x33",
        b"\xff" * 4,
        b"\x00\xaa\xbb\x33",
        hunks=(
            '{ offset = 0x1, before = "1122", data = "aabb" }, '
            '{ offset = 0x2, before = "22", data = "cc" }'
        ),
    )

    with pytest.raises(SaveFixtureError, match="sorted and non-overlapping"):
        SaveFixtureManifest.from_file(manifest)


def test_checked_in_first_scene_fixture_is_well_formed() -> None:
    manifest = SaveFixtureManifest.from_file(
        Path(__file__).parents[1] / "runtime" / "save-fixtures.toml"
    )

    fixture = manifest.fixture("first-scene")

    assert fixture.scenario == "f0000.mes"
    assert fixture.target_path == PurePosixPath("FERM/REG_01")
    assert len(fixture.hunks) == 35
