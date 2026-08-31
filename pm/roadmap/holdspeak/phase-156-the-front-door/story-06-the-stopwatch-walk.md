# HS-156-06 - The stopwatch walk and the close

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** HS-156-01, HS-156-02, HS-156-03, HS-156-04, HS-156-05
- **Unblocks:** HS-155-01
- **Owner:** unassigned

## Problem

The Front Door is claimed only against a stopwatch: a cold owner
reaches a working chat turn AND a working dictation in under 60
seconds, without reading anything twice (settled design D5). The bar
is measured, not vibed.

## Scope

- **In:** the stopwatch rig (glass, real hub): from a fresh desk AND
  from an owner-shaped desk (legacy config + explicit LAN endpoint
  seeded), drive the door path — open Models, pick the recommended
  pack, confirm, wait for wired — then a real chat turn (fake engine
  at the endpoint) and a real transcribe; assert wall-clock < 60 s
  excluding download transfer time (reported separately, with sizes).
  Metal: apply a pack wiring the REAL .43 server, prove a live turn.
  Glass 1440 + 393 shots of every door state AND the topology map; exhibit artifact. Docs:
  README quick start rewritten around the door; USER_GUIDE Models
  section reframed (door first, advanced under it). Close counsel;
  honest sweep incl. `npm --prefix web run check` (the new close law).
- **Out:** Phase 155 The Crew (unblocked after).

## Acceptance criteria

- [ ] Stopwatch: both starting shapes meet the bar; the number ships in the evidence (and the exhibit).
- [ ] Metal: the .43 pack applies and a live turn answers; payloads kept.
- [ ] Glass both widths, zero overflow; exhibit link in the evidence; counsel zero open must-fix; docs rewritten; sweep name-diff clean vs main + the web contract green.
- [ ] The owner's own verdict on his real desk is requested with the exhibit — the merge word is his.

## Test plan

- **Unit:** the full scoped 156 set.
- **Integration:** the stopwatch rig; the glass file; the metal script.
- **Manual / device:** the owner's real-desk walk holds the merge word.

## Notes / open questions

- If the stopwatch fails, the phase is not done — cut scope elsewhere, never the bar.
