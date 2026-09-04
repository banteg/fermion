# Translation reference and technical notes

The [translation brief](fermion_translation_brief.md) is the main reference for
reading and translating *Fermion*. It covers the complete story, character
voices, terminology, and the decisions behind the English. **It contains full
spoilers, including the ending.**

The other documents explain how we read the original game files. They support
the translation and preserve findings that would otherwise be easy to lose:

| Document | What it helps with |
|---|---|
| [Following the story](gm-scenario-flow.md) | Finding scene branches and rejoins without mistaking file order for play order. |
| [Identifying speakers](gm-speaker-attribution.md) | Distinguishing names actually displayed by the game from identities inferred by a translator. |
| [Why the scripts need General Message support](mes-roundtrip.md) | Understanding an early failed conversion and the format support that replaced it. Historical note. |

Counts in these notes describe the original extraction or an early inventory,
not the current amount of translated or reviewed text. The
[catalog and coverage ledger](../translations/README.md) track translation work;
the [development guide](../DEVELOPMENT.md) has commands for generating fresh
reports and checking builds.

In these documents, **MES** means a game script file, **General Message (GM)**
is the scripting language used by this release, and an **anchor** is a reference
to a text instruction’s location in an unchanged original file. Offsets and
instruction bytes are retained so findings can be checked against the source.
