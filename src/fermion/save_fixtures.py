"""Portable sparse save-slot fixtures for Fermion HDI images."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from fermion.hdi import HDIImage

_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class SaveFixtureError(ValueError):
    """Raised when a save fixture is malformed or does not match its source."""


@dataclass(frozen=True)
class SaveHunk:
    offset: int
    before: bytes
    data: bytes


@dataclass(frozen=True)
class SaveFixture:
    name: str
    description: str
    scenario: str
    template_path: PurePosixPath
    template_sha256: str
    target_path: PurePosixPath
    target_sha256: str
    result_sha256: str
    hunks: tuple[SaveHunk, ...]

    def build_slot(self, template: bytes) -> bytes:
        """Apply the sparse delta to its hash-pinned template slot."""
        actual = hashlib.sha256(template).hexdigest()
        if actual != self.template_sha256:
            raise SaveFixtureError(
                f"fixture {self.name!r} expects template SHA-256 "
                f"{self.template_sha256}, got {actual}"
            )

        result = bytearray(template)
        for hunk in self.hunks:
            end = hunk.offset + len(hunk.data)
            if end > len(result):
                raise SaveFixtureError(
                    f"fixture {self.name!r} hunk at 0x{hunk.offset:x} exceeds "
                    f"the {len(result)}-byte template"
                )
            actual_before = bytes(result[hunk.offset:end])
            if actual_before != hunk.before:
                raise SaveFixtureError(
                    f"fixture {self.name!r} hunk at 0x{hunk.offset:x} expects "
                    f"{hunk.before.hex()}, got {actual_before.hex()}"
                )
            result[hunk.offset:end] = hunk.data

        built = bytes(result)
        actual = hashlib.sha256(built).hexdigest()
        if actual != self.result_sha256:
            raise SaveFixtureError(
                f"fixture {self.name!r} produced SHA-256 {actual}, "
                f"expected {self.result_sha256}"
            )
        return built

    def apply(self, image: HDIImage) -> HDIImage:
        """Install the fixture into a copied image, refusing a non-pristine target slot."""
        template = image.read_file(self.template_path)
        target = image.read_file(self.target_path)
        actual_target = hashlib.sha256(target).hexdigest()
        if actual_target != self.target_sha256:
            raise SaveFixtureError(
                f"fixture {self.name!r} expects target SHA-256 "
                f"{self.target_sha256}, got {actual_target}"
            )
        built = self.build_slot(template)
        if len(built) != len(target):
            raise SaveFixtureError(
                f"fixture {self.name!r} builds {len(built)} bytes for a "
                f"{len(target)}-byte target slot"
            )
        return image.replace_files({self.target_path: built})


@dataclass(frozen=True)
class SaveFixtureManifest:
    fixtures: tuple[SaveFixture, ...]

    @classmethod
    def from_file(cls, path: Path) -> SaveFixtureManifest:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise SaveFixtureError(f"cannot read save fixture manifest {path}: {error}") from error
        if data.get("version") != 1:
            raise SaveFixtureError("save fixture manifest version must be 1")
        raw_fixtures = data.get("fixtures")
        if not isinstance(raw_fixtures, list) or not raw_fixtures:
            raise SaveFixtureError(
                "save fixture manifest must contain at least one [[fixtures]] table"
            )
        fixtures = tuple(
            _parse_fixture(value, index) for index, value in enumerate(raw_fixtures, 1)
        )
        names = [fixture.name for fixture in fixtures]
        if len(names) != len(set(names)):
            raise SaveFixtureError("save fixture manifest contains duplicate fixture names")
        return cls(fixtures)

    def fixture(self, name: str) -> SaveFixture:
        for fixture in self.fixtures:
            if fixture.name == name:
                return fixture
        choices = ", ".join(fixture.name for fixture in self.fixtures)
        raise SaveFixtureError(f"unknown save fixture {name!r}; choose one of: {choices}")


def write_fixture_hdi(
    fixture: SaveFixture,
    image_path: Path,
    output_path: Path,
) -> HDIImage:
    """Apply one sparse fixture while preserving the source image."""
    if output_path.resolve() == image_path.resolve():
        raise SaveFixtureError("output must differ from the input image")
    if output_path.exists():
        raise SaveFixtureError(f"output already exists: {output_path}")
    result = fixture.apply(HDIImage.from_file(image_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(result.data)
    return result


def _parse_fixture(value: object, index: int) -> SaveFixture:
    context = f"fixtures[{index}]"
    if not isinstance(value, dict):
        raise SaveFixtureError(f"{context} must be a table")
    name = _string(value, "name", context)
    if not _SAFE_NAME.fullmatch(name):
        raise SaveFixtureError(
            f"{context}.name must use lowercase letters, digits, and hyphens"
        )
    description = _string(value, "description", context)
    scenario = _string(value, "scenario", context)
    try:
        scenario.encode("ascii")
    except UnicodeEncodeError as error:
        raise SaveFixtureError(f"{context}.scenario must be ASCII") from error
    template_path = _image_path(value, "template_path", context)
    target_path = _image_path(value, "target_path", context)
    if template_path == target_path:
        raise SaveFixtureError(f"{context} template_path and target_path must differ")

    raw_hunks = value.get("hunks")
    if not isinstance(raw_hunks, list) or not raw_hunks:
        raise SaveFixtureError(f"{context}.hunks must be a non-empty array of tables")
    hunks = tuple(
        _parse_hunk(item, hunk_index, context)
        for hunk_index, item in enumerate(raw_hunks, 1)
    )
    previous_end = 0
    for hunk in hunks:
        if hunk.offset < previous_end:
            raise SaveFixtureError(f"{context}.hunks must be sorted and non-overlapping")
        previous_end = hunk.offset + len(hunk.data)

    return SaveFixture(
        name=name,
        description=description,
        scenario=scenario,
        template_path=template_path,
        template_sha256=_hash(value, "template_sha256", context),
        target_path=target_path,
        target_sha256=_hash(value, "target_sha256", context),
        result_sha256=_hash(value, "result_sha256", context),
        hunks=hunks,
    )


def _parse_hunk(value: object, index: int, fixture_context: str) -> SaveHunk:
    context = f"{fixture_context}.hunks[{index}]"
    if not isinstance(value, dict):
        raise SaveFixtureError(f"{context} must be a table")
    offset = _integer(value, "offset", context)
    if offset < 0:
        raise SaveFixtureError(f"{context}.offset must not be negative")
    before = _hex_bytes(value, "before", context)
    data = _hex_bytes(value, "data", context)
    if not data:
        raise SaveFixtureError(f"{context}.data must not be empty")
    if len(before) != len(data):
        raise SaveFixtureError(f"{context}.before and data must have the same length")
    if before == data:
        raise SaveFixtureError(f"{context} does not change any bytes")
    return SaveHunk(offset, before, data)


def _string(table: dict[str, object], key: str, context: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise SaveFixtureError(f"{context}.{key} must be a non-empty string")
    return value


def _integer(table: dict[str, object], key: str, context: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SaveFixtureError(f"{context}.{key} must be an integer")
    return value


def _hash(table: dict[str, object], key: str, context: str) -> str:
    value = _string(table, key, context).lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise SaveFixtureError(f"{context}.{key} must contain 64 hexadecimal characters")
    return value


def _hex_bytes(table: dict[str, object], key: str, context: str) -> bytes:
    value = _string(table, key, context)
    if len(value) % 2 or any(char not in "0123456789abcdefABCDEF" for char in value):
        raise SaveFixtureError(f"{context}.{key} must contain an even number of hex digits")
    return bytes.fromhex(value)


def _image_path(table: dict[str, object], key: str, context: str) -> PurePosixPath:
    value = PurePosixPath(_string(table, key, context))
    if value.is_absolute() or any(part in ("", ".", "..") for part in value.parts):
        raise SaveFixtureError(f"{context}.{key} must be a safe relative HDI path")
    return value
