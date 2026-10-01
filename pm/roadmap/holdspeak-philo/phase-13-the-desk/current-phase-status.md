# Phase 13 - The Desk

**Last updated:** 2026-10-01 (DRAFTED by the Fedaykin docs lane for Muad'Dib from PROPOSAL r2 and the five forks the owner ruled; unchecked.)

**Status:** DRAFT, 2026-10-01 — UNCHECKED, awaiting Astra; then the owner's ratification.

## Goal

The Desk becomes a Workbench desk he keeps open all day. Every window and the frame around them hold together: work is never destroyed, every face tells one truth, everything he reads opens, the Desk remembers where he was, and it looks and behaves like Workbench 2.0+ on steroids (gadgets, a screen title bar, one material, live AppIcons, a palette that does verbs, Send from the window he is reading). Everything except the Floor.

## Authority

The owner, 2026-10-01, verbatim:

> "I do want us to restructure and refine our Desk experiences. We've been soooo heavily investing into the floor, and totally ignoring the desk..."

> "Make sure we want an incredible exeprience. The whoe Workbench 2.0+ on steroids needs to really lean on steroids. Get it?"

His answers (2026-10-01, verbatim):

| Question | His word | What it rules |
|---|---|---|
| What is "the Desk"? | "Both, the whole thing" | The windows he works in and the OS frame (menu bar, Dock, registry, window management, pullouts, the Chair dock, palette). Everything except the Floor. |
| Phase 12? | "Fold it into the Desk work" | Phase 12 story 01 carries; its window-side intent becomes C5; its Floor work is parked. |
| How to start? | "Audit, then propose" | The grounding below, then PROPOSAL r2, then this charter. |

The five forks of PROPOSAL §5, ruled 2026-10-01:

| # | Fork | His word | What it rules |
|---|---|---|---|
| 1 | How far does the Workbench look go? | "All the way" | C1: gadgets, a screen title bar, one material, the Chair as a desk of windows; canvas first against seven criteria. |
| 2 | What does a tap on a name do? | "Opens its own window" | B1: every named row opens its object in its own window. |
| 3 | What does the Desk remember across a reload? | "Everything" | B2: every window, its place and any unsent draft, automatically. |
| 4 | Saved window sets in this phase? | "Later" | D1 is OUT. Parked in BACKLOG; after B2 proves return in real use. |
| 5 | Where does `Send to ▸` live in a window? | the default stands (he did not object) | C5: the title-bar menu and the Object menu, one composition; the SEND well stays the one place Send is pressed. |

Muad'Dib's ruling (PROPOSAL §5, not forked) stands: **B5** — the update draft reads the week without the engine.

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); Article V (he presses Send); Article III, honest egress; Article XI, the kernel; UX-CANON §A (A.1 every verb the library Button, A.2 the canvas before build, A.3 no prose, A.4 no modals, A.8 no counter of zero, A.9 egress where egress happens, A.10 honest states, A.11 a verb that does nothing is withheld, A.13 the owner sees shots before merge), §B (the species), §E (the review protocol) (`docs/internal/UX-CANON.md:17-58`); his standing rule "never delete — park instead"; his Phase 10 and 11 rulings: **"You, every time"**, **"Saved destinations"**, **"I'm the only user"**, **"Stop being so paranoid"**, **"if it changes, we re-send"**; his ruling on thread authority (2026-09-29: a thread stops for his press on EGRESS, AUTHORITY and CONFIG); the 12 px floor (2026-09-21).

## The roots

- **Tenet 6 (Workbench 2.0+ on steroids):** he named the gap. The Chair at 1440 reads as a black web dashboard of rows and chips (`grounding/shots/surfaces/01-chair-pop-1440.png`). Workbench gave every window one gadget set (close, depth, zoom), right button = the active window's menu bar, Amiga-key shortcuts, AppIcons with live state, Commodities pop-keys and Snapshot (`grounding/faces-jobs.md:146`). Wave C is that, on steroids.
- **Tenet 7 (a Senior Architect with reports):** the unit of value is the Tuesday spine J1–J5 (the morning, a meeting, a 1:1 with one of his three reports, a project, a thought), walked end to end with return and recovery (`grounding/faces-jobs.md:13-115`).
- **Tenet 3 (help and accelerate):** J1 has 5 dead taps at 1440; J3 takes 37 gestures and the note is typed four times (`grounding/faces-jobs.md:17-28`). One open grammar, one meaning of "needs you", a Desk that remembers.
- **Tenet 1 (no over-engineering for safety):** no new event system (the RuntimeBus exists, `grounding/structure.md:166-192`); no virtual-screen model; park is a state on the existing row, not an archive framework (`grounding/structure.md:224`); palette Send only opens the preview.
- **Tenet 2 (not even pre-alpha):** no compatibility layer. Old doors stay only until the new path is walked; then they park.
- **Tenet 5 (component framework):** one material as tokens, worn by every `DeskWindowFrame` host (19 host files, `grounding/structure.md:151`); the kit already has rows, wells, gadgets and footers (`web/src/desk/surface/index.ts:21`). Bodies adopt it as they are touched.
- **Tenet 4 (ASD-STE100):** failures in plain words with a verb, never raw server text (`grounding/faces-jobs.md:177`); a narrower count says what it counts ("2 need a summary").

## Status of this charter

DRAFT, 2026-10-01, written by the Fedaykin docs lane for Muad'Dib — UNCHECKED, awaiting Astra; then the owner's ratification.

Source: `docs/internal/philo/phase-13/PROPOSAL.md` (r2; Astra check r1 RATIFY-WITH-CONDITIONS, paid, `docs/internal/philo/phase-13/grounding/checks/proposal-astra.md`). This charter turns it into roadmap form. It does not redesign it. The five forks are ruled (Authority).

## The grounding (main `4c49651e`; no drift in `web/src` or `holdspeak` to `c3855bbf`)

`grounding/` = [`docs/internal/philo/phase-13/grounding/`](../../../../docs/internal/philo/phase-13/grounding/).

| Part | Owner | What it holds | Check |
|---|---|---|---|
| [PLAN.md](../../../../docs/internal/philo/phase-13/grounding/PLAN.md) | Muad'Dib | the bar (Job / Workbench 2.0+ / Steroids), the Tuesday spine J1–J5, the two halves | Astra r1, paid (`checks/plan-astra.md`) |
| [inventory.md](../../../../docs/internal/philo/phase-13/grounding/inventory.md) (S0) | Astra | 23 manifest actions, 7 object windows, 14 pullout components, the frame, the handoffs | Muad'Dib RATIFY (`checks/structure-muaddib.md`) |
| [structure.md](../../../../docs/internal/philo/phase-13/grounding/structure.md) | Astra | §1 registry census; §2 window manager (what survives a return); §3 component grammar; §4 live state; §5 Phase 12 fold and the hard-delete paths; §6 consolidation map; §7 ambition | Muad'Dib RATIFY |
| [faces.md](../../../../docs/internal/philo/phase-13/grounding/faces.md) → [faces-surfaces.md](../../../../docs/internal/philo/phase-13/grounding/faces-surfaces.md), [faces-jobs.md](../../../../docs/internal/philo/phase-13/grounding/faces-jobs.md) | Muad'Dib | every surface at 1440 and 393, cold and populated (187 shots, `shots/surfaces/`); J1–J5 end to end (85 shots, `shots/jobs/`); the fold map; 10 ambition moves | Astra r1, paid (`checks/faces-astra.md`) |

The six truths (PROPOSAL §2): (1) work is destroyed or forgotten; (2) the Desk does not tell one truth; (3) what he reads does not open; (4) a closed window stays, invisible, and swallows taps; (5) on the phone the frame takes a third of the screen; (6) it does not look or behave like Workbench.

## Scope

- **In:** the 18 stories below, in three waves (PROPOSAL §3).
  - **Wave A — Trust:** A1 park, never delete (story 02); A2 one meaning of "needs you" (03); A3 faces that do not lie (04); A4 close means gone (05).
  - **Wave B — Everything opens, everything returns:** B0 walk what was not walked (01, the gate on B2); B1 one open grammar (06); B2 the Desk remembers (07); B3 decide where the meeting is (08); B4 the 1:1 finds its person (09); B5 the update writes the week (10).
  - **Wave C — Workbench 2.0+, on steroids:** C1 the Workbench look (11, the face gate); C2 the missing gadgets (12); C3 a live Dock (13); C4 a palette that knows his week (14); C5 `Send to ▸` from any document window (15, the Phase 12 fold); C6 capture from anywhere (16); C7 the phone desk (17); C8 the 12 px floor (18).
  - **Consolidation rides Waves B and C; no story of its own** (`grounding/structure.md:227-265`): Live meeting joins Meetings; Rhythm, Context, Commands and Processes move under Settings or their running work; Components leaves daily view; the two Models rows become one; Ask is contextual first. Each move lands in the story whose face receives it. Old doors stay until the new path is walked; nothing is deleted.
- **Out (with their homes):**
  - **The Floor.** The owner's scope ("everything except the Floor").
  - **D1 saved window sets / screens for his day.** The owner ruled "Later" (fork 4). BACKLOG; after B2 proves return in real use.
  - **A palette `Send` that sends.** C4's `Send …` row only opens the exact preview; he presses Send (Article V; `grounding/faces.md:36`).
  - **A new event system.** C3 uses the RuntimeBus and the current read endpoints (`grounding/structure.md:168`, `:302`).
  - **A virtual-screen model** (Intuition screen depth). Separate and larger (`grounding/structure.md:19`, `:147`).
  - **Anything unwalked before B0.** Calendar snapshot, Roadmap, Repository, Delivery dossier and terminal, Chain, Coder, Directory/Zone and Info windows keep their doors as they are until B0 walks them (`grounding/faces.md:33`).
  - **The parked Phase 12 Floor work:** destination icons, the drop and its tag, the brief icon on the Floor, the decision and channel sprites, J2 (artifact on a folder), the drag leg of the closing use. Kept with their records in `../phase-12-send-from-the-floor/`.
  - **Records already deleted.** A1 stops future loss; it cannot bring back rows already deleted (`grounding/checks/proposal-astra.md`, finding 1).
  - **Engine-on behaviour** (model drafts, live transcription, live summaries). The `.43` engine is down; "engine off" excuses only the unavailable operation (`grounding/PLAN.md:132-137`).

## The Phase 12 fold

Phase 12 closes as "folded into Phase 13" once this charter is ratified (PROPOSAL §3, "The Phase 12 fold"; `grounding/faces-jobs.md:117-142`; `grounding/structure.md:195-214`). Story 01 stays done. Stories 02–06 are `blocked`, with the reason "parked — folded into PHILO-13 C5 (owner 2026-10-01)", never `done` (`../phase-12-send-from-the-floor/current-phase-status.md`).

| Phase 12 story | Disposition | What carries (and where) | Its proof in Phase 13 |
|---|---|---|---|
| 01 the artifact source and the Floor binding | done; carries as-is | `floorSendBinding.resolve` (`web/src/desk/floorSendBinding.ts:61`), `GET /api/brief/{brief_id}` (`holdspeak/web/routes/monday_brief.py:152`), `_ArtifactSource` (`holdspeak/services/document_sources.py:495`) → C5 | its focused unit proof carries only its scope; C5's rendered preview must agree with the real source |
| 02 the canvases F–J | parked — folded into PHILO-13 C5 | intent and species as evidence; never ratified. Boards H, G7–G9, I2–I3, J1 are redrawn for the window origin in C5's canvas; F, G1–G6, I1/I4, J2 stay as unratified artifacts | C5's canvas, owner-ratified |
| 03 Send to, the artifact window, the reads | parked — folded into PHILO-13 C5 | the in-window `Send to ▸`; the push seam (`web/src/desk/surface/send/SendWell.tsx:64`, `:572`); the artifact SEND well and its three library Buttons (`web/src/desk/pullouts/ArtifactPullout.tsx:38`, `:57`, `:64`); the reads module; the Room link `{ projectId, updateId, destinationId }`; the exact brief-id handoff; the same-second tie rule → C5. The Floor/list/menu-bar origin composition and the decision sprite: parked | C5's fences |
| 04 destinations on the Floor and the drop | parked — folded into PHILO-13 C5 | only destination identity and active/parked semantics, for the window picker → C5. Floor icons, drag, drop tags, icon positions: parked | none (no Floor proof substitutes for the window click) |
| 05 the atlas cases | parked — folded into PHILO-13 C5 | per-document face cases for the five kinds, transitions, artifact picked/PREPARED/SENT, `.op` siblings → C5. Floor drop/tag cases: parked, visible | C5's atlas cases |
| 06 the closing use | parked — folded into PHILO-13 C5 | real sends by `Send to ▸` with far-side readback or a named limit; the cold-agent artifact prepare → C5. The drag leg: parked | C5's closing leg |

## Exit criteria (evidence required)

The proof is new capability through the real hub on an isolated HOME, minted through real producers, never a test double that lies about the field a check reads. "At both widths" means 1440x900 (mouse) and 393x852 (touch: `has_touch`, every press a tap). "Red on main" applies where a defect exists.

- [ ] 1. **The unwalked paths are walked (B0).** One atlas case per unwalked path at both widths, passing on main before B2 merges; red-before-green where it finds a defect.
- [ ] 2. **Nothing is destroyed (A1).** Delete on a meeting and on a Workbench item parks it; Restore from the same face brings it back with its segments, summary, artifacts and run links; no SQL DELETE on the normal path; single and bulk; after reload.
- [ ] 3. **One truth (A2, A3).** Every "needs you" on a shot is one number from one projection; a narrower count names what it counts. Record shows "Not recording" + the reason on a refused start. No face shows "ON" for a fact that is "OFF" elsewhere unless the two name different facts.
- [ ] 4. **Close means gone (A4).** After Close, `elementFromPoint` at the old centre hits the Desk at both widths, for every opener that passes a qualified id.
- [ ] 5. **Everything opens (B1, B3, B4).** J1 dead taps 5 → 0; J1 path 7 → 3 gestures; J3 prep 5 → 1; decision 5 → 2 gestures with its meeting and project; no false "No 1:1 planned".
- [ ] 6. **The Desk remembers (B2).** Reload or close mid-job: 0 re-navigation, 0 lost drafts, at both widths.
- [ ] 7. **The update writes the week (B5).** The deterministic draft lists the linked meetings' summaries, decisions and owned actions; 111 typed characters → 0.
- [ ] 8. **The look, as ratified (C1).** The C1 canvas ratified by the owner (his word recorded) before the first C1 face commit; the seven canvas criteria hold on the built shots at both widths.
- [ ] 9. **Workbench behaviour (C2, C3, C4, C6).** Depth, zoom, right-button menu and Amiga-key shortcuts by mouse, key and touch; a live Dock within ~1 s with every window closed; the palette finds people and thought text and runs verbs; a thought in 1 key press, titled from its first words.
- [ ] 10. **Send from the window (C5).** Send from an open meeting in 3 gestures at both widths; Phase 12's fences carried (story 15).
- [ ] 11. **The phone and the floor (C7, C8).** At 393, window content ≥ 700 of 852 px; zero readable text under 12 px on a full-surface scan at both widths.
- [ ] 12. **The atlas** has every new case, run one case per `scripts/graph_walk.py` invocation; the Phase 7–12 atlas cases still pass. The web baseline has zero branch-new failures.

## Story status

| ID | Proposal | Story | Status | Story file | Evidence |
|---|---|---|---|---|---|
| PHILO-13-01 | B0 | Walk what was not walked | backlog | [story-01-b0-walk-what-was-not-walked](./story-01-b0-walk-what-was-not-walked.md) | — |
| PHILO-13-02 | A1 | Park, never delete | backlog | [story-02-a1-park-never-delete](./story-02-a1-park-never-delete.md) | — |
| PHILO-13-03 | A2 | One meaning of "needs you" | backlog | [story-03-a2-one-meaning-of-needs-you](./story-03-a2-one-meaning-of-needs-you.md) | — |
| PHILO-13-04 | A3 | Faces that do not lie | backlog | [story-04-a3-faces-that-do-not-lie](./story-04-a3-faces-that-do-not-lie.md) | — |
| PHILO-13-05 | A4 | Close means gone | backlog | [story-05-a4-close-means-gone](./story-05-a4-close-means-gone.md) | — |
| PHILO-13-06 | B1 | One open grammar | backlog | [story-06-b1-one-open-grammar](./story-06-b1-one-open-grammar.md) | — |
| PHILO-13-07 | B2 | The Desk remembers | backlog | [story-07-b2-the-desk-remembers](./story-07-b2-the-desk-remembers.md) | — |
| PHILO-13-08 | B3 | Decide where the meeting is | backlog | [story-08-b3-decide-where-the-meeting-is](./story-08-b3-decide-where-the-meeting-is.md) | — |
| PHILO-13-09 | B4 | The 1:1 finds its person | backlog | [story-09-b4-the-one-on-one-finds-its-person](./story-09-b4-the-one-on-one-finds-its-person.md) | — |
| PHILO-13-10 | B5 | The update writes the week | backlog | [story-10-b5-the-update-writes-the-week](./story-10-b5-the-update-writes-the-week.md) | — |
| PHILO-13-11 | C1 | The Workbench look (the canvases; the face gate) | backlog | [story-11-c1-the-workbench-look](./story-11-c1-the-workbench-look.md) | — |
| PHILO-13-12 | C2 | The gadgets that are missing | backlog | [story-12-c2-the-gadgets-that-are-missing](./story-12-c2-the-gadgets-that-are-missing.md) | — |
| PHILO-13-13 | C3 | A live Dock (AppIcons) | backlog | [story-13-c3-a-live-dock](./story-13-c3-a-live-dock.md) | — |
| PHILO-13-14 | C4 | A palette that knows his week and does verbs | backlog | [story-14-c4-a-palette-that-knows-his-week](./story-14-c4-a-palette-that-knows-his-week.md) | — |
| PHILO-13-15 | C5 | Send to from any document window (the Phase 12 fold) | backlog | [story-15-c5-send-to-from-any-document-window](./story-15-c5-send-to-from-any-document-window.md) | — |
| PHILO-13-16 | C6 | Capture from anywhere | backlog | [story-16-c6-capture-from-anywhere](./story-16-c6-capture-from-anywhere.md) | — |
| PHILO-13-17 | C7 | The phone desk | backlog | [story-17-c7-the-phone-desk](./story-17-c7-the-phone-desk.md) | — |
| PHILO-13-18 | C8 | The 12 px floor | backlog | [story-18-c8-the-12-px-floor](./story-18-c8-the-12-px-floor.md) | — |

Numbers follow the build order the brief set (B0 first: it gates B2). The Proposal column carries PROPOSAL r2's IDs; story titles carry them too.

## Lanes

Per TWO-BRAINS §4 (`docs/internal/TWO-BRAINS.md:104-128`): one owner brain per story, disjoint files (PROPOSAL §4).

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| Data + truth | 01 B0, 02 A1, 03 A2, 09 B4, 10 B5, 13 C3 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-13-astra | feat/philo-13-astra |
| Faces + frame | 04 A3, 05 A4, 06 B1, 07 B2, 08 B3, 11 C1, 12 C2, 14 C4, 15 C5, 16 C6, 17 C7, 18 C8 | Muad'Dib (Fedaykin, Opus 5.5) | Astra | ../wt-philo-13-muaddib | feat/philo-13-muaddib |

- **Why this split** (TWO-BRAINS §4): Astra takes the backend, the projections, the live layer and the verification harness (B0's atlas); Muad'Dib takes the faces, the frame, the canvases and the owner-facing close. D1 would have been the faces lane's; it is out (fork 4).
- A lane runs its scoped fences and rig cases only. The orchestrator runs the full suite before the done call. CI does not gate a merge (the owner, 2026-09-28).

### File ownership (the collision map, PROPOSAL §4)

- **Astra owns:** `holdspeak/db/**`, `holdspeak/services/**`, `holdspeak/web/routes/**` for its stories; `web/src/desk/projections.ts`, `web/src/desk/components/window/Dock.tsx` (logic), `web/src/runtime/**`, `web/src/desk/useDeskChangedRefresh.ts`, `web/src/pages/cores/PeopleCore.tsx` (B4), the meeting/Workbench delete/park call sites (`HistoryCore.tsx` delete path, `WorkbenchWindow.tsx` removal path, A1), and the atlas cases of B0.
- **Muad'Dib owns:** `web/src/desk/chair/**`, `web/src/desk/components/DeskWindow.tsx` and `window/*` except `Dock.tsx` logic, all CSS including `dock.css`, `web/src/desk/store/**` (B2, A4), `recordingSlice.ts` (A3), pullouts, `verbRegistry.ts`, `DeskToolShelf.tsx`, `windowMenuAdapter.tsx`, `send/**`.
- **Seams:** A2 delivers the one needs-you projection + hook; Muad'Dib wires the Chair in B1. A1's park/restore verbs on faces Muad'Dib owns land through a brief exchange, one lane at a time on the file. Any file touched by both lanes is merged serially: the first lane's PR merges, the second rebases.

**Files the stories need that the map does not name** (for Astra's check; each is assigned to the story's lane, and the serial-merge seam applies where both lanes touch it):

| File | Needed by | Lane |
|---|---|---|
| `docs/internal/philo/graph/atlas.json` | B0 and every story's atlas cases | both — serial merge; B0 first |
| `web/src/pages/cores/history/helpers.ts` (the Meetings headline, `:216-233`) | A2 (the narrower count) | Data + truth |
| the Room headline (`web/src/features/project-room/**`) | A2 (narrower count), A3 (raw publish failure), B2 (the update draft) | both — serial merge |
| `web/src/pages/cores/PeopleCore.tsx` | B4 (owner), A3 (the 503 face), B2 (the 1:1 note draft) | Data + truth owns; A3 and B2 land through a brief exchange |
| `web/src/pages/cores/settingsPrefs.tsx`, `web/src/desk/components/TrustWindow.tsx` | A3 | Faces + frame |
| `web/src/desk/components/Pullout.tsx`, `web/src/desk/components/DeskMenuBar.tsx` | A4, C2, C5 | Faces + frame |
| `web/src/meetings/MeetingSendWell.tsx` | C5 | Faces + frame |
| `web/src/desk/newThought.ts` | C6 | Faces + frame |
| `holdspeak/services/project_update_service.py` | B5 | Data + truth (under `holdspeak/services/**`) |

### The canvas gate (inside the faces lane)

C1's canvas comes first: it sets the material every later face obeys. Then the B1, B3, C5 and C7 canvases, drawn on C1's material. Astra checks each; **the owner ratifies**; his word is recorded verbatim. No C-story face is built before its canvas is ratified (UX-CANON A.2). Wave A and B0 build while the C1 canvas is on the table.

## Order / waves

| Step | Data + truth (Astra) | Faces + frame (Muad'Dib) |
|---|---|---|
| 1 | 01 B0, 02 A1, 03 A2 | 04 A3, 05 A4, 11 C1 canvas |
| 2 | 09 B4, 10 B5 | 06 B1 and 08 B3 (after their canvases are ratified); 07 B2 **after 01 B0's cases exist and pass on main** |
| 3 | 13 C3 (after 03 A2 and 04 A3) | after C1's ratification: 11 C1 build, 12 C2, 14 C4, 15 C5, 16 C6, 17 C7, 18 C8 |

D1 runs only on a later word from the owner (fork 4: "Later").

## Where we are

2026-10-01: DRAFTED (branch `docs/philo-13-charter`) from PROPOSAL r2 and the five forks he ruled. Eighteen stories, all `backlog`. Phase 12 folded (stories 02–06 `blocked`, parked — folded into PHILO-13 C5). D1 parked in BACKLOG. Next: Astra's check of this charter; then the owner's ratification. On ratification, 01 (B0) and 11 (C1, its canvas) flip to `ready`: each lane's long pole.

## Open dissents

None.

## Forecast

**Elapsed: 3–4 weeks** (PROPOSAL §4), two lanes in parallel. The gates are the C1 canvas ratification (Wave C waits on it), B0 on main before B2, the per-face canvas rounds (B1, B3, C5, C7), Astra's built checks, and C5's real-send legs. The grounding sizes each move S/M/L (`grounding/faces-jobs.md:152-161`; `grounding/structure.md:298-306`); each story carries its size. No day count per story is claimed.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| B2's shared lifecycle breaks an unwalked window | medium | B0 gates B2 | B2 merges before B0's cases pass on main |
| C1 grows into a redesign of every body | medium | bodies inherit the material through `DeskWindowFrame`; C1 does not redesign every body (PROPOSAL C1) | a C1 commit that rewrites a body's content |
| Two lanes in one file | medium | the file map; serial merge | a PR that touches a file the other lane holds open |
| Palette or menu sends without his press | low | C4/C5 open the preview only | a `channel_sends` row or a kernel operation before Send |
| A fence passes on a double that lies | medium | mint through real producers; mutate the producer field to show the fence rejects it | a park, needs-you or recording fence that reads a field the real producer does not write |
| A face word changes and its fence is rewritten to pass | medium | rehome the guard onto live behaviour in the same commit | a guard edited only to match a removal |

## Decisions made (this phase)

- 2026-10-01 — the owner named the scope ("Both, the whole thing"), folded Phase 12 ("Fold it into the Desk work") and set the method ("Audit, then propose").
- 2026-10-01 — the owner ruled the five forks: "All the way"; "Opens its own window"; "Everything"; "Later"; the Send placement default stands.
- 2026-10-01 — Muad'Dib ruled B5 (the update draft reads the week without the engine).
- 2026-10-01 — DRAFTED: 18 stories in build order; two lanes; the file map; the canvas gate; Phase 12 02–06 `blocked` (parked — folded into C5), since `parked` is not a status the gate accepts (`.githooks/dw_pmo/model.py:18`) — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- The look itself (material, gadget art, the screen title bar, the Chair as windows): the C1 canvas, ratified by the owner.
- The B1, B3, C5 and C7 faces: their canvases, ratified by the owner.
- Each consolidation move: the story whose face receives it, after B0 walks the path.
