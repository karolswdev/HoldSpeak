# HS-153-04 - Annotations (selection popover, draft parts, mic)

- **Project:** holdspeak
- **Phase:** 153
- **Status:** done
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

## What shipped

**Files changed (backend):**
- `holdspeak/db/schema.py` -- additive `thread_message_parts.draft INTEGER NOT NULL DEFAULT 0`
- `holdspeak/db/threads.py` -- `ThreadMessagePart.draft` field; `_row_to_part` reads it; `append_part` accepts `draft=` kwarg; new methods: `draft_message_for(thread_id)`, `is_draft_message(message_id)`, `draft_parts(thread_id)`, `delete_part(part_id)`, `promote_drafts(message_id)`
- `holdspeak/services/thread_service.py` -- `get()` filters draft messages from transcript, exposes `draft_annotations[]`; `_assemble_payload` skips draft messages; `start_turn` promotes draft (draft=0, appends typed text part after the annotation parts — annotation parts already carry their prefix text, so the assembler concatenates them without duplication); `_message_dict` includes `draft` on wire parts
- `holdspeak/web/routes/threads.py` -- `POST /api/threads/{id}/annotations {message_id, quote, comment}` creates/reuses ONE draft user message, appends annotation part (draft=1); `DELETE /api/threads/{id}/annotations/{part_id}` removes a draft annotation part; validates source message belongs to thread; carries `sensitive` from source part

**Files changed (web):**
- `web/src/desk/threads.ts` -- `DraftAnnotation` interface; `addAnnotation()`, `deleteAnnotation()` API functions; `ThreadDetail.draftAnnotations`; `getThread` parses draft_annotations; `ThreadStoreState.draftAnnotations` + hydration in `loadThread`
- `web/src/desk/pullouts/ThreadPullout.tsx` -- `AnnotationPopover` (in-flow, anchored under selection; comment field + MicButton; Save/Cancel; Esc closes); `AnnotationChips` above composer (quote head + x); popover opens on `selectionchange` (debounced 80ms) when a non-empty selection lies inside an assistant text part (not tool/guardrail/user rows, not while focus is in an input); `a` key is the keyboard route; dismiss on mousedown outside the popover; `handleAnnotationSave` (optimistic + POST + rollback); `handleAnnotationRemove` (optimistic + DELETE + rollback); `handleSend` clears drafts optimistically; callback ref on body div for reliable mount timing
- `web/src/desk/pullouts/thread-pullout.css` -- popover, chip, input, quote head styles

**Files changed (tests):**
- `tests/unit/test_thread_annotations.py` (NEW) -- 15 tests: TestDraftParts (9: append, draft_message_for, is_draft_message, delete_part, promote, draft_parts, second annotation reuses), TestServiceDraftAnnotations (2: GET hides draft, GET shows promoted), TestRealCoordinatorAnnotationPayload (2: annotation prefix in admitted payload, two annotations before send), TestReconcileDraftColumn (1: pre-change DDL gains column, default 0, draft=1 insert)
- `web/src/desk/__tests__/annotations.test.tsx` (NEW) -- 5 tests: chips render with annotations, no chips when empty, remove button present, selectionchange with non-collapsed range inside assistant text part opens popover (mocked getSelection), selection while activeElement is a textarea does not open popover
- `tests/e2e/test_hs153_practice_glass.py` -- `test_annotation_popover_and_chips` glass leg at 1440+393: assertive (no defensive `if count > 0`); real mouse drag across assistant text (fallback: programmatic Range + dispatchEvent selectionchange); popover visible and anchored inside pullout (bounding box within viewport), MicButton present, comment typed via native setter, Save, chip visible, reload persists, Send promotes, GET shows annotation prefix in user content + `draft_annotations == []`, no h-overflow; no test-only hooks in the built bundle; shots: annotation-popover, annotation-chip, annotation-after-send at both widths
- `web/src/desk/__tests__/ThreadPullout.test.tsx` -- fixed: `draftAnnotations: []` on ThreadDetail
- `web/src/desk/__tests__/ThreadToolRows.test.tsx` -- fixed: `draftAnnotations: []` on ThreadDetail
- `web/src/desk/__tests__/threads.test.ts` -- fixed: `draftAnnotations: []` on ThreadDetail

**Seams:**
- Owner annotations are distinguished from frozen-ref annotations by `meta_json.source === "owner"` (frozen-ref annotations carry `ref_kind`/`ref_id` instead -- thread_service.py L371 unchanged)
- Draft message strategy: a pure-draft user message (all parts draft=1) is invisible in the transcript and payload; Send promotes it and appends the typed text after the annotation parts
- Reconcile: `_add_missing_columns` automatically picks up the new `draft` column (schema.py defines it; reconcile's reference-schema diff adds it with `DEFAULT 0` for existing rows)
- Sensitive fence: annotating a sensitive assistant part marks the annotation part `sensitive=1`; the assembler carries its text into `_sensitive_texts` for M1 redaction on cloud egress

**Real-path defects found:**
- Zustand selector `s.draftAnnotations[threadId] ?? []` created a new array reference every render, causing an infinite re-render loop. Fixed by using a stable constant `EMPTY_DRAFT_ANNOTATIONS` (same pattern as EMPTY_TOOL_ROWS).
- Annotation prefix duplicated in admitted payload: `start_turn` was building prefix lines from meta_json AND the annotation part already carried prefix text; `_assemble_payload` concatenated both. Fixed by removing the redundant prefix construction -- the annotation parts already carry their prefix text from the POST route.
- Popover did not open on mouseup in headless Chromium: the `mouseup` event handler called `checkSelection` synchronously, but the browser had not yet finalized the selection from a multi-click or drag gesture. Fixed by switching the production path to `selectionchange` (debounced 80ms), which fires after the browser commits the new selection. The glass leg now uses a real mouse drag (Playwright `page.mouse.move/down/move/up`) with a fallback to programmatic `Range` + `dispatchEvent(selectionchange)` when the drag produces no selection. No test-only hooks in the built bundle.

## Notes / open questions

- One draft user message per thread; a fork/regenerate keeps drafts on the origin thread.
