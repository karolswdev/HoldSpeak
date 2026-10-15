# Editor repair build — 2026-10-15

FOCUSED GREEN — SOURCE FROZEN — HOLD FOR SHIP. Owned paths and design:
`docs/internal/VISUAL-REFINEMENT-2026-10-15/DESIGN.md`.

Root explicitly settled its actual-component Inspector, Recipe, and Question
1440/393 canvases before product edits. Root's corrected Inspector footer
composition is used: `SurfaceFooter` inside the existing `desk-surface-foot`
sibling outside the scrolling body. Canvas inspection is root's claim; this
lane did not run a browser or view runtime shots.

## Changes

- `web/src/desk/components/DeskToolInspector.tsx`: the shared frame owns
  geometry and fits content. Integration state/destination, exact bound
  source, and preview lead; one Details disclosure retains technical facts.
  All project/target/integration verbs use library Button. Footer owns
  egress, actual outcome and the existing Post/Approve/Reject/Retry/Return/
  Configure actions. Executed is success, refused warning, rejected idle,
  failed failure. The proposal/source/decision handlers and immediate
  execution behavior are retained. Known URLs use canonical host extraction;
  opaque destination labels remain remote. A changed selection cannot replace
  the proposal's bound source text with another selected object's text.
- `web/src/desk/components/chrome-menus.css`: Inspector selectors now own
  only content composition. Removed its second fixed panel geometry, border,
  shadow, custom button skin, nested plated fact/receipt blocks, inner source
  scroll, and universal green receipt wash. Other chrome selectors are not
  part of this lane.
- `web/src/desk/pullouts/ThreadPullout.tsx` and `thread-pullout.css`:
  questions use one inset Answer group, labeled rows and Check/String/Cycle
  gadgets. Submit/Decline stay together in that group's local action slot.
  Schema-provided question content, field names, initial blank number,
  number conversion, boolean values, enum string values, call ID and handlers
  are retained. Private input/checkbox well styling is removed; neighboring
  Thread message, tool decision and disclosure flows are unchanged.
- `web/src/desk/pullouts/editors/RecipeEditor.tsx`: populated values have
  visible row/group labels, Instructions owns one sheet, Advanced uses the
  reversible library disclosure. The existing writer, avatar, append dictation,
  tool splitting, whitespace and host footer are retained.

Test changes are confined to `DeskToolInspector.test.tsx`,
`askai.app.test.tsx`, and `pullouts/editors/editorRepair.test.tsx`.
`ThreadToolRows.test.tsx` was run unchanged. No shared kit, Workbench,
Calendar, API or schema-engine changes belong to this lane.

## Focused checks

Every command below runs through `.tmp/visual-refinement/locked.py --web`,
which supplies an isolated HOME and Node 22.21.0, and serializes the run
through `scripts/test_lock.py`. No browser, build, install, whole suite,
staging, or commit is part of this lane.

Collection before additions:

```text
python3 .tmp/visual-refinement/locked.py editors-collect --web node node_modules/vitest/vitest.mjs list src/desk/components/DeskToolInspector.test.tsx src/desk/__tests__/askai.app.test.tsx src/desk/__tests__/ThreadToolRows.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx
exit 0
log: .tmp/visual-refinement/editors-collect.log
```

Added regressions cover the Inspector's executed/failed/rejected/refused
outcome tones, library actions, footer custody, opaque nonlocal destination,
and failure recovery; mixed string/number/boolean/enum answer submission;
populated Recipe labels, reversible Advanced, tool splitting, preserved
whitespace, and writer flush. Existing tests cover source binding, immediate
execution without approval, question visibility alongside collapsed work,
and the shared editor writer's failure/retry behavior.

Red against the unchanged product:

```text
python3 .tmp/visual-refinement/locked.py editors-red --web node node_modules/vitest/vitest.mjs run src/desk/components/DeskToolInspector.test.tsx src/desk/__tests__/askai.app.test.tsx src/desk/__tests__/ThreadToolRows.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx --maxWorkers=2
exit 1
Test Files  3 failed | 1 passed (4)
Tests       6 failed | 70 passed (76)
Duration    2.70s
log: .tmp/visual-refinement/editors-red.log
```

The six failures are the four Inspector outcome cases, the mixed-type
question case, and the Recipe control-sheet case. Existing ThreadToolRows
checks passed.

First implementation run: `.tmp/visual-refinement/editors-first.log` reports
74 passed / 2 failed. All new regressions passed. Two older Inspector
assertions needed the settled face's semantics: query the destination in the
lead rather than assume one occurrence after footer egress is added, and
query the actual Executed status chip rather than former receipt prose.
Those assertions still protect source binding and the immediate-execution
path. A known-host regression and an actual failed-Retry round trip were
added before the final run.

Final collection:

```text
python3 .tmp/visual-refinement/locked.py editors-collect-final --web node node_modules/vitest/vitest.mjs list src/desk/components/DeskToolInspector.test.tsx src/desk/__tests__/askai.app.test.tsx src/desk/__tests__/ThreadToolRows.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx
exit 0
77 test names collected
log: .tmp/visual-refinement/editors-collect-final.log

DeskToolInspector.test.tsx > keeps executed undefined receipts honest in the library footer
DeskToolInspector.test.tsx > keeps failed undefined receipts honest in the library footer
DeskToolInspector.test.tsx > keeps rejected undefined receipts honest in the library footer
DeskToolInspector.test.tsx > keeps proposed refused receipts honest in the library footer
DeskToolInspector.test.tsx > names a known endpoint host at the action without exposing its path
DeskToolInspector.test.tsx > binds an Integration proposal and Receipt to the exact selected source
DeskToolInspector.test.tsx > renders YOLO posture authority and the immediate Receipt without an approval prompt
editorRepair.test.tsx > names populated values, folds advanced fields both ways and preserves its writer
askai.app.test.tsx > submits typed string, number, boolean and enum answers from one named library sheet
```

Final focused run:

```text
python3 .tmp/visual-refinement/locked.py editors-green --web node node_modules/vitest/vitest.mjs run src/desk/components/DeskToolInspector.test.tsx src/desk/__tests__/askai.app.test.tsx src/desk/__tests__/ThreadToolRows.test.tsx src/desk/pullouts/editors/editorRepair.test.tsx --maxWorkers=2
exit 0
Test Files  4 passed (4)
Tests       77 passed (77)
Duration    3.00s
log: .tmp/visual-refinement/editors-green.log
```

An explicit-path `git diff --check` on the eight owned changed source/test
files exited 0. Source was frozen at this checkpoint; root subsequently
authorized the two review corrections recorded below.

## Review corrections and final Inspector recheck

Root's review found that using the egress host as the leading destination
hid a GitHub target's exact `owner/repo`. The lead now shows the original
configured destination, while the footer continues to show its canonical
host/scope. Disabled integrations omit the placeholder destination instead
of repeating `Not configured` beside the state chip. Two new regressions
failed against the prior source (2 failed / 8 passed,
`.tmp/visual-refinement/editors-target-red.log`, 2.17s), then passed after the
single JSX correction (10/10, `editors-target-green.log`, 2.19s).

Root's production walk then found that removing the entire old host rule
also removed necessary structural positioning: `DeskWindowFrame` supplies
the rect values but does not supply `position` or flex layout. The Inspector
host now has exactly `position: fixed`, `display: flex`,
`flex-direction: column`, and `overflow: hidden`. Old top/right/bottom,
width, z-index, frame outline, fill and shadow remain removed. The native
`is-card` modifier was not added because it depends on the legacy pullout
class, whose default geometry and skin are unnecessary here; `fitContent`
already supplies the unarranged height cap. One raw-CSS regression in the
same Inspector test protects structural positioning and the absence of a
second geometry/material definition. It is source proof, not a substitute
for root's live shot.

Only `DeskToolInspector.tsx`, its test, and the Inspector host selector in
`chrome-menus.css` changed in this correction round. The Thread and Recipe
source remained frozen.

```text
python3 .tmp/visual-refinement/locked.py editors-recheck-collect --web node node_modules/vitest/vitest.mjs list src/desk/components/DeskToolInspector.test.tsx
exit 0
11 test names collected
log: .tmp/visual-refinement/editors-recheck-collect.log

DeskToolInspector.test.tsx > keeps the Inspector in the desk plane while the shared frame owns geometry and material
DeskToolInspector.test.tsx > keeps the exact GitHub repository visible before creating an issue and its host in the footer
DeskToolInspector.test.tsx > names an unconfigured integration once without repeating a placeholder destination

python3 .tmp/visual-refinement/locked.py editors-recheck-green --web node node_modules/vitest/vitest.mjs run src/desk/components/DeskToolInspector.test.tsx --maxWorkers=2
exit 0
Test Files  1 passed (1)
Tests       11 passed (11)
Duration    2.20s
log: .tmp/visual-refinement/editors-recheck-green.log
```

An explicit-path `git diff --check` on these three files exited 0. Source
is frozen again for root's live and reviewer recheck. No additional suite,
build, browser, install, stage or commit was run in this correction round.

## Remaining verification

Root owns the production build, combined quick check, isolated live walks,
1440/393 screenshots, and independent review. This lane cannot claim runtime
layout, click/hit ownership, contrast, actual external sends or native voice
behavior. Root owns live verification that the restored structural shell
keeps the Inspector visible and its controls clear of the dock at both widths.
