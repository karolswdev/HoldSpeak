# PHILO-9-03 - The Room's face tells the truth (canvas first)

- **Project:** holdspeak-philo
- **Phase:** 9
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter and his answer to Q3; the items canvas ratified before the items section is built; PHILO-9-01 for the backend reads (health, NEEDS YOU, RECEIPTS, the Room read)
- **Unblocks:** PHILO-9-05, PHILO-9-06
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Codex Astra checks
- **Closure finding:** `docs/internal/philo/phase-9/grounding/README.md` F1, F2, F3, F7, F10, F11, F15 (corrected); shots under `docs/internal/philo/phase-9/grounding/face/`; Codex Astra r1 F5, F7, F8
- **Canvas:** under Q3 (a) the items section; under Q3 (b) the items section and its Add control; under Q3 (c) none — at both widths, from the library species, ratified by the owner before build. The other repairs draw an existing state honestly and need no canvas.
- **Backend:** none here. Health, NEEDS YOU, RECEIPTS and the Room read are story 01's `ProjectService` edits; a backend change this lane finds goes to story 01's lane by patch, never co-edited.

## Problem

- **F1:** eight callers open the Room with the key `project-room`, which is registered nowhere; the fallback `/projects` is no route and `web/src/App.tsx:68` sends it home (`web/src/desk/chair/ChairHome.tsx:851,864,1815,1953`, `web/src/desk/components/SystemShade.tsx:458,594`, `web/src/features/project-room/recall/RecallFace.tsx:84`, `web/src/pages/cores/history/MeetingReview.tsx:273`). Walked: a meeting's project button opens nothing at 1440 and 393. The working key is `open-project-memory` with the scope `project:<id>` (`web/src/desk/components/DeskToolShelf.tsx:341`).
- **F2:** the Room has no items section (`web/src/features/project-room/ProjectRoomCore.tsx`), so a milestone seven days late does not show; health says ON TRACK.
- **F3:** the steward face counts each phase's checkpoint step as a source, a proposal and an effect (`web/src/features/project-room/steward/StewardPosture.tsx:155-164`): "Act 1 effect" for a run with `actions_taken: 0`. The run is not empty: COMPARE opened a review (`holdspeak/services/project_steward_service.py:860-869`). With no policy no effect kind is eligible, and the face does not say so.
- **F7:** RECEIPTS shows the Room's own reads ("READ MEETINGS" ×n), not the writes.
- **F10:** at 393 the Ask well covers the Steward verb and the SOURCES heading on first view.
- **F11:** the update list says "DRAFTS" for a published update, its row words run together, and its emblem is a fixed "E" (`web/src/features/project-room/update/UpdatePosture.tsx:257`, `:268-270`).
- **F15 (corrected, code-read):** the normal SUGGESTED row's Add and Dismiss are wired (`ProjectRoomCore.tsx:976-1000`); the Button with no action (`:1050`) is on a watch source row whose `src.suggested` is set.

## Scope

- **In:** one registered key for the Room and every `openSurfaceOr("project-room", …)` caller moved to it (close the class: a census of callers, handover XXX law 9); the items section as Q3 rules (under (a): no Add control, items come from owner-authenticated MCP; under (b): with the Add control; under (c): none); the steward counts read from the run's effect steps, the review COMPARE opened shown, and "no effect allowed" said in words; RECEIPTS drawn from story 01's write receipts; the Ask well not covering a verb at 393; the update list's head, spacing and emblem; the `:1050` branch reproduced, then wired or withheld (UX-CANON §A.11).
- **Out:** an Add control unless Q3 (b); the Room's other postures (Prepare, Ask, people); any `ProjectService` edit (story 01).

## Acceptance criteria

Per the charter's red-first matrix: behavioural red where affected, preservation green where not.

- [ ] Every caller of the Room opens the Room for its project, one caller per face fenced, at 1440 and 393 (red on main at both: the meeting's project button).
- [ ] Under Q3 (a)/(b): a past-due milestone and a risk show in the Room as the ratified canvas draws them, at both widths (red on main at both). Under Q3 (c): no box; F2 stays on the BACKLOG.
- [ ] The steward face's source, proposal and effect counts equal the hub's run, read in the same fence; the opened review is shown; a run with nothing allowed says so (red on main at both widths: "Act 1 effect" for 0 actions).
- [ ] RECEIPTS lists the writes (create, publish, steward run), as rendered after each transition (red on main at both widths).
- [ ] At 393 `elementFromPoint` at the Steward verb's centre hits the verb (red on main: `room-ask-well`); at 1440 preservation green.
- [ ] The update list's words are right for each lifecycle (red on main at both widths).
- [ ] Every verb on the touched faces is the library Button; the web baseline has zero branch-new.

## Effort (not a promise)

PROVISIONAL: 1.5–2.5 engineering days, the items canvas included.

## Test plan

- **Fences and atlas cases ship with this story** (story 05 only assembles and reruns).
- **Glass:** executable failing assertions through the real hub on an isolated HOME at 1440 and 393; the steward counts compared with `GET /api/projects/{id}/steward/runs` in the same test; existing atlas words changed in the same commit as the face.
- **Web unit:** `uv run python scripts/check_web_baseline.py --run`.
- **Manual / device:** the owner's review of the canvas and the shots.

## Notes

- 2026-09-27 — drafted by the Fedaykin docs lane for Muad'Dib; unratified. The Chair, shade and recall callers of F1 were not clicked in the grounding (they need a connector snapshot or a decision in a Room).
- 2026-09-27 — round two (Codex Astra r1 paid): Q3 propagated; backend moved to story 01; F3 and F15 corrected; the red-first matrix.
