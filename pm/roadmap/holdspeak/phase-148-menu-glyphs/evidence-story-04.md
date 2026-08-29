# Evidence - HS-148-04

- **Story:** HS-148-04 - Head + dock menus on the registry (AA)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T16:34:56Z

- **Command:** `bash -c (cd web && npx vitest run src/desk/__tests__/windows.test.tsx src/desk/__tests__/windowMenuRegistry.test.tsx src/desk/__tests__/workMenu.test.tsx src/desk/__tests__/verbRegistry.test.ts)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e69f890a522e3185c85f41b3448b4bca5bb9bebc

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  4 passed (4)
      Tests  55 passed (55)
   Start at  10:34:56
   Duration  802ms (transform 433ms, setup 193ms, import 904ms, tests 384ms, environment 842ms)
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder's word: 55 focused re-run and read. The
adapter ruling (WorkMenu over primitives — the story-01 wells, lane
law, and collapse arrive free; the Escape guard survives because it
lives on the window frame's own handler) is correct and the smaller
diff in spirit. The two-window scoping pin is the criterion that
matters — the BACK window's Close closes itself, front untouched.
Registry-label deviation ("Close window" over "Close") ACCEPTED:
labels from the one registry IS the story; the dock's "Restore"
state-toggle exception is honest and pinned. snap-left/snap-right
VerbGlyph kinds staged for story 02's Window-menu wiring. Zero
hardcoded menu labels remain in DeskWindow/Dock (grep pin in the
new windowMenuRegistry test).
