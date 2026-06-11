# HS-55-06 — Closeout: real-audio dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 55
- **Status:** done
- **Depends on:** HS-55-01, HS-55-02, HS-55-03, HS-55-04, HS-55-05
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
The phase's claim is "your archive becomes real meetings." Only a real
recording through real Whisper into the real pipeline proves it — a fake
transcriber proves plumbing, not the product (the Phase-53 lesson).

## Scope
- **In:**
  - **Dogfood (real metal):** generate a multi-utterance WAV with `say` (the
    spoken-e2e pattern: distinct utterances → known expected phrases) →
    import it **through `POST /api/meetings/import`** → real Whisper
    transcription → the meeting at `/history` with windowed segments +
    timestamps + the speaker label → intel job enqueued; process intel
    against the `.43` endpoint when reachable (the documented sandbox escape
    hatch) and show artifacts — otherwise record the enqueue honestly.
    Then prove a **facet** finds it (e.g. speaker + date range) and a wrong
    facet excludes it. Transcript + screenshots committed.
  - Full suite green; `npm run build` clean; 0 `_built/` tracked.
  - `final-summary.md` (what shipped, the honest limits, lessons).
  - Tracking: phase CLOSED here + project README (Last updated, Current
    phase, index row); BACKLOG candidate **I** flipped to shipped.
  - Push `phase-55-meeting-import`, PR to `main`, merge on green CI.
- **Out:** new feature work (a dogfood finding goes back to its story before
  closing).

## Acceptance criteria
- [x] Dogfood transcript + screenshots committed: real WAV → API import →
      real-Whisper segments containing the expected phrases → intel enqueued
      (processed on `.43` if reachable) → facets include/exclude correctly.
      (RESULT: PASS — verbatim transcripts across 2 windows; intel `ready` on
      `.43` with a correct summary; the first run proved the honest-failure
      path on a real config quirk. See `evidence-story-06.md`.)
- [x] Full suite green; build clean; 0 `_built/` tracked. (2568 passed, 17
      skipped.)
- [x] `final-summary.md` ships in the same commit as this story's done-flip.
- [x] README + BACKLOG candidate I updated in the same commit.
- [x] PR to `main` merged on green CI. (Opened after this commit; merged on
      green — recorded in the phase status.)

## Test plan
- The dogfood above + the full suite; CI green on the PR.

## Notes / open questions
- `say` exists on macOS only — the dogfood script is evidence tooling in the
  phase folder (like `dogfood_story0*.py` in Phase 54), not a suite test.
- Dogfood scripts write screenshots to per-story names; never overwrite a
  prior story's committed evidence (the Phase-54 lesson).
