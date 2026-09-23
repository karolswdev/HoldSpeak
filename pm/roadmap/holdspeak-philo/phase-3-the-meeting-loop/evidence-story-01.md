# Evidence - PHILO-3-01

- **Story:** PHILO-3-01 - Record the decision (A1)
- **Status:** done
- **Date:** 2026-09-22

## Proof

### Captured run — 2026-09-23T05:25:49Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.q1fQF9sQKA sh -c uv run --extra dev pytest -q -p no:cacheprovider tests/unit/test_philo3_01_decision_route.py tests/unit/test_phase200_doc_claims.py && uv run python scripts/philo_api_reference.py --check && uv run python scripts/philo_openapi_reference.py --check && uv run python scripts/generate_capability_docs.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dc2b492ac3226832a8c6bcbcc74cd7c070901506

```text
.................................................                        [100%]
49 passed in 2.40s
API reference checked
OpenAPI: 569 paths
Architecture documentation checked (10 outputs).
```

### Captured run — 2026-09-23T05:56:01Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Hpf6JLmXCD PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright sh -c uv run --extra dev pytest -q -p no:cacheprovider tests/unit/test_philo3_01_decision_route.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_phase200_doc_claims.py && cd web && npx vitest run src/desk/__tests__/philo301DecisionFace.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts 2>&1 | tail -3 && cd .. && uv run python scripts/philo_api_reference.py --check && uv run python scripts/philo_openapi_reference.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2d410d2027370a26df33760a1f2254104f226175

```text
...................................................                      [100%]
51 passed in 2.67s
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
API reference checked
OpenAPI: 569 paths
```

### Captured run — 2026-09-23T15:06:28Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ydLESzY4DN PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm sh -c set -o pipefail; (cd web && npx vitest run src/desk/__tests__/philo301DecisionFace.test.tsx src/desk/__tests__/philo301DecisionNoLoss.test.tsx src/desk/__tests__/philo301RetryKept.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts) && uv run --extra dev pytest -q -p no:cacheprovider tests/unit/test_philo3_01_decision_route.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_phase200_doc_claims.py tests/e2e/test_philo3_01_receipt_hits.py && uv run python scripts/philo_api_reference.py --check && uv run python scripts/philo_openapi_reference.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9fe4be94220d3a99125dc95aeaf5978bbb11d24e

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-3-01/web


 Test Files  4 passed (4)
      Tests  13 passed (13)
   Start at  09:06:28
   Duration  1.70s (transform 2.05s, setup 287ms, import 2.60s, tests 421ms, environment 852ms)

.......................................................                  [100%]
55 passed in 23.53s
API reference checked
OpenAPI: 569 paths
```
