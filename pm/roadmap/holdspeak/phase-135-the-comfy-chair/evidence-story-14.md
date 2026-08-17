# Evidence - HS-135-14

- **Story:** HS-135-14 - The chrome speaks Workbench
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T02:35:19Z

- **Command:** `bash -c cd web && npx vitest run src/desk/systemSprites.test.ts src/desk/components/MicButton.test.tsx src/pages/cores/__tests__/cadenceCore.test.tsx 2>&1 | tail -30`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ea6909ec55e415ca7e6578bae4abba350f6e3618

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  3 passed (3)
      Tests  21 passed (21)
   Start at  20:35:19
   Duration  839ms (transform 318ms, setup 179ms, import 509ms, tests 324ms, environment 875ms)
```
