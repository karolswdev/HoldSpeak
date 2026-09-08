# The daily Project workflow -- the settled design (Phase 200, HS-200-09)

> **SETTLED against `feat/phase-200-g0` (2026-09-06), the baseline
> `bea4176c2f7e5a5709e3404e517bd0790d2fe7b2` that BASELINE.md attests.
> Counsel BOUNCED the 2026-09-06 draft
> (`assets/counsel-on-design-200-09.md`: P0-1..P0-4, C1--C21); the
> orchestrator RULED, and this document was REWRITTEN to those rulings
> rather than annotated around them. **Counsel's re-read:
> RATIFY-WITH-CONDITIONS -- N1, N2 and two notes, all ruled accepted
> and applied.** The addendum at the end records every condition and
> where it moved. The owner's word on the canvas is the exit of this
> story.**

Twenty-two artboards ride with this document in `assets/mockups/`
(`canvas.json` lays them out in seven rows, one row per posture plus
the library). Every board is 1440 or 393 on the ratified 170 shell
chrome. Every verb on every board is the library Button. No face
carries a sentence.

The face canon binds (`docs/internal/UX-CANON.md`): every verb the
library Button (A.1), design before build (A.2), no prose (A.3), no
modals (A.4), one screen where one will do (A.5), the name said once
per face (A.7), no counters of zero (A.8), egress exactly where egress
happens (A.9), honest states with plain reasons (A.10), a verb that
does nothing is a lie (A.11). The species canon binds
(`web/src/desk/surface/contract.md`). The type steps bind (canon C:
display 26/650 once per face, primary 15/600, body 13, secondary 12
mono, caption 11 mono uppercase; at least three steps per face).
Constitution articles III (local first), IV (voice first-class), V
(consent), VI (honest by construction) and XI (kernel receipts) bind
every line below.

Phase 200's contracts bind: C2 (claim meaning), C3 (evidence manifests
and working context), C4 (coverage and attention), C5 (prepared recipe
configuration), C6 (setup transactions and recovery), C11 (shared
experience and interfaces).

**Every `file:line` below was read on this branch, and every citation
counsel corrected has been re-verified line by line** (C21). Where
something is NOT built, this document says MISSING rather than
describing it as though it exists -- and counsel found four places
where the first draft broke that promise. They are fixed in D3.

---

## D0 -- the Tuesday moment

It is 9:12 on a Monday. He opens the desk.

The arrival says **`17 need you across 3 projects`** -- the true total,
in the one big word on the screen. Above the list it says
**`COVERAGE · 6 OF 8`**: jira KAN could not be checked (`CANT CHECK ·
JIRA REJECTED THE QUERY`, observed 08:41, `Reconnect`), and confluence
PLATFORM is mid-check. He can see that the seventeen are seventeen out
of what was readable, not seventeen out of everything. The section
caption says **`NEEDS YOU 5 OF 17`**: five rows, ranked overdue first,
each with a reason, a source, its Project and one verb, then
`12 MORE · Show all`. He is not reading a queue. He is reading a
decision about where to start.

*(On his actual desk today it reads `3 need you` with no Project token
at all, because he has one active Project. That is board
`P2ArrivalOne`, and it is beat 1 of his walk.)*

He starts with the 11:00 architecture review. He opens the Room --
*Cut the payments platform over without an incident* -- and speaks into
the ask well: *"architecture review, cut-over sequencing."* The mic is
on the field, as it is on every field. He cycles `Result` to
`Preparation brief` and presses `Prepare`.

The route says `READY · QWEN3 35B · 192.168.1.43 · LAN` beside the
verb, so he knows where the words go before they go. The run shows five
real steps and keeps `Stop` visible; the per-source read detail lives
inside the `ACTIONS 4` disclosure, not on the face.

The brief arrives in 11.4 seconds. Two things to decide, two things to
ask. Under it, four claims, each on three independent axes: the
cut-over decision is `DECISION · SUPPORTED · ACCEPTED`; Priya's figure
is `INFERENCE · LINKED · UNREVIEWED` with `DEADLINE 2026-12-31 · NO
SOURCE` and `NUMBER 95% · NO SOURCE` -- values printed, and printed as
unsupported; the velocity sentence is `INFERENCE · UNSUPPORTED ·
UNREVIEWED` and carries `NO SOURCE` with `Find support` rather than a
citation it does not have. `NOT READ 1` says confluence PLATFORM was
omitted, and why. He presses `Keep`.

At 11:47 the meeting ends. The desk reads it and offers five
proposals -- two decisions, three commitments -- each tagged `PROPOSAL`
with its transcript span and its support, and each unknown left unknown
(`OWNER · UNKNOWN`, `DUE · UNKNOWN`). Each row carries one verb,
`Confirm`, with `Edit`, `Dismiss` and `Open evidence` behind its `MORE`
disclosure. He confirms three, edits one in place, dismisses one.

Tuesday morning he cannot remember which freeze window won. He types
*freeze window* into Desk memory. The current decision comes back
accented, with its rationale, its source (`MTG 09-07 · 11:31`), its
Project and `Carry into brief`; the Saturday version sits under it,
dimmed, `SUPERSEDED BY DEC 09-07`. One ref, under a minute.

Wednesday the LAN engine is down and the confluence credential has
expired. The desk says `3 to repair`, names each reason with its own
provider, gives each the same verb for the same failure class, keeps
the unfinished ask with its purpose and its saved time, and keeps the
items it last observed at 08:41 stamped as such. Nothing is silently
retried, nothing silently disappears, nothing reads green that is not.

That is the loop: **ask · return · prepare · review · recall ·
recover.** Six postures on the surfaces that already exist.

---

## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| Coverage rides above the answer, never under it | C4; UX-CANON A.10 | Coverage is stated between the head and the first result on **every** posture that reads sources -- postures 1, 2, 3 and 4, in every state including refused. A face that omits it clears a known gap by omission |
| **A face that lists every source states coverage as a TOKEN, not a second section** | canon D (one object, drawn once); ruling N2 | Where the face already draws a `SOURCES M` ledger, the head carries `COVERAGE · N OF M` and the gap is marked in **that one ledger row** -- its own state chip, its `OBSERVED hh:mm`, and its repair verb, drawn raised. A `COVERAGE` section above it would draw the same source twice. The arrival and the meeting faces KEEP their `COVERAGE` section because they list no sources of their own |
| **`N` in `N OF M` is the count in state `available`** | C4; `needs_you_aggregate.py:52`; ruling on P0-4 | A stale-but-read source is NOT in `N`. `N == M` is therefore unreachable while the read is incomplete. The head states coverage only when it is COMPLETE; when it is not, the section states it and the head does not say the same fraction twice |
| **The display line is the TRUE total; the caption carries the cap** | `README.md:60-62`; ruling on P0-2 | `17 need you across 3 projects` in the one display element; `NEEDS YOU 5 OF 17` in the section caption; `12 MORE · Show all` as the remainder row. The biggest word on his screen is never the cap |
| An empty COMPLETE result is an all-clear; an empty PARTIAL result is not | C4; `ChairHome.tsx:247-254` | `headlineFor` already rules it: `Nothing needs you` only when `complete`, `Coverage incomplete` otherwise. **The wording as HS-200-07 shipped it stands**; concern 4 is his ear, not this design's edit |
| A missing source cannot lower a known item's severity by disappearing | C4 | The item stays, stamped with the observation it came from (`ChairHome.tsx:848-855`, `fromLastObservation`). Board `P6Repair` draws it as `STILL TRUE` |
| The three claim axes are independent | C2; `project_update_service.py:90-127` | Kind, support and acceptance are three chips, never one. A model score can raise support and can never raise acceptance |
| A valid reference establishes source linkage only | C2 | `LINKED` is not `SUPPORTED`. `LINKED · MIGRATED` says a pre-HS-200-06 record was mapped conservatively and never that a human reviewed it |
| **An unsupported value is printed AND typed unsupported** | C2 ("names, deadlines, numerical measures ... require explicit source support"); ruling on C10 | `DEADLINE 2026-12-31 · NO SOURCE`, `NUMBER 95% · NO SOURCE`, `OWNER · UNKNOWN`. Never a hedged guess (`PRIYA?`), never a bare value in a warning chip that reads as a fact |
| No source, no source chip | UX-CANON A.8, A.11 | A claim with no reference shows `NO SOURCE` and `Find support`, **at both widths**. It never shows an empty chip and never an `Open source` that opens nothing |
| **One filled primary per face** | UX-CANON A.1; ruling on C15 | Exactly one Button on a face is drawn primary, and it is the action the face is FOR. Every other verb is ghost or raised, dense on a row |
| **One verb per row; its secondaries live in the row's `MORE` disclosure** | canon D (one row grammar per species); ruling on C15 | `Confirm` on the row, `Edit`/`Dismiss`/`Open evidence` inside `MORE`. `Resume` on the row, `Discard` inside `MORE` |
| **The way back to the originating Project is on every posture** | story 09 AC2; ruling on C8 | The Project is a library `Button` inside a `role="group"` region (canon D), on every face of every posture, withheld only when the desk holds one Project. A write (`Confirm`, `Carry into brief`) is never named as a way back |
| **A refused primary is DRAWN refused** | UX-CANON A.11; ruling on C9 | `disabled` + `aria-disabled`, flat, dashed, muted -- never byte-identical to the enabled verb. One refusal, one grammar, on both refusal boards |
| **One failure class, one verb, one token** | UX-CANON A.10, canon D; ruling on C17 | An expired credential is `CREDENTIAL EXPIRED · <PROVIDER>` with `Reconnect`, wherever it appears. A rejected query is `<PROVIDER> REJECTED THE QUERY` with `Reconnect`. The token names its own provider, never another's |
| Every text input takes his voice, click to toggle | Article IV.1; UX-CANON B; owner ruling | `MicButton` (`web/src/desk/components/MicButton.tsx:42`) trails inside every `StringGadget` and sits in every `PadGadget` corner. Toggle at `:362-370`; never press-and-hold. Unavailable is NAMED (`:159-177`). **Its accessible name is `Dictate into <field>`**, never the field's own name (ruling on C16) |
| One mic authority per face | Article IV.3 | `Talk` owns the desk floor; inside a window the field mics own their fields and no transport competes |
| Execution detail lives in the Actions disclosure, off the primary line | C11; ruling on H5 | The per-source read, the model call, the retry -- inside `Disclosure` (`patterns/Disclosure.tsx:13`), on its own line above the route and the primary. Requests for input, refusals, failures and useful results stay on the face |
| Primary actions stay visible while loading, failing and reviewing | C11 | `Stop` on a run, `Set up model` on a refusal, `Accept reviewed` on a review. A face never goes verbless |
| Generated content belongs in a document surface | C11 | The brief's prose is `Material` (`Material.tsx:82`); the claims are a ledger beneath it |
| Egress exactly where egress happens -- and only there | Article III; UX-CANON A.9; ruling on H1 | `EgressChip` beside the verb that sends, and in the footer of a face that HAS sent. A face that has sent nothing carries `THIS DEVICE` or an empty egress slot, never a decorative host chip |
| The name said once per face | UX-CANON A.7; ruling on C14 | The window's subject is in the title bar and nowhere else. A head token line never repeats it; an empty state never repeats its own display line as a token |
| One display element per face | UX-CANON C | One 26/650 line, and it is the one big honest fact |
| No modals; edit in world | UX-CANON A.4 | The ask well unfolds in the Room. `Edit` on a proposal is `EditInPlace`. `Discard` is `ConfirmVerb` |
| A verb that does nothing is a lie -- including one that leads where you are | UX-CANON A.11; ruling on C13 | `Open source` is withheld where there is no source; a footer verb never names the wing that is already active |
| Reading the desk creates no external effect | C4 | Arrival, brief, recall and repair faces are reads |
| A replacing face keeps its verbs | 175 law | Every face this design touches keeps the verbs it has today |
| Recurring elements are ADDED to the library, never invented twice | UX-CANON B | Six species are owed to `contract.md` before stories 10--12 and 15 write a control. D2.0 lists them |
| Design before build | UX-CANON A.2 | This document plus its twenty-two artboards. His word gates the build |

---

## D2 -- the faces (element by element, species named)

### D2.0 -- the library FIRST (before any feature-specific control)

Canon B: *a recurring element a face needs and the library lacks is
ADDED to the library, documented in contract.md, then used -- never
invented inline.* Board: **`Library.dc.html`**, which now draws a true
specimen for every row.

**Reused exactly as they are (24).** Nothing below is modified by this
design.

| Species | File | Where this design uses it |
|---|---|---|
| `Button` (primary / ghost / dense / **unavailable**) | `web/src/components/signal/Signal.tsx:21` | Every verb on every board |
| `MicButton` | `web/src/desk/components/MicButton.tsx:42` (shim `desk/surface/controls/MicButton.tsx:3-4`) | Every text input |
| `StringGadget` | `web/src/desk/surface/gadgets.tsx:237` | Purpose · search |
| `PadGadget` | `gadgets.tsx:309` | A purpose that must wrap at 393 |
| `CycleGadget` | `gadgets.tsx:137` | The recipe pick (a closed set of three) |
| `CheckGadget` (`variant="token"`) | `gadgets.tsx:79` | Source scope on the prepare well |
| `EgressChip` | `gadgets.tsx:736` | The route, and the footer of a face that has sent |
| `StateChip` | `patterns/StateChip.tsx:35` | Coverage · support · run state |
| `ProvenanceChip` / `Receipt` | `patterns/ProvenanceChip.tsx:6,36` | The source ref on a claim |
| `CitationChips` / `openSourceRef` / `sourceLabel` | `citations.tsx:48,25,20` | `Open source` on a claim |
| `Disclosure` | `patterns/Disclosure.tsx:13` | `ACTIONS` · `MORE` · the dedup sources |
| `ProgressPlan` | `patterns/ProgressPlan.tsx:23` | The run, and only what genuinely runs |
| `SurfaceSection` | `Surface.tsx:105` | Caption + count, never zero |
| `SurfaceLedger` / `SurfaceLedgerRow` | `Surface.tsx:762,793` | Attention · sources · claims · unfinished |
| `SurfaceIdentity` | `Surface.tsx:51` | The head: one display line over its token row |
| `SurfaceState` | `Surface.tsx:202` | The one empty / loading / error treatment |
| `SurfaceWell` | `Surface.tsx:422` | The ask well · the search well |
| `SurfaceFooter` | `SurfaceFooter.tsx:6` | Egress · receipt · verbs |
| `SurfaceWings` | `wings.tsx:41` | `ROOM`/`HISTORY`; `SEARCH`/`UNFINISHED`/`REPAIRS` |
| `Material` | `Material.tsx:82` | The brief's generated prose, in a document surface |
| `EditInPlace` | `Surface.tsx:1063` | Correcting a claim or a proposal in world |
| `ConfirmVerb` | `Surface.tsx:1188` | `Discard` -- one step, in world |
| `ScrollHint` | `Surface.tsx:1302` | Every scrolling well |
| `FilterTokens` | `FilterTokens.tsx:37` | The recall filter strip (promoted in 176) |
| `countToken` / `countLabel` | `count.ts:12,25` | The one way a face renders a count |
| `useRovingRows` | `roving.ts:34` | Up/Down inside every ledger |

**Two of those reused species are not in `contract.md`** (C19):
`EditInPlace` (`Surface.tsx:1063`) and `ConfirmVerb`
(`Surface.tsx:1188`). Canon B's documentation is owed for both. The
`Library` board flags them in warning ink.

**Owed to the library (6).** Each is drawn two or more times across the
six postures. Each must be added to `web/src/desk/surface/` and
documented in `contract.md` BEFORE the story that would otherwise
hand-roll it a second time. Each now has an owning story AND an
acceptance criterion (C12; see Sizes).

| # | Species | Why it is owed | Built today, inline, at | Owning story |
|---|---|---|---|---|
| S1 | **`CoverageLedger` / `CoverageRow`** | The coverage projection now appears on eleven boards across postures 1, 2, 3 and 4. One grammar: emblem · label · reason · state chip · `OBSERVED hh:mm` · repair verb | `ChairHome.tsx:902-940` (section), `:946-976` (`CoverageVerb`), `:895-900` (`coverageEmblem`); the vocabulary at `web/src/desk/coverage.ts:8-13`. Note `ChairHome.tsx:923-929` draws the token as a raw `<span className="arrival-why-token">` while `ConciergeCore.tsx:275-278` uses `StateChip` for the same fact -- converge on `StateChip` inside the promotion | 15 (promote), consumed by 11 and 12 |
| S2 | **`ClaimAxes`** | The three-chip triple appears in the brief (P3), the meeting review (P4) and recall (P5). It is currently reachable only from the update posture | `UpdatePosture.tsx:141` (the `hasAxes` gate), `:145-171` (the three chips + unknowns); tokens at `update/model.ts:141-196` | 11 (promote), consumed by 12, 13 |
| S3 | **`RepairRow`** | Built TWICE already for one idea. Postures 1, 2, 3, 4 and 6 all show it | `ConciergeCore.tsx:247-291` and `ChairHome.tsx:946-976` | 15 (promote one; retire the duplicate in a later story) |
| S4 | **`SurfaceLedger` cap + remainder** | The true total in the head, the cap in the caption, the remainder as a real count with a real verb. Unbuilt for attention | `ChairHome.tsx:1169` (`BRIEF_CAP = 3`), `:1181-1182`, `:1220-1227` -- the identical pattern, for the brief only | 15 |
| S5 | **`TaskResume`** | The saved ask with its state, its custody token and its ONE verb appears in postures 1, 3 and 6. Today return-to-task is an EVENT with no face | Event `holdspeak:settings-updated`, consumed `web/src/pages/cores/dictation/SpeakFace.tsx:288-289` and `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:211-212`, dispatched `web/src/features/concierge/useConciergeController.ts:487` and `web/src/pages/cores/SettingsCore.tsx:890` | 10 |
| S6 | **`ProjectButton`** | The way back to the originating Project, on every posture (C8). Drawn today as a decorative token on six boards and absent on fifteen | Nothing; `ChairHome.tsx` renders the Project name as inert text | 15 (promote), consumed by 11, 12, 13 |

**Two canon residues on surfaces this design uses**, counted and
located as counsel corrected them (C20):

- **A raw `<textarea>`** at `web/src/desk/components/ThreadComposer.tsx:968`, self-flagged by
  the comment at `:966`. This is a **mic-law site the scanner cannot
  see** (`ux_canon_scan.py` does not match `<textarea>` -- the 176 C9
  finding). It is carried in the ceiling under rule `B`, not `A1`.
- **Two raw `<button className="desk-chip">`** (`Stop`, `Send`) at
  `web/src/desk/components/ThreadComposer.tsx:985-1004`. Rule A.1. This is a **separate**
  residue from the textarea.

Both must be paid by whichever of stories 10--12 touches the Thread
first, with an AC naming them (C12).

- Thread draft custody is **in-memory only**
  (`web/src/desk/threadComposerDrafts.ts:5-15`, cleared at
  `web/src/desk/threads.ts:889-890`). **Ruling R2:** the face states the
  limitation with the token `DRAFT NOT SAVED` (drawn on `P6Repair` and
  `P6Phone`) unless persistence proves trivial, and **story 10 gains
  the AC** -- the phase's only other draft AC is 28 AC1, at G3, which
  is too late to carry it.

---

### D2(a) -- Posture 1: the first architecture result

**Boards:** `P1Ask` (1440, empty) · `P1Running` (1440, loading) ·
`P1RouteUnset` (1440, refused) · `P1Phone` (393, the same face).

**Where it lives.** The Project Room, `ROOM` wing, in the existing
sticky ask well (`ProjectRoomCore.tsx:1378-1476`). No new surface.

**Elements, in order.**

1. **Title bar** -- the Project's outcome, said once, `min-width:0`
   ellipsis. Wings `ROOM` / `HISTORY` (`SurfaceWings`, `wings.tsx:41`).
2. **Head** (`SurfaceIdentity` recomposed) -- ONE display line, the
   outcome of the face: `Nothing prepared yet` · `Preparing` ·
   `Cannot prepare`. Beneath it a token row that opens with the
   **`ProjectButton`**, then the face's own facts (`CHECKED 2 MIN
   AGO`; `RUNNING · 00:38 · MANIFEST FROZEN`; `PURPOSE KEPT · NOTHING
   SENT`). It never repeats the title bar and never repeats the
   coverage fraction the section below states.
3. **`COVERAGE · N OF M`** -- a head TOKEN, not a section (N2). This
   face lists every source below, so the gap is marked once, in its own
   `SOURCES` row: its reason, its state chip, `OBSERVED hh:mm` and its
   repair verb drawn raised. The token is present in every state,
   refused included.
4. **The ask well** (`SurfaceWell`), unfolded in world, never a modal:
   - `Purpose` -- `StringGadget` with its `MicButton` trailing inside,
     accessible name `Dictate into Purpose`. Pre-filled from a linked
     meeting's title when one exists; otherwise typed or spoken.
     **Never blocked on a calendar** (story 11 AC1; the owner has zero
     calendar sources).
   - `Result` -- `CycleGadget` over exactly the three C5 recipes:
     `Preparation brief` · `Decision and commitment review` ·
     `Weekly Project update`.
   - The route line: `StateChip` + the model token + `EgressChip`,
     then the one filled primary `Prepare`. **The egress chip sits
     beside the verb that sends.** When a refusal row is present the
     route chip is WITHHELD from this line: the reason is named once,
     on the row that carries its repair verbs.
5. **`SOURCES M`** -- once per face, drawing **all M rows**. Each row:
   52px emblem (`GH` · `J` · `MTG` · `CAL` · `CNF`), the source name at
   primary step, its facts, its state chip, its observation and its
   verb.

**The five states.**

| State | Face | Verbs kept |
|---|---|---|
| **Empty** | `Nothing prepared yet`; the well is present and usable; the head token reads `COVERAGE · 3 OF 4`; `SOURCES 4` draws four rows and the Calendar row carries `UNAVAILABLE · OBSERVED NEVER · Connect calendar` | `Prepare` (the one primary) |
| **Loading** | `Preparing`; `ProgressPlan` with five REAL steps (`READ SOURCES` · `FREEZE MANIFEST` · `DRAFT` · `SUPPORT CHECK` · `REVIEW`); `ACTIONS 4` disclosure on its own line above the route | **`Stop` stays visible** (C11). The purpose stays visible and editable |
| **Partial** | The head token plus the marked row in `SOURCES`, present in every state, naming each non-available source with its repair verb | The missing source's own verb |
| **Failed / refused** | `Cannot prepare`; `COVERAGE · 3 OF 4` still in the head and the gap still marked in `SOURCES 4`; the named reason in a warning-bordered row (`KEY NOT SET`); `PURPOSE KEPT`; `NOTHING SENT`; **`Prepare` drawn `disabled` + `aria-disabled`**, dashed and muted; `THIS DEVICE` in the footer | `Set up model` (the one primary, returns here) + `Write it myself` |
| **Resumed** | Drawn on `P6Resume`: `RESUMED AFTER RESTART`, `SAVED 09:04`, readiness re-read (`41 MS`), the purpose intact | `Resume` |

**Voice.** `Purpose` carries `MicButton` inside the field, accessible
name `Dictate into Purpose` -- never the field's own name, so a screen
reader does not announce two controls called "Purpose" (C16). Click to
toggle (`MicButton.tsx:362-370`). Dictated text APPENDS and never
submits (Article IV.2).

**Keyboard.** Tab order: Purpose field, its mic, Result cycle, Prepare,
then the COVERAGE rows, then the SOURCES rows in document order (each
row's verb is one stop). `Enter` in Purpose runs `Prepare` when the
field is non-empty and the verb is enabled (the composer precedent,
`web/src/desk/components/ThreadComposer.tsx:875-883`). `Escape` in Purpose clears the
uncommitted edit and leaves focus in the field; `Escape` on the mic
stops the session (`MicButton.tsx:135-147`).

**Accessible names.** `Purpose`; `Dictate into Purpose`; `Result --
pick the recipe`; `Prepare -- run the preparation brief`; when refused,
`Prepare -- unavailable until a route is ready` on the disabled
control; `Stop -- end this run`; `Set up model -- open Models and come
back`; `Write it myself -- keep the purpose, draft by hand`; per row
`Open -- <source>` / `Retry -- <source>` / `Reconnect -- <source>` /
`Connect calendar -- Calendar`; `Open the Project -- Q4 platform`.
**Every button on every board carries one** (C16).

**Focus return.** `Prepare` moves focus to the run region
(`role="status"`), which announces the step changes. `Set up model`
opens the Concierge window; on its `Apply` the window closes, the ask
well refreshes readiness WITHOUT a reload, and **focus returns to
`Prepare`**. That is the missing half of return-to-task: the state half
exists as an event (`web/src/pages/cores/dictation/SpeakFace.tsx:288-289`), the focus half does not
(D3, MISSING; AC owed to story 10).

**Disclosure.** `ACTIONS n` holds the per-source read, its latency, the
skipped sources and the model call. It sits on **its own line**, above
the route and the primary. Closed by default; `Escape` closes it and
returns focus to its trigger (`Disclosure.tsx:66-79`).

---

### D2(b) -- Posture 2: returning priorities

**Boards:** `P2Arrival` (1440, the many-Project case) ·
`P2ArrivalOne` (1440, **his desk** -- one Project, the token
withheld) · `P2ArrivalPhone` (393, the same face) ·
`P2ArrivalQuiet` (1440, the complete all-clear).

**Where it lives.** `web/src/desk/chair/ChairHome.tsx`, the `Arrival`
face (declared at `:345`). No new surface.

**Elements, in order.** Head (display + the ranking rule + the calendar
state and its verb) · `COVERAGE n OF m` · `NEEDS YOU 5 OF 17` · the
remainder row · `BRIEF` · the existing Thoughts / Meetings / Agents
sections · the capture bar.

**What changes from what is built.**

1. **The true total, then the cap.** The display line carries the true
   total (`17 need you across 3 projects`); the section caption carries
   the cap (`NEEDS YOU 5 OF 17`); the remainder row carries
   `12 MORE · Show all`, absent when there are none (A.8). Today
   `unmutedItems` is every merged item with no cap
   (`ChairHome.tsx:436-447`; rendered `:812` with no `.slice`).
2. **The ranking key, complete, and stated on the face.** The head
   token reads `RANKED · OVERDUE · DUE TODAY · NOT RUN · NO DUE DATE ·
   WAITING` on **every** board that ranks, and the full key is:

   | Rank | Class | Ordered within the class by |
   |---|---|---|
   | 1 | Overdue | Most overdue first |
   | 2 | Due today | Earliest due time first |
   | 3 | **Not run** -- a meeting owed a review | Oldest meeting first |
   | 4 | **No due date** | Most recently changed first |
   | 5 | Waiting (a future due date, or none applicable) | Longest waiting first |
   | -- | Tie-break, in every class | The stable item id (`_item_id`) |

   **`NOT RUN` is the class his desk actually has** (ruling N1): six
   meetings, zero decisions, and meeting intelligence run zero times
   (BASELINE.md). Without it, the one row he will act on every day
   falls into `WAITING` and sorts last.
   Severity is NOT a sort key: it is carried on the row's reason token
   in its own ink (danger / warning / muted) and it never reorders a
   class, so a failing source cannot lower a known item by
   disappearing (C4).
   `P2Arrival`'s five rows are drawn in exactly this order:
   `OVERDUE · 2 DAYS` · `DUE TODAY` · `NO DUE DATE · CHANGED 40 MIN
   AGO` · `WAITING · 3 DAYS` · `WAITING · 1 DAY`.
   **`P2ArrivalOne` obeys the same key**, and because his desk has a
   `NOT RUN` meeting it opens with one: `NOT RUN · 2 DAYS` ·
   `NO DUE DATE · CHANGED 40 MIN AGO` · `WAITING · 3 DAYS`. Its one
   filled primary is `Run intelligence`, the top row's verb.
   **The dedup key is not a blank sheet:** `_item_id`
   (`needs_you_aggregate.py:135-143`, docstring *"A stable id for one
   attention row, for dedup and reconciliation"*) exists with **zero
   callers**. Story 15 wires it rather than inventing one.
3. **Dedup, drawn.** One obligation projected by meeting, Watch and
   commitment is ONE row whose sources are traceable in a
   `2 SOURCES` `Disclosure` on the row (`P2Arrival` and
   `P2ArrivalPhone` draw it on *Priya confirms the freeze window*).
   Story 15 AC3's "traceable sources" now has a face.
4. **Coverage above the list.** `CoverageSection` already renders only
   when `!coverage.complete` (`ChairHome.tsx:667-676`) and already sits
   above `NEEDS YOU` (`:679`). That order is kept, and the `CHECKING`
   state is its own row rather than a spinner.
5. **The row grammar, one at both widths.** 1440: emblem 52px · name
   (primary, ellipsis) · reason token · `ProjectButton` · [the dedup
   disclosure] · one verb. 393: emblem 32px · name (wrapping) · then a
   full-width second line holding reason + `ProjectButton` +
   disclosure on the left and the verb on the right. **The same object,
   the same verbs, the same rows** (C1).
6. **One filled primary.** The top-ranked row's verb. Every other row
   verb is ghost dense.

**The five states.**

| State | Face |
|---|---|
| **Empty, complete** | `Nothing needs you` (muted display) + `COVERAGE COMPLETE · 8 OF 8 AVAILABLE` + `NO CALENDAR · Connect calendar` + the `BRIEF · Generate` row. **No prose line**: with no calendar there is no "next thing that happens" to name, so the empty state says nothing rather than inventing a calendar fact (C18). Board `P2ArrivalQuiet` |
| **Empty, partial** | `Coverage incomplete` + the coverage rows. **Already built and shipped** by HS-200-07: `assets/story-07-shots/build-arrival-partial-empty-1440.png` and `-393.png`. Its wording is unchanged by this design (concern 4 is his ear) |
| **Loading** | First paint carries the counts already fetched (canon D); a source mid-observation shows its own `CHECKING` coverage row with `Retry`. The face never blanks |
| **Partial** | `COVERAGE 6 OF 8` and one row per gap. Board `P2Arrival` |
| **Failed** | A failed source keeps its coverage row AND its previously-observed items keep their rows, stamped `FROM THE LAST GOOD READ · 08:41` (`ChairHome.tsx:848-855`). Board `P6Repair` |
| **Resumed** | After a restart the aggregate re-reads; items whose source is now unreadable become the `STILL TRUE` case above rather than vanishing |
| **One Project** | Board `P2ArrivalOne`. The `ProjectButton` is WITHHELD from every row (repeating one word three times says nothing), `headlineFor` already drops the project clause (`ChairHome.tsx:254`), and the rows obey the same five-class key -- opening on `NOT RUN`, the class his desk has |

**Notifications** (story 15 AC4, C4). Notify on a changed ITEM SET,
computed from `_item_id`, never on a changed count. Quiet hours, mute
and per-Project settings gate delivery. A restart re-reads before it
notifies.

**Voice.** The arrival has no text input of its own; `Talk` in the
capture bar is the desk's one mic authority (Article IV.3).

**Keyboard.** Roving rows (`roving.ts:34`): Up/Down move between rows,
`Enter` fires the row's verb, `Tab` leaves the ledger. `Escape` returns
focus from the remainder expansion to `Show all`, and closes a dedup
disclosure back onto its trigger.

**Accessible names.** `Open -- KAN-7 Payments cut-over runbook`;
`Complete -- Priya confirms the freeze window`; `Sources -- Priya
confirms the freeze window`; `Reconnect -- jira KAN`; `Retry --
confluence PLATFORM`; `Show all -- the remaining 12`; `Generate --
today's brief`; `Connect calendar`; `Open the Project -- Q4 platform`.

**Focus return.** Acting on a row removes it and moves focus to the row
that took its place. If the ledger empties, focus moves to the section
caption.

---

### D2(c) -- Posture 3: preparation

**Boards:** `P3Prepare` (1440) · `P3Brief` (1440) · `P3BriefPhone`
(393, the same face) · `P3PrepareNoModel` (1440, failed).

**Where it lives.** The Room's ask well for the request; a document
surface (`Material`, `Material.tsx:82`) inside a window for the kept
brief. `MondayBriefService` and `ProjectUpdateService` own the work.

**The prepare face.** Head `Prepare a brief` + the `ProjectButton` +
`COVERAGE · 2 OF 4` + `PURPOSE SET BY HAND` + `NO CALENDAR`. **The head
names no clock time**: it cannot say "the 11:00 review" beside a token
that says there is no calendar (C18). Then the ask well. Then
**`SOURCES 4`, once**, all four with their state -- and the two gaps
marked in their own rows (N2): `KAN · LAST READ 03:41 · STALE ·
OBSERVED 03:41 · Retry` and `confluence PLATFORM · CONFLUENCE TOKEN
EXPIRED · CREDENTIAL EXPIRED · OBSERVED 08:41 · Reconnect`. The
coverage is visible **before** the run, so he can repair first or
accept the gap deliberately. Then `CARRIED FORWARD 2`: the current
decision and the open commitment this brief will inherit (story 13).

**The kept brief face.** Head `Brief ready` + `ProjectButton` + `KEPT`
+ `MANIFEST M-118 · REV 1` + `COVERAGE · 3 OF 4` + `PREPARED 09:12`.
Then, in order:

1. **The document** -- the generated prose, in `Material`, with
   caption-step headings (`DECIDE TODAY`, `ASK THEM`) and body-step
   sentences. Bounded: two decisions, two questions, not a source dump
   (story 11 AC3).
2. **`CLAIMS 4`** -- one row per claim: the sentence at primary step,
   its `ProvenanceChip` ref and `Open source`; beneath it the
   `ClaimAxes` triple plus any unsupported values, printed AND typed:
   `DEADLINE 2026-12-31 · NO SOURCE`, `NUMBER 95% · NO SOURCE`.
   A claim with no reference shows `NO SOURCE` and `Find support`
   **at both widths**.
3. **`NOT READ 1`** -- **this row IS the coverage record** (N2): the
   source, `CONFLUENCE TOKEN EXPIRED · OMITTED`, its own
   `CREDENTIAL EXPIRED` state chip, `OBSERVED 08:41`, and `Reconnect`
   (the one verb for that failure class). The head token says how many;
   this row says which one and why.
4. **Footer** -- `EgressChip` + the model and elapsed receipt
   (`QWEN3 35B · 11.4 S`) + `Copy` · `Open sources` · `Keep` (the one
   filled primary). **`P3BriefPhone` carries all of it**, because a
   model produced this face at both widths.

**The manifest.** **Ruling R3:** the manifest binds to the **kept**
brief only, and it reuses mechanics that exist rather than inventing
them -- `refinement_attachment_revisions`' integer `attachment_revision`
and `attachment_sha256` recomputed and compared on every read
(`refinement_context_service.py:1105-1111`), its `frozen=True`
self-validating snapshot (`:25-43`), its named stale repair
(`{"repair": "update_context"}`, `:1113-1119`), and `_coverage_row`'s
eight fields (`needs_you_aggregate.py:91-113`) persisted. It shows as
ONE token (`MANIFEST M-118 · REV 1`) and opens in the `SOURCES` wing.
The service freezes the material; the browser never submits a copied
replacement (C3).

**The five states.**

| State | Face |
|---|---|
| **Empty** | `Nothing prepared yet` in the Room (board `P1Ask`); the brief window does not exist until a run does |
| **Loading** | Board `P1Running` |
| **Partial** | Board `P3Brief`: `COVERAGE · 3 OF 4` in the head and the one `NOT READ 1` row carrying the state chip, the observation and the repair. The document is not silently shorter -- the gap is counted once and named once (N2) |
| **Failed** | Board `P3PrepareNoModel`: `Cannot draft`, the named engine reason, `PURPOSE KEPT`, `NOTHING SENT`, `Prepare` drawn disabled; `Set up model` + `Write it myself`; **and `COVERAGE · 2 OF 4` still in the head with both gaps still marked in `SOURCES 4`**, because a failed face may not clear a known gap by omission |
| **Resumed** | The kept brief reopens by id after a restart with the same manifest revision and its sha re-verified. A source that has since become unavailable turns the brief `INCOMPLETE · 3 OF 4 SOURCES` in the unfinished ledger (board `P6Resume`) |

**Voice.** `Purpose` carries its mic (`Dictate into Purpose`). Editing
a claim's sentence uses `EditInPlace` (`Surface.tsx:1063`), whose `mic`
prop defaults true. **Editing a supported sentence invalidates its
support** (C2): the support chip becomes `LINKED · EDITED` without
deleting provenance (`update/model.ts:161-176`).

**Keyboard.** `Tab` walks coverage, document, claims, then the footer
verbs. Inside `CLAIMS`, Up/Down rove rows, `Enter` opens the source. No
hidden single-key shortcuts. `Escape` closes an open disclosure and
returns focus to its trigger.

**Accessible names.** `Prepare -- build the brief from these sources`;
`Open source -- MTG 09-05`; `Find support -- Sprint velocity improved
over the trailing average`; `Reconnect -- confluence PLATFORM`;
`Retry -- KAN`; `Copy the brief`; `Open sources`; `Keep this brief`;
`Open the Project -- Q4 platform`.

**Focus return.** `Keep` keeps focus on `Keep` and changes the head
token to `KEPT` (the receipt is the feedback, not a toast). `Open
source` opens the source in context; closing it returns focus to the
claim row it came from.

---

### D2(d) -- Posture 4: meeting review

**Boards:** `P4Processing` (1440, loading + resumed) · `P4Review`
(1440) · `P4ReviewPhone` (393, the same face).

**Where it lives.** The meeting window, wings `MEETING` / `REVIEW`.
`ProposalBridgeService` and the decision / follow-through services own
the work.

> **This posture asks the most of the wire.** Counsel established that
> `follow_through_proposals` (`holdspeak/db/schema.py:4061-4089`)
> stores `kind ∈ {decision, action}` and `state ∈ {proposed, confirmed,
> dismissed}` and nothing else -- no support, no acceptance, no
> unknowns, no `refs[]` -- and that `segment_timestamp` (`:4071`) is a
> single REAL, a point, not a span. Four D3 rows now say MISSING, and
> **story 12 is re-judged L** (Sizes). Posture 4, not the manifest, is
> the biggest unknown in this design.

**The processing face.** Head `Reading the meeting` + `ProjectButton` +
`ADMITTED` + `JOB K-8C21` + `ATTEMPT 2 · SAME JOB`. **The meeting's
name is in the title bar and nowhere else** (C14). Then
`COVERAGE 31 OF 47 TURNS` -- the transcript's own coverage, above the
answer -- with `PARTIAL`, its observation and `Re-read`. Then
`ProgressPlan` with real stages and real counts, the `ACTIONS 6`
disclosure on its own line, the route, and `Stop` as the one primary.
Then **`ALREADY KEPT 2`** -- the results attempt 1 produced, each
stamped `ATTEMPT 1`. That section is the face's answer to C6: a retry
cannot look like new work, and nothing is duplicated.

*The progress requirement cannot pass with a decorative spinner*
(ACCEPTANCE.md). Every step drawn is a stage the kernel reports, or the
row that would draw it is named MISSING in D3.

**The review face.** Head `5 to review` + `ProjectButton` +
`NOTHING ACCEPTED YET` + `EXTRACTED 12:04`. Then
`COVERAGE 47 OF 47 TURNS` with `AVAILABLE` and `Open transcript`. Then
`DECISIONS 2` and `COMMITMENTS 3`. Each row:

- The proposed sentence at primary step.
- **One verb, `Confirm`** (ghost dense), and a `MORE` disclosure
  holding `Edit`, `Dismiss` and `Open evidence` (C15).
- Beneath: `ProvenanceChip` with the transcript **span**
  (`MTG 09-07 · 11:18–11:21`), then `ClaimAxes` reading
  `PROPOSAL · <support> · UNREVIEWED`, then the unknowns as typed
  unknowns -- `OWNER · UNKNOWN`, `DUE · UNKNOWN`, `DATE · UNKNOWN`,
  never a hedged guess (C10).
- The face's one filled primary is `Accept reviewed` in the footer.

**Why `PROPOSAL · UNREVIEWED` and not "extracted".** C2: kind and
acceptance are independent. Extraction produces a proposal; only his
`Confirm` produces acceptance, and a model score can never produce it.

**The five states.**

| State | Face |
|---|---|
| **Empty** | A completed meeting with no proposals reads `NOTHING TO REVIEW` (`SurfaceState`), with the coverage row and the transcript verb kept. It never reads "all clear" |
| **Loading** | Board `P4Processing` |
| **Partial** | `COVERAGE 31 OF 47 TURNS` with `PARTIAL` and `Re-read`; the un-read span is named in `Open evidence`. The proposals stand; the coverage of the reading is stated. **The numerator does not exist today** (D3, MISSING) |
| **Failed** | The run row turns `FAILED · <named reason>` with `Check`/`Retry` and the same job identity; `ALREADY KEPT` persists. No proposal is invented from a partial read |
| **Resumed** | Board `P4Processing`: `ATTEMPT 2 · SAME JOB` + `ALREADY KEPT 2 · ATTEMPT 1`. Repeated completion, model retry and a lost acknowledgement produce no duplicate proposals (story 12 AC5). **The proposal→job/attempt link does not exist today** (D3, MISSING) |

**Voice.** `Edit` (inside `MORE`) opens `EditInPlace` on the sentence,
mic included. **Ruling R5:** edit-then-confirm is lawful and the routes
are verified; but C2 requires the edit to drop support to
`LINKED · EDITED`, and **the confirm route does no such thing today**.
That invalidation is named MISSING in D3 and owned by story 12, so the
face does not lie about it.

**Keyboard.** Up/Down rove proposal rows; `Enter` fires `Confirm`;
`Backspace` does NOT dismiss (destructive verbs need their own click,
and `Dismiss` is one level in). `Escape` closes `MORE` and returns
focus to its trigger.

**Accessible names.** `Confirm -- Cut-over runs on the read replica
first`; `Edit -- ...`; `Dismiss -- ...`; `Open evidence -- ...`;
`Open transcript`; `Accept reviewed`; `Stop -- end this run`;
`Re-read -- Transcript`; `Open the Project -- Q4 platform`.

**Focus return.** `Confirm` leaves the row in place, flips its
acceptance chip to `ACCEPTED`, and keeps focus on the row so the next
Down key is the next proposal. `Dismiss` removes the row and moves
focus to its successor.

---

### D2(e) -- Posture 5: recall

**Boards:** `P5Recall` (1440) · `P5RecallPhone` (393, the same face) ·
`P5RecallQuiet` (1440, the miss).

**Where it lives.** Desk memory, wings `SEARCH` / `UNFINISHED` /
`REPAIRS`. The Room already falls back to a Desk Memory search face
when unscoped (`ProjectRoomCore.tsx:1758-1774`). `MemoryService`
(`GET /api/memory/search`, `holdspeak/web/routes/memory.py:19`) and
`DecisionRecordService` (`holdspeak/web/routes/decision_records.py:28-58`)
own the work.

**Elements, in order.**

1. Head: `3 remembered` + `REF · FREEZE WINDOW` + `SEARCHED 09:20`.
   **No `n OF m PROJECTS`**: `MemorySearchResult.to_dict()`
   (`holdspeak/db/memory.py:67-97`) returns hits, page and ranking and
   no per-Project readability, so search-side coverage is named MISSING
   in D3 and is not drawn (a coverage token the wire cannot produce is
   the thing this design refuses to draw anywhere else).
2. The search well: `StringGadget` with its mic (`Dictate into the
   search`) + `Search` (raised).
3. `FilterTokens`: `All · Decisions · Commitments · Briefs · Meetings`
   -- the same five at both widths (`FilterTokens.tsx:37`). Present on
   every state including the miss.
4. **`CURRENT 1`** -- the accented card: the decision at primary step,
   `ClaimAxes` reading `DECISION · SUPPORTED · ACCEPTED`, the
   `ProjectButton`, the rationale at body step, then `SOURCE` +
   `ProvenanceChip` + `Open source`. Verbs: `Open` (ghost dense) and
   `Carry into brief` (the one filled primary).
5. **`SUPERSEDED 1`** -- the same object, dimmed to 0.72, its
   acceptance chip reading `SUPERSEDED`, a trailing
   `SUPERSEDED BY DEC 09-07`, its `ProjectButton` and its `Open`.
   **Discoverable, never current** (story 13 AC2).
6. **`OWED 1`** -- the commitment the decision left behind, with
   `DUE TODAY`, its `ProjectButton` and `Complete`. It carries **no
   `OPEN` state chip**: `Open` is a verb on this face, and one word
   never carries two meanings on one face (C13).

`Carry into brief` attaches the canonical record BY REFERENCE to the
next preparation (C3), never a copy -- so a decision superseded between
the recall and the preparation resolves to the current one at read time.

**The five states.**

| State | Face |
|---|---|
| **Empty (no query yet)** | The well and the filters, and `SEARCH THE DESK` as the one token. No results region, no zero counts |
| **Loading** | The results region keeps its last content dimmed with a `SEARCHING` token in the head; the well stays usable |
| **Partial** | **Not drawable today.** Search-side coverage has no wire (D3, MISSING). Until it exists, a miss under a failed source is indistinguishable from a true miss -- that is stated here rather than papered over with a token |
| **Failed** | `CANT SEARCH · <named reason>` with `Retry`; the query stays in the well |
| **Resumed** | The query and its filter survive a restart. `UNFINISHED` (board `P6Resume`) is the wing that resumes work rather than results |

**The miss.** Board `P5RecallQuiet`: display `Nothing matches`, and
beneath it the empty region carries **only** the glyph and one true
line -- `Four projects searched, none holds this`. The display line is
not repeated as an empty token (C14). The filters stay. `Clear` is
withheld: there is nothing to clear (A.11).

**Voice.** The search field carries its mic. Speaking a query does not
auto-submit; `Search` or `Enter` submits.

**Keyboard.** `Enter` in the field searches. Left/Right rove the filter
tokens (`role="group"`, `aria-pressed`); `Enter`/`Space` toggles one.
Up/Down rove result rows. `Escape` in the field clears the query and
restores the previous results.

**Accessible names.** `Search desk memory`; `Dictate into the search`;
`Filter -- Decisions`; `Carry into brief`; `Open -- the current
decision`; `Open -- the superseded decision`; `Open source -- MTG
09-07`; `Complete -- Priya confirms the freeze window`; `Open the
Project -- Q4 platform`. **The footer names `Unfinished` and `Repairs`
only** -- never `Search`, because the `SEARCH` wing is already active
(C13).

**Focus return.** `Search` moves focus to the results region
(`role="region"`, labelled with the query). `Carry into brief` keeps
focus on itself and changes its own state to `CARRIED`.

---

### D2(f) -- Posture 6: recovery

**Boards:** `P6Repair` (1440) · `P6Resume` (1440) · `P6Phone` (393,
the same face).

**Where it lives -- stated plainly** (H9). Posture 6 is **not** the
arrival re-composed. It is Desk memory's third wing: `SEARCH` /
`UNFINISHED` / `REPAIRS`, one window, three wings, drawn on all three
posture-5 and posture-6 boards. The arrival keeps its own coverage
section for the gaps it must show inline; the `REPAIRS` wing is where
he goes to fix them and to pick work back up.

**The repair face** (`REPAIRS` wing). Head `3 to repair` +
`NOTHING LOST` + `1 TASK WAITING` + `CHECKED 09:22`. Then:

1. **`REPAIRS 3`** -- one `RepairRow` per failure: emblem
   (`SRC` / `ENG`), the subject at primary step, the NAMED reason
   **carrying its own provider**, its **own state chip**, and the
   owning verb. **The chips stay distinct** (C17 note): the aggregate's
   seven tokens are seven different facts (`_repair`,
   `needs_you_aggregate.py:65-87`), and collapsing them to one
   `CANT CHECK` would tell him three failures are the same failure.

   | Subject | Reason | Chip | Verb |
   |---|---|---|---|
   | jira KAN | `JIRA REJECTED THE QUERY` | `CANT CHECK` | `Reconnect` |
   | Qwen3 35B | `192.168.1.43 UNREACHABLE` | `ENDPOINT UNREACHABLE` | `Check` |
   | confluence PLATFORM | `CONFLUENCE TOKEN EXPIRED` | `CREDENTIAL EXPIRED` | `Reconnect` |

   **One failure class, one VERB** (C17) and **one failure, its own
   TOKEN** (C17 note) are the same rule read from both ends: the verb
   says what to do, the chip says what happened. Two sources that
   cannot be read for a credential reason take `Reconnect`; an
   unreachable engine takes `Check`.
2. **`UNFINISHED 1`** -- the saved ask: its purpose, `SAVED 09:04`, its
   recipe, its `ProjectButton`, why it is stopped (`WAITING ON THE
   ENGINE`), and **`DRAFT NOT SAVED`** (ruling R2). One verb, `Resume`
   (the face's one filled primary); `Discard` (`ConfirmVerb`) lives in
   its `MORE` disclosure.
3. **`STILL TRUE 2`** -- the items last observed before the source
   failed, each stamped `FROM THE LAST GOOD READ · 08:41`, each with
   its `ProjectButton` and its `Open`. **A failed source cannot clear
   known work** (C4; story 15 AC5).
4. Footer: `THIS DEVICE` + `NOTHING RETRIED` + `Search` · `Unfinished`
   (never `Repairs` -- that wing is active).

**The resumed face** (`UNFINISHED` wing). Head `6 unfinished` +
`RESUMED AFTER RESTART` + `NOTHING LOST` + `READINESS RE-READ · 41 MS`.
Then **`YOUR WORK 6`**, one row per work item, drawing the six states
the product must distinguish (README "Returning to work"), each with
its `ProjectButton` and one verb:

| State | Chip | Its one verb |
|---|---|---|
| saved | `SAVED 09:04` | `Resume` (the face's one filled primary) |
| running | `RUNNING · 00:52` | `Stop` |
| waiting | `WAITING ON YOU` | `Answer` |
| failed | `FAILED · 192.168.1.43 UNREACHABLE` | `Check` |
| incomplete | `INCOMPLETE · 3 OF 4 SOURCES` | `Re-read` |
| accepted | `ACCEPTED 09-02` | `Open` |

Then **`THE RUNTIME`** -- the C1 identity line at secondary step
(`BACKEND bea4176c · BUNDLE bea4176c · STARTED 09:21`) with
`Diagnostics`. Compact when healthy; the compact repair state when the
parts disagree (C1). Detailed process and filesystem facts stay in
diagnostics.

**The five states.**

| State | Face |
|---|---|
| **Empty** | No repairs and nothing unfinished: the section is ABSENT (A.8) and the wing reads `NOTHING TO REPAIR` |
| **Loading** | A repair in flight shows `CHECKING` on its own row; the other rows do not move |
| **Partial** | `3 to repair` beside `STILL TRUE 2` -- the failure and the surviving knowledge are both stated |
| **Failed** | A repair that fails returns a NEW named reason on the same row. It never returns to green without an observation |
| **Resumed** | Board `P6Resume` in full |

**Voice.** No text input on either face, so no mic -- the voice law is
per input, not per face.

**Keyboard.** Up/Down rove rows; `Enter` fires the row's verb. `Resume`
is reachable by Tab from the section caption. `Discard` (inside `MORE`)
is a `ConfirmVerb`: first press asks `Sure?` in place, `Escape` cancels
and returns focus to the verb.

**Accessible names.** `Reconnect -- jira KAN`; `Check -- Qwen3 35B`;
`Reconnect -- confluence PLATFORM`; `Resume -- the architecture review
brief`; `Discard the unfinished ask`; `Answer -- Decision review --
governance`; `Stop -- Weekly update -- Q4 platform`; `Re-read --
Architecture review -- brief`; `Diagnostics`; `Open the Project -- Q4
platform`.

**Focus return.** A successful repair keeps focus on the row and
replaces the reason token with the new observation. `Resume` opens the
originating Room with the ask well focused and the purpose intact --
the same mechanism as `Set up model` in D2(a).

---

### D2(g) -- the continuity rule, corrected

Story 09 AC2 asks for "continuity back to the originating Project". A
write is not a way back. This table now names, per posture, where the
Project is drawn and **what actually navigates**.

| Posture | Where the Project is drawn | What navigates back |
|---|---|---|
| 1 first result | The Room's title bar (its outcome) **and** the `ProjectButton` in the head token row | It IS the Room -- no navigation needed |
| 2 priorities | `ProjectButton` on every row (withheld when the desk has one Project) | The `ProjectButton` opens that Project's Room |
| 3 preparation | `ProjectButton` in the head of both the prepare face and the kept brief | The `ProjectButton`. `Keep` is a write, not a way back, and is no longer named as one |
| 4 meeting review | `ProjectButton` in the head of `P4Processing`, `P4Review` and `P4ReviewPhone` | The `ProjectButton`. `Confirm` is a write |
| 5 recall | `ProjectButton` on the current decision, the superseded decision and the owed commitment, at both widths | The `ProjectButton`. `Carry into brief` is a write |
| 6 recovery | `ProjectButton` on the unfinished ask, on every `YOUR WORK` row and on every `STILL TRUE` row | The `ProjectButton`, and `Resume`, which reopens the originating Room with the purpose intact |

---

## D3 -- the wire

Every seam below exists on this branch unless marked **MISSING**.
Twelve citations counsel measured as off have been corrected against
the tree; the two he called materially wrong are corrected and noted.

### The attention seam (postures 2 and 6)

| What | Where |
|---|---|
| Aggregate builder | `holdspeak/services/needs_you_aggregate.py`, `build_aggregate` (`:202`) |
| Coverage vocabulary | `needs_you_aggregate.py:52` -- `available · stale · failed · forbidden · unavailable`; kinds at `:53` |
| One coverage record | `_coverage_row` (`:91-113`): `source_id · kind · state · observed_at · label · project_id · reason · repair` -- **the eight fields the manifest persists** (ruling R3) |
| The repair path | `_repair` (`:65-87`): the token and the OWNING VERB, `href` is a route not an API path. Tokens: `FORBIDDEN` · `CANT CHECK` · `STALE` · `PAUSED` · `NEVER CHECKED` · `NOT OBSERVED` · `READ FAILED` |
| Aggregate freshness vs source freshness | `:366-372` -- `computedAt` is the aggregate's clock; each record carries its own `observed_at`; `complete` is `all(state == "available")`, which is why `N` is the `available` count |
| The dedup key | `_item_id` (`:135-143`), docstring *"A stable id for one attention row, for dedup and reconciliation"* -- **exists, zero callers** |
| Route | `GET /api/desk/needs-you` (`holdspeak/web/routes/projects.py:436-450`), cached `NeedsYouCache` at `:429-430`, `max_age_s=900` |
| Browser vocabulary | `web/src/desk/coverage.ts:8-13`; `readCoverage` `:76-112`; the `DESK_UNREAD` synthetic gap `:52-60`; gap ordering `:62-67` |
| Face | `ChairHome.tsx`, `Arrival` declared at **`:345`**, returning at `:616-796`; `CoverageSection` `:902-940`; `CoverageVerb` `:946-976`; `coverageEmblem` `:895-900`; `headlineFor` `:247-254`; the raw coverage token `:923-929` |
| **MISSING: the cap and the true total** | `unmutedItems` is uncapped (`:436-447`; rendered `:812` with no `.slice`). The remainder pattern to copy is `BRIEF_CAP = 3` at `:1169`, `:1181-1182`, `:1220-1227` |
| **MISSING: the ranking** | Sort is severity only (`:439`), one key, no tie-break. Overdue / due-today / no-due / waiting is unwritten |
| **MISSING: the dedup wiring** | `_item_id` has zero callers; no projection joins on it |
| **MISSING: the traceable-sources disclosure** | Story 15 AC3 requires it; nothing renders a deduplicated row's constituent sources |
| **MISSING: the changed-set notification** | The notification edge is count-based (BASELINE.md, "Project attention"). *Counsel did not trace this in code; it is carried as BASELINE's claim, not as a verified seam* |

### The claim seam (postures 3, 4, 5)

| What | Where |
|---|---|
| Kinds | `holdspeak/services/project_update_service.py:90-103` -- `observation · inference · proposal · decision · execution_result · outcome_measure` |
| Support | `:107-116` -- `unknown · source_linked · supported · disputed` |
| Acceptance | `:118-127` -- `unreviewed · accepted · rejected · superseded` |
| The only two methods that may raise support | `:130-132` -- `field_mapping` and `reviewer`. **A model score is neither** |
| The conservative migration | `CLAIM_SUPPORT_MAPPING_VERSION = "c2.1"` (`:136`); recorded per claim, the stored blob never rewritten in place |
| Invalidation | `INVALIDATION_TEXT_EDITED` (`:139`), applied at `:1910` |
| `Claim` / `SupportRecord` | `project_update_service.py:144-240` -- reusable by a brief unchanged; only the binding is new |
| Browser tokens | `web/src/features/project-room/update/model.ts:141-148` (kind), `:161-176` (support, incl. `LINKED · EDITED` and `LINKED · MIGRATED`), `:180-192` (acceptance), `:194-196` (unknowns) |
| Face | `UpdatePosture.tsx:141` (the `hasAxes` gate), `:145-171` (the chips) |
| **Owed** | The triple is reachable ONLY from the update posture today. S2 promotes it |

### The preparation seam (posture 3)

| What | Where |
|---|---|
| Room read | `GET /api/projects/{id}/room` (`projects.py:46`), forced re-read `POST .../room/read` (`:55`) |
| The four questions, as built | `ProjectRoomCore.tsx:2-3`; sections `NeedsYou` `:692-880`, `Sources` `:881-1099`, `SinceYouLooked` `:1145-1192`, `DecisionsCommitments` `:1193-1323` |
| The ask well | `RoomAskWell` `:1378-1472` (free text + mic + grounding receipt) |
| Posture routing | `:1783-1810` -- Review > Update > Steward > Room, each owning the body |
| Brief service | `GET /api/brief/latest`, `POST /api/brief/generate`, `GET /api/brief/shelf`, `POST /api/brief/items/{id}/shelf` (`holdspeak/web/routes/monday_brief.py:100,110,118,122`) |
| Updates | `GET /api/projects/{id}/updates`, `POST .../updates/draft`, `POST /api/updates/{id}/regenerate`, `.../publish`, `.../markdown` (`project_updates.py:54,74,134,167,195`) |
| **Two frozen source manifests DO exist** (corrects the first draft) | `project_updates.source_manifest_json` (`schema.py:3941`, built `project_update_service.py:565-580`) and `project_reviews.source_manifest_json` (`schema.py:3916`, built `project_delta_service.py:1454-1475`). The true statement is **"no manifest is bound to a brief"**, not "no such record exists" |
| The freeze mechanics to reuse | `refinement_attachment_revisions.attachment_revision` + `attachment_sha256`, recomputed and compared on every read (`refinement_context_service.py:1105-1111`); the `frozen=True` snapshot (`:25-43`); the named stale repair (`:1113-1119`) |
| **MISSING: `Keep` has no route and no service write** | `monday_brief.py:100-140` exposes latest / generate / shelf only; `monday_briefs.disposition` (`schema.py:2281`) is never written by `monday_brief_service.py`. Story 11 owns it |
| **MISSING: `monday_briefs` has no `project_id`** | `schema.py:2274-2282` is window-keyed (`period_start`/`period_end`). Story 11 AC4's "the kept brief remains attached to the originating Project" has nothing to attach to. Story 11 owns it |
| **MISSING: the brief's manifest binding** | Observed revisions, observation times, claims, coverage and the resolved data boundary are all absent from `monday_briefs`/`monday_brief_items`; the one `source_ref` per item is free text, never through `qualified_ref()`. **Seven new fields/bindings** (R3): brief↔Project; revision + freeze hash; persisted coverage rows; claims bound to a brief; the data boundary (copy `project_updates.generator, generator_host, generator_model`, `schema.py:3945-3947`); carried refs; a written lifecycle (`project_updates.lifecycle` is the working pattern) |
| **MISSING: the recipe pick** | `RoomAskWell` takes free text. The three-recipe `CycleGadget` and C5's plan record do not exist |
| **UNKNOWN, not verified** | Whether `RoomAskWell`'s submission is persisted anywhere durable. `RESUMED AFTER RESTART · SAVED 09:04` and the whole `UNFINISHED` ledger rest on this. Story 10 must trace it before building on it |

### The meeting seam (posture 4)

| What | Where |
|---|---|
| Proposals | `GET /api/meetings/{id}/follow-through-proposals` (`proposals.py:42`), `GET /api/projects/{id}/proposals` (`:54`) |
| Confirm / Dismiss | `POST /api/proposals/{id}/confirm` (`:66`), `POST /api/proposals/{id}/dismiss` (`:86`). No PUT/PATCH exists, so **`Edit` is edit-then-confirm** (ruling R5) |
| **Accept / reject DO exist** (corrects the first draft) | `POST /api/decisions/{id}/accept` and `/reject` at `holdspeak/web/routes/decisions.py:57,61`, backed by `decision_lifecycle_service.py:40-41`. The first draft cited `primitives/decisions.py`, a different router. **`BASELINE.md:69` carries the same error and should be corrected with it** -- flagged for the orchestrator |
| Decisions | `holdspeak/web/routes/primitives/decisions.py:30,37,62`; supersede at `:113` |
| Decision records | `decision_records.py:28` (list), `:36` (search), `:42` (review), `:46` (by source), `:52` (by work), `:58` (get) |
| Follow-through | `holdspeak/web/routes/follow_through.py:96` (board), `:110` (complete), `:122` (commit-decision) |
| Meeting completion | `POST /api/projects/{id}/meetings/{meeting_id}` (`projects.py:203`) |
| Decision lifecycle | `decisions.lifecycle` and `decisions.superseded_by` (`holdspeak/db/decisions.py:19,62,112`) |
| **MISSING 1: the claim axes on a proposal** | `follow_through_proposals` (`schema.py:4061-4089`) stores `kind ∈ {decision, action}` and `state ∈ {proposed, confirmed, dismissed}`. **No support, no acceptance, no unknowns, no `refs[]`.** `PROPOSAL · SUPPORTED · UNREVIEWED` and every `OWNER · UNKNOWN` chip on `P4Review` rest on this |
| **MISSING 2: the transcript SPAN** | `segment_timestamp` (`schema.py:4071`) is a single REAL -- a point, with no end. `MTG 09-07 · 11:18–11:21` and "the `EVIDENCE` disclosure holding the transcript span" have no end to draw |
| **MISSING 3: the proposal→job/attempt link** | `proposal_bridge_service.py` records no `job_id` and no `attempt`. `JOB K-8C21`, `ATTEMPT 2 · SAME JOB` and `ALREADY KEPT 2 · ATTEMPT 1` have nothing to read. `intel_jobs` (`schema.py:137-176`) holds the job; nothing joins it to a proposal |
| **MISSING 4: the turns-read numerator** | `segments` (`schema.py:76-86`) gives the 47; nothing anywhere counts how many were read. `COVERAGE 31 OF 47 TURNS` has no numerator |
| **MISSING 5: confirm does not invalidate support** | R5 requires an edited proposal's support to drop to `LINKED · EDITED` (C2). The confirm route does no such thing. Story 12 owns it, or the face lies |

### The recall seam (posture 5)

`GET /api/memory/search` (`holdspeak/web/routes/memory.py:19`, router
prefix `/api/memory` at `:17`) plus the decision-record routes above.
The Room already renders a Desk Memory search face when unscoped
(`ProjectRoomCore.tsx:1758-1774`).
**MISSING: search-side coverage.** `MemorySearchResult.to_dict()`
(`holdspeak/db/memory.py:67-97`) returns hits, page and ranking and no
per-Project readability. `SEARCHED n OF m PROJECTS` is therefore **not
drawn on any board** and the partial state of posture 5 is declared
undrawable in D2(e).

### The readiness and repair seam (postures 1 and 6)

| What | Where |
|---|---|
| Concierge | `holdspeak/web/routes/concierge.py:35` (prefix), `:46` detect, `:115` probe, `:208` apply |
| Repair face | `ConciergeCore.tsx:411-425` (the `NEEDS YOU n` section, absent at zero), `RepairRow` `:247-291`, its `StateChip` at `:275-278` |
| Return-to-task, state half | `window.dispatchEvent(new Event("holdspeak:settings-updated"))` at `web/src/features/concierge/useConciergeController.ts:487` and `web/src/pages/cores/SettingsCore.tsx:890`; consumed at `web/src/pages/cores/dictation/SpeakFace.tsx:288-289` (re-read readiness, no reload, utterance preserved) **and at `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:211-212`, a second consumer this table first omitted** |
| The Models window is reachable | `web/src/desk/applications.ts:308-313` |
| Setup status | `GET /api/setup/status` (`holdspeak/web/routes/setup.py:48`) |
| **MISSING: the focus half of return-to-task** | Nothing returns focus to the verb the owner left. One line per call site, and it is what makes returning feel like returning. Story 10 owns it |
| **MISSING: the generalisation** | The event is dictation-specific in practice; the Room's ask well must subscribe to it |

### The shared-experience seam (every posture)

| What | Where |
|---|---|
| `Button` | `web/src/components/signal/Signal.tsx:21` |
| `MicButton` | `web/src/desk/components/MicButton.tsx:42`; toggle `:362-370`; `aria-pressed` `:399`; unavailable NAMED `:159-177`; failure named `:419-428`; Enter/Escape stop `:135-147` |
| `Disclosure` | `patterns/Disclosure.tsx:13`; `aria-expanded` `:93`; Escape closes `:74-79`; focus returns to trigger `:66-72`; body `role="region"` `:105` |
| Roving rows | `web/src/desk/surface/roving.ts:34` |
| The canon guard | `scripts/ux_canon_scan.py`, ceiling `tests/ux_canon_ceiling.json`, test `tests/unit/test_ux_canon_ratchet.py`. **The voice law is at ceiling `mic: 0` after 176** |
| **Residue 1: a raw `<textarea>`** | `web/src/desk/components/ThreadComposer.tsx:968`, flagged by the comment at `:966`. A mic-law site the scanner cannot see (it does not match `<textarea>`); carried in the ceiling under rule `B` |
| **Residue 2: two raw `<button className="desk-chip">`** | `web/src/desk/components/ThreadComposer.tsx:985-1004` (`Stop`, `Send`). Rule A.1 |
| **Residue 3: draft custody in-memory** | `web/src/desk/threadComposerDrafts.ts:5-15`; cleared at `web/src/desk/threads.ts:889-890`. Ruling R2: the face says `DRAFT NOT SAVED`; story 10 gains the AC |
| **Residue 4: MCP steering read-only** | C11 requires the same service validation through Web and MCP. *Carried as BASELINE.md's claim; counsel did not trace it in code. UNKNOWN, not verified* |

---

## D4 -- counsel's hunts (what fails on HIS desk)

BASELINE.md attests the owner's actual desk on 2026-09-06. These are
not hypotheticals.

**1. He has ZERO calendar sources and zero calendar events.** The design
answers structurally: the purpose is typed or spoken and the recipe is
picked, so postures 1 and 3 work with no calendar. `NO CALENDAR` +
`Connect calendar` rides in the head of every arrival board and of
`P3Prepare`. **No board invents a clock fact**: `P3Prepare`'s head reads
`Prepare a brief`, not "the 11:00 review", and `P2ArrivalQuiet` carries
no "next at 11:00" line. **The walk runs the no-calendar path first.**

**2. He has ONE active Project and nine archived ones.** Board
`P2ArrivalOne` draws that face: `3 need you` with no project clause
(`headlineFor` already drops it, `ChairHome.tsx:254`) and the
`ProjectButton` WITHHELD from every row. It is beat 1 of his walk, and
it is now drawn rather than described.

**3. His default model route has KEY NOT SET; two LAN routes are ready
and unselected.** Board `P1RouteUnset` is the FIRST face he will meet.
Its `Prepare` is drawn `disabled`, so the refusal is visible and not
merely announced. `Cannot prepare` keeps the purpose, sends nothing,
carries `THIS DEVICE`, and offers `Write it myself`.

**4. He has six meetings, zero decisions, zero commitments and zero
interview sessions.** Posture 5 has nothing to recall on his desk. The
walk runs posture 4 BEFORE posture 5 in the same sitting.
`P5RecallQuiet` is the honest face until it does.

**5. Two `holdspeak web` processes are running against one database.**
`THE RUNTIME` on `P6Resume` is the face that says so. Until HS-200-02
lands, that line has nothing to read; it is drawn so story 02's identity
work has a destination.

**6. Coverage can be complete and the answer still wrong.**
`COVERAGE COMPLETE · 8 OF 8 AVAILABLE` says every source was read
successfully. It says nothing about whether the brief drew the right
conclusion. Coverage and support are separate rows, separate chips,
separate words, on every face.

**7. `N OF M` invites a false denominator.** M is the EXPECTED source
set, not the fetched one -- a deleted source must not shrink M and turn
coverage green by subtraction (C4: "an explicit coverage record for
every EXPECTED Project or source"). And N is now defined as the
`available` count, so four stale sources can never render `4 OF 4`.

**8. Five is a cap, not a truth -- and the total is now in the head.**
If the honest remainder is `47 MORE`, five plus a remainder may be worse
than a longer list. The cap stays at five because C4 fixes it; the
number is walk question 3.

**9. `Write it myself` must not be a dead end.** `P3PrepareNoModel`
draws `SOURCES 4` with their real states, so the manual path has
material and the gaps are visible while he writes. If it proves hollow
on the walk, it is a defect.

**10. `Carry into brief` can carry a stale record.** The record is
attached by reference (C3), so the preparation resolves it at read time;
a snapshot copy would be the bug.

**11. The Actions disclosure can become the place failures hide.** Every
board keeps failure ON the face and puts only latency, per-source reads
and the model call inside; the disclosure sits on its own line, off the
primary line.

**12. Promoting `RepairRow` (S3) edits two shipped faces.** Ruling R1:
promote the species, leave both call sites **behaviourally identical**
(175: a replacing face keeps its verbs), retire the duplicate in a later
story. One thing rides free and is not a behaviour change: converging
`ChairHome.tsx:923-929`'s raw `<span className="arrival-why-token">` on
`StateChip`, which `ConciergeCore.tsx:275-278` already uses for the same
fact. That is species canon, and it happens inside the promotion.

**13. Posture 4 draws more than the store holds.** Five D3 rows say
MISSING for one posture. `P4Review` and `P4Processing` are the boards
most likely to be built as a lie, and story 12 is re-sized L because of
it.

---

## D5 -- the walk (his verdict)

One sitting, his real desk, both widths, a window shot per beat. The
runner seeds nothing and writes nothing; the PRODUCT writes what the
beats say it writes, and nothing else. The before/after write-set is
asserted.

**Beat 0 -- the ground.** Confirm on his desk: one active Project, zero
calendar sources, the default route unset, two LAN routes ready. Record
which hub process is serving. *(Writes: none.)*

**Beat 1 -- the arrival he actually has.** Open the desk at 1440 and
393. Read board `P2ArrivalOne` beside the real face. Does the coverage
row tell him something he wanted to know, or is it noise? Does the face
feel emptier or cleaner without the Project token? *(Writes: none.)*

**Beat 2 -- the refusal first.** Open the one Project, speak a purpose
into the ask well, pick `Preparation brief`, press `Prepare` with the
route still unset. Expect `Cannot prepare`, the purpose kept, a visibly
disabled `Prepare`, nothing sent. Press `Set up model`, pick a LAN
route, come back. **The purpose must still be there, the route must
read READY without a reload, and focus must land on `Prepare`.**
*(Writes: one inference-assignment change.)*

**Beat 3 -- the first result.** Press `Prepare`. Watch the run. Open
`ACTIONS` once and close it. Read the brief. Press `Keep`. *(Writes:
one kept brief and its manifest.)*

**Beat 4 -- the claims.** On the kept brief, find one claim he
disagrees with. Edit it in place. Confirm the support chip drops to
`LINKED · EDITED` and the provenance survives. *(Writes: one claim
edit.)*

**Beat 5 -- the meeting.** Take a real meeting (or import one). Let it
complete through the actual trigger. Review the proposals: confirm two,
edit one, dismiss one. Confirm no duplicates after a deliberate second
completion. *(Writes: proposals, decisions, commitments.)*

**Beat 6 -- the next day.** Return to the arrival. Is the decision from
beat 5 in the brief? Search Desk memory for a phrase from it. Is the
current decision first, the superseded one visible, and does
`Carry into brief` do what it says? Time it. *(Writes: none, unless he
carries.)*

**Beat 7 -- the break.** Pull the LAN engine (or the confluence
credential). Reload. Confirm: the repairs are named with their own
providers, one failure class takes one verb, the unfinished ask keeps
its purpose, `STILL TRUE` keeps the items observed before the failure,
and nothing reads green. *(Writes: none.)*

**Beat 8 -- 393.** Repeat beats 1, 3 and 5 at 393. **Every verb, every
egress chip, every coverage row, every unknown token and every filter
that exists at 1440 must exist here** (C1). One row grammar, no
horizontal scroll.

### The questions for him

1. **Five, or more?** The display now says the true total (`17 need
   you`) and the caption the cap (`5 OF 17`). On a desk with 17 real
   items, is five the right cap, or does the remainder hide the thing he
   needed?
2. **Is coverage worth the line it costs?** It is above the answer on
   eleven boards. Does it earn that position every day, or only on the
   day something breaks?
3. **`Write it myself` -- real, or a courtesy?** When the route is down,
   would he draft by hand with the sources listed, or would he rather
   the desk refuse cleanly and stop?
4. **Recall in a minute.** Beat 6 is timed. If it takes longer than a
   minute on his real data, the target is wrong or the face is.
5. **`ATTEMPT 2 · SAME JOB` -- believable?** After beat 5's second
   completion, does the face make him confident nothing was duplicated,
   or does he still go and check?
6. **`Coverage incomplete` -- does it read as an error?** It is already
   shipped (HS-200-07) and unchanged by this design. His ear decides
   before stories 11 and 15 spread it to more faces.
7. **`DRAFT NOT SAVED` -- honest, or alarming?** Ruling R2 states the
   limitation on the face rather than persisting. Does the token help
   him, or does it just worry him?

---

## Sizes

Every gap named anywhere in this document now has an owning story AND
an acceptance criterion to gate it (C12). Where an AC does not exist
today, the story's AC text must gain it in the same change that adopts
this design.

| Story | Size | What this design commits it to, and the ACs it owes |
|---|---|---|
| **09** (this one) | S | This document, 22 artboards, `canvas.json`; counsel's read; the rulings; his word |
| **10** working context | **M** | Promotion with provenance and target revision; attach-by-reference; correction invalidates dependent work. **New ACs owed:** `TaskResume` (S5) as a face; the focus half of return-to-task; Thread draft custody stated as `DRAFT NOT SAVED` (R2) -- story 10's five ACs are promotion, reference, correction, revocation and People, and none covers a draft; the two `ThreadComposer` residues (`:968` textarea, `:985-1004` buttons). **First trace `RoomAskWell`'s durability** -- the UNFINISHED ledger rests on it |
| **11** preparation | **L** | The recipe `CycleGadget`; the manifest bound to the KEPT brief (R3, seven bindings); `ClaimAxes` promotion (S2); `CoverageLedger` consumption (S1); `NOT READ`; `Write it myself`; `Keep`; reopen-after-restart. **New ACs owed:** a `Keep` route and service write; `monday_briefs.project_id`; the manifest's observed revisions, observation times, coverage and resolved data boundary (11 AC2 names only decisions and omissions, which `CONTRACTS.md:53` does not satisfy); the recipe pick; `ClaimAxes` and `CoverageLedger` promotion |
| **12** meeting outcomes | **L** *(re-judged up from M)* | Five D3 rows say MISSING for this posture alone: the claim axes on a proposal; the transcript span; the proposal→job/attempt link; the turns-read numerator; and confirm-invalidates-support (R5). Each is a schema or service change, not a face change. **New ACs owed:** all five, plus the job identity on the face and accept/reject driving the acceptance axis (the routes exist at `decisions.py:57,61`) |
| **13** continuity | M | `CURRENT` / `SUPERSEDED` / `OWED`; `Carry into brief` by reference; the chain surviving restart. Depends on 11's manifest. **New AC owed:** `ProjectButton` (S6) consumption on the recall faces |
| **14** People preparation | S--M | Not previously in this table. Posture 5's `OWED` section and posture 3's `CARRIED FORWARD` both touch permitted People context; story 14 owns the boundary and this design draws nothing that crosses it. **No protected material appears on any board** |
| **15** attention **and posture 6** | **L** *(re-judged up from M; posture 6 has no other home)* | The cap and the true total (S4), the full ranking key, `_item_id` wiring, the traceable-sources disclosure, the changed-set edge, and the promotion of `CoverageLedger` (S1), `RepairRow` (S3) and `ProjectButton` (S6). **Plus all of posture 6**, which had no story at all: the `REPAIRS` wing, the six work states, `STILL TRUE`, and `THE RUNTIME`'s consumption of HS-200-02's identity. **New ACs owed:** the honest total in the display; the ranking key including the no-due case; the three species promotions; the six work states; `STILL TRUE` after a source failure. *If the orchestrator prefers, posture 6 splits out as a new story at the end of the phase (IDs stay stable, new IDs go at the end -- DELIVERY.md "Review and delivery units"); this design does not choose.* |

**The biggest unknown is no longer the manifest -- it is posture 4.**
Counsel established that two frozen source manifests already exist
(`project_updates.source_manifest_json`,
`project_reviews.source_manifest_json`) and that the
`refinement_attachment_*` triple supplies revision, sha256, a frozen
snapshot and a named stale repair. Story 11's manifest is **seven new
bindings over existing mechanics**. Story 12, by contrast, must add a
claim vocabulary, a span, a job link and a read counter to a table that
has none of them, and it must do it before three boards can be built
honestly. If story 12 proves wider than one story, the fallback is to
ship posture 4 with `PROPOSAL` and the two existing states only, draw no
support chip and no unknowns, and say so out loud -- rather than shipping
a review face that prints an axis the store cannot hold.

---

## Addendum -- counsel's read (2026-09-06): BOUNCE, the rulings

Counsel's read: `assets/counsel-on-design-200-09.md` (VERDICT: BOUNCE
on P0-1..P0-4; conditions C5--C21; hunts H1--H9). The orchestrator
ruled; this document is rewritten to the rulings below rather than
annotated around them.

| # | Counsel's item | The ruling | Where it moved |
|---|---|---|---|
| **C1** (P0-1) | The six 393 boards are not the same faces -- nine measured breaks: `Find support` becomes `Open source`, the EgressChip and receipt vanish from a face a model produced, a claim and an unknown are dropped, a whole `OWED` section and a filter vanish, every `SOURCES` row loses its verb, a coverage row vanishes, `Open transcript` and `Open` vanish | **PAID in full.** All six 393 boards redrawn as the SAME faces: same verbs, same egress, same coverage rows, same unknown tokens, same filters, same sections, and every section count equals its drawn rows. `P3BriefPhone` keeps `NO SOURCE · Find support`, the EgressChip and the receipt | Every `*Phone` board; D1 gains the both-widths law; D5 beat 8 restated |
| **C2** (P0-2) | The display line carries the cap, not the total; `README.md:60-62` requires an honest total | **PAID.** The display line is the TRUE total (`17 need you across 3 projects`); the caption carries the cap (`NEEDS YOU 5 OF 17`); `12 MORE · Show all` stays. The five drawn rows now span three Projects. **The cap of five stays until his word** (concern 3 splits: the total is ruled now, the number is his) | D1 new law; D2(b).1; `P2Arrival`, `P2ArrivalPhone`; D5 question 1 |
| **C3** (P0-3) | Posture 4 draws a claim vocabulary the meeting store does not have, and D3 does not say so | **PAID.** D3's meeting seam gains **five** MISSING rows (the four counsel named, plus R5's confirm-invalidation): claim axes on a proposal; the transcript span; the proposal→job/attempt link; the turns-read numerator; confirm does not invalidate support. **Story 12 re-judged M → L**, and named the biggest unknown in the phase | D3 meeting seam; D2(d) banner and Partial/Resumed rows; D4 hunt 13; Sizes |
| **C4** (P0-4) | The coverage law is not universal, and `N` is undefined | **PAID.** A `COVERAGE` section now rides above the answer on `P1Ask`, `P1Running`, `P1RouteUnset`, `P1Phone`, `P3Prepare`, `P3Brief`, `P3BriefPhone`, `P3PrepareNoModel`, `P4Processing`, `P4Review`, `P4ReviewPhone`, `P2Arrival`, `P2ArrivalOne`, `P2ArrivalPhone`. `SOURCES N` appears once and draws N rows. **`N` = the count in state `available`**, so `N == M` is unreachable while incomplete. The head no longer repeats the fraction the section states | D1 two new laws; every posture-1/3/4 board; D2(a)(c)(d) |
| C5 | `Keep` has no route and no service write; `monday_briefs` has no `project_id` | **PAID.** Both named MISSING in D3's preparation seam, with `monday_brief.py:100-140`, `schema.py:2281` and `schema.py:2274-2282` cited. **Story 11 owns both**, with ACs owed | D3; Sizes story 11 |
| C6 | "C3's versioned manifest has no record" is too absolute | **PAID.** D3 now says two frozen source manifests DO exist (`schema.py:3941`, `:3916`) and the true statement is "no manifest is bound to a brief". Story 11's unknown shrinks to **seven bindings over existing mechanics** | D3; D2(c) "The manifest"; Sizes closing paragraph |
| C7 | "MISSING: accept / reject" is false -- they exist at `decisions.py:57,61` | **PAID.** Verified on this branch (`transition(..., "accept"/"reject")`). D3 corrected and the wrong router named. **`BASELINE.md:69` carries the same error and is flagged for the orchestrator** -- this story does not edit BASELINE.md | D3 meeting seam; Sizes story 12 |
| C8 | Continuity is drawn on 6 of 21 boards, and D2(g) names two writes as ways back | **PAID.** The Project is a library `Button` in a `role="group"` region (`ProjectButton`, S6) on **every** posture, at both widths. D2(g) rewritten: the column now names what NAVIGATES, and `Confirm`/`Carry into brief` are labelled writes | D1 new law; D2.0 S6; D2(g); every board |
| C9 | The refused `Prepare` is byte-identical to the enabled primary; 0/21 boards use `disabled` | **PAID.** `button(..., off=True)` draws `disabled` + `aria-disabled`, flat, dashed, muted. Both refusal boards now use it, so one refusal has one grammar | D1 new law; `P1RouteUnset`, `P3PrepareNoModel`; D2(a) failed row |
| C10 | `OWNER · PRIYA?` asserts a name it cannot support; `DEADLINE · 2026-12-31` prints a value as a fact | **PAID.** `OWNER · PRIYA?` → `OWNER · UNKNOWN`. The values are printed AND typed unsupported: `DEADLINE 2026-12-31 · NO SOURCE`, `NUMBER 95% · NO SOURCE` | D1 new law; `P3Brief`, `P3BriefPhone`, `P4Review`, `P4ReviewPhone` |
| C11 | The stated ranking cannot produce the drawn order, and says nothing about the no-due case | **PAID.** The full four-class key with its tie-break is stated in D2(b).2, the head token names the classes, and `P2Arrival`'s five rows are redrawn in exactly that order. Severity is kept as the reason token's ink, not dropped. `_item_id` (`:135-143`, zero callers) named as the dedup key rather than treated as unwritten | D2(b).2; `P2Arrival`, `P2ArrivalOne`, `P2ArrivalPhone`; D3 |
| C12 | Eleven of sixteen gaps have no AC; posture 6 has no story; story 14 is absent | **PAID.** Every gap now names its owning story and the AC it owes, in Sizes. **Posture 6 lands on story 15**, which is re-judged M → L; the alternative (a new story at the end of the phase) is offered to the orchestrator, not chosen here. **Story 14 added** to the table | Sizes, rewritten |
| C13 | Footer verbs lead where the face already is; `Open` is both a verb and a state chip on one face | **PAID.** The footer names only the inactive wings (`Unfinished`, `Repairs` on the search face; `Search`, `Unfinished` on the repairs face). The `OPEN` state chip is gone -- the `OWED` section names the state | `P5Recall`, `P5RecallQuiet`, `P5RecallPhone`, `P6Repair`, `P6Resume`; D1 amended A.11 law |
| C14 | The name is said twice on three faces, and D2(d)'s TEXT asks for it | **PAID.** The text is fixed first: D2(d) no longer asks for the meeting name in the head. The meeting's name is in the title bar only. `P5RecallQuiet`'s empty region no longer repeats its own display line as a token | D2(d); `P4Review`, `P4Processing`, `P4ReviewPhone`, `P5RecallQuiet` |
| C15 | Row-verb grammar is not one grammar; two primaries on one face | **PAID.** One filled primary per face -- the action the face is FOR. One verb per row; secondaries in the row's `MORE` disclosure (`Edit`/`Dismiss`/`Open evidence`; `Discard`) | D1 two new laws; `P4Review`, `P4ReviewPhone`, `P6Repair`, `P6Resume`, `P6Phone`, `P2Arrival` |
| C16 | 67 of 211 buttons unlabelled; the mic is labelled with its field's name; three spellings of the mic label | **PAID.** **275 buttons, 318 accessible names, 0 unlabelled** across all 22 boards (the surplus is the `role="group"` regions). The mic is `Dictate into <field>` everywhere, including the `Library` specimen | Every board; D1 amended voice law; D2(a)--(f) accessible-name blocks |
| C17 | `JIRA CREDENTIAL EXPIRED` on a confluence row; one failure class, two owning verbs | **PAID.** The token names its own provider (`CREDENTIAL EXPIRED · CONFLUENCE`). One failure class, one verb: both credential/authorization failures take `Reconnect`; an unreachable engine takes `Check` | D1 new law; `P3Prepare`, `P3Brief`, `P3BriefPhone`, `P3PrepareNoModel`, `P6Repair`, `P6Phone` |
| C18 | The all-clear's one prose line is a calendar fact he has none of; `P3Prepare`'s head invents an 11:00 | **PAID.** `P2ArrivalQuiet` drops the prose line entirely and carries `NO CALENDAR · Connect calendar` plus the `BRIEF · Generate` row. `P3Prepare`'s head reads `Prepare a brief` | `P2ArrivalQuiet`, `P3Prepare`; D2(b) empty-complete row; D4 hunt 1 |
| C19 | `Material` and `SurfaceIdentity` declared nowhere; four table rows unspecimened; `ConfirmVerb`/`EditInPlace` absent from `contract.md` | **PAID.** The reuse table is now 24 rows, every one specimened on the `Library` board, including `Material`, `SurfaceIdentity`, `PadGadget`, `CheckGadget token`, `countToken` and `CitationChips`. `EditInPlace` and `ConfirmVerb` are flagged in warning ink as **not in `contract.md`**, and canon B's documentation is named as owed | D2.0; `Library.dc.html` |
| C20 | The two `ThreadComposer` residues are miscounted as one and mislocated | **PAID.** Two separate residues at their true lines: a raw `<textarea>` at `:968` (flagged by the comment at `:966`; a mic-law site the scanner cannot see, carried under rule `B`) and two raw `<button>`s at `:985-1004` (rule A.1) | D2.0; D3 shared-experience seam |
| C21 | Twelve citations off by 2--13 lines; two materially wrong | **PAID.** `Arrival` is declared at `ChairHome.tsx:345`; `hasAxes` is `UpdatePosture.tsx:141`; `build_aggregate` is `:202`; `headlineFor` is `:247-254`; the sort is `:436-447` and the render `:812`; accept/reject are `decisions.py:57,61`. The banner no longer claims more than was checked | Banner; D3 throughout |

### The rulings on the orchestrator's own concerns (R1--R5)

| # | Concern | The ruling |
|---|---|---|
| **R1** | Two shipped faces edited to promote `RepairRow` (S3) | **Promote the species; leave both call sites behaviourally identical** (175: a replacing face keeps its verbs); retire the duplicate in a later story. Converging `ChairHome.tsx:923-929`'s raw `<span>` on `StateChip` rides free inside the promotion -- it is species canon, not a behaviour change |
| **R2** | Thread draft custody is in-memory | **The face states the limitation** with the token `DRAFT NOT SAVED` (drawn on `P6Repair`, `P6Phone`, and specimened on `Library`) unless persistence proves trivial. The ruling had nowhere to land -- the phase's only draft AC is 28 AC1 at G3 -- so **story 10 gains the AC** |
| **R3** | The evidence manifest | **Bind the manifest to the KEPT brief only**, reusing `refinement_attachment_revisions`' revision + sha256 mechanics (`refinement_context_service.py:1105-1111`, `:25-43`, `:1113-1119`) and `_coverage_row`'s eight fields (`needs_you_aggregate.py:91-113`). Seven new bindings; everything else is reuse. The "no such record exists" claim is corrected (C6) |
| **R4** | The one-Project face is not drawn | **Draw it.** Board `P2ArrivalOne` -- his desk, the `ProjectButton` withheld from every row, `headlineFor`'s no-clause headline. It is beat 1 of his walk |
| **R5** | `Edit` has no route | **Edit-then-confirm is lawful** and the routes are verified (`proposals.py:66,86`; no PUT/PATCH exists). But C2 requires the edit to drop support to `LINKED · EDITED`, and **the confirm route does no such thing today** -- so it is named MISSING in D3's meeting seam and owned by story 12, rather than left for the face to lie about |

## Addendum 2 -- counsel's re-read (2026-09-06): RATIFY-WITH-CONDITIONS

Counsel re-read the rewritten design and all twenty-two boards.
**VERDICT: RATIFY-WITH-CONDITIONS** -- C1--C21 paid, nothing unpaid;
two new conditions and two notes. All four are RULED accepted and
applied below.

| # | Counsel's condition | The ruling | Where it moved |
|---|---|---|---|
| **N1** (P1) | `P2ArrivalOne` does not obey the ranking key `P2Arrival` states -- and the key is missing the class his desk actually has: a meeting whose intelligence has **not run** | **PAID.** The key gains a fifth class and the tie-break is stated: **OVERDUE · DUE TODAY · NOT RUN (a meeting owed a review) · NO DUE DATE (changed) · WAITING**, tie-broken in every class by the stable item id. The head token names all five on **every** board that ranks. `P2ArrivalOne` is redrawn in that order and now OPENS on `NOT RUN · 2 DAYS`, with `Run intelligence` as its one filled primary -- because that is the row his desk actually offers | D2(b).2 rewritten with the five-class table; D2(b) one-Project state row; `P2ArrivalOne`, `P2Arrival`, `P2ArrivalPhone` |
| **N2** (P1) | Seven faces draw a `COVERAGE` section AND a `SOURCES` ledger, so the same source is drawn twice | **PAID.** On a face that already lists every source, coverage is the head **TOKEN** (`COVERAGE · N OF M`) and the gap is marked in **that one ledger row** -- its own state chip, its `OBSERVED hh:mm`, and its repair verb drawn raised. No second section. **The arrival and the meeting faces KEEP their `COVERAGE` section**, because they list no sources of their own. `P1Running` gains the `SOURCES 4` ledger its token now points at | D1 new law; D2(a) element 3 and its state table; D2(c) both faces; `P1Ask`, `P1Running`, `P1RouteUnset`, `P1Phone`, `P3Prepare`, `P3PrepareNoModel`, `P3Brief`, `P3BriefPhone` |

**Counsel's notes, folded.**

- **C1 residue -- three secondary verbs dropped at 393.** `Ask` is
  restored to `P1Phone`'s footer row and `Search` to `P6Phone`'s. The
  third, `Open transcript` on `P4ReviewPhone`, was **already present**
  in the C1 redraw -- it is drawn twice there, on the coverage row and
  in the footer, exactly as at 1440. Verified by an `aria-label`
  census over all six 393 boards.
- **C17 note -- the failure chips stay distinct.** `P6Repair` and
  `P6Phone` previously drew one `CANT CHECK` for three different
  failures. The aggregate's seven repair tokens (`_repair`,
  `needs_you_aggregate.py:65-87`) are seven different facts, and the
  boards now carry `CANT CHECK` · `ENDPOINT UNREACHABLE` ·
  `CREDENTIAL EXPIRED`, each with its own reason naming its own
  provider. The C17 ruling constrains the **verb** (one failure class,
  one verb), never the token: the verb says what to do, the chip says
  what happened. The same three tokens now ride on `P3Prepare`,
  `P3PrepareNoModel`, `P3Brief` and `P3BriefPhone`, so one failure
  reads the same way on every face it appears.
- A closed `Disclosure` renders no children, so `Edit`, `Dismiss`,
  `Open evidence` and `Discard` appear on **no** board at either width
  -- they are behind a `MORE` trigger that is drawn closed. That is the
  same at 1440 and 393, so C1 holds; the design names them in D2(d)
  and D2(f) rather than the artboard.

### Unresolved concerns, for his eye

Two of the original nine are ruled above (R1--R5 covers 5--9). What
remains is his.

1. **The pilot stream is not chosen.** BASELINE.md's one blocking
   question -- which real transformation stream is the pilot and which
   sources belong to it -- is unanswered. Every board uses a synthetic
   *Q4 platform* Project. The design does not depend on the answer; the
   WALK does, and beats 3 through 6 cannot run honestly until he names
   the stream.
2. **The model route is his call.** HS-200-04 can repair the unset key
   without him, but choosing between the two ready LAN routes and a
   cloud route decides whether his meeting transcripts leave the
   machine. The design puts that choice beside the verb; it does not
   make it.
3. **Five items is a cap he has not seen.** The honest total is ruled
   and fixed. The NUMBER is his: walk question 1.
4. **`Coverage incomplete` may read as an error.** Already shipped by
   HS-200-07, unchanged here, and now on eleven more boards' worth of
   grammar. His ear decides before stories 11 and 15 spread it further:
   walk question 6.
5. **`DRAFT NOT SAVED` is a limitation stated, not fixed.** R2 chose
   honesty over persistence. If the token worries him more than the
   loss would, story 10 persists instead: walk question 7.

### Not paid, carried to the build lane

- **Whether `RoomAskWell`'s free text is persisted anywhere durable is
  UNKNOWN.** Counsel did not trace it and neither did this story.
  `RESUMED AFTER RESTART · SAVED 09:04` and the whole `UNFINISHED`
  ledger rest on it. Story 10 must trace it before building on it.
- **The changed-set notification gap and the MCP steering residue are
  BASELINE.md's claims, not verified seams.** D3 marks both as such.
- **`ACCEPTANCE.md:209` lists coverage as "available, stale, failed,
  excluded, missing"** while C4 and the code say `forbidden` and
  `unavailable`. This design follows the code. Correcting
  `ACCEPTANCE.md` is the orchestrator's, not this story's.
- **`BASELINE.md:69` repeats the accept/reject error** corrected in D3.
  Flagged, not edited -- this story writes only its own files.
- **No test was run and no live face was opened.** Every judgment in
  this document is against the rendered artboard and the read source,
  not against a built face.

---

## Addendum 3 -- corrections from story 10's trace lanes (2026-09-07)

Story 10 was opened, and the ratified design required it to trace
`RoomAskWell`'s durability before building on it. Three read-only lanes
ran. What they found corrects five premises of this document, resolves
its one UNKNOWN, fires one of its own conditional rulings, and splits
the story. Counsel ratified this design with conditions; nothing below
redraws a board or changes a face. Where a premise moved, the reason is
named.

### The UNKNOWN is resolved: the ask persists nothing

D3's preparation seam asked whether `RoomAskWell`'s submission is
durable. It is not, on any path. The typed text lives in `useState`
(`ProjectRoomCore.tsx:1387`); `runAsk` states it in its own docstring
(`web/src/desk/ask.ts:127`, "Persists nothing -- keep/bin is yours");
the kernel journals a payload **hash**, never the prompt
(`holdspeak/kernel/inference_runner.py:63-66`); `ask_results.payload_json`
(`holdspeak/db/schema.py:2069-2076`) holds the answer **without the
question** -- neither `_ask_projection`
(`holdspeak/services/ask_service.py:416-440`) nor `_routed_projection`
(`:371-414`) writes a `prompt` key; and `RoomAskWell` never calls
`keepAsk`, which only `web/src/desk/components/AskPanel.tsx:197` does.
One conditional pre-dispatch write exists
(`inference_adoption_material_snapshots.payload_json`, gated at
`ask_service.py:365-369`) and its migration family is **absent from the
owner's database**, read read-only. `RESUMED AFTER RESTART · SAVED
09:04` and the `UNFINISHED` ledger must therefore be **built**, not
bound.

The complete unfinished machinery does exist, for Thoughts:
`list_unfinished` (`holdspeak/services/refinement_thought_service.py:272-295`,
its own docstring calls itself "the Resume projection"), durable raw
words (`refinement_thoughts.raw_utf8`, `schema.py:890`), `resume_order`
and its index (`:902`, `:909-910`), restart recovery
(`recover_refinements_on_startup`, `:756`) and host leases
(`schema.py:2080-2086`). No `refinement_*` table carries a Project
binding, so a Project-scoped unfinished ledger is new schema by either
route.

**The sharpest honesty problem on this seam:** the **dictated audio**
for this very field already survives a browser restart, through
`draftScope={project-ask-${projectId}}` (`ProjectRoomCore.tsx:1455`)
into IndexedDB (`web/src/lib/pendingVoice.ts:39-110`). Only the typed
words are lost.

### Ruling R2 fires its own escape hatch: the draft is persisted

R2 said the face states the limitation with `DRAFT NOT SAVED` **"unless
persistence proves trivial"**. It proved trivial. The precedent already
ships for typed text -- `useLedgerFilter`
(`web/src/desk/surface/LedgerFilter.tsx:17-49`) persists a typed query
across reloads in about 25 lines -- and the composer's draft store has
exactly one writer (`updateField`,
`web/src/desk/threadComposerDrafts.ts:25-37`) and one eraser
(`clearThreadComposerDraft`, `:17-23`), in a 45-line file, with a
JSON-safe payload.

**The condition ratified in this document has fired, so the draft is
persisted and `DRAFT NOT SAVED` is drawn on no face.** The store is
`sessionStorage`, not `localStorage`: a draft can hold dictated meeting
material (`handleMicText`, `ThreadComposer.tsx:901-907`), and session
scope survives the reload and the crash restore R2 was about while
dying with the tab, so orphaned drafts and expiry never arise. One trap
recorded for the build: rehydrating `sending: true` leaves the composer
permanently disabled (`:977`, `:999`) -- force it false on hydrate.

**Walk question 7 is retired.** The owner is no longer asked whether
`DRAFT NOT SAVED` reads as honest or alarming, because no face says it.
Six questions remain his.

### Three premises in D2.0 and D3 were wrong

1. **Residue 1 is already paid.** `MicButton` is wired at
   `web/src/desk/components/ThreadComposer.tsx:981`, and the canon
   scanner is **not** blind to `<textarea>` -- it matches it under rule
   `B` (`scripts/ux_canon_scan.py:549`) and under the voice law
   (`:334`). The live scan reports `mic: 0`. There is no mic debt and no
   scanner debt at this site. What remains is the separate question of
   whether the textarea should become a library species; that is a
   library story, not story 10's, because `PadGadget` would need
   `forwardRef`, `onSelect` and prop spread before it could stand in,
   and 13 e2e locators plus about 20 test ids ride the current markup.
2. **Residue 2 is five raw buttons, not two** -- `ThreadComposer.tsx:53`,
   `:986`, `:995`, `:1088`, `:1096`.
3. **The library `Button` has no `unavailable` variant.** Its variants
   are `primary | secondary | ghost | danger`, plus `dense` and
   `loading` (`web/src/components/signal/Signal.tsx:21-33`); a refused
   verb is native `disabled`, which is what the D2(a) failed state
   already draws. The D2.0 table's parenthetical is corrected here
   rather than in place.

Citation paths are repaired in place throughout: `ThreadComposer.tsx` is
`web/src/desk/components/ThreadComposer.tsx`; the return-to-task files
are `web/src/features/concierge/useConciergeController.ts`,
`web/src/pages/cores/SettingsCore.tsx` and
`web/src/pages/cores/dictation/SpeakFace.tsx:288-289`, which has a
**second consumer this document omitted**,
`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:211-212`;
`RoomAskWell` ends at `:1472`.

### A defect on the same seam, found while tracing

`useModelLabel` (`ProjectRoomCore.tsx:1324-1364`) re-reads only on
`[projectId, targets]`, and `inferenceTargets` refreshes only through
the desk's own `refresh()`. After the owner assigns a model through
`Choose` (`:1462`) the chip still reads `MODEL · NOT SET`. That is the
state half of return-to-task failing on the very surface this design
sends him back to. It belongs to the story that owns return-to-task.

### The story splits

Story 10's five acceptance criteria are about promoting working
context. The four obligations the Sizes table added to it --
`TaskResume`, the focus half of return-to-task, draft custody and the
composer residues -- are about resuming unfinished work, and were
placed there only because "the phase's only other draft AC is 28 AC1,
at G3, which is too late to carry it". They are now
**HS-200-41 Return to unfinished work**, chartered on the convention
this document states for posture 6: IDs stay stable, new IDs go at the
end. Story 15 depends on it, because the `TaskResume` species is what
posture 6's `UNFINISHED` rows are made of.

Story 10 keeps its five criteria, is re-judged **M to L**, and gets a
wire design of its own before it is built
(`assets/settled-design-working-context.md`). Three problems its story
text does not settle: a target revision has no home and the three
target kinds disagree on what a revision is; the People boundary is a
classification problem rather than a plumbing one, since every existing
guard keys on the `person:` ref kind, the `people.*` tool family or
`thread_message_parts.sensitive` and a promoted Note is none of them;
and staleness is detect-on-read while AC3 asks for a push, with no
reverse index from a corrected record to its consumers.

### Carried out of this document, not paid here

`ACCEPTANCE.md`'s coverage row is corrected to the shipped C4
vocabulary. `BASELINE.md:69` was already corrected by counsel's read.

The A1 blind spot is **ledgered in BACKLOG.md, not paid**: rule A1
matches `r'<button[\s>/]'` per line over `content.splitlines()`
(`scripts/ux_canon_scan.py:429`, `:713`), so a tag Prettier wrote as
`<button` alone on its line never matches. Measured over non-test
`.tsx` under `web/src`, excluding the library's own files, **the
scanner sees 9 of 206 raw `<button>` tags across 77 files**, while
`tests/ux_canon_ceiling.json` records `A1: 4`. The guard for the
owner's standing ruling has not been enforcing it. The one-character
repair fails the ratchet on the spot; the honest repair is a conversion
campaign and a re-baseline that states the true number out loud.

---

## The boards

| Board | Width | What it shows |
|---|---|---|
| `P1Ask.dc.html` | 1440 | Posture 1 EMPTY -- `COVERAGE · 3 OF 4` as a head token, the ask well, the route READY with its egress, `SOURCES 4` with the gap marked in its own row |
| `P1Running.dc.html` | 1440 | Posture 1 LOADING -- five real steps, `Stop` kept, `ACTIONS 4` on its own line, and the `SOURCES 4` ledger its coverage token points at |
| `P1RouteUnset.dc.html` | 1440 | Posture 1 REFUSED -- `KEY NOT SET`, `Prepare` drawn disabled, purpose kept, coverage token and marked row kept |
| `P1Phone.dc.html` | 393 | Posture 1 -- the SAME face: the coverage token, all four sources with their verbs, and `Ask` restored to the footer |
| `P2Arrival.dc.html` | 1440 | Posture 2 -- the true total in the head, `5 OF 17` in the caption, the ranking order drawn, a dedup disclosure, `12 MORE` |
| `P2ArrivalOne.dc.html` | 1440 | Posture 2 -- **his desk**: one Project, the Project token withheld, `3 need you`, opening on `NOT RUN` under the same five-class key |
| `P2ArrivalPhone.dc.html` | 393 | Posture 2 -- the SAME face: both coverage rows, all five items, the dedup disclosure, the remainder |
| `P2ArrivalQuiet.dc.html` | 1440 | Posture 2 EMPTY-COMPLETE -- the only lawful all-clear, with no invented calendar fact |
| `P3Prepare.dc.html` | 1440 | Posture 3 -- the coverage token, the ask, ONE `SOURCES 4` with both gaps marked and their repair verbs, `CARRIED FORWARD 2` |
| `P3Brief.dc.html` | 1440 | Posture 3 -- the kept brief: coverage token, document, `CLAIMS 4` on three axes with typed unknowns, `NOT READ 1` carrying the state chip and the repair |
| `P3BriefPhone.dc.html` | 393 | Posture 3 -- the SAME face: four claims, `NO SOURCE · Find support`, the EgressChip, the receipt and the marked `NOT READ` row |
| `P3PrepareNoModel.dc.html` | 1440 | Posture 3 FAILED -- the coverage token and both marked rows KEPT, `Prepare` disabled, `Write it myself` |
| `P4Processing.dc.html` | 1440 | Posture 4 LOADING + RESUMED -- transcript coverage, one job, attempt 2, `ALREADY KEPT 2` |
| `P4Review.dc.html` | 1440 | Posture 4 -- five proposals, three axes, spans, typed unknowns, one verb per row + `MORE` |
| `P4ReviewPhone.dc.html` | 393 | Posture 4 -- the SAME face, including `Open transcript` and the receipt |
| `P5Recall.dc.html` | 1440 | Posture 5 -- `CURRENT` accented, `SUPERSEDED` dimmed, `OWED`, all five filters |
| `P5RecallPhone.dc.html` | 393 | Posture 5 -- the SAME face: all three sections, all five filters, the superseded link, the footer |
| `P5RecallQuiet.dc.html` | 1440 | Posture 5 EMPTY -- `Nothing matches` said once, the filters kept |
| `P6Repair.dc.html` | 1440 | Posture 6 -- the `REPAIRS` wing: three repairs with three DISTINCT tokens (`CANT CHECK` · `ENDPOINT UNREACHABLE` · `CREDENTIAL EXPIRED`), the unfinished ask with `DRAFT NOT SAVED`, `STILL TRUE 2` |
| `P6Resume.dc.html` | 1440 | Posture 6 RESUMED -- the six work states, one verb each, `THE RUNTIME` |
| `P6Phone.dc.html` | 393 | Posture 6 -- the SAME face: three repairs with their distinct tokens, the unfinished ask, both `STILL TRUE` rows with their verbs, and `Search` restored to the footer |
| `Library.dc.html` | 1440 | 24 species reused with their files and true specimens; 6 owed to `contract.md`; 2 reused ones undocumented |

Every board was rendered in Chromium and read against the canon before
this document was filed. **Mechanical census across all 22: one display
element each, three to five type steps each, every board exactly 1440
or 393, zero counters of zero, 275 buttons and 0 unlabelled (318 accessible names, the surplus being the `role="group"` regions).** Board
heights: 900--1130 for the 1440 desk boards (1520 for `Library`); the
393 boards run 762 to 1085.
