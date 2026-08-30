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
| HS-153-06 | The walk and the close | done | [story-06-walk-and-close](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Phase 153 COMPLETE 6/6. The walk and the close (HS-153-06): metal DRY 6/6 and LIVE 6/6 on `.43` Qwen3.6 (mode switch, effect-guard violation + safe-mode deny + yolo receipt, annotation round-trip, /compact with a clean post-cut payload, /todo on the Door, egress-guard + the fence's [people content withheld]); glass 6 legs both widths, zero overflow, 12 exhibit shots; docs entry points touched (tool count 142 unchanged); close counsel RATIFY-WITH-CONCERNS with M1 (practice capabilities redacted on chat.turn's scope, not their own boundary) and S1–S3 all fixed in-round; honest sweep name-diffed against main (41-name baseline), all 13 branch-new fences resolved. Environment finding: the `.43` llama.cpp server runs a default dictation grammar — the engine now sends `grammar:""` on non-tool custom-endpoint calls and json_schema response_format for the practice capabilities.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
