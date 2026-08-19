# FERMION — English Translation Brief

- **Source:** full extracted Japanese script (`script.md`), 77 content-unique MES files / 17,401 mode-1 text records; the `FOP.MES`-reachable story view (`script-story.md`) contains 72 files / 16,994 mode-1 records
- **Purpose:** authoritative plot reconstruction, translator’s brief, terminology and voice guide, implementation contract, QA guide, and localization-risk register for the English fan translation
- **Spoilers:** complete, including the central identity reveal and ending
**Content note:** this document describes the game’s sexual material only at a high level. The source includes sexualized high-school-age characters, ambiguous/coercive consent framing, family/incest-adjacent material, adultery, abduction, reproductive coercion, and medical abuse. The English version treats every character depicted in sexual content as 18 or older and discloses that change in an editorial note; source ages remain documented here rather than being retroactively attributed to the Japanese work. Section 11 records the release policy.

---

## 1. The game in one paragraph

In 2296, pollution has degraded the human gene pool so badly that the population is collapsing and pieces of once-normal genetic information can no longer be reconstructed. A temporary space-time phenomenon called a **Time Quake** opens a path exactly three hundred years into the past. **Connie**, an engineered cat-human mutant who works as a mutant hunter, pilots an experimental time machine to 1996 to collect intact human genetic data and warn the past about the environmental catastrophe ahead. She is rescued by a chronically ill girl from the **Takano family**, grows attached to the household, and uses its members and acquaintances as sources for her mission. The apparent rescue story then turns into a family tragedy and conspiracy: Connie’s creator, **Dr. Kaori Kanzaki**, is actually the adult future self of the sick girl, who survived by sleeping for centuries and waking after everyone she loved was dead. Kanzaki has used Project D both to save humanity and to rewrite her own past, while **Dr. Marie Procyon**, broken by the death of Akira, has coerced her into abducting a healthy person from 1996. The climax resolves the conspiracy, sends the future travelers home with enough genetic data to repair humanity’s descendants, and leaves the altered younger girl writing a letter to people she can never meet again.

---

## 2. What kind of story it actually is

The first half presents itself as a light science-fiction erotic adventure: a powerful but emotionally naïve catgirl from a ruined future discovers ordinary 1990s domestic life, school, family, food, clean rain, and intimacy. The second half reveals that nearly every sentimental motif in that material—motherhood, younger sisters, illness, loneliness, scent-memory, being “left behind,” and Connie’s resemblance to the Takano women—is structural foreshadowing.

The central dramatic idea is not merely “save the future.” It is:

> **What happens to a girl who is saved physically but displaced so far into the future that everyone and everything constituting her life is gone?**

Kaori’s crime is an attempt to repair that trauma by force: save her younger body, recover her mother and sister for a few hours, and prevent another version of herself from suffering the same exile. Connie’s arc mirrors hers. Connie was manufactured rather than born, longs for a mother and a family, and keeps finding substitute sisters and maternal figures. She begins as Kanzaki’s created dependent and ends as a moral agent capable of protecting Kanzaki, the younger Kanzaki, Marna, the Takano family, and even Marie.

The erotic routes are therefore not wholly detachable from the themes, although their execution is often exploitative. They repeatedly collapse the categories of lover, mother, sister, daughter, guardian, creator, and genetic relative. An English version should understand that thematic function even if it edits or removes individual scenes.

The translation’s thematic compass is the game’s unexpected shift: what first looks like a playful erotic time-travel premise becomes a story about a woman returning to the family she lost, a created person discovering that she belongs to two eras, and grief deciding whether science saves people or treats them as material.

---

## 3. Full plot, in narrative order

### 3.1 Prologue: Akira and the coercion behind Project D

An unnamed woman is taken to see the body of **Akira**, the person she loved. She blames herself for not saving him in time. A later exchange shows one scientist coercing another: bring back at least one human test subject from the past, or the other scientist’s “precious mutant” will be endangered. The ending identifies the grieving and coercive figure as Marie and the person being pressured as Kanzaki.

The title sequence spells **FERMION**, checks “fermion particles” and a **Time Quake**, and establishes the year 2296. Pollution of the atmosphere, ocean, and soil has weakened human genetics and reduced the population. Environmental recovery is too slow, and genetic information already lost cannot simply be reconstructed.

**Source anchors:** FOP, script lines 9816–9927.

### 3.2 Connie and Project D

**Connie** is a mutant made by combining human and animal genes. She works as a specialist hunter of other mutants; publicly she has police status, and for this mission she receives time-patrol authority. Her creator, guardian, superior, and lover is **Dr. Kaori Kanzaki**, head of **Project D**, also called the Space-Time Project.

Connie’s body has a cellular age of roughly seventeen, but she has existed for only three years. Mutants can mature extremely quickly before their growth rate settles into something closer to a human’s. As a child she believed Kanzaki was literally her mother; after learning that she had been manufactured, she cried through the night and Kanzaki held her. Connie consequently understands Kanzaki simultaneously as mother, older sister, boss, creator, and beloved partner.

The temporary Time Quake connects 2296 with 1996. A machine can enter the time tunnel by matching its oscillation frequency to the space-time oscillation, then reducing the frequency to emerge at the target time. Connie understands the piloting procedure but not the full theory. The mission is to collect genetic information still intact in people from 1996 and to deliver information capable of steering that era away from catastrophic pollution.

**Remia**, another mutant hunter and Connie’s former field partner, is intended to pilot a second machine after Connie proves the route. **Marie Procyon**, head of mutant development, appears stern and hostile toward mutants. Kanzaki behaves unusually on launch day and quietly says “I’m sorry” where only Connie’s enhanced hearing can catch it.

**Source anchors:** F0001, especially script lines 403–771.

### 3.3 First arrival in 1996

Connie reaches 1996 in a rainstorm. The first passage is physically brutal: she suffers severe headache, nausea, exhaustion, and loss of coordination. To conserve energy and hide, she changes into her small catlike **Mini form**, but collapses in a private garden.

A chronically ill high-school-age girl finds her. The girl smells faintly of milk, treats the apparent animal gently, carries her indoors, warms her, and feeds her milk-based soup. Connie initially remains in Mini form and reads the girl’s emotions through touch. She senses profound loneliness and fear of dying as the girl’s health worsens and school absences increase.

During a bath, Connie transforms into human form and reveals that she is a mutant from 2296, a police-like hunter searching for genes. The girl accepts the impossible unusually quickly and enthusiastically agrees to help. Connie begins thinking of her as a younger sister. The time machine has materialized in the garden of the **Takano household**, where the girl lives with her mother, father, and older sister.

The girl’s name is not present as ordinary text in the extraction because it is one of five player-renamable variables. The recovered bytecode maps her stable `name-slot:dear-person` role to default **Kanako (加奈子)**. Translation records should use the stable role rather than hardcoding the editable default.

**Source anchors:** F0002–F0005.

### 3.4 Life with the Takano family and the sample routes

Connie stays in the Takano home, usually concealing herself in Mini form when necessary. The family learns enough of the truth to shelter her. The girl becomes intensely attached to Connie; the mother offers calm warmth and adult acceptance; the older sister is more skeptical and blunt but eventually helps. The largely off-screen father is a doctor employed at the nearby hospital visible from the house. Later references to “father’s hospital” mean the hospital where he works, not necessarily one he owns.

Connie explains the future’s condition more precisely. Calling the target “strong genes” is convenient but scientifically imprecise even within the script. Her ring-like analyzer is actually checking whether a person possesses pieces of genetic information missing from 2296 humans. The real objective is therefore **intact or missing genetic data**, not generic hereditary superiority.

The time distortion is expected to last about ten days. Connie has a second mission beyond collection: ask the people of the past to choose a future that does not produce her polluted world.

The game’s branching adult structure occupies much of this middle act. Connie forms intimate relationships with members of the Takano household and with women introduced through them, including a senior named **Nanase**, a student named **Minazuki Yoshimi**, and two player-renamable friends. These encounters are used as the in-story mechanism for gathering cell samples. Some routes have L/R variants, alternate participants, or follow-up scenes. They are route branches, not separate timelines with distinct endings; the main plot continues after enough material has been collected.

For an English project, these scenes cannot be treated as neutral filler. Several involve a character the script explicitly places at roughly sixteen/high-school age, and many use a genre convention in which spoken refusal is contradicted by narration. That convention reads as coercion or assault in contemporary English. See the editorial section below.

### 3.5 First return to 2296

After spending a night in 1996, Connie returns to 2296 with samples and the machine’s transit telemetry. The return is much smoother because the onboard computer can use the outbound trace. Travel takes less than thirty minutes from her perspective and appears to preserve approximately the same local time at both ends.

Kanzaki has remained at the facility waiting for Connie and embraces her publicly when she returns. Connie hands over the trace data and genetic samples. After analysis and machine adjustment, Connie and Remia prepare to make the second crossing together.

Remia’s machine fails to synchronize: the unit that imposes the needed oscillation on the hull malfunctions. Remia orders Connie to continue alone, and Kanzaki confirms the order. Connie reaches 1996 for a second stay while Remia remains safely in 2296 recovering from fatigue and the failed synchronization.

**Source anchors:** F0013–F0016.

### 3.6 Second stay: school, acquaintances, and Kanzaki’s arrival

The Takano family welcomes Connie back. The remaining social and school routes take place during this stay. The school material lets the game contrast ordinary 1996 communal education with the isolated, terminal-based schooling of 2296. Connie is fascinated by the number of people, the normality of the environment, and the freedom children have to go outside.

Kanzaki then arrives in the second time machine herself. She says Remia is resting and that she refused to let Connie and Remia bear all the danger. On the surface she has come to inspect Connie’s safety and bring additional mission material, including plant seeds; privately she is visibly tense around the Takano family and knows small details of the house she should not know.

She tells Connie that the samples already obtained are technically sufficient, but leaves Connie in 1996 to gather more while she plans to return the next morning. During the visit, several clues accumulate:

- she finds household switches and supplies too easily;
- she knows the family’s bathing habits;
- she wears the same perfume as the mother;
- her bodily scent and mannerisms resemble the sick daughter;
- she reacts to the family with grief and suppressed recognition;
- the daughter and mother both feel that she is strangely familiar.

Kanzaki’s expressed reason for returning is concern for Connie. Her hidden reasons are to meet the family she lost, treat her younger self, and carry out Marie’s coerced demand.

**Source anchors:** F0027–F0029.

### 3.7 The disappearance

After Kanzaki departs, the sick girl vanishes from her room. Connie detects traces of an anesthetic or mutant-capture drug and suspects that she was sedated and carried into Kanzaki’s machine.

At this point the girl’s mother reveals the truth about the planned 1996 operation. Contemporary medicine cannot save her. The “operation” was going to be staged in the hope that believing herself cured would restore her will to live. The parents had also considered an experimental cold-sleep procedure that might preserve her until medicine advanced enough to treat her.

Connie immediately follows. Her return coordinates have been altered. Instead of the ordinary time port, she emerges at an unfamiliar hospital/research facility in 2296 beside Kanzaki’s machine. A trap incapacitates her with an anti-mutant capture drug.

**Source anchors:** F0030–F0031.

### 3.8 Kanzaki’s apparent betrayal

Connie wakes in a reinforced room designed to confine mutants. Kanzaki admits changing the coordinates and confirms that the missing girl is at the facility. She then performs the role of a ruthless scientist: she says the girl is a valuable reproductive test subject, threatens neurological surgery to remove resistance, and tells Connie she is being spared only if she remains compliant.

The language is intentionally monstrous because Kanzaki is trying to keep Connie away from the deeper conspiracy and, ultimately, leave her in 1996 where Marie cannot reach her. The tranquilizer shots she later fires at Connie are deliberately off target. At this stage, however, Connie experiences the performance as total betrayal by the person she trusts most.

**Source anchors:** F0032–F0033.

### 3.9 The vent-maze escape and Marna

The facility becomes the game’s adventure-game set piece. Connie notices the ventilation system, changes into Mini form, breaks into the ductwork, and begins mapping routes through rooms, corridors, lockers, storage areas, and the machine bay. The many `F00340x` files are spatial nodes and state variants for this maze rather than conventional linear chapters.

Kanzaki assigns **Marna**, a younger mutant she recently rescued, to care for Connie and keep her confined. Marna is frightened, apologetic, lonely, and absolutely devoted to Kanzaki. She attaches a supposed electromagnetic transformation-inhibiting collar, but later it is revealed to be a fake. Kanzaki has deliberately given Connie an escape route while maintaining the appearance of cooperation with Marie.

Connie and Marna form the sisterly bond foreshadowed in the opening. Marna senses that Marie is not simply cruel but profoundly lonely. Connie eventually tells Marna about the escape, arranges evidence that Marna was overpowered, and uses the vent network to locate and free the treated girl. The escape sequence includes inventory/problem-solving elements such as hiding tools and finding liquid hydrogen associated with the time machines—this is the part of the game most likely to require an actual map during play.

Connie transports the girl back through time and takes her to the nearby hospital where her father works in 1996. The future surgery has repaired the heart condition.

**Source anchors:** F0033–F0038, especially the `F003400*` maze nodes.

### 3.10 The identity reveal: Kanzaki is the girl’s future self

At the Takano home, Kanzaki confronts Connie and the family while holding a tranquilizer gun. She continues the villain performance, claiming the treatment was only incidental to preparing a test subject and saying Connie will be left in 1996 forever. Connie recognizes that Kanzaki’s aim is intentionally poor and that she is trying to sedate rather than kill her.

The girl’s mother suddenly addresses Kanzaki as her daughter and orders her to lower the gun. Kanzaki obeys and finally calls her **“Mom.”** The mother explains how she knew:

- Kanzaki knew where the family kept towels;
- she replaced missing bath supplies with the younger daughter’s preferred products;
- she used household routines identical to the daughter’s;
- perfume could not hide the daughter’s underlying scent from her own mother.

Kanzaki breaks down. She is the adult future version of the sick girl, living under a changed name.

### 3.11 Kaori Kanzaki’s original history

In the original timeline, the girl entered cold sleep in 1996. She woke in **2288**, after medicine had developed a successful operation. To her, only days had passed; in the outside world nearly three centuries had elapsed. Her parents, sister, and everyone she knew were dead.

A nurse named **Miki Kanzaki** helped her face the truth. She was taken in by the Kanzaki family—descendants connected with the preservation of the Takano home—and given a new legal identity: **Kaori Kanzaki**. Miki became her adoptive older sister.

The newly awakened girl found 2288 polluted and alien: artificial food, dangerous outdoor air, remote schooling, and a world in which her old community no longer existed. To give herself a purpose, she studied medicine and genetics. She joined the secret time project and recognized that the Time Quake might let her alter the past.

Her plan served two goals:

1. compare her own intact 1996 genes with her degraded future genes, making missing information unusually easy to identify;
2. bring her younger self to the future, perform the successful operation, and return her to 1996 so that no version of herself would wake alone centuries later.

She secretly set Connie’s original destination to her childhood home. She did not originally intend to keep the girl as a subject; she intended to return her after treatment. She hid the truth because Project D was already compromised by Marie’s demands and because admitting the personal plan would expose everyone involved.

The script says the sleep lasted “about 280 years,” but 1996 to 2288 is **292 years**. The archival English repairs this to **“nearly three hundred years”** and records the intervention in the restoration log rather than reproducing false arithmetic without comment.

**Source anchors:** F0039–F0040.

### 3.12 Marie’s intervention and the truth about Akira

Connie asks why Kanzaki said she wished Connie had remained in 1996. Kanzaki explains that she wanted Connie beyond Marie’s reach.

Marie then arrives in the third machine with a laser weapon. She intends to take healthy people from 1996 as reproductive subjects. Kanzaki exposes the motive behind her collapse:

- Marie and Akira worked together on genetic degradation and mutant research;
- Akira was gravely injured in a laboratory accident;
- Marie discovered a way to halt human genetic collapse, but too late to save him;
- grief and guilt turned her scientific mission into an obsession;
- she forced Kanzaki to abduct someone by threatening Connie’s safety.

Marna has secretly followed Marie by hiding in the third machine. She tries to disarm Marie and is shot. Her mutant physiology and Kanzaki’s guidance allow her to slow the bleeding and survive. Even while injured, Marna insists that Marie is not evil, only lonely, and says she sensed that loneliness when Marie once touched her.

Marna’s compassion breaks through Marie’s fixation. Kanzaki argues that live captive subjects are unnecessary: Connie’s samples contain enough information to reconstruct what future humanity has lost. Marie agrees to return and apply her expertise to the actual restoration problem.

**Source anchors:** F0041.

### 3.13 Farewell and ending

The Time Quake begins collapsing ahead of schedule. Connie, Kanzaki, Marie, and the injured Marna must leave within minutes. The third machine is tethered to Connie’s proven first machine rather than abandoned as future technology in 1996.

The farewell resolves the story’s family motifs:

- Connie tells the younger girl that half of Connie’s genes came from Kanzaki, so in a real biological sense Connie carries the younger girl’s genetic inheritance too.
- Adult Kanzaki says goodbye to her mother, older sister, and younger self.
- Kanzaki gives her mother a letter containing comments she wrote about one of her mother’s books after waking in the future—words she had carried for years with no one left to receive them.
- The family asks the younger girl to create a better future.

In 2296, Kaori Kanzaki and Marie analyze the recovered samples. Genetic information previously substituted with animal material can be restored, and the next generation is born with the repaired human sequences.

The altered younger girl survives in 1996 and writes an impossible letter to Connie and Kanzaki. She says Connie’s arrival has made it possible to change the future, that she wants to build a world in which people like Connie never have to be created as a response to human collapse, and that she will never forget the people she loved. The letter is addressed to **Connie Kanzaki** and **Kaori Kanzaki**, and the game closes with **“To be continued.”**

The script does not resolve the temporal paradox in detail. Adult Kanzaki continues to exist after her younger self’s history is changed. Treat the time model as emotionally mutable rather than mechanically rigorous; do not add explanatory dialogue that the Japanese does not contain.

**Source anchors:** F0042.

---

## 4. Chronology at a glance

### Original history

1. **1996:** The younger Takano daughter is about sixteen and has a congenital heart condition that contemporary medicine cannot cure.
2. Her family arranges experimental cryosleep in the hope that future medicine can save her. She believes she is undergoing an ordinary operation.
3. **2288:** She wakes after successful heart treatment and learns that her parents, sister, and everyone she knew are dead.
4. Nurse Miki Kanzaki supports her. The Kanzaki family adopts her, and she takes the new legal name **Kaori Kanzaki**.
5. Kaori studies medicine and genetics, joins the secret Space-Time Project, and eventually becomes head of Project D.
6. She creates Connie from human and feline genetic material. Connie understands Kaori as creator, mother, older sister, superior, and lover.
7. **2296:** Project D detects a temporary Time Quake linking 2296 with 1996.
8. Kaori sends Connie to recover genetic information missing from future humanity and secretly sets the Takano home as Connie’s first destination.

### Altered history created during the game

1. Connie befriends Kaori’s younger self without knowing who she is, collects intact genetic material, and gives the Takano family warnings about future pollution.
2. Connie returns to 2296 with samples and transit data, then makes a second trip to 1996.
3. Adult Kaori visits the Takano home, meets her lost family, and covertly takes her younger self to 2296.
4. Future medicine repairs the younger girl’s heart.
5. Connie escapes Kaori’s staged imprisonment, rescues the girl, and returns her to 1996.
6. The Takano mother exposes adult Kaori’s identity.
7. Marie’s plan to abduct healthy people from the past is stopped after Marna intervenes.
8. Connie, Kaori, Marie, and Marna return to 2296 with the recovered samples.
9. Kaori and Marie reconstruct missing genetic information for the next generation.
10. The altered 1996 family begins trying to prevent the environmental history that produced Kaori’s ruined future.

### Deliberate unresolved paradox

The ending lets the saved younger self and the already existing adult Kaori coexist across the altered timeline. There is no explicit branching-universe lecture, erasure effect, or closed-loop reconciliation. Preserve that ambiguity.

---

## 5. Character and voice bible

### At-a-glance voice matrix

| Character | Story function | English voice target |
|---|---|---|
| **Connie** | Protagonist, hunter, pilot, and emotional viewpoint | Fast, direct, warm, and slightly cocky. Use contractions. Let professional lines become crisp and procedural; use feline comedy selectively and never reduce her to cat puns or baby talk. |
| **Dr. Kaori Kanzaki** | Project D leader, Connie’s creator, and the younger daughter’s future self | Precise and restrained in public, soft and maternal in private. Her false-villain register should be deliberately cold but visibly strained; at the reveal, adult control collapses into the voice of a lost daughter. |
| **Kanako / young Kaori** | Connie’s rescuer and emotional center of the Takano home | Gentle, affectionate, and recognizably teenage rather than childlike. Preserve both her fear of abandonment and her capacity for resolve. |
| **Yuki / Takano mother** | Family anchor and the person who recognizes adult Kaori | Warm and unhurried, then short and authoritative when her family is threatened. She is observant, not mystical or vague. |
| **Ruri / Takano older sister** | Skeptic and protector | Casual, blunt, socially grounded, and protective, with room for dry humor. |
| **Remia** | Connie’s professional peer and intended second pilot | Practical, confident, and teasing. Concern appears through dry humor rather than sentimentality. |
| **Marna** | Connie’s intended younger sister and Marie’s moral counterweight | Quiet, deferential, and sincere. Keep her language simple without making her naïve, comic, or babyish. |
| **Dr. Marie Procyon** | Antagonist and geneticist whose grief drives the crisis | Clipped, clinical, and intimidating. Her late change should emerge from shock and grief rather than an instant personality replacement. |
| **Miki Kanzaki** | Kaori’s nurse and adoptive older sister | Gentle professional reassurance that gradually becomes familial. |
| **Akira** | Marie’s deceased loved one and research partner | Preserve his emotional importance without inventing a legal or romantic label the source does not supply. |

### Relationship map

- **Connie → Kaori:** creator, mother figure, older-sister figure, superior, and lover.
- **Kaori → Connie:** created daughter/protégé, subordinate, protected mutant, and lover.
- **Connie → young Kaori:** protected younger-sister figure and romantic/sexual partner.
- **Young Kaori = adult Kaori:** the two relationships form an intentional temporal mirror.
- **Kaori → Takano mother and older sister:** an adult daughter returning to the family she lost.
- **Connie → Marna:** promised younger sister and fellow mutant.
- **Marna → Marie:** empathic attachment that interrupts Marie’s grief-driven violence.

This network is both the story’s emotional structure and the source of many of its editorial and rating risks. Preserve the distinctions among chosen family, authority, genetic relationship, and erotic attachment rather than flattening them into generic affection.

### Connie / コニー

- **Function:** protagonist; cat-human mutant; hunter; pilot; emotional viewpoint.
- **Core contradiction:** physically formidable and professionally observant, but only three years old in lived experience and desperate for family connection.
- **Japanese voice:** predominantly `あたし`; lively, informal, sometimes blunt; switches to polite speech with authority or elders; internal narration can become mock-clinical, bashful, or overtly catlike.

**English voice recommendations:**

- Use an informal, energetic first-person voice without turning her into a generic anime catgirl.
- Let her tactical observations be concise: scent, distance, exits, pulse, motive.
- Preserve her self-corrections and comic overthinking.
- Use occasional feline phrasing only where the source does; do not insert “meow” into ordinary lines.
- Her embarrassment should read young and inexperienced, but avoid baby talk.
- Keep her erotic narration blunt, repetitive, and concrete where the Japanese is blunt, repetitive, and concrete. Do not elevate it into romantic or literary prose.
- Distinguish **chronological age (three years since creation)** from **physical/cellular age (about seventeen)** every time it matters.

**Forms of address:**

- `神崎博士` → **Dr. Kanzaki**, not “Professor Kanzaki.”
- `コニーおねえちゃん` → **Big Sis Connie** or **Connie, my big sis**. “Sister Connie” sounds religious in English.
- `おねえさん` is context-dependent: **miss**, **young lady**, **big sis**, or simply **you**.

### Dr. Kaori Kanzaki / 神崎香織

- **Function:** Project D leader; Connie’s creator/guardian/lover; adult future self of the sick Takano daughter.
- **Public voice:** precise, strict, professionally controlled.
- **Private voice:** maternal, teasing, tactile, sometimes vulnerable.
- **Reveal voice:** once she says `おかあさん`, her diction and emotional posture regress to the abandoned child she still is.

Do not make her apparent-villain dialogue too melodramatic. It should sound deliberately cold, as though she is forcing herself to say lines she despises. Her missed shot and trembling hands are essential signals.

### The sick Takano daughter — default Kanako / 加奈子

- **Function:** Connie’s rescuer; emotional center of the 1996 household; younger Kaori.
- **Age/status:** described as around sixteen and in high school; physically frail but curious, affectionate, and eager to be useful.
- **Voice:** bright, colloquial, somewhat childish in affect but not a small child; frequent elongated vowels and excited questions; fear of loneliness undercuts the cheerfulness.

Because the name is player-configurable, source-facing documentation may call her **the younger daughter** or **young Kaori** when identity matters more than the default. Catalog records use the stable `name-slot:dear-person` role; the recovered slot mapping confirms **Kanako** as its reset value.

### Takano mother — default Yuki / 由貴

- **Function:** novelist; warm maternal authority; the first person to recognize adult Kaori.
- **Voice:** calm, elegant, teasing, emotionally perceptive; can become sharply commanding when protecting her children.
- **Key localization point:** her recognition is not mystical. It is accumulated domestic knowledge—towels, shampoo, scent, habits—and should sound observant rather than supernatural.

### Takano older sister — default Ruri / 瑠璃

- **Function:** skeptical/practical older sister; counterweight to the younger daughter’s immediate trust.
- **Voice:** blunter and more adult; protective; capable of dry humor.
- **Extraction issue:** many lines contain only the runtime name token and therefore appear blank.

### Remia / レミア

- **Function:** Connie’s hunter partner and intended second pilot.
- **Voice:** practical and direct, with an impulsive streak; less deferential than Connie; uses teasing to conceal concern.
- **Plot note:** her machine malfunction explains why Connie conducts the second trip alone and why Kanzaki later crosses personally.

### Marna / マーナ

- **Function:** rescued younger mutant; Connie’s intended adoptive sister; moral catalyst in the climax.
- **Voice:** hesitant, apologetic, very polite, prone to repetition; grows more decisive after Connie encourages her.
- **Do not flatten her into comic timidity.** Her empathy is the one force capable of reaching Marie.

### Dr. Marie Procyon / マリー・プロシオン

- **Function:** mutant-development chief; antagonist driven by grief; brilliant geneticist needed for the solution.
- **Voice:** clipped, intimidating, emotionally brittle; anger often hides panic or bereavement.
- **Name issue:** introduced as `プロシオン` (**Procyon**) but called `プレシオン` in the ending. Use **Marie Procyon** provisionally and record the ending spelling as a likely source typo.

### Miki Kanzaki / 神崎美樹

- **Function:** nurse in 2288; Kaori’s adoptive older sister and first attachment after waking.
- **Voice:** gentle, hesitant because she knows the truth before Kaori does; becomes a stable familial presence.

### Akira / アキラ

- **Function:** Marie’s loved one and research partner, killed after a laboratory accident.
- **Voice:** no substantial living dialogue in the extracted main script; his importance is retrospective.

### The 1996 duty physician / 医師

**Function:** the on-call emergency physician who examines Kanako after Connie returns her to 1996. He works at the same nearby hospital as Kanako’s father but is not the father.

**Voice:** competent, calm, and professionally curious about the impossibly clean future surgical work.

**Bytecode label:** `【医師】` begins five records in `F0038.MES`.

### The 2288 attending physician / 医者

**Function:** the physician who removes Kanako’s bandages, tells her that the year is 2288, and explains the cryosleep interval.

**Voice:** gentle and hesitant; he delays the revelation to avoid shocking her and uses the editable given name plus `ちゃん`. Render that care through syntax and tone, not a romanized suffix.

**Bytecode label:** `【医者】` begins nine records in `F0040.MES`. This is a different figure from the 1996 `医師` and from the unlabelled doctor in the prologue.

### Fixed and uncertain secondary names

- `鷹野` → **Takano**.
- `水無月 良美` → family name **Minazuki**. **Yoshimi** is a plausible reading of 良美, but confirm from manual, package material, voice data, or original promotional text.
- `七瀬` → **Nanase**. Her given name is one of the runtime variables and is absent from ordinary extracted text.
- The player-renamable friends reset to **Yoko (陽子)** and **Hiroko (弘子)**.

---

## 6. Interpolated names and composite authoring records

The main menu has a **Name Change** system and resets five names to:

> 由貴・瑠璃・加奈子・陽子・弘子

The name editor labels five slots by role, in the same order:

1. `(お母さん)` — mother
2. `(お姉さん)` — older sister
3. `(あたしの大切な人)` — “my precious person”
4. `(お友達１)` — friend 1
5. `(お友達２)` — friend 2

The editor roles, reset strings, and recovered bytecode slots establish this mapping:

| Slot address | Stable role | Reset value | Romanization |
|---:|---|---|---|
| `0x03e8` | mother | 由貴 | Yuki |
| `0x03f6` | older sister | 瑠璃 | Ruri |
| `0x0404` | dear person / young Kaori | 加奈子 | Kanako |
| `0x0412` | friend 1 | 陽子 | Yoko |
| `0x0420` | friend 2 | 弘子 | Hiroko |

With reset names, young Kaori’s original 1996 name is therefore **Kanako Takano**. The editable given name changes what the game displays, not the character’s identity or her later legal identity as Kaori Kanzaki.

### Reveal and spoiler invariant

The `name-slot:dear-person` value is also adult Kaori’s original given name. When the mother addresses the adult scientist by that name in `F0039`, the rendering must exactly match the player-selected value. Do not replace it with **Kaori**, and do not expose the identity link early through catalog context visible to players, speaker labels, save descriptions, menus, route names, gallery titles, or character profiles.

The final letter and every replay/gallery surface that displays the younger daughter’s name are part of the same regression surface. A name preset is not complete merely because ordinary dialogue renders correctly.

### What the dump actually contains

There are **no** literal `【】` or `【 】` records in the content-deduplicated dump. The `FOP.MES`-rooted story corpus instead contains:

- 2,036 physical text records whose entire decoded text is `【`;
- 2,037 physical text records beginning with the orphaned suffix `】`;
- 5,124 name-slot renders in total, many occurring mid-sentence without brackets; and
- 12 renders from the two customizable adult-term slots.

Every standalone `【` record participates in the proven `0x4a` text, `0x45` string-copy, `0x4b` indirect-render, `0x4a` text sequence. The extra suffix is not damage: `[F0003:0c1c]` ends a longer sentence fragment with `【`, the name is inserted, and `[F0003:0c4d]` is `】。」`. Thus the 2,037 naked `】` records are only the most visible symptom; a bracket census is a lower bound on interpolated lines.

The compact physical view may consequently show records such as `[F0003:0c4d] 】。」` with no apparent name. A translator-facing view should reconstruct the whole rendered message, while the build must retain every physical record and the intervening opcodes.

### Locked authoring-token grammar

Authoring tokens are UTF-8 catalog metadata, never GM text:

- `⟦name:mother⟧`
- `⟦name:older-sister⟧`
- `⟦name:dear-person⟧`
- `⟦name:friend-1⟧`
- `⟦name:friend-2⟧`
- `⟦term:slot-1⟧` and `⟦term:slot-2⟧`

The grammar is `⟦(name|term):[a-z0-9]+(?:-[a-z0-9]+)*⟧`. The non-CP932 delimiters are deliberate: accidentally passing a token to lime-juice must fail encoding rather than produce plausible corrupt text. ASCII brace forms such as `{NAME_MOTHER}` are forbidden because they look like compilable dialogue even though mode-1 GM cannot encode them as intended.

### Locked merged-to-physical representation

`translations/fermion.toml` remains the sole canonical source. Catalog schema 5 will add composite entries with one canonical translation and one or more physical occurrences. Each occurrence is an ordered segment list:

1. a **text segment** stores its pristine MES file, text-opcode offset, mode, and exact Japanese;
2. a **token segment** stores its stable token ID and the exact immutable copy/render instruction span; and
3. the generated translator view joins those segments into one readable Japanese and English message.

For example, the catalog can display one message containing `⟦name:dear-person⟧` while retaining the three physical components at `F0003:0c1c`, the `0x45`/`0x4b` span, and `F0003:0c4d`.

The import/build rule is deterministic:

1. the English token sequence, order, and multiplicity must exactly match the source composite;
2. split the English on those immutable tokens;
3. map the resulting literal chunks back to the corresponding physical text segments in order;
4. leave every token’s original copy/render bytecode untouched; and
5. reject missing, reordered, duplicated, unknown, or leaked tokens before invoking lime-juice.

Only records separated by a recognized immutable token may be merged for display. Adjacent narration records remain distinct. This preserves the one-to-one physical text map, source anchors, opcode count, and timing while still letting a translator draft a natural sentence around a variable. Exact duplicate occurrences may share one canonical entry only when speaker, meaning, and context agree; contextual variants remain separate entries.

TSV, JSONL, SQLite, or another ergonomic database may be generated from this catalog and imported back with hash, anchor, and token checks. None is a second source of truth.

### English grammar problem

Japanese can insert a bare name almost anywhere. English may need:

- `⟦name:mother⟧'s room`
- `Hey, ⟦name:dear-person⟧, ...`
- `I went with ⟦name:older-sister⟧.`

A raw byte substitution cannot automatically supply apostrophes, articles, or comma spacing. The English script should keep punctuation outside the variable and avoid constructions whose grammar depends on the spelling of the chosen name.

Fixed Japanese surnames also precede editable given-name tokens where English normally reverses them. Treat forms such as `鷹野 + ⟦name:dear-person⟧`, `七瀬 + ⟦name:friend-2⟧`, and `速水 + ⟦name:friend-1⟧` as explicit schema-5 grammar and design tests. Preserve the existing runtime tokens; before claiming natural English order, prove a reversible segment mapping or an intentionally scoped renderer patch. Do not invent parallel preassembled variables or accept Japanese order silently.

### Locked name-editor policy

The archival English build keeps the name system but localizes it as a **tested preset selector**. It does not promise arbitrary Latin input: `0x4b` renders the stored strings through the game’s mode-1 path, and an unrestricted ASCII editor would require a separate engine patch plus exhaustive length and grammar testing. Every shipped preset must be encodable in the existing slot, tested at all five roles, and exercised in story, letter, and replay/gallery surfaces. The feature is preserved rather than removed; free-form Latin entry can be reconsidered only after the renderer and slot limits are proven.

---

## 7. Recommended terminology

| Japanese | Recommended English | Notes |
|---|---|---|
| フェルミオン / ＦＥＲＭＩＯＮ | **FERMION** | Keep the logo/title capitalization; use *Fermion* in prose if desired. |
| 時空震動 | **Time Quake** in UI/story shorthand; **space-time oscillation** in technical exposition | The original opening already displays “Time Quake.” `震動` is marked terminology, not merely ordinary `振動`. |
| 時空震動数 | **space-time oscillation frequency** | Avoid “time-quake number.” |
| 時空のひずみ／歪み | **space-time distortion** | Sometimes “rift” is smoother in dialogue. |
| 時空トンネル | **time tunnel** / **space-time tunnel** | Pick one as the formal term; “time tunnel” is more natural in Connie’s speech. |
| 時空移動マシン | **time-transfer machine** in formal explanation; **time machine** in ordinary dialogue | Preserve Connie’s occasional distinction without forcing the formal compound into every line. |
| Ｄ計画（時空計画） | **Project D (the Space-Time Project)** | The script never explains what D stands for. Do not invent “Dimension.” |
| ミュータント | **mutant** | In-world social class: engineered animal-human posthumans, not random comic-book mutation. |
| ミュータントハンター | **Mutant Hunter** | A formal occupational title is defensible. |
| タイムパトロール | **Time Patrol** / **Temporal Patrol** | Use **Temporal Patrol** if aiming for less pulp; menu/genre tone supports **Time Patrol**. |
| 時空監察官 | **temporal inspector** / **time-patrol officer** | Keep distinct from hunter role where possible. |
| ミニマム | **Mini form** | More natural than “Minimum.” Capitalize if treated as a formal transformation state. |
| 正常な遺伝子 | **intact genetic material** / **undamaged genetic data** | “Normal genes” carries modern eugenic implications and is less accurate to the script’s own clarification. |
| 強い遺伝子 | **robust genes** only when characters use the shorthand | Narration explicitly says this is imprecise. |
| 失われた／欠落した遺伝子情報 | **lost/missing genetic information** | Central scientific term. |
| 遺伝子劣化 | **genetic degradation** | Environmental decline across generations. |
| 遺伝子崩壊 | **genetic collapse** | Stronger term used in the Marie/Akira exposition; do not flatten every occurrence into “degradation.” |
| ヒト | **human(s)** | Katakana marks humans as a biological species from Connie’s perspective. Occasionally “the human species” helps. |
| 獣の遺伝子 | **animal genes** | “Beast genes” is too fantasy-coded for the scientific register. |
| 実験体 | **test subject**; occasionally **specimen** in deliberately dehumanizing speech | Marie and false-villain Kaori must sound abusive without the translation endorsing their framing. |
| パラサイト銃 | provisionally **capture gun** or **tranquilizer gun** | Literal “Parasite Gun” is suspicious. Verify art/manual before treating it as a proper noun. |
| 対ミュータント用捕獲薬 | **anti-mutant capture drug** / **mutant tranquilizer** | Choose based on scene register. |
| 電磁首輪 | **electromagnetic restraint collar** | Later revealed to be fake. |
| 前頭葉の手術 / ロボトミー | **frontal-lobe surgery / lobotomy** | The staged threat is meant to be horrifying; do not euphemize it. |
| フェルミ粒子 | **fermions** | `フェルミ粒子` is awkward Japanese scientific shorthand. |
| ヘリウム３ | **helium-3** | The pseudo-science links it to measurable oscillation. |
| コールドスリープ | **cryosleep** in normal dialogue; **suspended animation** in medical exposition | “Cold sleep” is intelligible but dated Engrish. |
| 一日留学 | **one-day visiting student** / **one-day exchange student** | This is a school visit, not literal international study abroad. |
| 博士 | **Dr.** | Use **Dr. Kanzaki** and **Dr. Marie**; “Professor” changes the institutional meaning. |
| エッチ / Ｈ | Contextual: **sex**, **fooling around**, **naughty**, or **intimate** | Translate the function and register rather than forcing one English equivalent everywhere. |
| `さん` / `ちゃん` / `様` / address-form `先生` | **Do not retain as romanized suffixes** | Express distance, affection, deference, or authority through syntax, names, kinship terms, and ordinary English titles such as **Dr.** |

### “Gene” versus “genetic information”

This distinction matters. The premise is not that people in 1996 possess a mystical “superior gene.” The analyzer looks for sequences/information absent in 2296. Translate explanatory passages with **data**, **sequence**, **information**, **missing segments**, and **intact material**. Reserve “strong genes” for Connie’s own acknowledged shorthand.

---

## 8. Voice and prose style

### Register shifts

Japanese character relationships are carried heavily by register:

- Connie is polite to Kanzaki in professional settings, looser in private.
- Kanzaki’s public speech is strict and controlled; at home she becomes warm and teasing.
- Marna uses deferential language even with Connie.
- The younger daughter is informal and openly affectionate.
- Marie uses formality as emotional armor and drops it when enraged.

An English patch should reproduce these shifts through syntax and word choice rather than preserving every honorific.

### Honorifics — locked policy

Do not use systematic romanized suffixes such as `-san`, `-chan`, `-sama`, or `-sensei`. Render their relationship work in English: first name versus surname, **Dr. Kanzaki**, **Mom**, **Big Sis**, a softened request, a formal sentence, or no overt marker where English naturally leaves one out. A plot-significant title or kinship term remains; a suffix does not survive merely because it is present in Japanese. Apply this policy consistently in dialogue, labels, and translator notes.

Kinship terms carry plot information. At the reveal, `おかあさん` should be **Mom**, not formal “Mother.” `コニーおねえちゃん` can begin as **Big Sis Connie** and become less marked as intimacy grows. Adult Kaori’s farewell to `おねえちゃん` should use the form already established for her older sister. Marna’s changing address to Connie should likewise register growing trust without importing a romanized suffix.

### Ellipses

The script uses very long runs of Japanese full stops as pacing and textbox timing. Do not reproduce every dot one-for-one. Recommended policy:

- `……` or long pauses → `…`
- emotionally broken speech → `I… I don’t…`
- silent beat in its own record → preserve that record and normally render a short `…`

Punctuation may be compressed **within** a record, but records are never merged, deleted, or reassigned to adjacent narration. Some silent records are branch timing, CG pacing, or voice/SFX synchronization points; the one-to-one anchor invariant applies even when two neighboring lines would read more smoothly as one paragraph.

### Exclamation and elongation

Reduce repeated `！！！！！`, `～～～～`, and elongated vowels unless they are essential to the performance. A single exclamation mark plus stronger wording is normally more natural. Preserve excess selectively for screaming, comic panic, or deliberate melodrama, and retain every physical timing record even when its visible punctuation is compressed.

### Internal thought

Connie’s internal monologue creates the contrast between her competent exterior and flustered private reactions. Keep thought visibly distinct from spoken dialogue using only presentation the renderer actually supports—source parentheses, quotation conventions, or a proven text-window treatment. Do not assume italics exist, and do not turn thoughts into neutral narration merely to simplify punctuation.

### Onomatopoeia

The source is saturated with sound-symbolic prose. Use three categories:

1. **Keep/localize as sound:** knocks, alarms, mechanical hums, impacts.
2. **Convert to action:** `こくん` → “She gave a small nod.”
3. **Omit or reduce:** repetitive tactile/erotic SFX that sound comic or clinical in English.

Connie’s feline comedy deserves selective preservation—ear twitches, purring thoughts, kotatsu enthusiasm, and occasional catlike diction are character beats.

### “Native organism” joke

Connie initially thinks of the 1996 girl as `原住生物`, literally a native/local organism. A natural rendering is:

> “Getting help from a native life-form might not be a bad idea… No. That sounds awful. She’s a human kid.”

The joke is that Connie’s mission mindset momentarily dehumanizes the very people she is learning to love.

### Technical exposition

The Japanese pseudo-science is repetitive and sometimes internally loose. The translation should improve sentence flow but not invent real physics. Connie herself admits she only understands enough to operate the machine. Preserve that limitation; it is part of the humor and protects the story from sounding as though it makes a rigorous scientific claim.

Use a three-level register for Connie:

1. **Procedural commands:** concise and confident.
2. **General explanation:** accessible and slightly textbook-like.
3. **Underlying theory:** hesitant, memorized, or openly incomplete.

Kanzaki and Marie may use more exact scientific language, but the translation must not repair the source’s fictional physics by adding unsupported explanations.

### Historical attitudes and negative utterances

The source contains period dialogue that treats same-sex attraction as strange and sexual scenes where narration contradicts spoken refusal. Apart from the disclosed adult-age framing, the English translation preserves characterization and meaning; it does not modernize isolated lines or disguise coercion through inaccurate vocabulary.

Translate negatives according to syntax and context:

- `恥ずかしい` → **I’m embarrassed / This is embarrassing**;
- `やめて` → **Stop**;
- `嫌` / `いや` → **No / I don’t want that**, or a non-lexical emotional cry only where the context genuinely supports it;
- `だめ` → **Don’t / You can’t / I can’t / This is too much**, according to the construction.

The adult-age note must not be used to manufacture assent line by line. Any future consent edit would have to revise setup and action explicitly and remain mechanically separate from the canonical translation.

---

## 9. Script/route structure for implementation

### Generated route graph is authoritative

The route graph is generated from bytecode, not maintained by hand. Every one of the 168 `0x6d` and `0x6f` scenario transfers in the 77 content-unique MES files has a literal target. Use:

```sh
uv run fermion gm transitions working/archives --format dot
uv run fermion gm script --story working/archives
```

The graph preserves branches, rejoins, cycles, and separately reachable duplicate records. The story view selects the 72 files reachable from `FOP.MES`; its filename order is convenient for reading but is not control flow. See [`gm-scenario-flow.md`](gm-scenario-flow.md) for the recovered topology and exact commands.

### Narrative section index — editorial aid only

This is a translator-facing map of narrative function, not a substitute for the generated graph:

| Span | Narrative phase |
|---|---|
| `FOP`–`F0001` | Akira and Marie prologue; Project D; Connie’s launch |
| `F0002`–`F0014` | First Takano-household stay, early branches, and Connie’s first return |
| `F0015`–`F0026L/R` | Second expedition, donor routes, and one-day school visit |
| `F0027`–`F0033` | Kaori’s homecoming, disappearance, capture, and staged betrayal |
| `F0034` / `F003400*`–`F0038` | Facility graph, Marna, escape, and the successful heart treatment |
| `F0039`–`F0040` | Identity reveal and Kaori’s original history |
| `F0041`–`F0042` | Marie and Akira, Marna’s intervention, farewell, and epilogue |

The extraction contains one clear common final ending. That does not by itself rule out hidden flag prerequisites, local game-over exits, or non-mode-1 behavior; retain those as executable QA questions rather than inferring them from filename order.

### Physical extraction order is not play order

The markdown combines files in a non-narrative order. The practical story order is broadly:

```text
FOP
F0000–F0014
F0015–F0029
F0030–F0033
F0034 / F003400* / F003401–F003417
F0035–F0038
F0039–F0042
```

The extraction places several later-numbered files before `FOP`, UI resources, and missing earlier-numbered files. Build your translation manifest by scene ID, not by line position in `script.md`.

### Branch suffixes

Files such as:

- `F0010L` / `F0010R`
- `F0022L` / `F0022R`
- `F0025L` / `F0025R`
- `F0026L` / `F0026R`

are branch variants. Do not expose “Left Route” and “Right Route” to players unless the engine itself does. Track the entry choice and rejoin point.

### Vent-maze nodes

`F0034` and `F0037` are empty container/index headings in the extraction. The actual maze/state content lives in:

- `F003400`
- `F0034001`
- `F0034002`
- `F0034003`
- `F003401` through `F003417`
- `F0034101`
- `F003701`

Treat these as rooms, ducts, or stateful revisits. Many repeated descriptions are intentional because the player can re-enter a location under different conditions.

### Apparent duplicates

There are many exact or near-exact repeated blocks. Causes include:

- multiple choices resolving to the same prose;
- state-specific copies of a location description;
- separate CG or timing paths;
- authoring duplication in the original.

Do **not** globally deduplicate physical records. A canonical catalog entry may own several anchors only after review proves that speaker, meaning, context, and required English agree. The bytecode graph still retains every separately reachable occurrence; a context-sensitive duplicate gets a separate canonical entry even when its Japanese is identical.

### Command labels

Common interaction commands:

| Japanese | Recommended UI |
|---|---|
| 見る | **Look** |
| 考える | **Think** |
| 話す | **Talk** |
| いじる | Contextual: **Touch**, **Tease**, or **Play with** |
| 攻める | For an adult archival build: **Take the lead** / **Press on**; avoid literal **Attack** |
| 身を任せる | **Let her lead** / **Give in** |
| ささやく | **Whisper** |

Use short labels; the original UI is designed around compact fixed-width text.

### Main menu

Suggested English:

- ２ＦＤドライブでプレイする → **Play with 2 Floppy Drives**
- １ＦＤ＋ＲＡＭディスクでプレイする → **Play with 1 Floppy Drive + RAM Disk**
- 最初から始める → **New Game**
- 続きから始める → **Continue**
- 名前変更 → **Change Names**
- 名前初期化 → **Reset Names**
- 単語変更 → **Change Terms**
- 単語初期化 → **Reset Terms**
- 絵を見る → **CG Gallery**
- シーンを見る → **Scene Replay**
- カタログを見る → **Catalog**
- ＤＯＳ → **Exit to DOS**

The catalog is a period Silky’s product catalog, not part of Fermion’s story.

### Mode-2 editor labels are not gallery noise

The unique corpus contains **16 mode-2 text records total**, not 16 `BS` records: ten `BS`, four ASCII quotation marks, and two spaces. Five `BS` labels occur in `NAME.MES` and five in `MONO.MES`, each beside the character grid and the visible `← / 中止 / 決定` controls. `MAIN.MES` calls those files as the name and term editors; they are not story or gallery records. Treat `BS` as the editor’s visible **Backspace** key and include these surfaces in UI QA.

### Custom adult-word system

The original lets the player replace two explicit anatomical terms. This is a localization trap:

- English articles and possessives may change around the inserted word.
- Singular/plural behavior can break.
- A player-entered phrase may overflow a textbox.
- The feature intersects with any edited/censored release policy.

**Locked decision:** retain the system as a small set of tested terminology presets using `⟦term:slot-1⟧` and `⟦term:slot-2⟧` in authoring. Do not ship unrestricted text entry, and do not remove the feature from the archival build. Every preset must fit the proven slot limit and be grammatically valid at all 12 story insertions. The localized editor should expose the preset choices directly rather than leave the Japanese character grid in an otherwise English build.

---

## 10. Source inconsistencies and restoration decisions

### Definite or probable source errors

1. **Marie’s surname**
   - introduction: `マリー・プロシオン` → **Marie Procyon**
   - ending: `マリー・プレシオン` → *Marie Presion/Plesion*
   - **Decision:** use **Procyon** throughout unless official packaging/manual evidence contradicts it; retain the ending variant in the restoration log.

2. **Cryosleep duration**
   - 1996 → 2288 is 292 years.
   - Script says “about 280 years.”
   - **Decision:** translate this as **“nearly three hundred years”** and disclose the repair. This preserves the intended scale without presenting false arithmetic.

3. **`確率された時代`**
   - In the doctor’s explanation, `確率` is almost certainly a typo for `確立`: the era in which the technology was **established/developed**.

4. **`プロシオン` / `プレシオン` spelling drift**
   - Keep in the QA database even after choosing a house spelling.

5. **Repeated lines and paragraphs**
   - Some are authoring duplicates; others are branching copies. The generated control-flow graph proves reachability; canonical sharing still requires speaker and context review.

### Restoration log — locked entries

| Location | Source | Archival English treatment | Reason |
|---|---|---|---|
| `F0040.MES:0x40c8` | `約２８０年` (“about 280 years”) | **nearly three hundred years** | The stated dates 1996 and 2288 are 292 years apart. The repair preserves the intended magnitude and is disclosed rather than silent. |
| Opening terminal sequence | period English including `Dimention` and broken system-status phrasing | use the naturalized terminal copy in section 13 | The strings are already English, but consistent naturalization is clearer than a mixed typo-only pass. Preserve the exact source in catalog notes. |
| Ending surname variant | `プレシオン` after earlier `プロシオン` | **Procyon** | Standardize an apparent spelling drift while retaining both source forms in QA notes. |

### Ambiguities to preserve

- Adult Kaori’s continued existence after younger Kaori is saved.
- The environmental warnings given to the Takano family should alter the ruined future, yet the epilogue still describes Kaori and Marie repairing the 2296 genome. The source does not say whether prevention is gradual, creates a branch, or changes a later future.
- Only eight years separate Kaori’s 2288 awakening from the 2296 mission. In that interval she recovers, enters university, studies medicine and genetics, joins the project, creates three-year-old Connie, and becomes project head. The chronology is implausibly compressed, but no alternate date is established.
- `F0040.MES:0x49cf` says that the Kanzaki couple who adopt Kaori are **her descendants** and caretakers of the old house. A childless sixteen-year-old entering cryosleep cannot have literal direct descendants; wider-family or older-sister descendants are plausible, but the source does not clarify.
- Whether final “Connie Kanzaki” is a legal surname, an affectionate family claim, or symbolic address.
- Exact expansion of the “D” in Project D.
- Whether `パラサイト銃` is a proper product name or an extraction/authorial oddity.

### Names requiring external confirmation

- reading of `良美`;
- any official Latin spelling for Remia, Marna, Procyon, and Connie.

---

## 11. Locked content and release policy

The canonical project goal is a source-faithful English translation of the 1995 work with one disclosed editorial change: every character depicted in sexual content is treated as 18 or older in the English version. The original Japanese ages and school status remain part of the archival record and must not be misreported as having changed in the source. Other translation choices remain source-faithful so the project does not drift into an undocumented rewrite.

### Major issues

1. **High-school-age sexual content**

   The younger daughter is described as about sixteen/high-school age. A disclaimer does not solve this for many jurisdictions or distribution platforms.

2. **Ambiguous or coercive consent**

   The source often has a character say “no,” “stop,” or try to move away while narration asserts that she does not “really” mean refusal. Literal English makes the coercion more explicit, not less.

3. **Family/incest-adjacent framing**

   The story repeatedly overlaps mother/daughter/sister/lover categories, and one adult character describes prior sexual contact with a sister.

4. **Adultery and household power dynamics**

   Some optional routes involve married adults or members of the same household.

5. **Abduction, reproductive coercion, lobotomy threat, and experimentation**

   These are plot-critical villain actions and should remain clearly framed as abuse, not euphemized away.

### A. Canonical English translation — accepted

- Preserve the original plot and route structure.
- Treat every character depicted in sexual content as 18 or older in the English version.
- Disclose the change in the English release notes instead of claiming that the source assigned adult ages.
- Do not embellish explicit content.
- Add strong upfront content warnings and restoration notes.
- Keep every physical record and document corrections, normalizations, and technical compromises.

All present translation, speaker, context, and restoration work targets this English layer. The original Japanese and source-age facts remain intact in source fields, research notes, and restoration records.

The English version must include this note:

> The original Japanese work assigns younger ages or school status to some characters. For this English version, every character depicted in sexual content is treated as 18 or older. This is an editorial change to the English version, not a claim about the original text.

### B. Story-focused rewrite — rejected

The project will not replace sample collection, remove route structure, or rewrite the game into a different story-focused edition. That would be an adaptation rather than preservation and is out of scope.

### Editorial invariant

Maintain one canonical English source of truth. Keep the adult-age policy explicit, preserve source ages in the archival fields and research record, and do not use the note as cover for unrelated or undocumented censorship.

---

## 12. Suggested translation workflow

### Phase 1 — Reconstruct the executable script model

- Keep the recovered five name slots and their `0x45`/`0x4b` interpolation spans under regression test.
- Finish semantic labels and preset constraints for the two customizable-term slots.
- Generate the scene/choice graph from bytecode; do not hand-maintain it.
- Identify textbox limits, encoding, line breaks, control codes, delays, and CG triggers.
- Confirm which repeated records are separately reachable.

### Phase 2 — Extend the canonical TOML catalog

For every record, preserve:

- MES file and offset (`F0001:0704`);
- raw Japanese;
- resolved variable placeholders;
- speaker;
- route/state condition;
- draft English;
- translator note;
- QA status.

Implement the composite-entry and token contract from section 6 in the next catalog schema. `translations/fermion.toml` remains authoritative. TSV, JSONL, CSV, or SQLite are generated translator views with a validated import path; they must never become parallel canonical databases.

### Phase 3 — Apply the locked glossary and policies

The following decisions are already locked and should be enforced during review:

- **Procyon**, **Mini form**, and the contextual **Time Quake** / **space-time oscillation** split;
- no romanized honorific suffixes;
- Yuki, Ruri, Kanako, Yoko, and Hiroko as reset-name romanizations;
- preset-only localized name and adult-term editors; and
- the disclosed adult-age framing as the canonical English content policy.

Voice-calibration examples belong in anchored canonical catalog entries with source, context, and notes. Do not create a second table of free-floating “final” translations inside this brief.

### Phase 4 — Translate the main-story spine first

Recommended order:

1. FOP — **complete and QA-ready; focused coverage and end-to-end route are green**
2. F0000 — **complete and QA-ready; 398 physical records / 391 canonical lines,
   human playtest pending**
3. F0001–F0002 — **complete and QA-ready; 462 physical records / 454 canonical translations**
4. F0003 — **translation and structural build complete; human playtest and native fixture pending**
5. F0004–F0016
6. F0027–F0042
7. Later route branches and scene replay labels
8. Menus, name editor, term editor, and catalog last

This keeps the canonical catalog contiguous from New Game across every
reachable branch. Do not skip an earlier scenario merely because a later file
is easier to draft or automate.

### Phase 5 — Review passes and in-engine QA

Run distinct passes rather than treating “edited once” as completion:

1. **Source and linguistic pass:** verify meaning, register, and terminology against the exact anchored Japanese.
2. **Reveal pass:** make every early clue work retrospectively without letting metadata or wording spoil Kaori’s identity.
3. **Variable pass:** exercise every name and term preset, including maximum-length values and English punctuation around tokens.
4. **Editorial pass:** audit content warnings, confirm the adult-age note is present, and verify that no other adaptation is undocumented.
5. **Playthrough pass:** exercise every branch, the facility graph, replay/gallery surfaces, and the final letter in the emulator.

Test specifically for:

- variable names at maximum length;
- apostrophes and commas around names;
- branching lines that rejoin with changed pronouns;
- scene-gallery unlock names;
- vent-maze navigation text;
- full-width/half-width Latin characters;
- `\n` behavior;
- ellipsis timing;
- save compatibility after adding Latin text;
- every renamed character appearing correctly in final letters and the identity reveal.

---

## 13. Locked naturalized opening terminal English

The source contains period Engrish such as `Target Dimention Space... input.` The implemented archival English is:

```text
FERMION STATUS ..... NOMINAL
Fermion field stable.

TIME QUAKE .... CONFIRMED
Space-time oscillation holding.

TARGET COORDINATES
...... ENTERED

ALL SYSTEMS .... NOMINAL
All instruments nominal.
Final checks... complete.
Control panel... unlocked.

-- SYSTEM SHUTDOWN --
End of operations confirmed.
SYSTEM POWER OFF
```

Use the naturalized version above. A typo-only Engrish pass is not an active alternative. The dot counts and split TARGET/ENTERED screens follow the actual physical timing records rather than an invented consolidated line. The source animation clears and redraws between several stages; do not merge those records merely to make a static transcript resemble one terminal page. Preserve the original terminal strings and the naturalization rationale in catalog/restoration notes so the archival intervention remains reviewable.

---

## 14. Compact pitch for a patch page

> **2296. Humanity is dying from centuries of pollution, and the genetic information it has lost cannot be rebuilt. Connie—a cat-human mutant, hunter, and experimental time-machine pilot—is sent to 1996 to recover intact human genes before a temporary rift in time closes forever. What begins as a strange visit to an ordinary family becomes a confrontation with the woman who created her, a childhood displaced by three centuries, and the cost of rewriting the past.**

**English-version editorial note:** The original Japanese work assigns younger
ages or school status to some characters. For this English version, every
character depicted in sexual content is treated as 18 or older. This is an
editorial change to the English version, not a claim about the original text.

---

## 15. Translation QA checklist

### Story and reveal

- [ ] The selected younger-daughter name is reproduced exactly when the mother addresses adult Kaori.
- [ ] No save label, gallery/replay title, speaker tag, route name, or player-visible profile spoils the identity reveal.
- [ ] Kaori’s staged-villain dialogue remains frightening, while her restraint, missed shots, and dummy collar make retrospective sense.
- [ ] The collar’s apparent and actual functions remain consistent before and after its discovery.
- [ ] Marie’s threat to Connie clearly pays off the prologue’s “precious mutant” coercion.
- [ ] Akira remains Marie’s loved one and research partner without an unsupported legal or romantic label.
- [ ] Adult Kaori’s farewell distinguishes Mom, her older sister, and her past self clearly.

### Names, tokens, and address

- [ ] Every composite preserves the exact token sequence, order, and multiplicity, and no authoring token reaches compiled GM text.
- [ ] Editable given names appear in natural English full-name order with Takano, Nanase, and Hayami.
- [ ] Apostrophes, commas, articles, and surrounding spaces remain grammatical for every shipped preset.
- [ ] No systematic romanized honorific suffix survives; titles and kinship terms follow the locked English policy.
- [ ] Every preset is exercised in ordinary story text, the identity reveal, final letter, save data, and replay/gallery surfaces.
- [ ] **Connie Kanzaki** appears only where the ending intends it and is not normalized backward through the script.

### Terminology and voice

- [ ] **Project D**, **Space-Time Project**, **Time Quake**, **space-time oscillation**, and **time tunnel** do not drift between equivalent contexts.
- [ ] Genetic exposition distinguishes missing information from simplistic “normal” or “superior” genes.
- [ ] **Procyon**, **Mini form**, cryosleep terminology, and the logged 292-year restoration remain consistent.
- [ ] Connie sounds procedurally competent without becoming a theoretical physicist or a generic catgirl.
- [ ] Kaori’s public/private/reveal registers, Marie’s grief, Remia’s peer voice, and Marna’s sincere deference remain distinct.
- [ ] Refusal and negative utterances are translated accurately rather than softened into manufactured assent.

### Engine and presentation

- [ ] Only proven interpolation spans are merged in translator views; every physical record, silent beat, and opcode span remains anchored.
- [ ] Exact Japanese duplicates are shared only after speaker, meaning, and route context agree.
- [ ] Literal `\n`, explicit line breaks, full-width/half-width Latin text, and one-glyph terminal animation are tested in engine.
- [ ] L/R branches reach the verified destinations, and facility nodes are tested through actual navigation rather than filename order.
- [ ] Long technical explanations, the mother’s deduction, the Marie/Akira exposition, and epilogue cards fit their message windows.
- [ ] Maximum-length names and terms wrap safely without corrupting control flow or save compatibility.
- [ ] Gallery unlocks, scene replay, name editor, term editor, and return-to-menu behavior remain functional.

### Editorial and release

- [ ] The English release includes the locked adult-age editorial note.
- [ ] Apart from the disclosed adult-age framing, the English translation preserves source meaning without embellishment or undocumented censorship.
- [ ] Every restoration intervention is logged at its source anchor.
- [ ] Content warnings cover high-school-age sexual material, coercive consent framing, family/incest-adjacent dynamics, adultery, abduction, reproductive coercion, medical abuse, grief, death, and gun violence.
- [ ] Distribution and platform review are completed independently of linguistic QA.

---

## 16. Evidence questions and highest-priority unresolved tasks

### Questions requiring executable, visual, or external evidence

1. What official Latin spellings, if any, exist for Connie, Remia, Marna, Procyon, and the reading of 良美?
2. Is `パラサイト銃` visibly named in art, packaging, or a manual, or should the provisional **capture gun / tranquilizer gun** remain?
3. Do condition flags expose a bad ending, game-over exit, or prerequisite not captured by the recovered inter-MES transition graph?
4. What are the effective line and column limits for message surfaces beyond the proven 61-column F0001/F0002 dialogue windows?
5. Does original documentation explain the intended time-travel model or the in-world meaning of **FERMION**?
6. Is **Connie Kanzaki** official nomenclature or only the younger daughter’s familial sign-off?

### Highest-priority implementation and research tasks

1. Implement catalog schema 5 composite occurrences, immutable authoring tokens, and validated merged-view import without changing the existing simple-entry behavior.
2. Prove a reversible strategy for English full-name order around the existing name-token spans, or define the smallest renderer change that can do so without creating parallel variables.
3. Semantically identify the two adult-term slots (`0x042e` and `0x043e`) and define a small grammatically safe preset set for all 12 story insertions.
4. Determine encodable, length-safe name presets and exercise every role in story, final-letter, replay, and gallery contexts.
5. Confirm the official readings/spellings of 良美, Remia, Marna, Procyon, and Connie from non-script materials.
6. Continue speaker/context review from the generated story inventory, splitting exact Japanese duplicates when route context requires different English.
7. Decide whether “Connie Kanzaki” is canonical nomenclature or only the younger girl’s familial sign-off.
