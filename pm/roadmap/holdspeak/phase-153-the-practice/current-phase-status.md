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
| HS-153-04 | Annotations (selection popover, draft parts, mic) | backlog | [story-04-annotations](./story-04-annotations.md) | - |
| HS-153-05 | Compaction and todo (chat.compact cut row, door.add_item) | backlog | [story-05-compact-todo](./story-05-compact-todo.md) | - |
| HS-153-06 | The walk and the close | backlog | [story-06-walk-and-close](./story-06-walk-and-close.md) | - |

## Where we are

HS-153-01 DONE, HS-153-02 DONE, HS-153-03 code + tests delivered (awaiting flip). Story 03: guardrail notes (YAML front matter in body_markdown), two seeds (effect-guard + egress-guard), per-mode enablement (Chase: both, Desk: egress-guard, Draft/Plan: none), guardrail admission ONCE per pass in the tool loop (after tool_calls extracted, before per-call admission), thread_guardrail frame + guardrail part persisted, default_decision on pending frames (deny when violation + non-yolo), guardrail failure = warning row (never blocks), /guardrail verb wired to toggle on the mode recipe, GuardrailRowView renderer (violations red, warnings amber, RAW fold), decision box honours defaultDecision. Two defects found: CHECK constraint on thread_message_parts.kind needed extending; zustand infinite re-render from unstable empty object in guardrailRows selector. 24 unit tests (all green), 123 scoped tests green, vitest 37/37 green, web baseline zero branch-new.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
