# HS-120-06 — Editors share one material

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Three editor surfaces use wrong or inconsistent controls:

1. **RecipeEditor** (`web/src/desk/pullouts/editors/RecipeEditor.tsx`):
   Raw `<input>`, `<textarea>`, and `<select>` elements instead of desk
   gadgets. A `🤖` avatar placeholder. This is a frequently used
   editor for the agent/recipe primitive.

2. **DecisionPullout** (`web/src/desk/pullouts/DecisionPullout.tsx`):
   Edit mode uses bare `<textarea className="desk-pullout-editbox">`
   for markdown fields where other editors use `DeskEditor` with
   CodeMirror, AI bar, and mic support. Status cycle button looks like
   a passive badge — no visual hint that clicking cycles the status.
   Field labels auto-generated with `.replace("_markdown", "")` produce
   lowercase uncapitalized headers.

3. **NoteEditor/KbEditor AI proposal inset**
   (`web/src/desk/pullouts/editors/NoteEditor.tsx`,
   `KbEditor.tsx`): The proposal inset uses extensive inline
   `style={{}}` objects, duplicated identically between both files.

When this ships:

1. RecipeEditor uses desk gadgets (StringGadget, PadGadget,
   CycleGadget) instead of raw HTML controls. Avatar uses AgentAvatar.
2. DecisionPullout edit mode uses DeskEditor for markdown fields.
   Status cycle has an affordance (CycleGadget or a chevron glyph).
   Labels are properly capitalized.
3. Note/Kb proposal inset styles are extracted into a shared CSS class
   (`.editor-proposal-inset` or equivalent). Zero inline style objects.

## Acceptance criteria

- [ ] RecipeEditor: zero raw `<input>`, `<textarea>`, `<select>`.
- [ ] RecipeEditor: avatar uses AgentAvatar component.
- [ ] DecisionPullout: markdown fields use DeskEditor.
- [ ] DecisionPullout: status cycle has visible affordance.
- [ ] DecisionPullout: field labels capitalized.
- [ ] Note/Kb editors: proposal inset styled via CSS class, not inline.
- [ ] Proposal rendering shared or deduplicated.

## Test plan

- Open recipe editor, verify desk gadgets render.
- Open decision pullout, edit a field, verify DeskEditor loads.
- Cycle decision status, verify the control looks interactive.
- Open note/kb editor, trigger AI proposal, verify styled consistently.

## Files in scope

- `web/src/desk/pullouts/editors/RecipeEditor.tsx`
- `web/src/desk/pullouts/DecisionPullout.tsx`
- `web/src/desk/pullouts/editors/NoteEditor.tsx`
- `web/src/desk/pullouts/editors/KbEditor.tsx`
- `web/src/desk/components/inline-editor.css` (or new shared CSS)
