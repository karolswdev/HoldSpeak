# Evidence - HS-169-07

- **Story:** HS-169-07 - The close (gates, the sweep, counsel, the debt ledger, final summary; 168 folded)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-05T03:51:59Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.1JbQPUvWku HS169_WALK=1 HS169_WALK_DB=isolated uv run pytest -q tests/e2e/test_hs169_door_glass.py tests/e2e/test_hs169_room_glass.py tests/e2e/test_hs169_door_legs_glass.py tests/e2e/test_hs168_connections_glass.py tests/e2e/test_hs168_window_wings_glass.py tests/e2e/live169_walk.py -p no:randomly -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3915f5f90e5f6ce2e179abe72eb89bc3f5c0cdbc

```text
............ss....                                                       [100%]
=========================== short test summary info ============================
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:318: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
16 passed, 2 skipped in 129.98s (0:02:09)
```
