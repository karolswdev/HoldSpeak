# Notifications material build

2026-10-15 · DRAFT · held for SHIP; no staging or commit

Worktree: `/Users/karol/dev/tools/wt-thread-ask-refinement-20261015`.
Base: `9e45b3319`, including urgent dismissal repair PR #1214.

## Built

- `web/src/components/AmbientLayer.tsx`: existing Preview, Qlippy,
  GenerationTheater and QueueHud share one `.ambient-notices` host. Preview
  and useful Qlippy content use SurfaceWell with the complete payload text.
  Removed the mascot plate and generic helper text. Existing Button,
  LampGadget and SurfaceState remain the control/state species. Queue uses
  SurfaceRows/SurfaceRow, omits each zero count, handles retries-only count
  honestly, and opens the existing `/history` route through a library Button.
- `web/src/styles/react-app.css`, ambient selectors only: explicit semantic
  token mapping to Workbench slate/paper/ink, square etched edges, 15px UI
  title / 13px UI payload / 12px mono source and state. One bounded scrolling
  stack clears the measured dock; child notices receive pointer events while
  empty host space passes them through. A named container gives compact
  notices 44px Button targets. Full payloads wrap without truncation.
  The running GenerationTheater lamp uses the existing
  `surface-state-pulse` animation; reduced motion disables it. Preview and
  Qlippy warning lamps stay still.
- `web/src/desk/components/pullout.css`: parked the old 452px Qlippy
  displacement, which no longer applies to a notice in the stack.
- `web/src/components/ambientMaterial.test.tsx`: seven focused rendered
  regression cases. Existing dismissal and doorless test files are unchanged.

No changes to projections, attention cutoff, presence settings, source data,
runtime subscriptions, preview endpoints, aftercare behavior, or mic/provider
effects. The Qlippy present/dismiss writer, exact-row retry, tab cutoff and
storage-failure fallback are unchanged.

## Focused proof

Both commands use `.tmp/thread-ask/locked.py`: isolated HOME, machine lock,
and owner-machine effects disabled by the existing wrapper.

```text
.venv/bin/python .tmp/thread-ask/locked.py notices-list --web ./node_modules/.bin/vitest list src/components/ambientDismiss.test.tsx src/components/ambientDoorless202.test.tsx src/components/ambientMaterial.test.tsx --maxWorkers=2

15 tests collected, exit 0
.tmp/thread-ask/notices-list.log

.venv/bin/python .tmp/thread-ask/locked.py notices-run --web ./node_modules/.bin/vitest run src/components/ambientDismiss.test.tsx src/components/ambientDoorless202.test.tsx src/components/ambientMaterial.test.tsx --maxWorkers=2

 Test Files  3 passed (3)
      Tests  15 passed (15)
   Start at  22:25:46
   Duration  1.55s

.tmp/thread-ask/notices-run.log
```

Counts: ambientDismiss 7; ambientDoorless202 1; ambientMaterial 7. Coverage
includes dictation journal exclusion, visible-row-only dismissal, old backlog
suppression through refresh/remount/module reload, new attention after cutoff,
pending and failed exact-row retry, denied session storage, doorless rendering,
full preview text and safe literal markup, exact Type/Discard writers and
retry, local wake discard, retry-only queue/no zeros/library navigation,
empty queue, full safe learning content and concurrent notice host membership.

`git diff --check` passed for the lane paths. No broader tests or build run by
this worker; the root coordinator owns quick check and actual browser evidence.
The animation addition changed CSS only. The root quick check covers the
stylesheet and actual browser geometry.

## Queue duplication follow-up

Root quick check found the retry-only count twice after expansion. Reproduced
the unchanged `queueHud.test.tsx` failure before fixing product code: 1 failed,
4 passed; `.tmp/thread-ask/notices-queue-red.log`, exit 1. Expanded QueueHud now
shows all nonzero counts in its outer lamp and removes the duplicate inner
count line. The collapsed dominant-count label, queue heading, shared job rows
and Open queue action are retained. No test waiver or test change.

```text
.venv/bin/python .tmp/thread-ask/locked.py notices-queue-list --web ./node_modules/.bin/vitest list src/components/ambientDismiss.test.tsx src/components/ambientDoorless202.test.tsx src/components/ambientMaterial.test.tsx src/components/queueHud.test.tsx --maxWorkers=2

20 tests collected, exit 0
.tmp/thread-ask/notices-queue-list.log

.venv/bin/python .tmp/thread-ask/locked.py notices-queue-red --web ./node_modules/.bin/vitest run src/components/queueHud.test.tsx --maxWorkers=2

 Test Files  1 failed (1)
      Tests  1 failed | 4 passed (5)
.tmp/thread-ask/notices-queue-red.log

.venv/bin/python .tmp/thread-ask/locked.py notices-queue-green --web ./node_modules/.bin/vitest run src/components/ambientDismiss.test.tsx src/components/ambientDoorless202.test.tsx src/components/ambientMaterial.test.tsx src/components/queueHud.test.tsx --maxWorkers=2

 Test Files  4 passed (4)
      Tests  20 passed (20)
   Start at  22:42:13
   Duration  1.95s
.tmp/thread-ask/notices-queue-green.log
```

## Glass and unknowns

Read the sample canvas notice at
`.tmp/thread-ask/canvas-final-1440/notice.png` and
`.tmp/thread-ask/canvas-final-393/notice.png` before implementing.

Actual 1440/393 shots, overlap/scroll checks, pointer ownership and open-sheet
fit are pending the root coordinator's browser pass. Unit rendering does not
prove geometry. `/history` navigation is exercised against a mocked location;
the destination's runtime behavior was not re-walked by this worker. No live
dictation or machine typing occurred. No new backend behavior is claimed.

Tuesday: the owner can read the real payload and choose its existing action;
the browser pass must still establish that all active notices and controls fit.
