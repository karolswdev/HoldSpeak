# Workbench build handover — 2026-10-15

**FROZEN — HOLD FOR SHIP.** Worktree `wt-account-layout-20261015`, base `3d46ffdc3`. Built the settled Workbench section of DESIGN.md, including root's observed resize repair and Home fact refinement. Root owns browser proof, finished review, quick check, staging and release.

The composer is now a named inset with visible Instruction, auto-growing multiline Pad, the existing grammar mic, P3→P1 priority cycle and primary Add. Enter adds; Shift+Enter inserts a newline. Typed source completion, pasted @, caret focus, full instruction/body, references, reopen, Retry and newer-draft custody keep their existing controllers and writers.

Configuration uses Agent, Engines and Starts when inset groups. A bound agent retains its identity above a folded chooser; the unbound chooser starts open. Mode/Schedule use native library Cycles, including a custom cron; Enabled, event/idle writers, assignments, search and New Agent remain. Skills and workspace use folds. Items keep their existing header/controller/selection and actions, with paper material, sans names and a visible Instruction editor. The single result reader and artifact opener remain.

Empty Runs uses the same known missing-engine fact as the title bar and offers Choose engine. Home retains total ITEMS/PENDING, derives positive DONE/FAILED/IN PROGRESS from actual nonparked item states, and marks failed work for attention. An omitted item list does not imply DONE. Recent run StateChips preserve running and terminal states.

PadGadget adds only protected optional native textarea props/ref and a native ResizeObserver in the existing auto-grow effect. Width changes remeasure height; same-width height feedback is ignored; cleanup disconnects the observer. Root diagnosed and corrected the existing immutable ResizeObserver test stub with exactly `configurable: true` and `writable: true` in `web/src/test/setup.ts`. That root-owned harness change allowed normal mocked-observer proof; no test-only product mechanism remains.

## Focused proof

All commands used `.venv/bin/python .tmp/account-workbench/locked.py <label> --web ./node_modules/.bin/vitest list|run <paths> --maxWorkers=2`, with the helper's isolated HOME, machine-state switches and single-machine lock.

Exact eight-file scope:

```text
src/desk/components/__tests__/workbenchEditing.test.tsx
src/desk/components/__tests__/workbenchOperates.test.tsx
src/desk/components/__tests__/workbenchFrames.test.tsx
src/desk/components/__tests__/workbenchPark.test.tsx
src/desk/components/__tests__/workbenchAutomations.test.tsx
src/desk/components/workbench/WorkbenchRunsWing.test.tsx
src/pages/cores/__tests__/workbenchesHome.test.tsx
src/desk/surface/gadgets.test.tsx
```

- Original collection: `.tmp/account-workbench/workbench_collect_before.log`, exit 0.
- Initial red: `workbench_red.log`, 15 failed / 70 passed, 85 total. Fourteen failures expose the intended face/state gaps; one was the new source-completion test needing a test-local jsdom scrollIntoView shim.
- Valid resize red after root's harness correction: `workbench_resize_red_final.log`, 1 failed / 27 passed. The auto-grow Pad had no observer; the test expected observe(pad) and received zero calls.
- Frozen final run: `workbench_green_frozen.log`, **8 files passed; 87 tests passed**, 9.16 seconds. The final visibility assertion waits for the existing window entrance paint.
- Frozen collection: `workbench_collect_frozen.log`, exit 0; includes the new multiline/source-caret, config/custom-cron, missing-engine, mixed/all-failed Home and protected/ref/resize Pad cases.
- Scoped `git diff --check`: exit 0.

**Unknown here:** production bundle/type check, actual 1440/393 fit, live width-resize behavior, pointer ownership and owner's live judgment. No browser, build, backend, account changes, install, staging or commit was performed in this Workbench lane.

## Mic canon follow-up

Root's quick canon run (`.tmp/account-workbench/quick-final/canon.log`)
found `mic: 0 -> 1` on the new Pad's explicit `mic={false}`. The scanner's
`scan_mic` intentionally treats an opt-out as uncovered even when its
component contains a MicButton. The existing Pad contract permits a host
capture path. This inlet's adjacent grammar MicButton is that path: it
writes the same instruction draft and source references, and its workbench
scope and proposal callbacks retain the single capture authority.

Root accepted and owns one named MIC_ALLOWLIST tuple for
`desk/components/WorkbenchWindow.tsx` and `label="New item instruction"`,
with a focused scanner regression preserving unrelated opt-out failures.
The ceiling and generic scanner rule are unchanged. No Workbench or kit
product code changed in this follow-up.

The new `workbenchEditing.test.tsx` pairing case observes the real MicButton
component and injects a transcript at its existing callback boundary. It
asserts one rendered inlet mic, exact grammar/scope, full typed multiline
and spoken text in the Pad, reference tray and resolver transcript path,
then the exact single Add title/body/priority/grounding payload. It proves
the field pairing and writer; microphone hardware and provider egress are
outside this test.

Only that file was collected and run through the same locked helper:
`workbench_mic_collect.log` confirms **20 collected**;
`workbench_mic_green.log` confirms **20 passed**, 6.07 seconds.
Root owns the scanner/combined quick results and live pairing verification.
**HOLD FOR SHIP.**
