# Evidence - HS-200-43

- **Story:** HS-200-43 - Let a watch become schedulable, and let a manual evaluation count
- **Status:** done
- **Date:** 2026-09-14

## Proof

### Captured run — 2026-09-15T04:05:27Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.citECOdvaO uv run pytest -q -p no:randomly tests/unit/test_phase200_watch_arming.py tests/unit/test_steward_conductor.py tests/unit/test_watch_evaluate_due.py tests/unit/test_watch_condition_matcher.py tests/unit/test_hs171_heartbeat_wire.py tests/unit/test_hs175_meeting_watch.py tests/integration/test_watch_compounding.py tests/integration/test_provider_routes.py tests/unit/test_mcp_sidecar_doc_drift.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1723abd09d5fb668fd9b0ba74d9300fc2c3a5330

```text
........................................................................ [ 29%]
........................................................................ [ 59%]
........................................................................ [ 88%]
...........................                                              [100%]
243 passed in 357.14s (0:05:57)
```

### Captured run — 2026-09-15T04:15:59Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.rOIDp9a7Df uv run pytest -q -p no:randomly tests/unit/test_phase200_watch_arming.py tests/unit/test_phase200_intel_drain.py tests/unit/test_steward_conductor.py tests/unit/test_watch_evaluate_due.py tests/unit/test_watch_condition_matcher.py tests/unit/test_hs171_heartbeat_wire.py tests/unit/test_hs175_meeting_watch.py tests/integration/test_watch_compounding.py tests/integration/test_provider_routes.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_phase200_ci_isolation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5ade218d0cba7fb80aa50d5d34ad4833ee11b25c

```text
........................................................................ [ 25%]
........................................................................ [ 51%]
........................................................................ [ 76%]
..................................................................       [100%]
282 passed in 397.79s (0:06:37)
```
