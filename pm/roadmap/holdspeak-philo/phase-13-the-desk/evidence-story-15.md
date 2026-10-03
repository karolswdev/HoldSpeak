# Evidence - PHILO-13-15

- **Story:** PHILO-13-15 - C5 — Send to from any document window (the Phase 12 fold)
- **Status:** done
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T17:37:38Z

- **Command:** `bash -c set -eo pipefail; HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.dYaTlgZ4AI PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -n 4 tests/e2e/test_philo13_15_send_to_glass.py tests/unit/test_philo13_muaddib_atlas.py tests/unit/test_philo_graph_atlas.py; cd web && npx vitest run src/desk/__tests__/windowSend.philo1315.test.tsx src/desk/__tests__/workMenu.philo1315.test.tsx 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 48ebbda17a94b58094a153e37948a004a63e8f6a

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 53%]
...............................................................          [100%]
135 passed in 244.41s (0:04:04)
      Tests  23 passed (23)
   Start at  11:41:43
   Duration  1.35s (transform 427ms, setup 119ms, import 588ms, tests 617ms, environment 374ms)
```
