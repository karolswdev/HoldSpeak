# Evidence - PHILO-2-07

- **Story:** PHILO-2-07 - The tree up to par
- **Status:** done
- **Date:** 2026-09-22

## Proof

### Captured run — 2026-09-23T04:02:05Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.KdpQdTArEK sh -c uv run --extra dev python scripts/philo_graph_reference.py --check && uv run --extra dev python scripts/philo_graph_reference.py --census && uv run --extra dev python scripts/philo_graph_validate.py docs/generated/graph.json && uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_doc_claims.py tests/unit/test_philo_graph_reference.py tests/unit/test_doc_drift_guard.py tests/unit/test_docs_navigation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 685a25a8cfe1591819ca7cb188d4c0d168e33469

```text
graph join checked: docs/generated/graph.json
census scope: HTTP routes (docs/generated/openapi.json), desk verbs (web/src/desk/verbRegistry.ts + applications.ts), MCP tools (the real holdspeak.mcp.tools catalogue). Face handlers, keys, timers, frames, CLI and connector edges are not censused. miscited = a pass cited a handler that was not in the file at the revision it examined.
miscited: http GET /api/brief/latest (edge.route.brief_latest): def api_latest was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/brief/items/{item_id}/shelf (edge.route.brief_item_shelf): def api_shelf was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/inference/assignments/set (edge.route.inference_assignments_set): def api_set_assignments was not in holdspeak/web/routes/inference_assignments.py at c42963bc either
miscited: http POST /api/settings/heartbeat/run-now (edge.route.heartbeat_run_now): def api_run_heartbeat was not in holdspeak/web/routes/system/settings.py at c42963bc either
census: 0 new, 0 removed, 0 changed, 4 miscited, 0 unread against docs/generated/graph.json (source_commit f575a582)
OK docs/generated/graph.json
........................................................................ [ 76%]
......................                                                   [100%]
94 passed in 3.49s
```
