# Fermion preservation and translation plan

## Goal

Produce a reproducible English translation workflow for the legally obtained
PC-98 release of *Fermion: Mirai kara no Houmonsha*. Distribute only tooling,
metadata, and binary differences; never commit original game data.

## Confirmed state

The original AI5 compatibility hypothesis was wrong. Fermion uses:

> General Message system-1 Rev.95:06:30 for PC-98xx

Its MES container resembles AI5, but its bytecode is incompatible with the AI5,
AI1, and ADV parsers in lime-juice.

Completed work:

- Preservation images can be materialized and hash-verified.
- FAT12 disks and Silky's installer archives can be listed and extracted.
- EXEPACK-compressed `SIL.EXE` has been unpacked for analysis.
- The DOS MZ load image and entry offset can be extracted reproducibly.
- A relocation-aware Ghidra project recovers substantially more 16-bit code
  than treating the executable as a raw binary.
- The General Message dispatcher and translation-critical text command are
  understood.
- A native-derived structural walker consumes every extracted MES instruction
  and validates address operands through the packaged `fermion gm audit`
  command.
- lime-juice has a GM engine with auto-detection, editable text, lossless raw
  fallback, local-target relocation, documentation, and synthetic tests.
- Every currently extracted Fermion MES file auto-detects as GM and performs a
  byte-exact no-op decompile/recompile round trip.
- A corpus-wide changed-length stress test grows all 26,293 mode-1 text records
  across the 96 on-disk MES copies. The rebuilt files remain structurally valid,
  all 17,044 local targets still land on instruction boundaries, and all 5,971
  external MLL target values remain unchanged.
- The packaged CLI can enumerate structurally decoded text records and replace
  one unique, same-sized file blob in a copied binary image without modifying
  the source media.
- Text extraction expands GM dictionary tokens, raw Shift-JIS, newlines, and the
  PC-98 box-drawing range. It decodes all 26,323 text records across the 96-file
  corpus and supports direct substring filtering.
- Speaker attribution now recognizes both literal `【name】` labels and the
  exact `0x45` copy plus `0x4b` render sequence used by all five customizable
  names. It leaves genuinely unlabelled dialogue unresolved instead of guessing
  from quote style.
- A compact full-script export deduplicates identical MES copies by content,
  retains stable offsets, and annotates every proven speaker for holistic plot
  review and translator-note drafting without treating generated output as the
  catalog source of truth.
- All 168 scenario transfers have literal filenames. A transition graph and
  `FOP.MES`-rooted story view isolate 72 story scripts, while a stable candidate
  inventory groups exact speaker/text pairs and flags unsafe contextual merges.
- A checked-in translation catalog retains stable pristine-source anchors,
  canonical one-to-many translations, original lines, speaker, context,
  wrapping constraints, progress status, and translator notes. The CLI verifies
  its file hashes, every exact physical text record, and every encoded speaker;
  it can also emit the original translator-table layout as TSV or JSONL.
- A checked-in coverage ledger enumerates complete story ranges independently
  of the translated entries, groups duplicate source lines, and reports every
  anchor as translated, explicitly excluded, or pending.
- Named headless routes can drive a writable copy of one translated HDI, capture
  several frames in a single run, reject content or framebuffer hash drift, and
  restore hash-keyed prefix state plus its matching disk snapshot.
- Sparse, checked-in save fixtures can be captured from NP2kai states and
  reconstruct a native loadable slot from hash-pinned `REG` banks, allowing
  short scenario-entry routes across rebuilt translation images without
  committing complete game state or disk images.
- The catalog can now build a fresh translated image end to end: lime-juice
  recompiles changed-length GM files, Silky's archive offsets are repacked, and
  the copied HDI's nested FAT12 file is safely resized and verified.
- The first major translation slice, all of `FOP.MES`, is QA-ready. Its focused
  ledger closes all 118 physical text records as 97 translated and 21 explicit
  title/layout exclusions, with zero pending records. A fresh image passes the
  canonical 34,200-frame route through the bedside scene, Marie's coercion of
  Kanzaki, the naturalized Project D terminal, the centered 2296 premise, and
  the first following scene.
- A chronology audit corrected the next-story priority: `FOP.MES` transfers to
  `F0000.MES`, and `F0000.MES` does not hand off to `F0001.MES` until after its
  complete departure-eve scene. The `departure-eve-with-kanzaki` ledger is now
  closed: all 398 physical text records in `F0000.MES` are translated as 391
  canonical lines with zero pending, including the explicit launch-eve scene
  and the Marna rescue flashback. A line-by-line editorial redo removed
  euphemized meaning and out-of-character purple prose, while a composite now
  keeps the live adult-term insertion in English. The `first-scene-save-fixture-proof`
  route is re-pinned to and green against the rebuilt fixture image. A human
  playtest remains the editorial gate because no later F0000 fixture exists.
- The second major slice, all of `F0001.MES` and `F0002.MES`, is QA-ready. Its
  ledger closes 462 physical records as 454 canonical translations with eight
  context-safe duplicate collapses and zero pending records. A native-load
  route verifies the opening F0001 dialogue and compile-time word wrapping;
  complete human playthrough remains the editorial gate for the slice.

The structural audit covers 96 on-disk MES copies representing 77 unique
SHA-256 hashes: 130,119 instructions and 23,015 address operands when duplicate
copies are included. All 17,044 in-file targets land on decoded instruction
boundaries; the remaining 5,971 operands are external MLL call addresses.

Relevant commits:

- Fermion `56e4bf7`: preservation and MES probing tools.
- Fermion `145ecd1`: MZ load-image extraction.
- Fermion `4c91a23`: native-derived General Message structural audit.
- Fermion `1825cd5`: compact, content-deduplicated full-script dump.
- lime-juice `acad05d`: General Message text support, on branch
  `feat/fermion-general-message`.
- lime-juice `86a0f68`: General Message source-span relocation and backpatching.
- lime-juice `4b54a8c`: mode-2 GM newline round-trip support.

## Confirmed General Message format

### Container

- The first little-endian word is the absolute code start within the MES file.
- Bytes from offset 2 to the code start are two-byte Shift-JIS dictionary entries.
- Runtime `BP` is initialized from that first word, so local jump targets are MES
  file offsets rather than offsets relative to the code section.

### Dispatcher

- Opcodes span `0x30` through `0x7f`.
- `0x00` ends the current interpreter invocation.
- The dispatch table contains 80 entries at executable load offset `0x1cbc`.

### Control-flow operands

- `0x31` and `0x32` contain a loop ID followed by one local target.
- `0x33`, `0x34`, and `0x35` contain one local target.
- `0x39`, `0x3f`, and `0x40` contain a local fallthrough target followed by a
  call target; the call can address either the current MES or the loaded MLL.
- Inline-data form `0x44` contains a local target that skips its embedded
  string payload. Its reference-to-reference form does not use that word as a
  branch target.
- `0x3a` is a 13-way subdispatch. Subtype 1 builds callback records and subtype
  9 executes the fifth word of a selected record. Fermion's callback words are
  computed expressions/references rather than embedded address literals, so
  they do not add another byte-level relocation in the current corpus.
- `0x6b` and `0x71` are additional expression-selected subdispatches. Their
  native handlers explain the last variable-length layouts in `MONO.MES` and
  `NAME.MES`.

### Text opcode `0x4a`

- The opcode is followed by a mode byte, payload, and zero terminator.
- Mode 1 uses dictionary references, raw two-byte Shift-JIS, and `0x04` newline.
- Tokens `0x18..0x7f` address dictionary entries `0..103`.
- Tokens `0xa0..0xdf` address dictionary entries `104..167`.
- Mode 2 renders printable single-byte text and is already used by the game for
  short UI strings. Across the 77 content-unique files there are 16 mode-2
  records total: ten `BS` backspace labels in `NAME.MES`/`MONO.MES`, four ASCII
  quotation marks, and two spaces. They are editor surfaces, not gallery noise.
  The same `0x04` newline control works in mode 2; lime-juice now round-trips it
  and the translated three-line disclaimer proves it in the live renderer.

### Scenario/module loading

- `0x6d` replaces the current MES scenario.
- `0x6e` loads an MLL module.
- `0x6f` calls a nested MES and restores the caller afterward.
- Parameter token `0x11` introduces a zero-terminated literal string; the
  parameter list ends with another zero.
- `MAIN.MES` begins with `6e 11 "system.mll" 00 00`.

## Completed blocker: upstream address relocation

The GM implementation preserves semantically unknown code in `(raw ...)` nodes,
but now structurally walks every instruction before emitting them. Decompiled
source contains a `gm-layout` map with one original span per code node and every
proven local 16-bit target field. The compiler maps those positions onto the new
output and backpatches local targets after text encoding.

This avoids prematurely inventing a semantic AST for all 80 opcodes. External
MLL addresses are not included in the relocation table, and raw nodes must keep
their original lengths. Generated layout metadata and node order must remain
intact.

## Completed milestone: relocatable GM control flow

### 1. Recover address-bearing instruction layouts — complete

Start with native handlers for opcodes `0x31..0x40`, especially `0x40`, which is
already known to read two little-endian 16-bit addresses before evaluating an
expression. For each handler, record:

- fixed operands consumed directly from `BP`;
- expression or parameter payloads consumed by shared decoders;
- which words are local MES targets, MLL addresses, data offsets, or counts;
- fall-through and stack behavior.

The layouts are validated across all 77 unique MES files. Every proposed local
target is an instruction boundary and every out-of-file call target falls in
the loaded MLL address range.

### 2. Recover shared variable-length encodings — complete

The walker covers literals, references with nested index expressions, operators,
random ranges, string parameters, reference parameters, composite assignments,
and the `0x3a`, `0x6b`, and `0x71` subdispatches. Expression semantics can remain
raw initially because their byte boundaries are now deterministic.

### 3. Add source mapping and backpatching to lime-juice — complete

The least-resistance implementation retains raw instructions and emits stable
source spans instead of exposing labels in the user-facing AST. During
decompilation it:

- decodes the complete instruction stream;
- emits only proven `0x4a` instructions as `gm-text`;
- records one source span for each `raw` or `gm-text` node;
- records local targets only when they land on decoded instruction boundaries.

During compilation it:

- computes the new span of every node after dictionary and text encoding;
- remaps each target field and destination through the source spans;
- backpatches local 16-bit targets while preserving external addresses;
- rejects length-changing raw edits, malformed maps, unresolved positions, and
  outputs beyond the 16-bit address space.

The synthetic test covers exact round-trip, a changed-length mode-2 edit, local
target movement, external-target preservation, and rejection of a resized raw
node. Independent corpus validation covers unchanged and aggressively resized
real scripts.

## Completed milestone: prove English rendering in the runtime

### 4. Prove single-byte English rendering — complete

A same-byte-length mode-2 probe is ready in ignored working files. It changes the
two ASCII spaces in `MAIN.MES`'s visible `Ｄ Ｏ Ｓ` main-menu label to `A`, at
MES offsets `0x1644` and `0x164d`. The rebuilt MES is the same 7,310-byte size,
passes the structural audit, and differs at only those two bytes. The copied HDI
likewise differs only at absolute offsets `0x9d8e9` and `0x9d8f2`; the pristine
working HDI retains SHA-256
`533a12e3e160af21a376de9eadde505a2d945d0069543a81131b564df7ddd4d8`.

The 2015 NP2debug launcher currently reaches ROM BASIC because the intended HDI
is not mounted. Its Windows argument parser treats extra positional media as
floppy disks, while `initgetfile()` appends `.ini` to an already suffixed custom
configuration path and therefore looks for `Fermion.ini.ini`. Manual
`Disks -> SASI #0 -> Open` followed by reset bypasses both launcher defects for
this probe; repair the persistent launcher only after the live emulator exits.

The probe boots in NP2debug when mounted manually as SASI #0. The final scrolling
menu entry renders as `ＤAＯAＳ`, proving that mode 2 produces clean Latin glyphs
inside the GM renderer. Each `A` advances by 8 logical pixels, half the 16-pixel
full-width mode-1 cells around it. The mixed-mode highlighted row remains aligned
and unclipped, and its cursor geometry is unchanged. Punctuation behavior and
narrative text wrapping remain to be tested.

## Completed milestone: changed-length runtime relocation

### 5. Build a changed-length title-menu slice — complete

First translate the three visible title-menu labels with deliberately different
encoded lengths. Compensate with shorter translations in hidden labels so the
overall `MAIN.MES` size stays 7,310 bytes. This isolates live relocation behavior
from FAT filesystem growth: targets between the edited nodes must move even
though the final file and HDI sizes remain unchanged.

That probe is ready in ignored working files. The visible labels are `START NEW
GAME` (14 bytes replacing 8), `LOAD` (4 replacing 9), and `CHANGE NAME` (11
replacing 4). Shorter `ART`, `CATALOG`, and `DOS` labels compensate for the net
growth. The rebuilt file remains 7,310 bytes with 941 instructions, 286 address
operands, and zero audit issues. Two of its 190 local targets move forward by six
bytes, while all 96 external MLL targets remain unchanged. The copied HDI differs
from the pristine working image at exactly the 226 bytes changed in `MAIN.MES`.

NP2debug renders all three English labels cleanly with the expected half-width
advance and unchanged selection geometry. Activating `START NEW GAME` reaches the
opening Japanese dialogue, proving the resized menu's relocated control flow is
executable rather than merely structurally valid.

## Completed milestone: first narrative vertical slice

### 6. Translate and test the opening sequence — complete

Locate the first displayed line in its scenario MES, then translate and test:

- one opening line;
- one speaker-labelled exchange;
- one additional command menu;
- one multiline text box;
- one mode-2 string.

The first line is `FOP.MES` offset `0x016c`:
`「見ない方がいいですよ。あなたのお気持ちはわかりますが・・・。」`.
An ignored runtime probe replaces its 34-byte mode-1 payload with the equally
sized mode-2 translation `"Don't look. I understand, but..."`. `FOP.MES`
remains 5,683 bytes with 700 instructions, 154 address operands, all targets
preserved, and zero audit issues. The combined menu-and-opening HDI differs from
the pristine working image at 261 bytes. NP2debug renders the English sentence
on one clean line with working ASCII quotes, apostrophe, comma, and periods;
narrative-box alignment and the continue indicator remain intact.

The next ignored probe expands the following reply from 36 to 62 bytes and
shrinks the response from 39 to 13, leaving `FOP.MES` at 5,683 bytes. It renders
`"No... He's someone very dear to me. Please let me see him..."` followed by
`"This way..."`. The rebuilt script still has 700 instructions, 154 preserved
address operands, and zero audit issues; its copied HDI differs from the pristine
image at 341 bytes.

NP2debug confirms automatic narrative wrapping and normal dialogue advance. The
first 61 half-width characters fill one line; the closing quote, character 62,
wraps alone onto the next line. The renderer therefore wraps at a 61-character
half-width boundary and does not preserve English word boundaries. Advancing
shows `"This way..."` normally, with the text box and continue indicator intact.
Translation tooling must wrap English deliberately instead of relying on the
renderer.

The initial six translated menu/dialogue records and their translator notes live in
`translations/fermion.toml`. Their anchors verify exactly against hash-pinned
pristine `MAIN.MES` and `FOP.MES` files. This keeps editorial decisions and
runtime discoveries reviewable while generated MES and HDI artifacts remain
ignored.

The catalog now also covers the first three lines of `F0000.MES`, whose inline
`【コニー】` and `【神崎】` labels are rendered as `[CONNIE]` and `[KANZAKI]`.
All three English lines fit on one observed 61-character half-width row. The
first in-scene menu at offsets `0x0832`, `0x0848`, and `0x085b` renders as
`LOOK AT DR. KANZAKI`, `LISTEN`, and `GIVE IN`, with its highlight, cursor, and
spacing intact. Literal alternatives and contextual inferences remain recorded
in the translator notes even though these six entries are runtime-verified.

The completed technical slice now contains a translated opening line,
speaker-labelled exchange, title and in-scene command menus, a deliberately
wrapped dialogue box, and mode-2 English. It survives catalog validation,
decompile, edit, compile, archive repacking, filesystem-aware media replacement,
unattended boot, and exact framebuffer checks. Editorial revision and contiguous
translation of the intervening Japanese remain separate ongoing work.

## Completed enabling milestone: self-driving runtime tests

### 7. Build a headless emulator harness — complete

Use the installed native NP2kai libretro core as the first automation target,
rather than porting the legacy Win9x NP2debug GUI. The core exports the standard
libretro load, reset, run, serialize, input, and video callbacks. Its current
source polls `RETRO_DEVICE_KEYBOARD` every frame and supplies the rendered
framebuffer directly to the frontend, which is enough to automate translation
tests without GUI accessibility or OCR.

The packaged `fermion emulator run` command now:

- loads an ignored copied HDI with the existing NP2kai system directory;
- runs a deterministic number of frames and taps PC-98 keys or mouse buttons;
- captures the raw framebuffer to PNG and saves/restores emulator state;
- reports a stable SHA-256 over packed RGB pixels for checkpoint comparisons.

The installed RetroArch core is x86-64 and cannot load into the arm64 `uv`
Python process. A clean arm64 build from upstream NP2kai commit `c023417` works;
the ignored core has SHA-256
`83e4f13371fb919e4ec7ce4ea9b1f7e2643dfb5df0ef561c6444f7c20257d68a`.
The harness uses an ignored copy of the NP2kai system directory so the core's
configuration writes do not touch the RetroArch installation.

The initial unattended 4,500-frame smoke route boots through the information screen,
color-mode selector, disclaimer, title, and translated menu; selects
`START NEW GAME`; displays `"Don't look. I understand, but..."`; and advances to
the deliberately wrapped long reply. Its final 640x400 RGB565 checkpoint has
packed-RGB SHA-256
`16755d4656c6606f82c8ba4fa7c6bffdcd6d1b13765cd5f885a1e602e3e1dc7e`.
Save and restore also work: restoring the 1,200-frame information-screen state,
tapping Return at frame 1, and running 200 frames reproduces the mode-selector
hash `910a14549d5812f2bda9df0ba206c4e2907c03f2a7d21bd0632b79d09f695965`.

Use the relocation-aware Ghidra project for native control-flow and data-format
recovery. Keep NP2debug for manual register, memory, breakpoint, and stepping
work. If those debugger facilities later need automation, patch its Windows
frame loop with a narrow local command channel and no-dialog screenshot path; a
full native port of its Win9x-only debugger UI is not required for the
translation pipeline.

The named route in `runtime/routes.toml` now pins the expanded translated HDI
and drives 34,200 frames through the prologue to the first scene menu. Two new
opening checkpoints verify the canonical duplicate translations: display-mode
selector hash
`8c32d32fbcafc99e370b95f24f0749dc151a7aa4b0de9340867344270b4cc8c6`
and fiction-disclaimer hash
`ba49984ceeb970c4df38422499d447a02df3e81131e49eb63c867e6076db4da3`.
It retains the three earlier opening checkpoints: translated-menu hash
`a736da6478d479150732eae5dcf49481a88d3c99e1bbb0d592590dd5d4b38045`,
opening-warning hash
`69c262007b4640fa1898c158de67566a49b8f289d3626ba750b3079e7137ce05`, and
opening-request hash
`16755d4656c6606f82c8ba4fa7c6bffdcd6d1b13765cd5f885a1e602e3e1dc7e`.
Four further checkpoints verify Connie's first line
`51c0ad3454562352f09ba96293cd422bdc1e36ba9f156e85a75e7fec113ea3e0`,
Kanzaki's reply
`217d9e55ef2f863cffe9d83326acf5df8ab8ecb6571341c0e9031b45ab1bfcd1`,
Connie's response
`f9f447ca09c1e57cd74382cada87ad6aea9e27045718ee3566ca9e90ae0a4c71`,
and the three-choice menu
`1a33b4520663c94af8ac41b438746d40fc0ed06065462ccffcf53cf83dfe5a0c`.

The route cache boundary is frame 26,099, immediately after the last labelled
dialogue proof. A cache miss runs and verifies all nine checkpoints, then saves
both libretro state and the writable HDI at that exact frame. A cache hit starts
at global frame 26,100 and executes only the final 8,100 frames. On this Mac the
measured route fell from about 49 seconds to 11.7 seconds and reproduced the
same final hash. `--no-cache` remains the full end-to-end release gate.

Clock multiplier is part of the emulated machine, not a safe host throttle. A
×4 trial ran 34,200 frames in 15.2 seconds instead of the ×20 profile's full
runtime, but all existing checkpoint hashes and several input landing points
changed. Suppressing rasterization between checkpoints produced no meaningful
speedup because guest CPU emulation dominates. Canonical routes therefore keep
×20 and use state prefixes; any lower-clock route needs separate schedules and
hashes.

## Completed enabling milestone: duplicate-aware coverage

### 8. Track canonical lines and every physical anchor — complete

Catalog schema 4 retains either one compact `file`/`offset` anchor or an
`anchors` array. One translation, status, and translator note can therefore
cover repeated bytecode without copy-pasted editorial state. Identical source
may still be split into multiple entries when scene context truly requires
different English; the coverage report counts such decisions explicitly.

The setup audit proved that the repeated strings are compiled control-flow, not
extractor artifacts. Color and monochrome each occur twice inside the same
six-item machine/disk setup menu. The three disclaimer lines each occur in
three separate initialization branches. Five canonical entries now cover those
13 physical anchors and are runtime-verified.

`translations/coverage.toml` defines the initial
`boot-to-first-scene-menu` range over `MAIN.MES`, `FOP.MES`, and `F0000.MES`.
It currently contains 178 decoded text anchors grouped into 120 exact source
lines. Seventeen canonical entries cover 25 anchors; 103 unique lines across
153 anchors remain pending. Intentional non-translations must be exact,
source-verified exclusions with reasons, and `--require-complete` can close a
scope without relying on a manual checklist.

## Completed enabling milestone: speaker-aware translation records

Static speakers are not stored in a preceding state record: they are literal
`【name】` prefixes inside opcode `0x4a`. Customizable speakers are assembled as
an opening-bracket `0x4a`, an opcode `0x45` copy from a persistent name slot to
scratch reference `0x00e0`, an opcode `0x4b` indirect render, and a closing-
bracket `0x4a`. Ghidra confirms that the native `0x45` handler copies strings
and the `0x4b` handler feeds an indirect string into the `0x4a` renderer.

The five stable roles and defaults are:

- `0x03e8`: `name-slot:mother` (`由貴`);
- `0x03f6`: `name-slot:older-sister` (`瑠璃`);
- `0x0404`: `name-slot:dear-person` (`加奈子`);
- `0x0412`: `name-slot:friend-1` (`陽子`);
- `0x0420`: `name-slot:friend-2` (`弘子`).

Across 77 content-unique MES files, 5,156 of 17,461 decoded text records inherit
a literal label, 4,206 inherit a customizable name slot, and 8,099 remain
contextual. All 2,036 partial opening-bracket records match the complete dynamic
sequence. No record contains a literal blank `【】`/`【 】` label. There are 2,037
records beginning with an orphaned `】`: 2,036 follow a standalone `【`, while
`F0003:0c1c` embeds the opening bracket in a longer fragment before the same
name render. The story graph contains 5,124 name renders in all, so the closing-
bracket census is only a lower bound on messages requiring a composite view.
`FOP.MES` proves the unresolved case: its opening alternates plain `0x4a`
messages separated by `0x50` and `0x00`, with no speaker-state opcode.

Catalog schema 4 therefore requires an explicit stable `speaker` and concise
`context` for every canonical entry. Source verification rejects disagreements
with encoded labels and slots while permitting documented manual roles for
unlabelled lines. `fermion translation table` emits `id`, `file`, `offset`,
`speaker`, `jp`, `en`, `context`, and `status` for translator review. The
byte-level and native evidence is retained in
`research/gm-speaker-attribution.md`.

## Completed enabling milestone: scenario-aware corpus inventory

Opcodes `0x6d` and `0x6f` expose every scenario replacement and nested load.
Across the 77 content-unique scripts, all 168 targets are literal filenames;
there are no computed transition targets in the corpus. `fermion gm
transitions` exports the exact edges as text, TSV, or Graphviz DOT.

Following those edges from `FOP.MES` and treating `MAIN.MES` as the terminal
title return selects 72 story scripts. `F_E.MES`, `MONO.MES`, `NAME.MES`, and
the `SILK.MES` software catalog remain available in the full dump but are
excluded by `fermion gm script --story`. Story output begins with the prologue
and then uses stable scenario-name order; the graph, rather than that linear
view, remains authoritative for branches and cycles.

`fermion gm inventory --story` groups 16,994 decoded records in the unique
corpus into 12,841 exact `(mode, proven speaker, Japanese)` candidates without
modifying the translation catalog. It assigns stable content-derived IDs,
retains every unique-file anchor, and leaves English and context blank. The
initial queue has 6,625 unresolved-speaker groups, 5,773 unique pending groups,
and 443 known-speaker groups requiring context review. Multi-anchor and
speaker-variant flags
make every proposed canonical merge explicit; identical source never becomes
one translation merely because the extractor saw it twice. Full evidence and
commands are retained in `research/gm-scenario-flow.md`.

## Completed enabling milestone: catalog-driven image builds

### 9. Remove the same-total-size constraint — complete

`fermion translation build` now treats `translations/fermion.toml` as the
build input. For every catalog file it:

- verifies the pristine extracted MES hash, original offset, mode, and text;
- decompiles GM through lime-juice and edits the exact text node corresponding
  to the stable pristine offset;
- recompiles with local-target relocation, then checks instruction order,
  unrelated text, external MLL targets, and the complete structural audit;
- rebuilds the containing Silky's archive in its original file order while
  preserving its raw filename fields; and
- locates the PC-98 partition inside the Anex86 HDI, reallocates the nested FAT12
  file's cluster chain, updates both FAT copies and its directory entry, and
  verifies the result without modifying the input image.

The five-file checkpoint build grew `MAIN.MES` from 7,310 to 7,541 bytes,
`FOP.MES` from 5,683 to 6,247 bytes, `F0000.MES` from 16,157 to 16,211 bytes,
`F0001.MES` from 17,509 to 26,040 bytes, `F0002.MES` from 4,402 to 5,964 bytes,
and `DISKA` from 1,090,166 to 1,101,108 bytes. Starting from pristine image
SHA-256
`533a12e3e160af21a376de9eadde505a2d945d0069543a81131b564df7ddd4d8`,
that QA build had SHA-256
`bab370803cd7fe8b63251a1cc126d4f5eca37260a7487d53ff38cffd2eec8232`.
The named routes prove that changed-size media reconstruction preserves live
control flow and rendering through the prologue, F0000, and the translated
opening of F0001.

## Completed enabling milestone: portable save fixtures

### 10. Start runtime tests at scenario boundaries — complete

Relocation-aware Ghidra analysis recovered the native `0x72` through `0x75` and
`0x7e` register handlers. `REG_00` is the persistent global/template bank;
`REG_01` through `REG_10` are ten loadable slots. Opcode `0x74` writes the
current 6,944-byte global segment to the selected slot, while `0x75` reloads a
slot and restarts the scenario named at offset `0x1b10`. Opcode `0x7e` merges a
small progress range into `REG_00`; it is not a user save operation.

`fermion save capture` now recovers that global segment directly from an ignored
NP2kai serialized state. It requires the expected scenario name, ranks candidate
segments by similarity to `REG_00`, rejects embedded unchanged template copies,
and refuses ambiguity unless an explicit state offset is supplied. It emits a
standalone sparse TOML fixture while the complete state and 6,944-byte slot
remain generated and ignored.

Three native fixtures are checked in and validated through the game's actual
`LOAD` menu. They resume the translated `FOP.MES` opening, the first translated
`F0000.MES` scene, and the following `F0001.MES` scene. Relative to the
hash-pinned `REG_00` template, their snapshots change 114 bytes in 40 contiguous
hunks, 110 bytes in 35 hunks, and 114 bytes in 40 hunks respectively.
`runtime/save-fixtures.toml` records only those before/after bytes and hashes.

`fermion save apply` verifies the template and empty target slot, reconstructs
`REG_01`, verifies the fixture's result hash, and writes a new HDI without
touching the input. The FOP and F0000 10,500-frame routes reproduce full
framebuffer hashes
`980c7d275c55077af9c5c66729e9b4f74dfb0f7547217f9ebeff20c4f2976e4c`
and `51c0ad3454562352f09ba96293cd422bdc1e36ba9f156e85a75e7fec113ea3e0`,
while the extended 15,300-frame F0001 route retains the 640x308 room hash
`24f99058f153f312ca3b6fb9a95e77945dae63ded556679b531b488e7f33a9e4`.
It then pins eight translated dialogue frames.
Eight-frame keyboard pulses cross the PC-98 scan without the missed input seen
with two frames or the repeat seen with thirty. Each route also verifies the
visible load operation and the exact scenario marker at serialized-state offset
`0x1c7e0`, so a visually similar fallback path cannot pass. A 10,500-frame
fixture route measured about 15.5 seconds cold and 3.9 seconds from its
exact-build 8,299-frame cache boundary, versus about 49 seconds for the full
prologue route.

The two acceleration layers have distinct roles. Native `REG` fixtures survive
translation-image rebuilds when their pinned banks are unchanged and resume at
scenario entry. Libretro states are core/config/content-specific but resume at
an exact frame within that shorter route. Full end-to-end routes remain the
release gate.

## Completed translation milestone: Project D launch and first arrival

The `project-d-launch-and-first-arrival` scope covers every mode-1 text record
in `F0001.MES` and `F0002.MES`: 367 launch-side anchors and 95 arrival-side
anchors. The 462 physical records are managed as 454 canonical translations;
only eight exact repeats share editorial state, and no context-dependent line
was merged merely because its Japanese matched.

The slice follows Connie through launch preparation, the Project D and Time
Quake exposition, her relationships with Kanzaki, Marie, and Remia, the first
time-machine crossing, the failed arrival in 1996, and the unnamed girl's first
attempt to help her. Every line has an explicit speaker, scene context, status,
and translator note. The English follows the archival voice bible: Connie's
technical competence and private insecurity coexist, Remia stays blunt but
protective, Marie remains coldly clinical, and Kanzaki's public control cracks
only at departure.

Both files declare a 61-column dialogue width. The catalog retains clean prose;
the build inserts deterministic word-boundary newlines, honors explicit
newlines and per-entry overrides, and rejects words that cannot fit. The native
F0001 fixture route now pins the room load plus eight translated dialogue
frames. That run caught and fixed the renderer's former mid-word wrapping of
“specializes” and “authority” before the slice was promoted to `qa-ready`.
The generated QA HDI hash is
`bab370803cd7fe8b63251a1cc126d4f5eca37260a7487d53ff38cffd2eec8232`;
after installing the `second-scene` fixture, the route input hash is
`00466ca99ef05e6e2129c64a48a964aa4616b4b998c8f7d707991a4874248b6d`.
Both images remain ignored build artifacts.

## Completed translation milestone: Connie and Kanako's first encounter

The `connie-and-kanako-first-encounter` scope closes all 426 physical text
records in `F0003.MES`, from Connie waking in Kanako's room through their first
bath and the `F0004.MES` handoff. They are managed as 395 canonical entries:
361 simple entries plus 34 rendered composites. Four context-safe duplicate
groups share editorial state; every other repeated Japanese line remains split
when its speaker or scene function differs. Nothing is excluded or pending.

Schema 5 makes the composite lines buildable without destroying their byte
map. The catalog retains each physical text anchor and immutable `0x45`/`0x4b`
copy/render span, verifies the token sequence and span hash, wraps using the
token's maximum width, and splits each English literal back onto its original
text record. Ruri and Kanako's same-sized reset initializers are localized to
ASCII while remaining tied to their proven persistent runtime slots.

The fresh image grows `F0003.MES` from 16,938 to 25,250 bytes; the rebuilt file
audits with 36 preserved name renders and no control-flow issues. Starting from
pristine image SHA-256
`533a12e3e160af21a376de9eadde505a2d945d0069543a81131b564df7ddd4d8`,
the six-file build produces SHA-256
`61210332f62dd94335a01aee1ec83d376426624fa61ce1d5da23371e22d333b6`.
This is a structurally build-verified, QA-ready slice, not a runtime-verified
one: no trustworthy live F0003 state exists yet. The first human playtest must
capture a native F0003 fixture for subsequent short automated routes.

## QA incident: F0001 post-knock fade

The apparent stall after `F0001.MES:0x3397` ("Even an ordinary knock has a
pattern my ears remember.") is root-caused to a stale NP2debug save state, not
translated GM control flow or emulator speed. The supplied page-fault backtrace
identified NP2debug's word-store path at host `0x41256b`. A conditional runtime
write tracer then caught guest `REP MOVSW` writing `DX=0x010b` through that path
to physical `0x2e800`; the malformed GP4 decode had crossed its circular output
area and begun overwriting the decoder itself.

A guest breakpoint immediately after the eight-byte DOS header read found
`2f 00 01 61 29 c5 39 35`. The requested file was proven through the PSP and
DOS system file table to be `DISKA`. `H001.GP4` starts at archive offset
`0xd38f7` with the valid header `00 08 00 03 01 ff 01 2f`; the stale state read
from `0xd38fe`, exactly seven bytes into the file. Its restored SFT cached
`DISKA` at `0x10edb1` bytes, while the current mounted archive is `0x10edaa`
bytes. Both `np21.S00` and `np21.S01` contain the old length.

A fresh boot of the same HDI reports `0x10edaa` in the live SFT and reaches the
title normally. The rebuilt archive is therefore sound. Loading an opaque
NP2debug state from a previous image restored stale DOS file metadata and a
cursor that no longer addressed the same byte. `fermion save
check-np2debug-state` now rejects this known size mismatch before manual QA.
A matching size is not a content fingerprint, so all NP2debug slots must still
be recreated after any image rebuild. Sparse game-native `REG` fixtures remain
the portable checkpoint format; exact NP2kai/NP2debug states remain paired with
their original image. The ignored proof bundle is retained under
`working/np2debug-fade-diagnosis/`.

NP2debug's generated `Fermion.ini.ini` also drifted to `ExMemory=1` even though
the intended `Fermion.ini` specifies 13 MB. This was not causal, but manual QA
should still use 13 MB so it matches the supported profile.

## Locked translation and release contract

- `translations/fermion.toml` is the only canonical translation source. TSV,
  JSONL, CSV, SQLite, or other translator databases are generated views; any
  future import path must validate back into TOML. No parallel editorial
  database is allowed.
- The working and initial release target is a source-faithful English
  translation with one disclosed editorial change: every character depicted in
  sexual content is treated as 18 or older. The English release notes state that
  this changes the localization rather than the original Japanese work. A
  parallel edited layer is not maintained, and a story-focused rewrite remains
  out of scope.
- Composite authoring uses non-CP932 metadata tokens such as
  `⟦name:dear-person⟧` and `⟦term:slot-1⟧`. Schema 5 retains each physical
  text anchor and immutable copy/render span, validates the exact token sequence,
  split merged English deterministically back into the original text records,
  and reject token leakage before lime-juice.
- Punctuation can be compressed within a record, but records are never merged
  or deleted for prose flow. Silent records remain independently anchored
  because they may carry branch, CG, SFX, or pacing semantics.
- Honorific suffixes are omitted and expressed through English syntax, titles,
  and kinship. The opening terminal is naturalized. `F0040.MES:0x40c8` renders
  the inconsistent “about 280 years” as “nearly three hundred years” and logs
  that restoration intervention.
- The archival English build retains the name and adult-term systems as tested
  preset selectors. It does not accept unrestricted Latin input or remove the
  features; every preset must pass slot, grammar, gallery/replay, and story QA.

## Tooling conventions and gates

- Python tooling uses `uv` and the packaged `fermion` entry point.
- Keep generated, derived, and copyrighted artifacts under ignored `working/`.
- Preserve pristine source hashes and work only on copies.
- Synthetic tests contain no game data.
- Require byte-exact no-op round trips for every supported original MES file.
- Require explicit changed-length control-flow tests before claiming translation
  safety.
- Keep Fermion and lime-juice changes in conventional commits.

## Later work

- Playtest the complete `departure-eve-with-kanzaki` slice and capture native
  fixtures past the first scene so the rest of F0000 gains automated
  framebuffer checkpoints.
- Add validated import for the generated translator views. Schema 5 composite
  occurrences, immutable name/term segments, and strict token validation are
  complete; TOML remains the sole canonical source.
- Run a complete human QA playthrough of the F0001/F0002 slice, recording every
  wording, pacing, overflow, and speaker-voice issue back in the canonical
  catalog rather than fixing only the generated image.
- Playtest the complete F0003 slice, capture a trustworthy native scenario
  fixture, and pin representative composite, dialogue, and menu framebuffers.
- After F0000 is complete and QA-ready, continue the main-story spine from
  `F0004.MES`, assigning contextual speakers explicitly and retaining every
  editorial uncertainty in the checked-in notes.
- Continue adding sparse game-native fixtures beyond `F0002.MES` as translation
  reaches later scenario boundaries, pairing each with a short boot/load route
  and translator-facing checkpoint coverage.
- Graphics inventory and translation through `juice-img` where applicable.
- Reproducible binary-difference release with exact input hashes and emulator
  instructions.
