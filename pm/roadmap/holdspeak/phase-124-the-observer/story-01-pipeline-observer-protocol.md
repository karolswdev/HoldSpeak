# HS-124-01 — PipelineObserver protocol and event schema

- **Project:** holdspeak
- **Phase:** 124
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-124-02, HS-124-03, HS-124-04, HS-124-05
- **Owner:** unassigned

## The thesis (the bar)

The observer needs a stable contract before any implementation. This
story defines two things:

1. **The `PipelineEvent` dataclass** — the shape of every recorded event.
2. **The `PipelineObserver` protocol** — what backends implement.

### PipelineEvent fields

| Field | Type | Source |
|-------|------|--------|
| `event_id` | `str` (UUID4) | Generated at call time |
| `timestamp` | `float` (epoch) | `time.time()` |
| `service` | `str` | Class name (e.g. `"PrimitiveService"`) |
| `method` | `str` | Method name (e.g. `"create_note"`) |
| `principal_kind` | `str` | `principal.kind.value` |
| `principal_identity` | `str` | `principal.identity` |
| `args_summary` | `str` | JSON of non-`self`/non-`principal` args, truncated to 2 KB |
| `result_summary` | `str` | JSON of result, truncated to 2 KB |
| `error` | `str \| None` | `repr(exception)` if raised, else `None` |
| `error_code` | `str \| None` | `ServiceError.code` if applicable |
| `duration_ms` | `float` | Wall-clock milliseconds |
| `correlation_id` | `str` | Thread-local or context-var, defaulting to `event_id` |
| `is_async` | `bool` | Whether the method was awaited |

### PipelineObserver protocol

```python
class PipelineObserver(Protocol):
    def on_event(self, event: PipelineEvent) -> None: ...
```

Single method, fire-and-forget. The observer must never raise — the
decorator catches and logs. Observers see completed events (result or
error already resolved), not in-flight calls.

### NullObserver

A `NullObserver` that does nothing, used as the default when no observer
is configured. Ensures the decorator never branches on `None`.

### File location

`holdspeak/services/observer.py` — the protocol, event dataclass, and
null observer.

## Acceptance

- `PipelineEvent` is a frozen dataclass with all fields above.
- `PipelineObserver` is a `typing.Protocol` with `on_event`.
- `NullObserver` implements the protocol as a no-op.
- Unit test: create a `PipelineEvent`, confirm it's frozen and all fields
  are accessible.
- Unit test: `NullObserver().on_event(event)` does not raise.

## Test plan

```bash
uv run pytest -q tests/ -k "pipeline_event or pipeline_observer or null_observer"
```
