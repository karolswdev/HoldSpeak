# Evidence - PHILO-13-05

- **Story:** PHILO-13-05 - Close means gone
- **Status:** done
- **Date:** 2026-10-01

## Proof

### Captured run — 2026-10-02T02:19:02Z

- **Command:** `bash -c set -e; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web && npx vitest run src/desk/__tests__/pulloutCloseQualified.test.tsx src/desk/__tests__/window.test.ts src/desk/__tests__/storeSplit.test.ts src/desk/__tests__/windowSingleInstance.test.ts 2>&1 | tail -6; cd ..; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_05_close_glass.py tests/unit/test_philo13_muaddib_atlas.py tests/unit/test_philo_graph_atlas.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c29d5d71eeaa57a8934f372548faf024b1899f44

```text

 Test Files  3 passed (3)
      Tests  58 passed (58)
   Start at  20:19:02
   Duration  1.87s (transform 909ms, setup 202ms, import 1.23s, tests 609ms, environment 589ms)

........................................................................ [ 56%]
.......................................................                  [100%]
127 passed in 72.49s (0:01:12)
```

### Captured run — 2026-10-02T14:44:15Z

- **Command:** `bash -c set -eo pipefail; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web; npx vitest run src/desk/__tests__/pulloutCloseQualified.test.tsx src/desk/__tests__/window.test.ts src/desk/__tests__/storeSplit.test.ts src/desk/__tests__/windowSingleInstance.test.ts src/desk/pullouts 2>&1 | tail -4; cd ..; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_05_close_glass.py tests/unit/test_philo13_muaddib_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo10_atlas.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a52be4bf9b90df61f790c38af9fc876e3b265311

```text
      Tests  139 passed (139)
   Start at  08:44:15
   Duration  3.02s (transform 4.28s, setup 2.12s, import 8.24s, tests 3.99s, environment 7.00s)

......................                                                   [100%]
238 passed in 88.59s (0:01:28)
```
