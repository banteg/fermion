"""End-to-end catalog, archive, and HDI translation builds."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fermion.archive import ArchiveError, InstallerArchive
from fermion.hdi import HDIError, HDIImage
from fermion.runtime_defaults import RUNTIME_DEFAULT_BANK_PATH, seed_runtime_token_defaults
from fermion.translation import (
    BuiltTranslationFile,
    TranslationCatalog,
    TranslationError,
    build_translation_files,
)

DEFAULT_ARCHIVE_DIRECTORY = PurePosixPath("FERM")


@dataclass(frozen=True)
class BuiltArchive:
    name: str
    image_path: PurePosixPath
    output_path: Path
    source_size: int
    output_size: int
    output_sha256: str


@dataclass(frozen=True)
class TranslationImageBuild:
    output_path: Path
    source_sha256: str
    output_sha256: str
    files: tuple[BuiltTranslationFile, ...]
    archives: tuple[BuiltArchive, ...]
    report_path: Path


def build_translation_image(
    catalog: TranslationCatalog,
    source_directory: Path,
    image_path: Path,
    output_path: Path,
    work_directory: Path,
    juice: Path,
    *,
    archive_directory: PurePosixPath = DEFAULT_ARCHIVE_DIRECTORY,
) -> TranslationImageBuild:
    """Build translated MES files, repack their archives, and patch a copied HDI."""
    if output_path.resolve() == image_path.resolve():
        raise TranslationError("output must differ from the input image")
    if output_path.exists():
        raise TranslationError(f"output already exists: {output_path}")
    if archive_directory.is_absolute() or any(
        part in ("", ".", "..") for part in archive_directory.parts
    ):
        raise TranslationError(f"unsafe HDI archive directory: {archive_directory}")

    files = build_translation_files(catalog, source_directory, work_directory, juice)
    by_archive: dict[str, list[BuiltTranslationFile]] = {}
    for built in files:
        by_archive.setdefault(built.catalog_file.archive, []).append(built)

    image = HDIImage.from_file(image_path)
    image_replacements: dict[PurePosixPath, bytes] = {}
    archives = []
    for archive_name, members in sorted(by_archive.items()):
        hdi_path = archive_directory / archive_name
        original_data = image.read_file(hdi_path)
        archive = InstallerArchive(original_data)
        replacements = {}
        for built in members:
            catalog_file = built.catalog_file
            entry = archive.entry(catalog_file.name)
            archived_source = archive.read(entry)
            archived_hash = hashlib.sha256(archived_source).hexdigest()
            if archived_hash != catalog_file.sha256:
                raise ArchiveError(
                    f"{catalog_file.file}: HDI archive SHA-256 mismatch: "
                    f"expected {catalog_file.sha256}, got {archived_hash}"
                )
            if archived_source != built.source_path.read_bytes():
                raise ArchiveError(
                    f"{catalog_file.file}: extracted source differs from the HDI archive"
                )
            replacements[catalog_file.name] = built.output_path.read_bytes()

        rebuilt = archive.rebuild(replacements)
        archive_output = work_directory / "archives" / archive_name
        archive_output.parent.mkdir(parents=True, exist_ok=True)
        archive_output.write_bytes(rebuilt)
        image_replacements[hdi_path] = rebuilt
        archives.append(
            BuiltArchive(
                archive_name,
                hdi_path,
                archive_output,
                len(original_data),
                len(rebuilt),
                hashlib.sha256(rebuilt).hexdigest(),
            )
        )

    if not image_replacements:
        raise TranslationError("catalog contains no translated files to build")

    default_source = image.read_file(RUNTIME_DEFAULT_BANK_PATH)
    default_seed = seed_runtime_token_defaults(catalog, default_source)
    if default_seed.data != default_source:
        image_replacements[RUNTIME_DEFAULT_BANK_PATH] = default_seed.data

    result_image = image.replace_files(image_replacements)
    for archive in archives:
        if result_image.read_file(archive.image_path) != archive.output_path.read_bytes():
            raise HDIError(f"rebuilt archive verification failed for {archive.image_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result_image.data)
    source_hash = hashlib.sha256(image.data).hexdigest()
    output_hash = hashlib.sha256(result_image.data).hexdigest()
    report_path = work_directory / "build-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "source_image": str(image_path),
                "source_sha256": source_hash,
                "output_image": str(output_path),
                "output_sha256": output_hash,
                "files": [
                    {
                        "file": built.catalog_file.file,
                        "source_size": built.source_size,
                        "output_size": built.output_size,
                        "output_sha256": built.output_sha256,
                    }
                    for built in files
                ],
                "archives": [
                    {
                        "name": archive.name,
                        "image_path": str(archive.image_path),
                        "source_size": archive.source_size,
                        "output_size": archive.output_size,
                        "output_sha256": archive.output_sha256,
                    }
                    for archive in archives
                ],
                "runtime_defaults": {
                    "image_path": str(RUNTIME_DEFAULT_BANK_PATH),
                    "source_sha256": hashlib.sha256(default_source).hexdigest(),
                    "output_sha256": hashlib.sha256(default_seed.data).hexdigest(),
                    "seeded": list(default_seed.seeded),
                    "already_english": list(default_seed.already_english),
                    "preserved_custom": list(default_seed.preserved_custom),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    return TranslationImageBuild(
        output_path,
        source_hash,
        output_hash,
        files,
        tuple(archives),
        report_path,
    )
