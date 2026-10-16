# Search refinement

Direction canvas uses the current Button, StringGadget, palette classes and
material. The two declared sample meetings share title and local day/time;
attendees distinguish them. It is direction, not a product screenshot.

Canvas: `canvas/index.html`, `canvas/main.tsx`, `canvas/canvas.css`.
Start from the worktree:
`/Users/karol/.nvm/versions/node/v22.21.0/bin/node web/node_modules/.bin/vite --config docs/internal/DESK-NAVIGATION-DELIGHT-2026-10-16/canvas/vite.config.mjs`
at `http://127.0.0.1:4492/`; review at 1440 and 393.

Root reviewed the canvas at 1440 and 393, with no browser errors, and gave GO.
Build follows that direction:

- Existing library Close calls the existing close path and returns focus to the
  launcher. Enter on Close keeps its native activation without running a result.
- Meeting rows retain `kind:id`; local day/time uses `wireDayClock` and attendee
  names come from the same meeting row. Missing facts add no empty metadata line.
- The shelf declares the existing named `surface` container. The shared
  StringGadget rule in `surface/gadgets.css` owns its 44 px mic; no mic override.

Focused collection and run used `.tmp/navigation/locked.py`, an isolated HOME and
the machine lock. Scope: `palette.app.test.tsx`, `palette.philo1314.test.tsx`,
`paletteRankHold.test.tsx`, `paletteMemory.test.tsx`, `paletteTwoLine.test.tsx`.

Collection: `.tmp/navigation/search-collected.json`, 68 tests (13 app, 11
philo1314, 6 rank hold, 8 memory, 30 two-line). The six new cases cover Close
pointer/focus/query reset, native keyboard Close without running a selected
result, exact meeting identities with same title/time and distinct attendees,
absent metadata, prompt Save and prompt abandonment. Collection exit 0;
`.tmp/navigation/search-collect.log` acquired the lock after 81 s.

Run: `.tmp/navigation/search-focused.log`, exit 0:
```
Test Files  5 passed (5)
     Tests  68 passed (68)
  Duration  9.94s
```
Scoped `git diff --check` exit 0.

Follow-up: root's quick sweep reported the palette 393 mic target exception as
healed. Removed only that obsolete `KNOWN_REDS` entry from
`tests/e2e/test_desk_sweep.py`; other exceptions and fences remain. This case
now holds the target fence without an exception.

Exact collection, `.tmp/navigation/search-palette393-collect.log`, exit 0:
```
tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[palette-393]
1 test collected in 0.08s
```
Exact run through the isolated HOME and machine lock,
`.tmp/navigation/search-palette393.log`, exit 0:
```
.                                                                        [100%]
1 passed in 11.96s
```
No other sweep cases or broader tests run by this lane.

Unknown: actual product touch ownership, product shots and live interaction are
root's final walk. This lane has not invoked a provider or audio capture.

Status: HOLD FOR SHIP — no staging or commit.
