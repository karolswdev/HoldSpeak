# Evidence - HS-135-05

- **Story:** HS-135-05 - The Chair shell
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T01:23:04Z

- **Command:** `bash -c cd /Users/karol/dev/tools/HoldSpeak/web && npx vitest run src/desk/chair/Chair.test.tsx src/desk/store/__tests__/windowSingleInstance.test.ts --reporter=verbose`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 62fcf5e3a01d56dee7bd2e422c87d20b8e5f7ff5

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web

 ✓ src/desk/store/__tests__/windowSingleInstance.test.ts > single-instance-per-surface window rule > opening a zone window twice yields one window, focused 2ms
 ✓ src/desk/store/__tests__/windowSingleInstance.test.ts > single-instance-per-surface window rule > opening a workbench window twice yields one window, focused 1ms
 ✓ src/desk/store/__tests__/windowSingleInstance.test.ts > single-instance-per-surface window rule > opening two DIFFERENT surfaces yields two windows 0ms
 ✓ src/desk/store/__tests__/windowSingleInstance.test.ts > single-instance-per-surface window rule > re-opening an already-open window moves it to the top of panelOrder 0ms
 ✓ src/desk/store/__tests__/windowSingleInstance.test.ts > single-instance-per-surface window rule > pullout: opening same id twice yields one pullout, focused 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > renders four lane slots in the fixed order 15ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > LANE_ORDER is exactly [brief, follow-through, meetings, agents] 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > DEFAULT_MAX_ITEMS is 12 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > maxItems caps the visible rows 68ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > header click fires onOpenInWindow with the surfaceId 4ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > row click fires onOpenInWindow with the item id 7ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > hero slot renders its placeholder 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > shows nothing before 300ms when all lanes are blank 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > shows exactly ONE SurfaceState after 300ms when all lanes are blank 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > does NOT show fallback when at least one lane has content 1ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > clears the fallback when a lane arrives after the timer fired 3ms
 ✓ src/desk/chair/Chair.test.tsx > Chair ember-only (no accent-cool/gradient in chair.css) > chair.css uses neither --accent-cool nor --accent-gradient as CSS values 0ms

 Test Files  2 passed (2)
      Tests  17 passed (17)
   Start at  19:23:05
   Duration  604ms (transform 233ms, setup 80ms, import 331ms, tests 110ms, environment 374ms)
```
