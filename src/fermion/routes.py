"""Named emulator routes and framebuffer checkpoints."""

from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from fermion.emulator import EmulatorError, KeyTap, parse_key_tap

_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class RouteCheckpoint:
    name: str
    frame: int
    sha256: str | None


@dataclass(frozen=True)
class EmulatorRoute:
    name: str
    description: str
    content_sha256: str
    frames: int
    taps: tuple[KeyTap, ...]
    checkpoints: tuple[RouteCheckpoint, ...]

    def verify_content(self, path: Path) -> None:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != self.content_sha256:
            raise EmulatorError(
                f"route {self.name!r} expects content SHA-256 {self.content_sha256}, "
                f"got {actual}"
            )


@dataclass(frozen=True)
class RouteManifest:
    routes: tuple[EmulatorRoute, ...]

    @classmethod
    def from_file(cls, path: Path) -> RouteManifest:
        try:
            data = tomllib.loads(path.read_text())
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
            raise EmulatorError(f"cannot read route manifest {path}: {error}") from error
        if data.get("version") != 1:
            raise EmulatorError("route manifest version must be 1")
        raw_routes = data.get("routes")
        if not isinstance(raw_routes, list) or not raw_routes:
            raise EmulatorError("route manifest must contain at least one [[routes]] table")
        routes = tuple(_parse_route(item, index) for index, item in enumerate(raw_routes, 1))
        names = [route.name for route in routes]
        if len(names) != len(set(names)):
            raise EmulatorError("route manifest contains duplicate route names")
        return cls(routes)

    def route(self, name: str) -> EmulatorRoute:
        for route in self.routes:
            if route.name == name:
                return route
        choices = ", ".join(route.name for route in self.routes)
        raise EmulatorError(f"unknown route {name!r}; choose one of: {choices}")


def _parse_route(value: object, index: int) -> EmulatorRoute:
    context = f"routes[{index}]"
    if not isinstance(value, dict):
        raise EmulatorError(f"{context} must be a table")
    name = _string(value, "name", context)
    if not _SAFE_NAME.fullmatch(name):
        raise EmulatorError(f"{context}.name must use lowercase letters, digits, and hyphens")
    description = _string(value, "description", context)
    content_sha256 = _hash(value, "content_sha256", context)
    frames = _integer(value, "frames", context)
    if frames < 1:
        raise EmulatorError(f"{context}.frames must be positive")

    raw_taps = value.get("taps", [])
    if not isinstance(raw_taps, list) or not all(isinstance(item, str) for item in raw_taps):
        raise EmulatorError(f"{context}.taps must be an array of strings")
    taps = tuple(parse_key_tap(item) for item in raw_taps)
    for tap in taps:
        if tap.frame >= frames:
            raise EmulatorError(f"{context}: tap {tap.name!r} falls outside the route")

    raw_checkpoints = value.get("checkpoints")
    if not isinstance(raw_checkpoints, list) or not raw_checkpoints:
        raise EmulatorError(f"{context} must contain at least one [[routes.checkpoints]] table")
    checkpoints = tuple(
        _parse_checkpoint(item, checkpoint_index, frames, context)
        for checkpoint_index, item in enumerate(raw_checkpoints, 1)
    )
    checkpoint_names = [checkpoint.name for checkpoint in checkpoints]
    if len(checkpoint_names) != len(set(checkpoint_names)):
        raise EmulatorError(f"{context} contains duplicate checkpoint names")
    checkpoint_frames = [checkpoint.frame for checkpoint in checkpoints]
    if len(checkpoint_frames) != len(set(checkpoint_frames)):
        raise EmulatorError(f"{context} contains duplicate checkpoint frames")
    return EmulatorRoute(name, description, content_sha256, frames, taps, checkpoints)


def _parse_checkpoint(
    value: object, index: int, frames: int, route_context: str
) -> RouteCheckpoint:
    context = f"{route_context}.checkpoints[{index}]"
    if not isinstance(value, dict):
        raise EmulatorError(f"{context} must be a table")
    name = _string(value, "name", context)
    if not _SAFE_NAME.fullmatch(name):
        raise EmulatorError(f"{context}.name must use lowercase letters, digits, and hyphens")
    frame = _integer(value, "frame", context)
    if not 0 <= frame < frames:
        raise EmulatorError(f"{context}.frame falls outside the route")
    expected = value.get("sha256")
    if expected is not None:
        expected = _hash(value, "sha256", context)
    return RouteCheckpoint(name, frame, expected)


def _string(table: dict[str, object], key: str, context: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise EmulatorError(f"{context}.{key} must be a non-empty string")
    return value


def _integer(table: dict[str, object], key: str, context: str) -> int:
    value = table.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise EmulatorError(f"{context}.{key} must be an integer")
    return value


def _hash(table: dict[str, object], key: str, context: str) -> str:
    value = _string(table, key, context).lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise EmulatorError(f"{context}.{key} must contain 64 hexadecimal characters")
    return value
