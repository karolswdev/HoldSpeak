# Evidence - HS-134-07

- **Story:** HS-134-07 - Sync understands inherit
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T22:56:21Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_sync_inherit_134.py tests/unit/test_primitive_contract.py tests/unit/test_web_routes_sync.py tests/unit/test_sync_decision_records_127.py tests/unit/test_schedule_delegations.py tests/unit/test_deployment_revisions.py tests/unit/test_workbench_runner_migration.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9b03cc1204e6046f68a5d10122b7bdbcfd80e849

```text
.....................................................................    [100%]
69 passed in 9.33s
```
