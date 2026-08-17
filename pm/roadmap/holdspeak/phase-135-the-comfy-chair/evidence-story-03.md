# Evidence - HS-135-03

- **Story:** HS-135-03 - The sizing tokens land
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T00:57:35Z

- **Command:** `bash -c cd /Users/karol/dev/tools/HoldSpeak/web && node scripts/generate-tokens.cjs --check && npx vitest run src/desk/surface/gadgets.test.tsx src/desk/__tests__/scrollOwnership.test.tsx src/desk/__tests__/containerQueryLaw.test.ts`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2bdd58362b641633d1c3ae5f30b89b8ca91d7b76

```text
tokens.css and tokens.gen.ts match design-tokens.json

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  3 passed (3)
      Tests  46 passed (46)
   Start at  18:57:35
   Duration  1.46s (transform 768ms, setup 204ms, import 1.33s, tests 506ms, environment 1.08s)
```
