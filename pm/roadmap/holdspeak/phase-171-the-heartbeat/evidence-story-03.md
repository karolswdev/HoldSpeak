# Evidence - HS-171-03

- **Story:** HS-171-03 - The needs-you aggregate (cache + cadence-driven refresh; 170's N+1 paid)
- **Status:** done
- **Date:** 2026-09-05

## Proof

### Captured run — 2026-09-05T13:13:58Z

- **Command:** `uv run pytest -q -p no:cacheprovider tests/unit/test_hs171_aggregate_notify.py tests/unit/test_hs170_faces_wire.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a995185d7b6409526297ed3bc814e8f8db7e69cf

```text
.........................................                                [100%]
41 passed in 1.18s
```
