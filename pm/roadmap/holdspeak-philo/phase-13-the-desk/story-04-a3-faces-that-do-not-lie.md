# PHILO-13-04 - A3 Faces that do not lie

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
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
  - Failure faces in plain words with a verb (A.3, A.10, Tenet 4): Intelligence BRIEF, the Room publish, People (the window keeps the person and the draft; the failure is a row, not the window), Ask with no model (withhold ASK or name the fact, A.11), the voice failure (`Open Setup` as a library Button).
  - Files: `recordingSlice.ts`, `settingsPrefs.tsx`, `TrustWindow.tsx`, the pullout views. `PeopleCore.tsx` (Astra's, B4) and the Room face land through a brief exchange, merged serially.
- **Out:** making the engine work; Meetings' needs-you wording (A2); the People store itself.

## Acceptance criteria

- [ ] A refused start (501) shows `Not recording` + the reason at both widths; no `is-recording`, no timer. Red on main (`J2-01`), green here. The fence boots a real hub with no recorder; no mocked `fetch`.
- [ ] Settings, Trust, the Chair and Meetings each name the fact they show; no face shows "ON" for a fact that is "OFF" elsewhere; two faces differ only when they name different facts. Shots at both widths on the populated week with the engine off.
- [ ] No raw server text (`detail` strings, error codes, model paths) on Intelligence BRIEF, the Room publish failure, People or Ask; each failure has a verb. A static fence over these faces' failure branches.
- [ ] A People store failure keeps Priya's window and the unsent note; the failure is a row with a verb.
- [ ] Every verb the library Button; no prose (A.3 one-line empty-state exception only).

## Test plan

- **Focused:** web unit on `recordingSlice` (non-ok response → idle + reason); the fact labels; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** Playwright through the real hub on an isolated HOME: the 501 start; injected 500/503 for the brief, publish and People reads (the J1/J3/J4 recovery legs of `grounding/faces-jobs.md`).
- **Atlas:** `case.j4.record_start.capture_recording` is BLOCKED today (no `browser_audio_device`, `grounding/faces-jobs.md:36`); a refused-start case that needs no microphone, at 1440 and 393 (touch), one case per invocation.
- **Shots:** 1440 and 393, touch at 393.

## Worker-brief scars

- **Doubles that lie:** the refused start is the real hub's 501, not a stubbed `fetch` that never existed in production.
- **The receipt under one branch:** every branch the Record press leaves (started, refused, network failure) shows its own true state.
- **Fences that name old words:** fences asserting `SUMMARY ON`, `RECORDING` after a refusal, or a raw error string change in the same commit.

## Effort (not a promise)

Grounding size: Record `res.ok` is part of move 5 (M) (`grounding/faces-jobs.md:156`). PROVISIONAL.

## Notes

- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
