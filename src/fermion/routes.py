"""Named emulator routes and framebuffer checkpoints."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from fermion.emulator import (
    EmulatorError,
    KeyTap,
    MouseTap,
    parse_key_tap,
    parse_mouse_tap,
)

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
    clicks: tuple[MouseTap, ...]
    checkpoints: tuple[RouteCheckpoint, ...]
    cache_frame: int | None

    def verify_content(self, path: Path) -> None:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != self.content_sha256:
            raise EmulatorError(
                f"route {self.name!r} expects content SHA-256 {self.content_sha256}, got {actual}"
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
        if data.get("version") != 2:
            raise EmulatorError("route manifest version must be 2")
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

    raw_clicks = value.get("clicks", [])
    if not isinstance(raw_clicks, list) or not all(isinstance(item, str) for item in raw_clicks):
        raise EmulatorError(f"{context}.clicks must be an array of strings")
    clicks = tuple(parse_mouse_tap(item) for item in raw_clicks)
    for click in clicks:
        if click.frame >= frames:
            raise EmulatorError(f"{context}: mouse click {click.name!r} falls outside the route")

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

    cache_frame = value.get("cache_frame")
    if cache_frame is not None:
        cache_frame = _integer(value, "cache_frame", context)
        if not 0 <= cache_frame < frames - 1:
            raise EmulatorError(f"{context}.cache_frame must leave at least one suffix frame")
        if not any(checkpoint.frame > cache_frame for checkpoint in checkpoints):
            raise EmulatorError(f"{context}.cache_frame must precede a checkpoint")
        for tap in taps:
            if tap.frame <= cache_frame < tap.frame + tap.hold_frames:
                raise EmulatorError(f"{context}.cache_frame crosses held key {tap.name!r}")
        for click in clicks:
            if click.frame <= cache_frame < click.frame + click.hold_frames:
                raise EmulatorError(
                    f"{context}.cache_frame crosses held mouse button {click.name!r}"
                )
    return EmulatorRoute(
        name,
        description,
        content_sha256,
        frames,
        taps,
        clicks,
        checkpoints,
        cache_frame,
    )


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


def route_cache_key(
    route: EmulatorRoute,
    core: Path,
    system_directory: Path,
    options: dict[str, str],
) -> str:
    """Hash every deterministic input needed to resume a route prefix safely."""
    if route.cache_frame is None:
        raise EmulatorError(f"route {route.name!r} does not define a cache frame")
    taps = [
        [tap.frame, tap.key, tap.hold_frames]
        for tap in route.taps
        if tap.frame <= route.cache_frame
    ]
    clicks = [
        [click.frame, click.button, click.hold_frames]
        for click in route.clicks
        if click.frame <= route.cache_frame
    ]
    identity = {
        "content_sha256": route.content_sha256,
        "cache_frame": route.cache_frame,
        "taps": taps,
        "clicks": clicks,
        "options": options,
        "core_sha256": hashlib.sha256(core.read_bytes()).hexdigest(),
        "system_sha256": _system_fingerprint(system_directory),
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _system_fingerprint(system_directory: Path) -> str:
    root = system_directory / "np2kai"
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "little"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "little"))
        digest.update(data)
    return digest.hexdigest()
