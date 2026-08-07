# HS-124-07 — MCP resource: pipeline events

- **Project:** holdspeak
- **Phase:** 124
- **Status:** backlog
- **Depends on:** HS-124-06
- **Unblocks:** HS-124-10
- **Owner:** unassigned

## The thesis (the bar)

The event query service exists. This story exposes it as MCP resources
so any MCP client can ask "what happened?"

### Resources

| URI | Type | Description |
|-----|------|-------------|
| `pipeline://events/recent` | static | Last 50 events (default) |
| `pipeline://events/recent/{service}` | template | Events for a specific service |
| `pipeline://events/stats` | static | Service heatmap / analytics |
| `pipeline://events/correlation/{id}` | template | Causal chain for a correlation ID |

### MCP tool

One tool for richer queries:

| Tool | Description |
|------|-------------|
| `pipeline_events_query` | Query pipeline events with filters (service, method, principal, time range, errors_only, limit) |

### Implementation

Add to `holdspeak/mcp/resources.py` and `holdspeak/mcp/tools.py`. The
resources and tool delegate to `EventQueryService`.

### File changes

- `holdspeak/mcp/resources.py` — 4 new resource registrations.
- `holdspeak/mcp/tools.py` — 1 new tool.

## Acceptance

- `resources/list` includes all 4 pipeline resources.
- `resources/read` on each returns valid JSON with correct schema.
- `tools/call` with `pipeline_events_query` returns filtered events.
- Walk: seed events via service calls, then query via MCP and confirm
  the events appear.

## Test plan

```bash
uv run pytest -q tests/ -k "mcp_pipeline or mcp_resource_pipeline"
```
