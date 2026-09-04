# Building and checking the translation

This guide is for working with the original disks, building an English game
image, and checking the result in an emulator. For translation decisions, start
with the [translation brief](research/fermion_translation_brief.md); for editing
English, use the [catalog guide](translations/README.md).

- [Prepare the source files](#prepare-the-source-files)
- [Read the scripts](#read-the-scripts)
- [Check and build the translation](#check-and-build-the-translation)
- [Check the game in an emulator](#check-the-game-in-an-emulator)
- [Start from a saved scene](#start-from-a-saved-scene)
- [Compare screenshots after a change](#compare-screenshots-after-a-change)

The examples use `working/archives/disk-a/` through `disk-d/` for unchanged
extracted scripts and `working/emulator/` for disk images. Generated files stay
under ignored `working/` paths. Keep the original extraction unchanged: catalog
references and checksums refer to those files.

## Prepare the source files

You need Python 3.12 or later and uv. Disk extraction also needs the preservation
archive described in [Provenance](provenance/PROVENANCE.md). Building a translated
image later in this guide requires an installed, pristine game HDI; extracting
the floppy files alone does not create that bootable image.

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
uv run fermion archive extract working/files/disk-a/DISKA working/archives/disk-a
```

Repeat the filesystem and archive extraction for disks B, C, and D, using
`disk-b`, `disk-c`, and `disk-d` directories and their corresponding installer
archives. The catalog expects this per-disk layout under `working/archives/`.

## Read the scripts

MES files hold the game’s scripts. This release uses General Message (GM), a
language understood by these tools and the GM-enabled version of lime-juice.

For translation review, start with a readable script that includes speaker
labels and removes identical file copies:

```sh
uv run fermion gm script working/archives --story > working/story-script.md
uv run fermion gm script working/archives > working/script.md
```

The story view starts with `FOP.MES` and includes scenes reachable before a
return to `MAIN.MES`, the title system. It lists the remaining scenes by
filename. The full dump uses extraction order. Neither is a playthrough: use
the transition graph to follow choices, rejoins, and revisited rooms.

```sh
uv run fermion gm transitions working/archives
uv run fermion gm transitions working/archives \
  --format dot \
  > working/scenario-graph.dot
```

See [Following the story](research/gm-scenario-flow.md) for the main branches.

### Find a line or speaker

Search decoded text without decompiling whole scripts. Mode 1 is the game’s
dictionary-compressed Japanese text; mode 2 holds single-byte ASCII strings.

```sh
uv run fermion gm texts working/archives --contains '見ない方'
uv run fermion gm texts working/archives --mode 2
uv run fermion gm speakers working/archives --attributed-only
uv run fermion gm speakers working/archives/disk-a/FOP.MES \
  --unresolved-only \
  --format tsv
```

The speaker command recognizes displayed name labels, including customizable
names. It leaves unlabelled dialogue for a translator to identify in context.
[Identifying speakers](research/gm-speaker-attribution.md) explains the source
instructions and their limits.

### Look for repeated or unlabelled text

Generate an inventory for a focused review:

```sh
uv run fermion gm inventory working/archives \
  --story \
  > working/story-inventory.tsv
```

This groups matching Japanese by text mode and known speaker, retaining all
source locations. English and context cells start blank; it is a source
inventory, not a translation-progress report. Flags identify repeated text,
speaker differences, and unknown speakers that need a closer read. Use
`--duplicates-only`, `--unresolved-only`, or `--format jsonl` to narrow the output.
Make translation edits in the catalog, not this generated table.

### Inspect script instructions

When working on the tools, check that script jumps land on instruction
boundaries. Pass one MES file or a directory tree:

```sh
uv run fermion gm audit working/archives
uv run fermion gm audit working/archives/disk-a/MAIN.MES --verbose
```

For a small rendering experiment, `replace-exact` can swap one unique compiled
MES file for a same-sized replacement in a copied image:

```sh
uv run fermion binary replace-exact \
  working/base.hdi original.MES patched.MES working/test.hdi
```

Use the translation build below for normal text changes; it handles changed
file sizes and archive repacking.

## Check and build the translation

[`translations/fermion.toml`](translations/fermion.toml) is the source of truth
for English text, source anchors, speakers, scene context, layout, and review
status. Generated MES files, disk images, and screenshots stay under ignored
`working/` paths. See
[`translations/README.md`](translations/README.md) for the entry format and
editing guidance.

Validate the catalog alone or against a hash-checked pristine extraction:

```sh
uv run fermion translation check translations/fermion.toml
uv run fermion translation check translations/fermion.toml \
  --source-dir working/archives \
  --verbose
```

Export a translator table, inspect register drift, or audit coverage:

```sh
uv run fermion translation table translations/fermion.toml \
  --source-dir working/archives \
  > working/translation-table.tsv
uv run fermion translation drift translations/fermion.toml --only-flagged
uv run fermion translation coverage \
  translations/fermion.toml \
  translations/coverage.toml \
  working/archives \
  --require-complete
```

The image build needs lime-juice with General Message support. The example
below assumes its source is already checked out at `$HOME/dev/FuzionCD/lime-juice`;
substitute your checkout path if it differs. Build into this project’s working
directory:

```sh
cmake -S "$HOME/dev/FuzionCD/lime-juice" \
  -B working/vendor/lime-juice-build \
  -DCMAKE_BUILD_TYPE=Release
cmake --build working/vendor/lime-juice-build --parallel
```

Then build a translated HDI from the pristine installed image. Here that input
is named `fermion-debug.hdi`; use your own pristine image path if different.
Choose a new output path for each build: existing outputs are refused.

```sh
uv run fermion translation build \
  translations/fermion.toml \
  working/archives \
  working/emulator/fermion-debug.hdi \
  working/emulator/fermion-translation.hdi \
  --juice working/vendor/lime-juice-build/juice
```

The build verifies hashes and source anchors, round-trips GM through lime-juice,
audits control flow, repacks changed archives, updates FAT12 storage, and verifies
the output image. It seeds untouched runtime name and term defaults while
preserving player-customized slots.

The HDI operations are also available directly:

```sh
uv run fermion hdi ls working/emulator/fermion-debug.hdi
uv run fermion hdi replace-file input.hdi FERM/DISKA rebuilt-DISKA output.hdi
```

## Check the game in an emulator

The packaged CLI can drive NP2kai directly through libretro. It does not launch
RetroArch, Wine, or a GUI: scheduled keyboard and mouse-button input goes into
the emulator and the final framebuffer is written directly to PNG.

The following setup is for an Apple Silicon Mac. It builds the pinned NP2kai
revision used by this project as a native arm64 core and copies firmware from
an existing RetroArch installation. Adjust the build and firmware paths for
other systems. Keep source, firmware, cores, states, and captures under ignored
`working/` paths:

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

The checked-in `opening-translation-proof` route verifies the display selector,
title menu, opening premise, early dialogue, and in-scene menu against pinned
framebuffer checkpoints and the translated HDI content hash:

```sh
uv run fermion emulator route \
  runtime/routes.toml \
  opening-translation-proof \
  working/emulator/fermion-translation.hdi
```

Checkpoint PNGs are written under ignored
`working/emulator/checkpoints/opening-translation-proof/`.

Verify that a fresh translated image opens both editors with the catalog's
English names and adult terms already populated:

```sh
uv run fermion emulator route \
  runtime/routes.toml \
  english-runtime-defaults-proof \
  working/emulator/fermion-translation.hdi
```

## Start from a saved scene

Save fixtures let you start at a known scene without replaying the opening.
They use the game’s own save system. `REG_00` holds persistent defaults;
`REG_01` through `REG_10` are the ten loadable slots. Each slot stores 6,944 bytes
of game state, as confirmed by the original save/load code in Ghidra.

The checked-in [fixture file](runtime/save-fixtures.toml) records only the bytes
that differ from a known template, with checksums to identify that template.
It contains no complete save slot or game image.

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

Create the other two route inputs, then verify their short paths:

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

The save-fixture routes verify the visible native `LOAD`, serialized scenario
marker, and pinned dialogue checkpoints. The
`second-scene-three-row-proof` route exercises
`launch-humans-ended-mutants` across all three dialogue rows, providing the
runtime basis for the catalog's 61-column, three-row story default:

```sh
uv run fermion emulator route \
  runtime/routes.toml \
  second-scene-three-row-proof \
  working/emulator/second-scene.hdi
```

### Emulator states and rebuilds

Manual NP2debug `.S00`/`.S01` slots are opaque, exact-image snapshots. Check a
slot against the image it will resume before loading it:

```sh
uv run fermion save check-np2debug-state \
  path/to/np21.S01 \
  working/emulator/fermion-translation-current.hdi
```

The check compares the open `DISKA` length cached in the state's DOS system
file table with `FERM/DISKA` in the HDI. It catches the known seven-byte stale
state failure, which restored an old file cursor and made a GP4 read begin
inside its payload. A pass proves only that the lengths match, not that the
contents do: discard and recreate manual NP2debug slots after every image
rebuild.

Game-native fixtures are portable across translation rebuilds as long as their
hash-pinned `REG` banks remain unchanged; libretro states remain the precise,
core-specific accelerator within one such route. Native loads resume at a
scenario entry rather than an arbitrary dialogue instruction.

Named routes may declare a `cache_frame`: on a miss the command runs the full
route and stores the libretro state plus matching writable HDI snapshot under
ignored `working/emulator/state-cache/`; on a hit it restores that pair and
executes only the suffix. The cache is invalidated by any HDI, core,
firmware/config, effective-option, or prefix-input change, and the source HDI
is always copied before NP2kai mounts it. Use checked-in game-native save
fixtures and short routes for scene-by-scene iteration; keep the full route
with `--no-cache` as the release check.

Force the full end-to-end path for release validation with:

```sh
uv run fermion emulator route \
  runtime/routes.toml \
  opening-translation-proof \
  working/emulator/fermion-translation.hdi \
  --no-cache
```

## Compare screenshots after a change

The screenshot suite helps catch changes in line wrapping, menus, and other
visible text. It covers selected scenes; it does not replace reading the
translation or playing through the branches.

[`runtime/visual-qa.toml`](runtime/visual-qa.toml) groups the checked-in routes
into one screenshot suite and declares which rebuilt MES files can affect each
case. Run it against the JSON report from a fresh translation build:

```sh
uv run fermion emulator qa \
  runtime/visual-qa.toml \
  working/translation-build/build-report.json
```

The command verifies that the report's exact output HDI still exists unchanged,
applies any required sparse save fixture to a temporary copy, and records every
selected route checkpoint under `working/visual-qa/screenshots/`. The generated
`working/visual-qa/manifest.json` retains per-file build hashes, route/runtime
fingerprints, screenshot hashes, and the inputs for every case. On later runs,
only cases whose declared MES dependencies, fixture, route schedule, source
image, runtime defaults, core, firmware/config, or options changed are executed.
Use `--case ROUTE` for a narrower probe or `--force` to refresh selected cases.

Changed captures preserve prior and new PNGs under
`working/visual-qa/diff/`. The command also reports rebuilt MES files without a
declared visual-QA case; ordinary `emulator route` runs continue to enforce
every pinned hash.

Changing `np2kai_clk_mult` changes input timing and checkpoint hashes, not just
speed: keep ×20 for canonical tests and record lower clocks as separate routes
with their own schedules and hashes.

The built-in core options match the Fermion configuration. Use `--options` to
load a RetroArch `.opt` file or repeat `--option KEY=VALUE` for overrides.
