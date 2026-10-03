# Evidence - PHILO-13-06

- **Story:** PHILO-13-06 - B1 — One open grammar
- **Status:** done
- **Date:** 2026-10-02

## Proof

### Captured run — 2026-10-03T03:07:45Z

- **Command:** `bash -c set -eo pipefail; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web; npx vitest run src/desk src/pages/cores src/features/project-room 2>&1 | grep -E "Test Files|Tests "; npx tsc --noEmit -p .; echo TYPECHECK-OK; npm run --silent guard:architecture 2>&1 | tail -1; cd ..; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_06_open_glass.py tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 071b9093f376206d79ee8bb6b8cc3f9836e87470

```text
 Test Files  301 passed (301)
      Tests  2751 passed (2751)
TYPECHECK-OK
React architecture guard passed (895 source files; zero framework residue).
.......................................................                  [100%]
127 passed in 56.75s
```
