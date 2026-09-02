# HS-160-03 - The frozen review: twelve steps, versioned materiality, golden truth

- **Project:** holdspeak
- **Phase:** 160
- **Status:** done
- **Depends on:** HS-160-02
- **Unblocks:** HS-160-04
- **Owner:** unassigned

## Problem

§7.2 IS the algorithm — twelve numbered steps from acquiring the
revision + last accepted cursor through freezing the manifest,
classifying changes (added/changed/closed/overdue/blocked/
contradicted/coverage-degraded), conflict retention without silent
winners, deterministic proposals, versioned materiality, stable
ordering, and the stored window. DEL-001 kills the
latest-two-meetings shortcut; SYS-024 demands idempotent re-runs;
DEL-007 keeps the deterministic path model-free.

## Scope

- **In:** `ProjectDeltaService.open_review(project_id)` implementing
  §7.2's steps 1-10 + 12 (step 11's model seam exists as a no-op
  hook — the model stays out of P2); prev_ review rows via 01;
  pprop_ deterministic proposals (kind/target/patch per §5.7);
  the materiality formula VERSIONED (a named constant + factors per
  §7.2: outcome relevance, severity, overdue/blocked, decision
  impact, novelty, confidence) and testable in isolation; ordering
  by materiality/time/kind/id; conflicts become their own proposal
  kind carrying both sources (DOM-005 distinguishability
  throughout: observed fact vs assessment vs proposal — SYS-022).
- **Out:** decisions (04), routes (05), any model call.

## Acceptance criteria

- [ ] GOLDEN TESTS (TST-004): a seeded desk's review window reproduces byte-identically across runs (SYS-024); ordering stable; conflicts retained with both sources; the window re-opened from storage matches.
- [ ] DEL-001: the window derives from the last ACCEPTED cursor + frozen manifest (a test proves meetings beyond the cursor enter and pre-cursor material stays out).
- [ ] SYS-025/DOM-008: a failed/stale source appears as degraded coverage IN the manifest and the review — never silent "no change".
- [ ] Materiality is versioned: the formula constant appears in the review row; changing factors requires the version bump (a pin).
- [ ] Every proposal states kind/change/observed time/source refs/provenance class (SYS-022).

## Test plan

- **Unit:** `tests/unit/test_frozen_review.py` (golden windows, cursor law, degraded leg, materiality unit tests, conflict retention).

## What shipped

- `ProjectDeltaService.open_review` — §7.2's twelve steps mapped
  one-to-one (the report's table is the record); step 11 ships as
  a proven identity hook (P4's seam, may add, never rewrite).
- CLOSED proposal-rule table (4 rules): followthrough.overdue/stale →
  risk_attention (assessment), decision.review_due → review_flag
  (assessment), watch.transition → observation_attention
  (observed_fact); informational kinds propose nothing.
- MATERIALITY_VERSION=v1: six weighted factors, each unit-tested;
  the version pin locks the string AND a canonical example at 0.795 —
  a factor change without a version bump fails the pin.
- ONE-OPEN-REVIEW RULED: an existing open window returns
  byte-identically; accept clears the way (SYS-020's cursor spirit).
- Golden windows: run-twice identical, re-read identical, ordering
  stable; cursor law proven both directions; degraded coverage
  visible in manifest AND proposals; conflicts carry both sources,
  no winner. 45 new tests; 149 scoped green.

## Notes / open questions

- Keep step 11's hook honest: a named extension point that P2 ships as identity — documented so P4's model never rewrites deterministic entries (§7.2's own rule).
