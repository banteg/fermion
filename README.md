# Fermion: Mirai kara no Houmonsha

An archival English translation of **Fermion: Mirai kara no Houmonsha**
(フェルミオン ～未来からの訪問者～), Silky’s 1995 adventure game for the
NEC PC-98.

This repository brings together the English translation, a guide to the story
and its characters, records of the original disks, and the tools needed to put
the translation back into the game.

## The game

*Fermion: Visitor from the Future* is a science-fiction adult adventure with a
surprising second act. In 2296, centuries of pollution have left humanity’s
genetic inheritance in ruins. Connie, a mutant hunter who can turn into a cat,
is sent three hundred years into the past to collect healthy genetic material.
She arrives in 1996 and finds a home with the Takano family.

What begins as an unlikely mix of domestic comedy, time travel, and erotic
adventure turns into something stranger: a research facility, a betrayal,
ventilation ducts, machinery puzzles, and an escape. Connie’s cat form becomes
as useful for getting through a vent as it was for hiding in a quiet household.
Underneath it all is a story about family, grief, and the cost of trying to
recover a life you’ve lost.

The original pitch for this project called it **“the Half-Life of hentai.”**
Gordon Freeman merely lacked the catgirl transformation mechanic.

## Our approach

We want to make the original work readable in English while preserving its
character. That means translating in scene context, keeping character voices
and relationships distinct, and retaining the original story, choices, and
customizable names. English already printed by the game keeps its period
wording and presentation. Small restoration corrections are documented rather
than silently folded into the text.

The translation lives in [translations/fermion.toml](translations/fermion.toml).
Each entry connects the English to its original Japanese and location in the
game, with context and notes where a choice needs explaining. Extracted scripts
and review tables are reading aids; edits belong in the catalog.

## Where things stand

The catalog covers the declared translation scope, including story text and
menus. Automated checks verify the source references, text encoding, and
coverage; selected emulator routes also check how the translation appears on
screen. Full linguistic review and playtesting are still unfinished. Coverage
is not a claim that every line has been reviewed or every branch played.

## Read and contribute

- **Find your way through the escape:** the [facility maps](research/facility-maps.md)
  show the vents, corridors, useful rooms, and puzzle sequence. **Facility spoilers.**

- **Understand the translation:** the [translation brief](research/fermion_translation_brief.md)
  covers the plot, characters, voice, terminology, and restoration decisions.
  **Full spoilers.**
- **Edit or review the English:** the [catalog guide](translations/README.md)
  explains entries, source references, names, layout, and review status.
- **Build and check the game:** the [development guide](DEVELOPMENT.md) walks
  through disk extraction, translation builds, and emulator checks.
- **Trace the original release:** the [disk provenance record](provenance/PROVENANCE.md)
  identifies the source archive and records its checksums.
- **Understand the file formats:** the [technical notes](research/README.md)
  explain scene order, speaker labels, and how support for the game’s script
  format was recovered.

For translation changes, read the Japanese in scene context, preserve entry IDs
and source references, and leave a note when the wording depends on an ambiguity
or a restoration decision. Then validate the catalog and check the affected
scenes in game.

## Tools

For a general-purpose PC-98 emulator in your browser, see
[WebNP2](https://uraraworks.github.io/WebNP2/?lang=en) and its
[user guide](https://uraraworks.github.io/WebNP2/help.html?lang=en).
It accepts local disk images and keeps them in browser storage without uploading
them. Download modified disks for backups; clearing site data removes browser
saves. This project does not host a separate player or disk images.
See [Emulator setup](EMULATORS.md) for the browser font fix and RetroArch as a
local alternative.

The Python tools use [uv](https://docs.astral.sh/uv/) and Python 3.12 or later:

```sh
uv sync
uv run fermion --help
uv run fermion translation check translations/fermion.toml
```

Building a playable image also requires the original game data, an installed
base image, and lime-juice with General Message support. Emulator checks need
NP2kai and its firmware. See [Development](DEVELOPMENT.md) for setup and commands.

Original game data and generated disk images are not included in version
control. Local source archives live under `artifacts/`; extracted files, builds,
and screenshots live under `working/`.
