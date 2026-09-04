# Why Fermion needs General Message support

**Historical note.** An early attempt to read Fermion’s scripts with lime-juice’s
AI5 parser lost almost the entire file, even though the commands reported
success. The game’s General Message dialect was subsequently identified and
implemented directly. Translation builds now use that support.

The failed test is retained here to explain the format choice and help anyone
revisiting the original files avoid the same mistake.

## The original compatibility test

Fermion's files have an AI5-like dictionary header, but the tested
`lime-juice` AI5 parser did **not** understand the bytecode that follows it.
The commands succeeded without rebuilding a usable script.

Tested input:

- file: `MAIN.MES`, extracted from `DISKA`
- size: 7,310 bytes
- SHA-256: `8182bbd7d4983e8b054cc5ed81d7feadbc1c832d1223a948ed3fe2b94091e703`

Tested tool:

- lime-juice v0.2.3
- commit: `dc00362a0d7e9f52931040119080b1435d26724a`

All four plausible configurations exited successfully during decompilation and
compilation, but every rebuilt file was only 207 bytes:

| Variant | Decompile | Compile | Input | Rebuilt | Exact |
|---|---:|---:|---:|---:|---|
| auto-engine | 0 | 0 | 7,310 | 207 | no |
| AI5 default | 0 | 0 | 7,310 | 207 | no |
| AI5, dictionary base D0 | 0 | 0 | 7,310 | 207 | no |
| AI5, dictionary base D0, extra opcodes | 0 | 0 | 7,310 | 207 | no |

The dictionary ends at offset `0xC6`. The instruction stream begins with this
sequence, which lime-juice misinterprets as text:

```text
6e 11 73 79 73 74 65 6d 2e 6d 6c 6c 00 00
n  .  s  y  s  t  e  m  .  m  l  l  \0 \0
```

The same `system.mll` prefix occurs immediately after the dictionary in other
scenario files. At the time, that repeated prefix pointed to an unsupported Silky’s script
format rather than a damaged file.

The temporary `fermion mes roundtrip` compatibility probe was retired after
the General Message dialect was identified and implemented directly. This
document retains the original negative result as provenance for that decision.

## How it was resolved

Analysis of `SIL.EXE` recovered the General Message instruction grammar. The
dialect now has direct support in lime-juice, so translation no longer passes
through the incompatible AI5 parser.
