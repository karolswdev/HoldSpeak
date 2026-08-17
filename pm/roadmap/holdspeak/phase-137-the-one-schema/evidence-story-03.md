# Evidence - HS-137-03

- **Story:** HS-137-03 - The test reckoning
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-17T16:00:19Z

- **Command:** `uv run pytest -q tests/unit/test_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3c98d0fce2c2624a88d33c33a190fda45f0b4f93

```text
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 14.40s
```

## Orchestrator verification
- ~19 migration-chain tests deleted (whole-file where migration-only,
  else the single function); `test_db_schema_policy.py` and
  `test_doctor_config_honesty.py` rewritten to assert shape/behavior not
  version numbers; the canonical-snapshot shape guard kept; unrelated
  `*_SCHEMA_VERSION` payload/protocol tests left alone.
- Full suite green: 5917 passed, 0 real failures (part of the bundle).
