# HS-144-03 — The kanban on glass

- **Project:** holdspeak
- **Phase:** 144
- **Status:** backlog
- **Depends on:** HS-144-01
- **Unblocks:** HS-144-04
- **Owner:** unassigned

## Problem

Obligations are split across three renderings of the same truths
(BriefLane, FollowThroughLane, the Intelligence pullout's
FollowThroughView) with no single composed view and no headline count
(audit B). The owner's TODO reality lives one click deep in a pullout.
The Door's kanban puts it ON the front door.

## Scope

### In

- **Reforge ChairHome's lane half** (`web/src/desk/chair/
  ChairHome.tsx:38-63`, `laneContract.ts:26-31`) — replace, never sit
  beside: the follow-through and brief lanes give way to the Door
  board rendered from `GET /api/door`. The hero (ThoughtEntry) and
  the First Sentence gate (`DeskApp.tsx:137-196`) are UNTOUCHED.
- **The board**: columns from the aggregate (now / waiting /
  unassigned / overdue / active-thoughts). Cards show source, age/due,
  owner where present. Every card action calls the EXISTING verb the
  aggregate named (complete, dismiss, snooze, commit-decision,
  thought resume/complete; settled design §2) and renders the
  receipt in-flow — errors never overlap UI. A card with no lawful
  verb renders no affordance. No modals; anything editable edits
  in-world.
- **The headline counts** from the aggregate — the first honest
  "3 overdue, 2 waiting" in the product. Labels state WHAT in fewest
  words; no prose.
- **Brief access survives**: the Monday Brief remains reachable from
  the Door (its pullout entry point stays; only the lane real estate
  is reforged). Nothing the old lanes could do becomes unreachable —
  the walk (HS-144-06) asserts this.
- **The shared-file law honored in-slice**: touching
  ChairHome/laneContract drags the Chair, First Sentence, lane, and
  Intelligence-pullout e2e files into this story's net — the plan
  NAMES them and the story runs them.
- Both widths (1440 + 393) built and shot; empty, populated, and
  error states; beauty pass after the functional pass.

### Out

- The upcoming rail and schedule-create (HS-144-04).
- New write verbs or backend changes (glass consumes HS-144-01 as-is;
  a missing need goes back to 01, not into an ad-hoc route).
- Drag-reordering WITHIN a column (no board-position store — settled
  design §2).

## Acceptance criteria

- [ ] The Door board renders the five columns from `GET /api/door`
  with honest counts; the old FollowThroughLane/BriefLane lane slots
  are replaced, not duplicated (tests + grep that the replaced lane
  components are gone or exclusively re-homed).
- [ ] Every card action round-trips a real verb and shows its receipt
  in-flow; a verb failure renders the refusal honestly (tests).
- [ ] First Sentence cold-open is byte-identical in behavior: fresh
  HOME still opens on the one job (e2e).
- [ ] The named neighbor e2e files all pass in this story's focused
  net (list them in the evidence).
- [ ] Live shots at 1440 + 393 (+200% zoom leg): populated, empty,
  and error states, zero console errors, zero horizontal overflow.

## Test plan

- `(cd web && npx vitest run)` — board, cards, counts, verb
  round-trips.
- Real-hub Playwright e2es for the Chair/First-Sentence/pullout net,
  isolated HOME.
- Shots folded into evidence; owner sees them before any merge word.
