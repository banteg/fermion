"""Command-line interface for Fermion preservation and translation tools."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path, PurePosixPath
from typing import NoReturn

from fermion.archive import ArchiveError, InstallerArchive
from fermion.binary import BinaryPatchError, replace_exact
from fermion.coverage import CoverageManifest, analyze_coverage
from fermion.d88 import D88Error, convert_file
from fermion.disks import DiskVerificationError, materialize
from fermion.drift import analyze_translation_drift
from fermion.emulator import (
    FERMION_CORE_OPTIONS,
    EmulatorError,
    LibretroFrontend,
    load_core_options,
    parse_key_tap,
    parse_mouse_tap,
    parse_option,
    run_checkpoints,
    run_scheduled,
)
from fermion.fat import FAT12, FATError
from fermion.gm import GMError, GMFile
from fermion.hdi import HDIError, HDIImage, write_replaced_hdi
from fermion.mz import MZError, MZImage
from fermion.np2debug import NP2DebugStateError, verify_np2debug_state_image
from fermion.pipeline import build_translation_image
from fermion.routes import RouteManifest, route_cache_key
from fermion.save_fixtures import (
    SaveFixtureError,
    SaveFixtureManifest,
    capture_save_fixture,
    verify_state_scenario,
    write_fixture_hdi,
    write_save_fixture_manifest,
)
from fermion.script import collect_mes_files, render_script, script_groups, story_mes_files
from fermion.translation import (
    CompositeTextSegment,
    TranslationCatalog,
    TranslationError,
)


def _path(value: str) -> Path:
    return Path(value).expanduser()


def _integer(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid integer: {value!r}") from error


def _tsv_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fermion")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)

    d88 = commands.add_parser("d88", help="work with D88 floppy images")
    d88_commands = d88.add_subparsers(dest="d88_command", required=True)
    convert = d88_commands.add_parser("convert", help="convert D88 to flat raw sectors")
    convert.add_argument("source", type=_path)
    convert.add_argument("destination", type=_path)
    convert.set_defaults(handler=_convert_d88)

    disks = commands.add_parser("disks", help="work with the four preservation disks")
    disks_commands = disks.add_subparsers(dest="disks_command", required=True)
    materialize_parser = disks_commands.add_parser(
        "materialize", help="create and verify HDM images from the preservation zip"
    )
    materialize_parser.add_argument("archive", type=_path)
    materialize_parser.add_argument("--output-dir", type=_path, default=Path("working/disks"))
    materialize_parser.set_defaults(handler=_materialize)

    fat = commands.add_parser("fat", help="read FAT12 filesystems from raw disk images")
    fat_commands = fat.add_subparsers(dest="fat_command", required=True)
    list_parser = fat_commands.add_parser("ls", help="list files recursively")
    list_parser.add_argument("image", type=_path)
    list_parser.set_defaults(handler=_fat_list)
    extract = fat_commands.add_parser("extract", help="extract files recursively")
    extract.add_argument("image", type=_path)
    extract.add_argument("destination", type=_path)
    extract.set_defaults(handler=_fat_extract)

    archive = commands.add_parser("archive", help="read Silky's installer archives")
    archive_commands = archive.add_subparsers(dest="archive_command", required=True)
    archive_list = archive_commands.add_parser("ls", help="list archived files")
    archive_list.add_argument("archive", type=_path)
    archive_list.set_defaults(handler=_archive_list)
    archive_extract = archive_commands.add_parser("extract", help="extract archived files")
    archive_extract.add_argument("archive", type=_path)
    archive_extract.add_argument("destination", type=_path)
    archive_extract.set_defaults(handler=_archive_extract)

    gm = commands.add_parser("gm", help="inspect General Message MES bytecode")
    gm_commands = gm.add_subparsers(dest="gm_command", required=True)
    gm_audit = gm_commands.add_parser(
        "audit", help="walk instructions and validate embedded code targets"
    )
    gm_audit.add_argument("source", type=_path)
    gm_audit.add_argument("--verbose", action="store_true", help="list every relocation")
    gm_audit.set_defaults(handler=_gm_audit)
    gm_texts = gm_commands.add_parser(
        "texts", help="list structurally decoded text records with file offsets"
    )
    gm_texts.add_argument("source", type=_path)
    gm_texts.add_argument("--mode", type=int, choices=(1, 2))
    gm_texts.add_argument("--contains", help="only show decoded text containing this string")
    gm_texts.set_defaults(handler=_gm_texts)
    gm_speakers = gm_commands.add_parser(
        "speakers", help="attribute speaker labels encoded in rendered text streams"
    )
    gm_speakers.add_argument("source", type=_path)
    speaker_filter = gm_speakers.add_mutually_exclusive_group()
    speaker_filter.add_argument(
        "--attributed-only", action="store_true", help="omit records without encoded speakers"
    )
    speaker_filter.add_argument(
        "--unresolved-only", action="store_true", help="show only records needing context"
    )
    gm_speakers.add_argument(
        "--format", choices=("text", "tsv", "jsonl"), default="text"
    )
    gm_speakers.set_defaults(handler=_gm_speakers)
    gm_transitions = gm_commands.add_parser(
        "transitions", help="list literal scenario loads and replacements"
    )
    gm_transitions.add_argument("source", type=_path)
    gm_transitions.add_argument(
        "--format", choices=("text", "tsv", "dot"), default="text"
    )
    gm_transitions.set_defaults(handler=_gm_transitions)
    gm_inventory = gm_commands.add_parser(
        "inventory", help="group canonical translation candidates across the corpus"
    )
    gm_inventory.add_argument("source", type=_path)
    gm_inventory.add_argument(
        "--story", action="store_true", help="include only scenarios reachable from FOP.MES"
    )
    gm_inventory.add_argument(
        "--duplicates-only", action="store_true", help="show only multi-anchor groups"
    )
    gm_inventory.add_argument(
        "--unresolved-only", action="store_true", help="show only groups needing a speaker"
    )
    gm_inventory.add_argument("--format", choices=("tsv", "jsonl"), default="tsv")
    gm_inventory.set_defaults(handler=_gm_inventory)
    gm_script = gm_commands.add_parser(
        "script", help="dump the deduplicated scenario script with per-line anchors"
    )
    gm_script.add_argument("source", type=_path)
    gm_script.add_argument(
        "--story", action="store_true", help="include only scenarios reachable from FOP.MES"
    )
    gm_script.set_defaults(handler=_gm_script)

    binary = commands.add_parser("binary", help="patch copied binary media conservatively")
    binary_commands = binary.add_subparsers(dest="binary_command", required=True)
    binary_replace = binary_commands.add_parser(
        "replace-exact", help="replace one unique same-sized blob in a copied image"
    )
    binary_replace.add_argument("image", type=_path)
    binary_replace.add_argument("original", type=_path)
    binary_replace.add_argument("replacement", type=_path)
    binary_replace.add_argument("output", type=_path)
    binary_replace.set_defaults(handler=_binary_replace_exact)

    mz = commands.add_parser("mz", help="work with DOS MZ executables")
    mz_commands = mz.add_subparsers(dest="mz_command", required=True)
    load_image = mz_commands.add_parser(
        "extract-load-image", help="strip the MZ header for raw disassembler loading"
    )
    load_image.add_argument("source", type=_path)
    load_image.add_argument("destination", type=_path)
    load_image.set_defaults(handler=_mz_extract_load_image)

    hdi = commands.add_parser("hdi", help="inspect and patch Anex86 HDI filesystems")
    hdi_commands = hdi.add_subparsers(dest="hdi_command", required=True)
    hdi_list = hdi_commands.add_parser("ls", help="list FAT files in an HDI")
    hdi_list.add_argument("image", type=_path)
    hdi_list.set_defaults(handler=_hdi_list)
    hdi_replace = hdi_commands.add_parser(
        "replace-file", help="replace one FAT file and safely resize its cluster chain"
    )
    hdi_replace.add_argument("image", type=_path)
    hdi_replace.add_argument("path", help="DOS path inside the HDI, such as FERM/DISKA")
    hdi_replace.add_argument("replacement", type=_path)
    hdi_replace.add_argument("output", type=_path)
    hdi_replace.set_defaults(handler=_hdi_replace_file)

    save = commands.add_parser("save", help="work with portable runtime save fixtures")
    save_commands = save.add_subparsers(dest="save_command", required=True)
    save_list = save_commands.add_parser("list", help="list checked-in save fixtures")
    save_list.add_argument("manifest", type=_path)
    save_list.set_defaults(handler=_save_list)
    save_apply = save_commands.add_parser(
        "apply", help="install one sparse save fixture into a copied HDI"
    )
    save_apply.add_argument("manifest", type=_path)
    save_apply.add_argument("fixture")
    save_apply.add_argument("image", type=_path)
    save_apply.add_argument("output", type=_path)
    save_apply.set_defaults(handler=_save_apply)
    save_capture = save_commands.add_parser(
        "capture", help="recover a sparse fixture from a serialized NP2kai state"
    )
    save_capture.add_argument("image", type=_path)
    save_capture.add_argument("state", type=_path)
    save_capture.add_argument("output", type=_path)
    save_capture.add_argument("--name", required=True)
    save_capture.add_argument("--description", required=True)
    save_capture.add_argument("--scenario", required=True)
    save_capture.add_argument("--template-path", default="FERM/REG_00")
    save_capture.add_argument("--target-path", default="FERM/REG_01")
    save_capture.add_argument(
        "--state-offset",
        type=_integer,
        help="explicit slot offset in the state, in decimal or 0x-prefixed hexadecimal",
    )
    save_capture.set_defaults(handler=_save_capture)
    save_check_np2debug = save_commands.add_parser(
        "check-np2debug-state",
        help="detect a stale NP2debug state from its cached archive size",
    )
    save_check_np2debug.add_argument("state", type=_path)
    save_check_np2debug.add_argument("image", type=_path)
    save_check_np2debug.add_argument("--archive-path", default="FERM/DISKA")
    save_check_np2debug.set_defaults(handler=_save_check_np2debug_state)

    emulator = commands.add_parser("emulator", help="run headless NP2kai translation tests")
    emulator_commands = emulator.add_subparsers(dest="emulator_command", required=True)
    emulator_run = emulator_commands.add_parser(
        "run", help="boot an HDI for an exact frame count and optionally capture it"
    )
    emulator_run.add_argument("image", type=_path)
    emulator_run.add_argument("--frames", type=int, default=1800)
    emulator_run.add_argument(
        "--tap",
        action="append",
        default=[],
        metavar="FRAME:KEY[:HOLD]",
        help="tap a libretro keyboard key at a frame; may be repeated",
    )
    emulator_run.add_argument(
        "--click",
        action="append",
        default=[],
        metavar="FRAME:BUTTON[:HOLD]",
        help="click a libretro mouse button at a frame; may be repeated",
    )
    emulator_run.add_argument(
        "--core",
        type=_path,
        default=Path("working/emulator/np2kai_libretro.dylib"),
        help="native NP2kai libretro core",
    )
    emulator_run.add_argument(
        "--system-dir",
        type=_path,
        default=Path("working/emulator/system"),
        help="RetroArch system directory containing np2kai/",
    )
    emulator_run.add_argument("--options", type=_path, help="RetroArch per-game .opt file to load")
    emulator_run.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="override one NP2kai core option; may be repeated",
    )
    emulator_run.add_argument("--capture", type=_path, help="write the final frame as PNG")
    emulator_run.add_argument(
        "--state-in", type=_path, help="restore a libretro state before running"
    )
    emulator_run.add_argument("--state-out", type=_path, help="save a libretro state after running")
    emulator_run.set_defaults(handler=_emulator_run)
    emulator_route = emulator_commands.add_parser(
        "route", help="execute a named route and verify several framebuffer checkpoints"
    )
    emulator_route.add_argument("manifest", type=_path)
    emulator_route.add_argument("route")
    emulator_route.add_argument("image", type=_path)
    emulator_route.add_argument(
        "--core",
        type=_path,
        default=Path("working/emulator/np2kai_libretro.dylib"),
        help="native NP2kai libretro core",
    )
    emulator_route.add_argument(
        "--system-dir",
        type=_path,
        default=Path("working/emulator/system"),
        help="RetroArch system directory containing np2kai/",
    )
    emulator_route.add_argument(
        "--options", type=_path, help="RetroArch per-game .opt file to load"
    )
    emulator_route.add_argument(
        "--option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="override one NP2kai core option; may be repeated",
    )
    emulator_route.add_argument(
        "--output-dir", type=_path, default=Path("working/emulator/checkpoints")
    )
    emulator_route.add_argument(
        "--cache-dir",
        type=_path,
        default=Path("working/emulator/state-cache"),
        help="store deterministic prefix states and matching writable disk snapshots",
    )
    emulator_route.add_argument(
        "--no-cache",
        action="store_true",
        help="execute and verify the complete route without reading or writing a prefix cache",
    )
    emulator_route.set_defaults(handler=_emulator_route)

    translation = commands.add_parser(
        "translation", help="work with the checked-in translation catalog"
    )
    translation_commands = translation.add_subparsers(dest="translation_command", required=True)
    translation_check = translation_commands.add_parser(
        "check", help="validate catalog structure, encodings, and source anchors"
    )
    translation_check.add_argument("catalog", type=_path)
    translation_check.add_argument(
        "--source-dir", type=_path, help="directory containing pristine source MES files"
    )
    translation_check.add_argument("--verbose", action="store_true")
    translation_check.set_defaults(handler=_translation_check)
    translation_table = translation_commands.add_parser(
        "table", help="emit the translator table with speaker and context fields"
    )
    translation_table.add_argument("catalog", type=_path)
    translation_table.add_argument(
        "--source-dir", type=_path, help="verify pristine source anchors before emitting rows"
    )
    translation_table.add_argument("--format", choices=("tsv", "jsonl"), default="tsv")
    translation_table.set_defaults(handler=_translation_table)
    translation_drift = translation_commands.add_parser(
        "drift", help="report per-file and per-speaker English register diagnostics"
    )
    translation_drift.add_argument("catalog", type=_path)
    translation_drift.add_argument(
        "--min-records",
        type=int,
        default=10,
        help="minimum analyzable records required for output and outlier baselines",
    )
    translation_drift.add_argument(
        "--file",
        action="append",
        default=[],
        help="include one exact ARCHIVE/FILENAME path; may be repeated",
    )
    translation_drift.add_argument(
        "--speaker", action="append", default=[], help="include one exact speaker; may be repeated"
    )
    translation_drift.add_argument("--only-flagged", action="store_true")
    translation_drift.add_argument("--format", choices=("tsv", "jsonl"), default="tsv")
    translation_drift.set_defaults(handler=_translation_drift)
    translation_coverage = translation_commands.add_parser(
        "coverage", help="report translated, excluded, and pending text in a scope"
    )
    translation_coverage.add_argument("catalog", type=_path)
    translation_coverage.add_argument("manifest", type=_path)
    translation_coverage.add_argument("source_dir", type=_path)
    translation_coverage.add_argument("--scope", help="report only one coverage scope")
    translation_coverage.add_argument("--verbose", action="store_true")
    translation_coverage.add_argument(
        "--require-complete",
        action="store_true",
        help="fail if any in-scope text anchor is pending",
    )
    translation_coverage.set_defaults(handler=_translation_coverage)
    translation_build = translation_commands.add_parser(
        "build", help="build translated MES files, archives, and a bootable copied HDI"
    )
    translation_build.add_argument("catalog", type=_path)
    translation_build.add_argument("source_dir", type=_path)
    translation_build.add_argument("image", type=_path)
    translation_build.add_argument("output", type=_path)
    translation_build.add_argument("--juice", type=_path, default=Path("juice"))
    translation_build.add_argument(
        "--work-dir", type=_path, default=Path("working/translation-build")
    )
    translation_build.add_argument(
        "--archive-directory",
        default="FERM",
        help="DOS directory containing DISKA/DISKB/DISKC/DISKD",
    )
    translation_build.set_defaults(handler=_translation_build)
    return parser


def _convert_d88(args: argparse.Namespace) -> None:
    convert_file(args.source, args.destination)
    print(args.destination)


def _materialize(args: argparse.Namespace) -> None:
    for destination in materialize(args.archive, args.output_dir):
        print(destination)


def _fat_list(args: argparse.Namespace) -> None:
    filesystem = FAT12.from_file(args.image)
    for entry in filesystem.entries():
        kind = "d" if entry.is_directory else "f"
        print(f"{kind} {entry.size:>8} {entry.path}")


def _fat_extract(args: argparse.Namespace) -> None:
    filesystem = FAT12.from_file(args.image)
    for destination in filesystem.extract(args.destination):
        print(destination)


def _archive_list(args: argparse.Namespace) -> None:
    archive = InstallerArchive.from_file(args.archive)
    for entry in archive.entries:
        print(f"f {entry.size:>8} {entry.name}")


def _archive_extract(args: argparse.Namespace) -> None:
    archive = InstallerArchive.from_file(args.archive)
    for destination in archive.extract(args.destination):
        print(destination)


def _mz_extract_load_image(args: argparse.Namespace) -> None:
    image = MZImage.from_file(args.source)
    image.extract(args.destination)
    print(args.destination)
    print(f"entry-offset: 0x{image.entry_offset:x}")


def _hdi_list(args: argparse.Namespace) -> None:
    image = HDIImage.from_file(args.image)
    for partition, entry in image.entries():
        kind = "d" if entry.is_directory else "f"
        print(f"{partition.index}:{partition.name} {kind} {entry.size:>8} {entry.path}")


def _hdi_replace_file(args: argparse.Namespace) -> None:
    source = HDIImage.from_file(args.image)
    before = source.read_file(args.path)
    replacement = args.replacement.read_bytes()
    result = write_replaced_hdi(args.image, {args.path: replacement}, args.output)
    after = result.read_file(args.path)
    print(args.output)
    print(f"path: {args.path}")
    print(f"size: {len(before)} -> {len(after)}")


def _save_list(args: argparse.Namespace) -> None:
    manifest = SaveFixtureManifest.from_file(args.manifest)
    for fixture in manifest.fixtures:
        print(
            f"{fixture.name}: scenario={fixture.scenario} target={fixture.target_path} "
            f"hunks={len(fixture.hunks)}"
        )
        print(f"  {fixture.description}")


def _save_apply(args: argparse.Namespace) -> None:
    fixture = SaveFixtureManifest.from_file(args.manifest).fixture(args.fixture)
    write_fixture_hdi(fixture, args.image, args.output)
    print(args.output)
    print(f"fixture: {fixture.name}")
    print(f"scenario: {fixture.scenario}")
    print(f"slot: {fixture.target_path} sha256={fixture.result_sha256}")


def _save_capture(args: argparse.Namespace) -> None:
    capture = capture_save_fixture(
        HDIImage.from_file(args.image),
        args.state.read_bytes(),
        name=args.name,
        description=args.description,
        scenario=args.scenario,
        template_path=args.template_path,
        target_path=args.target_path,
        state_offset=args.state_offset,
    )
    write_save_fixture_manifest((capture.fixture,), args.output)
    print(args.output)
    print(f"fixture: {capture.fixture.name}")
    print(f"scenario: {capture.fixture.scenario}")
    print(f"state-offset: 0x{capture.state_offset:x}")
    print(
        f"delta: {capture.changed_bytes} bytes in {len(capture.fixture.hunks)} hunks"
    )
    print(
        f"slot: {capture.fixture.target_path} sha256={capture.fixture.result_sha256}"
    )


def _save_check_np2debug_state(args: argparse.Namespace) -> None:
    check = verify_np2debug_state_image(
        args.state.read_bytes(),
        HDIImage.from_file(args.image),
        archive_path=args.archive_path,
    )
    print(f"state: {args.state}")
    print(f"image: {args.image}")
    print(f"archive: {check.archive_path}")
    print(f"sft-offset: 0x{check.state.sft_offset:x}")
    print(f"position: 0x{check.state.position:x}")
    print(f"archive-size: 0x{check.image_size:x} (matches cached SFT size)")
    print("note: a size match does not make an opaque NP2debug state portable")


def _gm_audit(args: argparse.Namespace) -> None:
    if args.source.is_dir():
        sources = sorted(path for path in args.source.rglob("*") if path.suffix.upper() == ".MES")
    else:
        sources = [args.source]
    if not sources:
        raise GMError(f"no MES files found under {args.source}")

    failures: list[str] = []
    for source in sources:
        try:
            gm = GMFile.from_file(source)
            audit = gm.audit()
        except GMError as error:
            print(f"{source}: error: {error}")
            failures.append(str(source))
            continue

        local = sum(gm.code_start <= item.target < len(gm.data) for item in audit.relocations)
        print(
            f"{source}: instructions={len(audit.instructions)} "
            f"relocations={len(audit.relocations)} local={local} issues={len(audit.issues)}"
        )
        if args.verbose:
            for item in audit.relocations:
                scope = "local" if gm.code_start <= item.target < len(gm.data) else "external"
                print(f"  0x{item.field_offset:04x} -> 0x{item.target:04x} {scope} {item.purpose}")
        for issue in audit.issues:
            print(f"  issue: {issue}")
        if audit.issues:
            failures.append(str(source))

    if failures:
        raise GMError(f"audit failed for {len(failures)} of {len(sources)} MES files")


def _gm_texts(args: argparse.Namespace) -> None:
    if args.source.is_dir():
        sources = sorted(path for path in args.source.rglob("*") if path.suffix.upper() == ".MES")
    else:
        sources = [args.source]
    if not sources:
        raise GMError(f"no MES files found under {args.source}")

    for source in sources:
        gm = GMFile.from_file(source)
        for record in gm.text_records():
            if args.mode is not None and record.mode != args.mode:
                continue
            if args.contains is not None and (
                record.text is None or args.contains not in record.text
            ):
                continue
            if record.text is not None:
                payload = f"text={json.dumps(record.text, ensure_ascii=False)}"
            else:
                payload = f"hex={record.payload.hex()}"
            print(
                f"{source}:0x{record.offset:04x} mode={record.mode} "
                f"size={len(record.payload)} {payload}"
            )


def _gm_speakers(args: argparse.Namespace) -> None:
    if args.source.is_dir():
        sources = sorted(path for path in args.source.rglob("*") if path.suffix.upper() == ".MES")
    else:
        sources = [args.source]
    if not sources:
        raise GMError(f"no MES files found under {args.source}")

    writer = None
    if args.format == "tsv":
        writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        writer.writerow(
            ("file", "offset", "speaker", "attribution", "default_name", "mode", "japanese")
        )

    for source in sources:
        gm = GMFile.from_file(source)
        for item in gm.attributed_text_records():
            if args.attributed_only and item.speaker is None:
                continue
            if args.unresolved_only and item.speaker is not None:
                continue
            record = item.record
            speaker = item.speaker.id if item.speaker else ""
            attribution = item.speaker.source if item.speaker else "unresolved"
            default_name = item.speaker.default_name if item.speaker else ""
            text_value = record.text if record.text is not None else record.payload.hex()
            if args.format == "tsv":
                assert writer is not None
                writer.writerow(
                    (
                        source,
                        f"0x{record.offset:04x}",
                        speaker,
                        attribution,
                        default_name,
                        record.mode,
                        _tsv_text(text_value),
                    )
                )
            elif args.format == "jsonl":
                print(
                    json.dumps(
                        {
                            "file": str(source),
                            "offset": record.offset,
                            "speaker": speaker or None,
                            "attribution": attribution,
                            "default_name": default_name or None,
                            "mode": record.mode,
                            "japanese": record.text,
                            "payload_hex": None if record.text is not None else record.payload.hex(),
                        },
                        ensure_ascii=False,
                    )
                )
            else:
                label = f" default={json.dumps(default_name, ensure_ascii=False)}" if default_name else ""
                payload = (
                    f"text={json.dumps(record.text, ensure_ascii=False)}"
                    if record.text is not None
                    else f"hex={record.payload.hex()}"
                )
                print(
                    f"{source}:0x{record.offset:04x} speaker="
                    f"{json.dumps(speaker, ensure_ascii=False)} "
                    f"attribution={attribution}{label} {payload}"
                )


def _gm_transitions(args: argparse.Namespace) -> None:
    files = collect_mes_files(args.source)
    if not files:
        raise GMError(f"no MES files found under {args.source}")
    rows = [
        (path.name.upper(), transition)
        for path in files
        for transition in GMFile.from_file(path).transitions()
    ]

    if args.format == "dot":
        print("digraph gm_scenarios {")
        for source, transition in rows:
            label = f"{transition.kind} @ {transition.offset:04x}"
            print(
                f"  {json.dumps(source)} -> {json.dumps(transition.target.upper())} "
                f"[label={json.dumps(label)}];"
            )
        print("}")
        return

    if args.format == "tsv":
        writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        writer.writerow(("source", "offset", "kind", "target"))
        for source, transition in rows:
            writer.writerow(
                (
                    source,
                    f"0x{transition.offset:04x}",
                    transition.kind,
                    transition.target.upper(),
                )
            )
        return

    for source, transition in rows:
        print(
            f"{source}:0x{transition.offset:04x} {transition.kind} "
            f"-> {transition.target.upper()}"
        )


def _gm_inventory(args: argparse.Namespace) -> None:
    files = collect_mes_files(args.source)
    if not files:
        raise GMError(f"no MES files found under {args.source}")
    if args.story:
        files = story_mes_files(files)
    groups = script_groups(files)
    if args.duplicates_only:
        groups = [group for group in groups if len(group.anchors) > 1]
    if args.unresolved_only:
        groups = [group for group in groups if group.speaker is None]

    if args.format == "tsv":
        writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "id",
                "anchors",
                "speaker",
                "jp",
                "en",
                "context",
                "status",
                "occurrences",
                "mode",
                "attribution",
                "default_name",
                "flags",
            )
        )
        for group in groups:
            writer.writerow(
                (
                    group.id,
                    ";".join(
                        f"{anchor.file}:0x{anchor.offset:04x}" for anchor in group.anchors
                    ),
                    group.speaker or "",
                    _tsv_text(group.japanese),
                    "",
                    "",
                    group.status,
                    len(group.anchors),
                    group.mode,
                    group.attribution,
                    group.default_name or "",
                    ",".join(group.flags),
                )
            )
        return

    for group in groups:
        print(
            json.dumps(
                {
                    "id": group.id,
                    "anchors": [
                        {"file": anchor.file, "offset": anchor.offset}
                        for anchor in group.anchors
                    ],
                    "speaker": group.speaker,
                    "jp": group.japanese,
                    "en": "",
                    "context": "",
                    "status": group.status,
                    "occurrences": len(group.anchors),
                    "mode": group.mode,
                    "attribution": group.attribution,
                    "default_name": group.default_name,
                    "flags": list(group.flags),
                },
                ensure_ascii=False,
            )
        )


def _gm_script(args: argparse.Namespace) -> None:
    files = collect_mes_files(args.source)
    if not files:
        raise GMError(f"no MES files found under {args.source}")
    if args.story:
        files = story_mes_files(files)
    print(render_script(files))


def _binary_replace_exact(args: argparse.Namespace) -> None:
    result = replace_exact(args.image, args.original, args.replacement, args.output)
    print(result.output)
    print(f"offset: 0x{result.offset:x}")
    print(f"size: {result.size}")


def _emulator_run(args: argparse.Namespace) -> None:
    options = load_core_options(args.options) if args.options else {}
    for encoded in args.option:
        key, value = parse_option(encoded)
        options[key] = value
    taps = [parse_key_tap(encoded) for encoded in args.tap]
    clicks = [parse_mouse_tap(encoded) for encoded in args.click]

    with LibretroFrontend(args.core, args.system_dir, args.image, options) as frontend:
        print(f"core: {frontend.core_identity}")
        if args.state_in:
            frontend.load_state(args.state_in)
        frame = run_scheduled(
            frontend,
            args.frames,
            taps,
            mouse_taps=clicks,
            capture_final=args.capture is not None,
        )
        print(f"frames: {args.frames}")
        if args.capture:
            if frame is None:
                raise EmulatorError("no final framebuffer was captured")
            frame.write_png(args.capture)
            print(f"capture: {args.capture}")
            print(
                f"framebuffer: {frame.width}x{frame.height} pitch={frame.pitch} "
                f"format={frame.pixel_format} sha256={frame.sha256}"
            )
        if args.state_out:
            frontend.save_state(args.state_out)
            print(f"state: {args.state_out}")


def _emulator_route(args: argparse.Namespace) -> None:
    route = RouteManifest.from_file(args.manifest).route(args.route)
    route.verify_content(args.image)
    options = load_core_options(args.options) if args.options else {}
    for encoded in args.option:
        key, value = parse_option(encoded)
        options[key] = value

    capture_frames = {checkpoint.frame for checkpoint in route.checkpoints}
    effective_options = dict(FERMION_CORE_OPTIONS)
    effective_options.update(options)
    use_cache = route.cache_frame is not None and not args.no_cache
    cache_state: Path | None = None
    cache_disk: Path | None = None
    staged_cache_state: Path | None = None
    staged_cache_disk: Path | None = None
    start_frame = 0
    cache_hit = False
    if use_cache:
        cache_key = route_cache_key(
            route,
            args.core,
            args.system_dir,
            effective_options,
        )
        cache_root = args.cache_dir / route.name / cache_key
        cache_state = cache_root / "prefix.state"
        cache_disk = cache_root / "prefix.hdi"
        cache_hit = cache_state.is_file() and cache_disk.is_file()
        if cache_hit:
            start_frame = route.cache_frame + 1
    runtime_image = args.cache_dir / "runtime" / f"{route.name}.hdi"
    runtime_image.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cache_disk if cache_hit else args.image, runtime_image)

    checkpoint_states: dict[int, bytes] = {}
    scenario_frames = {
        checkpoint.frame for checkpoint in route.checkpoints if checkpoint.scenario is not None
    }
    with LibretroFrontend(args.core, args.system_dir, runtime_image, options) as frontend:
        print(f"core: {frontend.core_identity}")
        print(
            f"route: {route.name} frames={route.frames} "
            f"start={start_frame} executed={route.frames - start_frame}"
        )
        if use_cache:
            state = "hit" if cache_hit else "miss"
            print(f"cache: {state} frame={route.cache_frame} state={cache_state}")
        else:
            print("cache: disabled")
        if cache_hit:
            assert cache_state is not None
            frontend.load_state(cache_state)

        def save_prefix(current: int) -> None:
            nonlocal staged_cache_disk, staged_cache_state
            if current in scenario_frames:
                checkpoint_states[current] = frontend.serialize()
            if not use_cache or cache_hit or current != route.cache_frame:
                return
            assert cache_state is not None and cache_disk is not None
            cache_state.parent.mkdir(parents=True, exist_ok=True)
            temporary_state = cache_state.with_suffix(".state.tmp")
            temporary_disk = cache_disk.with_suffix(".hdi.tmp")
            frontend.save_state(temporary_state)
            shutil.copyfile(runtime_image, temporary_disk)
            staged_cache_disk = temporary_disk
            staged_cache_state = temporary_state

        frames = run_checkpoints(
            frontend,
            route.frames,
            list(route.taps),
            capture_frames,
            mouse_taps=list(route.clicks),
            start_frame=start_frame,
            after_frame=save_prefix,
        )

    failures: list[str] = []
    output_dir = args.output_dir / route.name
    for checkpoint in route.checkpoints:
        frame = frames.get(checkpoint.frame)
        if frame is None:
            if checkpoint.frame < start_frame:
                print(
                    f"checkpoint: {checkpoint.name} frame={checkpoint.frame} cached-prefix skipped"
                )
                continue
            raise EmulatorError(f"route did not capture checkpoint {checkpoint.name!r}")
        checked_frame = frame.crop(*checkpoint.crop) if checkpoint.crop else frame
        output = output_dir / f"{checkpoint.name}.png"
        checked_frame.write_png(output)
        result = "recorded"
        if checkpoint.sha256 is not None:
            result = "ok" if checked_frame.sha256 == checkpoint.sha256 else "MISMATCH"
            if result == "MISMATCH":
                failures.append(checkpoint.name)
        crop = (
            f" crop={','.join(str(value) for value in checkpoint.crop)}"
            if checkpoint.crop
            else ""
        )
        scenario = ""
        if checkpoint.scenario is not None:
            assert checkpoint.state_offset is not None
            state = checkpoint_states.get(checkpoint.frame)
            if state is None:
                raise EmulatorError(
                    f"route did not capture state for checkpoint {checkpoint.name!r}"
                )
            try:
                verify_state_scenario(state, checkpoint.scenario, checkpoint.state_offset)
            except SaveFixtureError as error:
                if checkpoint.name not in failures:
                    failures.append(checkpoint.name)
                scenario = (
                    f" scenario={checkpoint.scenario}@0x{checkpoint.state_offset:x}:"
                    f"MISMATCH({error})"
                )
            else:
                scenario = f" scenario={checkpoint.scenario}@0x{checkpoint.state_offset:x}:ok"
        print(
            f"checkpoint: {checkpoint.name} frame={checkpoint.frame} "
            f"sha256={checked_frame.sha256}{crop}{scenario} {result} {output}"
        )
    if failures:
        for temporary in (staged_cache_state, staged_cache_disk):
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        raise EmulatorError(
            f"{len(failures)} route checkpoint(s) mismatched: {', '.join(failures)}"
        )
    if staged_cache_state is not None and staged_cache_disk is not None:
        assert cache_state is not None and cache_disk is not None
        staged_cache_disk.replace(cache_disk)
        staged_cache_state.replace(cache_state)


def _translation_check(args: argparse.Namespace) -> None:
    catalog = TranslationCatalog.from_file(args.catalog)
    files_by_name = {file.file: file for file in catalog.files}
    if args.source_dir:
        catalog.verify_sources(args.source_dir)
    print(
        f"{args.catalog}: files={len(catalog.files)} entries={catalog.entry_count} "
        f"anchors={catalog.anchor_count} "
        f"sources={'verified' if args.source_dir else 'not-checked'}"
    )
    if args.verbose:
        for entry in catalog.entries:
            print(
                f"{entry.id}: anchors={len(entry.anchors)} speaker={entry.speaker} "
                f"attribution={entry.attribution} status={entry.status}"
            )
            for anchor in entry.anchors:
                print(f"  anchor: {anchor.file}:0x{anchor.offset:04x}")
            print(f"  context: {entry.context}")
            print(f"  source: {entry.source}")
            print(f"  translation: {entry.translation}")
            layouts = {
                (
                    entry.box_width
                    if entry.box_width is not None
                    else files_by_name[anchor.file].box_width,
                    entry.box_rows
                    if entry.box_rows is not None
                    else files_by_name[anchor.file].box_rows,
                    entry.wrap_mode
                    if entry.wrap_mode is not None
                    else files_by_name[anchor.file].wrap_mode,
                )
                for anchor in entry.anchors
            }
            for box_width, box_rows, wrap_mode in sorted(
                (layout for layout in layouts if layout[0] is not None),
                key=lambda layout: (layout[0], layout[1] or 0, layout[2]),
            ):
                assert box_width is not None
                for number, line in enumerate(
                    entry.wrapped_translation_for(box_width, wrap_mode), 1
                ):
                    capacity = f"/{box_rows}" if box_rows is not None else ""
                    print(
                        f"  line {number}{capacity} width={box_width} "
                        f"wrap={wrap_mode}: {line}"
                    )
            for line in entry.notes.splitlines():
                print(f"  note: {line}")
        tokens = {token.id: token for token in catalog.tokens}
        for entry in catalog.composites:
            print(
                f"{entry.id}: composite-occurrences={len(entry.occurrences)} "
                f"anchors={len(entry.anchors)} speaker={entry.speaker} "
                f"attribution={entry.attribution} status={entry.status}"
            )
            for occurrence in entry.occurrences:
                print(f"  occurrence: {occurrence.file}")
                for segment in occurrence.segments:
                    if isinstance(segment, CompositeTextSegment):
                        print(f"    text: 0x{segment.anchor.offset:04x}")
                    else:
                        print(
                            f"    token: {segment.token} "
                            f"0x{segment.start:04x}-0x{segment.end:04x}"
                        )
            print(f"  context: {entry.context}")
            print(f"  source: {entry.source}")
            print(f"  translation: {entry.translation}")
            layouts = {
                (
                    entry.box_width
                    if entry.box_width is not None
                    else files_by_name[occurrence.file].box_width,
                    entry.box_rows
                    if entry.box_rows is not None
                    else files_by_name[occurrence.file].box_rows,
                    entry.wrap_mode
                    if entry.wrap_mode is not None
                    else files_by_name[occurrence.file].wrap_mode,
                )
                for occurrence in entry.occurrences
            }
            for box_width, box_rows, wrap_mode in sorted(
                (layout for layout in layouts if layout[0] is not None),
                key=lambda layout: (layout[0], layout[1] or 0, layout[2]),
            ):
                assert box_width is not None
                wrapped = entry.compiled_translation(box_width, tokens, wrap_mode)
                for number, line in enumerate(wrapped.splitlines() or [""], 1):
                    capacity = f"/{box_rows}" if box_rows is not None else ""
                    print(
                        f"  line {number}{capacity} width={box_width} "
                        f"wrap={wrap_mode}: {line}"
                    )
            for line in entry.notes.splitlines():
                print(f"  note: {line}")


def _translation_table(args: argparse.Namespace) -> None:
    catalog = TranslationCatalog.from_file(args.catalog)
    if args.source_dir:
        catalog.verify_sources(args.source_dir)

    columns = (
        "id",
        "file",
        "offset",
        "speaker",
        "attribution",
        "jp",
        "en",
        "context",
        "status",
    )
    if args.format == "tsv":
        writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        for row in _translation_rows(catalog):
            writer.writerow(
                (
                    row[0],
                    row[1],
                    f"0x{row[2]:04x}",
                    row[3],
                    row[4],
                    _tsv_text(row[5]),
                    _tsv_text(row[6]),
                    _tsv_text(row[7]),
                    row[8],
                )
            )
        return

    for row in _translation_rows(catalog):
        print(
            json.dumps(
                {
                    "id": row[0],
                    "file": row[1],
                    "offset": row[2],
                    "speaker": row[3],
                    "attribution": row[4],
                    "jp": row[5],
                    "en": row[6],
                    "context": row[7],
                    "status": row[8],
                },
                ensure_ascii=False,
            )
        )


def _translation_drift(args: argparse.Namespace) -> None:
    catalog = TranslationCatalog.from_file(args.catalog)
    try:
        rows = analyze_translation_drift(catalog, min_records=args.min_records)
    except ValueError as error:
        raise TranslationError(str(error)) from error
    files = set(args.file)
    speakers = set(args.speaker)
    rows = tuple(
        row
        for row in rows
        if row.records >= args.min_records
        and (not files or row.file in files)
        and (not speakers or row.speaker in speakers)
        and (not args.only_flagged or row.flags)
    )
    columns = (
        "file",
        "speaker",
        "records",
        "sentences",
        "contractions_per_100",
        "stiff_forms_per_100",
        "mean_sentence_words",
        "repeated_opening_percent",
        "flags",
        "top_openings",
    )
    if args.format == "tsv":
        writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        writer.writerow(columns)
        for row in rows:
            writer.writerow(
                (
                    row.file,
                    row.speaker,
                    row.records,
                    row.sentences,
                    f"{row.contraction_rate:.1f}",
                    f"{row.stiff_form_rate:.1f}",
                    f"{row.mean_sentence_words:.1f}",
                    f"{row.repeated_opening_rate:.1f}",
                    ",".join(row.flags),
                    "; ".join(
                        f"{opening} ({count})" for opening, count in row.top_openings
                    ),
                )
            )
        return

    for row in rows:
        print(
            json.dumps(
                {
                    "file": row.file,
                    "speaker": row.speaker,
                    "records": row.records,
                    "sentences": row.sentences,
                    "contractions_per_100": round(row.contraction_rate, 1),
                    "stiff_forms_per_100": round(row.stiff_form_rate, 1),
                    "mean_sentence_words": round(row.mean_sentence_words, 1),
                    "repeated_opening_percent": round(row.repeated_opening_rate, 1),
                    "flags": row.flags,
                    "top_openings": [
                        {"opening": opening, "count": count}
                        for opening, count in row.top_openings
                    ],
                },
                ensure_ascii=False,
            )
        )


def _translation_rows(
    catalog: TranslationCatalog,
) -> list[tuple[str, str, int, str, str, str, str, str, str]]:
    rows = []
    for entry in catalog.entries:
        for anchor in entry.anchors:
            rows.append(
                (
                    entry.id,
                    anchor.file,
                    anchor.offset,
                    entry.speaker,
                    entry.attribution,
                    entry.source,
                    entry.translation,
                    entry.context,
                    entry.status,
                )
            )
    for entry in catalog.composites:
        for occurrence in entry.occurrences:
            rows.append(
                (
                    entry.id,
                    occurrence.file,
                    occurrence.start,
                    entry.speaker,
                    entry.attribution,
                    entry.source,
                    entry.translation,
                    entry.context,
                    entry.status,
                )
            )
    file_order = {file.file: index for index, file in enumerate(catalog.files)}
    rows.sort(key=lambda row: (file_order[row[1]], row[2], row[0]))
    return rows


def _translation_build(args: argparse.Namespace) -> None:
    catalog = TranslationCatalog.from_file(args.catalog)
    result = build_translation_image(
        catalog,
        args.source_dir,
        args.image,
        args.output,
        args.work_dir,
        args.juice,
        archive_directory=PurePosixPath(args.archive_directory),
    )
    for built in result.files:
        print(
            f"file: {built.catalog_file.file} {built.source_size}->{built.output_size} "
            f"sha256={built.output_sha256}"
        )
    for archive in result.archives:
        print(
            f"archive: {archive.image_path} {archive.source_size}->{archive.output_size} "
            f"sha256={archive.output_sha256}"
        )
    print(f"image: {result.output_path}")
    print(f"sha256: {result.source_sha256} -> {result.output_sha256}")
    print(f"report: {result.report_path}")


def _translation_coverage(args: argparse.Namespace) -> None:
    catalog = TranslationCatalog.from_file(args.catalog)
    manifest = CoverageManifest.from_file(args.manifest)
    reports = analyze_coverage(
        catalog,
        manifest,
        args.source_dir,
        scope_id=args.scope,
    )
    incomplete = []
    for report in reports:
        print(f"scope: {report.scope.id}")
        print(f"  description: {report.scope.description}")
        print(
            f"  anchors: total={len(report.texts)} "
            f"translated={len(report.translated_anchors)} "
            f"excluded={len(report.excluded_anchors)} "
            f"pending={report.pending_anchor_count}"
        )
        print(
            f"  canonical-lines: total={report.canonical_line_count} "
            f"managed={report.managed_line_count} "
            f"pending={len(report.pending_groups)} "
            f"duplicates={report.duplicate_line_count} "
            f"context-splits={report.contextual_split_count}"
        )
        if report.pending_groups:
            incomplete.append(report.scope.id)
        if args.verbose:
            for group in report.pending_groups:
                existing = (
                    f" canonical={','.join(group.translated_ids)}" if group.translated_ids else ""
                )
                print(
                    f"  pending: mode={group.source_mode} anchors={len(group.anchors)}"
                    f"{existing} source={json.dumps(group.source, ensure_ascii=False)}"
                )
                for anchor in group.anchors:
                    print(f"    {anchor.file}:0x{anchor.offset:04x}")
    if args.require_complete and incomplete:
        raise TranslationError("coverage incomplete for " + ", ".join(incomplete))


def _fail(message: str) -> NoReturn:
    raise SystemExit(f"fermion: error: {message}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except (
        ArchiveError,
        BinaryPatchError,
        D88Error,
        DiskVerificationError,
        EmulatorError,
        FATError,
        GMError,
        HDIError,
        MZError,
        NP2DebugStateError,
        OSError,
        SaveFixtureError,
        TranslationError,
        UnicodeError,
    ) as error:
        _fail(str(error))
