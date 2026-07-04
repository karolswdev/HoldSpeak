# Evidence — HSM-23-04 — Sync integrity: the round-trip matrix + the contract pin

**Status:** done (2026-07-04), on `holdspeak-mobile/hsm-23-04-sync-integrity`.

## 1. The last two matrix rows (chain + workflow)

`tests/unit/test_web_routes_sync_primitives.py` gains the same lock every other kind
already carried:

- `test_chain_and_workflow_push_pull_round_trip_and_tombstone` — push both kinds,
  assert the live-store merge (ordered `steps`; the workflow's `graph_json` — the
  Phase-22 travelling graph, with `runs_on`/`failure_policy` nodes — survives
  byte-faithful), pull them back with exact `meta`, then tombstone (with `value: null`,
  the §12 rule) and assert the hidden store + the payload-less tombstone riding the
  next pull.
- `test_chain_and_workflow_push_last_write_wins` — an older incoming push is skipped
  for both kinds (`received == 0`, stored copies untouched).

All 10 sync kinds now carry a per-primitive push→pull + LWW + tombstone lock — the
audit critic's matrix, landed as tests, not a chart.

## 2. §11 brought current (`SERIALIZATION-CONTRACT.md`)

§11 described a dead wire (`change_set: {meetings, artifacts}`, two-value `kind` enum,
the envelope schema in the future tense). Rewritten to the shipping truth: the ten
buckets, the matching kind enum, the membership id rule, tombstone ⇒ `value: null`,
pointers to `schemas/changeset.schema.json` and the per-primitive locks, history noted
(HSM-10-01 shipped two buckets; Phases 72–77 grew it; this story back-updated the doc).

## 3. The stale "lossy manual_context" finding corrected — and pinned cross-language

Phase 77 (db v7) fixed the HS-72-01 loss; three places still recorded it as live:

- **§12 locked-findings note** → now records the fix (persist + merge + re-emit,
  round-trip locked in `tests/unit/test_agent_pinned_context.py`).
- **`agent.schema.json`** → the "KNOWN LOSSY FIELDS" description and both per-field
  "NOT persisted by the hub (lossy)" notes replaced with the Phase-77 truth.
- **The golden fixture predated the fields entirely** — the cross-language pin never
  covered them. `fixtures/primitives-sample.json`'s agent record now carries
  `manual_context` + `use_zone_context` (the hub's real `to_dict` emission), and
  `PrimitiveContractFixtureTests.testGoldenFixtureDecodesEveryKind` asserts the values
  REACH `Agent.manualContext`/`useZoneContext` (not just decode tolerantly).

## Suites (all read, 2026-07-04)

- `uv run pytest -q tests/unit/test_web_routes_sync_primitives.py
  tests/unit/test_primitive_contract.py tests/unit/test_web_routes_sync.py
  tests/integration/test_primitive_framework_sync.py
  tests/unit/test_agent_pinned_context.py` — **39 passed** (was 37; +2 matrix rows).
- `uv run python pm/roadmap/holdspeak-mobile/contracts/validate.py` —
  **ALL CHECKS PASSED** (fixture still canonical after the agent enrichment).
- `swift test` (full package) — **432 tests, 8 skipped, 0 failures** (the new
  pinned-context assertion green).
- `uv run pytest -q tests/unit/test_doc_drift_guard.py` — **18 passed**.

## Honest boundaries

- Meetings still emit `started_at` as `last_modified` on pull (a transport-grade
  stamp, documented in `sync.py`); conflict-grade `updated_at` stays out of scope, as
  the story declared.
- The Wave-1 live-merge and the HS-72-01 tri-guard are pre-paid foundations this story
  finished, not work it claims.
