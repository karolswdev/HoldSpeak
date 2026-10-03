# Evidence - PHILO-13-18

- **Story:** PHILO-13-18 - C8 — The 12 px floor
- **Status:** done
- **Date:** 2026-10-02

## Proof

### Captured run — 2026-10-03T04:34:03Z

- **Command:** `bash -c set -eo pipefail; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web; npx tsc --noEmit -p .; echo TYPECHECK-OK; npm run --silent guard:architecture 2>&1 | tail -1; npm run --silent tokens:check 2>&1 | tail -1; npm run --silent bundle:gate 2>&1 | tail -1; cd ..; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_18_type_floor_glass.py tests/unit/test_philo13_18_type_floor_static.py tests/e2e/test_hs202_05_first_use_type_floor.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -2; uv run python scripts/check_web_baseline.py --run 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f592b2e061c4bba1021324c1624641091c98e70e

```text
TYPECHECK-OK
React architecture guard passed (903 source files; zero framework residue).
tokens.css and tokens.gen.ts match design-tokens.json
bundle gate passed (Desk JS 1360387 B; Desk CSS 337662 B; source maps 0)
.................................................................        [100%]
137 passed in 226.65s (0:03:46)

VERDICT: BRANCH-NEW FAILURES: 1
```

### Captured run — 2026-10-03T04:51:01Z

- **Command:** `bash -c set -eo pipefail; H=$(mktemp -d); trap "rm -rf \"$H\"" EXIT INT TERM; cd web; npx tsc --noEmit -p .; echo TYPECHECK-OK; npm run --silent guard:architecture 2>&1 | tail -1; npm run --silent tokens:check 2>&1 | tail -1; cd ..; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_philo13_18_type_floor_glass.py tests/unit/test_philo13_18_type_floor_static.py tests/e2e/test_philo13_18_editor_wrap_glass.py tests/e2e/test_philo13_18_strip_escape_glass.py tests/e2e/test_hs202_05_first_use_type_floor.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py --basetemp=$H/bt -p no:cacheprovider 2>&1 | tail -2; uv run python scripts/check_web_baseline.py --run 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f592b2e061c4bba1021324c1624641091c98e70e

```text
TYPECHECK-OK
React architecture guard passed (903 source files; zero framework residue).
tokens.css and tokens.gen.ts match design-tokens.json
....................................................................     [100%]
140 passed in 241.42s (0:04:01)

VERDICT: baseline-subset, zero branch-new
```
