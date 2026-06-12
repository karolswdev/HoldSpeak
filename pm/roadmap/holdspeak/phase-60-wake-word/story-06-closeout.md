# HS-60-06 — Closeout: real-metal loop + final-summary + PR

- **Project:** holdspeak
- **Phase:** 60
- **Status:** done
- **Depends on:** HS-60-01..05
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
The phase claims a hands-free loop that is safe by default; only the
live loop proves it.

## Scope
- **In:** real metal on this Mac: `say` the wake phrase → the real
  listener detects → the armed broadcast observed → a spoken sentence →
  `wake_preview` carrying the real Whisper transcript through the real
  pipeline → Type it via the one-shot route; `action="type"` proven as
  the explicit opt-in; defaults byte-identical (disabled → no listener
  thread, no stream, no broadcasts). Full suite; build clean;
  `final-summary.md`; BACKLOG **O** flipped; README CLOSED + index row;
  PR to `main` merged on green CI.
- **Out:** new feature work (findings go back to their story).

## Acceptance criteria
- [x] The live-loop transcript + screenshot committed (7/7, zero page
      errors; real detection → armed → real Whisper verbatim → the
      preview default held → Type it through the real route → the
      token burned → the type opt-in proven; defaults off). Two REAL
      production bugs found and fixed along the way (GGML's lldb
      auto-attach suspension; the process-fatal cross-thread MLX call
      — see `evidence-story-06.md`).
- [x] Full suite green (2723 passed, 17 skipped); build clean; 0
      `_built/` tracked.
- [x] `final-summary.md` + this story's evidence in the same commit.
- [x] README + BACKLOG (O shipped) updated in the same commit; PR
      merged on green.

## Test plan
- The live loop + the full suite; CI green on the PR.
