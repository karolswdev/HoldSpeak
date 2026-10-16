# Presence build handover

2026-10-16 — HOLD for SHIP. Owned product and test source are frozen.

## Scope

- `web/src/pages/PresencePage.tsx`: small standalone Workbench panel, one
  SurfaceSection Runtime caption, library Desk Button, and block LampGadget.
- Only the Presence rules in `web/src/styles/react-app.css`: local Workbench
  token mapping, square paper/steel wells and bevels, complete activity wrapping.
- `web/src/pages/__tests__/PresencePage.test.tsx`: 10 focused cases.

The existing `runtime_activity` subscription and label, tone and lamp-on
expressions are unchanged. The activity retains a polite status live region.
Desk returns through the existing router and preserves the exact current query.
No runtime protocol, producer, global gadget, or component API changed.

## Canvas before build

Root read all eight declared-sample PNGs (Ready, long activity, Connecting,
activity error; 1440 and 393) and approved the direction. The phone condition
was confirmed before implementation: the Desk Button's 46.8125 × 44 px target
owned all nine pointer samples in each state. The painted plate is 28 px high.
The long phone activity wraps within the 361 px panel; document width is 393 px.

Source: `canvas-presence/`. PNGs and geometry:
`.tmp/entry/canvas-presence-shots/`, including `facts.json`. This handover
records the later GO and supersedes the canvas README's initial draft status.
Canvas samples do not establish runtime producer execution.

## Focused proof

Collected before running, through the isolated HOME and machine-lock helper:

```sh
.venv/bin/python .tmp/entry/locked.py presence-collect --web npx vitest list src/pages/__tests__/PresencePage.test.tsx
.venv/bin/python .tmp/entry/locked.py presence-run --web npx vitest run src/pages/__tests__/PresencePage.test.tsx
```

Read `.tmp/entry/presence-collect.log`: 10 names covering composition and live
region, four existing connection states, connected/offline activity errors,
complete long labels, and pointer/keyboard returns with the exact query.

Read `.tmp/entry/presence-run.log`, exit 0:

```text
Test Files  1 passed (1)
     Tests  10 passed (10)
  Duration  976ms
```

The tests mock runtime hooks. They verify presentation and navigation against
the declared inputs, not live transport. Scoped `git diff --check` is clean.

## Remaining ownership

Root owns the final build, full quick check, actual 1440/393 runtime observations,
and release. No further product amendments, build, staging, commit or push were
performed by this lane after the focused run.
