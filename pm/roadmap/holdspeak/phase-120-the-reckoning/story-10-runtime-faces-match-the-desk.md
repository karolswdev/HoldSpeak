# HS-120-10 — Runtime faces match the desk

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Two runtime surfaces use pre-Signal or token-bypassing visuals:

1. **PresencePage** (`web/src/pages/PresencePage.tsx`): Renders a
   centered card with a circular pulsing orb, glow halo, `elev-3` box
   shadow, and `radius-lg` border-radius. Uses raw `<strong>`, `<p>`,
   `<small>` with no surface kit. Has no navigation affordance to
   return to the desk. Says "Waiting for activity." in prose where the
   desk says "no prose in the UI." Pre-Signal material on a current
   route.

2. **WorkbenchCanvas** (`web/src/styles/react-app.css:229-236`):
   Hardcoded `background-color: #0b0c10`, dot-grid uses
   `rgba(255,255,255,0.13)`, node port borders use `3px solid #0b0c10`
   to fake transparency. All bypass the token system. If a light theme
   ever ships, this surface breaks.

When this ships:

1. PresencePage uses `LampGadget` for state indication, desk-grade
   depth tokens (`var(--desk-window-etch)`), no circular orb or glow
   halo. State labels are tokens ("IDLE", "LISTENING", "WORKING"),
   not prose. A minimal nav affordance ("Back to Desk" chip or link)
   is present.

2. WorkbenchCanvas uses `var(--bg)` for the canvas background,
   `var(--text-faint)` or `var(--border)` for the dot-grid, and
   `var(--bg)` for port borders. Zero hardcoded hex colors.

## Acceptance criteria

- [ ] PresencePage: no circular orb, no glow halo, no `elev-3`.
- [ ] PresencePage: uses LampGadget and desk tokens for state.
- [ ] PresencePage: has a nav affordance back to the desk.
- [ ] PresencePage: no prose sentences in the UI.
- [ ] WorkbenchCanvas: zero hardcoded hex colors.
- [ ] WorkbenchCanvas: uses `var(--bg)`, `var(--text-faint)` or
      similar tokens.

## Test plan

- Visual: navigate to /presence, verify desk-grade material.
- Visual: click "Back to Desk" (or equivalent), verify it works.
- Visual: open the workbench workflow editor, verify canvas renders
  with token-based colors.
- Grep: `#0b0c10` returns zero hits.

## Files in scope

- `web/src/pages/PresencePage.tsx`
- `web/src/styles/react-app.css` (canvas rules)
