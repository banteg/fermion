# Fermion translation tools

This repository contains reproducible preservation and translation tooling for
*Fermion: Mirai kara no Houmonsha* on PC-98. Original game data and generated
working images are intentionally excluded from version control.

Install the development environment and inspect the CLI:

```sh
uv sync
uv run fermion --help
```

Materialize verified raw HDM images from the preservation archive:

```sh
uv run fermion disks materialize artifacts/fermion_flux_dump.zip
```

The command writes the images to `working/disks/` and checks them against the
MAME software-list SHA-1 hashes recorded in `provenance/PROVENANCE.md`.

List or extract a disk's FAT12 filesystem:

```sh
uv run fermion fat ls working/disks/fermion-a.hdm
uv run fermion fat extract working/disks/fermion-a.hdm working/files/disk-a
```

The installed game files are stored inside `DISKA` through `DISKD`. Inspect or
extract one of these Silky's installer archives with:

```sh
uv run fermion archive ls working/files/disk-a/DISKA
uv run fermion archive extract working/files/disk-a/DISKA working/installed
```

Probe a scenario with a locally built `lime-juice` executable. The command
tries the plausible AI5 configurations, recompiles every successful
decompilation, and reports whether any result is byte-identical:

```sh
uv run fermion mes roundtrip working/installed/MAIN.MES --juice /path/to/juice
```

Walk General Message bytecode and verify that embedded local addresses land on
instruction boundaries. Pass either one MES file or a directory tree:

```sh
uv run fermion gm audit working/installed
uv run fermion gm audit working/installed/MAIN.MES --verbose
```

List decoded text instruction offsets. Mode 1 expands dictionary tokens and
Shift-JIS; mode 2 exposes the single-byte ASCII strings used by the game. Results
can be filtered without decompiling whole scripts:

```sh
uv run fermion gm texts working/installed --mode 2
uv run fermion gm texts working/installed --contains '見ない方'
```

For a same-sized renderer probe, replace one unique compiled MES blob in a
copied hard-disk image without touching the input image:

```sh
uv run fermion binary replace-exact \
  working/base.hdi original.MES patched.MES working/test.hdi
```

## Headless runtime tests

The packaged CLI can drive NP2kai directly through libretro. It does not launch
RetroArch, Wine, or a GUI: scheduled keyboard input goes into the emulator and
the final framebuffer is written directly to PNG.

The installed RetroArch core is x86-64, so build a native arm64 core from the
current upstream source. All source, firmware copies, cores, states, and captures
remain under ignored `working/` paths:

```sh
gh repo clone AZO234/NP2kai working/vendor/NP2kai
git -C working/vendor/NP2kai checkout c023417
make -C working/vendor/NP2kai/sdl -f Makefile.libretro \
  platform=osx 'ARCHFLAGS=-arch arm64' 'CXX_VER=-std=c++14' \
  NP2KAI_VERSION=0.86 NP2KAI_HASH=c023417 -j4
cp working/vendor/NP2kai/sdl/np2kai_libretro.dylib working/emulator/
mkdir -p working/emulator/system
cp -R "$HOME/Documents/RetroArch/system/np2kai" working/emulator/system/
```

Run an exact number of frames, inject one or more key taps, and capture the final
640x400 framebuffer. A tap uses `FRAME:KEY[:HOLD_FRAMES]`:

```sh
uv run fermion emulator run working/emulator/fermion-exchange.hdi \
  --frames 4500 \
  --tap 1000:return \
  --tap 1300:return \
  --tap 1750:return \
  --tap 2200:return \
  --tap 2900:return \
  --tap 4100:return \
  --capture working/emulator/headless-exchange.png
```

This route boots through the information screen, color-mode selector,
disclaimer, title, and translated menu, selects `START NEW GAME`, then advances
to the long translated reply. The command reports a SHA-256 over packed RGB
pixels for stable checkpoint comparisons.

Save states can turn the expensive boot route into a short checkpoint test:

```sh
uv run fermion emulator run working/emulator/fermion-exchange.hdi \
  --frames 1200 --state-out working/emulator/information.state
uv run fermion emulator run working/emulator/fermion-exchange.hdi \
  --state-in working/emulator/information.state \
  --frames 200 --tap 1:return \
  --capture working/emulator/mode-selector.png
```

The built-in core options match the Fermion configuration. Use `--options` to
load a RetroArch `.opt` file or repeat `--option KEY=VALUE` for overrides.
