# HS-159-02 - The watch service: one façade, no second lifecycle

- **Project:** holdspeak
- **Phase:** 159
- **Status:** backlog
- **Depends on:** HS-159-01
- **Unblocks:** HS-159-03
- **Owner:** unassigned

## Problem

§2's ruling: a transport-neutral `WatchService` becomes the universal
application façade over the graduated `connector_watches`;
`ReactionService` delegates or is incrementally absorbed behind
compatibility tests. No competing Project-only Watch root; no second
lifecycle (AD-PRJ-010).

## Scope

- **In:** `holdspeak/services/watch_service.py`: spec CRUD/read
  (`list/get/update/pause/retire`), `test` (bounded non-mutating read
  through the EXISTING native/snapshot paths — external providers out
  of scope; test shows current entities, persists test_state/
  test_result_json — ACT-002 semantics incl. `Test passed · 0
  current matches`), `baseline` (sets snapshot without emitting
  historical transitions — ACT-005), revision increments on material
  edits (ACT-008: material edits stale test/baseline), rules CRUD
  into `watch_rules` (WatchCondition@1/WatchAction@1 shapes VALIDATED
  as closed declarative trees — §7.2/7.3; no code, no prompts in
  conditions). ReactionService's watch-touching operations delegate
  to (or wrap) the façade — its public behavior pinned unchanged.
  Results follow the project_contracts envelope discipline where
  shapes are new.
- **Out:** evaluation/effects execution (P5), provider adapters
  (P2a), MCP exposure (P6), scheduling.

## Acceptance criteria

- [ ] Every connector_watches write path in the codebase flows through WatchService (or a pinned ReactionService delegate) — a fence/inventory test proves no third door.
- [ ] WatchCondition@1 validation: closed operators/comparisons only; Python/shell/SQL/prompt strings refused as typed validation errors.
- [ ] Material edit → revision+1 + test_state/baseline_state staled; non-material edit (name/intent) does not stale (ACT-008).
- [ ] Baseline never emits historical events (ACT-005 — proven by the event-ledger assertion).
- [ ] Legacy pins from 01 stay green; retire stops future evaluation while retaining history (ACT-009 shape).

## Test plan

- **Unit:** `tests/unit/test_watch_service.py` (lifecycle, revisions, staling, condition validation, baseline honesty); the no-third-door fence; ReactionService pins re-run.

## Notes / open questions

- Keep the façade thin over the graduated table — the P5 evaluator and P2a adapters bolt onto THIS contract; don't pre-build their seams beyond what §10/§11 name.
