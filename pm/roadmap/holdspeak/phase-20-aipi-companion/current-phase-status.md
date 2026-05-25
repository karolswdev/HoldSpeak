# Phase 20 — AIPI Companion

**Last updated:** 2026-05-24 (HS-20-01 closed: agent waiting query surface).

## Goal

Make AIPI-Lite a physical companion for HoldSpeak's local agent and meeting workflows. The first useful loop is simple: when Claude or Codex is waiting for a response, AIPI can show that state and the latest captured question, then a follow-up story routes the user's spoken reply back through intelligent typing.

## Scope

### In

- Device query access to captured Claude/Codex awaiting-response state.
- LCD-safe status text for agent waiting and latest agent question.
- Same-LAN gesture/voice reply loop after the query surface is stable.
- Web/debug visibility for device-agent companion state.

### Out

- Cross-network device reach.
- Autonomous replies to Claude/Codex without explicit user speech/action.
- Hosted assistant certification.
- New device frame types unless the existing `query`/`status` contract becomes insufficient.

## Exit criteria

- [x] AIPI can query whether Claude/Codex is waiting and display the latest captured question.
- [ ] AIPI can initiate a voice reply path that targets the active Claude/Codex profile.
- [ ] HoldSpeak exposes enough debug state to diagnose hook/device companion setup.
- [ ] Broad focused regression is green at phase close; evidence files capture commands and results.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-20-01 | Agent waiting query surface | done | [story-01-agent-waiting-query.md](./story-01-agent-waiting-query.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-20-02 | AIPI voice reply to waiting agent | backlog | — | — |
| HS-20-03 | Companion debug surface | backlog | — | — |
| HS-20-04 | Phase exit and companion UX handoff | backlog | — | — |

## Where we are

HS-20-01 is closed. HoldSpeak now exposes `query:agent_status` and `query:agent_question` over the existing device `query` frame and answers with normal `status` frames. Current pickup moves to HS-20-02: voice reply routing to the waiting agent.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Captured agent question is stale | medium | Short max-age window and explicit `No agent waiting` response. | Users see outdated prompts on device after replying. |
| LCD text overwhelms device UI | medium | Truncate through shared LCD helper and provide short status/query variants. | Device display becomes unreadable or scrolls constantly. |
| Voice reply writes to wrong target | high | Separate reply-routing story; require explicit user action and target profile. | Any automated reply lands in the wrong app/session. |

## Decisions made

- 2026-05-24 — **Reuse `query` / `status`.** Agent companion state starts as new query names, not new wire frame types.
- 2026-05-24 — **No autonomous replies.** AIPI may show agent state and start capture, but user speech/action drives replies.

## Decisions deferred

- Exact firmware gesture mapping for “reply to agent”.
- Whether the server should proactively push agent-waiting status or rely on device polling/query.
- Whether replies should paste into the focused app or route through an explicit agent transport.
