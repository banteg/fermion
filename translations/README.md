# Translation catalog

`fermion.toml` is the checked-in source of truth for translated text and
translator reasoning. Generated MES files and original game media do not belong
in the catalog.

The catalog is the source-faithful archival English. Policy is section 10 of
[`../research/fermion_translation_brief.md`](../research/fermion_translation_brief.md).
Do not alter it for release.

The catalog contains:

- `[[scenes]]` records with stable IDs and shared source-scene context;
- `[[files]]` records with logical archive paths, extracted paths, SHA-256
  hashes, and optional layout defaults;
- `[[entries]]` records with stable IDs, pristine anchors, Japanese source,
  canonical English, speaker and attribution, scene, encoding, status, layout
  overrides, and optional translator notes.

Offsets refer to the pristine MES named by the catalog. Use `notes` for
line-specific alternatives, ambiguity, tone decisions, and technical
compromises; omit routine voice policy already established by the scene and
translation brief. Scene `context` and entry `notes` describe the Japanese
source rather than adding localization-only age framing or restating the
section 7 refusal rule.

Draft English from the Japanese in scene context. Automated tools can expose
anchors, duplicates, speakers, layout problems, and runtime regressions, but
they do not replace translation.

English printed by the original game follows the archival treatment in section
12 of the translation brief, including its single logged spelling correction.

The catalog stores readable, unwrapped English. At build time, the effective
width inserts word-boundary newlines while preserving explicit authoring
newlines. File-level `box_width`, `box_rows`, and `wrap_mode` values define the
default; entry overrides describe real surface-specific differences.

Numbered story files normally use 61 columns and three rows. Special cards and
`SILK.MES` panels declare their own limits. Narrow vertical cards use
`wrap_mode = "characters"`, and adjacent text records sharing a surface are
checked together.

A story record containing only a run of `・` followed by `。` is a silent beat
and translates to mode-2 ASCII `...`. The opening terminal's single-glyph
progress animation is exempt.

A single occurrence uses `file` and `offset`; exact duplicates use one entry
with an `anchors` array. Identical Japanese may remain separate when scene
context requires different English.

Validation merges records with identical source, translation, speaker,
attribution, scene, encoding, layout, and QA status. A genuine mechanical split
uses a note beginning with `Duplicate split:`.

`speaker` is a stable lowercase identity such as `connie`, `kanzaki`,
`catalog-copy`, or `name-slot:mother`. `attribution = "proven"` requires a
recognized literal or dynamic source label; scene-based assignments use
`inferred`. Every `scene` resolves to one top-level context record.

Do not infer speakers from Japanese quote style. The recovered label rules,
name slots, and corpus evidence are documented in
[`../research/gm-speaker-attribution.md`](../research/gm-speaker-attribution.md).

## Composite interpolation contract

Composites represent rendered messages split across physical text records by a
runtime name or term substitution. Authoring tokens use non-CP932 delimiters:

```text
⟦name:mother⟧
⟦name:older-sister⟧
⟦name:dear-person⟧
⟦name:friend-1⟧
⟦name:friend-2⟧
⟦term:slot-1⟧
⟦term:slot-2⟧
```

Each occurrence preserves ordered text segments and immutable token spans.
Validation:

1. requires the source and English token sequence, order, and multiplicity to
   match;
2. maps each literal English segment back to its original text-opcode anchor;
3. preserves the intervening copy/render instructions;
4. rejects missing, reordered, duplicated, unknown, or leaked tokens.

Only records separated by a recognized token span may be merged. Ordinary
adjacent records retain one-to-one source and target mappings.

Keep punctuation outside tokens and write clauses that remain grammatical for
supported custom values. A source-initial token may need to remain first in
English; use a grammatical token-led clause rather than adding text opcodes to
move it.

The name and term editors use mode-2 half-width ASCII while preserving their
runtime slots and save ranges. Values are limited to ten ASCII characters.
Exercise default and maximum-length values through editing, saving, cold
loading, dialogue, the identity reveal, and the final letter.

Slot roles and the identity-reveal invariant are in section 5 of the
[translation brief](../research/fermion_translation_brief.md).

## Status and review

- `draft`: meaning, context, or English remains incomplete;
- `translated`: source-anchored English passes catalog, source, and structural
  build checks;
- `reviewed`: Japanese, scene context, and English received dedicated
  linguistic review;
- `runtime-verified`: the current wording and layout were exercised in game.

Generate the compact speaker-annotated corpus for plot review:

```sh
uv run fermion gm script working/archives > working/script.md
```

Before a register pass, generate deterministic review leads:

```sh
uv run fermion translation drift translations/fermion.toml --only-flagged
```

The drift report compares contraction use, stiff forms, sentence length, and
repeated openings across file/speaker groups. Treat flags as lines to inspect
in Japanese and scene context, not target rates.

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
