# PHILO-13-15 - C5 Send to from any document window (the Phase 12 fold)

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** PHILO-13-11 (C1 canvas ratified); this story's own canvas ratified; PHILO-12-01 (done, merged #717)
- **Unblocks:** PHILO-13-14 (the palette's `Send …` row uses the push seam)
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** C5 (PROPOSAL §3, Wave C; "The Phase 12 fold"); fork 5 (the default stands)
- **Closure finding:** `grounding/faces-jobs.md:117-142` (the fold), move 4 (`:155`); `grounding/structure.md:195-214`, move 5 (`:304`); `grounding/checks/proposal-astra.md` finding 6; carries Phase 12 stories 03, 05 and 06 (window side)
- **Canvas:** one, on the C1 material, at 1440 and 393: the in-window origin (Phase 12 boards H, G7–G9, I2–I3, J1 redrawn for the window; `grounding/faces-jobs.md:142`)

`grounding/` = `docs/internal/philo/phase-13/grounding/`. Phase 12 = `../phase-12-send-from-the-floor/`.

## Goal

From any document window, `Send to ▸` in the window's title-bar menu and in the Object menu (one composition, fork 5) picks a saved destination; the window's SEND well shows the exact preview, in view; he presses Send in the well.

## Problem

The title-bar right-click builds Minimize / Maximize / Close only (`web/src/desk/components/window/windowMenuAdapter.tsx:16-56`; `web/src/desk/components/DeskWindow.tsx:815-821`). Phase 12's design names Floor, list and menu-bar origins only; an in-window origin was never designed (`../phase-12-send-from-the-floor/design/floor-send.md:57`; `grounding/PLAN.md:23-35`). The pick lives in a private module map, set once (`web/src/desk/surface/send/SendWell.tsx:64`, `:572`); the meeting form is private (`web/src/meetings/MeetingSendWell.tsx:28`, `:34`). At 393 the well sits below the fold of a ~540 px window (`grounding/shots/jobs/J2-04-preview-393.png`). Closing Meetings mid-send loses the record and the well (`J2-05-came-back-1440.png`). The artifact window has no SEND well and three raw buttons (`web/src/desk/pullouts/ArtifactPullout.tsx:13`, `:38`, `:57`, `:64`). Each window's document ref exists: `desk_decision` (`web/src/desk/documentSends.tsx:33-35`), `monday_brief` (`:28-31`), `decision_record` (`:37-39`), the meeting forms (`MeetingSendWell.tsx:31-54`), `project_update` (the Room's Update posture), `artifact` (Phase 12 story 01). The menu species nests; at ≤720 px the submenu replaces the panel (`web/src/desk/components/DeskMenu.tsx:182-201`, `:592`). Story 01's seams carry: `floorSendBinding.resolve` (`web/src/desk/floorSendBinding.ts:61`), `GET /api/brief/{brief_id}` (`holdspeak/web/routes/monday_brief.py:152`), `_ArtifactSource` (`holdspeak/services/document_sources.py:495`).

## Scope

- **In:**
  - **The canvas** (UX-CANON A.2): the in-window origin at 1440 and 393; Astra checks; the owner ratifies.
  - **One composition** of `Send to ▸` from the window's own document ref, in the title-bar menu and in the Object menu (`DeskMenuBar.tsx:78-95` reads the front window's document). Rows from the active destinations; `Add destination` when there are none (opens Settings at the form); withheld where the window's document cannot send (A.11; a meeting with no summary has no well, `web/src/desk/pullouts/MeetingPullout.tsx:152-155`).
  - **The push seam** (Phase 12 design §6): one setter per well; an open well reacts in place; the destination kept across Summary → Digest → Follow-up; the Room link `{ projectId, updateId, destinationId }`, also when the Room is open on another update; the exact brief-id handoff (`latest` never substitutes).
  - **The reads** where the window does not already hold the fact: meeting summary presence and a project's latest published update, each `pending` / known / failed; `pending` is never a refusal; a failed read shows `CAN'T CHECK` and still opens the well.
  - **The arrival:** the picked row, its preview and Send come into view at both widths, clear of sticky strips.
  - **The artifact window:** its SEND well on `artifact:<id>`; its three raw buttons become library Buttons.
  - **The tie rule** (Muad'Dib, 2026-09-30, Phase 12 story 03 notes): the latest published update is the greatest `published_at`, then the greatest `rowid`. If the read (`holdspeak/web/routes/project_updates.py:61`) does not apply it, handoff **H-C5**: Astra's lane changes the read (its files); this story edits no backend file.
- **Out:** the Floor icons, the drop, its tag, the brief icon on the Floor, the decision and channel sprites, J2 (parked with Phase 12); `Send` from the palette that sends (C4 opens the preview only); a `Send` Button in each footer (fork 5's alternative, not chosen); notes as documents.

## Acceptance criteria

- [ ] Canvas ratified by the owner (his word recorded) before the first face commit.
- [ ] Send from an open meeting in 3 gestures (right-click title → `Send to ▸` → destination; then Send) at 1440 and at 393 (touch long-press); the preview arrives in view.
- [ ] `Send to ▸` from one composition in the title-bar menu and the Object menu for each sendable kind; withheld where it cannot send; `Add destination` with none.
- [ ] Zero `channel_sends` rows and zero kernel operations until he presses Send.

**Phase 12's fences, carried** (`grounding/structure.md:209-212`; `../phase-12-send-from-the-floor/story-05-the-atlas-cases.md`, `story-06-the-closing-use.md`):

- [ ] **Per-document atlas cases for the five kinds** (decision, meeting summary forms, project update, brief, artifact), each minted through its real producer, one case per `scripts/graph_walk.py run` invocation, at 1440 and 393 (touch), with `.op` siblings that read the hub's send row and receipt; each red on the pre-feature revision and green on the head; a mutated producer field shows the fence rejects the wrong outcome.
- [ ] **Rendered transitions with receipts in every branch the click leaves:** a second pick on an open well changes it in place; Summary → Digest → Follow-up keeps the destination and sends the chosen form; the Room open on another update switches to the linked update; Intelligence → BRIEF keeps the handed brief id when `latest` is another; a document or form change during prepare. Each ends with Send and its receipt, at both widths.
- [ ] **The same-second latest-update tie:** two publishes inside one second through the real routes; the read names the later-inserted update.
- [ ] **Refusals:** a parked destination and an absent document (known no summary, known no published update) refuse by name; `pending` never refuses.
- [ ] **Artifact:** picked, PREPARED and SENT outcomes; no raw `<button>` in `ArtifactPullout` (red on main).
- [ ] **The real-send leg:** for each retained kind on the channels he has, a real send by `Send to ▸`, read back from the far side, or a named limit with its reason. A cold Codex session prepares one artifact send from the MCP catalogue alone; he presses Send on the face. Secrets redacted at capture. Rehearsed, owner-reviewed shots; never recorded as a sitting.
- [ ] The Phase 7–11 atlas cases still pass; the web baseline has zero branch-new failures.
- [ ] **Gate (review evidence):** this story's PR merge record cites the owner's ratification record of its canvas (path + his quote); without it the checker refuses the merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on the composition per kind and per refusal; the reads' states; the push seams; `uv run python scripts/check_web_baseline.py --run`. Story 01's focused Python tests re-run (`grounding/probes/structure-tests-output.txt` lists them).
- **Glass:** Playwright through the real hub on an isolated HOME at both widths, touch at 393; each fence ends with Send and reads the hub's send row and receipt.
- **Atlas:** the per-document and transition cases above, one case per `scripts/graph_walk.py run` invocation.
- **Real send:** the FILE destination in the HOME, read back; other channels by his named targets or a named limit.
- **Shots:** each board as built, both widths.

## Worker-brief scars

- **The receipt under one branch:** a fence that checks the receipt only on success proves one branch; every branch the click leaves shows its receipt (Phase 12 design §6).
- **Doubles that lie:** each document is minted through its real producer; a send row is read from the hub, not from the face.
- **Never rewrite a guard to match a removal:** Floor-origin guards are parked with their scope, not deleted or loosened to make this story green; the Phase 11 no-internal-id fence keeps all nine kinds.
- **Labels stay strings:** a submenu label also names its panel for a screen reader (`web/src/desk/components/DeskMenu.tsx:638`; Phase 12 story 03 notes).
- **Touch is the proof at 393:** a mouse right-click does not count.

## Effort (not a promise)

Grounding size: M (`grounding/faces-jobs.md:155`; `grounding/structure.md:304`). PROVISIONAL.

## Notes

- 2026-10-02 — canvas drawn for the owner's ruling, NOT RATIFIED: `assets/story-15-canvas/` (README lists the boards, the acceptance line each answers, the forks and the limits). Drawn by a Fedaykin on main `76c361537` (the C1 frame and C2 window menu built); unchecked, awaiting Astra's check, then the owner.
- 2026-10-01 — `web/src/meetings/MeetingSendWell.tsx` and `web/src/desk/components/DeskMenuBar.tsx` are not named in PROPOSAL §4's map; assigned to this lane (status file, "File ownership").
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
