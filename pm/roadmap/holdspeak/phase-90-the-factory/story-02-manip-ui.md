# HS-90-02 — The manipulation surface on the web desk

- **Project:** holdspeak
- **Phase:** 90
- **Status:** done
- **Shipped:** 2026-07-08 — you drive a terminal from glass now. The armed session pull-out gained a key palette (`^C`/`Esc`/`Tab`/`⏎`/arrows → `/keys`), a `⧉ Panes` picker (attach to any `pane:%N`), and a node chip (this Mac / a configured node, routing through the relay). Built + desk tests 97/97 + screenshot-verified. Evidence: [evidence-story-02.md](./evidence-story-02.md), [screenshots](./screenshots/).
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

- [x] The key palette appears only in the armed window (in the
      `SteerComposer` footer) and sends real keys through `/keys`; each
      key is a clear labeled cap, `^C` styled loud (interrupt).
- [x] The `⧉ Panes` picker reads `GET /api/coders/steering/panes` and
      attaches to any by its `pane:%N` key (`openSession("pane:%N")`);
      the active pane is marked; watch free, arm to steer.
- [x] The node chip targets a configured node (`GET .../nodes`, names
      only); a node routes arm/steer/keys/peek through the relay
      (`verbEndpoint`); absent config reads the honest "this Mac".
- [x] Built (`npm run build`) + desk tests 97/97 + tsc clean;
      screenshot-verified on the running desk (armed key palette + the
      pane picker). The consent cues stay honest (keys armed-only, the
      countdown visible).
- [x] Live hub + tmux end-to-end is HS-90-03's walk; the screenshot here
      is the built desk driven with Phase-89/90-shaped API responses.

## Implementation direction

- Extend the existing session pull-out, do not add a new screen. The
  key palette is a small row of buttons that POST a single named key.
- The pane picker is a list backed by `/panes`, each row an attach
  action; reuse the arm chip for steering.
- Keep the consent legible: keys/kill only in the armed window; the
  countdown stays visible.
- React + Vite (the standing web stack); build to verify, screenshot the
  running desk (the Phase-73+ pattern).
