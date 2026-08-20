# Translation catalog

`fermion.toml` is the checked-in source of truth for Fermion's translated text
and the reasoning behind it. It intentionally contains text and metadata, not
compiled MES files or original game media.

The English version carries this editorial note:

> The original Japanese work assigns younger ages or school status to some
> characters. For this English version, every character depicted in sexual
> content is treated as 18 or older. This is an editorial change to the English
> version, not a claim about the original text.

Each `[[files]]` table identifies one pristine MES file by its logical
`DISKA/FILENAME` archive path, extracted source path, SHA-256, and optional
default dialogue `box_width`. Schema 5 retains schema-4 simple records; each
`[[entries]]` table records:

- a stable, descriptive `id`;
- one or more pristine text-opcode anchors and their shared source mode;
- the exact original Japanese and current English translation;
- an explicit stable `speaker` and short scene `context`;
- the target encoding mode and optional per-entry dialogue-box-width override;
- a progress `status` and optional free-form translator `notes`.

Offsets always refer to the pristine file named by the enclosing catalog, not a
rebuilt or relocated MES. `notes` are for line-specific alternatives,
ambiguities, tone decisions, technical compromises, and anything worth
revisiting. Omit them when the speaker/context fields and the checked-in voice
brief fully explain the translation; do not repeat a slice-wide voice policy on
every line. Do not erase an unresolved nuance merely because the current probe
uses shorter wording.

`context` and `notes` describe the Japanese source scene rather than restating
the English release's adult-age framing on every record. Use **adult** only
where the plot itself requires the distinction, such as adult Kaori versus her
younger self; the single editorial note above is the authoritative disclosure.

Draft canonical English by reading the Japanese in scene context and applying
the checked-in plot, voice, and terminology notes. Automated tools may expose
anchors, duplicates, speakers, length problems, and runtime regressions; they
must not manufacture the catalog prose as a substitute for translation.

The catalog stores readable, unwrapped English. At build time the file default
width inserts newlines only at word boundaries, preserving explicit authoring
newlines; a narrower entry override wins when a specific display requires it.
Validation rejects an unbreakable word longer than its effective width.

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

Catalog schemas 4 and 5 make speaker and context mandatory. Source verification
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

Schema 5 represents rendered messages as ordered physical text segments
separated by immutable interpolation segments. A physical record containing
only `】...` is therefore no longer presented as a complete display line. The
checked-in TOML remains canonical; a merged translator table or database is
only a generated view, and any future import must be validated.

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

`[[tokens]]` records the Japanese default, ASCII authoring default, maximum
display width, four tested editor presets, and any reset initializer to patch
after decompilation. Runtime name and term slots are rendered by GM's mode-1
indirect-text opcode, so the builder stores the ASCII choices as full-width
CP932 glyphs while leaving their catalog spelling readable. Name slots are 14
bytes and therefore fit at most six such characters plus a terminator; Lime
Juice can relocate a longer initializer instruction, but it does not enlarge
the fixed runtime slot. `max_width` counts the resulting display columns, not
ASCII bytes.
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
max_width = 12
presets = ["Kanako", "Kana", "Sarah", "Emma"]
initializers = [
  { file = "DISKA/MAIN.MES", offset = 0x18ea, slot = 0x0404 },
]

[[composites]]
id = "example-name-line"
target_mode = 2
source = "【⟦name:dear-person⟧】「こんにちは。」"
translation = "[⟦name:dear-person⟧] \"Hello.\""
speaker = "name-slot:dear-person"
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

The current statuses are:

- `draft`: recorded but not yet exercised in the game;
- `runtime-proof`: renderer or control-flow proof whose wording is still
  provisional;
- `qa-ready`: source and context review are complete and the story slice builds
  into a fresh, structurally audited image. A representative automated route is
  required once a valid scenario fixture exists; a human playtest still
  exercises every line and can send it back for editorial revision;
- `runtime-verified`: the current wording and layout have been exercised in the
  game. This is not necessarily final editorial approval.

The current catalog contains 13,003 canonical records covering 17,680 physical
anchors across 76 MES files: `MAIN.MES`, `FOP.MES`, the translated story
through the `F0042.MES` ending, scene replay, both mirrored editors, and the
period Silky's catalog.
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

The first closed scope is `opening-prologue`: all 118 physical text records in
`FOP.MES`, from the bedside scene through the 2296 premise screen. Ninety-seven
records are translated, 21 unchanged title/layout records are explicitly
excluded, and none are pending. They represent 74 canonical source lines, with
duplicate timing records merged only when their target and context agree.

The second closed scope is `project-d-launch-and-first-arrival`: all 462
physical text records in `F0001.MES` and `F0002.MES`, from Connie's launch-day
wait through her collapse after reaching 1996. All 462 anchors are translated
as 454 managed canonical lines, eight exact contextual duplicates are shared,
and none are excluded or pending.

The third closed scope is `departure-eve-with-kanzaki`: all 398 physical text
records in `F0000.MES`, from the launch-eve scene with Dr. Kanzaki through the
Marna rescue flashback and the next-day handoff to `F0001.MES`. They are
managed as 391 canonical lines; five exact duplicates share wording across
reconverging menu branches, and two contentless pause records join
pre-existing canonical entries from later files. None are excluded or pending.
The slice contains the game's first explicit scene; its translation follows
the disclosed adult-age release policy. F0000 was retranslated line by line
after review found euphemized sexual meaning, mechanical terminology, and prose
that did not match Connie's plain, direct voice. Anatomical wording is now
chosen by sentence rather than forced through a one-word glossary, and the live
`term:slot-1` insertion is rendered in English instead of leaking Japanese. A
`first-scene-save-fixture-proof` route re-pinned to the rebuilt image verifies
the first scene's framebuffer and scenario register; the full scene still
needs a human playtest because no later F0000 fixture exists.

The fourth closed scope is `connie-and-kanako-first-encounter`: all 426 physical
text records in `F0003.MES`, from Connie waking in Kanako's room through their
first bath and the `F0004.MES` handoff. They are managed as 395 canonical
entries, including 34 composite display messages; all 426 anchors are
translated and none are excluded or pending. The image builds and audits
cleanly. No trustworthy live F0003 state exists yet, so the upcoming human
playtest must capture a native fixture before this slice gains automated
framebuffer checkpoints.

The fifth closed scope is `connie-and-kanako-first-intimacy`: all 424 physical
text records in `F0004.MES`, from Connie washing Kanako through their first
sexual encounter, genetic-sample collection, and post-bath confession. They
are managed as 286 catalog entries, including 175 composite display messages;
all anchors are translated and none are excluded or pending.

The sixth closed scope is `connie-explains-her-mission`: all 343 physical text
records in `F0005.MES`, from the post-bath conversation through Connie's
genetic analysis and the plan to meet Kanako's family. They are managed as 225
catalog entries, including 124 composite display messages; all anchors are
translated and none are excluded or pending. The file is stored in `DISKB`,
and the rebuilt image audits both changed archives. No trustworthy live F0005
state exists yet, so this slice remains `qa-ready` pending a human playtest and
native fixture capture.

The seventh closed scope is `connie-meets-kanakos-mother`: all 337 physical
text records in `F0006.MES`, from Kanako's mother returning home through
Connie's introduction, transformation, family reflections, and the dinner
invitation. They are managed as 231 catalog entries, including 96 composite
display messages; all anchors are translated and none are excluded or pending.
This slice activates the live `name:mother` token and reorders the fixed Takano
surname around the editable given name for natural English. No trustworthy live
F0006 state exists yet, so it remains `qa-ready` pending a human playtest and
native fixture capture.

The eighth closed scope is `connie-and-yuki-kitchen-encounter`: all 644
physical text records in `F0007.MES`, from Connie approaching Yuki in the
kitchen through the genetic-sample route and the alternate ear-teasing branch.
They are managed as 426 catalog entries, including 275 composite display
messages; all anchors are translated and none are excluded or pending. The
translation keeps Yuki's warm adult voice distinct from Connie's blunt hunter
calculus, preserves every spoken refusal and the source narration around it,
and carries the Kanzaki scent and reaction clues without resolving them early.
No trustworthy live F0007 state exists yet, so it remains `qa-ready` pending a
human playtest and native fixture capture.

The ninth closed scope is `connie-meets-kanakos-sister`: all 265 physical
text records in `F0008.MES`, from Connie watching Yuki cook through Ruri's
arrival, the transformation proof, the genetic-sample argument, and Kanako
inviting Connie to her room. They are managed as 179 catalog entries,
including 98 composite display messages; all anchors are translated and none
are excluded or pending. Ruri's blunt skeptic voice is kept distinct from
Yuki's warm teasing and Connie's polite first-meeting register. No
trustworthy live F0008 state exists yet, so it remains `qa-ready` pending a
human playtest and native fixture capture.

The tenth closed scope is `first-night-in-the-takano-house`: all 191 physical
text records in `F0009.MES`, from Kanako pulling Connie upstairs through the
room talk, dinner, the pollution briefing, and Connie carrying Kanako to bed.
They are managed as 132 catalog entries, including 72 composite display
messages; all anchors are translated and none are excluded or pending. Kanako
drops Big Sis for bare Connie; the English age lock keeps the sleepy
observation from saying she looks underage. No trustworthy live F0009 state
exists yet, so it remains `qa-ready` pending a human playtest and native
fixture capture.

The eleventh closed scope is `ruri-nighttime-route`: all 215 physical text
records in `F0010L.MES`, from Kanako falling asleep through Connie reconciling
with Ruri, demonstrating Mini form, and changing back. They are managed as 157
catalog entries, including 83 composite display messages; all anchors are
translated and none are excluded or pending. Connie's player-facing age is
about eighteen under the disclosed English-release policy, while her three
years of lived experience remain explicit. No trustworthy live F0010L state
exists yet, so it remains `qa-ready` pending a human playtest and native fixture
capture.

The twelfth closed scope is `yuki-nighttime-route`: all 542 physical text
records in `F0010R.MES`, from Connie returning to the living room through Yuki
taking the lead, their shared-toy scene, and the afterglow. They are managed as
398 catalog entries, including 210 composite display messages; all anchors are
translated and none are excluded or pending. Every spoken refusal, stop, and
limit remains explicit, as do the source's statements about when Connie resists
or gives herself over. No trustworthy live F0010R state exists yet, so it
remains `qa-ready` pending a human playtest and native fixture capture.

The thirteenth closed scope is `ruri-genetic-sample-route`: all 464 physical
text records in `F0011L.MES`, covering the assertive, slow, and talk-first
approaches to Ruri's genetic-sample route. They are managed as 312 catalog
entries, including 203 composite display messages; all anchors are translated
and none are excluded or pending. Ruri's blunt voice remains distinct from
Connie's teasing, while every spoken refusal and attempted resistance remains
explicit even where Connie's narration interprets it differently. No
trustworthy live F0011L state exists yet, so it remains `qa-ready` pending a
human playtest and native fixture capture.

The fourteenth closed scope is `yuki-after-ruri-route`: all 614 physical text
records in `F0012L.MES`, covering Connie's six late-night approaches to Yuki
after the Ruri route and her eventual return to bed. They are managed as 409
catalog entries, including 249 composite display messages; all anchors are
translated and none are excluded or pending. The translation preserves Yuki's
warm, observant voice and the early clue that her gestures and scent resemble
Dr. Kanzaki, without resolving that clue. Every request to be put down,
refusal, withdrawal, and act of resistance remains explicit, including where
Connie overrides it; Yuki's later request and assent remain separate records.
No trustworthy live F0012L state exists yet, so it remains `qa-ready` pending
a human playtest and native fixture capture.

The fifteenth closed scope is `first-return-to-2296`: all 253 physical text
records in `F0013.MES` and `F0014.MES`, from Connie's first-stay departure
through her reunion with Dr. Kanzaki at the 2296 time port. They are managed as
219 catalog entries, including 24 composite display messages and 13
context-safe duplicate pairs shared across equivalent menu branches; all
anchors are translated and none are excluded or pending. Connie's clean-air,
school, and conservation reflections retain her direct, slightly comic voice,
while the reunion shifts Dr. Kanzaki from unguarded private concern back to
professional control as the staff arrives. No trustworthy live F0013/F0014
state exists yet, so the scope remains `qa-ready` pending a human playtest and
native fixture capture.

The sixteenth closed scope is `second-expedition-and-route-reunion`: all 917
physical text records in `F0015.MES` through `F0017.MES`, from Connie and
Remia's attempted two-machine departure through Connie's second arrival, the
Takano family's recruitment plan, and the route-dependent reunion. They are
managed as 681 canonical records, including 287 composite display messages and
13 context-safe duplicate pairs shared across equivalent branches; all anchors
are translated and none are excluded or pending. The launch sequence keeps
machine vibration hardware distinct from the surrounding space-time
oscillation. The reunion keeps the loved one's initiation and later assent
separate from every spoken refusal and head-shake, including the places where
Connie continues. No trustworthy live F0015-F0017 state exists yet, so the
scope remains `qa-ready` pending a human playtest and native fixture capture.

The seventeenth closed scope is `nanase-recruitment-and-genetic-sample`: all
922 physical text records in `F0018.MES` through `F0020.MES`, from Nanase's
arrival through Connie's recruitment request, the genetic-sample encounter,
and its aftermath. Its 678 canonical source lines are all managed; all anchors
are translated and none are excluded or pending. The English preserves the
women's affirmative participation separately from every refusal and
physical resistance. No trustworthy live F0018-F0020 state exists yet, so the
scope remains `qa-ready` pending a human playtest and native fixture capture.

The eighteenth closed scope is `school-visit-and-student-routes`: all 3,982
physical text records in `F0021.MES` through both `F0026L/R.MES` branches. They
contain 2,858 managed canonical source lines; all anchors are translated and
none are excluded or pending. The slice covers the family bath branches, the
one-day school visit, Yoshimi's confession route, and Yoko's swimming-club
route. Every spoken refusal, request to stop or let go, attempt to withdraw,
physical restraint, and unconsented sample collection remains explicit. The
disclosed adult-age policy applies to every character depicted sexually, while
the archival context continues to document the source's school status. No
trustworthy live F0021-F0026 state exists yet, so the scope remains `qa-ready`
pending a human playtest and native fixture capture.

The nineteenth closed scope is `kanzaki-homecoming-and-apparent-betrayal`: all
1,782 physical text records in `F0027.MES` through `F0033.MES`, from Dr.
Kanzaki's arrival at the Takano home through the disappearance, altered return
coordinates, Connie's capture, the apparent betrayal, and the first duct-escape
plan. They contain 1,409 managed canonical source lines; all anchors are
translated and none are excluded or pending. The catalog contributes 1,337
records after context-safe duplicate consolidation. Reveal clues remain
unexplained at first presentation,
while the abduction, capture drug, reproductive-experiment threat, and lobotomy
threat stay explicit. The disclosed adult-age policy applies to all sexual
material. No trustworthy live F0027-F0033 state exists yet, so the scope
remains `qa-ready` pending a human playtest and native fixture capture.

The twentieth closed scope is `facility-scouting-and-escape`: all 2,367
physical text records in the 26 text-bearing files reached through the F0034
facility graph and the return in `F0038.MES`. They contain 1,956 managed
canonical source lines; all anchors are translated and none are excluded or
pending. The catalog contributes 2,033 records after context-safe duplicate
consolidation. `F0034.MES` and `F0037.MES` themselves contain control flow but
no text records, so the scope names their text-bearing descendants explicitly.
The translation preserves the fake-collar clues, fuel and wheelchair planning,
the threatened lobotomy and reproductive exploitation, the patient's
drugged abduction, and the medical confirmation after the escape. Across the
Marna branches, every spoken refusal, request not to continue, head
shake, physical withdrawal, and restraint remains distinct from later assent
or participation. No trustworthy live facility state exists yet, so the scope
remains `qa-ready` pending a human playtest and native fixture capture.

The twenty-first closed scope is `future-self-reveal-and-farewell`: all 1,287
physical text records in `F0039.MES` through `F0042.MES`. They contain 978
managed canonical source lines; all anchors are translated and none are
excluded or pending. The catalog contributes 935 records after context-safe
duplicate consolidation. The slice preserves the four-hour time-slip clue,
the reveal that Dr. Kanzaki is the patient's future self, the concealed
cryosleep chronology, Dr. Marie's coercion and reproductive threat,
Marna's intervention, and the choice to disclose both doctors' conduct after
returning to 2296. The final departure, genetic-repair epilogue, and
undeliverable letter remain one continuous ending. No trustworthy live ending
state exists yet, so the scope remains `qa-ready` pending a human playtest and
native fixture capture.

The final closed scope is `replay-editors-and-period-catalog`: all 716 physical
text records in `F_SHENE.MES`, both mirrored copies of `NAME.MES` and
`MONO.MES`, and `SILK.MES`. They contain 238 canonical source lines; all
anchors are translated and none are excluded or pending. The catalog
contributes 430 records after sharing byte-identical editor copies and
context-safe duplicates. Scene replay has 44 logical titles across 50 physical
anchors, the name and adult-term editors expose four English presets per role,
and all 176 records in Silky's period product catalog are translated. The
localized editor branch and full-width Latin runtime values have been exercised
in the emulator; story, final-letter, and unlocked replay contexts still need a
human playtest with every preset.

The broader `boot-to-first-scene-menu` scope is now closed. It contains 178
physical anchors and 120 canonical source lines: 152 anchors are translated,
and 26 already-final FERMION/DOS glyphs or terminal-layout records are
explicitly excluded. Exclusions are scope-local, so the FOP title and layout
records are anchored independently in this scope and in `opening-prologue`.
Use `--require-complete` for closed scopes; deliberate non-translations belong
in `[[scopes.exclusions]]` with exact source anchors and a non-empty reason.

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

Run the corresponding gate for the next slice with:

```sh
uv run fermion translation coverage \
  translations/fermion.toml \
  translations/coverage.toml \
  working/archives \
  --scope project-d-launch-and-first-arrival \
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
