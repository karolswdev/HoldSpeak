# Evidence - PHILO-13-11

- **Story:** PHILO-13-11 - C1 — The Workbench look (the canvases; the face gate)
- **Status:** done
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T20:47:25Z

- **Command:** `bash -c set -eo pipefail; HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.fZ6zz5AhhP PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q -n 4 tests/e2e/test_philo13_11_titlebar_glass.py tests/e2e/test_philo13_11_frame_glass.py tests/e2e/test_philo13_12_gadgets_glass.py tests/e2e/test_philo13_13_dock_glass.py tests/e2e/test_philo13_17_phone_desk_glass.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_philo_graph_atlas.py; cd web && npx vitest run src/desk/__tests__/workbenchFrame.test.tsx 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1b9938d5b695170f95d0a2958aaad32bdba3476f

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 59%]
.................................................                        [100%]
121 passed in 94.89s (0:01:34)
      Tests  11 passed (11)
   Start at  14:49:00
   Duration  1.32s (transform 478ms, setup 64ms, import 700ms, tests 286ms, environment 194ms)
```
