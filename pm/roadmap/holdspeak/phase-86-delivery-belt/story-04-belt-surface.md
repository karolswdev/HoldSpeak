# HS-86-04 — The belt surface on the web desk

- **Project:** holdspeak
- **Phase:** 86
- **Status:** backlog
- **Depends on:** HS-86-03
- **Unblocks:** HS-86-05
- **Owner:** unassigned

## Problem

The factory floor needs to LOOK like one: belts you can read at a
glance across every project in the headquarters — which are moving,
which are stalled and why — in the desk's own grammar, not a
dashboard of tables. This is the craft story; the bar is the DeskOS
philosophy (memory: high UI standards; flat/basic gets rejected).

## Scope

- In: `/belt` as a React island page (Astro shell only), desk-first:
  one belt lane per registered repo — phase segments (closed dimmed,
  current lit), story objects riding the current phase's segment with
  status-shaped chips (Signal tokens; the workbench node-canvas
  visual language is the nearest kin), station lights at the lane's
  head: gate (last gate event pass/refusal — a refusal wears its rule
  as an in-world chip), PR (open PRs + check conclusions as lights),
  close (final-summary presence); the agent lane: `dw sessions`
  correlations pinned to their story objects (`on_story`), honest
  off-belt shelf for the rest; the rail-events ticker (refusal-first);
  evidence opens IN PLACE (pull-out panel, the desk pattern — never a
  modal, never a route away); `scope:"belt"` frames refresh the lane
  live; TopNav entry per the Studio tier rules (Phase 70 IA).
- Out: any action affordance that mutates (no approve, no dispatch —
  B2 renders the empty hands honestly); iPad (B4); theming beyond
  Signal.

## Acceptance criteria

- [ ] `/belt` renders both real belts from `/api/belt/state`;
      screenshots in evidence show: the two lanes, a lit current
      phase, story chips, station lights, the agent lane with a live
      correlated session, an evidence file opened in place, and a
      gate-refusal chip (captured against a staged refusal).
- [ ] No prose, no modals: the desk-lock patterns extended to the
      belt tree (`test_desk_locks.py` or a sibling) — no
      `role="dialog"`, no reassurance copy; labels state WHAT.
- [ ] Live update: a story flip in a registered repo appears on the
      belt without reload (frame-driven), shown in the HS-86-05 walk.
- [ ] Page-content tests cover the built surface; web bundle rebuilt
      from `web/src`; api-surface regenerated after this consumer
      lands; full suite green.

## Test plan

- Unit: page-content tests (source markers) + lock tests.
- Integration / Cypress: screenshot set via the existing Playwright
  scripts against the live hub.
- Manual / device: the owner's glance test — which belts move, which
  stall, why, in one look.

## Notes / open questions

- Density: two belts today, N later — the lane must summarize (counts
  + current phase) before it itemizes; overflow is a portfolio, not a
  scroll of doom.
