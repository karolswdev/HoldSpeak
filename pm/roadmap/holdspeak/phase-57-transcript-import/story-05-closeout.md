# HS-57-05 — Closeout: real-VTT dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 57
- **Status:** backlog
- **Depends on:** HS-57-01..04
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
The phase's claims (real timestamps, real speakers, intel parity, the audio
path untouched) are behavioral — only a live runtime proves them.

## Scope
- **In:**
  - **Dogfood (live server):** a realistic multi-speaker VTT uploaded
    through the real API → the meeting at /history with the file's speaker
    names and cue timestamps → **real intel on the `.43` endpoint** →
    the speaker facet filters by a transcript-carried name → a WAV imported
    in the same run proves the recording path untouched. Screenshots.
  - Full suite green; build clean; 0 `_built/` tracked.
  - `final-summary.md`; phase CLOSED here + project README + index row;
    BACKLOG **P** flipped to shipped.
  - Push, PR to `main`, merge on green CI.
- **Out:** new feature work (findings go back to their story first).

## Acceptance criteria
- [ ] Dogfood transcript + screenshots committed (VTT speakers/timestamps,
      real intel ready on `.43`, the facet pass, the audio-path pass).
- [ ] Full suite green; build clean; 0 `_built/` tracked.
- [ ] `final-summary.md` + this story's evidence in the same commit.
- [ ] README + BACKLOG updated in the same commit.
- [ ] PR to `main` merged on green CI.

## Test plan
- The dogfood + the full suite; CI green on the PR.
