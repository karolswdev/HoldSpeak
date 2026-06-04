# Evidence — HS-38-06: Closeout + final-summary

**Date:** 2026-06-04. **Branch:** `phase-38/hs-38-01-write-connector-framework`.

## What shipped

The Phase-38 closeout — proving the safety invariant **still** holds now that actuators reach
real systems and approve live, capturing the demo, and writing the record.

- **`final-summary.md`** — leads with the **extended egress-posture review**: no write path
  reaches an external system without (1) a registered, capability-enabled actuator, (2) a
  persisted `approved` proposal, (3) the `allow_actuators` + allow-list governance gate, (4)
  payload parity, (5) **the connector's permission manifest + `PermissionGate`** (new this
  phase — refuses before egress), and (6) an audit row. The negatives are cited from the
  tests + the demo. Then the what-shipped table, state-at-close, decisions of record, and the
  next-frontier handoff (mirrors Phases 36/37).
- **Demos (reproducible, committed):**
  - `evidence/actuator_write_loop.md` (via `evidence/demo_write_loop.py`) — the GitHub
    write-connector loop end to end with an **injected `gh` runner**: propose → (execute
    before approval → refused, no egress) → (a `gh repo delete` op → `ConnectorOperationRefused`
    before the gate, runner never called) → approve → execute → `executed` + the issue URL →
    the audit trail `proposed → approved → executed`. **Exactly one** `gh` call — the executed
    issue.
  - `evidence/live_pending_actions.png` (via `evidence/capture_live_panel.py`) — the live
    "Pending actions" dashboard panel, seeded with the **read-only** descriptors the
    `actuator_proposed` broadcast carries (a GitHub + a webhook proposal), rendered from the
    built bundle with Playwright (no backend). Signal-styled: lifecycle accent edge, typed
    "Awaiting approval" status chip, target icon, reversibility, the preview line, and
    Approve / Reject + the "nothing runs without your approval" guard.

## Verification

```
$ uv run python3 pm/roadmap/holdspeak/phase-38-actuators-ii/evidence/demo_write_loop.py
wrote .../actuator_write_loop.md        # 1 gh call (the executed issue); negatives = 0 egress

$ cd web && npm run build               # bundle gitignored
8 page(s) built
$ uv run python3 pm/roadmap/holdspeak/phase-38-actuators-ii/evidence/capture_live_panel.py
wrote .../live_pending_actions.png

# Routing invariants — actuators still off + unregistered by default (byte-identical)
$ uv run pytest -q -k "intent_router or intent_dispatch or intent_pipeline or multi_intent_routing" tests/unit/
38 passed, 1704 deselected

# The Phase-38 actuator stack (framework + 2 connectors + live + Phase-37 executor/reference/contract/repo)
$ uv run pytest -q tests/unit/test_gated_connector.py tests/unit/test_github_issue_actuator.py \
    tests/unit/test_webhook_post_actuator.py tests/unit/test_live_proposals.py \
    tests/unit/test_actuator_executor.py tests/unit/test_actuator_reference.py \
    tests/unit/test_actuator_contract.py tests/unit/test_actuator_repository.py
91 passed

# Doc-guards + full suite
$ uv run pytest -q tests/unit/test_doc_drift_guard.py -k "drift or link or dangling"
3 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2123 passed, 15 skipped in 58.76s

# The build product is never committed
$ git ls-files holdspeak/static/_built | wc -l
0
```

- **No real outbound call in CI** — every connector/loop test injects the runner / HTTP
  client; the demo runner is a fake `gh`; the live-panel capture serves static files (no
  backend, no network egress).
- **Cadence:** project README phase row → `done` + Current-phase + Last-updated;
  `HANDOVER.md` refreshed (Phase 38 closed; next-frontier teed up).

## Notes

- The `_built` bundle is rebuilt to verify and stays gitignored (0 tracked); only `web/src/**`
  source is committed.
- This phase is the local branch `phase-38/hs-38-01-write-connector-framework` (scaffold + 6
  story commits) — push + open a PR to `main` per the merge-phases cadence.
