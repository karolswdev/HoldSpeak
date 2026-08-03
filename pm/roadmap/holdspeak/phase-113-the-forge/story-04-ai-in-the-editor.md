# HS-113-04 - AI in the editor

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-02
- **Unblocks:** HS-113-05
- **Owner:** unassigned

## The thesis (the bar)

The editor must have built-in AI composition. A user writing a note
should be able to select text and trigger rewrite/expand/summarize, or
position their cursor and request a continuation — all in-place,
consent-gated, egress-badged, and without leaving the editor. The
existing Ask infrastructure (`/api/ask`, grounding, egress receipts)
is the LLM backend; the editor is the new insertion surface.

**Articles served:** II (capabilities are primitives), V (local-first,
egress-badged), VII (no modals, in-world), IX (consent-gated
execution).

## Ground (from the pre-charter survey)

- `web/src/desk/components/AskPanel.tsx` — the Ask panel posts to
  `/api/ask`, renders receipts with model/egress/grounding metadata,
  and can persist output via `/api/ask/keep`. Currently creates a
  separate artifact; no path to insert result into an open editor.
- `web/src/desk/ask.ts` — Ask request/response data layer. Supports
  `context` (selected desk items for grounding) and returns structured
  results with egress badges.
- `web/src/desk/grounding.ts` — grounding selection helpers. Already
  wired for desk-item context; can be extended to include
  editor-selection text.
- `web/src/desk/components/InlineEditor.tsx` — no AI integration
  today. Voice dictation (`MicButton`) appends text but does not
  transform existing content.
- After HS-113-01 ships, the editor will be CodeMirror 6. CM6's
  `dispatch` API supports atomic range replacements:
  `view.dispatch({ changes: { from, to, insert } })` — this is how
  AI results land in the document.

## Method

1. Build an `EditorAIBar` component that appears as a floating
   toolbar above a text selection in the CM6 editor. Trigger:
   select text + short delay (300ms), or Cmd+J keybinding.
2. The bar offers four verbs: **Rewrite**, **Expand**, **Summarize**,
   **Continue**. Each maps to a system prompt template + the selected
   text (or document tail for Continue).
3. On verb click:
   - Show an inline loading state replacing the selected text with a
     shimmering placeholder (Desk-style, not a spinner).
   - POST to `/api/ask` with the verb prompt, selected text as
     context, and the note's existing grounding.
   - On response, replace the selection range via CM6 `dispatch`.
   - Show a one-line egress receipt below the toolbar (model name,
     egress badge) that auto-dismisses after 3s.
4. **Continue** works at cursor position with no selection: takes the
   last 500 characters as context, appends the AI continuation at the
   cursor.
5. **Escape** during a pending AI operation cancels the request and
   restores the original text. Undo (Cmd+Z) also restores after
   completion.
6. The toolbar respects Desk Grammar verb law: verbs are registered,
   ineligible verbs are ghosted with reason (e.g., "No model
   configured" if no inference target is set).
7. Add a Cmd+J keybinding to the CM6 keymap that opens the AI bar
   with the current selection (or positions cursor for Continue if
   no selection).

## Test plan

- Unit: `EditorAIBar` renders on text selection, shows four verbs,
  dismisses on Escape.
- Unit: Rewrite verb sends correct prompt to `/api/ask`, replaces
  selection on response.
- Unit: Continue verb sends tail context, appends at cursor.
- Unit: Cancel during pending request restores original text.
- Unit: Cmd+Z after AI replacement undoes to pre-AI state.
- Unit: egress receipt appears with model name and badge, auto-
  dismisses.
- Integration: open a note, type a paragraph, select it, Rewrite —
  the text changes in place. Undo — the original returns.
- Screenshot walk: 1440px — AI bar floating above selection, receipt
  visible, Desk glass aesthetic. Must not feel like a chat interface.
- Error leg: no inference target configured — Rewrite verb is ghosted
  with "No model configured."
