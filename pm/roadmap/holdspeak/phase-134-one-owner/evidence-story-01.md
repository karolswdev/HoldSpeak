# Evidence - HS-134-01

- **Story:** HS-134-01 - Recipe execution takes the precedence door
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-16T21:57:58Z

- **Command:** `HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.jpONoi1P5S uv run pytest -q tests/unit/test_recipe_precedence.py tests/unit/test_recipe_runner_migration.py tests/unit/test_one_path_spine.py tests/unit/test_placement_resolver.py --tb=short`
- **Cwd:** .
- **Exit code:** 127
- **Index-tree:** fe0759a20fb0714eff45a83f85ee1310712d7347

```text
(command could not be executed: [Errno 2] No such file or directory: 'HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.jpONoi1P5S')
```

### Captured run — 2026-08-16T21:58:12Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.e7tR04nD2V uv run pytest -q tests/unit/test_recipe_precedence.py tests/unit/test_recipe_runner_migration.py tests/unit/test_one_path_spine.py tests/unit/test_placement_resolver.py --tb=short`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fe0759a20fb0714eff45a83f85ee1310712d7347

```text
..........................................                               [100%]
42 passed in 6.28s
```
