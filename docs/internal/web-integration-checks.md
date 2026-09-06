# Web integration prerequisites

Verified 2026-09-05 against main `d4fbfaca`. The existing web check stopped on 19 raw CSS values, four surface fence findings, eight TypeScript diagnostics, and swallowed Chair writes. This repair preserves the CSS values through shared tokens, uses public surface imports and feature-owned layout classes, restores typed native Button refs, supplies the Concierge choice label slot, and reports failed Chair writes with Retry. Guard ceilings and allowlists were not raised.

Actual output from `npm run check` (bundled Node, isolated worktree):

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (12 allow-listed exceptions, all in use)
React architecture guard passed (663 source files; zero framework residue).
 Test Files  220 passed (220)
      Tests  2165 passed (2165)
✓ built in 4.05s
bundle gate passed (Desk JS 1248814 B; Desk CSS 292517 B; source maps 0)
```

The final Chair generation recovery change and native focus restoration were additionally verified with:

```text
> holdspeak-web@0.0.1 test:web
> vitest run --maxWorkers=2 src/desk/chair/ChairHome.test.tsx src/components/signal/Signal.test.tsx src/desk/__tests__/writeReceiptGuard.test.ts


 RUN  v4.1.9 /Users/karol/dev/alt/HoldSpeak-quality/web


 Test Files  3 passed (3)
      Tests  11 passed (11)
   Start at  16:52:31
   Duration  1.83s (transform 1.20s, setup 172ms, import 1.51s, tests 183ms, environment 585ms)
```

TypeScript and generated-token consistency were checked again after the final test. Full command output is retained in the quality worktree's `.tmp/web-check.log` and `.tmp/web-recovery-tests.log`. Canvas warnings from jsdom are not browser-rendering evidence. This repair does not claim the unrelated Python/model or E2E suites are green; those remain subject to the feature integration checks.
