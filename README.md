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
