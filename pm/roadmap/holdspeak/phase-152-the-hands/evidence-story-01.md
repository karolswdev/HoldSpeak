# Evidence - HS-152-01

- **Story:** HS-152-01 - The tool loop (passes, tool_call parts, frames, abort)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T04:10:30Z

- **Command:** `uv run pytest -q tests/unit/test_thread_tool_loop.py tests/unit/test_thread_service.py tests/integration/test_threads_api.py tests/unit/test_realtime_frame_registry.py tests/unit/test_thread_tool_gate.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 44be8e07e2da9ca511523cb7dff8d1a463c8ec16

```text
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 30.37s
```

## Orchestrator triage (2026-08-30)

Read: 80 passed — 11 `test_thread_tool_loop.py` (2-pass happy path with
frames in order + DB rows; held→approve; held→deny → `tool_denied`;
pass cap; abort during a slow execute → indeterminate; sensitive result
→ accumulator → the M1 redactor withholds on a cloud boundary; no-tools
turn byte-identical; tool_unknown; broker passed through) + thread
service/API + frame registry + the gate's 29 (door.add_item classified
by the orchestrator in-round). Composed with the REAL executor; frames
`thread_tool_pending` / `thread_tool_result` / `thread_status_line`
allow-listed emitted-without-consumer until 04/05 wire the UI.
