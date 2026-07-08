# HS-90-02 — The manipulation surface on the web desk

- **Project:** holdspeak
- **Phase:** 90
- **Status:** backlog
- **Depends on:** HS-90-01
- **Unblocks:** HS-90-03

## Problem

Phase 89 shipped full manipulation as routes; there is no way to DO it
from the desk. This is the fast-follow UI the owner asked for: drive a
terminal from glass, not `curl`.

## Scope

- In: on the web desk's session surface (the Phase-87 SessionPullout /
  steer composer, `web/src/desk`): a KEY PALETTE (buttons for `C-c`,
  `Escape`, arrows, `Tab`, `Enter` → `POST /keys`) shown only while
  armed; a PANE PICKER (reads `GET /api/coders/steering/panes`, attach to
  any `pane:%N`); a NODE CHIP (target a configured node, routing through
  the relay). Screenshot-proven on the running desk.
- Out: the factory controls (HS-90-03); mobile/iPad (that surface is the
  B4 track); a full terminal emulator.

## Acceptance criteria

- [ ] The key palette appears only in the armed window and sends real
      keys through `/keys`; each key is a clear, labeled affordance
      (not raw text).
- [ ] The pane picker lists live panes with session/command/title and
      attaches to any by its `pane:%N` key (watch free; arm to steer).
- [ ] The node chip targets a configured node; steers/keys route through
      the relay; an offline node shows the honest `node_offline` state.
- [ ] Built (`npm run build`) and screenshot-verified on the running
      desk; the egress/consent cues stay honest.
- [ ] Guards green (density/lint as applicable); `swift`/py suites
      unaffected.

## Implementation direction

- Extend the existing session pull-out, do not add a new screen. The
  key palette is a small row of buttons that POST a single named key.
- The pane picker is a list backed by `/panes`, each row an attach
  action; reuse the arm chip for steering.
- Keep the consent legible: keys/kill only in the armed window; the
  countdown stays visible.
- React + Vite (the standing web stack); build to verify, screenshot the
  running desk (the Phase-73+ pattern).
