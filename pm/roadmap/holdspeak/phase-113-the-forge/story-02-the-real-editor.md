# HS-113-02 - The real editor

- **Project:** holdspeak
- **Phase:** 113
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-113-04, HS-113-05, HS-113-06, HS-113-08
- **Owner:** unassigned

## The thesis (the bar)

The Desk's editor must be a real composition tool, not a browser
textarea. A user opening a note, artifact, or KB entry should be able
to write markdown fluently — headings, bold, italic, code, lists,
links — with syntax-aware highlighting, keyboard shortcuts, proper
undo/redo, and the Desk's dark-glass aesthetic. The stored format
stays `body_markdown`; the editor makes that format visible and
productive.

**Articles served:** I (the Desk is the front door), VII (quiet
chrome, fewest words), VIII (native-grade craft, 60fps interaction
budget).

## Ground (from the pre-charter survey)

- `web/src/desk/components/InlineEditor.tsx` — the primary editor is
  a `<textarea rows={7}>` with 450ms debounced save. No formatting
  toolbar, no syntax awareness, no keyboard shortcuts beyond browser
  defaults.
- `web/src/desk/surface/Material.tsx` — the markdown *renderer*
  supports headings, lists, bold, italic, inline code, and links. The
  *editor* is blind to all of this.
- `web/src/desk/components/Pullout.tsx` — the pullout note editor is
  a second, independent textarea with its own save semantics
  (explicit commit vs. debounce). Both paths must converge on the new
  editor.
- `web/src/desk/components/MicButton.tsx` — voice dictation appends
  text to the body. Must continue working with CM6 (append at cursor
  position instead of end-of-field).
- `web/package.json` — no editor library dependency exists today.
  CodeMirror 6 is the chosen library.
- `web/design-tokens.json` — the Desk design system tokens must drive
  the CM6 theme: `--surface-*`, `--text-*`, `--accent-*`, font stack,
  and spacing scale.

## Method

1. Add `@codemirror/view`, `@codemirror/state`, `@codemirror/lang-markdown`,
   and `@codemirror/commands` to `web/package.json`.
2. Build a `DeskEditor` component wrapping CM6 with:
   - Markdown language mode with syntax highlighting.
   - A Desk-matched theme built from `design-tokens.json` CSS
     variables (dark background, mono font, accent-colored headings).
   - Standard keybindings: Cmd+B (bold), Cmd+I (italic), Cmd+Z/Y
     (undo/redo), Tab (indent list), Shift+Tab (outdent).
   - Debounced `onChange` callback matching the existing 450ms save
     contract.
   - Controlled value prop for external updates (voice dictation,
     AI insertion).
   - Focus management: `autoFocus` prop, `Escape` to close editor.
3. Replace the `<textarea>` in `InlineEditor.tsx` with `DeskEditor`
   for note, artifact, and KB editing paths.
4. Replace the pullout note textarea in `Pullout.tsx` with the same
   `DeskEditor`, preserving explicit-commit semantics (Cmd+Enter to
   save, Escape to discard).
5. Wire `MicButton` to insert at cursor position via CM6's
   `dispatch({ changes: { from: cursor, insert: text } })`.
6. Verify `Material.tsx` rendering still matches — the editor and
   renderer must agree on the supported markdown subset.

## Test plan

- Unit: `DeskEditor` renders, accepts markdown input, fires onChange
  with debounce, responds to Cmd+B/I/Z shortcuts.
- Unit: `InlineEditor` with CM6 saves note body on change, closes on
  Escape, focuses on open.
- Unit: `Pullout` note edit with CM6 saves on Cmd+Enter, discards on
  Escape.
- Unit: `MicButton` appends at cursor position, not end of document.
- Integration: open a note on the spatial desk, type markdown, close,
  reopen — rendered output in `Material.tsx` matches what was typed.
- Screenshot walk: 1440px desktop and 393px mobile, editor open on a
  note with mixed markdown content. Editor must feel like a Desk
  window interior, not an embedded IDE.
- Bundle size check: CM6 additions must not exceed 150KB gzipped in
  the production build.
