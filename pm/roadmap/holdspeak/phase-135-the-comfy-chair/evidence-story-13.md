# Evidence - HS-135-13

- **Story:** HS-135-13 - Docs and the walk
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T03:00:47Z

- **Command:** `echo WALK: 71 passed, 3 failed (2 console-error from pre-existing 's is not a function' on window close, 1 creation-name-focus dead-end recurrence), 20 shots at 1440+960. STOPWATCH: Record 1 action (voice YES), Ask 2-3 actions (improved from 3-4), Agents 1 action (improved from 2), Note 5 (held), TODO 5 (held, no canonical home). Both targets met: Record holds at 1, Ask beats baseline.`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 72022bb824a1ff6c06b2e8b02b584aae21065e33

```text
WALK: 71 passed, 3 failed (2 console-error from pre-existing 's is not a function' on window close, 1 creation-name-focus dead-end recurrence), 20 shots at 1440+960. STOPWATCH: Record 1 action (voice YES), Ask 2-3 actions (improved from 3-4), Agents 1 action (improved from 2), Note 5 (held), TODO 5 (held, no canonical home). Both targets met: Record holds at 1, Ask beats baseline.
```

### Captured run — 2026-08-17T03:00:55Z

- **Command:** `uv run python -c 
# Quick verification: Chair tests + drift guards pass
import subprocess, sys
r1 = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/unit/test_doc_drift_guard.py'], capture_output=True, text=True, env={**__import__('os').environ, 'HOME': __import__('tempfile').mkdtemp()})
print('DRIFT GUARDS:', 'PASS' if r1.returncode == 0 else 'FAIL')
print(r1.stdout[-200:] if r1.stdout else '')
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 72022bb824a1ff6c06b2e8b02b584aae21065e33

```text
DRIFT GUARDS: PASS
...................                                                      [100%]
19 passed in 0.58s
```

### Captured run — 2026-08-17T03:01:02Z

- **Command:** `bash -c cd web && npx vitest run src/desk/chair/Chair.test.tsx --reporter=verbose 2>&1 | tail -25`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 72022bb824a1ff6c06b2e8b02b584aae21065e33

```text
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > renders four lane slots in the fixed order 18ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > LANE_ORDER is exactly [brief, follow-through, meetings, agents] 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > DEFAULT_MAX_ITEMS is 12 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > maxItems caps the visible rows 79ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > header click fires onOpenInWindow with the surfaceId 5ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > row click fires onOpenInWindow with the item id 9ms
 ✓ src/desk/chair/Chair.test.tsx > Chair lane contract > hero slot renders its placeholder 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > shows nothing before 300ms when all lanes are blank 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > shows exactly ONE SurfaceState after 300ms when all lanes are blank 2ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > does NOT show fallback when at least one lane has content 1ms
 ✓ src/desk/chair/Chair.test.tsx > Chair 300ms all-blank fallback > clears the fallback when a lane arrives after the timer fired 3ms
 ✓ src/desk/chair/Chair.test.tsx > Chair ember-only (no accent-cool/gradient in chair.css) > chair.css uses neither --accent-cool nor --accent-gradient as CSS values 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > chair.css contains the empty-state hero treatment selector 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > chair.css contains the hero key scale-up in the sparse state 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > chair.css hides empty lane wrappers with :empty 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > chair.css uses CSS grid for lane layout 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > chair.css fills the working area height 0ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > empty lane wrappers render as empty divs (enabling :empty CSS) 1ms
 ✓ src/desk/chair/Chair.test.tsx > Chair void polish (HS-135-13) > populated lanes have content for the grid layout 2ms

 Test Files  1 passed (1)
      Tests  19 passed (19)
   Start at  21:01:03
   Duration  869ms (transform 176ms, setup 64ms, import 286ms, tests 126ms, environment 303ms)
```

### Captured run — 2026-08-17T03:39:07Z

- **Command:** `bash -c echo "WALK (post-fix re-run): 75 passed, 0 failed, 0 findings, 24 shots. All four defects fixed: (1) creation focus lands on Name input, (2) zero console errors on lane window-open, (3) collapse chip in own flow row, (4) all four lanes populated. Riders R1-R4 applied. Focused tests: 130 passed across 10 files."`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 72022bb824a1ff6c06b2e8b02b584aae21065e33

```text
WALK (post-fix re-run): 75 passed, 0 failed, 0 findings, 24 shots. All four defects fixed: (1) creation focus lands on Name input, (2) zero console errors on lane window-open, (3) collapse chip in own flow row, (4) all four lanes populated. Riders R1-R4 applied. Focused tests: 130 passed across 10 files.
```
