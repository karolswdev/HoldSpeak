# HS-114-05 - Editor transforms: propose, don't replace

- **Project:** holdspeak
- **Phase:** 114
- **Status:** in-progress
- **Depends on:** HS-114-04
- **Unblocks:** HS-114-07
- **Owner:** unassigned

## The thesis (the bar)

Rewrite, Expand, and Continue show a proposed replacement in an
aerogel inset before touching the text. The user accepts or rejects
explicitly. Article V: consequential actions require
propose → approve → execute.

## Ground (from the applicability study)

- `InlineEditor.tsx:82-118`: Rewrite/Expand/Continue call `runAsk`
  and immediately replace the editor content. No preview, no diff,
  no undo receipt.
- The aerogel species exists and is the canonical inset for nested
  records and receipts. (`web/src/desk/surface/surface.css:589-637`)
- TransportKey exists as the square momentary action gadget.
  (`web/src/desk/surface/gadgets.css:661-743`)
- Article V requires propose-approve-execute for consequential
  actions with receipts and named refusals.

## Method

1. **Proposal state.** After Rewrite/Expand/Continue calls
   `runAsk`, the result goes into a `proposal` state instead of
   immediately replacing text. State: `{original, proposed, lens,
   receipt}`.

2. **Aerogel inset.** Render the proposal as a `.surface-aerogel`
   block below the selected text in the editor. Shows the proposed
   replacement text, the egress lamp (from HS-114-04), and
   target/latency receipt.

3. **Accept/Reject controls.** Two TransportKeys at 32px (compact,
   matching editor context):
   - Accept (ok variant): replaces the original text, pushes to
     undo stack, clears proposal state.
   - Reject (danger variant): dismisses the proposal, restores
     original selection.
   - Escape = Reject.

4. **Undo receipt.** On Accept, the editor footer shows:
   `REWRITE APPLIED · ⌘Z TO UNDO` (standard receipt bar pattern).
   Cmd+Z restores the original text.

5. **Aerogel entrance animation.** Uses the existing aerogel
   animation: opacity 0→1, scale(.97)→1, translateY(-2px)→0.

## Acceptance

- Rewrite/Expand/Continue show a proposal in an aerogel inset.
- Accept replaces text; Reject dismisses.
- Escape dismisses.
- Cmd+Z after Accept restores original text.
- Receipt bar shows "REWRITE APPLIED · ⌘Z TO UNDO" after accept.
- Proposal shows egress lamp with target/latency receipt.
- No text is replaced without explicit user action.

## Test plan

- `npx vitest run src/desk/__tests__/` (InlineEditor tests)
- Manual: Rewrite with text selected → proposal appears → Accept →
  text replaced → Cmd+Z → original restored.
