# HS-159-07 - The close: gates, suite amendments, final summary

- **Project:** holdspeak
- **Phase:** 159
- **Status:** done
- **Depends on:** HS-159-01, HS-159-02, HS-159-03, HS-159-04, HS-159-05, HS-159-06
- **Unblocks:** Phase P2 (The Delta)
- **Owner:** unassigned

## Problem

The interview claims the front door of the product. The close proves
it: full gates, the sweep, counsel, the suite amended with every
discovery, the owner's verdict already recorded on 05, and the P2
backlog carried forward (incl. 158's S-1/N-1/N-3 if P2 charters
next).

## Scope

- **In:** full suite isolated HOME `-n auto` (metal excluded);
  name-diff vs main's latest run — zero true branch-new (candidates
  proven at root cause, the 157/158 precedent); web check + baseline;
  counsel close (M in-round; S documented-or-fixed); suite
  amendments; restore suite-churned PNGs before staging; roadmap
  cadence; `final-summary.md`; PR gated on conclusion JSON in its
  own step + name-diff; merge AFTER the owner's 05 verdict.
- **Out:** P2 work.

## Acceptance criteria

- [ ] Full suite run and READ; sweep zero true branch-new.
- [ ] Web check green; baseline zero branch-new (churn-flakes proven if any).
- [ ] Counsel: zero open must-fix.
- [ ] Suite amendments committed (or none-arose note).
- [ ] final-summary.md; COMPLETE 7/7; README true; PR merged via merge commit.

## Test plan

- **Everything:** this story IS the gate run.

## Gate record (running)

- **Web baseline (FINAL tree, post-shell + counsel fixes):**
  1984 passed / 0 failed — baseline-subset, zero branch-new.
  Web check green on the same tree (guard passed, bundle gate
  passed) — both fence catches resolved the library way.
- **Web check: THE FENCE CAUGHT THE ROUND-4 DEVIATION** —
  `library-css-outside` on SuggestionCards.tsx + setup.css (library
  ChoiceCard classes applied feature-side). The machine judged what
  counsel was asked to judge. RULING (the 158 TitleSlotContext
  precedent): the library grows `ChoiceCardShell` — the material as
  a composable presentational export with no interaction model;
  ChoiceCard itself refactors onto it (one source of material);
  SuggestionCards consumes via the barrel. LANDED (8439b080):
  ChoiceCardShell in the library with its 14-test contract +
  contract.md entry; ChoiceCard composes it (one source of
  material); the orchestrator's own document.querySelector scroll
  fix ALSO tripped the guard and became a ref. Check green, fence
  baseline unchanged, rules unweakened. Cards pixel-equivalent to
  the owner's PASSED round 4 (verified by eye + both glass suites).
- **Counsel in-round fixes LANDED (59fb7673):** M-1 fence sealed via
  conn-accepting automations helpers (SANCTIONED_WRITERS unchanged,
  atomicity fault-proven still green); S-1 session completion inside
  the transaction + the honest-replay belt; S-2 evidence stub
  pinned. 192 scoped green.

## Counsel close (HS-159)

**VERDICT: RATIFY-W-C — one M, two S, four N.** In-round work:

- **M-1:** the phase's OWN fence caught its own finalize —
  `create_from_setup` raw-INSERTs `connector_watches`
  (project_service.py:564; watch_rules at :593 same door, uncovered).
  Introduced one story after the fence; invisible to 03's scoped set;
  the full suite catches it exactly as designed. FIX IN FLIGHT:
  counsel option (b) — conn-accepting automations helpers; the
  fence rule stays full-strength; atomicity untouched.
- **S-1:** session completion sat OUTSIDE the finalize transaction —
  a crash between = duplicate-Project hazard. FIX IN FLIGHT: the
  completion joins the conn + a belt check (existing project_id →
  honest replay).
- **S-2:** the evidence stub untested → one pin lands.
- **N-1:** the ChoiceCard classes-not-component deviation judged
  LAWFUL REUSE (multi-select vs radiogroup, documented) — and the
  fence flagged the material anyway; the ChoiceCardShell library
  extraction (in flight) is counsel's own named right-fix.
- N-2 seeding gaps honest; N-3 fixtures match the wire (spot-checked);
  N-4 no injection surface (the closed schema IS the refusal).
- Axis A: resume is GENUINE server-side rehydration, no cache theater.

## What shipped

- Authoritative full suite (post-fixes): 15F/8187P in 22:10; sweep
  vs main's 27 names → 5 candidates: hs151 glass, kernel real-hub,
  device-recording tick, node-link two-process ALL isolated green on
  untouched files (churn); test_api_surface REAL — the manifest
  lacked the face as consumer of /api/project-setups (api.ts landed
  after 04's regen) — regenerated, isolated green. Zero unexplained
  branch-new.
- Web finals: check green (guard + bundle), baseline 1984/0
  baseline-subset zero branch-new.
- Counsel fixes landed (59fb7673), shell landed (8439b080),
  final-summary.md written; phase COMPLETE 7/7. Suite-amendment
  duty: no P1a discovery invalidated a suite claim; the P2 walls
  (seeding routes, evidence read path, name override) recorded in
  the final summary.

## Notes / open questions

- P2 "The Delta" charters after the merge, anchors re-verified — the standing rule. P2 inherits the 158 backlog (S-1, N-1, N-3).
