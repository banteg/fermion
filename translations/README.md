# Translation catalog

`fermion.toml` is the checked-in source of truth for Fermion's translated text
and the reasoning behind it. It intentionally contains text and metadata, not
compiled MES files or original game media.

The English version carries the locked content note from
[`../research/fermion_translation_brief.md`](../research/fermion_translation_brief.md)
section 11 verbatim. Any distribution-specific age alteration must be a
disclosed, mechanically separate override; it is not part of this canonical
catalog.

Each `[[scenes]]` table stores one stable scene ID and its shared context.
Entries reference that ID instead of repeating prose thousands of times. Each
`[[files]]` table identifies one pristine MES file by its logical
`DISKA/FILENAME` archive path, extracted source path, SHA-256, and optional
default `box_width`, visible `box_rows`, and `wrap_mode`. Catalog version 7
retains catalog version 4's simple records and catalog version 5's composites,
keeps catalog version 6's speaker evidence split, and adds reusable scenes. Each
`[[entries]]` table records:

- a stable, descriptive `id`;
- one or more pristine text-opcode anchors and their shared source mode;
- the exact original Japanese and current English translation;
- a canonical lowercase `speaker`, its `attribution`, and a `scene` reference;
- the target encoding mode and optional per-entry surface-layout overrides;
- a progress `status` and optional free-form translator `notes`.

Offsets always refer to the pristine file named by the enclosing catalog, not a
rebuilt or relocated MES. `notes` are for line-specific alternatives,
ambiguities, tone decisions, technical compromises, and anything worth
revisiting. Omit them when the speaker and resolved scene context plus the
checked-in voice brief fully explain the translation; do not repeat a
slice-wide voice policy on every line. Do not erase an unresolved nuance merely
because the current probe uses shorter wording.

Scene `context` and entry `notes` describe the Japanese source scene. Use
**adult** only where the plot itself requires the distinction, such as adult
Kaori versus her younger self; do not insert age labels as a localization
workaround.

Draft canonical English by reading the Japanese in scene context and applying
the checked-in plot, voice, and terminology notes. Automated tools may expose
anchors, duplicates, speakers, length problems, and runtime regressions; they
must not manufacture the catalog prose as a substitute for translation.

The catalog stores readable, unwrapped English. At build time the effective
width inserts newlines at word boundaries and preserves explicit authoring
newlines. An entry override wins when a specific display differs from its file
default. `wrap_mode = "characters"` is reserved for narrow vertical surfaces,
where every character cell may be a break point. Validation rejects a line or
row count that exceeds the effective `box_width` and `box_rows`.

The ordinary numbered story files use a 61-column, three-row declaration. A
save-fixture emulator route directly exercises all three rows of
`launch-humans-ended-mutants` in F0001. Silky's catalog is deliberately not
covered by that default: its decompiled `text-window` instructions expose
full-page cards, two-, three-, and four-row panels, and Koi Hime's two-column
vertical cards. `SILK.MES` therefore carries per-surface limits, explicit
newlines for adjacent text opcodes, and character-cell wrapping on the vertical
cards. The adjacent-record policy test checks the combined rows, not merely
each source record in isolation. Other terminal, editor, and special card
surfaces still require route-specific visual QA.

A story record whose source is only a run of `・` followed by `。` is a pure
silent beat and always translates to the fixed mode-2 ASCII `...`. Catalog
validation rejects variable-length dot runs and parenthesized variants. The
opening terminal's single-glyph progress records are timed UI animation and are
intentionally exempt.

A line with one physical occurrence may use the compact `file` and `offset`
fields. Exact duplicates use one canonical entry with an `anchors` array:

```toml
[[scenes]]
id = "equivalent-narration-branches"
context = "The same narration in two equivalent control-flow branches."

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
attribution = "inferred"
scene = "equivalent-narration-branches"
status = "draft"
notes = "Keep the wording synchronized across both anchors."
```

This keeps the English and translator notes in one place while applying them to
every physical copy. Identical Japanese may still use separate entries when the
surrounding scene genuinely requires different English; that contextual split
is explicit and visible to the coverage report.

Catalog validation also audits exact duplicate English. Records with identical
source, translation, speaker, attribution, and scene must share anchors or
composite occurrences whenever their encoding, layout, and QA status agree.
When a real mechanical difference prevents sharing, every retained record uses
a `notes` value beginning with `Duplicate split:` to explain it. Notes alone do
not make otherwise mergeable records distinct.

Catalog version 7 makes speaker identity, attribution evidence, scene
identity, and scene context separate fields. `speaker` is a stable lowercase ID
such as `connie`, `kanzaki`, `catalog-copy`, or `name-slot:mother`.
`attribution` is `proven` only when that record's source contains a recognized
literal or dynamic speaker label; scene-based assignments use `inferred`.
Source verification checks every `proven` identity against the original label.
Each entry's `scene` must resolve to exactly one top-level context, and duplicate
or unused scene records are rejected. Catalog versions 4 through 6 remain
readable for older fixtures; their per-entry contexts resolve in memory without
becoming a second scene store.

GM can encode speaker identities directly:

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

Catalog version 7 retains catalog version 5's representation of rendered
messages as ordered physical text segments separated by immutable interpolation
segments. A physical record containing only `】...` is therefore no longer
presented as a complete display line. The checked-in TOML remains canonical; a
merged translator table or database is only a generated view, and any future
import must be validated.

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

They are UTF-8 catalog metadata and must never reach lime-juice. Catalog
validation checks that the token sequence, order, and multiplicity match the
source composite,
splits English on those tokens, maps each literal chunk back to its original
text-opcode anchor, and leaves the copy/render instructions unchanged. Only
records separated by one of these recognized token spans may be merged for
display; ordinary adjacent records keep a one-to-one source/target mapping.

The physical segment pattern can force a source-initial token to remain first
in English. Do not disguise that constraint with a `NAME--I ...` construction.
Write a grammatical token-led clause (`NAME gets ...`, `NAME's ... is ...`) or,
when the source itself breaks off, a genuine thought pause. Moving a token by
inserting new text opcodes remains out of scope until that renderer change has
its own proven and logged compatibility contract.

Source nominal fragments may retain that shape: `NAME... an image of her ...`
is preferable to bending the sentence around a trailing “in the image” merely
to manufacture a finite token-led clause.

`[[tokens]]` records the Japanese default, ASCII authoring default, and any
reset initializer to patch after decompilation. Each runtime string begins with
an `ff` marker and a render-mode byte. Ghidra analysis of `mes_op_4b` at
`1000:2529` shows that indirect text reads that second header byte, copies the
payload, and passes the recovered mode to the ordinary `0x4a` renderer at
`1000:23bb`. The builder therefore stores English defaults as `ff 02`, plain
ASCII, and zero padding. No executable patch is required.

The five name slots remain 14 bytes and the two term slots remain 16 bytes.
`0x4b` copies payloads in 16-bit pairs until it sees an aligned zero word, and
both editors share a 14-byte scratch string. Ten ASCII characters are therefore
the largest zero-surgery value that leaves the required two-byte terminator
inside every source and destination buffer. Each default is capacity-checked
against that common editor limit, and its wrapping width is its half-width ASCII
length.

Player-visible dialogue speaker tags use Title Case. Fixed labels therefore
render as `[Connie]`, `[Kanzaki]`, or `[Woman's Voice]`; dynamic labels retain
their authoring token and render the editable display value, such as
`[Kanako]`. Bracketed Silky product headings are titles, not speaker tags, and
retain their own capitalization.

`NAME.MES` and `MONO.MES` retain their original free-form editor destinations,
confirmation flow, and save/load ranges. The builder bypasses the Japanese
character-class menu and replaces the visible grid and coordinate mapping with
one mode-2 Latin palette. Append, scan, backspace, and mouse-action paths use
the engine's byte reference at the scratch buffer's absolute base; cursor motion
advances by one half-width column. The editor reasserts the `ff 02` header and
writes payload bytes at indexes 2 through 11, rejecting an eleventh character.
Legacy mode-1 values remain renderable and untouched in persistent slots; if a
player chooses to edit one, the temporary buffer starts empty in the supported
Latin mode, and cancelling still preserves the old value.

This keeps the slot addresses and save format intact. The earlier operand-tail
probe correctly showed that the two bytes following a `0x4b` reference are not
a mode switch, but it tested the wrong control point: the operative mode is the
referenced string header. Emulator probes now cover the mode-2 defaults, a
ten-character edit, eleventh-character rejection, backspace, save, cold reload,
and indirect dialogue rendering.
An initializer's persistent slot must map to the same authoring token. Each
`[[composites]]` table then stores one merged source/translation pair and one or
more physical occurrences. Text segments retain their pristine opcode offset,
mode, and source; token segments retain the exact copy/render span and its
SHA-256. Verification requires byte adjacency across the whole occurrence and
rejects missing, reordered, duplicated, unknown, or leaked tokens.

```toml
[[tokens]]
id = "name:dear-person"
source = "加奈子"
translation = "Kanako"
initializers = [
  { file = "DISKA/MAIN.MES", offset = 0x18ea, slot = 0x0404 },
]

[[composites]]
id = "example-name-line"
target_mode = 2
source = "【⟦name:dear-person⟧】「こんにちは。」"
translation = "[⟦name:dear-person⟧] \"Hello.\""
speaker = "name-slot:dear-person"
attribution = "proven"
context = "Example only."
status = "draft"
notes = "The catalog holds the merged display line."

[[composites.occurrences]]
file = "DISKA/F0003.MES"
segments = [
  { kind = "text", offset = 0x1000, source_mode = 1, source = "【" },
  { kind = "token", token = "name:dear-person", start = 0x1004, end = 0x1013, sha256 = "..." },
  { kind = "text", offset = 0x1013, source_mode = 1, source = "】「こんにちは。」" },
]
```

The complete design, translator guidance, QA checklist, and locked editorial
policies are recorded in
[`../research/fermion_translation_brief.md`](../research/fermion_translation_brief.md).

For holistic plot review or LLM-assisted translator notes, generate the compact
speaker-annotated corpus under the ignored working directory:

```sh
uv run fermion gm script working/archives > working/script.md
```

This removes byte-identical MES copies, keeps each source offset, escapes
embedded newlines, and labels only speakers proven by the bytecode. It is a
review artifact; canonical English, context, status, and notes still belong in
`fermion.toml`.

Before a register pass, generate the deterministic drift report:

```sh
uv run fermion translation drift translations/fermion.toml --only-flagged
```

The report groups canonical prose once per file and canonical speaker, ignores records
without English words, and measures contractions, stiff forms, sentence length,
and repeated two-word openings. Flags compare a group with that exact speaker's
other files when at least three qualifying groups exist, otherwise with the
whole corpus. A single `connie` baseline now includes both contextual and
bytecode-proven lines; the separate `attribution` field preserves that evidence
without fragmenting character-level diagnostics. Treat every flag as a
line-review lead, never as a target rate.

The current statuses are:

- `draft`: recorded, but its source meaning, context, or English is still
  incomplete;
- `translated`: source-anchored English exists and passes catalog, source, and
  structural build checks. This does not claim a dedicated linguistic review or
  in-game execution of the individual record;
- `reviewed`: the exact Japanese, scene context, and English wording have received
  a dedicated linguistic review, but the record is not necessarily exercised in
  the game;
- `runtime-verified`: the current wording and layout have been exercised in the
  game. This is runtime evidence, not a claim of final editorial approval.

At this checkpoint, 12,608 records are `translated`, 279 are `reviewed`, and 15
are `runtime-verified`. The reviewed set is limited to records whose wording
changed during dedicated source-and-context passes over the ending,
token-initial prose, and later full-catalog review findings; unchanged
neighboring records were not bulk-promoted.

The current catalog contains 12,902 canonical records covering 17,680 physical
anchors across 76 MES files: `MAIN.MES`, `FOP.MES`, the translated story
through the `F0042.MES` ending, scene replay, both mirrored editors, and the
period Silky's catalog.
The duplicate audit consolidated 101 redundant records across 61 reviewed
groups without changing a physical translation. Four catalog-copy wording
groups remain as ten annotated records because their panels need different
layout overrides.
The setup selector pair, three-copy fiction disclaimer,
repeated terminal timing records, and context-safe duplicate collapses in the
Project D and first Kanako slices demonstrate when physical anchors should
share or split a canonical translation. The 34 F0003 composites demonstrate
when several physical anchors must instead appear as one rendered line. The
departure-eve slice shows the inverse cross-file case: two contentless pause
records in `F0000.MES` join canonical entries first anchored in `F0001.MES`
and `F0002.MES`.

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

All 22 focused story scopes and the broader `boot-to-first-scene-menu` scope
are closed: every decoded text record is either translated or explicitly
excluded, and none are pending. Per-scope history — anchor counts, duplicate
consolidations, voice notes, and save-fixture caveats — lives in this
repository's commit history instead of being restated here. Coverage work is
complete; current effort is dedicated linguistic review and in-engine QA.

Fresh translated images seed the source-derived English names and adult terms
into the persistent `REG_00` template bank. The build only migrates slots that
still contain their Japanese source defaults (or are blank), so rebuilding from
an image with player-customized values does not overwrite those choices.

Gate any closed scope with:

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

The TSV columns are `id`, `file`, `offset`, `speaker`, `attribution`, `scene`,
`jp`, `en`, `context`, and `status`. It expands canonical multi-anchor entries
to one physical row but does not duplicate their English or notes in the source
catalog. Use `--format jsonl` when a structured stream is more convenient.

For an incremental batch:

1. Add or revise catalog entries while preserving stable IDs.
2. Record line-specific translation alternatives and uncertainties in `notes`;
   omit routine voice-policy boilerplate.
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
