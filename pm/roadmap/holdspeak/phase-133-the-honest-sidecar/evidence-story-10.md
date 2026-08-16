# Evidence - HS-133-10

- **Story:** HS-133-10 - The sidecar has a manual
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T16:54:17Z

- **Command:** `HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sbxxKRg6BC uv run pytest -q tests/unit/test_doc_drift_guard.py --tb=short`
- **Cwd:** .
- **Exit code:** 127
- **Index-tree:** 201e3b6ac0f8e10c54658a6affc42738eae53ee4

```text
(command could not be executed: [Errno 2] No such file or directory: 'HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sbxxKRg6BC')
```

### Captured run — 2026-08-16T16:54:24Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_doc_drift_guard.py --tb=short 2>&1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 201e3b6ac0f8e10c54658a6affc42738eae53ee4

```text
...................                                                      [100%]
19 passed in 0.24s
```
