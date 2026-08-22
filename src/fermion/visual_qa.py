"""Incremental screenshot-suite manifests for emulator visual QA."""

from __future__ import annotations

import hashlib
import json
import re
import struct
import tomllib
import zlib
from dataclasses import dataclass
from pathlib import Path

from fermion.emulator import EmulatorError
from fermion.routes import EmulatorRoute, RouteManifest
from fermion.save_fixtures import SaveFixture, SaveFixtureError, SaveFixtureManifest

_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


class VisualQAError(ValueError):
    """Raised when a visual-QA suite or build receipt is invalid."""


@dataclass(frozen=True)
class VisualQACase:
    route: str
    files: tuple[str, ...]
    fixture: str | None = None
    checkpoints: tuple[str, ...] = ()


@dataclass(frozen=True)
class VisualQAManifest:
    route_manifest_path: Path
    fixture_manifest_path: Path | None
    cases: tuple[VisualQACase, ...]
    routes: RouteManifest
    fixtures: SaveFixtureManifest | None

    @classmethod
    def from_file(cls, path: Path) -> VisualQAManifest:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise VisualQAError(f"cannot read visual-QA manifest {path}: {error}") from error
        if data.get("version") != 1:
            raise VisualQAError("visual-QA manifest version must be 1")

        route_manifest_path = _relative_path(data, "route_manifest", path)
        routes = RouteManifest.from_file(route_manifest_path)

        raw_fixture_path = data.get("fixture_manifest")
        fixture_manifest_path = None
        fixtures = None
        if raw_fixture_path is not None:
            fixture_manifest_path = _relative_path(data, "fixture_manifest", path)
            fixtures = SaveFixtureManifest.from_file(fixture_manifest_path)

        raw_cases = data.get("cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise VisualQAError("visual-QA manifest must contain at least one [[cases]] table")
        cases = tuple(
            _parse_case(value, index, routes, fixtures)
            for index, value in enumerate(raw_cases, 1)
        )
        route_names = [case.route for case in cases]
        if len(route_names) != len(set(route_names)):
            raise VisualQAError("visual-QA manifest contains duplicate route cases")
        return cls(route_manifest_path, fixture_manifest_path, cases, routes, fixtures)

    def case(self, route: str) -> VisualQACase:
        for case in self.cases:
            if case.route == route:
                return case
        choices = ", ".join(case.route for case in self.cases)
        raise VisualQAError(f"unknown visual-QA case {route!r}; choose one of: {choices}")


@dataclass(frozen=True)
class TranslationBuildReport:
    source_sha256: str
    output_image: Path
    output_sha256: str
    file_sha256: dict[str, str]
    runtime_defaults_sha256: str

    @classmethod
    def from_file(cls, path: Path) -> TranslationBuildReport:
        try:
            data = json.loads(path.read_text())
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise VisualQAError(f"cannot read translation build report {path}: {error}") from error
        if not isinstance(data, dict):
            raise VisualQAError("translation build report must contain a JSON object")

        source_sha256 = _json_hash(data, "source_sha256", "translation build report")
        output_sha256 = _json_hash(data, "output_sha256", "translation build report")
        raw_output = data.get("output_image")
        if not isinstance(raw_output, str) or not raw_output:
            raise VisualQAError("translation build report output_image must be a path string")

        raw_files = data.get("files")
        if not isinstance(raw_files, list) or not raw_files:
            raise VisualQAError("translation build report must contain a non-empty files array")
        file_sha256: dict[str, str] = {}
        for index, value in enumerate(raw_files, 1):
            context = f"translation build report files[{index}]"
            if not isinstance(value, dict):
                raise VisualQAError(f"{context} must be an object")
            name = value.get("file")
            if not isinstance(name, str) or not name:
                raise VisualQAError(f"{context}.file must be a non-empty string")
            if name in file_sha256:
                raise VisualQAError(f"translation build report contains duplicate file {name!r}")
            file_sha256[name] = _json_hash(value, "output_sha256", context)

        raw_defaults = data.get("runtime_defaults")
        if not isinstance(raw_defaults, dict):
            raise VisualQAError("translation build report must contain runtime_defaults")
        runtime_defaults_sha256 = _json_hash(
            raw_defaults, "output_sha256", "translation build report runtime_defaults"
        )
        return cls(
            source_sha256,
            Path(raw_output).expanduser(),
            output_sha256,
            file_sha256,
            runtime_defaults_sha256,
        )

    def verify_image(self, path: Path) -> None:
        try:
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as error:
            raise VisualQAError(f"cannot read translated image {path}: {error}") from error
        if actual != self.output_sha256:
            raise VisualQAError(
                f"build report expects output image SHA-256 {self.output_sha256}, got {actual}"
            )

    def dependencies(self, case: VisualQACase) -> dict[str, str]:
        missing = [name for name in case.files if name not in self.file_sha256]
        if missing:
            raise VisualQAError(
                f"visual-QA case {case.route!r} references files absent from the build report: "
                + ", ".join(missing)
            )
        return {name: self.file_sha256[name] for name in case.files}


def case_fingerprint(
    case: VisualQACase,
    route: EmulatorRoute,
    fixture: SaveFixture | None,
    report: TranslationBuildReport,
    runtime_sha256: str,
) -> str:
    """Hash the runtime inputs that can affect one route's selected screenshots."""
    if not _HASH.fullmatch(runtime_sha256):
        raise VisualQAError("runtime fingerprint must contain 64 lowercase hex characters")
    selected = set(case.checkpoints)
    checkpoints = [
        {
            "name": checkpoint.name,
            "frame": checkpoint.frame,
            "crop": checkpoint.crop,
            "scenario": checkpoint.scenario,
            "state_offset": checkpoint.state_offset,
        }
        for checkpoint in route.checkpoints
        if not selected or checkpoint.name in selected
    ]
    identity = {
        "version": 1,
        "route": {
            "name": route.name,
            "frames": route.frames,
            "taps": [[tap.frame, tap.key, tap.hold_frames] for tap in route.taps],
            "clicks": [
                [click.frame, click.button, click.hold_frames] for click in route.clicks
            ],
            "checkpoints": checkpoints,
        },
        "fixture": _fixture_identity(fixture),
        "source_image_sha256": report.source_sha256,
        "runtime_defaults_sha256": report.runtime_defaults_sha256,
        "files": report.dependencies(case),
        "runtime_sha256": runtime_sha256,
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def changed_build_files(
    previous: dict[str, str] | None, current: dict[str, str]
) -> tuple[str, ...]:
    if previous is None:
        return tuple(sorted(current))
    return tuple(
        sorted(
            name
            for name in previous.keys() | current.keys()
            if previous.get(name) != current.get(name)
        )
    )


def png_rgb_sha256(path: Path) -> str:
    """Hash packed RGB pixels from PNGs emitted by :meth:`Frame.write_png`."""
    try:
        data = path.read_bytes()
    except OSError as error:
        raise VisualQAError(f"cannot read visual-QA screenshot {path}: {error}") from error
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise VisualQAError(f"visual-QA screenshot is not a PNG: {path}")

    offset = 8
    width = height = None
    compressed = bytearray()
    while offset < len(data):
        if offset + 12 > len(data):
            raise VisualQAError(f"visual-QA screenshot has a truncated PNG chunk: {path}")
        length = struct.unpack_from(">I", data, offset)[0]
        kind = data[offset + 4 : offset + 8]
        start = offset + 8
        end = start + length
        if end + 4 > len(data):
            raise VisualQAError(f"visual-QA screenshot has a truncated PNG payload: {path}")
        payload = data[start:end]
        expected_crc = struct.unpack_from(">I", data, end)[0]
        if zlib.crc32(payload, zlib.crc32(kind)) != expected_crc:
            raise VisualQAError(f"visual-QA screenshot has a bad PNG checksum: {path}")
        if kind == b"IHDR":
            if length != 13:
                raise VisualQAError(f"visual-QA screenshot has an invalid PNG header: {path}")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise VisualQAError(f"visual-QA screenshot uses an unsupported PNG format: {path}")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
        offset = end + 4

    if width is None or height is None or not compressed:
        raise VisualQAError(f"visual-QA screenshot is missing PNG image data: {path}")
    try:
        scanlines = zlib.decompress(compressed)
    except zlib.error as error:
        raise VisualQAError(f"visual-QA screenshot has invalid compressed data: {path}") from error
    row_size = width * 3
    expected_size = height * (row_size + 1)
    if len(scanlines) != expected_size:
        raise VisualQAError(f"visual-QA screenshot has an unexpected pixel-data size: {path}")
    rows = []
    for row in range(height):
        start = row * (row_size + 1)
        if scanlines[start] != 0:
            raise VisualQAError(f"visual-QA screenshot uses an unsupported PNG filter: {path}")
        rows.append(scanlines[start + 1 : start + 1 + row_size])
    return hashlib.sha256(b"".join(rows)).hexdigest()


def _relative_path(table: dict[str, object], key: str, manifest_path: Path) -> Path:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise VisualQAError(f"visual-QA manifest {key} must be a non-empty path string")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = manifest_path.parent / candidate
    return candidate


def _parse_case(
    value: object,
    index: int,
    routes: RouteManifest,
    fixtures: SaveFixtureManifest | None,
) -> VisualQACase:
    context = f"cases[{index}]"
    if not isinstance(value, dict):
        raise VisualQAError(f"{context} must be a table")
    route_name = value.get("route")
    if not isinstance(route_name, str) or not _SAFE_NAME.fullmatch(route_name):
        raise VisualQAError(
            f"{context}.route must use lowercase letters, digits, and hyphens"
        )
    try:
        route = routes.route(route_name)
    except EmulatorError as error:
        raise VisualQAError(str(error)) from error

    raw_files = value.get("files")
    if (
        not isinstance(raw_files, list)
        or not raw_files
        or not all(isinstance(item, str) and item for item in raw_files)
    ):
        raise VisualQAError(f"{context}.files must be a non-empty array of strings")
    if len(raw_files) != len(set(raw_files)):
        raise VisualQAError(f"{context}.files contains duplicates")

    fixture = value.get("fixture")
    if fixture is not None:
        if not isinstance(fixture, str) or not _SAFE_NAME.fullmatch(fixture):
            raise VisualQAError(
                f"{context}.fixture must use lowercase letters, digits, and hyphens"
            )
        if fixtures is None:
            raise VisualQAError(f"{context}.fixture requires a top-level fixture_manifest")
        try:
            fixtures.fixture(fixture)
        except SaveFixtureError as error:
            raise VisualQAError(str(error)) from error

    raw_checkpoints = value.get("checkpoints", [])
    if not isinstance(raw_checkpoints, list) or not all(
        isinstance(item, str) and _SAFE_NAME.fullmatch(item) for item in raw_checkpoints
    ):
        raise VisualQAError(f"{context}.checkpoints must be an array of safe names")
    if len(raw_checkpoints) != len(set(raw_checkpoints)):
        raise VisualQAError(f"{context}.checkpoints contains duplicates")
    available = {checkpoint.name for checkpoint in route.checkpoints}
    unknown = [name for name in raw_checkpoints if name not in available]
    if unknown:
        raise VisualQAError(
            f"{context}.checkpoints names unknown checkpoints: {', '.join(unknown)}"
        )
    return VisualQACase(route_name, tuple(raw_files), fixture, tuple(raw_checkpoints))


def _fixture_identity(fixture: SaveFixture | None) -> object:
    if fixture is None:
        return None
    return {
        "name": fixture.name,
        "scenario": fixture.scenario,
        "template_path": str(fixture.template_path),
        "template_sha256": fixture.template_sha256,
        "target_path": str(fixture.target_path),
        "target_sha256": fixture.target_sha256,
        "result_sha256": fixture.result_sha256,
        "hunks": [
            [hunk.offset, hunk.before.hex(), hunk.data.hex()] for hunk in fixture.hunks
        ],
    }


def _json_hash(table: dict[str, object], key: str, context: str) -> str:
    value = table.get(key)
    if not isinstance(value, str):
        raise VisualQAError(f"{context}.{key} must be a SHA-256 string")
    value = value.lower()
    if not _HASH.fullmatch(value):
        raise VisualQAError(f"{context}.{key} must contain 64 hexadecimal characters")
    return value
