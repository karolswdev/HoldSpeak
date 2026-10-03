# Evidence - PHILO-13-12

- **Story:** PHILO-13-12 - C2 — The gadgets that are missing
- **Status:** done
- **Date:** 2026-10-02

## Proof

### Captured run — 2026-10-03T01:46:43Z

- **Command:** `bash -c set -eo pipefail; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web; npx vitest run src/desk 2>&1 | tail -3; npx tsc --noEmit -p .; echo TYPECHECK-OK; npm run --silent guard:architecture 2>&1 | tail -1; npm run --silent bundle:gate 2>&1 | tail -1; cd ..; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_12_gadgets_glass.py tests/e2e/test_philo13_11_frame_glass.py tests/e2e/test_philo13_11_chair_glass.py tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo13_muaddib_atlas.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 87e57a969ae96db55687b704239deadd2ea340b9

```text
   Start at  19:46:43
   Duration  23.01s (transform 18.20s, setup 19.25s, import 72.69s, tests 56.60s, environment 68.53s)

TYPECHECK-OK
React architecture guard passed (892 source files; zero framework residue).
bundle gate passed (Desk JS 1350572 B; Desk CSS 333495 B; source maps 0)
..........                                                               [100%]
154 passed in 87.25s (0:01:27)
```
