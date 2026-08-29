# HS-149-03 — The gesture (picker + rail person chip)

- **Project:** holdspeak
- **Phase:** 149
- **Status:** ready
- **Depends on:** HS-149-02
- **Unblocks:** HS-149-06
- **Owner:** unassigned

## Problem

The Tuesday probe (a): with "1:1 w/ Ewa" on the rail there is no
person affordance anywhere (walk: DOES NOT EXIST). The link needs
its explicit gesture and its visible payoff.

## Scope

### In (settled-design D3, D4)

- PeopleCore relationship detail gains "Link calendar event…":
  upcoming events listed (title + next occurrence + source label),
  display_name-matching rows suggested first, NOTHING auto-links —
  the click is the gesture; in-world two-beat unlink beside it.
- door_service projects `person_label` onto LINKED calendar event
  items (read-time via the 02 resolution; sidecar unavailable → no
  chip, Door never blocks); the rail row wears a quiet mono person
  chip; PeopleCore's header shows "NEXT 1:1 · <when>".
- The People unconfigured/empty state adopts the joy pattern (lead
  with the act — the walk's era-mismatch note).
- Shots before done-claim: linked rail chip + picker + joy empty
  state, 1440+393, cross-read.

### Out

- The brief (04); Monday Brief; 393 reachability (ledgered).

## Acceptance criteria

1. The full gesture on glass: open person → picker → pick the
   series → the rail row wears the person chip within one
   re-fetch; unlink removes it.
2. Suggestions never auto-link (a pin proves no link without the
   click).
3. Joy: the empty state leads with the act; both widths clean.

## Test plan

PeopleCore component tests (picker, suggestions, unlink, joy
state), door service projection tests, DoorBoardLane chip test,
live shots via the story-06 rig patterns (through the 01 seam).
