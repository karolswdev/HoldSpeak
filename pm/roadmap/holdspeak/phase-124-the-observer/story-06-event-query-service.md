# HS-124-06 — Event query service

- **Project:** holdspeak
- **Phase:** 124
- **Status:** done
- **Depends on:** HS-124-04, HS-124-05
- **Unblocks:** HS-124-07
- **Owner:** unassigned

## The thesis (the bar)

Events are stored. Now they need to be queryable. This story adds an
`EventQueryService` that reads from `pipeline_events` and answers the
questions the HANDOVER planted:

- "What did the desk DO today?"
- "Which services are hot? Which are dead?"
- "What did agent X actually touch?"
- "Replay this user's last hour."

### API surface

```python
class EventQueryService:
    def __init__(self, db: Database) -> None: ...

    def recent(
        self, principal: Principal, *,
        limit: int = 50,
        service: str | None = None,
        method: str | None = None,
        principal_kind: str | None = None,
        since: float | None = None,
        until: float | None = None,
        correlation_id: str | None = None,
        errors_only: bool = False,
    ) -> list[dict[str, Any]]: ...

    def stats(
        self, principal: Principal, *,
        since: float | None = None,
        until: float | None = None,
    ) -> dict[str, Any]: ...

    def by_correlation(
        self, principal: Principal,
        correlation_id: str,
    ) -> list[dict[str, Any]]: ...
```

### `recent()` — filtered event stream

Returns events matching the filter, newest first. Pagination by `limit`
+ `since`/`until`. Each event is a dict with all `PipelineEvent` fields
plus the integer `id`.

### `stats()` — service heatmap

Returns:
```json
{
  "total_events": 1423,
  "period": {"since": 1723000000.0, "until": 1723086400.0},
  "by_service": [
    {"service": "PrimitiveService", "count": 312, "error_count": 2, "avg_ms": 4.1},
    ...
  ],
  "by_method": [
    {"service": "AskService", "method": "ask", "count": 87, "error_count": 5, "avg_ms": 2341.0},
    ...
  ],
  "by_principal": [
    {"kind": "OWNER", "identity": "karol", "count": 900},
    {"kind": "AGENT", "identity": "mcp-client", "count": 523}
  ]
}
```

### `by_correlation()` — causal chain

Returns all events sharing a `correlation_id`, ordered by timestamp.
This is the "replay" view.

### File location

`holdspeak/services/event_query_service.py`. This service is itself
observed (it eats its own dog food), but the observer must not recurse —
queries about events must not generate events about queries. The
`@observed` decorator skips methods on `EventQueryService` (or the
service opts out via a class attribute).

## Acceptance

- Seed 100 events across 5 services, query with each filter, confirm
  correct results.
- `stats()` returns accurate counts and averages.
- `by_correlation()` returns the correct causal chain.
- The service does not produce pipeline events about its own queries
  (no recursion).

## Test plan

```bash
uv run pytest -q tests/ -k "event_query"
```
