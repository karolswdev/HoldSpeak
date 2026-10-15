# Workbench repair build — 2026-10-15

BUILT — focused checks green; frozen, HOLD FOR SHIP.
Design: `DESIGN.md`, Workbench reader and read failure. Root settled the
native Workbench canvas at 1440 and 393 before product edits. The error
and output artboards are specimens; Runs and Items remain separate wings.

## Delivered

- One native inset result sheet uses the existing GadgetGroup, Material,
  StateChip, EgressChip and library Buttons. Copy stays on the result;
  Open artifact calls the existing `openSourceRef("artifact:<id>")` path.
  It no longer appends duplicate output, a raw ID or duplicate title.
  Review needed is the display label; no stored artifact value changed.
- The Workbench body owns reading scroll. Item list, result, Runs,
  Memory and configuration no longer have their own scrolling cap.
  Result facts can wrap. The standalone footer now has the existing
  `desk-surface-foot` host so its container rules can apply at 393.
- Runs and Memory consume the existing hook's loading/error/refresh.
  First-load failures show a named error and Try again. Empty states and
  their Run/Bind action appear only after a successful read. Known rows
  remain visible through refresh failure. Retry rereads its own resource.
- `WorkbenchItemRecord.to_dict` now includes the existing boolean
  `mint_attempted`. No runner, inference, schema or route behavior changed.
  A regression drives the production runner to actual item/artifact
  publication and checks pending/complete detail serialization.

Existing item body debounce, inlet draft custody, Copy/Re-run, retry mint,
legacy Keep, Dismiss, Park/Clear done/Restore and footer receipt priority
remain in their existing action paths. Focused checks cover body/inlet
custody, refused Re-run/retry mint/Dismiss, Park/Restore and run bus states.
The artifact-opening test checks exact dispatch, retained item actions and
one result presentation; it does not prove clipboard or legacy Keep I/O.

## Owned paths

Product: `web/src/desk/components/WorkbenchWindow.tsx`,
`web/src/desk/components/workbench-config.css`,
`web/src/desk/components/workbench/WorkbenchRunsWing.tsx`, and the one
`WorkbenchItemRecord.to_dict` line in `holdspeak/db/models/__init__.py`.

Tests edited: `WorkbenchRunsWing.test.tsx`,
`web/src/desk/components/__tests__/workbenchEditing.test.tsx`,
`tests/unit/test_workbench_runner_migration.py`.
Existing writeReceipts, workbenchPark and workbenchFrames tests were run
without editing them. Sibling product/test/canon files were not edited.

## Focused proof

All runs use root's `.tmp/visual-refinement/locked.py`, which supplies an
isolated HOME, Node 22.21.0 and the machine test lock. No browser, build,
install, whole suite, staging or commit ran in this lane.

Web file set (from `web/`):

```text
src/desk/components/workbench/WorkbenchRunsWing.test.tsx
src/desk/components/__tests__/workbenchEditing.test.tsx
src/desk/components/__tests__/writeReceipts.test.tsx
src/desk/components/__tests__/workbenchPark.test.tsx
src/desk/components/__tests__/workbenchFrames.test.tsx
```

Collection: `.venv/bin/python .tmp/visual-refinement/locked.py
work-views-web-final-collect --web node node_modules/vitest/vitest.mjs
list <web file set>`, exit 0.
Log: `.tmp/visual-refinement/work-views-web-final-collect.log`.
New check names present in the collection:

```text
WorkbenchRunsWing > retries a failed read without offering an empty-ledger run
WorkbenchRunsWing > keeps known runs readable when a refresh fails
WorkbenchRunsWing > waits for a first read before declaring the ledger empty
Workbench independent reads > names a failed 'Runs' read and retries only that read
Workbench independent reads > names a failed 'Memory' read and retries only that read
Workbench independent reads > keeps known memory and its disclosure while a refresh fails, then retries the read
Workbench independent reads > opens the linked artifact without repeating its result in the item
```

Red before product edits: six new checks failed, 36 existing checks passed
across the five files. The failures were the three RunsWing states, the
two failed resource reads and artifact dispatch. Log:
`.tmp/visual-refinement/work-views-web-red.log`. The warm Memory check was
added afterward and is not claimed as part of this red run.

Final command: `.venv/bin/python .tmp/visual-refinement/locked.py
work-views-web-final --web node node_modules/vitest/vitest.mjs run
<web file set> --maxWorkers=2`.

```text
exit 0
Test Files  5 passed (5)
Tests       43 passed (43)
Duration    5.99s
```

Log: `.tmp/visual-refinement/work-views-web-final.log`.
The final first-read cases replay root's actual isolated detail and empty
Runs/Memory responses, embedded in the owned test without a scratch-file
dependency. Source capture: `.tmp/visual-refinement/producer-wire/workbench.json`.
It was captured during repair from the baseline walk's stored rows;
it is not described as a before-fix wire fixture. Failure injection uses
503 responses. The warm Memory and linked artifact cases use explicit
existing contract data; real publication/serialization is proved below.

Python file and command were reported to root before running, then
explicitly approved. Collection command:

```text
.venv/bin/python .tmp/visual-refinement/locked.py work-views-python-collect uv run pytest --collect-only -q tests/unit/test_workbench_runner_migration.py
tests/unit/test_workbench_runner_migration.py::test_item_wire_retains_mint_attempted_from_real_publication
21 tests collected in 0.14s
exit 0
```

Log: `.tmp/visual-refinement/work-views-python-collect.log`.
The new test failed before the one-line serialization fix with
`KeyError: 'mint_attempted'`, after confirming the production runner had
stored the completed item, true mint fact and real artifact. Log:
`.tmp/visual-refinement/work-views-python-red.log`.

```text
.venv/bin/python .tmp/visual-refinement/locked.py work-views-python-green uv run pytest -q -n 8 --dist worksteal tests/unit/test_workbench_runner_migration.py
.....................                                                    [100%]
21 passed in 3.12s
exit 0
```

Log: `.tmp/visual-refinement/work-views-python-green.log`.
`git diff --check` on the seven owned product/test paths passed.

## Root verification still due

No live rendering claim is made by this lane. Root owns the combined
quick check and actual production shots/walk at 1440 and 393: long result
scroll, artifact arrival, failed Runs/Memory → successful read, retained
item draft and footer fit/target ownership. No actual provider execution
or failed-mint recovery run is claimed. The producer-backed regression
proves the existing stored fact reaches the wire.

## Typecheck correction

Root's subsequent TypeScript check found five unsupported `exact: true`
options on Testing Library `getByRole`/`queryByRole` calls in the new
artifact-opening test. The string `name` already gives exact matching.
Removed only those five options; the valid `queryByText` option remains.
Vitest's earlier green did not type-check these options. Product code
stayed frozen. Root owns the TypeScript recheck and build.

```text
.venv/bin/python .tmp/visual-refinement/locked.py work-views-typefix --web node node_modules/vitest/vitest.mjs run src/desk/components/__tests__/workbenchEditing.test.tsx --maxWorkers=2
exit 0
Test Files  1 passed (1)
Tests       16 passed (16)
Duration    5.46s
```

Log: `.tmp/visual-refinement/work-views-typefix.log`.
