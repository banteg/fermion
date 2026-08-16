from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

import pytest

from fermion.save_fixtures import (
    SCENARIO_OFFSET,
    SaveFixtureError,
    SaveFixtureManifest,
    capture_save_fixture,
    extract_global_segment,
    render_save_fixture_manifest,
    sparse_hunks,
    verify_state_scenario,
)


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


def test_checked_in_save_fixtures_are_well_formed() -> None:
    manifest = SaveFixtureManifest.from_file(
        Path(__file__).parents[1] / "runtime" / "save-fixtures.toml"
    )

    assert [fixture.name for fixture in manifest.fixtures] == [
        "first-scene",
        "opening-dialogue",
        "second-scene",
    ]
    fixture = manifest.fixture("first-scene")

    assert fixture.scenario == "f0000.mes"
    assert fixture.target_path == PurePosixPath("FERM/REG_01")
    assert len(fixture.hunks) == 35
    assert len(manifest.fixture("opening-dialogue").hunks) == 40
    assert len(manifest.fixture("second-scene").hunks) == 40


def slot(scenario: bytes = b"main.mes") -> bytes:
    result = bytearray(0x1B20)
    result[SCENARIO_OFFSET : SCENARIO_OFFSET + len(scenario) + 1] = scenario + b"\0"
    return bytes(result)


def test_extracts_changed_live_segment_and_ignores_static_template_copy() -> None:
    template = slot()
    live = bytearray(template)
    live[0x10:0x13] = b"abc"
    static_offset = 0x100
    live_offset = static_offset + len(template) + 0x80
    state = b"x" * static_offset + template + b"x" * 0x80 + bytes(live) + b"tail"

    offset, snapshot = extract_global_segment(state, template, "main.mes")

    assert offset == live_offset
    assert snapshot == bytes(live)


def test_sparse_hunks_group_only_contiguous_changes() -> None:
    hunks = sparse_hunks(b"abcdefgh", b"aBCdeFGh")

    assert [(hunk.offset, hunk.before, hunk.data) for hunk in hunks] == [
        (1, b"bc", b"BC"),
        (5, b"fg", b"FG"),
    ]


def test_capture_render_and_parse_round_trip(tmp_path: Path) -> None:
    template = slot(b"fop.mes")
    target = b"\xff" * len(template)
    live = bytearray(template)
    live[0x20:0x22] = b"ok"
    state_offset = 0x200
    state = b"x" * state_offset + bytes(live)

    class Image:
        def read_file(self, path: PurePosixPath) -> bytes:
            return {
                PurePosixPath("FERM/REG_00"): template,
                PurePosixPath("FERM/REG_01"): target,
            }[path]

    capture = capture_save_fixture(
        Image(),  # type: ignore[arg-type]
        state,
        name="opening-dialogue",
        description="Opening dialogue checkpoint",
        scenario="fop.mes",
    )
    manifest_text = render_save_fixture_manifest((capture.fixture,))
    manifest_path = tmp_path / "captured.toml"
    manifest_path.write_text(manifest_text)
    reparsed = SaveFixtureManifest.from_file(manifest_path).fixture("opening-dialogue")

    assert capture.state_offset == state_offset
    assert capture.changed_bytes == 2
    assert reparsed == capture.fixture
    assert 'name = "opening-dialogue"' in manifest_text
    assert 'offset = 0x0020, before = "0000", data = "6f6b"' in manifest_text


def test_rejects_explicit_offset_with_wrong_scenario() -> None:
    template = slot()
    state = b"x" * 0x100 + slot(b"fop.mes")

    with pytest.raises(SaveFixtureError, match="does not contain scenario"):
        extract_global_segment(state, template, "main.mes", state_offset=0x100)


def test_verifies_scenario_at_known_live_state_offset() -> None:
    state_offset = 0x100
    state = b"x" * state_offset + slot(b"f0001.mes")

    verify_state_scenario(state, "f0001.mes", state_offset)

    with pytest.raises(SaveFixtureError, match="expected 'fop.mes'"):
        verify_state_scenario(state, "fop.mes", state_offset)
