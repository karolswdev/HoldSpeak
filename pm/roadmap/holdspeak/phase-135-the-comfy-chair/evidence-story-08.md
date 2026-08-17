# Evidence - HS-135-08

- **Story:** HS-135-08 - The Follow-Through lane
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T01:32:47Z

- **Command:** `bash -c cd web && npx vitest run src/desk/chair/lanes/FollowThroughLane.test.tsx src/desk/chair/Chair.test.tsx --reporter=verbose`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 7837978b01de9307be4de532a51bd442930e30de

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web

 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > renders overdue items before now items before waiting items 68ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > caps visible items at maxItems 8ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > complete verb fires the done action 11ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > dismiss verb fires the dismiss action 7ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > renders honest empty state when board is empty 3ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > renders four lane slots in the fixed order 17ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > LANE_ORDER is exactly [brief, follow-through, meetings, agents] 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > DEFAULT_MAX_ITEMS is 12 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > maxItems caps the visible rows 69ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > header click fires onOpenInWindow with the surfaceId 4ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > row click fires onOpenInWindow with the item id 7ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > hero slot renders its placeholder 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > shows nothing before 300ms when all lanes are blank 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > shows exactly ONE SurfaceState after 300ms when all lanes are blank 3ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > does NOT show fallback when at least one lane has content 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > clears the fallback when a lane arrives after the timer fired 3ms
 ✓ src/desk/chair/Chair.test.tsx > Chair ember-only (no accent-cool/gradient in chair.css) > chair.css uses neither --accent-cool nor --accent-gradient as CSS values 0ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > header click opens Intelligence on the Follow-Through wing 5ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > newCommitmentVerb forward-compatible slot > prop exists on the component interface (typed) 0ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > newCommitmentVerb forward-compatible slot > renders nothing when null (the default) 4ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > newCommitmentVerb forward-compatible slot > renders the slot content when provided 4ms
 ✓ src/desk/chair/lanes/FollowThroughLane.test.tsx > FollowThroughLane > shows owner initials and age for each item 5ms

 Test Files  2 passed (2)
      Tests  22 passed (22)
   Start at  19:32:47
   Duration  668ms (transform 291ms, setup 87ms, import 477ms, tests 225ms, environment 390ms)
```
