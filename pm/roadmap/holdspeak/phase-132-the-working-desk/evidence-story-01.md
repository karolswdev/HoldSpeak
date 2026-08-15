# Evidence - HS-132-01

- **Story:** HS-132-01 - Stopping a meeting never stops the hub
- **Status:** done
- **Date:** 2026-08-15

## Proof

### Captured run — 2026-08-15T22:11:30Z

- **Command:** `env HOME=/tmp/hs132-01-home uv run pytest -q tests/integration/test_meeting_conflict_recovery.py tests/integration/test_meeting_stop_and_conflicts.py tests/integration/test_web_server.py::TestRuntimeControlEndpoints --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 96aca0a5a0d2a0bfec5300b79d7457b13c4c4f7a

```text
................                                                         [100%]
16 passed in 6.13s
```

## Orchestrator notes

- Worker baseline proof: with the one-line binding reverted, the named stop
  test fails (13 failed / 80 passed on the full test_web_server.py file);
  with the fix, 12 failed / 91 passed — the remaining 12 are pre-existing
  empty-DB/composition failures charted to HS-132-12 (MIR history, speakers,
  intel queue, global action items, dashboard, history smoke).
- Recorded gap: the "No active meeting" refusal surfaces as HTTP 500 with an
  honest body (generic except in web/routes/meetings/live.py:78-80). Status
  code not chartered here; flagged to HS-132-02.
