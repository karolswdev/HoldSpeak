# HS-23-06 Evidence — Live Dogfood and Closeout

**Date:** 2026-05-26.
**Story:** [story-06-live-dogfood-and-closeout.md](./story-06-live-dogfood-and-closeout.md).

## Hardware Setup

- Web runtime tmux session: `hs23-web`.
- Bridge tmux session: `hs23-bridge`.
- Bridge URL: `http://127.0.0.1:34999`.
- Device: `aipi-green.local` (`192.168.1.19`).

## Observations So Far

- Bridge connected to the physical AI PI and repainted link/status.
- Single-tap preview emitted `agent_question` and painted the selected
  question.
- Double-tap emitted `agent_next` and cycled between waiting sessions.
- Dogfood exposed a middle-display race: reply transcript flashes could be
  overwritten by companion agent polling before the TTL expired.
- Voice reply into the tmux-backed Claude pane delivered successfully, and the
  bridge continued to receive post-restart reply audio from AI PI.

## Display-Hold Fix

`HoldSpeakLeg` now notifies the companion poller when a middle-zone status
flash has a TTL. `CompanionStatusPoller` defers middle-zone companion paints and
clears until that TTL expires, then forces one repaint so the waiting-agent
screen returns cleanly.

Live validation confirmed the same mechanism on both paths:

- An `agent_next` status flash at `04:44:15` was followed by the next companion
  waiting repaint at `04:44:22`, rather than the previous roughly one-second
  overwrite.
- A reply transcript flash at `04:46:10.730` was followed by the next companion
  waiting repaint at `04:46:16.472`.
- A second reply transcript flash at `04:46:30.600` was followed by the next
  companion waiting repaint at `04:46:36.492`.

## Validation

- `aipi-lite/.venv/bin/python -m pytest aipi-lite/tests/test_companion_status.py aipi-lite/tests/test_dispatch.py -q`
- `.venv/bin/python -m pytest tests/unit/test_web_runtime.py tests/unit/test_agent_context.py tests/unit/test_agent_device.py tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q`
- `scripts/aipi_test.sh -q`
- `git diff --check`

## Remaining Product Gaps

- AI PI still has a tiny display; a browser companion panel should provide a
  richer overview of waiting sessions, stale sessions, and delivery targets.
- Polling is acceptable, but fast state transitions would feel better with a
  push path or explicit repaint events.
- The device can cycle sessions, but it cannot yet show a compact list/count
  of all waiting sessions at once.
- Target confidence is exposed in JSON and identity text, but the physical
  display needs clearer affordances for low-confidence or unavailable targets.
