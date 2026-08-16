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
- MES compatibility probes are reproducible through the `fermion` CLI.
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
- A checked-in translation catalog retains stable pristine-source anchors,
  canonical one-to-many translations, original lines, wrapping constraints,
  progress status, and translator notes. The CLI verifies its file hashes and
  every exact physical text record.
- A checked-in coverage ledger enumerates complete story ranges independently
  of the translated entries, groups duplicate source lines, and reports every
  anchor as translated, explicitly excluded, or pending.
- Named headless routes can drive a writable copy of one translated HDI, capture
  several frames in a single run, reject content or framebuffer hash drift, and
  restore hash-keyed prefix state plus its matching disk snapshot.
- Sparse, checked-in save fixtures can reconstruct a native loadable slot from
  hash-pinned `REG` banks, allowing short scenario-entry routes across rebuilt
  translation images without committing complete game state or disk images.
- The catalog can now build a fresh translated image end to end: lime-juice
  recompiles changed-length GM files, Silky's archive offsets are repacked, and
  the copied HDI's nested FAT12 file is safely resized and verified.

The structural audit covers 96 on-disk MES copies representing 77 unique
SHA-256 hashes: 130,119 instructions and 23,015 address operands when duplicate
copies are included. All 17,044 in-file targets land on decoded instruction
boundaries; the remaining 5,971 operands are external MLL call addresses.

Relevant commits:

- Fermion `56e4bf7`: preservation and MES probing tools.
- Fermion `145ecd1`: MZ load-image extraction.
- Fermion `4c91a23`: native-derived General Message structural audit.
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
  short strings such as `BS`. The same `0x04` newline control works in mode 2;
  lime-juice now round-trips it and the translated three-line disclaimer proves
  it in the live renderer.

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
`cdabbd064c71d86149a573c1ae5be14e5b6a97698f21224a036193b45d5cbcf6`,
Kanzaki's reply
`9e82f1f74ad3ff813585ff64e383e730faa12961fecb58461b41bef6862e95f5`,
Connie's response
`ba44453ad344526336e9b161f8c78f93fa48a154dd83d63cc180e3517bfa1f78`,
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

Catalog schema 3 permits either one compact `file`/`offset` anchor or an
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

The current catalog build grows `MAIN.MES` from 7,310 to 7,541 bytes,
`F0000.MES` from 16,157 to 16,211 bytes, and `DISKA` from 1,090,166 to
1,090,451 bytes. Starting from pristine image SHA-256
`533a12e3e160af21a376de9eadde505a2d945d0069543a81131b564df7ddd4d8`, it
produces `fermion-translation.hdi` SHA-256
`0755e6633e17ace9c9c4a73259d513cd1c517b98dd173e9ff83b601bd54a5963`.
The named opening route passes all nine framebuffer hashes on that fresh image,
proving that changed-size media reconstruction preserves live control flow and
rendering across the prologue and into `F0000.MES`.

## Completed enabling milestone: portable save fixtures

### 10. Start runtime tests at scenario boundaries — complete

Relocation-aware Ghidra analysis recovered the native `0x72` through `0x75` and
`0x7e` register handlers. `REG_00` is the persistent global/template bank;
`REG_01` through `REG_10` are ten loadable slots. Opcode `0x74` writes the
current 6,944-byte global segment to the selected slot, while `0x75` reloads a
slot and restarts the scenario named at offset `0x1b10`. Opcode `0x7e` merges a
small progress range into `REG_00`; it is not a user save operation.

The first native fixture was recovered from the same global segment inside an
ignored NP2kai serialized state and validated through the game's actual `LOAD`
menu. It starts `F0000.MES` at the first translated scene. Relative to the
hash-pinned `REG_00` template, the loadable snapshot changes 110 bytes in 35
contiguous hunks. `runtime/save-fixtures.toml` records only those before/after
bytes and hashes; the complete 6,944-byte slot remains generated and ignored.

`fermion save apply` verifies the template and empty target slot, reconstructs
`REG_01`, verifies result SHA-256
`d53b209b09c42e969156a1a6e5599b2b2898c27bb058a3a55be0f7aa6abb4f24`,
and writes a new HDI without touching the input. The game-native load route
reaches the translated opening of `F0000.MES` in 10,500 frames and reproduced
framebuffer SHA-256
`f9abdf0e2bc12996538c9fcffea8dabe22965337822124a29673dac70fb047a0`.
It measured about 15.5 seconds cold and 3.9 seconds from its exact-build
8,299-frame cache boundary, versus about 49 seconds for the full prologue route.

The two acceleration layers have distinct roles. Native `REG` fixtures survive
translation-image rebuilds when their pinned banks are unchanged and resume at
scenario entry. Libretro states are core/config/content-specific but resume at
an exact frame within that shorter route. Full end-to-end routes remain the
release gate.

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

- Work down the 103-line initial coverage backlog, beginning with the contiguous
  `FOP.MES` opening narration, while retaining speaker identity, context, and
  editorial review notes.
- Placeholder/control-token validation and enforced word-boundary wrapping.
- Cropped framebuffer checkpoints where full-screen animation makes an exact
  whole-frame hash unnecessarily fragile.
- Add sparse game-native fixtures at later scenario boundaries as translation
  reaches them, pairing each with a short boot/load route and translator-facing
  checkpoint coverage.
- Graphics inventory and translation through `juice-img` where applicable.
- Reproducible binary-difference release with exact input hashes and emulator
  instructions.
