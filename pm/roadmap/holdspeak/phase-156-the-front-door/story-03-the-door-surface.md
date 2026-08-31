# HS-156-03 - The door surface: pack cards, the health strip, the advanced fold

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** HS-156-01, HS-156-02
- **Unblocks:** HS-156-04, HS-156-05
- **Owner:** unassigned

## Problem

Settings → Models must open on a door, not an engine room: three pack
cards and one confirmation when unconfigured; a one-line health strip
with the whole advanced layer folded underneath once configured
(settled design D3; the owner's B: "easy to then go in and dig").

## Scope

- **In:** the door view inside the existing Models settings surface:
  when any group is unassigned → pack cards (name, one line per job,
  total download size, Balanced marked recommended) + "Set up my own"
  (jumps to the advanced layer); confirm → the live plan view (per-item
  progress from 02, in-flow, no modal); done → the health strip
  ("Everything wired · Balanced · change") above the UNCHANGED advanced
  Library/Assignments view. Every attention state anywhere on the
  Models surface names ONE next action and carries its button. Desk
  tokens, keyboard reachable, 393-safe.
- **Out:** wording overhaul beyond the door path (04), removing any
  advanced capability (forbidden).

## Acceptance criteria

- [ ] vitest: unconfigured state renders the cards (complete per-job lines, sizes); confirm posts apply and renders the live plan; configured state renders the strip + the advanced fold opens; an attention state renders exactly one action button.
- [ ] Glass 1440 + 393 on a real hub: fresh desk → cards; apply a stub pack → plan progresses to wired → strip appears; the advanced fold still exposes Library + Assignments fully; zero overflow. Shots both widths.
- [ ] Zero features removed from the advanced layer (the existing Library/Assignments vitest suites still pass untouched).

## Test plan

- **Unit:** vitest `frontDoor.test.tsx`.
- **Integration:** glass legs `door-cards`, `door-apply`, `door-strip` in `tests/e2e/test_hs156_front_door_glass.py`.
- **Manual / device:** story 05.

## Notes / open questions

- The door lives IN the Models surface — no new room, no wizard modal (no-modals law).
