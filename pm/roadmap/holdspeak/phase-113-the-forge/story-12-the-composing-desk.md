# HS-113-12 - The composing desk

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-02
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The editor must be a COMPOSING tool, not a developer scratchpad.
Notes are .md files — the editor must make markdown first-class
with visible formatting affordances. A user who doesn't know
markdown syntax should still be able to bold text, add a heading,
and make a list. Cmd+B, Cmd+I, and a compact toolbar are the
floor. This is an OS-level editor for an Architect's daily work.

**Articles served:** VII (the interface serves), VIII (native-grade
craft — a real text editor, not a syntax exercise).

## Ground (from the behavioral audit)

- `web/src/desk/components/DeskEditor.tsx` — CodeMirror 6 with
  markdown language mode and syntax highlighting. No formatting
  toolbar. No Cmd+B or Cmd+I keybindings. The only formatting
  affordance is the voice grammar (`editorVoiceGrammar`) which
  knows "bold that" / "italic that" — completely invisible to
  keyboard/mouse users.
- `web/src/desk/components/EditorAIBar.tsx` — the AI bar has
  Rewrite/Expand/Summarize/Continue but no basic formatting.
  It appears on text selection — the user must select text
  AND wait 300ms to see any toolbar at all.
- `web/src/desk/surface/Material.tsx` — the markdown renderer
  supports headings, bold, italic, code, links, lists. The
  editor should produce all of these with visible buttons.

## Method

1. **Formatting toolbar** — a fixed row of compact buttons above
   the CodeMirror editor area, inside the DeskEditor component:
   - **B** (bold, Cmd+B) — toggles `**` around selection
   - **I** (italic, Cmd+I) — toggles `*` around selection
   - **H** (heading cycle) — cycles `#` / `##` / `###` / none
     on the current line
   - **UL** (unordered list) — toggles `- ` prefix on selected
     lines
   - **OL** (ordered list) — toggles `1. ` prefix on selected
     lines
   - **`** (code) — toggles backticks on selection (inline) or
     fenced block for multi-line
   - **>** (quote) — toggles `> ` prefix on selected lines
   - **[ ]** (link) — wraps selection in `[text](url)` template

2. **Keybindings** — Cmd+B (bold), Cmd+I (italic) added to the
   CM6 keymap. The toolbar buttons show the shortcut as a tooltip.

3. **Toggle logic** — if the selection is already wrapped in the
   marker (e.g., `**text**`), clicking Bold removes the markers.
   If not wrapped, it adds them. For line-prefix operations
   (heading, list, quote), toggle the prefix on every line in
   the selection.

4. **Toolbar styling** — `desk-chip quiet` class for each button.
   Compact: 24px height, mono font, grouped with hairline
   separators. Active state when the cursor is inside a formatted
   range. The toolbar is part of DeskEditor, controlled by a
   `showToolbar` prop (default: true).

5. **DeskEditor `showToolbar` prop** — callers that want a
   minimal editor (e.g., inline rename fields) can pass
   `showToolbar={false}`.

## Test plan

- Unit: Cmd+B on selection wraps in `**`, Cmd+B again removes.
- Unit: Cmd+I on selection wraps in `*`, Cmd+I again removes.
- Unit: heading button cycles `#` / `##` / `###` / none.
- Unit: UL button toggles `- ` on each selected line.
- Unit: code button wraps inline selection in backticks, wraps
  multi-line in fenced block.
- Unit: toolbar buttons show active state when cursor is inside
  formatted range.
- Visual: toolbar renders as a compact row above the editor,
  matches the Desk aesthetic.
- Screenshot walk: 1440px — editor open on a note with toolbar
  visible, a heading and bold text showing active states.
