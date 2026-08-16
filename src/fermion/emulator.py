"""Minimal headless libretro frontend for automated NP2kai runtime tests."""

from __future__ import annotations

import ast
import ctypes
import hashlib
import struct
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Self


class EmulatorError(RuntimeError):
    """Raised when a libretro core cannot run a requested emulator operation."""


RETRO_DEVICE_KEYBOARD = 3
RETRO_DEVICE_MOUSE = 2

RETRO_DEVICE_ID_MOUSE_LEFT = 2
RETRO_DEVICE_ID_MOUSE_RIGHT = 3
RETRO_DEVICE_ID_MOUSE_MIDDLE = 6

RETRO_ENVIRONMENT_GET_CAN_DUPE = 3
RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY = 9
RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE = 13
RETRO_ENVIRONMENT_GET_VARIABLE = 15
RETRO_ENVIRONMENT_SET_VARIABLES = 16
RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE = 17
RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME = 18
RETRO_ENVIRONMENT_GET_LOG_INTERFACE = 27
RETRO_ENVIRONMENT_SET_SERIALIZATION_QUIRKS = 44
RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION = 52
RETRO_ENVIRONMENT_GET_MIDI_INTERFACE = 48 | 0x10000

RETRO_PIXEL_FORMAT_0RGB1555 = 0
RETRO_PIXEL_FORMAT_XRGB8888 = 1
RETRO_PIXEL_FORMAT_RGB565 = 2


FERMION_CORE_OPTIONS = {
    "np2kai_model": "PC-9801VX",
    "np2kai_clk_base": "2.4576 MHz",
    "np2kai_clk_mult": "20",
    "np2kai_cpu_feature": "Intel 80386",
    "np2kai_ExMemory": "13",
    "np2kai_keyboard": "Ja",
    "np2kai_SNDboard": "PC9801-86",
    "np2kai_usefmgen": "fmgen",
    "np2kai_inputmouse": "ON",
    "np2kai_joymode": "OFF",
    "np2kai_keyrepeat": "OFF",
    "np2kai_uselasthddmount": "OFF",
    "np2kai_xroll": "ON",
}


KEY_CODES = {
    "backspace": 8,
    "tab": 9,
    "return": 13,
    "enter": 13,
    "escape": 27,
    "space": 32,
    "delete": 127,
    "up": 273,
    "down": 274,
    "right": 275,
    "left": 276,
    "insert": 277,
    "home": 278,
    "end": 279,
    "pageup": 280,
    "pagedown": 281,
    "rshift": 303,
    "lshift": 304,
    "rctrl": 305,
    "lctrl": 306,
    "ralt": 307,
    "lalt": 308,
}
KEY_CODES.update({f"f{number}": 281 + number for number in range(1, 16)})
KEY_CODES.update({str(number): ord(str(number)) for number in range(10)})
KEY_CODES.update({chr(code): code for code in range(ord("a"), ord("z") + 1)})

MOUSE_BUTTON_CODES = {
    "left": RETRO_DEVICE_ID_MOUSE_LEFT,
    "right": RETRO_DEVICE_ID_MOUSE_RIGHT,
    "middle": RETRO_DEVICE_ID_MOUSE_MIDDLE,
}


class _RetroVariable(ctypes.Structure):
    _fields_ = [("key", ctypes.c_char_p), ("value", ctypes.c_char_p)]


class _RetroGameInfo(ctypes.Structure):
    _fields_ = [
        ("path", ctypes.c_char_p),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
        ("meta", ctypes.c_char_p),
    ]


class _RetroSystemInfo(ctypes.Structure):
    _fields_ = [
        ("library_name", ctypes.c_char_p),
        ("library_version", ctypes.c_char_p),
        ("valid_extensions", ctypes.c_char_p),
        ("need_fullpath", ctypes.c_bool),
        ("block_extract", ctypes.c_bool),
    ]


_EnvironmentCallback = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)
_VideoCallback = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t
)
_AudioCallback = ctypes.CFUNCTYPE(None, ctypes.c_int16, ctypes.c_int16)
_AudioBatchCallback = ctypes.CFUNCTYPE(
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t
)
_InputPollCallback = ctypes.CFUNCTYPE(None)
_InputStateCallback = ctypes.CFUNCTYPE(
    ctypes.c_int16, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint
)


@dataclass(frozen=True)
class KeyTap:
    frame: int
    key: int
    name: str
    hold_frames: int = 2


@dataclass(frozen=True)
class MouseTap:
    frame: int
    button: int
    name: str
    hold_frames: int = 2


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    pitch: int
    pixel_format: int
    data: bytes

    def rgb(self) -> bytes:
        """Convert the native-endian libretro framebuffer to packed RGB bytes."""
        bytes_per_pixel = 4 if self.pixel_format == RETRO_PIXEL_FORMAT_XRGB8888 else 2
        if self.pitch < self.width * bytes_per_pixel:
            raise EmulatorError("framebuffer pitch is shorter than one visible row")
        if len(self.data) < self.pitch * self.height:
            raise EmulatorError("framebuffer data is truncated")

        output = bytearray(self.width * self.height * 3)
        destination = 0
        for y in range(self.height):
            row = memoryview(self.data)[y * self.pitch : (y + 1) * self.pitch]
            for x in range(self.width):
                offset = x * bytes_per_pixel
                if self.pixel_format == RETRO_PIXEL_FORMAT_XRGB8888:
                    value = int.from_bytes(row[offset : offset + 4], "little")
                    red = (value >> 16) & 0xFF
                    green = (value >> 8) & 0xFF
                    blue = value & 0xFF
                else:
                    value = int.from_bytes(row[offset : offset + 2], "little")
                    if self.pixel_format == RETRO_PIXEL_FORMAT_RGB565:
                        red = _expand(value >> 11, 5)
                        green = _expand(value >> 5, 6)
                        blue = _expand(value, 5)
                    elif self.pixel_format == RETRO_PIXEL_FORMAT_0RGB1555:
                        red = _expand(value >> 10, 5)
                        green = _expand(value >> 5, 5)
                        blue = _expand(value, 5)
                    else:
                        raise EmulatorError(
                            f"unsupported libretro pixel format: {self.pixel_format}"
                        )
                output[destination : destination + 3] = bytes((red, green, blue))
                destination += 3
        return bytes(output)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.rgb()).hexdigest()

    def crop(self, x: int, y: int, width: int, height: int) -> Frame:
        """Return a tightly packed native-pixel crop of the visible framebuffer."""
        if x < 0 or y < 0 or width < 1 or height < 1:
            raise EmulatorError("framebuffer crop must have a non-negative origin and positive size")
        if x + width > self.width or y + height > self.height:
            raise EmulatorError(
                f"framebuffer crop {x},{y},{width},{height} exceeds "
                f"{self.width}x{self.height}"
            )
        bytes_per_pixel = 4 if self.pixel_format == RETRO_PIXEL_FORMAT_XRGB8888 else 2
        if self.pitch < self.width * bytes_per_pixel:
            raise EmulatorError("framebuffer pitch is shorter than one visible row")
        if len(self.data) < self.pitch * self.height:
            raise EmulatorError("framebuffer data is truncated")
        row_size = width * bytes_per_pixel
        start_x = x * bytes_per_pixel
        data = b"".join(
            self.data[row * self.pitch + start_x : row * self.pitch + start_x + row_size]
            for row in range(y, y + height)
        )
        return Frame(width, height, row_size, self.pixel_format, data)

    def write_png(self, path: Path) -> None:
        """Write the frame as a dependency-free RGB PNG."""
        rgb = self.rgb()
        scanlines = b"".join(
            b"\x00" + rgb[y * self.width * 3 : (y + 1) * self.width * 3] for y in range(self.height)
        )
        header = struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + _png_chunk(b"IHDR", header)
        png += _png_chunk(b"IDAT", zlib.compress(scanlines, level=9))
        png += _png_chunk(b"IEND", b"")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)


def _expand(value: int, bits: int) -> int:
    mask = (1 << bits) - 1
    return ((value & mask) * 255 + mask // 2) // mask


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(data, checksum)
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


def parse_key_tap(value: str) -> KeyTap:
    """Parse FRAME:KEY[:HOLD_FRAMES] into a scheduled key tap."""
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise EmulatorError("key tap must use FRAME:KEY[:HOLD_FRAMES]")
    try:
        frame = int(parts[0])
        hold_frames = int(parts[2]) if len(parts) == 3 else 2
    except ValueError as error:
        raise EmulatorError("key tap frame values must be integers") from error
    name = parts[1].lower()
    if frame < 0:
        raise EmulatorError("key tap frame must not be negative")
    if hold_frames < 1:
        raise EmulatorError("key tap hold duration must be at least one frame")
    if name not in KEY_CODES:
        choices = ", ".join(sorted(KEY_CODES))
        raise EmulatorError(f"unknown key {name!r}; choose one of: {choices}")
    return KeyTap(frame, KEY_CODES[name], name, hold_frames)


def parse_mouse_tap(value: str) -> MouseTap:
    """Parse FRAME:BUTTON[:HOLD_FRAMES] into a scheduled mouse click."""
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise EmulatorError("mouse tap must use FRAME:BUTTON[:HOLD_FRAMES]")
    try:
        frame = int(parts[0])
        hold_frames = int(parts[2]) if len(parts) == 3 else 2
    except ValueError as error:
        raise EmulatorError("mouse tap frame values must be integers") from error
    name = parts[1].lower()
    if frame < 0:
        raise EmulatorError("mouse tap frame must not be negative")
    if hold_frames < 1:
        raise EmulatorError("mouse tap hold duration must be at least one frame")
    if name not in MOUSE_BUTTON_CODES:
        choices = ", ".join(sorted(MOUSE_BUTTON_CODES))
        raise EmulatorError(f"unknown mouse button {name!r}; choose one of: {choices}")
    return MouseTap(frame, MOUSE_BUTTON_CODES[name], name, hold_frames)


def load_core_options(path: Path) -> dict[str, str]:
    """Read RetroArch's simple `key = "value"` per-game option format."""
    options: dict[str, str] = {}
    for number, raw_line in enumerate(path.read_text().splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise EmulatorError(f"{path}:{number}: expected key = value")
        key, encoded = (part.strip() for part in line.split("=", 1))
        try:
            value = ast.literal_eval(encoded)
        except (SyntaxError, ValueError) as error:
            raise EmulatorError(f"{path}:{number}: invalid quoted value") from error
        if not key or not isinstance(value, str):
            raise EmulatorError(f"{path}:{number}: option values must be strings")
        options[key] = value
    return options


def parse_option(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise EmulatorError("core option must use KEY=VALUE")
    key, option_value = value.split("=", 1)
    if not key or not option_value:
        raise EmulatorError("core option must have a non-empty key and value")
    return key, option_value


class LibretroFrontend:
    """A deliberately small, synchronous libretro frontend for NP2kai."""

    def __init__(
        self,
        core_path: Path,
        system_directory: Path,
        content_path: Path,
        options: dict[str, str] | None = None,
    ) -> None:
        self.core_path = core_path.resolve()
        self.system_directory = system_directory.resolve()
        self.content_path = content_path.resolve()
        for kind, path in (
            ("libretro core", self.core_path),
            ("system directory", self.system_directory),
            ("content image", self.content_path),
        ):
            if not path.exists():
                raise EmulatorError(f"{kind} does not exist: {path}")
        if not (self.system_directory / "np2kai").is_dir():
            raise EmulatorError(
                f"NP2kai firmware directory does not exist: {self.system_directory / 'np2kai'}"
            )

        self.options = dict(FERMION_CORE_OPTIONS)
        if options:
            self.options.update(options)
        self._option_bytes = {key: value.encode("utf-8") for key, value in self.options.items()}
        self._system_bytes = str(self.system_directory).encode("utf-8")
        self._content_bytes = str(self.content_path).encode("utf-8")
        self._pressed: set[int] = set()
        self._mouse_buttons: set[int] = set()
        self._capture_requested = False
        self._frame: Frame | None = None
        self.pixel_format = RETRO_PIXEL_FORMAT_0RGB1555
        self._closed = False

        try:
            self.core = ctypes.CDLL(str(self.core_path))
        except OSError as error:
            raise EmulatorError(f"cannot load libretro core {self.core_path}: {error}") from error

        self._environment_callback = _EnvironmentCallback(self._environment)
        self._video_callback = _VideoCallback(self._video)
        self._audio_callback = _AudioCallback(self._audio)
        self._audio_batch_callback = _AudioBatchCallback(self._audio_batch)
        self._input_poll_callback = _InputPollCallback(self._input_poll)
        self._input_state_callback = _InputStateCallback(self._input_state)
        self._configure_api()
        self._initialize()

    def _configure_api(self) -> None:
        core = self.core
        core.retro_set_environment.argtypes = [_EnvironmentCallback]
        core.retro_set_video_refresh.argtypes = [_VideoCallback]
        core.retro_set_audio_sample.argtypes = [_AudioCallback]
        core.retro_set_audio_sample_batch.argtypes = [_AudioBatchCallback]
        core.retro_set_input_poll.argtypes = [_InputPollCallback]
        core.retro_set_input_state.argtypes = [_InputStateCallback]
        core.retro_get_system_info.argtypes = [ctypes.POINTER(_RetroSystemInfo)]
        core.retro_load_game.argtypes = [ctypes.POINTER(_RetroGameInfo)]
        core.retro_load_game.restype = ctypes.c_bool
        core.retro_serialize_size.restype = ctypes.c_size_t
        core.retro_serialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        core.retro_serialize.restype = ctypes.c_bool
        core.retro_unserialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        core.retro_unserialize.restype = ctypes.c_bool

    def _initialize(self) -> None:
        self.core.retro_set_environment(self._environment_callback)
        self.core.retro_set_video_refresh(self._video_callback)
        self.core.retro_set_audio_sample(self._audio_callback)
        self.core.retro_set_audio_sample_batch(self._audio_batch_callback)
        self.core.retro_set_input_poll(self._input_poll_callback)
        self.core.retro_set_input_state(self._input_state_callback)
        self.core.retro_init()
        game = _RetroGameInfo(self._content_bytes, None, 0, None)
        if not self.core.retro_load_game(ctypes.byref(game)):
            self.core.retro_deinit()
            self._closed = True
            raise EmulatorError(f"libretro core rejected content image: {self.content_path}")
        # NP2kai defers machine creation until its first retro_run(). That call
        # does not execute a guest frame, but it must happen before state load.
        self.core.retro_run()

    @property
    def core_identity(self) -> str:
        info = _RetroSystemInfo()
        self.core.retro_get_system_info(ctypes.byref(info))
        name = info.library_name.decode("utf-8", errors="replace")
        version = info.library_version.decode("utf-8", errors="replace")
        return f"{name} {version}"

    def _environment(self, command: int, data: int) -> bool:
        if command == RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
            ctypes.cast(data, ctypes.POINTER(ctypes.c_char_p))[0] = self._system_bytes
            return True
        if command == RETRO_ENVIRONMENT_GET_VARIABLE:
            variable = ctypes.cast(data, ctypes.POINTER(_RetroVariable)).contents
            if not variable.key:
                return False
            value = self._option_bytes.get(variable.key.decode("utf-8"))
            if value is None:
                return False
            variable.value = value
            return True
        if command == RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
            ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))[0] = False
            return True
        if command == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            pixel_format = ctypes.cast(data, ctypes.POINTER(ctypes.c_int))[0]
            if pixel_format not in (
                RETRO_PIXEL_FORMAT_0RGB1555,
                RETRO_PIXEL_FORMAT_XRGB8888,
                RETRO_PIXEL_FORMAT_RGB565,
            ):
                return False
            self.pixel_format = pixel_format
            return True
        if command == RETRO_ENVIRONMENT_GET_CAN_DUPE:
            ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))[0] = True
            return True
        if command == RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
            return False  # Ask cores to use the simple SET_VARIABLES compatibility path.
        if command in (
            RETRO_ENVIRONMENT_SET_VARIABLES,
            RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME,
            RETRO_ENVIRONMENT_SET_DISK_CONTROL_INTERFACE,
            RETRO_ENVIRONMENT_SET_SERIALIZATION_QUIRKS,
        ):
            return True
        if command in (RETRO_ENVIRONMENT_GET_LOG_INTERFACE, RETRO_ENVIRONMENT_GET_MIDI_INTERFACE):
            return False
        return False

    def _video(self, data: int, width: int, height: int, pitch: int) -> None:
        if self._capture_requested and data:
            raw = ctypes.string_at(data, pitch * height)
            self._frame = Frame(width, height, pitch, self.pixel_format, raw)

    @staticmethod
    def _audio(_left: int, _right: int) -> None:
        return None

    @staticmethod
    def _audio_batch(_data: ctypes.POINTER(ctypes.c_int16), frames: int) -> int:
        return frames

    @staticmethod
    def _input_poll() -> None:
        return None

    def _input_state(self, _port: int, device: int, _index: int, identifier: int) -> int:
        if device == RETRO_DEVICE_KEYBOARD and identifier in self._pressed:
            return 1
        if device == RETRO_DEVICE_MOUSE and identifier in self._mouse_buttons:
            return 1
        return 0

    def run_frame(self, *, capture: bool = False) -> Frame | None:
        self._capture_requested = capture
        self._frame = None
        try:
            self.core.retro_run()
        finally:
            self._capture_requested = False
        if capture and self._frame is None:
            raise EmulatorError("libretro core did not provide a framebuffer")
        return self._frame

    def key_down(self, key: int) -> None:
        self._pressed.add(key)

    def key_up(self, key: int) -> None:
        self._pressed.discard(key)

    def mouse_down(self, button: int) -> None:
        self._mouse_buttons.add(button)

    def mouse_up(self, button: int) -> None:
        self._mouse_buttons.discard(button)

    def serialize(self) -> bytes:
        """Serialize the complete core state into an immutable byte string."""
        size = self.core.retro_serialize_size()
        if not size:
            raise EmulatorError("libretro core reported an empty save state")
        buffer = ctypes.create_string_buffer(size)
        if not self.core.retro_serialize(buffer, size):
            raise EmulatorError("libretro core failed to serialize state")
        return buffer.raw

    def save_state(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.serialize())

    def load_state(self, path: Path) -> None:
        state = path.read_bytes()
        buffer = ctypes.create_string_buffer(state)
        if not self.core.retro_unserialize(buffer, len(state)):
            raise EmulatorError(f"libretro core rejected save state: {path}")

    def close(self) -> None:
        if not self._closed:
            self.core.retro_unload_game()
            self.core.retro_deinit()
            self._closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()


def run_scheduled(
    frontend: LibretroFrontend,
    frame_count: int,
    taps: list[KeyTap],
    *,
    mouse_taps: list[MouseTap] | None = None,
    capture_final: bool,
) -> Frame | None:
    """Run an exact number of frames while applying scheduled key transitions."""
    capture_frames = {frame_count - 1} if capture_final else set()
    return run_checkpoints(
        frontend,
        frame_count,
        taps,
        capture_frames,
        mouse_taps=mouse_taps,
    ).get(frame_count - 1)


def run_checkpoints(
    frontend: LibretroFrontend,
    frame_count: int,
    taps: list[KeyTap],
    capture_frames: set[int],
    *,
    mouse_taps: list[MouseTap] | None = None,
    start_frame: int = 0,
    after_frame: Callable[[int], None] | None = None,
) -> dict[int, Frame]:
    """Run scheduled input and retain requested framebuffers by frame index."""
    if frame_count < 1:
        raise EmulatorError("frame count must be at least one")
    if not 0 <= start_frame < frame_count:
        raise EmulatorError(f"start frame {start_frame} is outside a {frame_count}-frame run")
    invalid_captures = sorted(frame for frame in capture_frames if not 0 <= frame < frame_count)
    if invalid_captures:
        raise EmulatorError(
            f"checkpoint frame {invalid_captures[0]} is outside a {frame_count}-frame run"
        )
    events: dict[int, list[tuple[str, int, bool]]] = {}
    for tap in taps:
        if tap.frame >= frame_count:
            raise EmulatorError(
                f"tap {tap.name!r} is scheduled at frame {tap.frame}, "
                f"outside a {frame_count}-frame run"
            )
        if tap.frame < start_frame < tap.frame + tap.hold_frames:
            raise EmulatorError(
                f"cannot resume at frame {start_frame} during held key {tap.name!r}"
            )
        events.setdefault(tap.frame, []).append(("key", tap.key, True))
        events.setdefault(tap.frame + tap.hold_frames, []).append(("key", tap.key, False))
    for tap in mouse_taps or []:
        if tap.frame >= frame_count:
            raise EmulatorError(
                f"mouse tap {tap.name!r} is scheduled at frame {tap.frame}, "
                f"outside a {frame_count}-frame run"
            )
        if tap.frame < start_frame < tap.frame + tap.hold_frames:
            raise EmulatorError(
                f"cannot resume at frame {start_frame} during held mouse button {tap.name!r}"
            )
        events.setdefault(tap.frame, []).append(("mouse", tap.button, True))
        events.setdefault(tap.frame + tap.hold_frames, []).append(("mouse", tap.button, False))

    captured: dict[int, Frame] = {}
    for current in range(start_frame, frame_count):
        for device, code, pressed in events.get(current, []):
            if device == "key" and pressed:
                frontend.key_down(code)
            elif device == "key":
                frontend.key_up(code)
            elif pressed:
                frontend.mouse_down(code)
            else:
                frontend.mouse_up(code)
        frame = frontend.run_frame(capture=current in capture_frames)
        if frame is not None:
            captured[current] = frame
        if after_frame is not None:
            after_frame(current)
    return captured
