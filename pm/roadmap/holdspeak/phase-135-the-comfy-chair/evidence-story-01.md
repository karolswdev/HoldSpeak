# Evidence - HS-135-01

- **Story:** HS-135-01 - The hub opens its own desk
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T00:54:12Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit/test_migration_v59_mesh_workers.py tests/unit/test_db_schema_policy.py tests/unit/test_kernel_cancelled_schema.py tests/unit/test_projection_schema.py -k "migrat or schema or mesh" --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 007e4e819c22054bbae1414d6e23acbffc855c40

```text
.............                                                            [100%]
13 passed in 1.53s
```
