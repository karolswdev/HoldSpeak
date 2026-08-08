# Evidence - HS-129-01

- **Story:** HS-129-01 - The foot slot — one window anatomy
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T20:56:03Z

- **Command:** `sh -c cd web && npx vitest run src/desk/__tests__/footSlot.test.tsx src/desk/surface/__tests__/surfaceFooter.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 24f2b4234a2ba5696af1de9fc1c51308bbb59b44

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  6 passed (6)
   Start at  14:56:04
   Duration  845ms (transform 226ms, setup 93ms, import 432ms, tests 132ms, environment 585ms)
```

### Captured run — 2026-08-08T20:56:09Z

- **Command:** `sh -c cd web && npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 24f2b4234a2ba5696af1de9fc1c51308bbb59b44

```text

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```
