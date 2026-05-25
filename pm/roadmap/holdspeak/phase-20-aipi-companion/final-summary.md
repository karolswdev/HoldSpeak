# Phase 20 — Final Summary

- **Phase opened:** 2026-05-24
- **Phase closed:** 2026-05-24
- **Chunks shipped:** 4

## Goal — was it met?

Original goal:

> Make AIPI-Lite a physical companion for HoldSpeak's local agent and meeting workflows. The first useful loop is simple: when Claude or Codex is waiting for a response, AIPI can show that state and the latest captured question, then a follow-up story routes the user's spoken reply back through intelligent typing.

**Yes.** HoldSpeak now exposes the first same-LAN AIPI companion loop:
AIPI-compatible devices can query whether Claude/Codex is waiting, display the
latest captured question, and initiate a user-spoken reply that routes through
the dictation pipeline with the correct agent target context. HoldSpeak also
exposes `/api/companion/status` so hook/device/dictation setup can be diagnosed
from one status surface.

Evidence per story:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md) ·
[03](./evidence-story-03.md) ·
[04](./evidence-story-04.md).

## Exit criteria — final state

- [x] AIPI can query whether Claude/Codex is waiting and display the latest captured question — [evidence-story-01](./evidence-story-01.md).
- [x] AIPI can initiate a voice reply path that targets the active Claude/Codex profile — [evidence-story-02](./evidence-story-02.md).
- [x] HoldSpeak exposes enough debug state to diagnose hook/device companion setup — [evidence-story-03](./evidence-story-03.md).
- [x] Broad focused regression is green at phase close; evidence files capture commands and results — [evidence-story-04](./evidence-story-04.md).
- [x] `final-summary.md` records the companion UX handoff — this file.

## Stories shipped

| ID | Title | Commit/PR | Date |
|---|---|---|---|
| HS-20-01 | Agent waiting query surface | `d471c3f` | 2026-05-24 |
| HS-20-02 | AIPI voice reply to waiting agent | `6cba66c` | 2026-05-24 |
| HS-20-03 | Companion debug surface | `7c696a6` | 2026-05-24 |
| HS-20-04 | Phase exit and companion UX handoff | this working set | 2026-05-24 |

## Stories cut or deferred

| Topic | Reason | Re-targeted to |
|---|---|---|
| Firmware gesture mapping | This phase shipped the server contract first. Gesture ergonomics should be designed against real device use. | Future AIPI companion UX phase |
| Proactive device push of agent-waiting state | Query/status polling is sufficient for v1 and avoids adding new wire frames. | Future LCD cadence/push design |
| Direct agent transport | Current behavior keeps user speech/action explicit and uses existing text insertion. | Future agent transport exploration |
| Cross-network companion reach | Phase 20 was same-LAN only. | Phase 15/out-and-about or a later security phase |

## Ready now

- Device query names:
  - `agent_status`
  - `agent_question`
- Device replies use existing `status` frames.
- Fresh waiting-agent window is 120 seconds.
- AIPI voice replies can use waiting-agent target context:
  - Codex -> `codex_cli`
  - Claude -> `claude_code`
- `/api/companion/status` reports readiness and blockers across devices,
  captured agent state, dictation pipeline config, and runtime text insertion.

## Handoff

The next companion work should be product/UX, not substrate. The likely next
phase should decide:

- what AIPI gesture means "answer the waiting agent";
- when LCD status should poll versus when HoldSpeak should push;
- how long the device should display a waiting question;
- whether the browser should expose a compact companion panel;
- whether replies should keep using text insertion or grow a deliberate agent
  transport later.

The load-bearing contract is intentionally small: `query` in, `status` out,
explicit user speech for replies, and `/api/companion/status` for diagnostics.

## Final asset / test posture

- Broad focused regression: `.venv/bin/pytest -q tests/unit/test_agent_device.py tests/unit/test_agent_context.py tests/unit/test_web_runtime.py tests/integration/test_device_audio_ingest.py tests/integration/test_web_server.py::TestDeviceHealthEndpoint tests/integration/test_web_server.py::TestCompanionStatusEndpoint tests/integration/test_web_server.py::TestRuntimeControlEndpoints` — `65 passed in 1.96s`.
- Diff hygiene: `git diff --check` — passed.
