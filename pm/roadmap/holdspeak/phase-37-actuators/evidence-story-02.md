# Evidence — HS-37-02: Proposal persistence + lifecycle

**Date:** 2026-06-04. **Branch:** `phase-37/hs-37-01-actuator-contract`.

## What shipped

A durable home for actuator proposals — the lifecycle, idempotency, and audit trail that
make "no silent egress" provable after the fact.

### Files

- **Schema (`holdspeak/db/core.py` `SCHEMA_SQL`)** — two tables:
  - `actuator_proposals` — the proposal row: `meeting_id` (FK → meetings, ON DELETE
    CASCADE), `window_id`, `plugin_id`/`plugin_version`, `idempotency_key` (UNIQUE),
    `status` (default `proposed`), `target`/`action`/`preview`/`payload_json`/`reversible`/
    `required_capabilities_json`, `decided_by`/`result_json`/`error`, and
    `created_at`/`decided_at`/`executed_at`/`updated_at`.
  - `actuator_proposal_audit` — one row per transition: `proposal_id` (FK → proposals,
    CASCADE), `actor`, `from_status`, `to_status`, `detail`, `created_at`.
  - 3 indexes (by meeting, by status, by proposal for the audit trail).
- **`holdspeak/db/actuators.py` (new)** — `ActuatorRepository`: `record_proposal`
  (idempotent insert + opening audit), `get_proposal`, `list_proposals(meeting_id,
  status=)`, `transition_proposal` (lifecycle-enforced + audited), `list_audit`. The
  lifecycle is an explicit `_LEGAL_TRANSITIONS` map — `proposed → {approved, rejected}`,
  `approved → {executed, failed}`, `failed → {approved}` (retry), `executed`/`rejected`
  terminal.
- **`holdspeak/db/models.py`** — `ActuatorProposalRecord` + `ActuatorProposalAuditEntry`
  dataclasses + `VALID_ACTUATOR_PROPOSAL_STATUSES`.
- **`holdspeak/db/core.py` + `__init__.py`** — the repo joins the `Database` container
  (`db.actuators`) and is re-exported.
- **`holdspeak/plugins/persistence.py`** — `record_actuator_proposal(db, run)`: persists
  the proposal carried by a `proposed` `PluginRun` (the HS-37-01 output).
- **`holdspeak/plugins/pipeline.py`** — in the persistence loop, a `proposed` run also
  persists its proposal (dormant until an actuator is dispatched, HS-37-05).
- **`holdspeak/plugins/contracts.py`** — `proposed` added to `PLUGIN_RUN_STATUSES` (the
  `PluginRun` contract) in lockstep, so dispatch's `_to_plugin_run` accepts an actuator's
  proposed result.
- **`tests/fixtures/db_schema_canonical.txt`** — regenerated (the fresh-build snapshot).

## Verification

### Repository + lifecycle + schema snapshot

```
$ uv run pytest -q tests/unit/test_actuator_repository.py \
    tests/unit/test_intent_contracts.py tests/unit/test_db.py::TestDatabaseShape
21 passed
```

`test_actuator_repository.py` (new, 13 cases) covers:
- **Round-trip** — all fields persist + reload (`get_proposal == record_proposal`),
  `list_proposals` by meeting + by status; the opening `→ proposed` audit entry.
- **Idempotency** — re-`record_proposal` with the same key returns the same row, no
  duplicate, no extra audit entry.
- **Lifecycle** — `proposed → approved → executed` (with `decided_by` preserved through
  execution + the full audit chain); `rejected` terminal; `failed → approved → executed`
  retry; illegal transitions (`proposed → executed`, `proposed → failed`, `executed →
  proposed`) + unknown status / unknown proposal raise.
- **Persistence adapter** — a `proposed` `PluginRun` → a durable proposal via
  `record_actuator_proposal`.

The canonical schema snapshot regenerated in this commit (422 objects; +2 tables, +3
indexes) and `test_fresh_schema_matches_canonical_snapshot` passes.

### Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2052 passed, 15 skipped in 56.73s        # +12 vs HS-37-01 (the new repo tests)
$ uv run ruff check holdspeak/db/ holdspeak/plugins/persistence.py \
    holdspeak/plugins/pipeline.py holdspeak/plugins/contracts.py
All checks passed!
```

## Notes

- The proposal `payload` is stored verbatim (`payload_json`) — the parity source-of-truth
  the guarded executor (HS-37-04) compares against the previewed payload before acting.
- The pipeline hook is **dormant by default**: no actuator is registered/dispatched until
  HS-37-05, so the default path persists zero proposals (and the routing/synthesis tests
  are unaffected).
- Decision taken (was deferred): the audit log is a **dedicated table** tied to the
  proposal row (not the activity ledger) — clean lifecycle surface, CASCADE-scoped.
