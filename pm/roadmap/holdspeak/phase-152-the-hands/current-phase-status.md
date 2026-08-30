# Phase 152 - The Desk Chat — The Hands (DC-02)

**Last updated:** 2026-08-29.

## Goal

Model tool calls inside a Thread turn run through the kernel's tool-turn lifecycle over the in-process MCP families — the Thread becomes a manager's hands.

## Owner mandate

The owner, on seeing DC-01 alone: "I was totally hoping for a holistic implementation." The port ships whole — 152 The Hands, 153 The Practice, 154 The Call, 155 The Crew — on PR #507, in order, same rigor. This phase is the RFC's §6.4/§6.7. Counsel design-beat (holistic) RATIFY-W-C; M1–M6 accepted into [assets/settled-design.md](./assets/settled-design.md); census in [assets/audit-census.md](./assets/audit-census.md).

## Scope

- **In:** the pass loop, the gate (truth table + kernel children), the People fence, the pending/elicitation rows, per-kind renderers + status line, the walk.
- **Out:** modes/guardrails/annotations/compaction (153), TTS/VAD/call (154), subthreads (155), external MCP servers.

## Exit criteria (evidence required)

- [ ] Counsel's four legs recorded (real `.43` tool turn with receipts; People boundary under profile switch; safe-mode decision box; glass both widths).
- [ ] No new admission path (one-path census + Phase-131 fence green).
- [ ] Close counsel; owner shot exhibit.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-152-01 | The tool loop (passes, tool_call parts, frames, abort) | in-progress | [story-01-tool-loop](./story-01-tool-loop.md) | - |
| HS-152-02 | The gate (thread_tool_policy, the truth table, kernel children) | done | [story-02-gate](./story-02-gate.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-152-03 | The People fence (sensitive results, multi-pass redaction) | backlog | [story-03-people-fence](./story-03-people-fence.md) | - |
| HS-152-04 | The pending box (decision + elicitation rows, decide route) | backlog | [story-04-pending-box](./story-04-pending-box.md) | - |
| HS-152-05 | The renderers and the status line | backlog | [story-05-renderers](./story-05-renderers.md) | - |
| HS-152-06 | The walk and the close | backlog | [story-06-walk-and-close](./story-06-walk-and-close.md) | - |

## Where we are

**Chartered — 0/6.** Engine tool-call streaming (tools= + tool_call deltas) is building ahead of story 01; story 02 (the gate) builds in parallel.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
