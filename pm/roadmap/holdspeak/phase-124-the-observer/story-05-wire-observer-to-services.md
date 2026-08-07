# HS-124-05 — Wire observer to all 33 services

- **Project:** holdspeak
- **Phase:** 124
- **Status:** backlog
- **Depends on:** HS-124-03, HS-124-04
- **Unblocks:** HS-124-06, HS-124-07, HS-124-08, HS-124-10
- **Owner:** unassigned

## The thesis (the bar)

The protocol exists. The decorator exists. The SQLite backend exists.
This story connects them: every public method on every service is
observed.

### Approach: class-level `_observe_all` utility

Rather than hand-decorating ~150 methods across 33 files, this story
adds a `observe_service(cls)` class decorator or a mixin that
introspects public methods (not `_`-prefixed, not `__dunder__`) and
wraps each with `@observed`. This is applied to every service class.

```python
@observe_service
class PrimitiveService:
    def __init__(self, db: Database, *, observer: PipelineObserver | None = None):
        self._db = db
        self._observer = observer or NullObserver()
    ...
```

### Constructor change

Every service `__init__` gains an optional `observer: PipelineObserver | None = None`
keyword argument, defaulting to `NullObserver()`. This is additive and
backward-compatible — no existing caller breaks.

### Route factory wiring

The `_svc()` factory functions in route modules pass the shared observer
instance. The observer is created once at app startup from the hub's
database connection, stored on the app/hub, and threaded through.

### MCP server wiring

The MCP server's service instantiation similarly receives the shared
observer.

### Audit

After wiring, a grep confirms:
- Every service class has `@observe_service` or equivalent.
- Every `_svc()` factory passes the observer.
- The MCP server passes the observer.
- `NullObserver` is used in tests (no SQLite observer needed for
  existing tests to pass).

### What this story does NOT do

- Does not change any service method's behavior or signature.
- Does not add new tests for individual services (the decorator is
  already tested in HS-124-03).
- Does not add the query service or MCP resource (those are later stories).

## Acceptance

- Every service class is decorated with `@observe_service`.
- A fresh hub starts with a `SQLiteObserver` wired to all services.
- Hitting any route produces a row in `pipeline_events`.
- All existing tests pass (observer defaults to `NullObserver` in tests).
- Census: `grep -c "@observe_service" holdspeak/services/*.py` = 33.

## Test plan

```bash
uv run pytest -q
```

Full suite — this touches every service. Use `-k "not metal"` as always.
