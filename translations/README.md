# Translation catalog

`fermion.toml` is the checked-in source of truth for Fermion's translated text
and the reasoning behind it. It intentionally contains text and metadata, not
compiled MES files or original game media.

Each `[[files]]` table identifies one pristine MES file by its logical
`DISKA/FILENAME` archive path, extracted source path, and SHA-256. Each
`[[entries]]` table records:

- a stable, descriptive `id`;
- one or more pristine text-opcode anchors and their shared source mode;
- the exact original Japanese and current English translation;
- the target encoding mode and optional dialogue-box width;
- a progress `status` and free-form translator `notes`.

Offsets always refer to the pristine file named by the enclosing catalog, not a
rebuilt or relocated MES. Notes should retain useful alternatives, speaker and
scene context, tone decisions, technical compromises, and anything worth
revisiting. Do not erase an unresolved nuance merely because the current probe
uses shorter wording.

A line with one physical occurrence may use the compact `file` and `offset`
fields. Exact duplicates use one canonical entry with an `anchors` array:

```toml
[[entries]]
id = "shared-line"
anchors = [
  { file = "DISKA/MAIN.MES", offset = 0x1000 },
  { file = "DISKA/MAIN.MES", offset = 0x1200 },
]
source_mode = 1
source = "同じ文"
translation = "The same line"
```

This keeps the English and translator notes in one place while applying them to
every physical copy. Identical Japanese may still use separate entries when the
surrounding scene genuinely requires different English; that contextual split
is explicit and visible to the coverage report.

The current statuses are:

- `draft`: recorded but not yet exercised in the game;
- `runtime-proof`: renderer or control-flow proof whose wording is still
  provisional;
- `runtime-verified`: the current wording and layout have been exercised in the
  game. This is not necessarily final editorial approval.

The current catalog contains 17 canonical records covering 25 physical anchors
across `MAIN.MES`, `FOP.MES`, and `F0000.MES`. The setup selector pair and
three-copy fiction disclaimer are runtime-verified examples of canonical
multi-anchor entries.

## Coverage ledger

`coverage.toml` defines reviewable ranges rather than relying on which lines
happen to be in the catalog. Every decoded text opcode in a range is classified
as translated, explicitly excluded with a reason, or pending. Pending records
are grouped by exact `(source_mode, source)` so a duplicate Japanese line
appears once with all of its physical anchors:

```sh
uv run fermion translation coverage \
  translations/fermion.toml \
  translations/coverage.toml \
  working/archives \
  --verbose
```

The initial `boot-to-first-scene-menu` scope contains 178 physical anchors and
120 unique source lines. Seventeen canonical lines (25 anchors) are translated;
103 unique lines (153 anchors) remain pending. Nothing is silently treated as
done. Use `--require-complete` in a release gate once a scope is expected to be
closed; deliberate non-translations belong in `[[scopes.exclusions]]` with exact
source anchors and a non-empty reason.

The early duplicates are compiled control-flow, not extractor noise:

- color and monochrome labels each occur twice in one six-item machine/disk
  setup menu, alongside the 2-FDD and 1-FDD+RAM choices;
- each of the disclaimer's three visible lines occurs in three distinct
  initialization branch bodies.

Those copies share canonical translations. Other repeated lines are only
merged when their anchors are added to the same catalog entry.

Validate structure and encodability after every edit:

```sh
uv run fermion translation check translations/fermion.toml
```

When the pristine extraction is available, also verify every file hash and
every source offset, mode, and Japanese string:

```sh
uv run fermion translation check translations/fermion.toml \
  --source-dir working/archives \
  --verbose
```

For an incremental batch:

1. Add or revise catalog entries while preserving stable IDs.
2. Record translation alternatives and uncertainties in `notes`.
3. Validate against the pristine sources.
4. Build a fresh image from the pristine copy:

   ```sh
   uv run fermion translation build \
     translations/fermion.toml \
     working/archives \
     working/emulator/fermion-debug.hdi \
     working/emulator/fermion-translation.hdi \
     --juice working/vendor/lime-juice-build/juice
   ```

5. Add or update a named route in `runtime/routes.toml` when the text is
   reachable automatically, then promote its status after the runtime check.

The build writes only ignored artifacts. It compiles each line through
lime-juice, verifies unchanged text and external MLL targets, repacks the
containing installer archive, and updates the copied HDI's FAT filesystem. MES
and archive files no longer need to preserve their original total sizes.
