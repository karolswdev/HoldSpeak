# HS-67-06 — Closeout: a recorded run

- **Project:** holdspeak
- **Phase:** 67
- **Status:** backlog
- **Depends on:** HS-67-01, HS-67-02, HS-67-03, HS-67-04, HS-67-05

- **Owner:** unassigned

## Problem

A protocol that has never been run proves nothing. The phase closes only when the
harness has actually been driven end to end and the result recorded, with any
findings filed as follow-on work.

## Scope

- **In:** one full pass of `dogfood/PROTOCOL.md` on real metal (`.43` + a Mac
  mic), a filled `dogfood/results/<date>.md`, a findings list (bugs/papercuts
  filed as new issues or a follow-on phase), and `final-summary.md`.
- **Out:** fixing the bugs the run finds (that's the follow-on work this run
  scopes).

## Acceptance criteria

- [ ] A dated, filled run exists under `dogfood/results/` covering both tiers
      (or Tier 1 + as much of Tier 2 as `.43`/mic allow, with skips noted).
- [ ] Every FAIL/PARTIAL is in the findings table with a repro; material ones are
      filed (issue or BACKLOG row).
- [ ] `final-summary.md` records what shipped, the run verdict, and what the next
      phase should pick up.
- [ ] Roadmap README + this status flipped to CLOSED in the closing commit.

      See `evidence-story-06.md`.

## Test plan

- Manual: the run *is* the test. Capture command output / screenshots into the
  results file.
- Unit: re-confirm the plumbing pytest green at closeout.

## Notes / open questions

- If `.43` or a mic is unavailable, record the Tier-2 skips honestly rather than
  faking a pass — a partial-but-honest run still closes the phase if Tier 1 is
  complete and the Tier-2 gaps are named.
