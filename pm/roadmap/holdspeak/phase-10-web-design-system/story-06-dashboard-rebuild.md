# HS-10-06 - `/` runtime dashboard rebuild

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-03, HS-10-04, HS-10-05
- **Unblocks:** HS-10-13
- **Owner:** unassigned

## Problem

`dashboard.html` is the front door of the product — a 2,800-line single
file with bespoke gradient cards, decorative routing panels, and a
visual hierarchy that does not match the operator's task (start a
meeting → talk → review). The primary start/stop action competes with
secondary status and routing controls. The four meeting states (idle /
active / stopping / stopped) are not visually distinct.

## Scope

- **In:**
  - Replace `holdspeak/static/dashboard.html` with the Astro-built
    output of `web/src/pages/index.astro`.
  - Layout: `AppLayout` shell + a primary action region (start/stop)
    + a transcript region + a side panel for runtime status, intel,
    deferred jobs, and routing.
  - State-driven layout: idle, active, stopping, stopped each have a
    distinct, scannable presentation. The primary action is the most
    visually emphatic element on the page only when an action is
    legitimately the next step.
  - Live transcript stream renders with a scoped Astro island; no JS
    on the page beyond what the live stream and the action buttons
    need.
  - Secondary panels (action items, topics, routing override, deferred
    jobs) use `Panel` + `ListRow` from HS-10-03.
  - All status uses `Pill` and `LocalPill` consistently.
- **Out:**
  - Backend changes — endpoint contracts and websocket payloads stay
    identical.
  - Adding new product features (e.g. new routing modes, new transcript
    actions); this is a presentation rebuild.
  - Mobile-specific gesture support.

## Acceptance Criteria

- [x] `/` renders correctly in idle, active, stopping, and stopped
  states (screenshots of each in the evidence file).
- [x] Start/stop action is the primary visual element exactly when it
  should be (idle → start; active → stop).
- [x] Live transcript continues to update via the same websocket; no
  regression in the existing message contract.
- [x] No inline `<style>` block in the rendered output; all styles
  flow from the Astro pipeline.
- [x] `/_design/components` gallery still renders (no shared-component
  regressions).
- [x] Manual smoke test: start a meeting, see live transcript, stop,
  see summary panels populate.

## Test Plan

- `uv run pytest -q` (excluding `tests/e2e/test_metal.py`) for any
  static-route smoke tests.
- Manual end-to-end: start meeting → speak briefly → stop → review.
- Visual diff against `designer-handoff/screenshots/dashboard-desktop.png`
  documented in evidence (this is a deliberate divergence — capture
  before/after).

## Notes

The rebuild is the user-visible payoff of HS-10-01..05. Resist scope
creep into "while we're in here, let's add X." New product behavior is
out of scope.
