# Context and Needs refinement

Status: built; HOLD FOR SHIP. No staging or commit by this worker.

Worktree: `/Users/karol/dev/tools/wt-desk-navigation-delight-20261015`.
Branch: `feat/desk-navigation-delight-20261015`.
Design: [DESIGN.md](DESIGN.md). Root sent GO after reading the direction at
1440 and 393. Tuesday: the owner can start Context without empty meters and
read the same Needs facts with less space around its phone verbs.

## Change

- `web/src/pages/cores/ConstitutionalContextCore.tsx:159`: revision renders
  only when positive, with the existing optional access retained for a
  missing Context payload; token and character usage render only for a nonempty
  draft. Real unsaved, saved, refusal, over-limit and History states stay on
  the existing paths (`:121`, `:168`). No new product text or state model.
- `web/src/desk/needs/needs.css:68`: the existing narrow Needs verb declares
  `--btn-painted-h: var(--desk-button-hit-size)`. Its painted minimum stays
  44 px. The shared narrow Button formula now reserves 4 px per side, 8 px
  total, instead of 12 px per side, 24 px total. Names, facts, lamps, actions
  and row grammar are unchanged. Global Button CSS was not edited.
- `web/src/pages/cores/__tests__/constitutionalContextSave.test.tsx:15`:
  declared software fixtures of the existing wire contract cover empty to
  nonempty draft, failure and clearing; saved empty draft with a real
  revision; nonempty and empty History selections followed by Cancel;
  a missing Context payload keeps the empty editor mounted.
  `NeedsDrawer.test.tsx` was run without edits.

The change applies Seven Tenets 3 and 5 and UX-CANON A.8 and C (hit ownership).

## Direction canvas

[canvas-context/main.tsx](canvas-context/main.tsx) imports the actual
DeskWindowFrame, Button, Pad/Cycle/Lamp gadgets, SurfaceSection, AppHead,
StatusStrip and NeedsRow source. Samples are declared direction content.

```sh
PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH web/node_modules/.bin/vite --config docs/internal/DESK-NAVIGATION-DELIGHT-2026-10-16/canvas-context/vite.config.mjs
```

Port 4493; routes `?face=context-empty`, `context-saved`, `context-unsaved`,
`context-refused` and `needs`. Root independently captured and read empty
Context and Needs directions in `.tmp/navigation/canvas-context-empty/` and
`.tmp/navigation/canvas-needs/` before GO.

The worker's earlier queued preview also completed under the lock. Its six
shots (empty Context, saved Context and three declared Needs rows at each
width) live in `.tmp/evidence-shots/navigation-context-canvas/`, with
`preview.json` reporting no page errors. These are canvas shots, not proof
of the production desk.

## Initial focused validation

Both commands ran through `.tmp/navigation/locked.py`, which creates and
removes an isolated HOME and acquires `scripts/test_lock.py`. No owner's hub,
DB, Keychain or other machine state was used.

```sh
.venv/bin/python .tmp/navigation/locked.py context-needs-collect --web node_modules/.bin/vitest list src/pages/cores/__tests__/constitutionalContextSave.test.tsx src/desk/needs/__tests__/NeedsDrawer.test.tsx --reporter=json --outputFile /Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/context-needs-collection.json
.venv/bin/python .tmp/navigation/locked.py context-needs-run --web node_modules/.bin/vitest run src/pages/cores/__tests__/constitutionalContextSave.test.tsx src/desk/needs/__tests__/NeedsDrawer.test.tsx --maxWorkers=2 --reporter=json --reporter=default --outputFile /Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/context-needs-run.json
```

Collection exit 0; `.tmp/navigation/context-needs-collect.log` contains 44
test names: 3 Context and 41 Needs. Vitest 4.1.9 `list` emitted text and did
not create the requested collection JSON despite the reporter/output flags;
the text log is the collection evidence.

Run exit 0; `.tmp/navigation/context-needs-run.log` and
`.tmp/navigation/context-needs-run.json` report:

```text
Test Files  2 passed (2)
     Tests  44 passed (44)
  Duration  4.03s
```

Needs emitted React `act` warnings in the existing recording countdown and
refused Cancel cases. Neither file failed. `git diff --check` passed for
the three changed source/test files.

## Regression caught by root's quick check

Root's wider quick run exposed a regression introduced by this worker:
the first positive-revision condition read `ctx.revision` directly where
the original face used optional access. The unchanged
`web/src/desk/__tests__/scrollOwnership.test.tsx` software fixture returns
`{}`; the missing `context` value caused `Cannot read properties of
undefined (reading 'revision')` at `ConstitutionalContextCore.tsx:158`.
The root's failing stack is in `.tmp/navigation/quick/vitest.log:513`.

The first source correction used `(ctx?.revision ?? 0) > 0`, with optional access
also in the rendered revision. No state model or fixture was changed to
hide the failure. The owned Context test file adds the same missing-payload
fixture and waits for the empty editor to mount. Root granted read/run
scope for the existing scroll ownership file; that file was not edited.

The same isolated HOME and machine lock were used for these two commands:

```sh
.venv/bin/python .tmp/navigation/locked.py context-regression-collect --web node_modules/.bin/vitest list src/pages/cores/__tests__/constitutionalContextSave.test.tsx src/desk/__tests__/scrollOwnership.test.tsx --reporter=json --outputFile /Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/context-regression-collection.json
.venv/bin/python .tmp/navigation/locked.py context-regression-run --web node_modules/.bin/vitest run src/pages/cores/__tests__/constitutionalContextSave.test.tsx src/desk/__tests__/scrollOwnership.test.tsx --maxWorkers=2 --reporter=json --reporter=default --outputFile /Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/context-regression-run.json
```

Collection exit 0: `.tmp/navigation/context-regression-collect.log` lists
4 Context and 3 scroll ownership tests. As above, `list` emitted text rather
than the requested JSON file. Run exit 0: the log and JSON at
`.tmp/navigation/context-regression-run.{log,json}` report:

```text
Test Files  2 passed (2)
     Tests  7 passed (7)
  Duration  1.47s
```

No unhandled errors were reported. The unchanged DeskToolInspector scroll
case emitted one React `act` warning. Needs code and CSS did not change
after their initial 41 passing cases and were not rerun for this correction.
Root subsequently reported its complete quick checks passing. The final
source clarification below follows that run.

## Explicit positive revision for the canon scanner

Root reported 3911 web tests, 697 Python tests and 109 sweeps passing after
the missing-payload correction. Its A8 scanner then flagged the nested
JSX expression `(ctx?.revision ?? 0) > 0` as a rendered zero fallback.
That was a mechanical false positive: the condition admitted only positive
revisions, and the four Context cases included empty and missing payloads
with no revision rendered. The scanner and its ceiling were not changed.

The final source derives `const revision = ctx?.revision ?? 0` alongside
`charCount` (`ConstitutionalContextCore.tsx:95`) and renders only
`revision > 0`, with `rev {revision}` (`:159`). This is equivalent null-safe
display logic, expressed without a zero fallback inside JSX. It introduces
no state, product copy or test changes.

Only the same four Context and three existing scroll ownership tests were
collected and run under the isolated locked runner:

```sh
.venv/bin/python .tmp/navigation/locked.py context-positive-collect --web node_modules/.bin/vitest list src/pages/cores/__tests__/constitutionalContextSave.test.tsx src/desk/__tests__/scrollOwnership.test.tsx --reporter=json --outputFile /Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/context-positive-collection.json
.venv/bin/python .tmp/navigation/locked.py context-positive-run --web node_modules/.bin/vitest run src/pages/cores/__tests__/constitutionalContextSave.test.tsx src/desk/__tests__/scrollOwnership.test.tsx --maxWorkers=2 --reporter=json --reporter=default --outputFile /Users/karol/dev/tools/wt-desk-navigation-delight-20261015/.tmp/navigation/context-positive-run.json
```

Collection exit 0: `.tmp/navigation/context-positive-collect.log` contains
seven names. The run log and JSON at
`.tmp/navigation/context-positive-run.{log,json}` report exit 0 and:

```text
Test Files  2 passed (2)
     Tests  7 passed (7)
  Duration  1.45s
```

The run JSON was read: `success=true`, seven passed, zero failed. There
were no unhandled errors; the unchanged DeskToolInspector case emitted one
React `act` warning. Root owns the final scanner verification and release
checks for this final source. Worker edits are frozen; HOLD FOR SHIP.

## Unknown and handover

This worker did not run the production build, quick check, production desk
walk, pointer ownership probe or real Context persistence checks. Root owns
those checks and the production shots at 1440 and 393. No fit or real target
claim is made from jsdom or the direction canvas. No other lane's files were
edited; no staging, commit or merge was performed.
