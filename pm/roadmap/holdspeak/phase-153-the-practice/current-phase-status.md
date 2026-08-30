# Phase 153 - The Desk Chat — The Practice (DC-03)

**Last updated:** 2026-08-30.

## Goal

Modes, prompts, guardrails, annotations, compaction and Door-backed todo on the Thread.

## Scope

- **In:** CLI-supported artifacts and workflow needed for this phase.
- **Out:** Related work not explicitly named by this phase.

## Exit criteria (evidence required)

- [ ] Exit criteria are defined before implementation begins.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-153-01 | Modes as recipes (kind, seeds, allow-lists, mode tabs) | done | [story-01-modes](./story-01-modes.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-153-02 | Prompts and slash verbs (notes tagged prompt, arguments) | done | [story-02-prompts-slash](./story-02-prompts-slash.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-153-03 | Guardrails (chat.guardrail, seeds, the advisory row) | done | [story-03-guardrails](./story-03-guardrails.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-153-04 | Annotations (selection popover, draft parts, mic) | done | [story-04-annotations](./story-04-annotations.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-153-05 | Compaction and todo (chat.compact cut row, door.add_item) | done | [story-05-compact-todo](./story-05-compact-todo.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-153-06 | The walk and the close | backlog | [story-06-walk-and-close](./story-06-walk-and-close.md) | - |

## Where we are

HS-153-01 DONE, HS-153-02 DONE, HS-153-03 DONE, HS-153-04 DONE, HS-153-05 code + tests + glass delivered (awaiting flip). Story 05: `compact_thread()` admits `chat.compact` through the real coordinator, creates a system row with `stats_json.compaction=true` + summary text part, assembler cut skips pre-cut messages; sensitivity inherited; M1 redactor applied before cloud egress. `todo_from_thread()` goes through `ThreadToolExecutor` for `door.add_item` with receipt row -- same gate/truth-table path as a model call. Web: cut marker row with RAW summary fold, earlier-messages fold toggle, `/compact` and `/todo` wired in composer, Door card "from a thread" provenance chip opening pullout. Also fixed: `run_guardrail` had the same four defects as `run_compact` -- fixed in this story, two real-coordinator tests unblocked + two cloud-redaction tests added. Seven real-path defects total. 145 scoped python tests green, 6 glass legs green, 116 vitest green, web baseline zero branch-new from our changes.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
