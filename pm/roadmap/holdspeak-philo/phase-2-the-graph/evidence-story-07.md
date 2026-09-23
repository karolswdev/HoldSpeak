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

### Captured run — 2026-09-23T04:27:08Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.cjNoMvqnpM sh -c uv run --extra dev python scripts/philo_graph_reference.py --check && uv run --extra dev python scripts/philo_graph_reference.py --census && uv run --extra dev python scripts/philo_graph_validate.py docs/generated/graph.json && uv run --extra dev pytest -q -p no:cacheprovider tests/unit/test_phase200_doc_claims.py tests/unit/test_philo_graph_reference.py tests/unit/test_doc_drift_guard.py tests/unit/test_docs_navigation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bfb505e5ee437a2090c41e2fbb7ae07360d4afbe

```text
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
census scope: HTTP routes (the app assembled from source by scripts/gen_api_surface.py, schema-hidden page routes excluded; stale = docs/generated/openapi.json differs from source), desk verbs (web/src/desk/verbRegistry.ts + applications.ts), MCP tools (the real holdspeak.mcp.tools catalogue). Face handlers, keys, timers, frames, CLI and connector edges are not censused. miscited = a pass cited a handler that was not in the file at the revision it examined.
miscited: http GET /api/brief/latest (edge.route.brief_latest): def api_latest was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/brief/items/{item_id}/shelf (edge.route.brief_item_shelf): def api_shelf was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/inference/assignments/set (edge.route.inference_assignments_set): def api_set_assignments was not in holdspeak/web/routes/inference_assignments.py at c42963bc either
miscited: http POST /api/settings/heartbeat/run-now (edge.route.heartbeat_run_now): source registered api_heartbeat_run_now at c42963bc already; the pass cited api_run_heartbeat
miscited: http POST /api/stop (edge.route.meeting_stop): source registered api_stop at c42963bc already; the pass cited api_meeting_stop
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
census: 0 new, 0 removed, 0 changed, 0 stale, 5 miscited, 0 unread, 14 subtype conflict note(s) against docs/generated/graph.json (source_commit f575a582)
OK docs/generated/graph.json
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 4.34s
```
