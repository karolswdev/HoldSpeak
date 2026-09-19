# Evidence - HS-201-01

- **Story:** HS-201-01 - The desk names the one thing it needs
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T22:47:08Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.NOSmwmJFDK PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run pytest -q tests/e2e/test_hs201_one_thing_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
......                                                                   [100%]
6 passed in 27.21s
```

### Captured run — 2026-09-19T22:47:39Z

- **Command:** `sh -c cd web && npx vitest run src/desk/chair/arrivalOneThing.test.tsx src/desk/setup.test.ts src/pages/cores/historyHeadline.test.ts 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text

 Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  16:47:39
   Duration  917ms (transform 609ms, setup 281ms, import 827ms, tests 41ms, environment 951ms)
```
