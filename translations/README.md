# Editing the translation

[fermion.toml](fermion.toml) holds the English translation alongside its Japanese
source, scene context, and review notes. Make text changes here; generated
scripts, review tables, and disk images are outputs of this catalog.

Read the [translation brief](../research/fermion_translation_brief.md) for
character voices, terminology, and archival policy before changing the English.
It contains full spoilers. The policy applies to the released translation too;
release preparation is not a separate rewrite.

## A typical edit

1. Find the entry and read its Japanese in scene context.
2. Revise the English, keeping the entry ID and source references intact.
3. Add a note if the decision depends on an ambiguity or a technical compromise.
4. Validate against the original files, build a fresh image, and check the
   affected scene in game. Commands are in [Development](../DEVELOPMENT.md).
5. Set the review status to match the work actually done.

Automated checks help with source references, repeated text, and layout. They
cannot decide whether a translation gets the scene right.

## How the catalog is organized

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
12 of the translation brief, including the original spelling `Dimention`.

## Text layout

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

## Repeated lines and speakers

An anchor identifies an occurrence in an unchanged original MES file.
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

## Names and terms inside dialogue

Some messages are split into several text records because the game inserts a
player-chosen name or term between them. A composite entry lets you read and
translate the whole message together while keeping those original pieces.
Write the insertion points with these tokens; their brackets deliberately fall
outside the game’s CP932 character encoding:

```text
⟦name:mother⟧
⟦name:older-sister⟧
⟦name:dear-person⟧
⟦name:friend-1⟧
⟦name:friend-2⟧
⟦term:slot-1⟧
⟦term:slot-2⟧
```

Keep every token in its original order, including repeated tokens. The build
puts each English segment back in the corresponding source record and leaves
the name or term insertion instructions intact. Validation:

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

`fermion gm script` dumps the speaker-annotated corpus for plot review.
`fermion translation drift --only-flagged` produces register-review leads;
treat flags as lines to inspect in Japanese and scene context, not target
rates. Commands are in [`../DEVELOPMENT.md`](../DEVELOPMENT.md).

## Checking coverage

[coverage.toml](coverage.toml) lists the parts of the original scripts that the
translation must account for. This lets us find missing lines even when they
have no catalog entry yet. Every decoded text opcode in a range is classified
as translated, explicitly excluded with a reason, or pending. Pending records
are grouped by exact `(source_mode, source)` so a duplicate Japanese line
appears once with all of its physical anchors. Gate a closed scope with
`--scope` and `--require-complete`.

## Building and reviewing changes

Fresh translated images seed the source-derived English names and adult terms
into the persistent `REG_00` template bank. The build only migrates slots that
still contain their Japanese source defaults (or are blank), so rebuilding from
an image with player-customized values does not overwrite those choices.

`translation check` validates structure and encodability. With `--source-dir`
it also verifies every file hash and every source offset, mode, and Japanese
string. `translation table` exports the reviewable TSV: `id`, `file`,
`offset`, `speaker`, `attribution`, `scene`, `jp`, `en`, `context`, and
`status`. It expands canonical multi-anchor entries to one physical row but
does not duplicate their English or notes in the source catalog.

When an affected scene can be reached automatically, add or update its route in
`runtime/routes.toml`. Mark an entry `runtime-verified` only after checking its
current wording and layout in game.

The build writes only ignored artifacts. It compiles each line through
lime-juice, verifies unchanged text and external MLL targets, repacks the
containing installer archive, and updates the copied HDI's FAT filesystem. MES
and archive files no longer need to preserve their original total sizes.
Build, coverage, and runtime commands are in
[`../DEVELOPMENT.md`](../DEVELOPMENT.md).
