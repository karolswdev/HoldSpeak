# Evidence - HS-152-02

- **Story:** HS-152-02 - The gate (thread_tool_policy, the truth table, kernel children)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T03:51:38Z

- **Command:** `uv run pytest -q tests/unit/test_thread_tool_gate.py tests/unit/test_thread_repository.py tests/unit/test_one_path_census.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_db.py -k not slow`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1f386f3a2b14901da3483b89d18ceca5f0c945ca

```text
........................................................................ [ 38%]
........................................................................ [ 77%]
.........................................                                [100%]
185 passed in 110.99s (0:01:50)
```

## Orchestrator triage (2026-08-30)

Read: 185 passed — 29 `test_thread_tool_gate.py` (all eight truth-table
rows; admit creates a kernel child through `broker.submit` via the
existing `tool.call@1` codec with the turn's operation as parent; hold →
approve executes with a receipt; deny → `tool_denied`; Allow-always
writes one policy row and the next call auto-admits, Allow-once none;
elicitation hold + answer re-dispatch; `people.*` → sensitive; cancel
mid-execute discards; classification fail-closed over every TOOLS
name), the thread repository, the one-path census + three 143 fences
(unchanged — the executor is a service dispatch, not a model site), and
the schema snapshot (regenerated: `thread_tool_policy`). RULE recorded
for the loop: `broker=None` is test-only; production composes the
executor with the kernel broker.
