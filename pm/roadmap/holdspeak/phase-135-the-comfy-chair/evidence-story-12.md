# Evidence - HS-135-12

- **Story:** HS-135-12 - The desk clicks
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T01:28:41Z

- **Command:** `bash -c cd web && npx vitest run src/lib/__tests__/sfx.test.ts 2>&1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 16747967b3e90a2681942da44d805a06c7ae063e

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  10 passed (10)
   Start at  19:28:41
   Duration  334ms (transform 30ms, setup 43ms, import 20ms, tests 9ms, environment 185ms)
```

### Captured run — 2026-08-17T01:28:51Z

- **Command:** `bash -c cd web && npx vitest run 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 16747967b3e90a2681942da44d805a06c7ae063e

```text
 Test Files  135 passed (135)
      Tests  1003 passed (1003)
   Start at  19:28:52
   Duration  12.23s (transform 11.68s, setup 8.74s, import 34.81s, tests 25.04s, environment 47.37s)
```

### Captured run — 2026-08-17T01:29:10Z

- **Command:** `bash -c HOME=$(mktemp -d) uv run pytest -q tests/unit -k settings --tb=short 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 16747967b3e90a2681942da44d805a06c7ae063e

```text
.......................................                                  [100%]
39 passed, 4830 deselected in 2.84s
```
