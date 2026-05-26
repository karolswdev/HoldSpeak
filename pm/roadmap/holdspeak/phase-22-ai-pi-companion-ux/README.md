# Phase 22 — AI PI Companion UX

**Status:** done (opened 2026-05-24; closed 2026-05-25).

Phase 22 turns AI PI from a working AIPI-Lite bridge into a deliberate physical
companion for HoldSpeak. The core loop is: notice when a local agent or meeting
needs attention, show that state clearly on the device, and let the user answer
or act by voice with explicit gestures.

## Where to look first

- `current-phase-status.md` — goal, scope, story table, risks, and pickup order.
- `companion-state-model.md` — HS-22-01 state names, LCD zones, priority rules, and stale clearing.
- `gesture-contract.md` — HS-22-02 physical gesture meanings and remote simulation names.
- `story-01-companion-state-model.md` — first story: state model and LCD priority contract.
- `story-02-gesture-contract.md` — gesture contract for agent and meeting actions.
- `story-03-bridge-companion-polling.md` — bridge polling/display wiring.
- `story-04-agent-voice-reply-dogfood.md` — current hardware dogfood story.
- `story-05-tmux-agent-reply-transport.md` — tmux-pane delivery for agent replies.
- `story-06-phase-exit-and-product-handoff.md` — phase closeout and Phase 23 handoff.
- `final-summary.md` — closed-phase summary and next-phase guidance.
- `../../../aipi-lite/` — firmware and Python bridge source.
- `../../../docs/AIPI_LITE_DEV_WORKFLOW.md` — unified AIPI setup/test/bridge/firmware workflow.
- `../phase-20-aipi-companion/final-summary.md` — shipped server-side AIPI companion v1.
- `../phase-21-aipi-lite-first-class/final-summary.md` — unified repo handoff.

## Phase boundaries

This phase owns the device-facing product experience: state model, gesture
contract, LCD cadence, bridge polling/display behavior, and live hardware
dogfood. It does not own cross-network reach, autonomous agent replies, or a
hosted assistant service.
