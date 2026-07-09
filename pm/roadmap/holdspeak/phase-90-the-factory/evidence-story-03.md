# Evidence - HS-90-03

- **Story:** HS-90-03 - The factory on glass + the walk + close
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-09T00:19:36Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/walk_routes.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8559ccb227356e41b0da2a12166eff9d05a54b68

```text
1) POST /factory/spawn -> 200 spawned pane=%0 exists=True
2) GET /steering/panes -> the spawned pane listed? True
3) /arm -> armed   4) /keys C-c -> delivered   5) /steer -> delivered landed=True
6) POST /factory/rename -> renamed new_exists=True old_gone=True
7) POST /{key}/kill -> killed session_gone=True

  audit (this pane, newest first):
    ✓ kill %0 (session)
    ✓ echo WALKED_FROM_GLASS
    ✓ C-c
    ✓ kill %0 (session)
    ✓ echo WALKED_FROM_GLASS
    ✓ C-c
    ✓ kill %0 (session)
    ✓ echo WALKED_FROM_GLASS
    ✓ C-c
    ✓ echo REMOTE_WALK_OK

  1 spawn=✓  2 in picker=✓  3 arm=✓  4 key=✓  5 steer=✓  6 rename=✓  7 kill=✓  8 audit=✓

HS-90-03 THE WALK (desk routes, live): PASS
```
