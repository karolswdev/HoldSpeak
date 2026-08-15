# HS-124-03 — The `@observed` decorator

- **Project:** holdspeak
- **Phase:** 124
- **Status:** done
- **Depends on:** HS-124-01
- **Unblocks:** HS-124-05
- **Owner:** unassigned

## The thesis (the bar)

The decorator is the single instrumentation point. It wraps a service
method, captures timing and arguments, builds a `PipelineEvent`, and
hands it to the configured `PipelineObserver`. It handles both sync and
async methods transparently.

### Behavior

```python
@observed
def create_note(self, principal: Principal, *, title: str = "", ...) -> dict:
    ...
```

1. Before the call: snapshot `time.time()`, extract service class name
   and method name, serialize non-self/non-principal args to JSON
   (truncated to 2 KB).
2. Call the original method.
3. After the call: compute duration, serialize result (truncated to 2 KB),
   build `PipelineEvent`, call `self._observer.on_event(event)`.
4. On exception: capture `repr(exception)` and `error_code` (if
   `ServiceError`), still build and emit the event, then re-raise.

### Observer injection

Services gain a `_observer: PipelineObserver` attribute. The decorator
reads `self._observer`. Default is `NullObserver()` (set in a base
mixin or by the decorator itself if missing).

### Async support

The decorator inspects `asyncio.iscoroutinefunction(fn)` and wraps
accordingly. The `is_async` field on the event reflects which path ran.

### Correlation ID

Uses a `contextvars.ContextVar[str]` named `correlation_id`. If unset,
the decorator generates a fresh UUID and sets it for the duration of the
call. Nested service calls within the same context share the correlation.

### Safety contract

- The decorator must NEVER prevent the original method from executing.
- The decorator must NEVER swallow an exception.
- If observer.on_event raises, the decorator catches and logs a warning.
- Overhead budget: < 1ms per call (measured in the walk).

### File location

`holdspeak/services/observer.py` — alongside the protocol from HS-124-01.

## Acceptance

- Sync method: decorator captures service, method, principal, args,
  result, duration, and emits event to a mock observer.
- Async method: same behavior under `asyncio.run`.
- Exception path: event is emitted with error fields, exception re-raised.
- Observer failure: warning logged, original method still succeeds.
- Correlation: two nested calls share the same `correlation_id`.
- Truncation: args/result > 2 KB are truncated with `…` suffix.

## Test plan

```bash
uv run pytest -q tests/ -k "observed_decorator or observed_sync or observed_async"
```
