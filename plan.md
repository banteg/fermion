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
  fallback, documentation, and a synthetic test.
- Every currently extracted Fermion MES file auto-detects as GM and performs a
  byte-exact no-op decompile/recompile round trip.

The structural audit covers 96 on-disk MES copies representing 77 unique
SHA-256 hashes: 130,119 instructions and 23,015 address operands when duplicate
copies are included. All 17,044 in-file targets land on decoded instruction
boundaries; the remaining 5,971 operands are external MLL call addresses.

Relevant commits:

- Fermion `56e4bf7`: preservation and MES probing tools.
- Fermion `145ecd1`: MZ load-image extraction.
- lime-juice `acad05d`: General Message text support, on branch
  `feat/fermion-general-message`.

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

## Current blocker: upstream address relocation

The GM implementation deliberately preserves unknown code in `(raw ...)` nodes.
That is sufficient for exact no-op round trips, but it is not yet safe for
arbitrary translation. If edited text changes byte length, later instructions
move while absolute branch/call targets inside raw code retain their old values.

Do not begin bulk translation until local code targets can be represented as
labels and backpatched during compilation.

## Active milestone: relocatable GM control flow

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

### 3. Add labels and backpatching to lime-juice — next

Incrementally replace raw control instructions with structured nodes. During
decompilation:

- identify local targets;
- emit stable labels;
- retain external addresses numerically.

During compilation:

- compute new node offsets;
- resolve labels after text encoding;
- backpatch local 16-bit targets;
- error on unresolved or out-of-range targets.

Keep raw fallback for instruction families that do not affect code addresses.
Port the Fermion walker narrowly: split code on proven instruction boundaries,
structure only the fixed relocation fields above, and preserve every other
instruction as raw bytes with its original offset attached for mapping.

### 4. Prove single-byte English rendering

Before relocation is complete, create one same-byte-length mode-2 ASCII patch in
a visible menu or late text record so no target moves. Run it in an emulator and
record:

- glyph source and appearance;
- horizontal advance (8 or 16 pixels);
- clipping and wrapping behavior;
- menu cursor/selection alignment;
- whether punctuation bytes have special meanings.

If mode 2 is unsuitable for narrative text, trace its glyph lookup, cursor
advance, and line-limit path from the `0x4a` handler before considering an
executable patch.

### 5. Build the first changed-length vertical slice

Once relocation works, translate and test:

- one opening line;
- one speaker-labelled exchange;
- one command menu;
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

- Safe replacement of translated files in a copied installed HDD image.
- Extraction table with stable IDs, Japanese, English, context, and screenshots.
- Placeholder/control-token validation and line-length checks.
- Graphics inventory and translation through `juice-img` where applicable.
- Reproducible binary-difference release with exact input hashes and emulator
  instructions.
