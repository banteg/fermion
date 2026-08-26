# Fermion translation tools

Reproducible preservation and translation tooling for *Fermion: Mirai kara
no Houmonsha* on PC-98. Original game data and generated working images stay
out of version control.

```sh
uv sync
uv run fermion --help
```

Materialize verified raw HDM images from the preservation archive. The
command writes `working/disks/` and checks them against the MAME
software-list SHA-1 hashes in [`provenance/PROVENANCE.md`](provenance/PROVENANCE.md):

```sh
uv run fermion disks materialize artifacts/fermion_flux_dump.zip
```

The archival English lives in
[`translations/fermion.toml`](translations/fermion.toml). Schema and
authoring contract:
[`translations/README.md`](translations/README.md). Voice, glossary, and
locked decisions:
[`research/fermion_translation_brief.md`](research/fermion_translation_brief.md).

Disks, GM, catalog builds, emulator routes, save fixtures, and visual QA
are in [`DEVELOPMENT.md`](DEVELOPMENT.md).
