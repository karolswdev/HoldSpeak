# HS-120-09 — Window chrome repair

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The desk window chrome has accumulated structural CSS bugs, dead rules,
and orphaned classes. This story is a targeted repair pass on the shared
chrome layer that every window inherits.

When this ships:

1. **DeskWindowFooter** (`DeskWindowFooter.tsx`): The classes
   `desk-window-footer-status` and `desk-window-footer-actions` get
   real CSS definitions. The inline `style={{}}` object on the actions
   wrapper moves to CSS. Both classes are defined in `pullout.css` or
   `window-chrome.css`.

2. **InlineEditor close button** (`pullout.css:152-158`): The naked
   `x` character gets hover, focus, and active states matching the
   desk's traffic-light chrome pattern — or migrates to the
   DeskWindowFrame close mechanism entirely.

3. **`var(--muted)` typo** (`pullout.css:229`, `speak-to-fill.css`):
   Changed to `var(--text-muted)` in both locations. This is a real
   bug — `--muted` is not defined in the token system, so the
   declaration is invalid and labels inherit the wrong color.

4. **Sub-pixel border** (`pullout.css:255`): `0.9px` border changes
   to `1px` to match the system's border convention. Uses
   `var(--border)` instead of `var(--shade-1)` if shade-1 is not a
   defined token.

5. **Dead CSS removed:**
   - `.desk-empty-word` (`inline-editor.css:16`)
   - `.meeting-conflict-versions` (`react-app.css:506`)
   - `.symbol-row` responsive rule (`react-app.css:543`)
   - `.desk-chat-hello*` rules (`pullout.css:170, 367-391`) — only if
     RecipePullout migrates to `surface-record-head` (coordinate with
     story 06).
   - Duplicate `@media (prefers-reduced-motion: reduce)` block in
     `react-app.css` (keep the canonical one in `tokens.css`).

6. **CoderPullout empty footer** (`CoderPullout.tsx:176`): The
   self-closing `<footer/>` gets standard verbs (at minimum "Watch
   live" moves from the body to the footer).

## Acceptance criteria

- [ ] `desk-window-footer-status` and `desk-window-footer-actions`
      defined in CSS.
- [ ] Zero inline `style={{}}` in DeskWindowFooter.
- [ ] InlineEditor close has hover/focus states.
- [ ] `var(--muted)` replaced with `var(--text-muted)` everywhere.
- [ ] No sub-pixel border widths in pullout.css.
- [ ] Listed dead CSS rules removed.
- [ ] CoderPullout footer has at least one verb.

## Test plan

- Grep: `var(--muted)` with no `-text` prefix returns zero hits.
- Grep: `0.9px` returns zero hits.
- Grep: `desk-empty-word`, `meeting-conflict-versions`, `symbol-row`
  return zero hits outside git history.
- Visual: open DeskWindowFooter consumers, verify layout holds.
- Visual: open InlineEditor, hover/focus the close button, verify
  states.
- Visual: open CoderPullout, verify footer has verbs.

## Files in scope

- `web/src/desk/components/DeskWindowFooter.tsx`
- `web/src/desk/components/pullout.css`
- `web/src/desk/components/speak-to-fill.css`
- `web/src/desk/components/inline-editor.css`
- `web/src/styles/react-app.css`
- `web/src/desk/pullouts/CoderPullout.tsx`
- `web/src/desk/components/window-chrome.css` (if footer classes go here)
