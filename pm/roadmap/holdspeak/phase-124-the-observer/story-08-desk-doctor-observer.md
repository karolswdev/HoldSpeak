# HS-124-08 — Desk doctor: observer health check

- **Project:** holdspeak
- **Phase:** 124
- **Status:** backlog
- **Depends on:** HS-124-05
- **Unblocks:** HS-124-10
- **Owner:** unassigned

## The thesis (the bar)

The desk doctor (from Phase 122) runs health checks. This story adds one
check for the pipeline observer.

### Check: `observer_wired`

Verifies:
1. The `pipeline_events` table exists in the database.
2. At least one service class has the `@observe_service` decorator
   applied (runtime check: instantiate a service, confirm `_observer`
   attribute exists and is not `None`).
3. A test event can be written and read back.

### Status reporting

- **healthy:** all three checks pass.
- **degraded:** table exists but no events in last 24 hours (observer
  may not be wired).
- **unhealthy:** table missing or write/read fails.

### File change

`holdspeak/doctor.py` — add `check_observer()` to the existing checks
list.

## Acceptance

- `holdspeak doctor` reports observer status.
- With a fresh DB: healthy (table created, test event written).
- With a broken DB connection: unhealthy with clear error message.

## Test plan

```bash
uv run pytest -q tests/ -k "doctor"
```
