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
| HS-153-03 | Guardrails (chat.guardrail, seeds, the advisory row) | backlog | [story-03-guardrails](./story-03-guardrails.md) | - |
| HS-153-04 | Annotations (selection popover, draft parts, mic) | backlog | [story-04-annotations](./story-04-annotations.md) | - |
| HS-153-05 | Compaction and todo (chat.compact cut row, door.add_item) | backlog | [story-05-compact-todo](./story-05-compact-todo.md) | - |
| HS-153-06 | The walk and the close | backlog | [story-06-walk-and-close](./story-06-walk-and-close.md) | - |

## Where we are

HS-153-01 DONE, HS-153-02 DONE. Story 02: two-stage slash completion in ThreadComposer (command stage + argument stage in one popover), R3 rule (/ only at line start), 10 slash commands each mapped to a registered verb id, /mode calls setMode, /prompt inserts the note body, /tools shows palette info, /todo /compact /guardrail show "not yet" with TODO hooks for stories 03/05. Second seed prompt added (1:1 prep). Backend test: 9 tests for list_by_tag(json_each). Vitest: 46 tests (completeSlash pure function, verb mapping, component behavior). Glass: 2 legs (modes + slash) at 1440+393, zero overflow. Three real-path defects found (Playwright/React controlled input, focus loss after JS setter, bundle staleness).

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
