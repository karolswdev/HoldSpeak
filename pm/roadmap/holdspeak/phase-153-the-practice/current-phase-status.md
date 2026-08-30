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
| HS-153-05 | Compaction and todo (chat.compact cut row, door.add_item) | backlog | [story-05-compact-todo](./story-05-compact-todo.md) | - |
| HS-153-06 | The walk and the close | backlog | [story-06-walk-and-close](./story-06-walk-and-close.md) | - |

## Where we are

HS-153-01 DONE, HS-153-02 DONE, HS-153-03 DONE, HS-153-04 code + tests delivered (awaiting flip). Story 04: additive `thread_message_parts.draft` column (reconcile adds it), one draft user message per thread (all parts draft=1), `POST /api/threads/{id}/annotations` creates annotation parts on the draft message, `DELETE` removes them, GET hides the draft from transcript but exposes `draft_annotations[]`, Send promotes (draft=0, annotation prefix prepended to user content), real coordinator payload capture proves the prefix, sensitive fence carries through. Web: AnnotationPopover (in-flow, anchored under selection, MicButton, Save/Cancel, Esc closes), AnnotationChips (quote head + x), selection + `a` key shortcut, optimistic add/remove with rollback. One defect found: zustand selector `?? []` created a new array reference every render (fixed with stable EMPTY constant). 115 scoped python tests green, 60 vitest green, 4 glass legs green (annotate at 1440+393), web baseline zero branch-new.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- 2026-08-29 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
