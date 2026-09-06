# HS-175-06 — The walk

- **Project:** holdspeak
- **Phase:** 175
- **Status:** done
- **Depends on:** HS-175-05
- **Unblocks:** HS-175-08
- **Owner:** unassigned

## Problem

The owner's attended walk on his desk is the exit gate (Article IX.4).
Calendar and the Clock introduces new behavior (calendar events on the
desk, event-born recordings, the meeting Watch adapter, the week brief)
that must be proven on his real desk with a real calendar and real
meetings. The walk is the proof that the calendar gave the desk its
clock.

## Scope

- In:
  - The owner's attended walk on his desk, both widths (1440 + 393).
  - The walk covers:
    1. Calendar events appear on the desk from his connected calendar
       source (the 146 adapter).
    2. An upcoming meeting with a meeting_url auto-creates an armed
       recording; the provenance chip names the calendar source.
    3. He overrides the recording's title; the calendar event is
       unchanged.
    4. The Room shows a meeting Watch entity with decisions and
       commitments from a linked meeting.
    5. SINCE YOU LOOKED shows the meeting Watch entity delta.
    6. The brief in the shade shows the week frame: meetings count,
       Watch changes, commitments due, next event.
    7. The `next` seam in the Room header shows the next event.
  - The stopwatch per face (Article IX.2).
  - His verdict (Article IX.4).
- Out:
  - Automated rig legs (those are in stories 02-05).
  - Linux walk.

## Acceptance criteria

- [ ] The owner walks all seven beats on his real desk (Article IX.1,
      IX.4).
- [ ] Calendar events appear from his connected calendar source.
- [ ] An event-born recording is armed with the correct provenance.
- [ ] The Room shows a meeting Watch entity with counts.
- [ ] The week brief shows the week frame in the shade.
- [ ] The `next` seam shows the next event.
- [ ] His word.

## Test plan

- Unit: n/a (walk story).
- Integration: n/a.
- Manual: the seven-beat walk on his desk; screenshots at both widths;
  the stopwatch per face; his verdict recorded verbatim.

## Notes / open questions

- The walk depends on: (a) at least one calendar source connected via
  the 146 adapter, (b) at least one upcoming event with a meeting_url,
  (c) at least one meeting linked to a Room with intel run (from Phase
  172). If his desk lacks any of these at walk time, they must be set
  up during the walk.
