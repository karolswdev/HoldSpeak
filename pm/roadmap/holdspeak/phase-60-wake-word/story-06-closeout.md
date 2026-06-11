# HS-60-06 — Closeout: real-metal loop + final-summary + PR

- **Project:** holdspeak
- **Phase:** 60
- **Status:** backlog
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
- [ ] The live-loop transcript + screenshots committed.
- [ ] Full suite green; build clean; 0 `_built/` tracked.
- [ ] `final-summary.md` + this story's evidence in the same commit.
- [ ] README + BACKLOG updated in the same commit; PR merged on green.

## Test plan
- The live loop + the full suite; CI green on the PR.
