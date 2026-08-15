from __future__ import annotations

import struct
import zlib

import pytest

from fermion.emulator import (
    RETRO_PIXEL_FORMAT_RGB565,
    EmulatorError,
    Frame,
    load_core_options,
    parse_key_tap,
    parse_option,
    run_checkpoints,
    run_scheduled,
)


def test_parses_scheduled_key_tap() -> None:
    tap = parse_key_tap("120:return:3")

    assert (tap.frame, tap.name, tap.key, tap.hold_frames) == (120, "return", 13, 3)


@pytest.mark.parametrize("value", ["return", "-1:return", "1:nope", "1:return:0"])
def test_rejects_invalid_key_tap(value: str) -> None:
    with pytest.raises(EmulatorError):
        parse_key_tap(value)


def test_loads_retroarch_options(tmp_path) -> None:
    path = tmp_path / "game.opt"
    path.write_text('np2kai_model = "PC-9801VX"\nnp2kai_clk_mult = "20"\n')

    assert load_core_options(path) == {
        "np2kai_model": "PC-9801VX",
        "np2kai_clk_mult": "20",
    }
    assert parse_option("np2kai_ExMemory=13") == ("np2kai_ExMemory", "13")


def test_converts_rgb565_and_writes_png(tmp_path) -> None:
    # Red, green, blue, white in native little-endian RGB565.
    data = struct.pack("<4H", 0xF800, 0x07E0, 0x001F, 0xFFFF)
    frame = Frame(2, 2, 4, RETRO_PIXEL_FORMAT_RGB565, data)

    assert frame.rgb() == bytes(
        [255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255]
    )

    output = tmp_path / "frame.png"
    frame.write_png(output)
    png = output.read_bytes()
    assert png.startswith(b"\x89PNG\r\n\x1a\n")

    idat_length = struct.unpack_from(">I", png, 33)[0]
    assert png[37:41] == b"IDAT"
    scanlines = zlib.decompress(png[41 : 41 + idat_length])
    assert scanlines == b"\x00" + frame.rgb()[:6] + b"\x00" + frame.rgb()[6:]


def test_runs_scheduled_key_transitions_and_captures_final_frame() -> None:
    captured = Frame(1, 1, 2, RETRO_PIXEL_FORMAT_RGB565, b"\x00\x00")

    class FakeFrontend:
        def __init__(self) -> None:
            self.pressed: set[int] = set()
            self.seen: list[tuple[frozenset[int], bool]] = []

        def key_down(self, key: int) -> None:
            self.pressed.add(key)

        def key_up(self, key: int) -> None:
            self.pressed.discard(key)

        def run_frame(self, *, capture: bool = False) -> Frame | None:
            self.seen.append((frozenset(self.pressed), capture))
            return captured if capture else None

    frontend = FakeFrontend()
    tap = parse_key_tap("1:return:2")

    assert run_scheduled(frontend, 4, [tap], capture_final=True) is captured
    assert frontend.seen == [
        (frozenset(), False),
        (frozenset({13}), False),
        (frozenset({13}), False),
        (frozenset(), True),
    ]


def test_captures_several_frames_in_one_run() -> None:
    captured = Frame(1, 1, 2, RETRO_PIXEL_FORMAT_RGB565, b"\x00\x00")

    class FakeFrontend:
        def key_down(self, _key: int) -> None:
            return None

        def key_up(self, _key: int) -> None:
            return None

        def run_frame(self, *, capture: bool = False) -> Frame | None:
            return captured if capture else None

    assert run_checkpoints(FakeFrontend(), 5, [], {1, 3}) == {
        1: captured,
        3: captured,
    }
