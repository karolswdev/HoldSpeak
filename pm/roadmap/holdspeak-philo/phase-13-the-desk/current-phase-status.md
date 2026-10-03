# Phase 13 - The Desk

**Last updated:** 2026-10-03 (RATIFIED by the owner, "Ratify, build it". #726 merged as 44ec934a. #727 r4 merged at `03c220e8` after the duplicate B0 commits dropped, both `has_summary` and `parked` preserved, and the marker-bearing history repaired; 42 source references are re-anchored, generated outputs refreshed, and the 377-test scoped A1/shared selection plus all 12 Documentation Navigation commands and generated-reference checks pass. Stories 01–03 remain in-progress for their named gates. Earlier: r3: Astra r2 paid (close→reopen place, Trust returns, H-B0b contract); Astra r3 RATIFY-WITH-CONDITIONS paid (anchor `:492`, this status). Earlier r2: Astra's check r1 DO-NOT-RATIFY paid — disjoint files with named handoffs, B2 covers every window family and named draft, A2's membership oracle, the Parked artboard, the gates as merge-record evidence, C4's query collision; unchecked r2.) Earlier: 2026-10-01 (DRAFTED by the Fedaykin docs lane for Muad'Dib from PROPOSAL r2 and the five forks the owner ruled; unchecked.) #728 r4 is rebased onto current `main` at #731 (`8485874f6`), tested A2 source revision `0f32ddb87613638725ec80c471a6ced7b0b3e070`. The `dedupAttention` skip mutant is rejected by the real-producer duplicate, returning 7 instead of the required 6. On the rebased head, the 132-test shared/A2 Python selection, 63-test seven-file serial web selection, typecheck, ten documentation generators, all 12 Documentation Navigation commands and generated-reference checks pass. The actual Dock case reads 6→5 at 1440 and 393 native touch on this source revision. PHILO-13-03 remains in-progress for A2-W; the r3 product conditions and r4 integration gates are paid, and the merge record will be posted on #728.

**Status:** RATIFIED by the owner 2026-10-01 ("Ratify, build it") after Astra's checks r1–r3 (all paid, `checks/`).

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

**r2, 2026-10-01:** Astra's check r1 was DO-NOT-RATIFY; its conditions are paid ("Round two" below). r2 is unchecked: awaiting Astra's check of r2; then the owner's ratification.

Source: `docs/internal/philo/phase-13/PROPOSAL.md` (r2; Astra check r1 RATIFY-WITH-CONDITIONS, paid, `docs/internal/philo/phase-13/grounding/checks/proposal-astra.md`). This charter turns it into roadmap form. It does not redesign it. The five forks are ruled (Authority).

## Round two — Astra check r1 (DO-NOT-RATIFY) paid

Astra's check r1 of this charter (Codex `gpt-6-astra`; run `.tmp/two-brains/20261001-165543-check-p13-charter/last.md`; Muad'Dib records it in `checks/`) was **DO-NOT-RATIFY**. Its conditions are paid in r2 on Muad'Dib's rulings:

| Astra r1 | Paid by |
|---|---|
| 1 the lane map shares `atlas.json`, the Room headline and `PeopleCore.tsx`; serial merges do not make files disjoint | "File ownership": one owner per path. Two atlas files, `atlas-phase13-astra.json` and `atlas-phase13-muaddib.json` (`scripts/graph_walk.py:6507` takes `--atlas` per run; `run_case(atlas_path, …)` `:6314`; `tests/unit/test_philo_graph_atlas.py:27` globs `atlas*.json`). The Room and `PeopleCore.tsx` are Muad'Dib's; A2 and B4 deliver pure modules (`needsYou.ts`, `people/prepData.ts`) and the faces lane wires them. "Merged serially" is removed; every crossing is a named handoff ("Named handoffs"). The shared `.op` count at `test_philo_graph_atlas.py:492` has one owner (H-B0b). |
| 2 B2's "Everything" leaves out Delivery Dossier and Terminal and the meeting form draft | story 07: every mounted window family listed with its disposition (returns, or exempt with a reason from the source), Dossier (`web/src/desk/DeskApp.tsx:267`; `web/src/desk/deliveryDossier.ts:182`) and Terminal (`DeskApp.tsx:268`; `web/src/desk/deliveryTerminal.ts:221`) return; every named draft field listed in the acceptance, the meeting SEND well's form and pick included. |
| 3 A2 has no membership rule or expected result | story 03: "needs you" = the Chair's existing membership (`web/src/desk/chair/ChairHome.tsx:795-812`, `:825-840`) stated as a rule; a real-producer week with expected row ids and count, one mutation with its expected change; a wrong projection fails. |
| 4 the gates are reviewer holds; A1's Parked face has no canvas | "The gates": each gate is a line the merge record must cite (B0's commit and evidence path for B2; the owner's ratification path + quote for every C face, B1, B3 and A1-F). A1's Parked and Restore face is a named artboard in C1's canvas set (story 11); A1's backend may merge first. |
| 5 C4's "same name" wording | story 14: the query `People` returns the `People & vocabulary` note above the People app (`grounding/shots/surfaces/110-palette-people-pop-393.png`). C4 app-first + one Escape and C7's Desk/Object/Window at 393 kept, both grounded. |

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
- [ ] 2. **Nothing is destroyed (A1).** (Its face, A1-F, merges only on the owner's ratified "Parked and Restore" artboard.) Delete on a meeting and on a Workbench item parks it; Restore from the same face brings it back with its segments, summary, artifacts and run links; no SQL DELETE on the normal path; single and bulk; after reload.
- [ ] 3. **One truth (A2, A3).** "Needs you" is the membership rule of story 03; the seeded week returns its expected row ids and count, and a mutation changes it as expected; every "needs you" on a shot reads it; a narrower count names what it counts. Record shows "Not recording" + the reason on a refused start. No face shows "ON" for a fact that is "OFF" elsewhere unless the two name different facts.
- [ ] 4. **Close means gone (A4).** After Close, `elementFromPoint` at the old centre hits the Desk at both widths, for every opener that passes a qualified id.
- [ ] 5. **Everything opens (B1, B3, B4).** J1 dead taps 5 → 0; J1 path 7 → 3 gestures; J3 prep 5 → 1; decision 5 → 2 gestures with its meeting and project; no false "No 1:1 planned".
- [ ] 6. **The Desk remembers (B2).** Every mounted window family returns or is exempt with a source reason; every named draft field survives; reload or close mid-job: 0 re-navigation, 0 lost drafts, at both widths. B2's merge record cites B0's merged commit and evidence path.
- [ ] 7. **The update writes the week (B5).** The deterministic draft lists the linked meetings' summaries, decisions and owned actions; 111 typed characters → 0.
- [ ] 8. **The look, as ratified (C1).** The C1 canvas ratified by the owner (his word recorded) before the first C1 face commit; the seven canvas criteria hold on the built shots at both widths.
- [ ] 9. **Workbench behaviour (C2, C3, C4, C6).** Depth, zoom, right-button menu and Amiga-key shortcuts by mouse, key and touch; a live Dock within ~1 s with every window closed; the palette finds people and thought text and runs verbs; a thought in 1 key press, titled from its first words.
- [ ] 10. **Send from the window (C5).** Send from an open meeting in 3 gestures at both widths; Phase 12's fences carried (story 15).
- [ ] 11. **The phone and the floor (C7, C8).** At 393, window content ≥ 700 of 852 px; zero readable text under 12 px on a full-surface scan at both widths.
- [ ] 12. **The atlas** has every new case, run one case per `scripts/graph_walk.py` invocation; the Phase 7–12 atlas cases still pass. The web baseline has zero branch-new failures.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| PHILO-13-01 | B0 — Walk what was not walked | in-progress | [story-01-b0-walk-what-was-not-walked](./story-01-b0-walk-what-was-not-walked.md) | — |
| PHILO-13-02 | A1 — Park, never delete | done | [story-02-a1-park-never-delete](./story-02-a1-park-never-delete.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-13-03 | A2 — One meaning of "needs you" | done | [story-03-a2-one-meaning-of-needs-you](./story-03-a2-one-meaning-of-needs-you.md) | [evidence-story-03](./evidence-story-03.md) |
| PHILO-13-04 | A3 — Faces that do not lie | done | [story-04-a3-faces-that-do-not-lie](./story-04-a3-faces-that-do-not-lie.md) | [evidence-story-04](./evidence-story-04.md) |
| PHILO-13-05 | A4 — Close means gone | done | [story-05-a4-close-means-gone](./story-05-a4-close-means-gone.md) | [evidence-story-05](./evidence-story-05.md) |
| PHILO-13-06 | B1 — One open grammar | done | [story-06-b1-one-open-grammar](./story-06-b1-one-open-grammar.md) | [evidence-story-06](./evidence-story-06.md) |
| PHILO-13-07 | B2 — The Desk remembers | backlog | [story-07-b2-the-desk-remembers](./story-07-b2-the-desk-remembers.md) | — |
| PHILO-13-08 | B3 — Decide where the meeting is | done | [story-08-b3-decide-where-the-meeting-is](./story-08-b3-decide-where-the-meeting-is.md) | [evidence-story-08](./evidence-story-08.md) |
| PHILO-13-09 | B4 — The 1:1 finds its person | backlog | [story-09-b4-the-one-on-one-finds-its-person](./story-09-b4-the-one-on-one-finds-its-person.md) | — |
| PHILO-13-10 | B5 — The update writes the week | in-progress | [story-10-b5-the-update-writes-the-week](./story-10-b5-the-update-writes-the-week.md) | — |
| PHILO-13-11 | C1 — The Workbench look (the canvases; the face gate) | in-progress | [story-11-c1-the-workbench-look](./story-11-c1-the-workbench-look.md) | — |
| PHILO-13-12 | C2 — The gadgets that are missing | done | [story-12-c2-the-gadgets-that-are-missing](./story-12-c2-the-gadgets-that-are-missing.md) | [evidence-story-12](./evidence-story-12.md) |
| PHILO-13-13 | C3 — A live Dock (AppIcons) | backlog | [story-13-c3-a-live-dock](./story-13-c3-a-live-dock.md) | — |
| PHILO-13-14 | C4 — A palette that knows his week and does verbs | backlog | [story-14-c4-a-palette-that-knows-his-week](./story-14-c4-a-palette-that-knows-his-week.md) | — |
| PHILO-13-15 | C5 — Send to from any document window (the Phase 12 fold) | backlog | [story-15-c5-send-to-from-any-document-window](./story-15-c5-send-to-from-any-document-window.md) | — |
| PHILO-13-16 | C6 — Capture from anywhere | backlog | [story-16-c6-capture-from-anywhere](./story-16-c6-capture-from-anywhere.md) | — |
| PHILO-13-17 | C7 — The phone desk | backlog | [story-17-c7-the-phone-desk](./story-17-c7-the-phone-desk.md) | — |
| PHILO-13-18 | C8 — The 12 px floor | backlog | [story-18-c8-the-12-px-floor](./story-18-c8-the-12-px-floor.md) | — |
Numbers follow the build order in PROPOSAL r2 (B0 first: it gates B2); the five-column story index follows Delivery Workbench.
## Lanes

Per TWO-BRAINS §4 (`docs/internal/TWO-BRAINS.md:104-128`): a lane is a set of stories with **disjoint files** and one owner brain. Every path below has exactly one owner. Where a story needs a file the other lane owns, the owner of the file does that change as a **named handoff** (what is delivered, by which story, consumed by which story). This is the Phase 12 pattern: a pure module in one lane, the wiring in the other (`../phase-12-send-from-the-floor/current-phase-status.md:105`).

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| Data + truth | 01 B0, 02 A1, 03 A2, 04 A3 (H-A3 only), 09 B4, 10 B5, 13 C3 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-13-astra | feat/philo-13-astra |
| Faces + frame | 04 A3, 05 A4, 06 B1, 07 B2, 08 B3, 11 C1, 12 C2, 14 C4, 15 C5, 16 C6, 17 C7, 18 C8; and the named wiring steps A1-F, A2-W, B4-W, C3-W | Muad'Dib (Fedaykin, Opus 5.5) | Astra | ../wt-philo-13-muaddib | feat/philo-13-muaddib |

- **Why this split** (TWO-BRAINS §4): Astra takes the backend, the projections, pure data modules, the live layer and the verification harness (B0's atlas); Muad'Dib takes every face, the frame, the canvases, the store and the owner-facing close. D1 would have been the faces lane's; it is out (fork 4).
- **The principle for any path not listed:** faces, CSS, store, chair, window, menu, send and pullout files → Muad'Dib; db, services, routes, projections, runtime and pure data modules → Astra.
- A lane runs its scoped fences and rig cases only. The orchestrator runs the full suite before the done call. CI does not gate a merge (the owner, 2026-09-28).

### File ownership (one owner per path)

PROPOSAL §4's map, made disjoint by Astra's check r1 and Muad'Dib's rulings (r2):

| Path | Owner | Stories that change it |
|---|---|---|
| `holdspeak/db/**`, `holdspeak/services/**`, `holdspeak/web/routes/**` | Astra | A1, A2, A3 (H-A3 only), B4, B5, C3; any backend handoff (H-B3, H-C5) |
| `web/src/desk/projections.ts`, `web/src/desk/attention.ts` (dedup and rank, pure); **new** `web/src/desk/needsYou.ts` (the pure needs-you module and its hook; it imports `web/src/desk/chair/meetingPathBlocker.ts` read-only) | Astra | A2 |
| **new** `web/src/desk/people/prepData.ts` (the pure Prep client module) | Astra | B4 |
| `web/src/desk/api.ts` (the park and restore client functions only) | Astra | A1 |
| `web/src/desk/components/window/Dock.tsx` (badge logic) | Astra | A2 (the badge reads `needsYou.ts`), C3 |
| `web/src/runtime/**`, `web/src/desk/useDeskChangedRefresh.ts` | Astra | C3 |
| `docs/internal/philo/graph/atlas-phase13-astra.json` (**new**) | Astra | B0, A1, A2, B4, B5, C3 |
| `docs/internal/philo/graph/atlas.schema.json` (shared atlas contract) | Astra; faces-lane additions by named handoff | B0 and every atlas change |
| `scripts/graph_walk.py` (shared graph rig) | Astra; faces-lane additions by named handoff | B0 and every graph-rig change |
| `tests/unit/test_philo_graph_atlas.py` (the shared `.op` sibling count, `:492`) | Astra | B0 (handoff H-B0b) |
| `tests/unit/test_philo13_astra_atlas.py` (**new**) | Astra | B0 and every Astra story's cases |
| `tests/unit/test_philo13_a3h_meeting_summary.py` and `tests/fixtures/philo3_summary_wire.json` | Astra | A3 (H-A3 data handoff) |
| `docs/internal/philo/graph/atlas-phase13-muaddib.json` (**new**) | Muad'Dib | every faces-lane story and wiring step |
| `tests/unit/test_philo13_muaddib_atlas.py` (**new**) | Muad'Dib | every faces-lane story's cases |
| `web/src/desk/chair/**` | Muad'Dib | A2-W, B1, C1, C7 |
| `web/src/desk/components/DeskWindow.tsx`, `window/*` except `Dock.tsx` logic | Muad'Dib | C1, C2, C7 |
| all CSS, including `dock.css` and `web/src/desk/surface/surface.css` | Muad'Dib | C1, C3-W, C7, C8 |
| `web/src/desk/store/**` (incl. `recordingSlice.ts`, `compositorSlice.ts`, `workspaceStorage.ts`, `windowFactory.ts`) | Muad'Dib | A3, A4, B2, C2 |
| `web/src/desk/deliveryDossier.ts`, `web/src/desk/deliveryTerminal.ts` (window open state) | Muad'Dib | B2 |
| pullouts (`web/src/desk/pullouts/**`), `web/src/desk/components/Pullout.tsx` | Muad'Dib | A3, A4, B1, B3, C5 |
| `web/src/desk/verbRegistry.ts`, `web/src/desk/components/DeskToolShelf.tsx`, `web/src/desk/components/window/windowMenuAdapter.tsx`, `web/src/desk/components/DeskMenuBar.tsx` | Muad'Dib | C2, C4, C5, C6 |
| `send/**` (`web/src/desk/surface/send/**`), `web/src/meetings/MeetingSendWell.tsx`, `web/src/desk/documentSends.tsx` | Muad'Dib | C5 |
| `web/src/pages/cores/HistoryCore.tsx`, `web/src/pages/cores/history/helpers.ts` | Muad'Dib | A1-F, A2-W |
| `web/src/desk/components/WorkbenchWindow.tsx` | Muad'Dib | A1-F |
| `web/src/pages/cores/PeopleCore.tsx` | Muad'Dib | A3, B2, B4-W |
| the Room face (`web/src/features/project-room/ProjectRoomCore.tsx` and its headline) | Muad'Dib | A2-W, A3, B2 |
| `web/src/desk/components/SystemShade.tsx`, `web/src/desk/components/AttentionDrawer.tsx` (the bell) | Muad'Dib | A2-W |
| `web/src/pages/cores/settingsPrefs.tsx`, `web/src/desk/components/TrustWindow.tsx` | Muad'Dib | A3 |
| `web/src/desk/newThought.ts` | Muad'Dib | C6 |
| `web/src/desk/components/AskPanel.tsx` (the Ask face) | Muad'Dib | A3, B2 |

### Named handoffs (no shared file; one owner does each change)

| ID | Delivered by (owner, story) | What | Consumed by |
|---|---|---|---|
| H-B0a | Astra, B0 (01) | `atlas-phase13-astra.json` created and validated against Astra-owned shared `atlas.schema.json`; `scripts/graph_walk.py` is the Astra-owned shared rig. The faces lane creates its own `atlas-phase13-muaddib.json` and requests schema/rig additions by named handoff; `test_philo_graph_atlas.py:27` globs `atlas*.json`, so neither needs registering | every Phase 13 atlas case |
| H-B0b | Astra, B0 (01) | `tests/unit/test_philo_graph_atlas.py:492` counts `.op` siblings outside the `atlas-phase13-*` files only; each lane's own test file asserts its own count; **the shared semantic checks (`:469`, `:551`, via the `:27` glob) still cover both Phase 13 files** | every story that adds an `.op` sibling |
| H-A1 | Astra, A1 (02) | park, Parked read and restore routes + `web/src/desk/api.ts`; r2 also hides a whole parked Meeting and its linked action items from owner reads (Brief/calendar, Recall, projections, proposals, intel claims, global/Project/People action lists, speaker reads); r3 fences both bound intel-claim stages, FollowThrough action and decision-cadence paths, Project stats, Meeting Watch, intel job list, collector, Room People commitments and Recall source-derived commitments while preserving promoted decision records; tombstones park | A1-F |
| A1-F | Muad'Dib, a named wiring step in A1's acceptance, on `feat/philo-13-muaddib` | the Parked filter, Restore and the `PARKED` receipt on Meetings (`HistoryCore.tsx`) and the Workbench window (`WorkbenchWindow.tsx`), built to the C1 artboard "Parked and Restore" | A1's done call |
| H-A2 | Astra, A2 (03) | `web/src/desk/needsYou.ts`: R1–R3 membership, bounded server read for all FAILED/RETRYING meetings, cached Room poll and explicit `fresh=1`; successful meeting action status writes invalidate that cache; planned milestones project and affect Room health from their own status and due date, never from a meeting-action title match; pure function + hook; Dock badge reads it. The five R1 source anchors and generated reference outputs are current | A2-W, C3 |
| H-A3 | Astra, A3 (04) | stored-summary boolean on `/api/meetings` list and search rows, derived from the same persisted summary as detail; independent of configuration and run status; fenced through real producers and list-route reads | A3-W |
| A2-W | Muad'Dib, a named wiring step in A2's acceptance, on `feat/philo-13-muaddib` | the Chair (its local `doorCardsToItems`/`hasMeetingAttention` membership code, `ChairHome.tsx:278`, `:309`, `:795-840`, replaced by `needsYou.ts`), the bell/shade and the Room headline read `needsYou.ts`; Meetings and the Room relabel narrower counts | A2's done call |
| H-B4 | Astra, B4 (09) | the calendar link suggestion and the Prep data in the People service/routes + `web/src/desk/people/prepData.ts` | B4-W |
| B4-W | Muad'Dib, a named wiring step in B4's acceptance, on `feat/philo-13-muaddib` | `PeopleCore.tsx` shows `NEXT 1:1` and Prep from `prepData.ts` | B4's done call |
| H-C3 | Astra, C3 (13) | the Dock state (badge logic, frames, invalidation) | C3-W |
| C3-W | Muad'Dib, a named wiring step in C3's acceptance | the AppIcon states drawn in `dock.css` to the C1 canvas | C3's done call |
| H-B3 | Astra, on request, only if B3 finds the decision has no meeting/project reference | the reference in the decision route/service | B3 (08) |
| H-C5 | Astra, on request, only if the latest-update read does not apply the tie rule | the tie rule in the read | C5 (15) |

A story with a wiring step flips `done` only when both halves are merged; the merge record names both commits.

### The gates (explicit review evidence; CI does not gate)

CI does not gate a merge (the owner, 2026-09-28). So each gate is a **line the merge record must carry**; a merge record without it is not a merge on verification, and the checker refuses it.

| Gate | What the merge record must cite |
|---|---|
| **B0 → B2** | B2's PR merge record cites B0's merged commit on main and atlas evidence (`evidence-story-01.md` and its run directories), plus the B0 rerun on B2's head; outside-home reds may remain with their home cited, but B0-F2 must pass in B2. Re-walk B0-F1 after #725 merges. |
| **Canvas → every C face** (C1, C2, C3-W, C4, C5, C6, C7, C8) and B1, B3 | the PR merge record cites the owner's ratification record of that face's canvas: its path and his quote. |
| **A1's face (A1-F)** | the merge record cites the owner's ratification record of C1's artboard "Parked and Restore" (path + quote). A1's backend half (H-A1) may merge before it. |

The canvas set, in order: C1's canvas first (the frame, the chrome, the Chair, the material, and the named artboard **"Parked and Restore"** for A1-F); then B1, B3, C5 and C7, drawn on C1's material. Astra checks each; **the owner ratifies**; his word is recorded verbatim. No face is built before its canvas is ratified (UX-CANON A.2). Wave A's backend, A3, A4 and B0 build while the C1 canvas is on the table.

## Order / waves

| Step | Data + truth (Astra) | Faces + frame (Muad'Dib) |
|---|---|---|
| 1 | 01 B0 (first: H-B0a, H-B0b), 02 A1 backend (H-A1), 03 A2 (H-A2) | 04 A3, 05 A4, 11 C1 canvas (with the "Parked and Restore" artboard); A2-W |
| 2 | 09 B4 (H-B4), 10 B5 | A1-F (after the artboard is ratified); B4-W; 06 B1 and 08 B3 (after their canvases are ratified); 07 B2 **after 01 B0 is merged and its cases pass on main** |
| 3 | 13 C3 (H-C3; after 03 A2 and 04 A3) | after C1's ratification: 11 C1 build, C3-W, 12 C2, 14 C4, 15 C5, 16 C6, 17 C7, 18 C8 |

D1 runs only on a later word from the owner (fork 4: "Later").

## Where we are

2026-10-03: **B5 candidate — UNCHECKED, awaiting Muad'Dib.** Deterministic linked-week data and real-producer fences implemented in `feat/philo-13-10-astra`. Both widths and the operation sibling ran; phone editor line clipping remains a named face-lane limitation. [Lane report](lane-10-astra.md). Story 10 remains in-progress.

2026-10-03: **PHILO-13-12 (C2) done** — To back (every window, menu, ⌃B, tap at 393), Intuition zoom (two remembered rects, persisted), the window's menu bar on the right button / long press with live key caps (Iconify ⌘M, Zoom ⌃M, To back ⌃B, Close ⌘W). Ledger: off-Mac Ctrl+M binds Zoom (⌃ chords first); `static-muaddib.json` still names Minimize/Maximize.

2026-10-02: **PHILO-13-11 slice two, atlas round** (Astra counsel r3 on #730): 76 atlas cases in 7 files open the right Chair window through the real doors at 393 (Go ▸ Chair ▸ window; the Dock's Speak for Capture); 34 first-value preconditions read `[data-testid=chair-desk]`; walked one case per run at both widths: 59 pass, 14 blocked outside the Chair, 3 fail at 393 only. **Muad'Dib's rulings:** Capture grows to 300 px while an aftercare card stands (accepted product fix); `case.p11.meeting_summary.chair.picked` keeps a 1440 zoom step, and 'scroll Send into view on pick' goes to C5's ledger; **homed reds** — `case.closure.chain.s3_same_summary_after_restart` (+`.replayed`) at 393 → B2 (story 07 remembers the open Chair window), and `case.philo603.toast.arrival` at 393 → new handoff **H-rig-clearof** (Astra: per-width `clear_of` in graph_walk.py + atlas.schema.json). The React architecture guard: `library-css-outside: chair.css` red → green.

2026-10-02: **PHILO-13-11 build, slice two — the Chair as windows** (Fedaykin; Muad'Dib verified): `chair:needs|brief|week|capture` as DeskWindowFrame hosts (full gadget set, depth withheld; Close closes; Window ▸ Chair with checks; a reopen Button in place); work first; Capture a fourth window on desktop and on demand from the Dock's Speak at 393 (Go ▸ Speak and ⌘1 keep the Speak window); the screen title names the front Chair window (reads every open window); the Chair's summary verb follows `has_summary`. Fences red on bbf7e9a4, green after; 29 old Chair/window glass files rehomed (none loosened). **Handoff H-C3-origin (to Astra, C3):** the Dock passes its launch origin explicitly so the Chair's 1.5 s Dock-press window can be removed.

2026-10-02: **PHILO-13-04 done** (A3-W merged with H-A3). **PHILO-13-11 build, slice one — the frame** (Fedaykin; Muad'Dib verified): Steel tokens, the gadget layout (depth withheld until C2), one blue front window (root cause: a registry read without a subscription), the screen title bar, strips that fold into a menu Button at 393, the phone frame (704 px content). Five frame fences red on main 02ce9e8c, green after; web baseline zero branch-new; `assets/story-11-build/`. Next slice: the Chair as windows.

2026-10-02: #726 r3 R1–R6 and the post-#725 Chain/Coder re-walk are paid on the rebased draft head; r4 pins the pre-fix Atlas to reachable e2e92c582 and all 12 Documentation Navigation commands pass after regenerating the API reference. A clean GitHub clone at df9ae07c5d34f39502d4305ac5cb1a1f1e5b3adf found the pin and passed all 166 focused tests. Story 01 stays in-progress: B0 merged at `44ec934a`; canonical `evidence-story-01.md` is still pending, and B0 must run on B2's head with F2 green before the B2 merge record can pass. F7 remains a product defect for C7/story 17 or a named face-lane handoff. #727 H-A1 and #728 H-A2 remain in-progress until their face handoffs merge. Their r3 handoff/status rows are preserved above, including the bound intel-claim and source-derived decision fences and removal of the title-match Room milestone rule.

2026-10-02: #727 r4 integration proof: after #726 merged at 44ec934a, rebase dropped both B0 copies and rewrote the marker-bearing 29fb/780 history while retaining H-A3 `has_summary` and A1 `parked`; the original shared selection showed four source/join failures, the Atlas anchors were re-mapped to their actual definitions, and generated references were refreshed. The final shared-plus-A1 selection collected and passed 377 tests; all Documentation Navigation and generated-reference checks pass. Story 02 remains in-progress until A1-F merges.

2026-10-03: #728 r4 integration proof: after #727, the rebase dropped the stale A1 Park and duplicate B0 commits; the branch then advanced from #730 to latest main at #731 (`8485874f6`). Tests and walks used A2 source revision `0f32ddb87613638725ec80c471a6ced7b0b3e070`; the evidence-only commit records that run. The pre-fix C4 fence failed because skipping `dedupAttention` still returned 6; the repaired probe mints a second action through the real meeting producer, links it through the project route, and reads both real Door and Room routes. The exact oracle stays at 6; skipping dedup returns 7 with `philo13-a2-dedup-A2`. On this source revision, the shared/A2 Python selection passed 132, the serial seven-file web selection passed 63, typecheck passed, all ten documentation generators ran, and all 12 Documentation Navigation commands plus operations, OpenAPI and graph generated-reference checks exited 0. The actual Dock case passed 6→5 at 1440 and 393 native touch. The observations report dirty only because untracked verification receipts were present; A2 product source paths were unchanged from the #730 candidate and the isolated DBs were under each run's temporary HOME. Story 03 remains in-progress for A2-W. An extra, non-gating graph census returned 1 with 42 unmapped source entries and 5 miscited references; attribution is unknown ([receipt](assets/story-03-needs-you/r4-graph-census-backlog.txt)). The parallel seven-file Vitest attempt timed out one real-producer test at 5 seconds after 62 passed; the serial rerun passed all 63 ([receipt](assets/story-03-needs-you/r4-vitest-parallel-timeout.txt)). Current-head evidence: [Python](assets/story-03-needs-you/r4-on-731-run.txt), [web](assets/story-03-needs-you/r4-on-731-vitest.txt), [generators](assets/story-03-needs-you/r4-on-731-generation.txt), [navigation](assets/story-03-needs-you/r4-on-731-doc-navigation.txt), [walks](walks-03-astra.md#r4-actual-dock-walk-on-the-731-head).

2026-10-02: **The Workbench look RATIFIED by the owner** ("Ratify, build it"; Steel; Park one press; Capture as a fourth Chair window) after Astra's canvas checks r1–r5 (r5 RATIFY). Wave C faces may now be built to `design/workbench-look.md`; each merge record cites the ratification (story 11).

2026-10-01: **PHILO-13-11 (C1) canvases drawn, round two** (`assets/story-11-canvas/`, `design/workbench-look.md`): 29 boards at 1440 and 393 on the real product with a harness shim; direction **Workbench Steel** recommended over Honest 2.0; the fixed Desk drawn (one needs-you number, narrower counts named). In-progress: Astra's check, then the owner's ratification.

2026-10-01: **PHILO-13-05 (A4) done** in `wt-philo-13-muaddib` (Fedaykin; Muad'Dib verified): the closed-window ghost fixed at its seam (the card now closes by the id the store keeps); red on main → green in unit (5), glass (4) and the atlas at 1440 and 393; `elementFromPoint` hits the Desk after Close for six openers. PHILO-13-04 (A3) built and committed **in-progress**: acceptance 2 waits on handoff H-A3 (Astra: a stored-summary field on `/api/meetings` rows; the faces lane wires the rail). See the story's Amendment. UNCHECKED — awaiting Astra's counsel on built.

2026-10-02: #727, #728 and #726 counsel conditions are paid on their r2 draft branches and recorded in the ownership/handoff map above. Astra's H-A3 backend handoff is in progress on `feat/philo-13-a3h-astra`: `/api/meetings` list/search `has_summary` comes from the same latest persisted summary as detail and the face rail remains A3-W's. The five-column status index keeps Stories 01–04 in-progress. H-A3 stays in-progress until A3-W also merges.

2026-10-01, round two: Astra's check r1 DO-NOT-RATIFY paid on Muad'Dib's rulings (table under "Round two"). Next: Astra's check of r2; then the owner's ratification.

2026-10-01: DRAFTED (branch `docs/philo-13-charter`) from PROPOSAL r2 and the five forks he ruled. Eighteen stories, all `backlog`. Phase 12 folded (stories 02–06 `blocked`, parked — folded into PHILO-13 C5). D1 parked in BACKLOG. Next: Astra's check of this charter; then the owner's ratification. On ratification, 01 (B0) and 11 (C1, its canvas) flip to `ready`: each lane's long pole.

## Open dissents

None.

## Forecast

**Elapsed: 3–4 weeks** (PROPOSAL §4), two lanes in parallel. The gates are the C1 canvas ratification (Wave C waits on it), B0 on main before B2, the per-face canvas rounds (B1, B3, C5, C7), Astra's built checks, and C5's real-send legs. The grounding sizes each move S/M/L (`grounding/faces-jobs.md:152-161`; `grounding/structure.md:298-306`); each story carries its size. No day count per story is claimed.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| B2's shared lifecycle breaks an unwalked window | medium | B0 gates B2; the merge record cites B0's commit and evidence | B2 merges before B0's cases pass on main |
| C1 grows into a redesign of every body | medium | bodies inherit the material through `DeskWindowFrame`; C1 does not redesign every body (PROPOSAL C1) | a C1 commit that rewrites a body's content |
| Two lanes in one file | medium | one owner per path; named handoffs; two atlas files | a PR that changes a path its lane does not own |
| Palette or menu sends without his press | low | C4/C5 open the preview only | a `channel_sends` row or a kernel operation before Send |
| A fence passes on a double that lies | medium | mint through real producers; mutate the producer field to show the fence rejects it | a park, needs-you or recording fence that reads a field the real producer does not write |
| A face word changes and its fence is rewritten to pass | medium | rehome the guard onto live behaviour in the same commit | a guard edited only to match a removal |

## Decisions made (this phase)

- 2026-10-01 — the owner named the scope ("Both, the whole thing"), folded Phase 12 ("Fold it into the Desk work") and set the method ("Audit, then propose").
- 2026-10-01 — the owner ruled the five forks: "All the way"; "Opens its own window"; "Everything"; "Later"; the Send placement default stands.
- 2026-10-01 — Muad'Dib ruled B5 (the update draft reads the week without the engine).
- 2026-10-01 — DRAFTED: 18 stories in build order; two lanes; the file map; the canvas gate; Phase 12 02–06 `blocked` (parked — folded into C5), since `parked` is not a status the gate accepts (`.githooks/dw_pmo/model.py:18`) — Fedaykin docs lane for Muad'Dib.

- 2026-10-01 — round two: Astra r1 DO-NOT-RATIFY paid on Muad'Dib's rulings: one owner per path (faces/CSS/store/chair/window/menu/send/pullout → Muad'Dib; db/services/routes/projections/runtime/pure data modules → Astra); two atlas files; named handoffs H-B0a/b, H-A1 + A1-F, H-A2 + A2-W, H-B4 + B4-W, H-C3 + C3-W, H-B3, H-C5; "needs you" = the Chair's existing membership; B2's window families and drafts listed; the Parked artboard in C1's set; gates as merge-record evidence — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- The look itself (material, gadget art, the screen title bar, the Chair as windows): the C1 canvas, ratified by the owner.
- The B1, B3, C5 and C7 faces: their canvases, ratified by the owner.
- Each consolidation move: the story whose face receives it, after B0 walks the path.

## Round three — Astra check r2 (DO-NOT-RATIFY) paid

Astra r2 (`checks/charter-astra-r2.md`): r1's five fixes present; three conditions left, all paid by Muad'Dib directly.

| Astra r2 | Paid |
|---|---|
| F2 close → reopen place untested | story 07: a close → reopen acceptance per returning family, actual atlas cases at 1440 and touch at 393 |
| F3 Trust exempt against "Everything" | story 07: Trust **returns** (open state + rect) |
| F4 H-B0b line ref and the shared contract | `:492` (the count); H-B0b filters the count only; the shared semantic checks cover both Phase 13 atlas files, shown red on a broken case (story 01) |
