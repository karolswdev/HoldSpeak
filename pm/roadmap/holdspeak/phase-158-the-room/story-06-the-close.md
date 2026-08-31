# HS-158-06 - The close: gates, suite amendments, final summary

- **Project:** holdspeak
- **Phase:** 158
- **Status:** backlog
- **Depends on:** HS-158-01, HS-158-02, HS-158-03, HS-158-04, HS-158-05
- **Unblocks:** Phase P1a (The Interview)
- **Owner:** unassigned

## Problem

P1 claims the aggregate. The close proves it: full suite CI-style,
name-diff zero branch-new, web gates, counsel, the SRS suite amended
with every P1 discovery (the precedence rule), and the owner's shot
verdict already recorded on 05 before the PR merges.

## Scope

- **In:** full suite isolated HOME `-n auto` (metal excluded);
  name-diff vs main's latest run — zero true branch-new or root-cause
  fixes (load-flakes proven by isolated greens, per the 157
  precedent); `npm --prefix web run check` + baseline; counsel close
  (M in-round); suite amendments (incl. the room-section vocabulary
  in CONTRACTS-P0.md and counsel-157's N-2 Note/artifact row split if
  this phase touches §3.2); restore any suite-regenerated shot PNGs
  in OTHER phases before staging (the 157 scar); roadmap cadence
  files; `final-summary.md`; PR gated on conclusion JSON in its own
  step + name-diff, merged via merge commit AFTER the owner's 05
  verdict.
- **Out:** P1a work.

## Acceptance criteria

- [ ] Full suite run and READ; name-diff zero true branch-new (candidates proven at root cause).
- [ ] Web check green; baseline zero branch-new.
- [ ] Counsel: zero open must-fix; M-findings fixed in-round.
- [ ] Suite amendments committed (or explicit none-arose note); N-2 resolved or explicitly deferred.
- [ ] final-summary.md; phase COMPLETE 6/6; README pointers true; PR merged (conclusion JSON read in its own step; the owner's verdict on 05 recorded first).

## Test plan

- **Everything:** this story IS the gate run.

## Notes / open questions

- P1a charters after this merges, anchors re-verified — the standing rule.
