# MES round-trip probe

## Result

Fermion's files have an AI5-like dictionary header, but the current
`lime-juice` AI5 parser does **not** understand the bytecode that follows it.
A successful process exit is therefore not evidence of compatibility.

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
scenario files. This looks like a consistent, unsupported Silky's VM variant,
not corruption or a one-file anomaly.

The temporary `fermion mes roundtrip` compatibility probe was retired after
the General Message dialect was identified and implemented directly. This
document retains the original negative result as provenance for that decision.

## Outcome

Analysis of `SIL.EXE` recovered the General Message instruction grammar. The
dialect now has direct support in lime-juice, so translation no longer passes
through the incompatible AI5 parser.
