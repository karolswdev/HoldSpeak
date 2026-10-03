# Evidence - PHILO-13-17

- **Story:** PHILO-13-17 - C7 — The phone desk
- **Status:** done
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T17:16:17Z

- **Command:** `bash -c set -eo pipefail; HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.KWE2KQ66y2 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -n 4 tests/e2e/test_philo13_17_phone_desk_glass.py tests/e2e/test_hs202_first_use_smoke.py tests/e2e/test_philo13_13_dock_glass.py tests/unit/test_philo13_muaddib_atlas.py tests/unit/test_philo_graph_atlas.py; cd web && npx vitest run src/desk/chair src/desk/components/window 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eb4c2ac24fcd9888748cb853f84646be99317f16

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 53%]
..............................................................           [100%]
134 passed in 161.76s (0:02:41)
      Tests  155 passed (155)
   Start at  11:19:00
   Duration  5.52s (transform 4.76s, setup 2.49s, import 16.07s, tests 17.16s, environment 8.98s)
```
