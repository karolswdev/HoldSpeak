# Evidence - HS-95-04

- **Story:** HS-95-04 - Embeddable page cores
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T02:56:52Z

- **Command:** `bash -c uv run pytest -q tests/unit/test_page_cores_guard.py 2>&1 | tail -1 && npm --prefix web run test:web 2>&1 | tail -3 && uv run python scripts/desk_gl_walk.py cores`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 99791585114edc306b0c92ec5cf2b20b98ba59d4

```text
2 passed in 0.03s
   Start at  20:56:52
   Duration  9.31s (transform 648ms, setup 1.30s, import 3.09s, tests 2.56s, environment 8.34s)

cores walk: shelf opens both cores in-world (chrome-free); flat routes keep the hero
```
