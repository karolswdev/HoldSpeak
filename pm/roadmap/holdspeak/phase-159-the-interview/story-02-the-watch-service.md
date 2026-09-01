# HS-159-02 - The watch service: one façade, no second lifecycle

- **Project:** holdspeak
- **Phase:** 159
- **Status:** done
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

## What shipped

- `holdspeak/services/watch_service.py` — the façade: list/get (full
  spec + rules), update (material fields → revision+1 + test/baseline
  staled; name/intent don't — ACT-008 exact), pause/resume/retire
  (ACT-009: history retained), `test_watch` (bounded non-mutating
  read via the existing snapshot seam; zero-match = PASSED —
  ACT-002; persists test_state/result), `baseline_watch` (snapshot +
  baseline_state, ZERO events — ACT-005 proven by ledger count),
  `set_rules` (replace-by-ordinal under the uniqueness).
- `holdspeak/watch_validation.py` — pure, package-root (the
  refs.py convention): closed WatchCondition@1 tree (recursive;
  unknown operators/comparisons/keys refused) + closed WatchAction@1
  kinds; P4/P5/P6 will import, not re-declare.
- NO-THIRD-DOOR fence: source-scan over holdspeak/ — raw
  connector_watches writes only in automations.py + watch_service.py;
  three sub-tests incl. anti-stale-entry.
- ReactionService: ALL seven watch methods stay as-is — partial
  absorption per §2, per-method reasoning recorded (different
  contracts/columns; delegation would risk the 31 pins). Wired into
  web context/server construction; routes come in 04.
- 83 + 3 new tests; scoped set 150 passed, 1 skipped (the real-DB
  CI-skip), captured.

## Notes / open questions

- Keep the façade thin over the graduated table — the P5 evaluator and P2a adapters bolt onto THIS contract; don't pre-build their seams beyond what §10/§11 name.
- WatchService has NO create by design (create stays legacy + finalize-time): story 03's atomic finalize creates/activates specs INSIDE its one transaction — via repo helpers or an internal conn-taking seam; 03 decides with the transaction constraint stated.
