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
  short strings such as `BS`.

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

## Active milestone: first changed-length vertical slice

### 5. Build the first changed-length vertical slice — in progress

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
Runtime boot and interaction are the remaining gate for this substep.

After that relocation proof, translate and test:

- one opening line;
- one speaker-labelled exchange;
- one additional command menu;
- one multiline text box;
- one mode-2 string.

The slice must survive decompile, edit, compile, media replacement, boot, and
interactive execution before expanding translation scope.

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

- Filesystem-aware replacement of translated files when their sizes change.
- Extraction table with stable IDs, Japanese, English, context, and screenshots.
- Placeholder/control-token validation and line-length checks.
- Graphics inventory and translation through `juice-img` where applicable.
- Reproducible binary-difference release with exact input hashes and emulator
  instructions.
