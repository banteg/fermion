"""Command-line interface for Fermion preservation and translation tools."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import NoReturn

from fermion.archive import ArchiveError, InstallerArchive
from fermion.d88 import D88Error, convert_file
from fermion.disks import DiskVerificationError, materialize
from fermion.fat import FAT12, FATError
from fermion.gm import GMError, GMFile
from fermion.mes import MESProbeError, probe_roundtrip
from fermion.mz import MZError, MZImage


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
    materialize_parser.add_argument(
        "--output-dir", type=_path, default=Path("working/disks")
    )
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

    mz = commands.add_parser("mz", help="work with DOS MZ executables")
    mz_commands = mz.add_subparsers(dest="mz_command", required=True)
    load_image = mz_commands.add_parser(
        "extract-load-image", help="strip the MZ header for raw disassembler loading"
    )
    load_image.add_argument("source", type=_path)
    load_image.add_argument("destination", type=_path)
    load_image.set_defaults(handler=_mz_extract_load_image)
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
                print(
                    f"  0x{item.field_offset:04x} -> 0x{item.target:04x} "
                    f"{scope} {item.purpose}"
                )
        for issue in audit.issues:
            print(f"  issue: {issue}")
        if audit.issues:
            failures.append(str(source))

    if failures:
        raise GMError(f"audit failed for {len(failures)} of {len(sources)} MES files")


def _fail(message: str) -> NoReturn:
    raise SystemExit(f"fermion: error: {message}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.handler(args)
    except (
        ArchiveError,
        D88Error,
        DiskVerificationError,
        FATError,
        GMError,
        MESProbeError,
        MZError,
        OSError,
        UnicodeError,
    ) as error:
        _fail(str(error))
