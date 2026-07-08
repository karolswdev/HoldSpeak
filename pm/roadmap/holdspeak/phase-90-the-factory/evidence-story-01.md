# Evidence - HS-90-01

- **Story:** HS-90-01 - The factory — spawn, rename, kill
- **Status:** done
- **Date:** 2026-07-08

## Proof

### Captured run — 2026-07-08T23:35:57Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/9244985d-2dd6-4abf-a33c-7a099253c728/scratchpad/factory_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7e777f90513e7ff24c312624801e3561549399d4

```text
1) spawn hs90fac: spawned pane=%0  exists=True
   bad-name spawn refused: bad_name
2) rename -> hs90shipped: renamed  old_gone=True new_exists=True
3) arm+steer the spawned pane: delivered  text landed=True
4) kill (session): killed  session_gone=True  grant_dropped=True

  audit (newest first):
    ✓ killed     kill %0 (session)
    ✓ delivered  echo BORN_AND_STEERED
    ✓ renamed    rename hs90fac -> hs90shipped
    ✕ bad_name   spawn evil; reboot
    ✓ spawned    spawn hs90fac :: bash --norc --noprofile

HS-90-01 FACTORY LIFECYCLE: PASS
```
