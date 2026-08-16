from __future__ import annotations

import hashlib

import pytest

from fermion.emulator import EmulatorError
from fermion.routes import RouteManifest, route_cache_key


def write_manifest(tmp_path, content_hash: str):
    path = tmp_path / "routes.toml"
    path.write_text(
        f'''version = 2

[[routes]]
name = "opening"
description = "Opening route"
content_sha256 = "{content_hash}"
frames = 20
cache_frame = 9
taps = ["3:return", "10:space:1"]
clicks = ["4:right"]

[[routes.checkpoints]]
name = "menu"
frame = 9
sha256 = "{"1" * 64}"

[[routes.checkpoints]]
name = "dialogue"
frame = 19
'''
    )
    return path


def test_loads_route_and_verifies_content(tmp_path) -> None:
    content = tmp_path / "game.hdi"
    content.write_bytes(b"game")
    path = write_manifest(tmp_path, hashlib.sha256(b"game").hexdigest())

    route = RouteManifest.from_file(path).route("opening")
    route.verify_content(content)

    assert route.frames == 20
    assert route.cache_frame == 9
    assert [(tap.frame, tap.name) for tap in route.taps] == [(3, "return"), (10, "space")]
    assert [(click.frame, click.name) for click in route.clicks] == [(4, "right")]
    assert [(item.name, item.frame, item.sha256) for item in route.checkpoints] == [
        ("menu", 9, "1" * 64),
        ("dialogue", 19, None),
    ]


def test_rejects_wrong_content(tmp_path) -> None:
    content = tmp_path / "game.hdi"
    content.write_bytes(b"different")
    path = write_manifest(tmp_path, hashlib.sha256(b"game").hexdigest())

    with pytest.raises(EmulatorError, match="expects content SHA-256"):
        RouteManifest.from_file(path).route("opening").verify_content(content)


def test_rejects_checkpoint_outside_route(tmp_path) -> None:
    path = write_manifest(tmp_path, "0" * 64)
    path.write_text(path.read_text().replace("frame = 19", "frame = 20"))

    with pytest.raises(EmulatorError, match="falls outside"):
        RouteManifest.from_file(path)


def test_rejects_cache_frame_during_held_key(tmp_path) -> None:
    path = write_manifest(tmp_path, "0" * 64)
    path.write_text(path.read_text().replace("cache_frame = 9", "cache_frame = 10"))

    with pytest.raises(EmulatorError, match="crosses held key"):
        RouteManifest.from_file(path)


def test_route_cache_key_covers_core_system_and_options(tmp_path) -> None:
    path = write_manifest(tmp_path, "0" * 64)
    route = RouteManifest.from_file(path).route("opening")
    core = tmp_path / "core.dylib"
    core.write_bytes(b"core-a")
    system = tmp_path / "system" / "np2kai"
    system.mkdir(parents=True)
    (system / "FONT.ROM").write_bytes(b"font")
    (system / "np2kai.cfg").write_text("clock=20")

    original = route_cache_key(route, core, system.parent, {"clock": "20"})
    core.write_bytes(b"core-b")
    changed_core = route_cache_key(route, core, system.parent, {"clock": "20"})
    core.write_bytes(b"core-a")
    (system / "np2kai.cfg").write_text("clock=4")
    changed_system = route_cache_key(route, core, system.parent, {"clock": "20"})
    changed_options = route_cache_key(route, core, system.parent, {"clock": "4"})

    assert len({original, changed_core, changed_system, changed_options}) == 4
