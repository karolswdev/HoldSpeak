# HS-124-02 — The `pipeline_events` table

- **Project:** holdspeak
- **Phase:** 124
- **Status:** done
- **Depends on:** HS-124-01
- **Unblocks:** HS-124-04
- **Owner:** unassigned

## The thesis (the bar)

The observer needs a durable store. This story adds a single append-only
SQLite table to the schema and bumps the schema version.

### Table definition

```sql
CREATE TABLE IF NOT EXISTS pipeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp REAL NOT NULL,
    service TEXT NOT NULL,
    method TEXT NOT NULL,
    principal_kind TEXT NOT NULL,
    principal_identity TEXT NOT NULL DEFAULT '',
    args_summary TEXT NOT NULL DEFAULT '{}',
    result_summary TEXT NOT NULL DEFAULT '',
    error TEXT,
    error_code TEXT,
    duration_ms REAL NOT NULL DEFAULT 0,
    correlation_id TEXT NOT NULL DEFAULT '',
    is_async INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_timestamp
ON pipeline_events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_service_method
ON pipeline_events(service, method, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_principal
ON pipeline_events(principal_kind, principal_identity, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_correlation
ON pipeline_events(correlation_id)
WHERE correlation_id != '';
```

### Design notes

- **Append-only:** no UPDATE or DELETE from application code. Retention
  is a future concern (a separate story can add a janitor).
- **Local-only:** Article III.3 — no telemetry leaves the machine.
- **Truncation:** `args_summary` and `result_summary` are pre-truncated
  by the decorator before insertion. The column stores what it receives.
- **Schema version:** bump `SCHEMA_VERSION` by one.

## Acceptance

- Table exists after `Database.ensure_schema()`.
- Schema version incremented.
- A raw `INSERT` and `SELECT` round-trips all fields correctly.
- The existing test suite passes unchanged (no regressions from schema bump).

## Test plan

```bash
uv run pytest -q tests/ -k "schema or pipeline_events"
```
