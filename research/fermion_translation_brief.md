# FERMION — English Translation Brief

- **Source:** full extracted Japanese script (`script.md`), 77 content-unique MES files / 17,401 mode-1 text records; the `FOP.MES`-reachable story view (`script-story.md`) contains 72 files / 16,994 mode-1 records
- **Purpose:** authoritative plot reconstruction, translator’s brief, terminology and voice guide, implementation contract, QA guide, and localization-risk register for the English fan translation
- **Spoilers:** complete, including the central identity reveal and ending
**Content note:** this document describes the game’s sexual material only at a high level. Section 11 records the full issue list and the locked release policy.

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

The girl’s name is one of five player-renamable variables (slot mechanics in section 6); her stable `name-slot:dear-person` role resets to **Kanako (加奈子)**, and translation records use the stable role rather than the editable default.

**Source anchors:** F0002–F0005.

### 3.4 Life with the Takano family and the sample routes

Connie stays in the Takano home, usually concealing herself in Mini form when necessary. The family learns enough of the truth to shelter her. The girl becomes intensely attached to Connie; the mother offers calm warmth and adult acceptance; the older sister is more skeptical and blunt but eventually helps. The largely off-screen father is a doctor employed at the nearby hospital visible from the house. Later references to “father’s hospital” mean the hospital where he works, not necessarily one he owns.

Connie explains the future’s condition more precisely. Calling the target “strong genes” is convenient but scientifically imprecise even within the script. Her ring-like analyzer is actually checking whether a person possesses pieces of genetic information missing from 2296 humans. The real objective is therefore **intact or missing genetic data**, not generic hereditary superiority.

The time distortion is expected to last about ten days. Connie has a second mission beyond collection: ask the people of the past to choose a future that does not produce her polluted world.

The game’s branching adult structure occupies much of this middle act. Connie forms intimate relationships with members of the Takano household and with women introduced through them, including a senior named **Nanase**, a student named **Minazuki Yoshimi**, and two player-renamable friends. These encounters are used as the in-story mechanism for gathering cell samples. Some routes have L/R variants, alternate participants, or follow-up scenes. They are route branches, not separate timelines with distinct endings; the main plot continues after enough material has been collected.

Several of these scenes involve a character the script explicitly places at roughly sixteen/high-school age, and many contradict spoken refusal in narration; sections 8 and 11 lock the editorial treatment.

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

At this point the girl’s mother reveals the truth about the planned 1996 operation. Contemporary medicine cannot save her. The “operation” was going to be staged in the hope that believing herself cured would restore her will to live. The parents had also considered an experimental cryosleep procedure that might preserve her until medicine advanced enough to treat her.

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

In the original timeline, the girl entered cryosleep in 1996. She woke in **2288**, after medicine had developed a successful operation. To her, only days had passed; in the outside world nearly three centuries had elapsed. Her parents, sister, and everyone she knew were dead.

A nurse named **Miki Kanzaki** helped her face the truth. She was taken in by the Kanzaki family—descendants connected with the preservation of the Takano home—and given a new legal identity: **Kaori Kanzaki**. Miki became her adoptive older sister.

The newly awakened girl found 2288 polluted and alien: artificial food, dangerous outdoor air, remote schooling, and a world in which her old community no longer existed. To give herself a purpose, she studied medicine and genetics. She joined the secret time project and recognized that the Time Quake might let her alter the past.

Her plan served two goals:

1. compare her own intact 1996 genes with her degraded future genes, making missing information unusually easy to identify;
2. bring her younger self to the future, perform the successful operation, and return her to 1996 so that no version of herself would wake alone centuries later.

She secretly set Connie’s original destination to her childhood home. She did not originally intend to keep the girl as a subject; she intended to return her after treatment. She hid the truth because Project D was already compromised by Marie’s demands and because admitting the personal plan would expose everyone involved.

The script says the sleep lasted **“about 280 years,”** although 1996 to 2288 is **292 years**. The archival English preserves the doctor’s stated figure and records the contradiction in the restoration log. Translation does not silently make a character more accurate than the source.

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

Because the name is player-configurable, source-facing documentation may call her **the younger daughter** or **young Kaori** when identity matters more than the default; slot mechanics are in section 6.

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

The final letter and every replay/gallery surface that displays the younger daughter’s name are part of the same regression surface. A custom name is not validated merely because ordinary dialogue renders correctly.

The localized editor remains free-form rather than offering translator-invented name choices. It replaces only the Japanese grid and coordinate mapping with full-width CP932 Latin letters, hyphen, and apostrophe. The original 14-byte slots and 35-byte save range are unchanged. The editor guard moves from 5 to 6 to expose the slot's six-glyph capacity; an emulator boundary probe confirms that the sixth glyph renders and the seventh is rejected.

### Connie Kanzaki — locked ending-only form

`コニー・カンザキ様` appears only as an addressee in the younger daughter’s final letter. Render it as **Dear Connie Kanzaki** there, but do not infer that Connie legally adopted the surname, expose it in menus, or normalize it backward into earlier dialogue. For this project it is an ending-only familial form of address, not a legal name.

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

`translations/fermion.toml` remains the sole canonical source. Catalog schema 7
retains schema 5's composite entries and schema 6's speaker-evidence split,
while storing each shared scene context once in a top-level `[[scenes]]` record.
Entries reference a stable scene ID. Each composite occurrence is an ordered
segment list:

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

Only records separated by a recognized immutable token may be merged for display. Adjacent narration records remain distinct. This preserves the one-to-one physical text map, source anchors, opcode count, and timing while still letting a translator draft a natural sentence around a variable. Exact duplicate occurrences may share one canonical entry only when speaker, attribution evidence, meaning, and context agree; contextual variants remain separate entries.

Exact source and English duplicates with the same speaker, attribution,
context, encoding, layout, and QA status must share one canonical entry. A
genuine mechanical split uses an entry note beginning with `Duplicate split:`;
notes by themselves never justify duplicate records. Catalog validation rejects
both mergeable duplicates and unannotated mechanical splits.

`speaker` is a canonical lowercase identity such as `connie`, `kanzaki`, or
`name-slot:mother`; it does not change spelling according to evidence type.
`attribution = "proven"` means the record itself contains a recognized literal
or dynamic speaker label and is checked against the pristine source.
Scene-derived assignments use `attribution = "inferred"`. The Silky product
catalog is `catalog-copy`, not whichever bracketed product title GM's mechanical
label scanner most recently saw.

`scene` is a stable, readable ID whose top-level record owns the archival
context prose. Entry objects resolve that context for reporting and review, but
the TOML never repeats it per line. Duplicate scene contexts, unknown scene
references, and unused scene records are validation errors.

TSV, JSONL, SQLite, or another ergonomic database may be generated from this
catalog and imported back with hash, anchor, and token checks. None is a second
source of truth.

### English grammar problem

Japanese can insert a bare name almost anywhere. English may need:

- `⟦name:mother⟧'s room`
- `Hey, ⟦name:dear-person⟧, ...`
- `I went with ⟦name:older-sister⟧.`

A raw byte substitution cannot automatically supply apostrophes, articles, or comma spacing. The English script should keep punctuation outside the variable and avoid constructions whose grammar depends on the spelling of the chosen name.

The preserved physical segment pattern can require a source-initial token to
remain first in English. Do not paper over that constraint with `NAME--I ...`.
Use a grammatical token-led clause such as `NAME gets ...` or `NAME's ... is
...`; reserve an ellipsis for a real hesitation or fragment in the source. Do
not insert new text opcodes merely to move a token unless that renderer change
is separately designed, compatibility-tested, and logged per affected anchor.

Fixed Japanese surnames also precede editable given-name tokens where English normally reverses them. Treat forms such as `鷹野 + ⟦name:dear-person⟧`, `七瀬 + ⟦name:friend-2⟧`, and `速水 + ⟦name:friend-1⟧` as explicit composite grammar and design tests. Preserve the existing runtime tokens; before claiming natural English order, prove a reversible segment mapping or an intentionally scoped renderer patch. Do not invent parallel preassembled variables or accept Japanese order silently.

### Locked name-editor policy

The archival English build preserves the original **free-form name editor**.
It uses a single Latin palette whose letters, hyphen, and apostrophe map to
full-width CP932 glyphs. This is not packed one-byte ASCII: each selection still
writes one 16-bit character cell through the original append path, so the
existing backspace, terminator, confirmation, storage slots, and save format
continue to apply. The Japanese four-class selector is bypassed; cancel returns
directly to the five-role name list.

Runtime proof fixes the limits precisely. Lime Juice can relocate a grown
initializer or editor routine, but relocation does not enlarge the five 14-byte
destination buffers. The indirect mode-1 renderer displays ordinary ASCII
bytes as Japanese glyphs, so both defaults and typed input are encoded as
full-width CP932 Latin at two bytes per character. Allowing for the terminator,
each name has a six-character maximum. The source-derived reset names—Yuki,
Ruri, Kanako, Yoko, and Hiroko—all fit that limit. The adult-term buffers are 16
bytes, allowing seven full-width characters plus the terminator. Both mirrored
editors use the same generated Latin coordinate table while retaining their
original destination addresses and file load/save ranges. Catalog loading
capacity-checks each reset value and derives wrapping width from its encoded
form rather than trusting a second hand-maintained width field.

---

## 7. Recommended terminology

| Japanese | Recommended English | Notes |
|---|---|---|
| フェルミオン / ＦＥＲＭＩＯＮ | **FERMION** | Keep the logo/title capitalization; use *Fermion* in prose if desired. |
| 時空震動 | **Time Quake** in Connie’s speech, thought, pilot narration, and story/UI shorthand; **space-time oscillation** in scientists’ technical exposition | The original opening already displays “Time Quake.” Let Connie use the in-world operational name rather than making her sound like a theorist. `震動` is marked terminology, not merely ordinary `振動`. |
| 時空震動数 | **Time Quake frequency** for Connie; **space-time oscillation frequency** in formal scientific exposition | Keep distinct from the machine or hull’s ordinary vibration frequency. |
| マシン震動 / マシン震動数 | **machine/hull vibration** / **machine vibration frequency** | Hardware vibration in F0015 is not another name for the Time Quake. |
| 時空のひずみ／歪み | **space-time distortion** | Sometimes “rift” is smoother in dialogue. |
| 時空トンネル | **time tunnel** | The catalog already uses the natural pulp term consistently; do not reopen **space-time tunnel** as a parallel formal variant. |
| 時空移動マシン | **time-transfer machine** in formal explanation; **time machine** in ordinary dialogue | Preserve Connie’s occasional distinction without forcing the formal compound into every line. |
| Ｄ計画（時空計画） | **Project D (the Space-Time Project)** | The script never explains what D stands for. Do not invent “Dimension.” |
| ミュータント | **mutant** | In-world social class: engineered animal-human posthumans, not random comic-book mutation. |
| ミュータントハンター | **Mutant Hunter** | A formal occupational title is defensible. |
| タイムパトロール | **Time Patrol** | The source itself chooses the pulp katakana title. Do not polish it into **Temporal Patrol**. |
| 時空監察官 | **temporal inspector** | The formal kanji title is distinct from both **Mutant Hunter** and the katakana **Time Patrol**. |
| ミニマム | **Mini form** | More natural than “Minimum.” Capitalize if treated as a formal transformation state. |
| 遺伝子 | **genes** in ordinary speech; **genetic samples** when collected or transported; **genetic material** only where the register is genuinely technical | Do not make Connie sound like a grant abstract merely because a biologically smoother mass noun is available. |
| 遺伝子を採取する / もらう | **collect/get a sample**, **collect genes** | Choose the concrete mission or bodily-sample sense; do not default every occurrence to “collect genetic material.” |
| 正常な遺伝子 | **intact genes** / **intact genetic material** / **undamaged genetic data** | Use the more technical forms in precise explanation. Avoid a translator-endorsed “superior genes” reading. |
| 強い遺伝子 | **robust genes** only when characters use the shorthand | Narration explicitly says this is imprecise. |
| 純粋な遺伝子 | **pure human genes** | Preserve the source’s uncomfortable eugenic shorthand where characters use it; do not silently rewrite it as missing-information terminology. |
| 失われた／欠落した遺伝子情報 | **lost/missing genetic information** | Central scientific term. |
| 遺伝子劣化 | **genetic degradation** | Environmental decline across generations. |
| 遺伝子崩壊 | **genetic collapse** | Stronger term used in the Marie/Akira exposition; do not flatten every occurrence into “degradation.” |
| ヒト | **human(s)** | Katakana marks humans as a biological species from Connie’s perspective. Occasionally “the human species” helps. |
| 獣の遺伝子 | **animal genes** | “Beast genes” is too fantasy-coded for the scientific register. |
| 実験体 | **test subject**; occasionally **specimen** in deliberately dehumanizing speech | Marie and false-villain Kaori must sound abusive without the translation endorsing their framing. |
| パラサイト銃 | **capture gun** | The sole script occurrence explicitly identifies Connie's mutant-hunting weapon. Keep this functional rendering unless external art or documentation proves a proper product name. |
| 麻酔銃 | **tranquilizer gun** | A separate ordinary term used when a human target is threatened or drugged; do not merge it backward into `パラサイト銃`. |
| 対ミュータント用捕獲薬 | **anti-mutant capture drug** | The technical drug name at Connie's altered return point. |
| 電磁首輪 | **electromagnetic restraint collar** | Later revealed to be fake. |
| 前頭葉の手術 / ロボトミー | **frontal-lobe surgery / lobotomy** | The staged threat is meant to be horrifying; do not euphemize it. |
| フェルミ粒子 | **fermions** | `フェルミ粒子` is awkward Japanese scientific shorthand. |
| ヘリウム３ | **helium-3** | The pseudo-science links it to measurable oscillation. |
| コールドスリープ | **cryosleep** in normal dialogue; **suspended animation** for the explanatory `冷凍睡眠` gloss | This is lexicalized Japanese science-fiction vocabulary, not source-origin English UI. Translate it to the idiomatic English equivalent rather than calquing the katakana. |
| 留学生 / 外国からの留学生 | **exchange student** / **exchange student from abroad** | This is the Takano family’s cover story in F0024 and the term used by the teacher. |
| 一日留学 | **one-day visit** / **here for a one-day visit** | This is Connie’s description of the visit in F0026L, not a second occurrence of 留学生 and not “one-day exchange student.” |
| 博士 | **Dr.** | Use **Dr. Kanzaki** and **Dr. Marie**; “Professor” changes the institutional meaning. |
| エッチ / Ｈ | Contextual: **sex**, **fooling around**, **naughty**, or **intimate** | Translate the function and register rather than forcing one English equivalent everywhere. |
| `さん` / `ちゃん` / `様` / address-form `先生` | **Do not retain as romanized suffixes** | Express distance, affection, deference, or authority through syntax, names, kinship terms, and ordinary English titles such as **Dr.** |

### “Gene” versus “genetic information”

This distinction matters, but it is register-sensitive. The premise is not that people in 1996 possess a mystical “superior gene”: precise explanatory passages should use **data**, **sequence**, **information**, **missing segments**, and **intact material**. Ordinary `遺伝子`, however, remains **genes** or **samples** in Connie’s dialogue and narration. Reserve **strong genes** and **pure human genes** for the characters’ own acknowledged or unsettling shorthand rather than silently correcting their worldview.

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

On-screen dialogue speaker tags use Title Case for both fixed and editable
names: `[Connie]` and the dynamic default `[Kanako]` belong to the same visual
system. Do not uppercase editable presets merely to repair a tag, because those
same values appear inside ordinary prose. Bracketed game and product titles are
not speaker tags and retain their established title capitalization.

### Naturalization and source-origin English

Naturalize fluent Japanese speech into fluent character English. A katakana loanword is part of the Japanese sentence and should be translated by meaning and register: `コールドスリープ` becomes **cryosleep**, while **kotatsu** may remain because it names a culturally specific object already established in English. Do not preserve an awkward English calque merely because the Japanese happens to be written in katakana.

English already printed by the original game is a different evidence class. Preserve its period computer flavor by default, including terseness and odd phrasing, and make any correction a source-anchored, logged intervention. The naturalized opening terminal in section 13 is the project’s already-approved exception; it is not precedent for silently polishing every source-origin English string.

### Honorifics — locked policy

Do not use systematic romanized suffixes such as `-san`, `-chan`, `-sama`, or `-sensei`. Render their relationship work in English: first name versus surname, **Dr. Kanzaki**, **Mom**, **Big Sis**, a softened request, a formal sentence, or no overt marker where English naturally leaves one out. A plot-significant title or kinship term remains; a suffix does not survive merely because it is present in Japanese. Apply this policy consistently in dialogue, labels, and translator notes.

Kinship terms carry plot information. At the reveal, `おかあさん` should be **Mom**, not formal “Mother.” `コニーおねえちゃん` can begin as **Big Sis Connie** and become less marked as intimacy grows. Adult Kaori’s farewell to `おねえちゃん` should use the form already established for her older sister. Marna’s changing address to Connie should likewise register growing trust without importing a romanized suffix.

Use this relationship matrix for recurring plot-bearing forms:

| Speaker / source form | English treatment | Function to preserve |
|---|---|---|
| Kanako `コニーおねえちゃん` | **Big Sis Connie** / **Connie, my big sis** | Her eager adoption of Connie as family. |
| Kanako `レミアおねえちゃん` | **Big Sis Remia** | Extends the same sister network to Remia; do not drop the kinship term. |
| Marna `コニーおねえさん` | **Big Sis Connie** / **Connie, my big sister** | Polite, tentative sisterhood growing into trust. |
| Marna `コニーおねえさま` in sleep-talk or heightened address | **Connie... my big sister** / **Big Sister Connie** | A more reverent or emotionally heightened rung than casual `おねえさん`; do not flatten both forms automatically. |
| Yoko `先輩……お姉さま` | **my senior... no, my big sister** | The self-correction is a character joke and relationship reveal; preserve both sides rather than choosing one generic address. The swimming-club setting alone does not establish **Captain**. |
| Adult Kaori `おねえちゃん` at farewell | **Sis** / the already-established older-sister form | Her professional control has collapsed back into family speech. |

### Ellipses

The script uses very long runs of Japanese full stops as pacing and textbox timing. Do not reproduce every dot one-for-one. Recommended policy:

- `……` or long pauses → ASCII `...` in the mode-2 English script
- emotionally broken speech → `I... I don't...`
- a source record consisting only of `・` followed by `。` → preserve the
  physical record but render the fixed short `...`, regardless of the Japanese
  dot count

The one-glyph `・` records in the opening terminal are timed progress animation,
not story silence, and remain outside that normalization. Unicode `…` is not an
authoring option for mode 2.

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

### Erotic narration and `攻める`

The adult command-label mapping in section 9 does not supply a prose gloss. In narration, `攻める` marks sustained, forceful, or targeted action; choose a concrete verb from the described body part and motion rather than defaulting to abstract **tease**, **pleasure**, or euphemistic “intimate flesh.” Those words remain available when they are genuinely the best local reading, but they are not a house translation.

Use the revised F0000 opening as calibration:

- `F0000.MES:0x2416` — **goes after one weak spot after another**;
- `F0000.MES:0x2953` — **keeps pressing me, trying to make me cry out**;
- `F0000.MES:0x318b` — **works a sensitive spot inside my slit**.

Preserve the source’s force and agency. If the sentence supplies fingers, tongue, pressure, rubbing, or a target, name that action rather than translating only its intended result.

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

### Refusal, narrator claims, and historical attitudes

The source contains period dialogue that treats same-sex attraction as strange and sexual scenes where narration contradicts spoken refusal. The English translation preserves characterization and meaning; it does not modernize isolated lines, alter stated ages, or disguise coercion through inaccurate vocabulary.

Keep three evidence levels distinct throughout the canonical catalog:

1. A character's spoken refusal remains a refusal, even when later dialogue or narration conflicts with it.
2. Observable action may show participation, resistance, stillness, or a later change of mind; translate only the action actually stated.
3. A narrator's claim about pleasure, desire, or hidden intent remains a narrator claim. Do not promote it into objective assent or rewrite the preceding speech to make the claim true.

Catalog context and notes should identify those conflicts when they affect interpretation. They must not resolve them on the character's behalf.

Translate negatives according to syntax and context:

- `恥ずかしい` → **I’m embarrassed / This is embarrassing**;
- `やめて` → **Stop**;
- `嫌` / `いや` → **No / I don’t want that**, or a non-lexical emotional cry only where the context genuinely supports it;
- `やん` → decide locally: it can be a coy protest, a shortened negative, or an erotic vocalization. Do not lock it globally to either **No** or a moan. Surrounding syntax, physical resistance, and adjacent explicit `嫌` / `だめ` / `やめて` determine whether it carries lexical refusal;
- `だめ` → **Don’t / You can’t / I can’t / This is too much**, according to the construction.

A content warning or distribution override must not be used to manufacture assent line by line. Any future consent edit would have to revise setup and action explicitly and remain mechanically separate from the canonical translation.

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

**Locked decision:** retain the original free-form system using
`⟦term:slot-1⟧` and `⟦term:slot-2⟧` in authoring. The localized term editor uses
the same full-width CP932 Latin palette as the name editor, with the original
16-byte slots and save layout. Its guard moves from 6 to 7 to expose the
seven-character slot capacity. Default and representative custom values
must be checked at all 12 story insertions; prose around the tokens must not
depend on a particular article, number, or spelling.

---

## 10. Source inconsistencies and restoration decisions

Repair only a demonstrable text-level error whose intended reading is independently recoverable, such as a clear kanji typo or an isolated spelling drift contradicted by the rest of the work. Preserve character claims, inconsistent arithmetic, compressed chronology, and inferred implausibilities when the source supplies no corrected wording. In both cases, record the evidence and treatment at the exact source anchor rather than silently improving the story.

### Definite or probable source errors

1. **Marie’s surname**
   - introduction: `マリー・プロシオン` → **Marie Procyon**
   - ending: `マリー・プレシオン` → *Marie Presion/Plesion*
   - **Decision:** use **Procyon** throughout unless official packaging/manual evidence contradicts it; retain the ending variant in the restoration log.

2. **Cryosleep duration**
   - 1996 → 2288 is 292 years.
   - Script says “about 280 years.”
   - **Decision:** preserve **“about 280 years”** and disclose the contradiction. The archival translation records authorial arithmetic rather than silently making the physician more accurate.

3. **`確率された時代`**
   - In the doctor’s explanation, `確率` is almost certainly a typo for `確立`: the era in which the technology was **established/developed**.

4. **Repeated lines and paragraphs**
   - Some are authoring duplicates; others are branching copies. The generated control-flow graph proves reachability; canonical sharing still requires speaker and context review.

### Restoration log — locked entries

| Location | Source | Archival English treatment | Reason |
|---|---|---|---|
| `F0040.MES:0x40c8` | `約２８０年` (“about 280 years”) | **about 280 years** | The stated dates 1996 and 2288 are 292 years apart. Preserve the source figure and disclose the contradiction rather than repairing character dialogue. |
| `F0040.MES:0x4093` | `確率された時代` (“an era whose probability was...”) | **an era whose technology could perform your operation** | Read `確率` as the contextually recoverable typo `確立` (“established”). Preserve the exact typo in source and notes. |
| `FOP.MES:0x06f1`–`0x0f6d` | period English including `Dimention` and broken system-status phrasing | use the naturalized terminal copy in section 13 | The strings are already English, but consistent naturalization is clearer than a mixed typo-only pass. Preserve the exact source in catalog notes. |
| `F003410.MES:0x1077` | `コニー】` without an opening `【` | **[Connie]** | Restore the demonstrably missing opening speaker-tag bracket; adjacent records and the remaining name plus closing bracket establish the intended form. |
| `F0042.MES:0x1bf7` | `プレシオン` after earlier `プロシオン` | **Procyon** | Standardize an apparent spelling drift while retaining both source forms in QA notes. |

### Ambiguities to preserve

- Adult Kaori’s continued existence after younger Kaori is saved.
- The environmental warnings given to the Takano family should alter the ruined future, yet the epilogue still describes Kaori and Marie repairing the 2296 genome. The source does not say whether prevention is gradual, creates a branch, or changes a later future.
- Only eight years separate Kaori’s 2288 awakening from the 2296 mission. In that interval she recovers, enters university, studies medicine and genetics, joins the project, creates three-year-old Connie, and becomes project head. The chronology is implausibly compressed, but no alternate date is established.
- `F0040.MES:0x49cf` says that the Kanzaki couple who adopt Kaori are **her descendants** and caretakers of the old house. A childless sixteen-year-old entering cryosleep cannot have literal direct descendants; wider-family or older-sister descendants are plausible, but the source does not clarify.
- Exact expansion of the “D” in Project D.
- Whether `パラサイト銃` is a proper product name or an extraction/authorial oddity.

### Names requiring external confirmation

- reading of `良美`;
- any official Latin spelling for Remia, Marna, Procyon, and Connie.

---

## 11. Locked content and release policy

The canonical project goal is a source-faithful English translation of the 1995 work. Stated ages, school status, and the distinction between Connie's cellular age and three years of lived experience are part of the text, not distribution metadata, and remain intact in player-facing English as well as the archival fields.

Do not automatically replace ordinary `女の子`, `先輩`, `留学生`, `一日留学`, or Connie's biological/hunter diction such as `牝` with **woman**, **young woman**, or other age-marking language. Translate the social, school, or animal-register distinction the Japanese actually makes.

Catalog `context` and `notes` are archival metadata, not another player-facing localization layer. Describe the source scene neutrally there. Use adulthood language only where the story itself needs the distinction, such as adult Kaori versus her younger self; do not insert **adult** or **adult-aged** as a localization workaround.

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
- Preserve the ages and school status stated in the source.
- Do not embellish explicit content.
- Add strong upfront content warnings and restoration notes without presenting a warning as a change to the text.
- Keep every physical record and document corrections, normalizations, and technical compromises.

All present translation, speaker, context, and restoration work targets this archival English layer.

The English version must include this content note:

> This archival English translation preserves the ages and school status stated in the original Japanese work. The game contains sexual depictions of high-school-age characters, along with coercive and otherwise sensitive material described in the translation brief.

### B. Distribution-specific age override — not canonical

If a particular storefront or jurisdiction requires changed age statements, implement them as a small, reviewable override applied after the canonical catalog. The build must disclose that adaptation, keep it mechanically separable, and never write its altered claims back into the archival `translation`, `context`, or `notes` fields. Distribution review decides whether such a version is viable; linguistic QA does not pretend that changing a few numerals resolves the source's school setting or content.

### C. Story-focused rewrite — rejected

The project will not replace sample collection, remove route structure, or rewrite the game into a different story-focused edition. That would be an adaptation rather than preservation and is out of scope.

### Editorial invariant

Maintain one canonical source-faithful English catalog. Keep any distribution adaptation explicit and mechanically separate, and do not use content notes as cover for unrelated or undocumented censorship.

---

## 12. Suggested translation workflow

### Phase 1 — Reconstruct the executable script model

- Keep the recovered five name slots and their `0x45`/`0x4b` interpolation spans under regression test.
- Keep semantic labels and fixed-slot constraints for the two customizable-term slots under regression test.
- Generate the scene/choice graph from bytecode; do not hand-maintain it.
- Identify textbox limits, encoding, line breaks, control codes, delays, and CG triggers.
- Confirm which repeated records are separately reachable.

The 61-column F0001 story window has direct framebuffer proof for a three-row
message (`launch-humans-ended-mutants`), and the numbered story scripts retain
that declared layout. It is not a game-wide upper envelope. Static recovery of
`SILK.MES` found full-page cards, two-, three-, and four-row horizontal panels,
plus Koi Hime's two-column vertical cards. Targeted emulator probes confirmed
that text exceeding a two-row Silky panel scrolls out of view and that ordinary
word wrapping is unsuitable for the vertical card. The canonical catalog now
records those surface-specific widths and row counts, preserves deliberate
newlines between adjacent text opcodes, and uses character-cell wrapping only
for the vertical card. Remaining terminal, editor, and special card surfaces
still need their own route-specific QA.

### Phase 2 — Extend the canonical TOML catalog

For every record, preserve:

- MES file and offset (`F0001:0704`);
- raw Japanese;
- resolved variable placeholders;
- canonical speaker identity and `proven` or `inferred` attribution evidence;
- route/state condition;
- draft English;
- translator note;
- QA status.

Keep enforcing the implemented schema-7 scene, speaker, composite-entry, and
token contract from section 6. `translations/fermion.toml` remains
authoritative. TSV, JSONL, CSV, or SQLite are generated translator views with a
validated import path; they must never become parallel canonical databases.

### Phase 3 — Apply the locked glossary and policies

The following decisions are already locked and should be enforced during review:

- **Procyon**, **Mini form**, **Time Patrol**, **temporal inspector**, and the speaker-scoped **Time Quake** / **space-time oscillation** split;
- **capture gun** for `パラサイト銃`, **tranquilizer gun** for `麻酔銃`, and **anti-mutant capture drug** for `対ミュータント用捕獲薬`;
- **cryosleep** for `コールドスリープ`, with **suspended animation** only where `冷凍睡眠` supplies the explanatory gloss;
- no romanized honorific suffixes;
- Yuki, Ruri, Kanako, Yoko, and Hiroko as reset-name romanizations;
- free-form full-width Latin name and adult-term editors; and
- source-faithful age and school-status wording in the canonical catalog.

Voice-calibration examples belong in anchored canonical catalog entries with source, context, and notes. Do not create a second table of free-floating “final” translations inside this brief.

### Phase 4 — Main-story spine status

The original authoring order was FOP, F0000, F0001-F0003, the remaining early
branches, the facility and ending, and finally the extra UI/catalog surfaces.
That sequence is historical guidance, not the current work queue. At this
checkpoint:

1. FOP through the F0042 ending are translated and structurally built. All 21
   focused story scopes are closed with no pending or excluded story anchors.
2. Scene replay, both mirrored name and adult-term editors, the title/menu
   surfaces, and the period Silky's catalog are represented in the canonical
   catalog or explicitly source-anchored coverage exclusions.
3. The catalog contains 12,902 canonical records over 17,680 physical anchors
   in 76 MES files: 12,611 `translated`, 276 `reviewed`, and 15
   `runtime-verified`.
4. The remaining work is dedicated linguistic review of the still-translated
   records plus in-engine route QA beyond the early FOP/F0000/F0001 fixtures,
   including representative maximum-length name and adult-term values. Structural completion is
   not a substitute for either pass.

Continue to work in source-order slices when practical so adjacent voices and
route state remain visible, but do not describe already covered files as
untranslated.

For each slice, “done” requires all of the following:

1. Every covered record is translated or explicitly excluded, and every changed line has been checked against its anchored Japanese and scene context.
2. Locked-term and forbidden-variant searches are clean, including split or punctuated forms such as `コールド・・・スリープ`.
3. A register pass samples every speaking character and compares basic diagnostics such as contractions, sentence openings, and repeated stock phrasing with adjacent finished slices. These are drift detectors, not quotas.
4. Context and notes remain source-facing, and every refusal, observed action, and narrator interpretation stays at its own evidence level.
5. Catalog validation, complete coverage, the policy regression tests, and a fresh-image build all pass before the slice is committed.

Generate the register leads with:

```sh
fermion translation drift translations/fermion.toml --only-flagged
```

Its same-speaker medians expose cross-file drift while preserving the catalog's
distinction between contextual and bytecode-proven speaker attribution. Read
every flagged line in Japanese and scene context before changing it; a formal
character can be a legitimate outlier.

### Phase 5 — Review passes and in-engine QA

Run distinct passes rather than treating “edited once” as completion:

1. **Source and linguistic pass:** verify meaning, register, and terminology against the exact anchored Japanese.
2. **Reveal pass:** make every early clue work retrospectively without letting metadata or wording spoil Kaori’s identity.
3. **Variable pass:** exercise defaults and representative custom name and term values, including maximum-length input and English punctuation around tokens.
4. **Editorial pass:** audit content warnings, confirm stated ages remain source-faithful, and verify that any distribution adaptation is documented and mechanically separate.
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

**English-version content note:** use the locked wording in section 11 ("The
English version must include this content note") verbatim.

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
- [ ] Apostrophes, commas, articles, and surrounding spaces remain grammatical for representative custom values.
- [ ] No systematic romanized honorific suffix survives; titles and kinship terms follow the locked English policy.
- [ ] Custom values are exercised in ordinary story text, the identity reveal, final letter, save data, and replay/gallery surfaces.
- [ ] **Connie Kanzaki** appears only where the ending intends it and is not normalized backward through the script.

### Terminology and voice

- [ ] Connie consistently uses **Time Quake** and **Time Quake frequency**; scientists’ formal **space-time oscillation** terminology and the machine’s ordinary hull vibration remain distinct.
- [ ] Genetic exposition distinguishes missing information from simplistic “normal” or “superior” genes.
- [ ] **Procyon**, **Mini form**, cryosleep terminology, and the logged 280/292-year contradiction remain consistent.
- [ ] **Time Patrol**, **temporal inspector**, **capture gun**, **tranquilizer gun**, and **anti-mutant capture drug** follow their locked source distinctions.
- [ ] Connie sounds procedurally competent without becoming a theoretical physicist or a generic catgirl.
- [ ] Kaori’s public/private/reveal registers, Marie’s grief, Remia’s peer voice, and Marna’s sincere deference remain distinct.
- [ ] Refusal and negative utterances are translated accurately rather than softened into manufactured assent.
- [ ] Spoken refusal, observed action, and narrator interpretation remain distinct evidence levels.

### Engine and presentation

- [ ] Only proven interpolation spans are merged in translator views; every physical record, silent beat, and opcode span remains anchored.
- [x] Exact Japanese duplicates are shared only after speaker, attribution evidence, meaning, and route context agree; mechanical splits are annotated.
- [ ] Literal `\n`, explicit line breaks, full-width/half-width Latin text, and one-glyph terminal animation are tested in engine.
- [ ] L/R branches reach the verified destinations, and facility nodes are tested through actual navigation rather than filename order.
- [ ] Long technical explanations, the mother’s deduction, the Marie/Akira exposition, and epilogue cards fit their message windows.
- [ ] Maximum-length names and terms wrap safely without corrupting control flow or save compatibility.
- [ ] Gallery unlocks, scene replay, name editor, term editor, and return-to-menu behavior remain functional.

### Editorial and release

- [ ] The English release includes the locked content warning for high-school-age sexual material.
- [ ] The canonical translation preserves stated ages, school status, and source meaning without embellishment or undocumented censorship.
- [ ] Any distribution-specific age override is disclosed and mechanically separate from the canonical catalog.
- [ ] Catalog context and notes do not introduce age framing absent from the source.
- [ ] Every restoration intervention is logged at its source anchor.
- [ ] Automated policy assertions cover every locked restoration entry and the highest-risk glossary invariants.
- [ ] Content warnings cover high-school-age sexual material, coercive consent framing, family/incest-adjacent dynamics, adultery, abduction, reproductive coercion, medical abuse, grief, death, and gun violence.
- [ ] Distribution and platform review are completed independently of linguistic QA.

---

## 16. Evidence questions and highest-priority unresolved tasks

### Questions requiring executable, visual, or external evidence

1. What official Latin spellings, if any, exist for Connie, Remia, Marna, Procyon, and the reading of 良美?
2. Is `パラサイト銃` visibly named in art, packaging, or a manual? Until such evidence appears, the functional script reading remains locked as **capture gun**.
3. Do condition flags expose a bad ending, game-over exit, or prerequisite not captured by the recovered inter-MES transition graph?
4. Which remaining terminal, editor, or special-card surfaces differ from their declared limits? The mixed Silky catalog surfaces are now mapped, but not every other UI route has visual proof.
5. Does original documentation explain the intended time-travel model or the in-world meaning of **FERMION**?

### Highest-priority implementation and research tasks

1. Exercise defaults and representative maximum-length custom names and terms in
   story, final-letter, unlocked replay, and gallery contexts during the human
   playtest.
2. Confirm the official readings/spellings of 良美, Remia, Marna, Procyon, and Connie from non-script materials.
3. Check manuals, packaging, and art for evidence about `パラサイト銃`; revise the locked functional translation only if that evidence proves a proper name.
4. Measure and visually verify the remaining terminal, editor, and special-card limits beyond the proven F0001 dialogue and mapped Silky catalog surfaces.
5. Complete final in-engine route QA and reconcile every logged restoration or ambiguity with the release notes.
