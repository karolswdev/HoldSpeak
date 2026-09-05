# Evidence - HS-174-09

- **Story:** HS-174-09 - LAN companion notifications (Bonjour mesh push; CONDITIONAL on the companion track)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T20:31:05Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_hs174_runner.py -k notif 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c08cd0862267ff10359f68bc951990e470b8d13a

```text
5 passed, 12 deselected in 0.32s
```
