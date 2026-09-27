# PHILO-9-03 - The Room's face tells the truth (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter and his answer to Q3; the items canvas ratified before the items section is built; PHILO-9-01 for the Room read the steward and updates rows need
- **Unblocks:** PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F1, F2, F3, F7, F10, F11, F15; shots under `docs/internal/philo/phase-9/grounding/face/`
- **Canvas:** the items section (if Q3 keeps it), both widths, from the library species, ratified by the owner before build. The other repairs draw an existing state honestly and need no canvas.

## Problem

- **F1:** eight callers open the Room with the key `project-room`, which is registered nowhere; the fallback `/projects` is no route and `web/src/App.tsx:68` sends it home (`web/src/desk/chair/ChairHome.tsx:851,864,1815,1953`, `web/src/desk/components/SystemShade.tsx:458,594`, `web/src/features/project-room/recall/RecallFace.tsx:84`, `web/src/pages/cores/history/MeetingReview.tsx:273`). Walked: a meeting's project button opens nothing at 1440 and 393. The working key is `open-project-memory` with the scope `project:<id>` (`web/src/desk/components/DeskToolShelf.tsx:341`).
- **F2:** the Room has no items section (`web/src/features/project-room/ProjectRoomCore.tsx`), so a milestone seven days late does not show; health says ON TRACK (overdue counts commitments only, `holdspeak/services/project_service.py:1457-1461`).
- **F3:** the steward face counts each phase's checkpoint step as a source, a proposal and an effect (`web/src/features/project-room/steward/StewardPosture.tsx:155-164`): "Act 1 effect" for a run with `actions_taken: 0`; with no policy nothing is eligible, and the face does not say so.
- **F7:** RECEIPTS shows the Room's own reads ("READ MEETINGS" ×n), not the writes (`project_service.py:1933`).
- **F10:** at 393 the Ask well covers the Steward verb and the SOURCES heading on first view.
- **F11:** the update list says "DRAFTS" for a published update, its row words run together, and its emblem is a fixed "E" (`web/src/features/project-room/update/UpdatePosture.tsx:257`, `:268-270`).
- **F15 (code-read):** a suggested source row's "Add" Button has no action (`ProjectRoomCore.tsx:1050`).

## Scope

- **In:** one registered key for the Room and every `openSurfaceOr("project-room", …)` caller moved to it (close the class: a census of callers, handover XXX law 9); the items section and health as Q3 rules (canvas first); the steward counts read from the run's effect steps and the "nothing is allowed" state said in words; RECEIPTS from the Room's writes; the Ask well not covering a verb at 393; the update list's head, spacing and emblem; F15 reproduced, then wired or withheld (UX-CANON §A.11).
- **Out:** an "add item" form unless Q3 (b); the Room's other postures (Prepare, Ask, people).

## Acceptance criteria

- [ ] Every caller of the Room opens the Room for its project at 1440 and 393 (red on main: the meeting's project button).
- [ ] A past-due milestone shows in the Room and turns health, as the ratified canvas draws it (red on main).
- [ ] The steward face's source, proposal and effect counts equal the hub's run, read in the same fence; a run with nothing allowed says so (red on main: "Act 1 effect" for 0 actions).
- [ ] RECEIPTS lists the writes (create, publish, steward run), not the Room's reads (red on main).
- [ ] At 393 `elementFromPoint` at the Steward verb's centre hits the verb (red on main: `room-ask-well`).
- [ ] The update list's words are right for each lifecycle (red on main).
- [ ] Every verb on the touched faces is the library Button; the web baseline has zero branch-new.

## Effort (not a promise)

PROVISIONAL: 2–3 engineering days, the items canvas included.

## Test plan

- **Glass:** fences through the real hub on an isolated HOME at 1440 and 393, each red on main; the steward counts compared with `GET /api/projects/{id}/steward/runs` in the same test.
- **Web unit:** `uv run python scripts/check_web_baseline.py --run`.
- **Manual / device:** the owner's review of the canvas and the shots.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The Chair, shade and recall callers of F1 were not clicked in the grounding (they need a connector snapshot or a decision in a Room); the lane fences at least one caller per face.
