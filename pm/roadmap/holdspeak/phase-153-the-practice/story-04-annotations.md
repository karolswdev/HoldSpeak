# HS-153-04 - Annotations (selection popover, draft parts, mic)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** backlog
- **Depends on:** HS-152-06
- **Unblocks:** HS-153-06
- **Owner:** unassigned

## Problem

The owner talks back to a specific sentence: select text in an
assistant part, comment (by voice), and the comment rides the next turn
as a quoted annotation — no modal, survives reload (counsel S5;
settled design D4).

## Scope

- **In:** additive `thread_message_parts.draft INTEGER NOT NULL DEFAULT 0`
  (reconcile.py, one column); `POST /api/threads/{id}/annotations
  {message_id, quote, comment}` → an `annotation` part (draft=1) on the
  thread's DRAFT user message (created on first annotation, reused);
  `DELETE …/annotations/{part_id}`; `GET /api/threads/{id}` lists draft
  parts. Composer: chips above the input (quote head · ×); Send promotes
  the draft message (draft=0, appends the typed text as its text part);
  the assembler prefixes each annotation as "The owner annotated:
  «quote» — comment". Selection popover in-flow under the selection
  (comment field WITH `MicButton`, Save / Cancel; Esc cancels); keyboard:
  a selection + `a` opens it.
- **Out:** annotating tool rows or user messages; annotation search.

## Acceptance criteria

- [ ] Select → comment → chip; reload → chip still there (draft part persisted); Send → the admitted payload's user content starts with the annotation prefix; the draft flag is 0 after.
- [ ] Mic fills the comment field (the existing browser mic pipeline, click-to-toggle).
- [ ] Glass 1440 + 393: popover anchored, no overflow, no modal; Esc closes.

## Test plan

- **Unit:** `tests/unit/test_thread_annotations.py` (repository + assembler prefix + real coordinator payload capture); vitest selection popover + chips.
- **Integration:** `tests/e2e/test_hs153_practice_glass.py` leg `annotate`.
- **Manual / device:** story 06 (annotation round-trip by voice on the real hub).

## Notes / open questions

- One draft user message per thread; a fork/regenerate keeps drafts on the origin thread.
