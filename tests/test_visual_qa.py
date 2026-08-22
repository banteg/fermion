from __future__ import annotations

import hashlib
import json
from argparse import Namespace

import pytest

from fermion.cli import _emulator_qa
from fermion.emulator import RETRO_PIXEL_FORMAT_RGB565, Frame
from fermion.visual_qa import (
    TranslationBuildReport,
    VisualQAError,
    VisualQAManifest,
    case_fingerprint,
    changed_build_files,
)


def write_route_manifest(tmp_path):
    path = tmp_path / "routes.toml"
    path.write_text(
        f'''version = 2

[[routes]]
name = "opening"
description = "Opening route"
content_sha256 = "{"0" * 64}"
frames = 20
taps = ["3:return"]

[[routes.checkpoints]]
name = "menu"
frame = 9
sha256 = "{"1" * 64}"

[[routes.checkpoints]]
name = "dialogue"
frame = 19
sha256 = "{"2" * 64}"
'''
    )
    return path


def write_visual_manifest(tmp_path):
    path = tmp_path / "visual-qa.toml"
    path.write_text(
        '''version = 1
route_manifest = "routes.toml"

[[cases]]
route = "opening"
files = ["DISKA/MAIN.MES"]
checkpoints = ["dialogue"]
'''
    )
    return path


def test_loads_suite_and_resolves_selected_checkpoints(tmp_path) -> None:
    write_route_manifest(tmp_path)
    suite = VisualQAManifest.from_file(write_visual_manifest(tmp_path))

    assert suite.route_manifest_path == tmp_path / "routes.toml"
    assert suite.case("opening").files == ("DISKA/MAIN.MES",)
    assert suite.case("opening").checkpoints == ("dialogue",)


def test_rejects_unknown_checkpoint(tmp_path) -> None:
    write_route_manifest(tmp_path)
    path = write_visual_manifest(tmp_path)
    path.write_text(path.read_text().replace('"dialogue"', '"missing"'))

    with pytest.raises(VisualQAError, match="unknown checkpoints"):
        VisualQAManifest.from_file(path)


def test_case_fingerprint_ignores_unrelated_built_files_and_output_image_hash(tmp_path) -> None:
    write_route_manifest(tmp_path)
    suite = VisualQAManifest.from_file(write_visual_manifest(tmp_path))
    case = suite.case("opening")
    route = suite.routes.route("opening")
    report = TranslationBuildReport(
        "6" * 64,
        tmp_path / "game.hdi",
        "5" * 64,
        {"DISKA/MAIN.MES": "3" * 64, "DISKB/OTHER.MES": "4" * 64},
        "7" * 64,
    )
    unrelated_change = TranslationBuildReport(
        report.source_sha256,
        report.output_image,
        "8" * 64,
        {"DISKA/MAIN.MES": "3" * 64, "DISKB/OTHER.MES": "9" * 64},
        report.runtime_defaults_sha256,
    )
    relevant_change = TranslationBuildReport(
        report.source_sha256,
        report.output_image,
        "a" * 64,
        {"DISKA/MAIN.MES": "b" * 64, "DISKB/OTHER.MES": "9" * 64},
        report.runtime_defaults_sha256,
    )

    original = case_fingerprint(case, route, None, report, "c" * 64)

    assert case_fingerprint(case, route, None, unrelated_change, "c" * 64) == original
    assert case_fingerprint(case, route, None, relevant_change, "c" * 64) != original


def test_build_report_verifies_the_exact_output_image(tmp_path) -> None:
    image = tmp_path / "game.hdi"
    image.write_bytes(b"game")
    report = TranslationBuildReport(
        "0" * 64,
        image,
        hashlib.sha256(b"game").hexdigest(),
        {"DISKA/MAIN.MES": "1" * 64},
        "2" * 64,
    )

    report.verify_image(image)
    image.write_bytes(b"different")
    with pytest.raises(VisualQAError, match="build report expects"):
        report.verify_image(image)


def test_lists_added_removed_and_changed_build_files() -> None:
    assert changed_build_files(
        {"same": "1", "changed": "2", "removed": "3"},
        {"same": "1", "changed": "4", "added": "5"},
    ) == ("added", "changed", "removed")


def test_incremental_qa_regenerates_only_when_case_inputs_change(
    tmp_path, monkeypatch
) -> None:
    write_route_manifest(tmp_path)
    suite_path = write_visual_manifest(tmp_path)
    image = tmp_path / "game.hdi"
    image.write_bytes(b"first image")
    report_path = tmp_path / "build-report.json"

    def write_report(main_hash: str) -> None:
        report_path.write_text(
            json.dumps(
                {
                    "source_sha256": "6" * 64,
                    "output_image": str(image),
                    "output_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
                    "files": [
                        {"file": "DISKA/MAIN.MES", "output_sha256": main_hash},
                        {"file": "DISKB/OTHER.MES", "output_sha256": "4" * 64},
                    ],
                    "runtime_defaults": {"output_sha256": "7" * 64},
                }
            )
        )

    calls = []

    def fake_route(args) -> None:
        calls.append(args.route)
        output = args.output_dir / args.route / "dialogue.png"
        pixel = b"\x00\x00" if args.image.read_bytes() == b"first image" else b"\xff\xff"
        Frame(1, 1, 2, RETRO_PIXEL_FORMAT_RGB565, pixel).write_png(output)

    monkeypatch.setattr("fermion.cli.runtime_fingerprint", lambda *_args: "c" * 64)
    monkeypatch.setattr("fermion.cli._run_visual_qa_route", fake_route)
    write_report("3" * 64)
    args = Namespace(
        manifest=suite_path,
        build_report=report_path,
        image=None,
        core=tmp_path / "core",
        system_dir=tmp_path / "system",
        options=None,
        option=[],
        output_dir=tmp_path / "visual-qa",
        cache_dir=tmp_path / "cache",
        case=[],
        force=False,
    )

    _emulator_qa(args)
    _emulator_qa(args)
    image.write_bytes(b"second image")
    write_report("8" * 64)
    _emulator_qa(args)

    assert calls == ["opening", "opening"]
    receipt = json.loads((args.output_dir / "manifest.json").read_text())
    screenshot = receipt["cases"]["opening"]["screenshots"][0]
    assert screenshot["state"] == "changed"
    assert screenshot["framebuffer_sha256"] == hashlib.sha256(b"\xff\xff\xff").hexdigest()
    assert (args.output_dir / screenshot["diff"]["before"]).read_bytes() != (
        args.output_dir / screenshot["diff"]["after"]
    ).read_bytes()
