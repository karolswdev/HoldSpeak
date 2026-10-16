# Receipt and policy controls — worker report

DRAFT — HOLD for SHIP. Root GO on the library direction received 2026-10-16.
No staging, commit or push. Root owns actual hub/write/layout observations,
counsel, quick check and delivery.

## Result

- Ask shows `UNGROUNDED` when `groundedMatchCount(receipt)` is zero. Positive
  counts stay `GROUNDED ON N OF M`, where N is matched minus overflow, clamped
  at zero, and M is the receipt's `matchedCount`. Citations and flagged claims
  still render from the original receipt. A context-free answer has no label.
- Resourcefulness places local-data and one-item limits with policy settings;
  selection, pending-work and source-review boundaries with routine choices;
  owner execution beside the existing Save/Pause/armed Enable controls. The
  two routine names are now visible through the library token CheckGadget.
- Enabled policy shows the existing ready state. Progress appears only when
  the stored `nightly_count` is positive, using the stored `nightly_target`.
  Paused policy shows `PAUSED` and `NO RESOURCEFUL WORK STARTS`.
- The existing write callback, `pendingRef` guard, Retry ownership, settings,
  routines payload, execution limits and enable confirmation are unchanged.
  No new state machine, service, route or framework was added.

Product paths:
`web/src/desk/components/AskPanel.tsx`,
`web/src/desk/components/WorkbenchResourceful.tsx`,
`web/src/desk/components/workbench-config.css` (resourcefulness scopes only).

## Canvas

Source: `canvas-receipts/`. Declared samples use the actual component library.
Shots: `.tmp/edges/canvas-receipts-shots/` (parked outside tracked docs).
The zero/positive Ask and enabled/paused policy samples were captured at
1440 and 393; resourcefulness also has scrolled `*-controls.png` views.
These are direction samples, not live hub evidence. Root read the direction
shots before giving GO, including the approved visible routine names.

## Scoped validation

All collection and runs used `.venv/bin/python .tmp/edges/locked.py`, which
sets an isolated HOME and takes the machine test lock.

Collection command:

```text
.venv/bin/python .tmp/edges/locked.py receipts-collect --web npx vitest list src/desk/__tests__/askPanelExperience.test.tsx src/desk/__tests__/askPanelRunsOn.test.tsx src/desk/components/__tests__/workbenchAutomations.test.tsx
```

Read `.tmp/edges/receipts-collect.log`: 30 named cases across the three files
(1 + 20 + 9). New cases include zero, all-overflow and positive receipts;
the receipt denominator differs from the source-reference count; a missing
receipt; zero/positive stored nightly progress while editing; and pending
Retry replay of the original exact policy write.

Run command:

```text
.venv/bin/python .tmp/edges/locked.py receipts-final --web npx vitest run src/desk/__tests__/askPanelExperience.test.tsx src/desk/__tests__/askPanelRunsOn.test.tsx src/desk/components/__tests__/workbenchAutomations.test.tsx
```

Read `.tmp/edges/receipts-final.log`:

```text
Test Files  3 passed (3)
     Tests  30 passed (30)
  Duration  4.32s
```

The original rendering run (`receipts-before.log`) had 7 failed, 23 passed.
One failure was a new test's incorrect `.btn` selector. The first product
run (`receipts-after.log`) had 4 failed, 26 passed: three citation assertions
used that incorrect class, and one token-checkbox test targeted the hidden
input. Tests now query citation button roles and press the visible token
label. No product change was needed for those four test corrections.

No wider test run, owner-state access, provider action or audio action was
performed by this worker. Actual runtime and narrow-layout proof remain
the root's work.

## Final presentation follow-up

Root read the actual receipt tour and approved the revised library canvas
before this follow-up. Named Ask samples and the Save-policy failure sample
are in `.tmp/edges/canvas-receipts-named-shots-v3/` at1440 and393.

- Ask's successful run status now has one home in its existing footer.
  Rounded zero seconds omit the elapsed phrase; positive elapsed seconds
  remain. Loading and failure RunLine behavior and the route receipt keep
  their existing paths. The shared RunLine component was not changed.
- Shared CitationChips reads the current Desk items through `useDesk` and
  the existing qualified `resolveRef`. A cached source shows `Kind · name`;
  an uncached source keeps the pure `sourceLabel(ref)` fallback and remains
  openable. The exact original receipt ref is the title and the opener
  argument. Existing meeting-scope, Thread-fragment and Desk-decision
  grammar supplies the parent lookup identity without changing the opener.
  No fetch, cache or resolver was added.
- Citation CSS changes are confined to `.surface-citations`: names wrap
  and grow in height within the available width. The existing narrow-frame
  target rule still applies.
- Save policy passes `SAVE POLICY` to the existing write channel. Enable
  and Pause retain their labels. Retry still owns the same callback and
  pendingRef guard, with the original settings/routines snapshot.

Additional product paths:
`web/src/desk/surface/citations.tsx` and
`web/src/desk/surface/surface.css` (citation scopes only).

Collected50 named tests across AskRunsOn24, citations16 and Workbench
automations10 in `.tmp/edges/receipts-seams-collect.log`. The pre-change
run had17 failed,33 passed (`receipts-seams-before.log`). The final scoped
run (`receipts-seams-after.log`) was:

```text
Test Files  3 passed (3)
     Tests  50 passed (50)
  Duration  5.05s
```

The cases cover qualified same-ID kind collisions, exact scoped opener
refs, unknown/plain fallback behavior, names arriving in the Desk cache,
full long titles, zero/positive elapsed footer status, route receipts,
and distinct Save/Enable failure labels with exact Retry replay. The
long-title unit case proves text/identity preservation; actual geometry
is covered by the runtime tour below. Owned diffs passed `git diff --check`.

## Final isolated runtime proof

Root subsequently delegated this scoped runtime tour to the worker. Product
source stayed frozen; the root retained the complete quick check and release.
Both runs used `.tmp/edges/receipt_tour.py` through the same isolated-HOME
machine-lock helper. The worker read both observations and all16 state PNGs.

| Width | Served build | Output under `.tmp/edges/` | Result |
| --- | --- | --- | --- |
| 1440x900 | `7210f8622d069ea6`, built14:18:30.746Z | `receipt-frozen-1440/` | captured8 states |
| 393x852 | `52f6ff3c43024642`, built14:25:36.535Z | `receipt-frozen-393-current/` | captured8 states |

The root rebuilt after the related test adjustment, changing build metadata
without changing frozen product source. A preliminary phone attempt in
`receipt-frozen-393/` stopped at its expected-build assertion before UI
actions (zero states). It is preserved separately. The successful phone
run records the served build honestly; the desktop run was not repeated
solely for changed test/build metadata.

Both successful observations report no page errors and no horizontal
document overflow. Fresh Hub DBs are under each output's `home/`; native
state is off, the scheduler is off and the engine mode is none. The rig's
HTTP writers created the recipe, Workbench, ordinary pending item and Notes.

Real Workbench policy behavior at both widths:

- Configure → Idle used the actual CycleGadget popup and pointer controls.
  Both routine names were visible on their library choices.
- The first Enable press armed `RUN AS OWNER?`, sent no policy PUT and left
  GET disabled. The confirming press wrote31 idle minutes,5 cooldown hours,
  target3, overnight21:00–08:00 and only `loose_ideas`; the real returned
  policy and GET matched every setting and routine.
- A browser-held Save PUT was refused with declared HTTP503. Save became
  busy/disabled, and the actual receipt said `SAVE POLICY FAILED · HTTP 503`
  with Retry. Retry replayed the original target4 payload after a newer
  target5 draft was entered. A duplicate pending Retry sent no new PUT.
  The held Retry was forwarded to the real writer; response and GET stored
  the original target4 and unchanged remaining settings/routines.
- Pause wrote disabled with target4 and the same remaining policy. Real
  response and GET confirmed it. The ordinary item remained pending with
  its original body, and resourceful history stayed empty. This proves
  policy persistence/recovery, not maintenance execution.

Declared Ask transport replay at both widths:

- Meta+i opened the actual Ask panel. One response had zero matches; the
  other had matched5/overflow2 and two real Note refs. No inference ran.
- The face showed `UNGROUNDED` and `GROUNDED ON 3 OF 5`, kept the flagged
  claim, and kept Keep visible/enabled. Both completed answers had exactly
  the `ANSWERED` footer status, no inline success RunLine and no zero-second
  phrase. The positive-duration path is covered by the focused unit cases.
- Cached citations showed `Note · Release checks` and the full long
  architecture title. Their original refs stayed in the titles. Text
  ranges fit within both citation boxes, with scrollWidth equal to
  clientWidth. At393 the long citation was245x54.640625px; its text range
  was205.921875x50.09375px, wholly within that box.

Each successful width recorded14 control probes and126 center/edge/corner
ownership points, all owned by the intended control after real pointer
moves. Every probed393 target was at least44x44, including the mode/Idle
choice, routine tokens, Enable, Save, Pause, Retry, Ask, Keep and citations.
Assertions apply to those controls in those states, not every app surface.

State names at each width: `resourceful-paused`, `resourceful-enable-armed`,
`resourceful-enabled-real`, `resourceful-save-pending`,
`resourceful-save-refused`, `resourceful-paused-real`, `ask-zero`,
`ask-positive`. Command tails are `receipts-frozen-1440.log` and
`receipts-frozen-393-current.log` under `.tmp/edges/`.
