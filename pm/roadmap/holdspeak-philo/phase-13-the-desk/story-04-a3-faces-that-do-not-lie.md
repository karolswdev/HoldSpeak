# PHILO-13-04 - A3 Faces that do not lie

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** done
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** PHILO-13-13 (C3 shows REC only when the hub confirms)
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** A3 (PROPOSAL §3, Wave A)
- **Closure finding:** `grounding/faces-jobs.md` F2 (`:168`), F4 (`:170`), F11 (`:177`), F13 (`:179`), F14 (`:180`); `grounding/faces-surfaces.md` F2 (`:189`), F5 (`:192`); `grounding/checks/faces-astra.md` finding 2
- **Canvas:** none new (words and states in existing species); any new element goes on the C1 material

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

Each face names the one fact it shows, from that fact's source. A refused start says so. A failure is plain words with a verb, never raw server text.

## Problem

- **Record lies.** `startRecording` awaits a bare `fetch` and sets `recording` with no `res.ok` check (`web/src/desk/store/recordingSlice.ts:47-56`; `web/src/lib/api.ts:27-32`). After a 501 from `POST /api/meeting/start` (`holdspeak/web/routes/meetings/live.py:100`) the orb shows recording and a timer runs; no receipt (`grounding/shots/jobs/J2-01-start-refused-1440.png`, `-393.png`; `grounding/probes/faces-jobs-record-start.out.txt`).
- **Faces name different facts with one word.** Settings `Meetings ✓ SUMMARY ON` reads the config switch (`web/src/pages/cores/settingsPrefs.tsx:515-517`); the Chair says `No engine for summaries`; Trust says `MEETING SUMMARY ● OFF` with a green dot (`web/src/desk/components/TrustWindow.tsx:62-68`, `:107-110`); Meetings shows `SUMMARY OFF` and `4 meetings need summaries` beside three stored summaries (`grounding/shots/surfaces/15-settings-pop-1440.png`, `103-objwin-this-device-chip-pop-1440.png`, `grounding/shots/jobs/J2-02-summary-1440.png`). Trust "Enabled destinations None" is **withdrawn** as a defect (a local FILE target; `holdspeak/setup_status.py:208`; `grounding/faces.md:21`).
- **Raw server text.** Intelligence BRIEF prints the server's `detail` (`grounding/shots/jobs/J1-09-intelligence-brief-failed-1440.png`); the Room's publish failure prints `injected failure` (`J4-07-publish-failed-1440.png`); People prints `people_store_unavailable` and replaces the whole window (`J3-06-note-failed-1440.png`, `J3-07-after-recovery-1440.png`). Ask runs with no model and fails with a raw model path (`grounding/shots/surfaces/120-engine-off-ask-pop-1440.png`). The voice failure is a sentence with `Open Setup` as text (`J5-02-voice-result-1440.png`).

## Scope

- **In:**
  - `startRecording` reads `res.ok`; a refused or failed start shows `Not recording` + the reason, with a verb where one exists; no timer.
  - Each status face names the one fact it shows: **configured** (summary on in Settings), **available** (an engine can run now), **stored** (summaries exist). Settings, Trust, the Chair and Meetings each say which; dot colour matches the fact (no green on OFF, A.10).
  - **H-A3 (Astra's data handoff):** `/api/meetings` list and search rows carry `has_summary`, derived from the latest persisted summary read by detail, independent of configuration and run status. The rows disclose the boolean, never the summary text. **A3-W (Muad'Dib's face handoff):** wire the stored-summary rail to this field after H-A3 merges. The story stays in-progress until both halves merge.
  - Failure faces in plain words with a verb (A.3, A.10, Tenet 4): Intelligence BRIEF, the Room publish, People (the window keeps the person and the draft; the failure is a row, not the window), Ask with no model (withhold ASK or name the fact, A.11), the voice failure (`Open Setup` as a library Button).
  - Files (all the faces lane's): `recordingSlice.ts`, `settingsPrefs.tsx`, `TrustWindow.tsx`, the pullout views, `PeopleCore.tsx` (the People failure face), the Room face (the publish failure), `AskPanel.tsx`. No other lane's file.
- **Out:** making the engine work; Meetings' needs-you wording (A2); the People store itself.

## Acceptance criteria

- [ ] A refused start (501) shows `Not recording` + the reason at both widths; no `is-recording`, no timer. Red on main (`J2-01`), green here. The fence boots a real hub with no recorder; no mocked `fetch`.
- [ ] Settings, Trust, the Chair and Meetings each name the fact they show; no face shows "ON" for a fact that is "OFF" elsewhere; two faces differ only when they name different facts. Shots at both widths on the populated week with the engine off.
- [ ] No raw server text (`detail` strings, error codes, model paths) on Intelligence BRIEF, the Room publish failure, People or Ask; each failure has a verb. A static fence over these faces' failure branches.
- [ ] A People store failure keeps Priya's window and the unsent note; the failure is a row with a verb.
- [ ] Every verb the library Button; no prose (A.3 one-line empty-state exception only).
- [ ] **H-A3:** real import/admission/summary producers persist one summary and leave one meeting unsummarized; `/api/meetings` list and search report true only for the persisted summary, matching the detail read after both config and run status are disabled; neither route leaks the generated summary string.
- [ ] **A3-W:** the stored-summary rail reads `has_summary`; this story closes only after H-A3 and A3-W both merge.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` holds this lane's NEW cases (`--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`. An existing case runs from the atlas that holds it (named below).
- **Focused:** web unit on `recordingSlice` (non-ok response → idle + reason); the fact labels; H-A3's `tests/unit/test_philo13_a3h_meeting_summary.py` and directly relevant summary detail tests; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** Playwright through the real hub on an isolated HOME: the 501 start; injected 500/503 for the brief, publish and People reads (the J1/J3/J4 recovery legs of `grounding/faces-jobs.md`).
- **Atlas:** `case.j4.record_start.capture_recording` (in `docs/internal/philo/graph/atlas.json`) is BLOCKED today (no `browser_audio_device`, `grounding/faces-jobs.md:36`); a refused-start case that needs no microphone, `case.p13.record.refused_not_recording` (in `atlas-phase13-muaddib.json`), at 1440 and 393 (touch), one case per invocation.
- **Shots:** 1440 and 393, touch at 393.

## Worker-brief scars

- **Doubles that lie:** the refused start is the real hub's 501, not a stubbed `fetch` that never existed in production.
- **The receipt under one branch:** every branch the Record press leaves (started, refused, network failure) shows its own true state.
- **Fences that name old words:** fences asserting `SUMMARY ON`, `RECORDING` after a refusal, or a raw error string change in the same commit.

## Effort (not a promise)

Grounding size: Record `res.ok` is part of move 5 (M) (`grounding/faces-jobs.md:156`). PROVISIONAL.

## Notes

- 2026-10-02 — Astra's H-A3 r2 handoff is in progress on `feat/philo-13-a3h-astra`; the list/search boolean is data-only and stays in-progress pending Muad'Dib's A3-W rail.
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.

## Amendment — 2026-10-01 (Muad'Dib, visible; the owner may overrule)

Built and verified in the faces lane (`evidence-story-04.md`). **Acceptance 2 is partly met:** the Meetings **list rail** still reads `OFF` beside a meeting that stores a summary, because `/api/meetings` list rows carry no summary field (a route change, Astra's file). New named handoff **H-A3:** Astra adds a stored-summary field to the `/api/meetings` list rows (real producer, route fence); the faces lane wires the rail (`HistoryCore.tsx`) to name the fact `SUMMARY STORED`. This story stays **in-progress** until both halves merge. Ledger from the build (homes): Intelligence's Acknowledge/Defer/Speak still shown on a brief failure (A.11) → B1; Room *load* failures still print raw text (`useProjectRoomController.ts`, `ProjectRoomCore.tsx:2302`) → B1; Ask's no-model case matched on hub text → C4; Settings `Voice ✓ LIVE` vs Speak `DICTATION NOT SET` → C6.

## Closed — 2026-10-02

Acceptance 2's open half is paid: H-A3 merged in #729 (Astra; `has_summary` on `/api/meetings` list and search rows), A3-W wired in the faces lane — the Meetings list rail says `SUMMARY STORED` beside a meeting that stores a summary, independent of configuration and run status; an ACTIVE run (RUNNING / QUEUED / FAILED with Retry) shows first (Muad'Dib's ruling: the live fact leads). Fenced in vitest (`railSummaryStored.philo13.test.tsx`, red on main and on the pre-ruling order) and in glass through the real producer (`TestMeetingsRailNamesStored`, 1440 + touch 393; `assets/story-04-shots/meetings-rail-stored-*`). All story-04 shots re-captured on the finished frame. Counsel: Astra r1 DNR → r2 DNR → r3 RATIFY-WITH-CONDITIONS, paid (`checks/faces-w1-counsel-astra-r1..r3.md`). Final capture: `evidence-story-04.md` 2026-10-02T20:07Z (vitest 94, tsc clean, pytest 52).
