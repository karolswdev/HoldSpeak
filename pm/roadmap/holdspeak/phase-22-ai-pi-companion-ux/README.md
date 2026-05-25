# Phase 22 — AI PI Companion UX

**Status:** in-progress (opened 2026-05-24).

Phase 22 turns AI PI from a working AIPI-Lite bridge into a deliberate physical
companion for HoldSpeak. The core loop is: notice when a local agent or meeting
needs attention, show that state clearly on the device, and let the user answer
or act by voice with explicit gestures.

## Where to look first

- `current-phase-status.md` — goal, scope, story table, risks, and pickup order.
- `story-01-companion-state-model.md` — first story: state model and LCD priority contract.
- `../../../aipi-lite/` — firmware and Python bridge source.
- `../../../docs/AIPI_LITE_DEV_WORKFLOW.md` — unified AIPI setup/test/bridge/firmware workflow.
- `../phase-20-aipi-companion/final-summary.md` — shipped server-side AIPI companion v1.
- `../phase-21-aipi-lite-first-class/final-summary.md` — unified repo handoff.

## Phase boundaries

This phase owns the device-facing product experience: state model, gesture
contract, LCD cadence, bridge polling/display behavior, and live hardware
dogfood. It does not own cross-network reach, autonomous agent replies, or a
hosted assistant service.
