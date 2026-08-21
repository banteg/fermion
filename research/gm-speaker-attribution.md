# General Message speaker attribution

## Result

Fermion does not attach a hidden speaker ID to every dialogue instruction.
Speaker identity is encoded in the rendered text stream in two forms:

1. Most named dialogue starts with a literal `【name】` inside opcode `0x4a`.
2. A customizable name is assembled from two `0x4a` fragments around an
   opcode `0x45` string copy and an opcode `0x4b` indirect render.

Text without either form has no mechanically recoverable speaker identity.
In particular, alternating quote styles are presentation, not speaker IDs. The
attribution tool therefore leaves such records unresolved instead of carrying
a speaker across message boundaries or guessing from punctuation.

## Literal labels

A static speaker is part of the decoded text itself:

```text
0x4a  【コニー】「……」
0x4a  【神崎】「……」
```

At the GM evidence layer, the source-local speaker ID is the exact string
between `【` and `】`. If one rendered message is split across multiple `0x4a`
records, the label applies to the later fragments until opcode `0x50` or `0x00`
ends that message. The translation catalog maps that evidence to a canonical
identity separately, so `コニー` and a contextual Connie assignment both use
`speaker = "connie"` without losing how the conclusion was reached.

## Customizable names

The five names editable from the title menu cannot be compiled into literal
labels. Their recurring instruction sequence is:

```text
0x4a  "【"
0x45  0e e0 00 ff 0c <name-slot-le16> 00
0x4b  0e e0 00 00 00
0x4a  "】……"
```

Opcode `0x45` copies the selected NUL-terminated name into scratch reference
`0x00e0`. Opcode `0x4b` renders the string at that reference through the same
text path used by `0x4a`. The destination, render reference, surrounding bracket
fragments, and source slot are all checked before an attribution is accepted.

`NAME.MES` supplies the roles shown in the editor, while `MAIN.MES` supplies the
default strings:

| Slot | Stable speaker ID | Default | Editor role |
|---:|---|---|---|
| `0x03e8` | `name-slot:mother` | 由貴 | `(お母さん)` (mother) |
| `0x03f6` | `name-slot:older-sister` | 瑠璃 | `(お姉さん)` (older sister) |
| `0x0404` | `name-slot:dear-person` | 加奈子 | `(あたしの大切な人)` (my dear person) |
| `0x0412` | `name-slot:friend-1` | 陽子 | `(お友達１)` (friend 1) |
| `0x0420` | `name-slot:friend-2` | 弘子 | `(お友達２)` (friend 2) |

The stable role is authoritative for translation voice; the displayed name is
player-editable and the default is retained only as useful review context.

## Native confirmation

The relocation-aware Ghidra project confirms the bytecode interpretation:

- `mes_op_45` at `1000:ace7` copies a NUL-terminated string;
- `mes_op_4b` at `1000:2529` resolves an indirect string, builds a local text
  buffer, and calls `mes_op_4a`;
- helper `FUN_1000_a5c7` resolves the reference operands used by both handlers.

This also explains why treating `0x45` or `0x4b` alone as a general speaker
opcode would be unsafe: they are string operations. Speaker meaning comes from
their exact position between the two bracket-rendering records.

## Unlabelled dialogue

The opening exchange in `FOP.MES` demonstrates the limit. Its first three lines
alternate directly as:

```text
0x4a <doctor line>  0x50 0x00
0x4a <reply>        0x50 0x00
0x4a <doctor line>  0x50 0x00
```

There is no intervening speaker-state command. `「…」` and `『…』` help a human
follow the exchange but do not encode identities. The catalog may record
contextual roles such as `prologue-doctor`; source verification enforces only
identities actually proven by the bytecode.

## Corpus result and tooling

Across the 77 unique MES files (96 physical copies), all 17,461 decoded text
records classify as:

| Attribution | Records |
|---|---:|
| literal `【name】` | 5,156 |
| customizable name slot | 4,206 |
| unresolved/contextual | 8,099 |

There are 2,036 partial `【` prefix records in the corpus. Every one matches the
complete customizable-name sequence above; none is left as an unexplained
partial prefix.

The inverse shape matters for translator tooling. No decoded record contains a
literal blank `【】` or `【 】` label, while 2,037 records begin with an orphaned
`】`. Of those, 2,036 follow the standalone `【` sequence above. The extra case
is `[F0003:0c1c]`, whose longer text fragment ends in `【` before the same copy
and render opcodes; `[F0003:0c4d]` then begins `】。」`. A physical-record dump
therefore exposes naked closing brackets even though the rendered message is
complete.

That closing-bracket census is only a lower bound. The 72-file story graph has
5,124 name-slot renders and 12 customizable-term renders in total, including
many unbracketed mid-sentence insertions. A translator-facing composite view
must reconstruct those messages without erasing the individual text anchors or
the intervening bytecode.

Use `fermion gm speakers` to inspect the source evidence. `fermion translation
table` emits the catalog as the translator-facing `id, file, offset, speaker,
attribution, scene, jp, en, context, status` table. Canonical catalog schema 7 requires
a lowercase speaker ID plus `attribution = "proven" | "inferred"`. Source
verification checks every `proven` identity against its encoded literal label
or name-slot role; contextual assignments remain explicit rather than being
disguised as a different spelling. Bracketed Silky product headings are a
notable semantic exception to the mechanical GM scanner: their catalog speaker
is inferred `catalog-copy`, not the most recently displayed product title.
`fermion gm script` produces a compact, content-deduplicated,
speaker-annotated mode-1 corpus for holistic plot review.
