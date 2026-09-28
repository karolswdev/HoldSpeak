# PHILO-9-03 - The Room's face tells the truth (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter (his Q0 and Q3 rulings); the items canvas and the copy-and-confirm canvas, each ratified before its face is built; PHILO-9-02 for the mark-delivered route; PHILO-9-01 for the backend reads (health, NEEDS YOU, RECEIPTS, the Room read); PHILO-9-02's review-id repair (F20) before the steward face can show the review its run opened
- **Unblocks:** PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F1, F2, F3, F7, F10, F11, F15 (corrected); shots under `docs/internal/philo/phase-9/grounding/face/`; Codex Astra r1 F5, F7, F8
- **Canvas:** two, at both widths, from the library species, ratified by the owner before build: **the items section** (the Q3 ruling: no Add control) and **the copy-and-confirm moment** (the Q0 ruling: a published update always offers Mark delivered with an optional inline To field — including when he returns after copying, since the Copy feedback expires in 2 s, `useUpdateController.ts:169`, and no clipboard state is stored (R4-3); the delivery history on the update and the DELIVERED chip in the list, its form (×N or the latest time and To) decided on the canvas; a mistaken delivery stays in the history, a later correct one does not retract or mark it, and DELIVERED ×N counts both — the canvas shows that limitation faithfully (undo is on the BACKLOG); each press of Mark delivered mints one `command_id` and keeps it across its retries (Codex Astra r5); no modal, UX-CANON §A.4; no egress badge, because the product sends nothing). The other repairs draw an existing state honestly and need no canvas.
- **Backend:** none here. Health, NEEDS YOU, RECEIPTS and the Room read are story 01's `ProjectService` edits; a backend change this lane finds goes to story 01's lane by patch, never co-edited.

## Problem

- **F1:** eight callers open the Room with the key `project-room`, which is registered nowhere; the fallback `/projects` is no route and `web/src/App.tsx:68` sends it home (`web/src/desk/chair/ChairHome.tsx:851,864,1815,1953`, `web/src/desk/components/SystemShade.tsx:458,594`, `web/src/features/project-room/recall/RecallFace.tsx:84`, `web/src/pages/cores/history/MeetingReview.tsx:273`). Walked: a meeting's project button opens nothing at 1440 and 393. The working key is `open-project-memory` with the scope `project:<id>` (`web/src/desk/components/DeskToolShelf.tsx:341`).
- **F2:** the Room has no items section (`web/src/features/project-room/ProjectRoomCore.tsx`), so a milestone seven days late does not show; health says ON TRACK.
- **F3:** the steward face counts each phase's checkpoint step as a source, a proposal and an effect (`web/src/features/project-room/steward/StewardPosture.tsx:155-164`): "Act 1 effect" for a run with `actions_taken: 0`. The run is not empty: COMPARE opened a review (`holdspeak/services/project_steward_service.py:860-869`). With no policy no effect kind is eligible, and the face does not say so.
- **F7:** RECEIPTS shows the Room's own reads ("READ MEETINGS" ×n), not the writes.
- **F10:** at 393 the Ask well covers the Steward verb and the SOURCES heading on first view.
- **F11:** the update list says "DRAFTS" for a published update, its row words run together, and its emblem is a fixed "E" (`web/src/features/project-room/update/UpdatePosture.tsx:257`, `:268-270`).
- **Delivery (the Q0 ruling):** Copy exists (`web/src/features/project-room/update/UpdatePosture.tsx:580-587`, `useUpdateController.ts:163-179`) but nothing lets him say he delivered it, and nothing shows that he did.
- **F15 (corrected, code-read):** the normal SUGGESTED row's Add and Dismiss are wired (`ProjectRoomCore.tsx:976-1000`); the Button with no action (`:1050`) is on a watch source row whose `src.suggested` is set.

## Scope

- **In:** one registered key for the Room and every `openSurfaceOr("project-room", …)` caller moved to it (close the class: a census of callers, handover XXX law 9); the items section (the Q3 ruling: no Add control; items come from owner-authenticated MCP); **the copy-and-confirm moment** on a published update — Copy, then Mark delivered with the optional To, calling story 02's `project.mark_update_delivered` route, each delivery listed with its time and To on the update, the DELIVERED chip in the update list, each delivery in RECEIPTS; a refusal named on the face; the steward counts read from the run's effect steps, the review COMPARE opened shown, and "no effect allowed" said in words; RECEIPTS drawn from story 01's write receipts; the Ask well not covering a verb at 393; the update list's head, spacing and emblem; the `:1050` branch reproduced, then wired or withheld (UX-CANON §A.11).
- **Out:** an Add control for items (BACKLOG); automated send (BACKLOG); the Room's other postures (Prepare, Ask, people); any `ProjectService` edit (story 01).

## Acceptance criteria

Per the charter's red-first matrix: behavioural red where affected, preservation green where not.

- [ ] Every caller of the Room opens the Room for its project, one caller per face fenced, at 1440 and 393 (red on main at both: the meeting's project button).
- [ ] A past-due milestone and a risk show in the Room as the ratified canvas draws them, at both widths (red on main at both).
- [ ] Mark delivered is offered on a published update when the window is reopened after Copy (the return state, R4-3) and after an earlier delivery; Copy then Mark delivered (To "Priya"), then again (To "Tomas"), writes two rows — read back from the hub in the same fence — and the face shows both deliveries and the ratified DELIVERED chip at 1440 and 393; a double-click on one press yields one row, and the rendered transition from pending to delivered is fenced (Codex Astra r5); a mistaken delivery followed by a correct one shows both, the count includes both; a draft offers no Mark delivered; no egress badge appears (a new capability: no red claimed; readbacks and a mutation).
- [ ] The steward face's source, proposal and effect counts equal the hub's run, read in the same fence; the opened review is shown; a run with nothing allowed says so (red on main at both widths: "Act 1 effect" for 0 actions).
- [ ] RECEIPTS lists the writes (create, publish, steward run), as rendered after each transition (red on main at both widths).
- [ ] At 393 `elementFromPoint` at the Steward verb's centre hits the verb (red on main: `room-ask-well`); at 1440 preservation green.
- [ ] The update list's words are right for each lifecycle (red on main at both widths).
- [ ] Every verb on the touched faces is the library Button; the web baseline has zero branch-new.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days, the two canvases included.

## Test plan

- **Fences and atlas cases ship with this story** (story 05 only assembles and reruns).
- **Glass:** executable failing assertions through the real hub on an isolated HOME at 1440 and 393; the steward counts compared with `GET /api/projects/{id}/steward/runs` in the same test; existing atlas words changed in the same commit as the face.
- **Web unit:** `uv run python scripts/check_web_baseline.py --run`.
- **Manual / device:** the owner's review of the canvas and the shots.

## Notes

- 2026-09-27 — canvases round three (Codex Astra canvases r2 finding 5): the build owns one open the canvas accepted: at 1440 the sticky Ask well covers the `RECEIPTS` head on first view (items canvas boards 1a, 2a); the F10 repair drawn at 393 does not reach it. Repair it in this build, fenced at 1440.
- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The Chair, shade and recall callers of F1 were not clicked in the grounding (they need a connector snapshot or a decision in a Room).
- 2026-09-27 — round eight (Codex Astra r5): one key per confirm gesture; double-click and the pending/success transition fenced; the mistaken mark shown faithfully.
- 2026-09-27 — round seven (the owner's "Several per update"): the delivery history; Mark delivered always offered on a published update; no `already_delivered`.
- 2026-09-27 — round six (Codex Astra r4, R4-3): the return state on the copy-and-confirm canvas; the clipboard fenced here as glass, not claimed by story 06.
- 2026-09-27 — round five (the owner's rulings): the copy-and-confirm moment and its canvas; the Q3 branches removed.
- 2026-09-27 — round two (Codex Astra r1 paid): Q3 propagated; backend moved to story 01; F3 and F15 corrected; the red-first matrix.
