# Evidence - HS-129-06

- **Story:** HS-129-06 - The container-query law
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T21:43:23Z

- **Command:** `sh -c cd web && npm run test:web -- src/desk/__tests__/containerQueryLaw.test.ts && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 209ca406ba9082a9cd2f16694065b1cf1b567d4e

```text

> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2 src/desk/__tests__/containerQueryLaw.test.ts


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  3 passed (3)
   Start at  15:43:23
   Duration  525ms (transform 84ms, setup 64ms, import 92ms, tests 3ms, environment 287ms)
```
