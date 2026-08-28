# Evidence - HS-145-01

- **Story:** HS-145-01 - The board scroll hint
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T19:34:45Z

- **Command:** `zsh -c cd web && npx vitest run src/desk/chair/lanes/DoorBoardLane.test.tsx 2>&1 | tail -8`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 48b0ab7af92634637fcae30d135c49043ab12260

```text
 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  18 passed (18)
   Start at  13:34:52
   Duration  11.35s (transform 1.65s, setup 1.17s, import 5.35s, tests 621ms, environment 4.04s)
```

## Orchestrator triage note

The captured vitest run (18 passed) covers the `computeScrollHint`
pure function (all four states) and the wrapper-attribute render
test. The rest of the story's proof chain, verified by the
orchestrator directly:

- **The glass proof** lives in
  `tests/e2e/test_hs145_door_polish_glass.py::test_hs145_scroll_hint_gradient_393_and_1440`
  (real hub, populated board): asserts `data-scroll-hint` =
  right → both → left across a real scroll at 393×900, `none` at
  1440×900, AND that the ::after pseudo-element actually paints
  (computed height > 0) — because the FIRST implementation did not:
  the plan's sticky in-flow pseudo-elements resolved to zero height.
  The worker's glass run caught it and the fix (an outer
  `.door-board-hint-wrap` with absolutely positioned pseudo-elements;
  `computeScrollHint` tolerance 20px absorbing
  `scrollbar-gutter: stable both-edges`) is the shipped design. The
  false-start → honest-fail → fixed chain is recorded here as
  provenance.
- **Shots** (`assets/story-03-shots/board-hint-*.png`, staged bytes
  eyeballed by the orchestrator, magnified edge crops checked): the
  card text dissolves into the edge band instead of hard-clipping;
  1440 shows no gradient. No two shots byte-identical.
- Typecheck provenance verified stash/pop: 13 errors at HEAD = 13
  dirty, all pre-existing in unrelated files.
- The full close sweep is story 03's captured record (readable run +
  dw capture pair).
