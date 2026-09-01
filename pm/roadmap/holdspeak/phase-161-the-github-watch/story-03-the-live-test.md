# HS-161-03 - The live test: current PRs, an honest baseline, and the first real evaluation

- **Project:** holdspeak
- **Phase:** 161
- **Status:** done
- **Depends on:** HS-161-02
- **Unblocks:** HS-161-04
- **Owner:** unassigned

## Problem

§8.1's test contract: the live test shows provider/connection, repo,
normalized query, entity count, up to five representative PRs,
present matched conditions, observation time, duration, and typed
error/partial state. ACT-002's zero-match honesty. Then baseline
(no false history — ACT-005) and MANUAL evaluation producing
watch.transition observations into the 160 Delta — the arc's
compounding proof.

## Scope

- **In:** WatchService.test_watch grows the github path: the 01
  adapter's snapshot (bounded, non-mutating, admitted+receipted)
  → the §8.1 display payload persisted in test_result_json;
  baseline_watch works unchanged (snapshot cached, zero events);
  NEW `evaluate_once(watch_id)` on WatchService (MANUAL only — P5
  owns scheduling): snapshot → diff_snapshots vs the baseline →
  semantic transitions → a `watch_evaluations` row (the 159 tables
  earn their first rows) → transitions become watch.transition
  observations via the 160 collector seam (the project binding's
  source) → advance the baseline. Idempotent: the same source
  revision evaluates once (the UNIQUE(watch_id, revision,
  source_revision) law); repeated identical snapshots produce zero
  new observations (WAT-006's spirit at the read level).
- **Out:** any effect/action execution (P5/V0-E), scheduling, UI.

## Acceptance criteria

- [ ] The github test payload carries every §8.1 field; zero matches with a successful read = PASS with the honest label; failures typed (PROV-009).
- [ ] Baseline emits zero events (the ledger assertion).
- [ ] evaluate_once: a changed PR snapshot yields transitions → watch_evaluations row → observations visible in the NEXT open_review as evidence-linked Delta (an integration test runs the full compounding path with a fake runner); identical re-evaluation = no-op (the uniqueness law proven).
- [ ] Every snapshot read receipted (the 01 kernel discipline).

## Test plan

- **Unit:** github test/baseline payloads (fake runner); evaluate_once truth table.
- **Integration:** the compounding path: watch → evaluate → observation → Delta proposal.

## Notes / open questions

- diff_snapshots already speaks GitHub PR semantics (review/checks/head/state/merge) — reuse; do not re-derive transition kinds.
