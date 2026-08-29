# HS-147-02 — The tap (rail verb + armed state, web)

- **Project:** holdspeak
- **Phase:** 147
- **Status:** done
- **Depends on:** HS-147-01
- **Unblocks:** HS-147-07
- **Owner:** unassigned

## Problem

The walk proved the job impossible: an EVENT row is a passive
`<li>` (`DoorBoardLane.tsx:260-305`; shots
`door-event-click-*.png`), and the only path is the generic form
with zero pre-fill — 2 clicks plus retyping title and time by hand.

## Scope

### In (settled-design D6)

- **RECORD THIS** inline button on each `calendar_event` row of
  `UpcomingRail` (the DoorCard `lawful_verbs` button precedent,
  `DoorBoardLane.tsx:454-499`); placement per the walk — right
  column under STARTS at 1440, `grid-column: 2 / -1` line at 393.
  In-world, no modal, no form.
- Store action `armEventRecording(eventId)` calling the story-01
  endpoint; Door re-fetch on completion (the existing
  `scheduledRecordings`-store trigger, `DoorBoardLane.tsx:335-345`).
- Armed state: when `armed_schedule_id` is present the button
  becomes an **ARMED** chip + **CANCEL?** in-world verb (existing
  cancel/delete authority; two-beat confirm per house grammar, no
  modal).
- Refusals render in-flow ON the row (named, fewest words, never
  prose, never overlapping UI).
- `DoorUpcomingItem` type gains `armed_schedule_id?`
  (`DoorBoardLane.tsx:39-52`); `commandForDoorVerb` table extended
  only if the verb dispatch rides it (`:114-162`) — a direct store
  action is equally lawful; builder picks the smaller diff.
- Keep the Door glass e2e files green (`test_hs144_door_glass.py`,
  `test_hs145_door_polish_glass.py`, `test_hs146_*` if they
  photograph the rail): new row geometry is this story's fallout to
  own.
- Screenshot-walk before claiming done: live shots at 1440 AND 393 —
  unarmed row with RECORD THIS, armed row with ARMED + CANCEL?, a
  refusal in-flow — cross-read against each other (times must
  agree).

### Out

- Reconciliation surfacing (03); Meetings-surface origin line (04);
  the walk-script leg (07).

## Acceptance criteria

1. One tap on RECORD THIS arms the event's recording — no other
   input; the rail reflects ARMED within one re-fetch.
2. CANCEL? on an armed row returns it to RECORD THIS; the schedule
   is gone/disabled server-side.
3. A refusal (e.g. already armed from another tab) renders on the
   row, in-flow, named.
4. Both widths clean: no overflow, no occlusion, geometry verified
   by shots; existing glass e2e green serially.
5. Does it operate with joy — the affordance reads instantly, the
   armed state is unmistakable, visible feedback ≤500 ms.

## Test plan

`web/src/desk/chair/lanes/DoorBoardLane.test.tsx` (button/chip/
refusal render rules, armed swap), store action unit test, the two
Door glass e2e files serially, live Playwright shots (1440 + 393)
against the real hub.
