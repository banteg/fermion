from __future__ import annotations

import hashlib

import pytest

from fermion.emulator import EmulatorError
from fermion.routes import RouteManifest


def write_manifest(tmp_path, content_hash: str):
    path = tmp_path / "routes.toml"
    path.write_text(
        f'''version = 1

[[routes]]
name = "opening"
description = "Opening route"
content_sha256 = "{content_hash}"
frames = 20
taps = ["3:return", "10:space:1"]

[[routes.checkpoints]]
name = "menu"
frame = 9
sha256 = "{'1' * 64}"

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
    assert [(tap.frame, tap.name) for tap in route.taps] == [(3, "return"), (10, "space")]
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
