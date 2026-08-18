# Evidence - HS-139-08

- **Story:** HS-139-08 - Open throttle
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-18T02:38:28Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest tests/unit/test_open_posture.py tests/unit/test_people_policy.py tests/unit/test_people_no_leaks.py tests/unit/test_people_key_custody.py tests/unit/test_people_crypto.py -q`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ce8084b65b422f380e449fcb4ea5d69c9463e655

```text
...............................................                          [100%]
47 passed in 0.59s
```
