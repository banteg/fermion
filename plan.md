[![Fermion Mirai kara no Hōmonsha (フェルミオン 未来からの訪問者) // Silky's // PC-98 ...](https://tse3.mm.bing.net/th/id/OIP.oBfaKqGmMGE-YYnmmZ4JjAHaEo?r=0\&pid=Api)](https://x.com/PC98_bot/status/1279988617583214593?utm_source=chatgpt.com)

Your **“Half-Life of hentai”** diagnosis is remarkably defensible.

*Fermion: Mirai kara no Hōmonsha*—roughly, **“Fermion: Visitor from the Future”**—is a short, one-route science-fiction adult adventure by Silky’s, released for PC-98 on December 22, 1995, across four floppy disks. It uses the classic command-selection format rather than free movement: at most a few context-sensitive commands appear at once, and one English-language playthrough estimates roughly five hours for the whole game. ([VNDBReview][1])

## What was actually happening

The protagonist is **Conny**—コニー, which an English translation might more naturally render as **Connie**—a genetically altered woman from around the year **2296**. She has feline traits and can voluntarily transform into an ordinary-looking cat. Humanity’s genome has deteriorated after centuries of pollution and mutation, leaving reproduction and physical health in serious decline. ([VNDBReview][1])

Conny is sent approximately 300 years into the past aboard a time-travel craft called **Fermion**. Her ostensible assignment is to locate healthy twentieth-century human genetic material. She arrives in **1996**, lands near a girl named **Kanako**, and begins investigating Kanako, her family, friends, and school acquaintances. That explains why the first half can look like an unusually contrived sequence of yuri encounters: the erotic premise is literally framed as a genetic-sampling mission. ([VNDBReview][1])

Then the game changes genre.

Dr. **Kanzaki Kaori**, Conny’s superior and adoptive or parental figure, comes to 1996 herself, abducts Kanako, and takes her back to the future. Conny follows, is confined inside the future installation, and gradually discovers that the supposedly species-saving mission concealed a much more personal objective. From there, *Fermion* becomes a small facility-escape adventure: transform into a cat, enter ventilation ducts, investigate rooms, find fuel, activate machinery, obtain a wheelchair, rescue Kanako, and escape. ([VNDBReview][1])

So yes: **silent protagonist-adjacent scientist, mysterious research complex, institutional betrayal, vents, fuel-related machinery puzzles, imprisoned woman, escape sequence.** Gordon Freeman merely lacked the catgirl transformation mechanic.

## The larger ending revelation

**Major spoilers follow.**

Kanzaki’s project is not motivated solely by humanity’s abstract genetic future. It is tied to **Akira**, someone extremely close to her who died—or was dying—from the future’s genetic deterioration. Conny’s mission is rooted in Kanzaki’s attempt to locate the hereditary pattern, temporal counterpart, or genetic connection that might restore Akira. Kanako matters because the women encountered in 1996 are connected to the people of 2296 through a deliberately melodramatic mixture of ancestry, recurrence, and implied reincarnation. The ending consequently reframes the game as a distorted family-rescue story rather than a straightforward “collect DNA to save humanity” plot. ([BCPark][2])

There is one translation warning here: the surviving detailed Korean synopsis describes Akira using both **fiancée-like** and **younger-sister-like** language. That may reflect deliberately complicated relationships, Japanese kinship terminology, or simply an imperfect fan synopsis. I would not establish the exact relationship in an English script until checking the original dialogue carefully. The same applies to names such as **Marna/Māna** for マーナ.

## You were not imagining the vent-maze cruelty

The surviving Japanese walkthrough includes **two separate hand-drawn vent maps**. Its sequence is approximately:

1. Locate Kanako.
2. Discover that the machine lacks fuel.
3. Retrieve and install the fuel.
4. Wait or sleep to advance events.
5. Check the doctor and Kanako.
6. Speak with Marna.
7. Acquire a wheelchair.
8. Enter the second duct map.
9. Reach Kanako and escape.

That is much closer to an actual inventory-and-navigation adventure sequence than one expects after the first half of the game. ([Atwiki][3])

One review even complains that Conny can apparently carry the fuel can while transformed into a cat. That only strengthens the *Half-Life* comparison: the protagonist’s inventory exists in a dimension inaccessible to ordinary physics. ([VNDBReview][1])

## An English patch looks unusually feasible

Technically this would be a **disk-image translation patch**, not really a ROM hack, although everyone will understand “ROM hack.”

The strongest reason for optimism is **lime-juice**, an existing open-source decompiler/compiler for the `MES` scenario bytecode used by several Elf, AliceSoft, Fairytale, and—crucially—**Silky’s** games. It converts compiled scenario files into editable RKT text and recompiles them afterward; its companion image tooling handles formats such as GP4, GPC, and GPA. It also has English-oriented text wrapping support. ([GitHub][4])

Its built-in presets already cover numerous Silky’s titles, including *Ai Shimai*, *Kawarazaki-ke no Ichizoku*, *Nonomura Byōin no Hitobito*, and the 1995 games *Jack* and *Mobius Roid*. Those latter two use the **AI5** engine family with a `D0` dictionary base. Since *Fermion* is also a late-1995 Silky’s release, there is a strong chance it uses a closely related MES/AI5 setup. That remains an inference: *Fermion* is not presently listed as its own lime-juice preset, and I have not inspected its files. ([GitHub][4])

That means the best case is not “reverse-engineer an unknown scenario VM from scratch.” It may be closer to:

```sh
# First try automatic engine detection
juice -d --auto-engine *.MES

# Plausible fallbacks for a late Silky's AI5 game
juice -d -e AI5 -D D0 *.MES
juice -d -e AI5 -D D0 -E *.MES

# Recompile translated RKT scripts with automatic line wrapping
juice -c --auto-wrap *.rkt
```

The `-E` variant enables additional opcodes used by some later games. These should be tested separately, beginning with automatic detection—not applied blindly to all files. ([GitHub][4])

## A sensible translation workflow

### 1. Work from an installed HDD image

Preserve hashes of the four pristine floppy images, then install the game to a writable PC-98 hard-disk image. A surviving player report says the completed installation occupies only about **4.9 MB**, with the installer progressively unpacking the later disks, so the entire working tree should be easy to version and compare. ([BCPark][2])

An HDD installation will be much less irritating than repeatedly modifying four floppy images.

### 2. Identify the engine before translating anything

Inventory the installation and look especially for:

```text
*.MES
*.GPC
*.GP4
*.GPA
*.DAT
*.EXE
```

Then:

* Decompile one MES file.
* Inspect whether the Japanese lines and control instructions look coherent.
* Recompile it **without changing anything**.
* Put it back into the HDD image and verify that the game still boots and reaches the relevant scene.

A successful no-op round trip would establish most of the technical feasibility immediately.

### 3. Make a ten-minute vertical slice

Translate only:

* the opening;
* one dialogue exchange;
* one command menu;
* one character-name display;
* one multiline text box;
* save/load text, if easily reachable.

This exposes the real risks before hundreds or thousands of lines are translated:

* whether half-width ASCII renders correctly;
* how many English characters fit;
* whether punctuation is interpreted as control syntax;
* whether text speed or pagination breaks;
* whether player-visible commands are strings or baked-in graphics;
* whether script recompilation changes offsets used elsewhere.

Do not start the full script until this slice works.

### 4. Build a small Python translation pipeline

Given your Python and reverse-engineering background, I would keep RKT as the authoritative technical representation but generate a translator-friendly table such as:

```text
script_id
instruction_offset
speaker
japanese
english
context
status
```

The tooling should automatically reject:

* altered control opcodes;
* missing variables or placeholders;
* duplicate or lost line IDs;
* overlong command labels;
* unbalanced quotes;
* text that still contains unexpected Japanese characters.

Screenshots keyed to script offsets would help enormously because *Fermion*’s short command-select lines may be ambiguous without scene context.

### 5. Treat graphics separately

Menus, title cards, signage, and possibly location labels may be embedded in proprietary image files rather than represented as script strings. `juice-img` may already support them if the game uses the expected Silky’s formats. Otherwise, these are still likely manageable indexed PC-98 graphics rather than a large modern asset pipeline. ([GitHub][4])

The two vent maps appear to be navigational spaces rather than displayed automaps, so an English patch probably does not need to redraw those particular walkthrough maps.

### 6. Reserve executable hacking for the end

Best case: the engine already renders ASCII and lime-juice handles all scenario work.

Less pleasant case: the executable assumes full-width Japanese glyphs or fixed two-byte text. Then the patch may need a small x86 modification for:

* glyph width;
* character advancement;
* line-length calculation;
* text-window wrapping;
* command-menu dimensions.

PC-98 translation projects sometimes reach this stage because the final executable is ordinary 16-bit x86 code and graphical formats were commonly proprietary. But the known Silky’s scenario tooling means there is a good chance only a narrow renderer patch would be needed, rather than a complete engine analysis. ([46 OkuMen][5])

### 7. Release only binary differences

The clean release format would be:

* an `xdelta` patch for one precisely identified installed HDD image, or patches for the individual modified files;
* SHA-1/SHA-256 hashes of the expected original;
* a patcher script;
* emulator and installation instructions;
* translation notes covering character-name decisions;
* no original game data.

Exact-image xdelta distribution is already a normal approach for PC-98 fan translations. ([Dank Zine][6])

## Overall verdict

This is actually a **very good first substantial PC-98 translation candidate**:

* approximately five hours and only one route;
* memorable enough that a patch would have a real identity;
* substantial story hidden behind an inaccessible language barrier;
* genuine puzzles rather than pure text progression;
* probable compatibility with an existing Silky’s script toolchain;
* only a few megabytes of installed data;
* enough absurdity to attract players who would never otherwise try an obscure 1995 adult adventure.

The main uncertainty is no longer “Can its script possibly be extracted?” It is **whether Fermion uses the expected AI5/MES variant and whether its renderer accepts English cleanly**. A directory listing of the installed files—or an archive of the legally obtained installed game tree—would be enough to answer that and attempt the first decompile/recompile round trip.

[1]: https://vndbreview.blogspot.com/2018/04/fermion-mirai-kara-no-houmonsha-silkys.html "Fermion ~Mirai kara no Houmonsha~ フェルミオン ～未来からの訪問者～ [Silky's] - VNDBReview"
[2]: https://www.bcpark.net/bbs/303321 "[hdi|PC98x.] 페르미온 미래에서 온 방문자 완성판 FERMION フェルミオン 未来からの訪問者 (1995 SILKY'S) ::: bcpark.net"
[3]: https://w.atwiki.jp/retropcgame/pages/538.html "フェルミオン ～未来からの訪問者～ - レトロPC美少女ゲーム攻略 @ wiki - atwiki（アットウィキ）"
[4]: https://github.com/FuzionCD/lime-juice "GitHub - FuzionCD/lime-juice: 🍹 C++ port of Tomyun's \"Juice\" de/recompiler for PC-98 games using the ADV engine. Aims to be far more stable, readable, and maintainable on modern systems. · GitHub"
[5]: https://46okumen.com/ "46okumen.com"
[6]: https://agentannk.com/download/the-slayers-pc-98-english-patch/?utm_source=chatgpt.com "The Slayers PC-98 English Patch"
