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
- an explicit stable `speaker` and short scene `context`;
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
speaker = "narrator"
context = "The same narration in two equivalent control-flow branches."
status = "draft"
notes = "Keep the wording synchronized across both anchors."
```

This keeps the English and translator notes in one place while applying them to
every physical copy. Identical Japanese may still use separate entries when the
surrounding scene genuinely requires different English; that contextual split
is explicit and visible to the coverage report.

Catalog schema 4 makes speaker and context mandatory. Source verification
checks speaker identities that GM encodes directly:

- a literal `【name】` prefix uses that exact name;
- a dynamic bracket/name/bracket sequence uses one of the stable
  `name-slot:mother`, `name-slot:older-sister`, `name-slot:dear-person`,
  `name-slot:friend-1`, or `name-slot:friend-2` roles;
- text with neither form remains contextual and may receive a documented human
  attribution such as `prologue-doctor`.

Do not infer a speaker from `「…」` versus `『…』`. The opening alternates those
styles without any speaker-state opcode. The full evidence and corpus totals
are in [`../research/gm-speaker-attribution.md`](../research/gm-speaker-attribution.md).

## Composite interpolation contract

Schema 4 deliberately does not pretend that a physical text record containing
only `】...` is a complete display line. The next schema will represent rendered
messages as ordered physical text segments separated by immutable interpolation
segments. The checked-in TOML remains canonical; a merged translator table or
database is only a generated view with validated import.

Authoring tokens use non-CP932 delimiters so accidental compilation fails:

```text
⟦name:mother⟧
⟦name:older-sister⟧
⟦name:dear-person⟧
⟦name:friend-1⟧
⟦name:friend-2⟧
⟦term:slot-1⟧
⟦term:slot-2⟧
```

They are UTF-8 catalog metadata and must never reach lime-juice. Import checks
that the token sequence, order, and multiplicity match the source composite,
splits English on those tokens, maps each literal chunk back to its original
text-opcode anchor, and leaves the copy/render instructions unchanged. Only
records separated by one of these recognized token spans may be merged for
display; ordinary adjacent records keep a one-to-one source/target mapping.

The complete design and locked editorial policies are recorded in
[`../research/fermion_plot_translation_notes.md`](../research/fermion_plot_translation_notes.md).

For holistic plot review or LLM-assisted translator notes, generate the compact
speaker-annotated corpus under the ignored working directory:

```sh
uv run fermion gm script working/archives > working/script.md
```

This removes byte-identical MES copies, keeps each source offset, escapes
embedded newlines, and labels only speakers proven by the bytecode. It is a
review artifact; canonical English, context, status, and notes still belong in
`fermion.toml`.

The current statuses are:

- `draft`: recorded but not yet exercised in the game;
- `runtime-proof`: renderer or control-flow proof whose wording is still
  provisional;
- `qa-ready`: source and context review are complete, the wording builds into a
  fresh image, and an automated route reaches it without structural or visual
  regression; a human playtest can still send it back for editorial revision;
- `runtime-verified`: the current wording and layout have been exercised in the
  game. This is not necessarily final editorial approval.

The current catalog contains 103 canonical records covering 119 physical
anchors across `MAIN.MES`, `FOP.MES`, and `F0000.MES`. The setup selector pair,
three-copy fiction disclaimer, repeated terminal timing records, and contextual
status labels demonstrate when physical anchors should share or split a
canonical translation.

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

The first closed scope is `opening-prologue`: all 118 physical text records in
`FOP.MES`, from the bedside scene through the 2296 premise screen. Ninety-seven
records are translated, 21 unchanged title/layout records are explicitly
excluded, and none are pending. They represent 74 canonical source lines, with
duplicate timing records merged only when their target and context agree.

The older `boot-to-first-scene-menu` scope remains deliberately broader. It
contains 178 physical anchors and 120 canonical source lines; 119 anchors are
translated and 59 remain pending across setup UI, unchanged layout records, and
the opening of `F0000.MES`. Exclusions are scope-local, so closing the focused
FOP scope does not silently classify records in this broader work queue. Use
`--require-complete` only for a scope expected to be closed; deliberate
non-translations belong in `[[scopes.exclusions]]` with exact source anchors and
a non-empty reason.

The prologue release gate is:

```sh
uv run fermion translation coverage \
  translations/fermion.toml \
  translations/coverage.toml \
  working/archives \
  --scope opening-prologue \
  --verbose \
  --require-complete
```

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

Export the reviewable translator table after source verification:

```sh
uv run fermion translation table translations/fermion.toml \
  --source-dir working/archives \
  > working/translation-table.tsv
```

The TSV columns are `id`, `file`, `offset`, `speaker`, `jp`, `en`, `context`,
and `status`. It expands canonical multi-anchor entries to one physical row but
does not duplicate their English or notes in the source catalog. Use
`--format jsonl` when a structured stream is more convenient.

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
