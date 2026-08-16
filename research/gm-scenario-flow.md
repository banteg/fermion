# General Message scenario flow

## Result

The scenario graph is directly recoverable from GM bytecode. Opcode `0x6d`
replaces the current MES scenario, while `0x6f` calls a nested MES and restores
the caller afterward. Every one of the 168 such instructions across the 77
content-unique files begins with parameter token `0x11` and a literal ASCII
filename; none uses a computed or indirect target.

The packaged extractor records the instruction offset, load kind, and target:

```sh
uv run fermion gm transitions working/archives
uv run fermion gm transitions working/archives --format tsv
uv run fermion gm transitions working/archives \
  --format dot \
  > working/scenario-graph.dot
```

The DOT view retains parallel and cyclic edges. Those cycles matter: dispatcher
scripts such as `F_SHENE.MES` and `F0034.MES` route into several branches and
receive control from them again, so the corpus does not have one honest total
execution order.

## Story boundary

Reachability from `FOP.MES`, with `MAIN.MES` treated as a terminal return to the
title system, selects 72 content-unique story files. The four other unique MES
files are utility or non-story surfaces:

- `F_E.MES`: CG-gallery/index surface;
- `MONO.MES`: customizable adult-term editor;
- `NAME.MES`: customizable-name editor;
- `SILK.MES`: Silky's software catalog.

`fermion gm script --story` uses that boundary. It emits `FOP.MES` first and
then stable filename order, while the transition graph supplies the branch
structure that filename order cannot express. This is a plot-review view, not
a claim that every branch executes in that order.

## Branch topology

The principal L/R branches and rejoins are explicit in the graph:

- `F0009` selects `F0010L` or `F0010R`. The left path continues through
  `F0011L` and `F0012L`; both paths rejoin at `F0013`.
- `F0021` selects `F0022L` or `F0022R`. The left path includes `F0023L`;
  both paths rejoin at `F0024`.
- `F0024` selects `F0025L` or `F0025R`, followed by the matching `F0026L` or
  `F0026R`; both paths rejoin at `F0027`.

The vent/facility section is a graph rather than a linear chapter. `F0033`
enters the `F0034` dispatcher, which can load 22 `F003400*`/`F00340*`/`F00341*`
state nodes. Most nodes return to `F0034`. Progression paths also pass through
`F003404`, `F0034101`, `F0037`, and `F003701`; the last can return to `F0037`
or advance to `F0038`. Exact offsets remain in the generated graph, avoiding a
hand-maintained route description as those states are annotated.

## Translation inventory

The story boundary contains 16,994 decoded mode-1 text records. Grouping exact
`(mode, proven speaker, Japanese)` values produces 12,841 translation
candidates:

| Initial state | Candidate groups |
|---|---:|
| speaker unresolved | 6,625 |
| unique speaker/text pending | 5,773 |
| known speaker but context review required | 443 |

There are 755 multi-anchor candidate groups covering 4,908 records, and 95
groups whose exact Japanese also appears under another speaker. These are
candidates, not automatic editorial merges: repeated text may still need
different English in different scenes.

Generate the review queue without modifying the checked-in catalog:

```sh
uv run fermion gm inventory working/archives \
  --story \
  > working/story-inventory.tsv
```

Each row has a stable content-derived ID, all unique-file anchors, proven
speaker and attribution source, original text, blank English and context cells,
an initial status, and review flags. The source catalog remains authoritative;
an inventory group should be promoted only after its scene context is reviewed,
and split when one shared source string needs different translations.
