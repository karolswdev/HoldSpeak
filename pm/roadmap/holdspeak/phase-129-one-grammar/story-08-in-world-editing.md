# HS-129-08 — In-world editing: the lightbox dies

- **Project:** holdspeak
- **Phase:** 129
- **Status:** done
- **Depends on:** HS-129-07
- **Unblocks:** HS-129-11
- **Owner:** unassigned

## The thesis (the bar)

Article VII.2: no modals. `InlineEditor` (desk/components/InlineEditor.tsx:
34-49; inline-editor.css:76-104) is a fixed-position lightbox with a
click-to-dismiss vignette — a modal wearing desk clothes. It hosts
Note/KB/Recipe/Workflow editing, steals focus without returning it to the
opener, and carries raw z-indexes (24/26) outside the ladder.

### What changes

1. Editing happens in-world: the editor renders inside the object's own
   pullout/window (the primitive kinds already have pullouts with edit
   affordances — the editors mount there), or as a standard
   `DeskWindowFrame` window when a primitive is edited from the desk
   surface with no pullout open. The vignette and fixed positioning die.
2. Focus contract: opener-return on close, Escape via the standard window
   path (DeskWindow.tsx:728-742) — no competing document listener.
3. inline-editor.css sheds its private select/editor skins (adopts shared
   controls, per audit D §5) and its raw z-indexes.
4. ShortcutSheet and the attention/system overlays are OUT of scope — they
   are OS chrome; their constitutional exemption is documented in
   HS-129-10's notes instead.

## Acceptance criteria

1. No `desk-vignette`, no fixed-position editor panel; creating/editing a
   Note, KB, Recipe, and Workflow happens in a real window or pullout with
   window physics (drag, Escape, focus-return).
2. Editing still autosaves/commits exactly as before (no behavior change in
   the write path).
3. `grep "position: fixed"` in editor CSS returns nothing; the two raw
   z-indexes are gone.

## Test plan

- Web: editor-mount tests per kind (opens in window/pullout, Escape closes,
  focus returns to opener); write-path regression tests stay green.
- Walk: open each of the four editors from the desk at 1440 — screenshot
  proves in-world placement (desk visible and interactive around it).
