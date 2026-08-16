# HS-124-04 — SQLiteObserver — the day-one backend

- **Project:** holdspeak
- **Phase:** 124
- **Status:** done
- **Depends on:** HS-124-01, HS-124-02
- **Unblocks:** HS-124-05, HS-124-06
- **Owner:** unassigned

## The thesis (the bar)

The `PipelineObserver` protocol is backend-agnostic. This story provides
the first real backend: a `SQLiteObserver` that writes events to the
`pipeline_events` table.

### Behavior

```python
class SQLiteObserver:
    def __init__(self, connection: Callable) -> None:
        self._connection = connection

    def on_event(self, event: PipelineEvent) -> None:
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO pipeline_events (...) VALUES (...)",
                event_to_row(event),
            )
```

### Design notes

- **Synchronous insert.** The observer runs in the same thread as the
  service call. The insert is a single SQLite row — microseconds. If
  this ever becomes a concern, a future story can add a background
  queue; premature async would add complexity the data doesn't justify.
- **Connection callable.** Same pattern as `JournalStore` and every
  repository — receives a `Callable[[], Connection]`.
- **Fire-and-forget safety.** If the insert fails (disk full, schema
  drift), the observer logs a warning and does not raise. The decorator
  already catches observer exceptions, but the observer itself should
  also be safe.

### File location

`holdspeak/services/sqlite_observer.py`.

## Acceptance

- Insert a `PipelineEvent` via `SQLiteObserver.on_event`, then `SELECT`
  it back and confirm all fields match.
- Insert with a deliberately broken connection → warning logged, no
  exception raised.
- Round-trip test: 100 events inserted, all retrievable ordered by
  timestamp.

## Test plan

```bash
uv run pytest -q tests/ -k "sqlite_observer"
```
