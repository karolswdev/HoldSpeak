# HS-111-11 - The terminal pane

- **Project:** holdspeak
- **Phase:** 111
- **Status:** done
- **Depends on:** HS-111-04
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## Problem

The owner reviewed the shipped crew console (HS-111-04) and ruled:
"those panes need to be runnin' on xterm.js... and be a lot more
utility-oriented." He is right about what shipped: the session
pullout's script well renders a PHOTOGRAPH of the pane, not the pane
— the Phase 87 peek wire strips ANSI server-side and caps at 200
lines/64 KB, so colors, cursor position, and terminal layout are
thrown away before the glass ever sees them. An operator's console
shows the actual wire.

## The thesis (the bar)

**The pane well becomes a real terminal.** xterm.js renders the raw
ANSI stream — true colors, cursor, layout — inside the same sunken
SurfaceWell frame, themed to Signal Workbench tokens (opaque fills,
2px, mono; xterm's theme API takes the palette; no glow cursor
styles). And the pullout gets utility-dense: searchable scrollback,
selection that copies, the density facts an operator wants at hand.

## Scope

- **In:**
  - A RAW peek mode on the coder read path (`coder_steering.peek_pane`
    + the `/api/coders/{key}/peek` route): ANSI passthrough behind an
    explicit `raw=1` param, same hash gate, same caps (or a raised
    byte cap argued honestly), stripped mode remains the default for
    existing consumers. Read-only; the CONSENT SPINE (arm/steer wire,
    grants, refusals) stays byte-untouched.
  - xterm.js in the web bundle (measure the size cost honestly; lazy
    chunk if heavy), mounted inside the pane SurfaceWell in
    SessionPullout, themed from tokens.css values.
  - Utility pass on the pullout: scrollback search (xterm addon),
    copy-on-select, and the operator facts (lines, last-change age)
    as tokens.
  - Screenshot proof on the real hub against a real tmux pane, both
    viewports.
- **Out:** any write path through xterm (the terminal is a VIEWER;
  typing goes through the armed steer composer only — Article XI /
  Phase 87 law); WebSocket streaming (polling cadence stays unless a
  later story charters the stream); the Delivery terminal surfaces
  (story 06 territory unless it lands first and wants the same well).

## Acceptance criteria

- [ ] The pane well renders raw ANSI via xterm.js: colors and cursor
      visible on a real tmux pane on the real hub.
- [ ] The terminal is read-only — keystrokes do NOT reach the pane;
      the armed steer composer remains the only input path; steering
      wire and tests byte-unchanged.
- [ ] Stripped peek remains the default; `raw` mode is opt-in on the
      route; hash gate and caps enforced in both modes.
- [ ] Scrollback search and copy-on-select work; operator facts
      render as tokens.
- [ ] xterm themed to Signal Workbench tokens inside the SurfaceWell
      frame — no stock xterm chrome, no glow cursor.
- [ ] Live shots at 1440+393 against a real pane.

## Test plan

- **Unit:** peek raw-mode unit tests (ANSI passthrough, caps, hash
  gate parity); xterm mount smoke test (renders, read-only) in the
  web suite.
- **Integration:** `/api/coders/{key}/peek?raw=1` route test; the
  existing steering wire tests pass with ZERO edits (the proof the
  spine is untouched).
- **Manual / device:** a real tmux pane with colored output (e.g.
  `ls --color`, a vim session) rendered faithfully on the real hub.

## Notes / open questions

- Bundle cost of xterm.js (~300 KB min) — lazy-load the chunk with
  the pullout.
- Whether the Delivery terminal (story 06) adopts the same xterm
  well — decide in story 06's audit; the species should be ONE
  component (`TerminalWell`) either way.
- Polling redraw vs xterm incremental write: start with full-repaint
  on poll (simplest honest step); a streaming charter is a separate
  story if the cadence feels wrong on real metal.
