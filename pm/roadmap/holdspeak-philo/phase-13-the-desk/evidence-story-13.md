# Evidence - PHILO-13-13

- **Story:** PHILO-13-13 - C3 — A live Dock (AppIcons)
- **Status:** done
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T17:07:18Z

- **Command:** `bash -c set -eo pipefail; HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.8iUtFGOv9j PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_philo13_13_dock_glass.py tests/unit/test_philo13_c3_dock.py tests/unit/test_philo13_astra_atlas.py; cd web && npx vitest run src/desk/components/__tests__/Dock.test.tsx src/desk/__tests__/dockState.test.ts 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f84a0f3a627aed97071109e2f9ddc9bc7ee57b44

```text
.....................................                                    [100%]
37 passed in 23.30s
filter: src/desk/components/__tests__/Dock.test.tsx, src/desk/__tests__/dockState.test.ts
include: **/*.{test,spec}.?(c|m)[jt]s?(x)
exclude:  **/_parked/**, **/node_modules/**
```

### Captured run — 2026-10-03T17:08:05Z

- **Command:** `bash -c set -eo pipefail; HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.13ELRDbCXa PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_philo13_13_dock_glass.py tests/unit/test_philo13_c3_dock.py tests/unit/test_philo13_astra_atlas.py; cd web && npx vitest run src/desk/components/window/Dock.test.tsx src/desk/components/window/dockState.test.ts 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f84a0f3a627aed97071109e2f9ddc9bc7ee57b44

```text
.....................................                                    [100%]
37 passed in 23.20s
      Tests  26 passed (26)
   Start at  11:08:30
   Duration  1.75s (transform 141ms, setup 153ms, import 190ms, tests 1.24s, environment 440ms)
```
