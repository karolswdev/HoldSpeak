# Evidence - HS-200-41

- **Story:** HS-200-41 - Return to unfinished work
- **Status:** done
- **Date:** 2026-09-07

## Proof

### Captured run — 2026-09-07T17:55:25Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_task_resume.py tests/integration/test_phase200_task_resume.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
.............................................................            [100%]
61 passed in 73.02s (0:01:13)
```

### Captured run — 2026-09-07T17:56:45Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs200_task_resume_glass.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
=========================== short test summary info ============================
FAILED tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440
1 failed, 14 passed in 112.50s (0:01:52)
```

### Captured run — 2026-09-07T18:51:05Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs200_task_resume_glass.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
=========================== short test summary info ============================
FAILED tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440
1 failed, 14 passed in 62.60s (0:01:02)
```

### Captured run — 2026-09-07T20:16:17Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q tests/e2e/test_hs200_task_resume_glass.py -p no:cacheprovider 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
...............                                                          [100%]
15 passed in 67.90s (0:01:07)
```

### Captured run — 2026-09-07T20:17:33Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_task_resume.py tests/integration/test_phase200_task_resume.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_web_vocabulary_guard.py tests/integration/test_phase200_runtime_identity.py tests/unit/test_db.py -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
1 failed, 181 passed in 73.38s (0:01:13)
```

### Captured run — 2026-09-07T20:21:23Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run pytest -q tests/unit/test_phase200_task_resume.py tests/integration/test_phase200_task_resume.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_web_vocabulary_guard.py tests/integration/test_phase200_runtime_identity.py tests/unit/test_db.py -p no:cacheprovider 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
......................................                                   [100%]
182 passed in 72.71s (0:01:12)
```

### Captured run — 2026-09-07T20:22:40Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run python scripts/check_web_baseline.py --run 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4663daedd24c318a10a59e0ee5fb33c01b05ce52

```text
Suite totals: 2452 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```
