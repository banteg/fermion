"""Command-line interface for Fermion preservation and translation tools."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path, PurePosixPath
from typing import NoReturn

from fermion.archive import ArchiveError, InstallerArchive
from fermion.binary import BinaryPatchError, replace_exact
from fermion.coverage import CoverageManifest, analyze_coverage
from fermion.d88 import D88Error, convert_file
from fermion.disks import DiskVerificationError, materialize
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
from fermion.mes import MESProbeError, probe_roundtrip
from fermion.mz import MZError, MZImage
from fermion.pipeline import build_translation_image
from fermion.routes import RouteManifest, route_cache_key
from fermion.save_fixtures import (
    SaveFixtureError,
    SaveFixtureManifest,
    write_fixture_hdi,
)
from fermion.translation import TranslationCatalog, TranslationError


def _path(value: str) -> Path:
    return Path(value).expanduser()


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

    mes = commands.add_parser("mes", help="probe MES decompiler/compiler compatibility")
    mes_commands = mes.add_subparsers(dest="mes_command", required=True)
    roundtrip = mes_commands.add_parser(
        "roundtrip", help="try plausible lime-juice configurations and compare outputs"
    )
    roundtrip.add_argument("source", type=_path)
    roundtrip.add_argument("--juice", type=_path, default=Path("juice"))
    roundtrip.add_argument("--output-dir", type=_path, default=Path("working/roundtrip"))
    roundtrip.set_defaults(handler=_mes_roundtrip)

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


def _mes_roundtrip(args: argparse.Namespace) -> None:
    results = probe_roundtrip(args.source, args.juice, args.output_dir)
    print(f"{'variant':<16} {'decompile':>9} {'compile':>7} {'sizes':>15} {'exact':>5}")
    for result in results:
        compile_code = "-" if result.compile_returncode is None else str(result.compile_returncode)
        output_size = "-" if result.output_size is None else str(result.output_size)
        sizes = f"{result.input_size}->{output_size}"
        print(
            f"{result.variant:<16} {result.decompile_returncode:>9} "
            f"{compile_code:>7} {sizes:>15} {('yes' if result.exact else 'no'):>5}"
        )
    if not any(result.exact for result in results):
        raise MESProbeError("no configuration produced an exact no-op round-trip")


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
            if not use_cache or cache_hit or current != route.cache_frame:
                return
            assert cache_state is not None and cache_disk is not None
            cache_state.parent.mkdir(parents=True, exist_ok=True)
            temporary_state = cache_state.with_suffix(".state.tmp")
            temporary_disk = cache_disk.with_suffix(".hdi.tmp")
            frontend.save_state(temporary_state)
            shutil.copyfile(runtime_image, temporary_disk)
            temporary_disk.replace(cache_disk)
            temporary_state.replace(cache_state)

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
        output = output_dir / f"{checkpoint.name}.png"
        frame.write_png(output)
        result = "recorded"
        if checkpoint.sha256 is not None:
            result = "ok" if frame.sha256 == checkpoint.sha256 else "MISMATCH"
            if result == "MISMATCH":
                failures.append(checkpoint.name)
        print(
            f"checkpoint: {checkpoint.name} frame={checkpoint.frame} "
            f"sha256={frame.sha256} {result} {output}"
        )
    if failures:
        raise EmulatorError(
            f"{len(failures)} route checkpoint(s) mismatched: {', '.join(failures)}"
        )


def _translation_check(args: argparse.Namespace) -> None:
    catalog = TranslationCatalog.from_file(args.catalog)
    if args.source_dir:
        catalog.verify_sources(args.source_dir)
    print(
        f"{args.catalog}: files={len(catalog.files)} entries={len(catalog.entries)} "
        f"anchors={catalog.anchor_count} "
        f"sources={'verified' if args.source_dir else 'not-checked'}"
    )
    if args.verbose:
        for entry in catalog.entries:
            print(f"{entry.id}: anchors={len(entry.anchors)} {entry.status}")
            for anchor in entry.anchors:
                print(f"  anchor: {anchor.file}:0x{anchor.offset:04x}")
            print(f"  source: {entry.source}")
            print(f"  translation: {entry.translation}")
            if entry.box_width is not None:
                for number, line in enumerate(entry.wrapped_translation, 1):
                    print(f"  line {number}/{entry.box_width}: {line}")
            for line in entry.notes.splitlines():
                print(f"  note: {line}")


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
        MESProbeError,
        MZError,
        OSError,
        SaveFixtureError,
        TranslationError,
        UnicodeError,
    ) as error:
        _fail(str(error))
