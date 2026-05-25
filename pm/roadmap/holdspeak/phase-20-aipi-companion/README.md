# Phase 20 — AIPI Companion

**Status:** in-progress (opened 2026-05-24).

Phase 20 turns AIPI-Lite from a remote microphone/LCD into a same-LAN physical companion for HoldSpeak's local work loop. The first product target is coding-agent assistance: Claude/Codex hooks tell HoldSpeak when an agent is waiting, and AIPI can display that state and help the user answer by voice.

## Where to look first

- `current-phase-status.md` — goal, scope, story table, risks, and pickup order.
- `story-01-agent-waiting-query.md` — current first slice: device query access to captured agent-waiting state.
- `holdspeak/agent_context.py` — local Claude/Codex hook registry.
- `holdspeak/agent_device.py` — device-facing summaries of captured agent state.
- `holdspeak/web_runtime.py` — runtime query handler that bridges device queries to agent state.
- `docs/DEVICE_PROTOCOL.md` — device wire contract.

## Phase boundaries

This phase owns same-LAN physical companion UX: agent-waiting status, voice-reply routing, device gestures, and debug visibility. It does not own cross-network reach, hosted assistant orchestration, or autonomous agent actions.
