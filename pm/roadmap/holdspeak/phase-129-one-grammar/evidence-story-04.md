# Evidence - HS-129-04

- **Story:** HS-129-04 - Shell-scroller and double-scroll repairs
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T21:16:41Z

- **Command:** `sh -c cd web && npx vitest run src/desk/__tests__/scrollOwnership.test.tsx src/desk/__tests__/footSlot.test.tsx src/desk/components/DeskToolInspector.test.tsx --maxWorkers=2 && npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6b7fcc6280ac68ad7c4a73ac2ec55c694f50cbdc

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  3 passed (3)
      Tests  10 passed (10)
   Start at  15:16:41
   Duration  1.60s (transform 441ms, setup 156ms, import 1.10s, tests 472ms, environment 762ms)


> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```
