# HS-113-15 - Discoverability

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-04
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every feature the Desk has must be FINDABLE. Today, Cmd+J (AI
editor bar) has no visual hint. The Ask composer has no keyboard
shortcut. The keyboard shortcuts sheet (Cmd+/) is itself
undiscoverable. Formatting commands exist in the voice grammar
but are invisible to keyboard/mouse users. An OS where features
are built but not findable is a half-built OS.

**Articles served:** VII (the interface serves — affordances are
visible, ghosted verbs with reasons over hidden verbs), VIII
(native-grade craft — keyboard grammar).

## Ground (from the behavioral audit)

- `web/src/desk/components/EditorAIBar.tsx` — appears on text
  selection + 300ms delay or Cmd+J. No visual hint that Cmd+J
  exists. No tooltip. No menu entry.
- `web/src/desk/verbRegistry.ts` — no `desk.ask` verb with a
  key binding. The Ask composer has no keyboard shortcut.
- The keyboard shortcuts sheet (Cmd+/) shows existing bindings
  but Cmd+/ itself is not hinted anywhere in the UI.
- `web/src/desk/components/InlineEditor.tsx` — the MicButton is
  visible but its voice grammar capabilities (formatting
  commands, desk commands) are not described anywhere.
- No onboarding or hint system exists for new users.

## Method

1. **Cmd+J hint in editor** — when the CodeMirror editor is
   focused and has a non-empty selection, show a subtle hint
   line below the toolbar: "Cmd+J for AI" (10px, muted, mono).
   Disappears after the user uses Cmd+J once (tracked in
   localStorage).

2. **Ask keyboard shortcut** — register a `desk.ask` verb in
   the verb registry with `key: "Mod-Shift-a"`. Action:
   `openAsk()` from the store. Ghost: never (always available).

3. **Cmd+/ hint in the system bar** — add a small "?" button
   next to the clock in the chrome bar that opens the keyboard
   shortcuts sheet. Tooltip: "Keyboard shortcuts (Cmd+/)".

4. **Keyboard shortcuts sheet improvements** — add all new
   bindings to the sheet:
   - Cmd+N — New note
   - Cmd+J — AI bar (when editing)
   - Cmd+Shift+A — Ask
   - Cmd+B — Bold (when editing)
   - Cmd+I — Italic (when editing)
   - Delete/Backspace — Delete selected object

5. **Editor placeholder improvement** — change the CodeMirror
   placeholder from "Write" to "Write markdown — Cmd+B bold,
   Cmd+I italic" for the first-use state. After the user has
   typed once, revert to just "Write" (tracked in localStorage).

## Test plan

- Unit: Cmd+J hint appears when editor has a selection,
  disappears after first use.
- Unit: Cmd+Shift+A opens the Ask composer.
- Unit: "?" button in the chrome bar opens the keyboard
  shortcuts sheet.
- Unit: the shortcuts sheet lists all new bindings.
- Screenshot walk: 1440px — editor with selection showing
  "Cmd+J for AI" hint, chrome bar with "?" button visible.
