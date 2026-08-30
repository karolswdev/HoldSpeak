# Phase 152 - The Desk Chat — The Hands (DC-02)

**Last updated:** 2026-08-30 (HS-152-05 done — the renderers; 5/6; next 06 the walk).

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
| HS-152-01 | The tool loop (passes, tool_call parts, frames, abort) | done | [story-01-tool-loop](./story-01-tool-loop.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-152-02 | The gate (thread_tool_policy, the truth table, kernel children) | done | [story-02-gate](./story-02-gate.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-152-03 | The People fence (sensitive results, multi-pass redaction) | done | [story-03-people-fence](./story-03-people-fence.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-152-04 | The pending box (decision + elicitation rows, decide route) | done | [story-04-pending-box](./story-04-pending-box.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-152-05 | The renderers and the status line | done | [story-05-renderers](./story-05-renderers.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-152-06 | The walk and the close | backlog | [story-06-walk-and-close](./story-06-walk-and-close.md) | - |

## Where we are

**5/6 — a manager's desk renders the result.** Story 01 the loop, 02 the gate, 03 the People fence (real coordinator + real hub over HTTP, 15/15; LIVE on `.43` 10/10), 04 the pending box (tool rows, decision box, elicitation form, hydration from parts; glass 4 legs both widths, 15 shots reviewed), 05 the renderers + `thread.set_status` (per-kind result blocks from the Surface primitives, RAW fold on every row, the 32 KB result cap D2 was missing, 142 tools / 31 families; glass 6 legs). Story 03 found four latent defects the fake-adoption tests hid (handless hub ThreadService, palette after admission, runner dropping `tool_calls`, 79 KB census overflowing admission) plus DC-01's decorative `profile_override`; story 04 found two more seams (`/decide` had no Allow-always; elicitation answers were never collected). Next: 06 the walk — safe-mode leg on glass + `door.*` effect on `.43` (legs 1–2 already banked LIVE), door-walk leg, docs, close counsel, the honest sweep (name-diff vs main), the owner's shot exhibit.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-08-30 - HS-152-03: `CHAT_PALETTE` (26 hands, 12.6 KB) is what a turn offers; `TOOL_NAMES` stays the gate's table - the 141-schema census (79 KB) overflows admission under the one-token-per-byte law - orchestrator; addendum in [assets/settled-design.md](./assets/settled-design.md).
- 2026-08-30 - HS-152-03: `thread.profile_override` honored as an invocation-scoped next-run override before every admit (Phase 143 mechanism) - the assignment ledger stays the routing truth - orchestrator.
- 2026-08-30 - METAL BANKED EARLY (for story 06 legs 1–2): `assets/story-03-hub-leg.py` LIVE against `.43` Qwen3.6-35B-A3B through a legacy LAN profile row (the production path; the 151 v2 seeding + injected engine is NOT the real path) — 10/10: native `tool_calls` → real `people.readiness` dispatch → receipt `tr-ba9ef02551cb`, part `sensitive=1`, override → `cloud` at admission. Payloads in `assets/story-03-hub-payloads-live/`. RULING: no `ToolQualification` eval is needed for `chat.turn` (it does not `require.structured_tools`; llama.cpp emits native tool_calls for Qwen3.6 — probed directly, 0.3 s). Story 06 drops that leg. Observed: the model paraphrases the People result into its answer — R2 (paraphrase laundering) is real and stays the DC-03 `egress-guard`.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
