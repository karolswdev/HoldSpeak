# Evidence - HS-138-04

- **Story:** HS-138-04 - People belongs on the Desk
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-17T23:57:46Z

- **Command:** `sh -c cd web && npx vitest run src/pages/cores/__tests__/peopleCore.test.tsx 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a67258f2bbfb5dee95e68858c5a72d4ff983bdc1

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  4 passed (4)
   Start at  17:57:47
   Duration  1.01s (transform 173ms, setup 75ms, import 282ms, tests 240ms, environment 333ms)
```

## Walk shots (manual/device leg)

The HS-138-06 attended walk (scripts/people_walk_full.py, 55 PASS / 0 FAIL)
produced the populated desktop+narrow proof this story's manual leg requires:
`assets/walk/people-roster-populated-{1440,393}.png`, the Now/1:1s/Info lens
shots at both widths, and `people-detail-send-to-workbench-1440.png` (egress
badge at the point of decision). Zero console errors on every load; no
horizontal overflow at 393; readiness states walked unconfigured → ready →
key_unavailable (fail-closed) → recovered.
