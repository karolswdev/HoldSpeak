# HS-157-05 - The close: gates, suite updates, final summary

- **Project:** holdspeak
- **Phase:** 157
- **Status:** done
- **Depends on:** HS-157-01, HS-157-02, HS-157-03, HS-157-04
- **Unblocks:** Phase P1 (The Room)
- **Owner:** unassigned

## Problem

A P0 that ships without the full gates is a P0 that protected
nothing. The close proves the freeze: the whole suite runs the way CI
sees it, the name-diff against main is clean, the web baseline holds,
counsel reviews the phase, and any discovery made during P0 is
reflected back into the SRS suite (the suite's own precedence rule:
a discovery that invalidates a requirement updates the suite BEFORE
or WITH the code).

## Scope

- **In:** full suite under isolated HOME with `-n auto` (scratch
  script; metal excluded per standing law); name-diff vs main's
  latest run — zero branch-new or root-cause fixes;
  `npm --prefix web run check` + web baseline; counsel close
  (M-findings fixed in-round); the docs duty: SRS suite amendments
  from P0 discoveries land in `docs/internal/project-rooms/`,
  roadmap README "Current phase" line + this phase's status kept
  true; `final-summary.md`; PR to main gated on conclusion JSON
  read in its own step, then a merge commit.
- **Out:** starting P1 work in this phase's PR.

## Acceptance criteria

- [ ] Full pytest suite (isolated HOME, `-n auto`, metal excluded) run and READ; name-diff vs main zero branch-new (or every branch-new fixed at root cause and re-run).
- [ ] `npm --prefix web run check` green; web baseline zero branch-new.
- [ ] Counsel close: zero open must-fix; M-findings fixed in-round.
- [ ] Every P0 discovery that touched a suite claim has a matching suite amendment committed (or an explicit note that none arose).
- [ ] `final-summary.md` written; phase status COMPLETE 5/5; README "Current phase" line true; PR merged to main via merge commit after conclusion JSON read PASS.

## Test plan

- **Everything:** the phase's own exit criteria — this story IS the gate run.

## What shipped

- Full suite CI-style: `12 failed, 7766 passed, 53 skipped in 20:43`
  under isolated HOME + `-n auto`. Name-diff vs main's CI baseline
  (26 names): 2 candidates, BOTH proven load-flakes with isolated
  green re-runs (the branch changes zero runtime code, so neither can
  be a branch defect): `test_one_shot_disables_after_cancelled`
  (sleep-race, 1 passed in 0.78s isolated) and glass `error-1440`
  (contention, 1 passed in 4.12s isolated). Zero true branch-new.
- Web gates: `npm --prefix web run check` exit 0 (bundle gate passed);
  baseline verdict `baseline-subset, zero branch-new` (1791 passed).
- Counsel close: **RATIFY, zero M, zero S** — all five axes clean.
  N-1 applied in-round (`project_contracts.py` joined the fence list;
  167 re-green). N-2 (SRS §3.2 Note/artifact row split) recorded for
  the next suite amendment.
- Suite-amendment duty: no P0 discovery invalidated a suite claim
  (counsel confirmed CONTRACTS-P0.md contradicts nothing); N-2 is
  cosmetic and recorded, not amended.
- `final-summary.md` written; phase COMPLETE 5/5.

## Notes / open questions

- The next phase (P1 "The Room") charters only after this one merges; its anchors must be re-verified against the new main at that time (the handover's own rule).
- The merge rides the PR: conclusion JSON read in its own step, name-diff vs the PR's own CI run, then a merge commit.
