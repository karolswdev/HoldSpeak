# PHILO Phase 13 grounding: the faces half, jobs (the Tuesday spine, the Phase 12 fold, the ambition)

**UNCHECKED — awaiting Astra.**

**Date:** 2026-10-01. **Base:** `docs/philo-13-ground` at `89f69e346` (main `4c49651e` + the ratified plan). **Lane:** a Fedaykin docs lane (Opus 5.5) for Muad'Dib. Plan items 3c, 4 and 5 (`PLAN.md`). The sibling lane walks every surface one by one in `faces-surfaces.md`.

**Isolation.** One real hub (`tests/e2e/glass_infra.py` `_boot`) on a throwaway HOME (`mktemp -d`, removed after the walk; confirmed absent). No real HOME, no owner DB, no keychain (People ran on a FILE key in that HOME), no microphone (the hub has no recorder: `POST /api/meeting/start` answers 501; the voice leg used Chromium's synthetic tone device). The only sends went to the saved folder destination inside that HOME (two files, read back below). The intelligence and dictation engines are OFF. Five atlas cases also ran through `scripts/graph_walk.py`, each in its own fresh HOME (§1.0).

**The week** (`probes/faces-jobs-serve.py.txt`): 3 projects, each with a published update (Room routes); 4 people — 3 direct reports (Priya Nair, Marcus Chen, Dana Okafor) and 1 peer — on the encrypted sidecar, linked to projects, with a 1:1 session (2 agenda items), a grounding note and 2 accepted requests; 4 meetings this week, 3 with summaries and action items (repository producer, as the Phase 11 rigs mint them; no route makes a summary while the engine is off) and 1 with none; 2 meeting decisions (real projection); 2 desk decisions (one proposed); 2 notes; 3 calendar events (an ICS file in the HOME, the real ingest conductor): `1:1 Priya / Karol` today, `Ledger cutover sync` today, `Architecture review` tomorrow; 1 Ask Keep artifact; 1 saved folder destination; the brief (`POST /api/brief/generate`, 7 items).

**How to read the numbers.** *Gestures* = every press, tap, typed field and reload the owner makes, including the return and recovery legs. *Dead taps* = a press on the obvious thing that opens nothing or the wrong thing. *Rig s* = wall time of the walk (it includes a fixed 1.3 s settle after each gesture; it compares jobs, it is not his time). *KLM s* = a rough keystroke-level estimate of his time (1.1 s per press, 0.28 s per typed character, 1.35 s per new window to read, reload time + 2 s). At 393 every transition is a real touchscreen tap (`has_touch` context, `page.touchscreen.tap`), never a narrow screenshot alone.

## 1. The Tuesday spine

### 1.0 Totals (`probes/faces-jobs-summary.out.txt`; raw logs `probes/faces-jobs-J<n>-<width>.json`)

| Job | Width | Gestures | Presses | Typing | Reloads | Dead taps | Windows opened | Rig s | KLM s | End to end? |
|---|---|---|---|---|---|---|---|---|---|---|
| J1 morning | 1440 | 17 | 15 | 2 | 0 | 5 | 4 | 42.7 | 25 | yes, by the palette |
| J1 morning | 393 | 20 | 17 | 2 | 1 | 6 ¹ | 4 | 43.9 | 33 | yes, after a forced reload |
| J2 meeting | 1440 | 16 | 13 | 2 | 1 | 0 ² | 3 | 44.2 | 40 | partial: the live leg is blocked; summary → decision → sent |
| J2 meeting | 393 | 16 | 13 | 2 | 1 | 0 ² | 3 | 44.1 | 40 | same |
| J3 1:1 | 1440 | 37 | 27 | 9 | 1 | 1 | 4 | 50.8 | 121 | yes; the note typed 4 times |
| J3 1:1 | 393 | 37 | 27 | 9 | 1 | 1 | 4 | 50.7 | 121 | same |
| J4 project | 1440 | 22 | 17 | 4 | 1 | 1 | 2 | 36.1 | 74 | yes; the week typed by hand twice |
| J4 project | 393 | 22 | 17 | 4 | 1 | 1 | 2 | 36.2 | 76 | yes (a fresh project, see J4) |
| J5 thought | 1440 | 10 | 5 | 4 | 1 | 0 | 2 | 25.7 | 56 | yes; found by luck (newest first) |
| J5 thought | 393 | 16 | 10 | 5 | 1 | 3 ³ | 4 | 33.0 | 65 | yes, by guessing in the palette |

¹ The logger marked 5; a sixth tap (Intelligence → PEOPLE → Priya) went into an invisible closed window (F1) and opened nothing.
² The rig did not count the Record press as dead because the face changed; it is worse than dead: it says RECORDING after the hub refused (F2).
³ The logger marked 0; the three THOUGHTS-row taps opened `New Workbench`, nothing, and a `Triage Agent` workbench — none opened the thought.

**The known shortest path** (perfect knowledge, no return or failure legs), for the ambition baseline: J1 = 7 gestures (palette ×3 to the decision, palette ×3 + 1 to Priya); J2 from the summary = 9 (Dock, row, palette ×3 + type, back, pick, Send); J3 = 15; J4 = 9; J5 = 3 to capture, 1–4 to find (luck-dependent).

**Atlas cases on the rig** (`probes/faces-jobs-graphwalk.sh.txt`, outputs under `probes/faces-jobs-graphwalk/`): `case.j10.arrival_generate_brief.populated` PASS at 1440 and 393; `case.j11.write_a_thought.window_open` PASS at 1440 and 393; `case.j4.record_start.capture_recording` BLOCKED at 1440 (named: the `browser_audio_device` substitution is not implemented; the rig refuses to own a microphone). The single-window cases pass. The failures in this file appear only when the job crosses windows.

### 1.1 J1 the morning: arrive → read the brief → open what needs him today

Shots `shots/jobs/J1-*-{1440,393}.png`.

| Step | 1440 | 393 |
|---|---|---|
| Arrive | first useful pixel (headline + a NEEDS YOU row) 1.9 s; `7 need you`, NEXT `1:1 PRIYA / KAROL · 16:39` (J1-01) | 1.9 s; only 3 NEEDS YOU rows above the fold: the capture bar and a two-row Dock take ~300 of 852 px (J1-01-393) |
| Read the brief on the Chair | scroll 611 px to reach `BRIEF · 5 THINGS WAITING`; 3 rows + `2 more` (J1-02) | scroll 1353 px |
| Open the brief item (obvious try) | tap `Review decision: Freeze the old ledger on Nov 5` → **nothing** (dead) | dead |
| `2 more` | opens Intelligence → BRIEF (J1-03/04) | same, full width |
| Open the item there | tap → **selects only**; footer `SELECTED · decision · decision 94582473c9ff` (a raw id) with Acknowledge / Defer / Speak (dead for "open") | same |
| Open the decision | ⌘K, type `freeze`, pick → decision window (J1-05) | same |
| Today's 1:1 (obvious try) | tap `1:1 Priya / Karol` on the Chair → **nothing** (dead) | dead |
| Priya | close the decision → it fades but **stays in the DOM at opacity 0 and swallows the next tap** on Intelligence → PEOPLE (F1); fallback ⌘K `people` → Open People → Priya (J1-06) | same; at 393 the ghost covers the whole window area |
| The DUE TODAY item | tap `Review the rollout plan before Friday` → **nothing**; the row has only `Done` (dead) | dead |
| RETURN: reload mid-job | Intelligence and the decision window are **gone** (pullouts are not in the workspace document); People is kept but on its list, not on Priya (J1-07) | same |
| RECOVERY: the brief read fails | Chair: `BRIEF DID NOT LOAD · HTTP 500` + Retry (honest) (J1-08); Intelligence: `⚠︎ injected Try again` — the server's detail string shown raw (J1-09) | same |
| Recover | Intelligence `Try again` works; Chair `Retry` works (J1-10) | Chair `Retry` **swallowed** by the closed-Intelligence ghost; only a reload recovers (J1-10-retry-swallowed, J1-11) |

**Where he gets lost:** nothing he reads on the Chair opens. Brief rows (`ChairHome.tsx:2130-2140`, `expands={false}`, no open), calendar rows (`ChairHome.tsx:2618-2630`, no open) and commitment rows (only `Done`; `Open` exists only when a door card carries `open_ref`, `ChairHome.tsx:2013-2018`) are all read-only. The palette is the only door to a named object. People is on neither the Dock nor Go (`applications.ts:398-414`, no `dock`, no `group`).
**Context not carried:** the brief knows the item is `decision:…` but cannot open it; the Chair knows the 1:1 is with Priya (NEXT line) but the row does not open her; Intelligence → PEOPLE → Priya opens People on her `Now` tab, not on `Prep`.

### 1.2 J2 a meeting: start → live → summary → decision → send the update

| Step | 1440 | 393 |
|---|---|---|
| Start | Chair `Record meeting` → hub answers **501**; the orb turns `is-recording` and a timer runs (0:02 … 0:24 across later shots); no failure receipt (J2-01; `probes/faces-jobs-record-start.out.txt`) | same |
| Live | **BLOCKED**: no recorder in this hub; no live meeting can exist without a microphone. The face presentation of the refusal is audited above (it lies) | same |
| Summary | Dock Meetings → `Checkout latency review`: summary, topics, SEND (J2-02). Head says `4 meetings need summaries` and `SUMMARY OFF` beside three stored summaries | same; the footer chip overlaps `MD` / `SRT` |
| Decision | no decision verb in the meeting record (0 found); ⌘K `decision` → `New Decision` → a window titled **`New decision`** is created at once; type the decision (J2-03). Each try left a record named `New decision` (4 in the palette by the end) | same |
| Send | back to Meetings, pick `Team folder` → exact preview (J2-04) | the well is below the fold; scroll inside a ~540 px window |
| RETURN: close Meetings mid-send, come back | the record is **unselected**; the well is gone; 2 gestures to get back (J2-05) | same |
| RETURN: reload | Meetings window kept; selection and pick lost (J2-06) | same |
| RECOVERY: the send fails (`POST /api/channels/send` → 500) | `⚠ NO ANSWER · RESULT UNKNOWN` + `Retry` — honest (J2-07) | same |
| Send again | `✓ SAVED`; the file is on disk in the HOME: `2026-10-01-checkout-latency-review-summary-2026-10-01-2a6513bf.md` (`# Checkout latency review … ## Summary …`) (J2-08) | `…-5e464054.md` |

**Where he gets lost:** the start that is not a start (F2); the decision has no home in the meeting; the meeting record does not name its project.
**Context not carried:** the decision window knows nothing of the meeting it came from (empty context); the meeting does not show decisions made from it.

### 1.3 J3 a 1:1 with Priya: prep → notes → follow-ups

| Step | Both widths (identical counts) |
|---|---|
| Prep (obvious try) | tap `1:1 Priya / Karol` on the Chair → nothing (dead) |
| Find Priya | ⌘K `people` → Open People → Priya (4 gestures). `Now`: `YOU OWE · Review the rollout plan before Friday`; **`NEXT 1:1 · No 1:1 planned`** although the calendar holds `1:1 Priya / Karol` today and a 1:1 session exists (J3-01) |
| Prep tab | agenda 2 items only; not her open meeting actions (`WAITING ON PRIYA · Send the dry-run report` lives on the Chair), not her project (J3-02) |
| Notes | 1:1s tab → agenda item + `Add` (J3-03); Context tab → grounding note |
| RETURN: close People mid-typing | People reopens on the **list**; the draft is gone (J3-04) |
| RETURN: reload | People kept, on the list; the draft is gone (J3-05) |
| RECOVERY: the store fails (503 `people_store_unavailable`) | the **whole window** becomes `Recovery · Store unavailable` + the raw code; Priya and the draft are gone (J3-06). `Recovery` opens Settings; the People window stays stuck after the store is back, until he closes and reopens it (J3-07) — 7 gestures + retype |
| Saved | the note, typed the 4th time (J3-08) |
| Follow-up | `Now` → `Request` + `Add` → `Send me the EU shard backup plan by Tuesday` with `Accept` (J3-09). `Accept` mints **his** commitment (`people_service.py:212-214`); there is no way to record what Priya owes him from the 1:1. Nothing reaches the Chair (J3-10) |

### 1.4 J4 a project: open the Room → what changed → publish an update

At 393 the walk used `Observability uplift`, because the 1440 run had already published on `Payments ledger cutover` (one hub for both widths).

| Step | Both widths |
|---|---|
| Open (obvious try) | tap `Ledger cutover sync` on the Chair → nothing; no Room or project launcher on the Dock (0); ⌘K `Payments` → Open project (3 gestures) |
| What changed | ROOM: `Nothing needs you`, `SINCE YOU LOOKED … Nothing since` / `Created just now`; the linked meeting, its summary, its decision and its two action items are **absent** (J4-01). HISTORY: `Updated · meeting associated` (which meeting is not said), `Update published`, `Created · name` (J4-02) |
| Draft | `Draft update` → `Draft` / `Draft with model` (engine off) → the deterministic draft reads `No focus items … No decisions in this window … No upcoming actions … All sources consulted successfully` (J4-04). The composer reads Room items, not the week's meetings (`project_update_service.py:13-24`, `:315-318`) |
| Write | he types the week by hand (111 characters) |
| RETURN: close the Room without Save | typed text **lost**, no warning; the next `Draft` press makes a new revision and marks the old one SUPERSEDED; the list shows DRAFT, SUPERSEDED and PUBLISHED rows, all `just now`, with `REV` numbers (J4-05) |
| RETURN: reload after Save | the Room window comes back; the draft is under the update list |
| RECOVERY: publish fails (500) | the server's detail string raw over a warning glyph (`injected failure`); the draft is kept (J4-07) |
| Publish again | `✓ PUBLISHED`; the SEND well appears in place (J4-08) |

### 1.5 J5 capture a thought by voice, find it later

| Step | 1440 | 393 |
|---|---|---|
| Capture | Chair `Write a thought` → `Thought` window (J5-01) | same |
| Voice | `Speak the note` → `TRANSCRIPTION UNAVAILABLE Local transcription is unavailable. Your draft remains editable. Open Setup to see what this device needs.` — honest, but a sentence (UX-CANON A.3) and no verb to open Setup (J5-02) | same |
| Typed | autosaves `KEPT · 3:12 PM · IN INBOX` (J5-03) | same |
| RETURN: reload | the Thought window is gone (J5-04) | same |
| Find it later | Chair THOUGHTS: `Thought`, `Thought`, `Thought` — every thought is titled `Thought` (`newThought.ts:29`); ⌘K by a word in it: **0 results**; ⌘K `Thought`: 5+ identical rows; the first Chair row was the right one because it is newest | the three THOUGHTS-row taps opened `New Workbench`, nothing, `Triage Agent`; the palette guess found it |
| RECOVERY: save fails | `DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE` + `Retry` — honest; no automatic retry when the hub is back; `Retry` works (J5-05/06) | same |

## 2. The Phase 12 fold

Story 01 is merged (the artifact source, the pure binding `web/src/desk/floorSendBinding.ts`, `GET /api/brief/{id}`). Story 02's canvases F–J are merged as artifacts and never ratified. Below, each behaviour of stories 03–06 and each board, mapped.

| Behaviour (board) | Verdict | How it carries / why parked | Its proof (old 05 atlas, old 06 closing use) |
|---|---|---|---|
| `Send to ▸` on the spatial Floor, the list, the Object menu, compact Go (H1, H2, H2b, H2c, H5, H6) | **CARRIES, re-grounded** | The design names Floor, list and menu-bar origins only (`design/floor-send.md:57`). The in-window origin is new; see below | 05: one face case per window kind at 1440 and 393 (touch at 393); 06: the 393 leg by `Send to ▸` |
| `Add destination` with none (H3, H3b) | CARRIES | the same row in the window menu | 05 face case |
| Withheld where it cannot send (H4, G4/G4b at 393) | CARRIES | the window knows its own document; a meeting with no summary has no well today (`MeetingPullout.tsx:152-155`) | 05 face case |
| Reads loading / failed (H7a–c) | PARTLY | inside a window the document is already loaded; only the meeting summary and the Room's published update need `Fact<T>` | 05 |
| The push seam: a pick pushed into an open well; Summary → Digest keeps the destination; the Room switches to the linked update; the exact brief id (G7, G8, G9a/b, I2, I3) | **CARRIES** | this IS the in-window mechanism | 05: rendered-transition cases ending in Send + receipt; 06: real sends |
| The artifact window's SEND well and its three raw buttons as library Buttons (J1) | **CARRIES** | window-side; J4/J5 of the spine show artifacts are not reachable from their meeting, see §4 | 05: artifact send (picked, SENT, PREPARED); 06: the cold-agent artifact leg |
| The reads module and the Room link `{projectId, updateId, destinationId}` | CARRIES | needed by any origin | 05 |
| Destination icons on the Floor, their menu, Settings at the row, six channel sprites, the column wrap (F1, F2, F2b, F3, F5, F6) | **PARKED** | Floor work, by the owner's fold | — |
| The decision sprite (F4) | PARKED | Floor art; cheap; may ride a later Floor pass | — |
| The drag, the tag, refusals on the tag, release opens the preview (G1–G6) | **PARKED** | the drop | old 06 drag leg parked |
| The brief icon on the Floor; the brief row in the list (I1, I4, H6 row) | PARKED (icon) / CARRIES (the exact-id handoff, I2/I3) | | 05 handoff case |
| An artifact dropped on a folder (J2, J2b) | PARKED | the drop | — |

**What an in-window origin needs** (grounded in the Phase 11 wells):
1. **A place to say it.** The window's own menu. Today the title-bar right-click (`DeskWindow.tsx:815-821`) builds Minimize / Maximize / Close only (`windowMenuAdapter.tsx:16-56`). One `sub` entry, `Send to ▸`, built from the window's own DocRef: `desk_decision` (`documentSends.tsx:33-35`), `monday_brief` (`:28-31`), `decision_record` (`:37-39`), the meeting forms (`MeetingSendWell.tsx:31-54`), `project_update` (the Room's Update posture), `artifact` (story 01). The menu species already nests (`DeskMenu.tsx:182-201`; at ≤720 px the submenu replaces the panel, `:592`). The menu bar's Object menu reads the front window's document the same way (`DeskMenuBar.tsx:78-95`).
2. **The push.** The pick lives in a private module map (`SendWell.tsx:64`, set only at `:572`). The in-window origin needs exactly design §6's seam (one setter per well, an open well reacts) — nothing of the Floor binding.
3. **The arrival.** At 393 the well sits below the fold in a ~540 px window (J2-04-393). The pick must bring the picked row, its preview and Send into view (canvas "arrival", story 02 README N3).
4. **No reads at the origin.** The window already holds its document; `pending` only for the two facts in design §2.

**Five lines.** (1) Carries: `Send to ▸` from inside a window (new origin: the window menu and the Object menu), the push seam and its transitions, the artifact window's well and Buttons, the reads module, the exact-brief-id handoff. (2) Parked: destination icons, the drop and its tag, the brief icon, the decision and channel sprites, J2. (3) Old 05 becomes per-window face cases at both widths (touch at 393) plus the transition and artifact cases; the Floor-drop cases are parked. (4) Old 06 keeps the cold-agent artifact leg and the real sends by `Send to ▸`; the drag leg is parked. (5) Canvases H, G7–G9, I2–I3, J1 are redrawn for the window origin before build; F, G1–G6, I1/I4, J2 stay as unratified artifacts.

## 3. The ambition (Workbench 2.0 + Intuition, on steroids)

**What Workbench 2.0 and Intuition actually gave** (sources at the end): every window had the same system gadgets — close, drag bar, **depth** (front/back) and **zoom**, which toggles between two remembered size-and-position states; **screens** that the user drags down and depth-arranges, and from 2.0 **public screens** any program can share; the right mouse button shows **the menu bar of the active window**, with Amiga-key shortcuts; **AppIcons, AppWindows and AppMenuItems** (`workbench.library` V36), by which a running program puts a live icon on the Workbench, accepts icons dropped on its window, and adds items to the Tools menu; **Commodities** with a pop-key (`CX_POPKEY`) that brings a program's window to the front from anywhere; **Snapshot**, which keeps windows and icons where the user put them; **GadTools** and the Style Guide, one gadget set for every program.

**What HoldSpeak's Desk already has.** A verb registry and four menu faces (`verbRegistry.ts`; `DESK_GRAMMAR.md` §7); the window head menu (`windowMenuAdapter.tsx:16-56`); depth/zoom equivalents (`toggleMaximizePanel`, `DeskWindow.tsx:807-813`), Exposé and Switcher (`components/window/Expose.tsx`, `Switcher.tsx`), snap (`SnapGhost.tsx`); keyboard programs `⌘1`–`⌘4` (`applications.ts:84,114,135,155`); a palette (`DeskToolShelf.tsx`, label + terms ranking `:134-145`); a Dock with one live mark (`Dock.tsx:55-70`: the needs-you count or `•`); window memory for surface windows and zones (`store/workspaceStorage.ts:15-25`); Places (`ChangePlacesCore`, the screen-like idea); the library species (UX-CANON §B). **What it lacks, measured in §1:** objects named on the Chair do not open; windows forget their place; the palette does not know people or what is inside a thought; the Dock does not show his day.

**The moves, ranked by owner value.** Each is measured against §1.

1. **Everything he reads opens (one open grammar on the Chair and the brief).** *Job:* J1, J3, J4. *Observable:* J1 dead taps 5 → 0; J1 known path 7 → 3 gestures (tap the brief row → the decision; tap `1:1 Priya` → Priya on Prep); J3 prep 5 → 1; J4 open 3 → 1 when the calendar event carries a Room (`ROOM · <name>` is already drawn, `ChairHome.tsx:2624-2628`). *Smallest change:* give `BriefSection` rows an open from `source_ref` → `openPullout` (`ChairHome.tsx:2092-2140`; Intelligence BRIEF the same, `BriefView.tsx:395-401` now only selects); give calendar rows an open: `project_name` → `openProjectRoom`, a linked person → People at Prep (`ChairHome.tsx:2618`); give commitment rows their person (`ChairHome.tsx:1990-2030`). *Cost:* S.
2. **Windows that remember (Snapshot, on steroids).** *Job:* all. *Observable:* after a reload or a close, re-navigation 0 gestures instead of 2 (J2), 2 + retype (J3), 3 (J5); 0 lost drafts (J3 lost the note 3 times; J4 lost 111 typed characters). *Smallest change:* add `pullouts` and a per-window `place` (selected meeting, person + tab, the send pick, an unsent field draft) to `DeskWorkspaceDocumentV1` (`store/workspaceStorage.ts:15-25`) and restore them in `openPullout` (`compositorSlice.ts:137-152`); keep field drafts in the same document. *Cost:* M.
3. **A palette that knows his week and does verbs.** *Job:* J1, J3, J4, J5. *Observable:* `Priya` 0 results → her window (J3: 4 → 2 gestures); a word from a thought 0 → 1 result (J5 find: luck → 2 gestures); `send` today returns 16 noise rows (`probes/faces-jobs-palette.out.txt`) → `Send <front document> to Team folder`. *Smallest change:* feed relationships (`GET /api/people/relationships`), note bodies and meeting attendees into `terms`, which `rankRow` already scores (`DeskToolShelf.tsx:134-145`); register verb rows (`Send to …`, `Prep 1:1 with …`, `Draft update for …`) from the verb registry. *Cost:* M.
4. **`Send to ▸` from any document window, and from the Object menu (the fold, the AppMenuItem idea).** *Job:* J2, J4, J1. *Observable:* J2 send from an open meeting: no scroll hunt for the well; 3 gestures (right-click title → `Send to ▸` → `Team folder`, then Send) at both widths; at 393 the preview arrives in view. *Smallest change:* one `sub` entry in `headMenuEntries` (`windowMenuAdapter.tsx:16-56`) from the window's DocRef (`documentSends.tsx:28-39`); the push seam on `store.picked` (`SendWell.tsx:64`, `:572`). *Cost:* M.
5. **A live Dock (AppIcons with state).** *Job:* J1, J2, J4. *Observable:* the 1:1 time on People, `REC 12:04` on Meetings **only when the hub confirms recording** (today the orb lies, F2), an AppIcon per active project with its needs-you count: J4 open 3 → 1 gesture; J2 start shows the truth in under 1 s. *Smallest change:* generalise the one badge path (`Dock.tsx:55-70`) to per-app badges from the projections already loaded (`useProjections`, `DeskApp.tsx:186`); make `startRecording` read `response.ok` (`recordingSlice.ts:47-60`, `lib/api.ts:27-32`). *Cost:* M.
6. **The update writes the week itself (no engine).** *Job:* J4. *Observable:* the deterministic draft lists the linked meeting's summary, its decision and its two owned actions instead of `No decisions … No upcoming actions`; 111 typed characters → 0; he edits, he does not write. *Smallest change:* the deterministic composer also reads the project's linked meetings (summary, action items with owners) and linked decisions (`project_update_service.py:13-24`, `:315-318`; meetings linked through `POST /api/projects/{id}/meetings/{mid}`). *Cost:* M.
7. **Decide where the meeting is.** *Job:* J2. *Observable:* decision step 5 → 2 gestures (`Decide` in the record, type); 0 orphan `New decision` records (4 left in this walk); the decision carries its meeting and project. *Smallest change:* one `Decide` Button in the meeting record next to SEND, which creates the decision with the meeting as context and asks the title inline (no `New decision` placeholder); `POST /api/decisions` already takes `context_markdown`. *Cost:* S.
8. **The 1:1 finds its person.** *Job:* J3, J1. *Observable:* `NEXT 1:1 · No 1:1 planned` (false) → the event; the Chair's 1:1 row opens Priya on Prep with her agenda **and** her waiting meeting actions (`WAITING ON PRIYA` today lives only on the Chair); prep 5 → 1 gesture. *Smallest change:* suggest the calendar link when an event title contains an owner alias (`Priya` is saved as her alias in this walk; the link route exists, `people.py:193-204`); Prep reads the meeting action items whose owner is the alias. *Cost:* M.
9. **Screens for his day (public screens, on steroids).** *Job:* J1–J4. *Observable:* a `1:1` screen opens People at Prep and a note side by side in 1 press instead of 4–5; a `Morning` screen opens the brief and today's items. *Smallest change:* a saved set of window ids + places on top of move 2's document, offered from Places (`ChangePlacesCore`) and from the Chair's NEXT line. *Cost:* L. Depends on move 2.
10. **A pop-key for capture (Commodities).** *Job:* J5. *Observable:* a thought from anywhere in 1 key press (today: back to the Chair, scroll, `Write a thought`); the thought titled from its first words, so the Chair shows 3 different names, not `Thought ×3`. *Smallest change:* a registered verb with a global key (verb registry) that opens `openNewThought`; title from the first line on first save instead of the fixed `Thought` (`newThought.ts:29`). *Cost:* S.

## 4. Findings, ranked by owner cost

| # | Finding | Jobs | Evidence |
|---|---|---|---|
| F1 | **A closed object window stays on screen invisible and swallows taps.** After Close, the card animates to opacity 0 and stays (`pointer-events: auto`, ≥ 4 s, held until reload). At 393 the closed Intelligence window covers the whole Chair: `Retry` and every row tap go nowhere until a reload. Probable cause (read, not unit-tested): `openPullout(id)` stores the qualified id it was given (`decision:decision_…`, `intelligence:desk`; `compositorSlice.ts:137-152`), the card renders and closes with the bare `o.id` (`Pullout.tsx:60-68`), so `closePullout` filters nothing (`compositorSlice.ts:177-189`) and the faded element (`DeskWindow.tsx:645-668`) is never unmounted | J1, J5 (all) | `probes/faces-jobs-ghost-1440.out.txt`, `-393.out.txt`; J1-10-retry-swallowed-393 |
| F2 | **Record says it is recording when the hub refused.** `startRecording` awaits a bare `fetch` that never throws on HTTP errors and sets `recording` (`recordingSlice.ts:47-56`; `lib/api.ts:27-32`). After a 501 the orb shows recording and a timer runs; no receipt. In real use: a refused or failed start looks like a meeting being captured | J2 | `probes/faces-jobs-record-start.out.txt`; J2-01, J2-03 (timer 0:18) |
| F3 | **Nothing named on the Chair opens.** Brief rows, calendar rows and commitment rows are read-only; Intelligence BRIEF only selects (and shows a raw id); People is on neither Dock nor Go | J1, J3, J4 | §1.1; `ChairHome.tsx:2130-2140`, `:2618`; `BriefView.tsx:395-401`; `applications.ts:398-414` |
| F4 | **A People failure replaces the window and loses the work.** A 503 turns People into `Recovery · Store unavailable` + raw code; the person and the draft are gone; Recovery opens Settings; the window stays stuck after the store is back | J3 | J3-06, J3-07 |
| F5 | **Windows forget.** Pullouts are not persisted (`workspaceStorage.ts:15-25`); surface windows come back on their first screen; unsaved fields are lost on close or reload (People note, Room draft) | all | J1-07, J2-05/06, J3-04/05, J4-05, J5-04 |
| F6 | **The update draft ignores the week.** The deterministic draft says `No decisions … No upcoming actions` for a project with a summarized meeting, a decision and two owned actions | J4 | J4-04; `project_update_service.py:13-24` |
| F7 | **The Room does not say what changed.** `Created just now`, `Nothing since`; History says `meeting associated` without the meeting | J4 | J4-01, J4-02 |
| F8 | **Every thought is `Thought`.** Title fixed at create (`newThought.ts:29`); the palette cannot search inside it; at 393 THOUGHTS-row taps opened workbenches, not the thought | J5 | J5 logs; `faces-jobs-J5-393.json` |
| F9 | **Decisions are born as `New decision`.** No decision verb in the meeting; ⌘K `New Decision` writes a record titled `New decision` at once; abandoned tries stay | J2 | J2-03; the palette list in `faces-jobs-J2-393.json` |
| F10 | **The 1:1 does not know its event; follow-ups only flow one way.** `No 1:1 planned` beside a calendar 1:1 today; a request accepted becomes his commitment; nothing records what a report owes from the 1:1 | J3 | J3-01, J3-09 |
| F11 | **Server details shown raw.** Intelligence BRIEF and the Room's publish failure print the server's `detail` string; People prints `people_store_unavailable` | J1, J3, J4 | J1-09, J3-06, J4-07 |
| F12 | **The phone loses a third of the screen to chrome.** The capture bar + a 2–3-row Dock (window chips add a row) take 300–360 of 852 px; windows get ~540 px; the needs-you `Done` verb and the send well fall below the fold | all at 393 | J1-01-393, J1-06-393, J2-04-393 |
| F13 | **The Meetings head contradicts itself with the engine off.** `4 meetings need summaries` / `SUMMARY OFF` / `NO SUMMARY ROUTE · NO ASSIGNMENT` beside three stored summaries | J2 | J2-02 |
| F14 | **The voice failure is a sentence.** Honest, but prose (UX-CANON A.3) and `Open Setup` is text, not a verb | J5 | J5-02 |
| F15 | **Update revisions pile up.** Each `Draft` supersedes and adds a row; DRAFT / SUPERSEDED / PUBLISHED rows all `just now`, `REV 1`/`REV 2` (UX-CANON A.8 names `REV 1`) | J4 | J4-05 |

Honest states that worked: the Chair's `BRIEF DID NOT LOAD · HTTP 500` + Retry; the send's `NO ANSWER · RESULT UNKNOWN` + Retry; the Thought's `DID NOT SAVE` + Retry; the Room kept the draft on a failed publish.

## 5. Open forks for the owner

1. **What a tap on a name does.** Default: **open the object in its own window** (decision → decision window; event → its person or Room; commitment → the person). Alternative: unfold under the row (well), as the brief does now.
2. **What the Desk remembers across a reload.** Default: **every open window, where it was, and an unsent draft** (Snapshot is automatic; no Snapshot verb). Alternative: windows only, never drafts.
3. **Where `Send to ▸` lives in a window.** Default: **the window's title-bar menu and the Object menu**, both from one composition; the SEND well stays the one place where Send is pressed. Alternative: a `Send` Button in each window's footer.
4. **Should the update draft read the week without the engine?** Default: **yes** — linked meetings' summaries, decisions and owned actions, each line with its claim ref; he edits. Alternative: keep the deterministic draft to Room items and wait for the engine.
5. **Screens for his day.** Default: **not yet** — first moves 1–3 (open, remember, palette); a saved window set comes after, on Places. Alternative: chart Morning / Meeting / 1:1 / Project screens now.

## Unknown (not verified here)

- F1's cause is read from code, not proven by a unit test; the ghost was observed in headless Chromium at both widths. Not verified in the owner's browser.
- The live meeting leg (J2 "live"): no recorder in this hub; nothing about the live window is observed here.
- Engine-on behaviour: model drafts, transcription, summaries generated live.
- Seconds are rig seconds and a KLM estimate, not a timed human.
- J2 and J4 at 393 ran on the same hub after the 1440 runs; J2's well therefore showed earlier sends (`Send again`); J4 used a second project to start clean.
- The Dock clipping its left edge with several window chips at 1440 (seen in shots) is the frame lane's subject; not measured here.
- `has_touch` taps are Playwright touch events, not a physical device.

## Sources (Workbench / Intuition)

- [Intuition Windows — AmigaOS Documentation Wiki](https://wiki.amigaos.net/wiki/Intuition_Windows) (zoom gadget: two preset sizes and positions; depth gadget)
- [Intuition Screens — AmigaOS Documentation Wiki](https://wiki.amigaos.net/wiki/Intuition_Screens) (screen drag and depth gadgets)
- [Workbench Library — AmigaOS Documentation Wiki](https://wiki.amigaos.net/wiki/Workbench_Library) (AppWindow, AppIcon, AppMenuItem)
- [Commodity Tool Types, RKM Libraries ch. 31](http://amigadev.elowar.com/read/ADCD_2.1/Libraries_Manual_guide/node0406.html) (`CX_POPKEY`)
- [Workbench (AmigaOS) — Wikipedia](https://en.wikipedia.org/wiki/Workbench_(AmigaOS)) (2.0: GadTools and the Style Guide, Commodities, public screens, right button = menus, Snapshot)
- `pm/roadmap/holdspeak/phase-148-menu-glyphs/assets/audit-amiga-reference.md` (menu grammar, ghosting law)
