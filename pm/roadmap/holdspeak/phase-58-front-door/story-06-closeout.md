# HS-58-06 — Closeout: fresh-eyes pass + final-summary + PR

- **Project:** holdspeak
- **Phase:** 58
- **Status:** backlog
- **Depends on:** HS-58-01..05
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
A docs phase ships words; only a fresh-eyes read of the rendered result
proves them.

## Scope
- **In:** a rendered review of README (push preview on the PR), link
  spot-check (absolute URLs; the lock covers relative), before/after
  metrics (per-file dash counts to zero, corpus size, AI-vocab zero),
  full suite green, `final-summary.md`, BACKLOG row flipped, project
  README CLOSED + index row, PR to `main` merged on green CI.
- **Out:** new revision work (findings go back to their story).

## Acceptance criteria
- [ ] Before/after metrics in evidence; rendered README reviewed.
- [ ] Full suite green; doc slice green.
- [ ] `final-summary.md` + this story's evidence in the same commit.
- [ ] README + BACKLOG updated in the same commit; PR merged on green.

## Test plan
- The full doc slice + full suite; CI green on the PR.
