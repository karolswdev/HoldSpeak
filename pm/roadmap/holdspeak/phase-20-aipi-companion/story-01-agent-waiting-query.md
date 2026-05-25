# HS-20-01 — Agent Waiting Query Surface

- **Project:** holdspeak
- **Phase:** 20
- **Status:** done
- **Depends on:** HS-18 agent hooks, HS-17 device query substrate
- **Unblocks:** HS-20-02
- **Owner:** unassigned

## Problem

AIPI can already query meeting state, and HoldSpeak can already detect when Claude/Codex is waiting for a user response. Those two systems are not connected. The device needs a small, stable way to ask HoldSpeak whether an agent is waiting and what the latest captured question is.

## Scope

### In

- New device query names for agent waiting state.
- LCD-safe formatting of the latest captured Claude/Codex question.
- Protocol documentation and focused tests.

### Out

- Sending a voice reply back to the agent.
- Proactive push notifications on every hook event.
- Cross-network transport.

## Acceptance Criteria

- [x] `query:agent_status` returns a `status` frame summarizing the waiting agent or `No agent waiting`.
- [x] `query:agent_question` returns the latest captured question only or `No agent waiting`.
- [x] Responses are bounded for LCD display.
- [x] Unknown query behavior remains unchanged.
- [x] Unit/integration coverage exists.

## Test Plan

- Unit tests for agent-state to device-status formatting.
- WebSocket integration test for the new query path.
- Focused agent/device tests.

## Notes

- 2026-05-24 closeout: implemented via existing `query` / `status` frames; no new device envelope. See [evidence-story-01.md](./evidence-story-01.md).
