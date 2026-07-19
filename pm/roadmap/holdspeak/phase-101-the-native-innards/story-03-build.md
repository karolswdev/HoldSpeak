# HS-101-03 — The build (authored at the gate, from the approved canon)

- **Project:** holdspeak
- **Phase:** 101
- **Status:** done
- **Depends on:** HS-101-02
- **Unblocks:** HS-101-04

## Problem

The approved interior canon (DESIGN_SYSTEM.md §"The interior canon
(HS-101)", amended and called by the owner 2026-07-19: "Well, merge
it in for me, and then keep going...") exists only as canon and
mockups. The interiors still compose as generic kit; six banned
accent rails still ship; the desk does not yet answer the hand with
motion.

## The ledger (each item lands as its own gated commit with its guard)

- **B1 — The kit and the rail-ban guard.** The aerogel inset as a kit
  piece on `--desk-aerogel-*`; ALL six shipped `border-left` accent
  rails die (surface.css `.surface-preview`, desk.css ×5); interior
  type-scale classes riding `--desk-type-*`; `EditInPlace`
  (presented text swaps to a same-geometry editor; Enter/blur
  commits, Escape reverts; disabled states name why).
  *Guard: `tests/unit/test_interior_canon_guard.py` — any
  accent-colored `border-left` in web/src CSS fails BY file:line;
  vitest covers EditInPlace grammar.*
- **B2 — The fluid desk.** Operating motion product-wide: wing
  crossfade, verb reveal eased on the tokens, list/stream entries
  settle in, aerogel receipts inflate from their row, transient
  surfaces spring. Compositor-only, `--duration-*`/`--ease-*` only,
  instant under reduced motion; idle never moves.
  *Guard: the canon guard grows a fluidity census — the named
  operating selectors must declare token-riding transitions.*
- **B3 — The Journal as a dated stream.** `SurfaceStream` kit
  (count-at-display head, day headers, primary-step entry text,
  secondary meta, hover verbs on the entry, aerogel replay preview);
  Journal rebuilt on it; edit-in-place on the transcript record
  (corrections stay the taught act).
  *Guard: the B8 interior assertions cover `dictate`; vitest on the
  stream grouping; live-viewport shots at 1440 + 393.*
- **B4 — Blocks as a library.** `SurfaceLibrary` tiles: the injection
  text IS the face, name + spoken matches on the spine, ghost create
  tile in the shelf (no side form), edit-in-place on the tile.
  *Guard: interior assertions cover the blocks wing; vitest on the
  library composition.*
- **B5 — Runs on as a switchboard.** `SurfaceSwitchboard` bays: the
  default bay leads with its model at display step, lamps never
  color-only, offline names its reason from liveness, boundary badge
  on the bay, "Make default" as a bay verb.
  *Guard: interior assertions cover `configure-runs-on`; vitest on
  bay states incl. the named offline reason.*
- **B6 — The system shade.** `SystemShade` behind the bell: the
  approve queue with inline verbs + egress badges, finished
  intelligence, learned corrections, recovered captures — honest
  counts at zero, real dismiss; replaces the AttentionDrawer face on
  the same projections feed.
  *Guard: vitest on the four groups + honest zero; the chrome walk
  leg opens it.*
- **B7 — Through the glass.** Drag-and-drop as a system verb: a
  .vtt/.srt/.txt or audio file dropped on the desk imports a
  Meeting (existing import routes); a desk object drags into the
  ask/steer composer as grounding; a result chip drags out onto the
  desk and is kept (existing keep-note path). Drop targets light
  before the drop; refused drops name why.
  *Guard: vitest on the drop contract (kind × target matrix incl.
  refusals); a walk leg proves the file-drop import live.*
- **B9 — The agent panes and the delivery rails wear the canon**
  (added mid-build at the owner's ask: "hoping the panes, you know,
  agent panes..., and the delivery-workbench integration"). The
  steering pull-out / terminal pane composes as a SCRIPT (the pane
  text is the material; the asked question already floats in aerogel
  from B1), verbs on the material, the type scale inside; the
  DeliveryBoard / dossier surfaces compose as receipts on the same
  scale. Survey what the advanced delivery-workbench now serves
  (the local rails read through `.githooks/dw` — newer receipts
  land as available); a deeper dw re-integration beyond the surfaces
  is recorded as a rider for its own phase.
  *Guard: the B8 interior assertions cover the pane and delivery
  windows; vitest on the script composition.*
- **B8 — The keyboard grammar and the grown walk.** ⌘1–⌘4 open the
  four applications, ⌘W closes and ⌘M minimizes the front window,
  ⌘/ draws the shortcut sheet; `desk_gl_walk.py geometry` grows the
  interior assertions (≥3 type-scale steps per registered face;
  label+input stacks outside configuring faces fail; the 360px
  squeeze holds).
  *Guard: the grown geometry leg in the chain; the chrome leg
  exercises the shortcuts.*

Route note, recorded honestly: the scaffold's "no new routes" out-
scope predates the gate. The approved canon requires minimal writes
the wire does not carry today (journal transcript update; block
update/delete). They land as the smallest possible additions inside
B3/B4, named in their commits; everything else rides existing routes.

## Acceptance criteria

- [x] B1 — kit + rail ban (zero `border-left` accent rails ship)
- [x] B2 — the fluid desk
- [x] B3 — the Journal stream
- [x] B4 — the Blocks library
- [x] B5 — the Runs-on switchboard
- [x] B6 — the system shade
- [x] B7 — through the glass
- [x] B8 — keyboard grammar + the grown geometry walk, green in the
      chain
- [x] B9 — the agent panes + the delivery rails wear the canon
      (the dw re-integration recorded as its own-phase rider)

## Test plan

Per-item guards above; `uv run pytest -q` (metal excluded) + vitest +
the walk legs against a staged hub; live-viewport screenshots at 1440
AND 393 for every interior; headed where headless lies.

## Evidence required

- One captured run per ledger item; the shots; the grown walk output.
