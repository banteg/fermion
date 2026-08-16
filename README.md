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

Recover speaker identities that are encoded in the GM render stream, or list
the records that still require scene context:

```sh
uv run fermion gm speakers working/archives --attributed-only
uv run fermion gm speakers working/archives/disk-a/FOP.MES \
  --unresolved-only \
  --format tsv
```

The command recognizes literal `【name】` labels and the exact `0x45`/`0x4b`
sequence used for the five customizable name slots. It deliberately does not
infer speakers from Japanese quote styles. A compact, speaker-annotated,
content-deduplicated mode-1 corpus dump is also available for offline review:

```sh
uv run fermion gm script working/archives > working/script.md
uv run fermion gm script working/archives --story > working/story-script.md
```

See [`research/gm-speaker-attribution.md`](research/gm-speaker-attribution.md)
for the recovered bytecode rule, slot roles, native-handler evidence, and
corpus accounting.

The story view follows literal GM scenario transitions from `FOP.MES`, stops
when the game returns to `MAIN.MES`, and then emits the reachable files in
stable scenario-name order. The default dump retains its original physical
extraction order so existing `script.md` line-number references do not move.
Inspect the actual branches and nested loads as text, TSV, or Graphviz DOT:

```sh
uv run fermion gm transitions working/archives
uv run fermion gm transitions working/archives \
  --format dot \
  > working/scenario-graph.dot
```

Generate a non-authoritative, whole-story work queue without changing the
catalog under active translation:

```sh
uv run fermion gm inventory working/archives \
  --story \
  > working/story-inventory.tsv
```

The inventory groups exact `(mode, proven speaker, Japanese)` candidates under
stable hash IDs, retains every unique-file anchor, and leaves `en` and `context`
blank. `multi-anchor`, `speaker-variant`, and `unresolved-speaker` flags identify
groups that need contextual review before they can become canonical catalog
entries. Use `--duplicates-only`, `--unresolved-only`, or `--format jsonl` for
focused passes. See
[`research/gm-scenario-flow.md`](research/gm-scenario-flow.md) for the recovered
story boundary and corpus totals.

For a same-sized renderer probe, replace one unique compiled MES blob in a
copied hard-disk image without touching the input image:

```sh
uv run fermion binary replace-exact \
  working/base.hdi original.MES patched.MES working/test.hdi
```

## Translation catalog

The checked-in [`translations/fermion.toml`](translations/fermion.toml) file is
the source of truth for translated text. Each entry keeps a stable ID, one or
more logical archive/file anchors, original Japanese, one canonical English
translation, speaker, scene context, encoding modes, status, wrapping width,
and free-form translator notes.
Generated MES files, disk images, and screenshots remain under ignored
`working/` paths.

Dialogue width is normally declared once on the containing `[[files]]` table.
The builder inserts deterministic word-boundary newlines at compile time while
leaving the canonical English prose unwrapped in TOML; an entry-level
`box_width` remains available for a real scene-specific exception.

Validate the catalog on its own, or verify every original line against a
hash-checked pristine extraction:

```sh
uv run fermion translation check translations/fermion.toml
uv run fermion translation check translations/fermion.toml \
  --source-dir working/archives \
  --verbose
```

Export the catalog in the original translator-table shape. One physical anchor
is emitted per row while canonical duplicates retain one shared catalog entry:

```sh
uv run fermion translation table translations/fermion.toml \
  --source-dir working/archives \
  > working/translation-table.tsv
```

The columns are `id`, `file`, `offset`, `speaker`, `jp`, `en`, `context`, and
`status`. Embedded newlines are escaped so the TSV remains one row per anchor;
`--format jsonl` is available for programmatic use.

The verbose view includes a word-wrapped preview for dialogue entries. See
[`translations/README.md`](translations/README.md) for the entry conventions
and incremental translation workflow.

Audit a checked-in story scope independently from the catalog. The report
groups identical pending Japanese under one canonical line while retaining all
physical offsets:

```sh
uv run fermion translation coverage \
  translations/fermion.toml \
  translations/coverage.toml \
  working/archives \
  --verbose
```

Two focused story scopes are now closed. `opening-prologue` accounts for all
118 `FOP.MES` records as 97 translated anchors and 21 explicit title/layout
exclusions. `project-d-launch-and-first-arrival` accounts for all 462
`F0001.MES`/`F0002.MES` records as 454 canonical translations, including eight
context-safe duplicate collapses, with no exclusions or pending records. A
deliberately untranslated line must be source-anchored in the coverage file
with a reason; `--require-complete` turns any remaining pending line into an
error.

Build lime-juice from the conventional sibling checkout without writing build
artifacts into that repository:

```sh
cmake -S "$HOME/dev/FuzionCD/lime-juice" \
  -B working/vendor/lime-juice-build \
  -DCMAKE_BUILD_TYPE=Release
cmake --build working/vendor/lime-juice-build --parallel
```

Then compile every catalog entry and produce a fresh translated HDI from the
pristine working copy:

```sh
uv run fermion translation build \
  translations/fermion.toml \
  working/archives \
  working/emulator/fermion-debug.hdi \
  working/emulator/fermion-translation.hdi \
  --juice working/vendor/lime-juice-build/juice
```

The command verifies the pristine hashes and source anchors, decompiles and
compiles GM through lime-juice, audits the rebuilt control flow, repacks the
changed-length `DISKA`, resizes its FAT12 cluster chain if necessary, and
verifies every layer in the output image. Generated RKT, MES, archive, and JSON
report files are kept under ignored `working/translation-build/`.

The current catalog contains 557 canonical entries covering 581 physical
anchors in five MES files. The QA build grows `F0001.MES` from 17,509 to 26,040
bytes and `F0002.MES` from 4,402 to 5,964 bytes; starting from pristine image
SHA-256 `533a12e3e160af21a376de9eadde505a2d945d0069543a81131b564df7ddd4d8`,
it produces SHA-256
`bab370803cd7fe8b63251a1cc126d4f5eca37260a7487d53ff38cffd2eec8232`.
Generated filenames are intentionally not release interfaces; rebuild from the
hash-pinned pristine input before testing.

The underlying HDI support is also available directly:

```sh
uv run fermion hdi ls working/emulator/fermion-debug.hdi
uv run fermion hdi replace-file input.hdi FERM/DISKA rebuilt-DISKA output.hdi
```

## Headless runtime tests

The packaged CLI can drive NP2kai directly through libretro. It does not launch
RetroArch, Wine, or a GUI: scheduled keyboard and mouse-button input goes into
the emulator and the final framebuffer is written directly to PNG.

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

Run an exact number of frames, inject one or more key taps or mouse clicks, and
capture the final 640x400 framebuffer. A tap uses
`FRAME:KEY[:HOLD_FRAMES]`; a click uses
`FRAME:BUTTON[:HOLD_FRAMES]` with `left`, `right`, or `middle`:

```sh
uv run fermion emulator run working/emulator/fermion-translation.hdi \
  --frames 4500 \
  --tap 1000:return \
  --tap 1300:return \
  --tap 1750:return \
  --tap 2200:return \
  --tap 2900:return \
  --tap 4100:return \
  --capture working/emulator/headless-exchange.png
```

This short smoke run boots through the information screen, color-mode selector,
disclaimer, title, and translated menu, selects `START NEW GAME`, then advances
to the long translated reply. The command reports a SHA-256 over packed RGB
pixels for stable checkpoint comparisons.

The complete path is checked in as a named 34,200-frame route with 19 exact
framebuffer checkpoints. It verifies the display selector and title menu,
samples Marie's bedside grief and the Marie/Kanzaki confrontation, checks every
naturalized terminal stage plus the complete 2296 premise screen, then continues
through the first labelled exchange and in-scene menu. It also verifies the
translated HDI's content hash before booting:

```sh
uv run fermion emulator route \
  runtime/routes.toml \
  opening-translation-proof \
  working/emulator/fermion-translation.hdi
```

Checkpoint PNGs are written under ignored
`working/emulator/checkpoints/opening-translation-proof/`.

### Portable save fixtures

Ghidra analysis of the native save/load handlers established that `REG_00` is
the persistent global/template bank and `REG_01` through `REG_10` are the ten
loadable slots. A slot is a 6,944-byte snapshot of the game's global segment.
The checked-in [`runtime/save-fixtures.toml`](runtime/save-fixtures.toml) file
stores only hash-pinned sparse changes, never a complete slot or game image.

List the available fixtures and install one into a new copied HDI:

```sh
uv run fermion save list runtime/save-fixtures.toml
uv run fermion save apply \
  runtime/save-fixtures.toml \
  first-scene \
  working/emulator/fermion-translation.hdi \
  working/emulator/first-scene.hdi
```

Application refuses an in-place output, a pre-existing output, a changed
template bank, or a non-pristine target slot. The manifest currently contains
scenario-entry fixtures for the translated opening in `FOP.MES`, the first
scene in `F0000.MES`, and the following `F0001.MES` scene. Each targets
`REG_01`, so apply fixtures to separate generated HDIs rather than stacking
them into one image.

Capture a new fixture from an ignored NP2kai state with the same packaged CLI:

```sh
uv run fermion save capture \
  working/emulator/fermion-translation.hdi \
  working/emulator/checkpoint.state \
  working/emulator/checkpoint-fixture.toml \
  --name checkpoint \
  --description "Start SCENE.MES at its scenario entry." \
  --scenario scene.mes
```

The extractor finds the live 6,944-byte global segment by its expected scenario
name and similarity to `REG_00`, ignores unchanged template copies embedded in
the state, and refuses equally plausible candidates. It emits a standalone,
hash-pinned sparse manifest. `--state-offset 0x...` is available when a new core
layout needs an explicit disambiguation.

The three fixtures contain respectively 114 bytes in 40 hunks, 110 bytes in 35
hunks, and 114 bytes in 40 hunks. All three were reconstructed into fresh
translated images and accepted through the game's native `LOAD` flow. Create
the other two route inputs, then verify the corresponding short paths:

```sh
uv run fermion save apply runtime/save-fixtures.toml opening-dialogue \
  working/emulator/fermion-translation.hdi \
  working/emulator/opening-dialogue.hdi
uv run fermion save apply runtime/save-fixtures.toml second-scene \
  working/emulator/fermion-translation.hdi \
  working/emulator/second-scene.hdi
uv run fermion emulator route \
  runtime/routes.toml \
  opening-dialogue-save-fixture-proof \
  working/emulator/opening-dialogue.hdi
uv run fermion emulator route \
  runtime/routes.toml \
  first-scene-save-fixture-proof \
  working/emulator/first-scene.hdi
uv run fermion emulator route \
  runtime/routes.toml \
  second-scene-save-fixture-proof \
  working/emulator/second-scene.hdi
```

The FOP and F0000 routes execute 10,500 frames; the translated F0001 route now
continues to frame 15,300 and pins eight dialogue checkpoints after the native
load. Eight-frame keyboard pulses reliably cross the PC-98 scan without
triggering the menu repeat seen with longer holds. Every route verifies the
visible `LOAD` operation and the exact scenario marker inside serialized live
state; the F0001 proof also retains its 640x308 room-only checkpoint before the
dialogue hashes.
Game-native fixtures are portable across translation rebuilds as long as their
hash-pinned `REG` banks remain unchanged; libretro states remain the precise,
core-specific accelerator within one such route. Native loads resume at a
scenario entry rather than an arbitrary dialogue instruction.

Named routes may declare a `cache_frame`. On a successful cache miss the command
performs the full route and commits both the libretro state and its matching
writable HDI snapshot under ignored `working/emulator/state-cache/`; a failed
route discards the staged prefix. On a hit it restores that exact pair and
executes only the suffix. NP2kai's rewritten runtime mount path is excluded from
the otherwise content-sensitive system fingerprint. The current full route
resumes at frame 26,100, reducing the measured run on this Mac from about 49
seconds to 11.7 seconds while preserving the original ×20 CPU profile and final
framebuffer hash. The source HDI is always copied before NP2kai mounts it, so
emulator writes cannot invalidate the hash-pinned build artifact.

The cache is deliberately invalidated by any HDI, core, firmware/config,
effective-option, or prefix-input change. It accelerates repeated checks of one
build without claiming that an opaque emulator state is portable across changed
game data. Later scene-by-scene iteration should use checked-in sparse
game-native save fixtures and short boot/load routes; keep the full route as the
release check.

Force the full end-to-end path for release validation with:

```sh
uv run fermion emulator route \
  runtime/routes.toml \
  opening-translation-proof \
  working/emulator/fermion-translation.hdi \
  --no-cache
```

Changing `np2kai_clk_mult` is a separate machine profile, not a transparent
speed control. A ×4 experiment completed the same nominal 34,200 frames in
15.2 seconds, but every existing input landing and checkpoint hash changed.
Keep ×20 for canonical tests; use lower clocks only in separately recorded
routes with their own schedules and hashes.

The built-in core options match the Fermion configuration. Use `--options` to
load a RetroArch `.opt` file or repeat `--option KEY=VALUE` for overrides.
