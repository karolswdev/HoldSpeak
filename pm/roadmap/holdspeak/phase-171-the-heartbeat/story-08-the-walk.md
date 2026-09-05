# HS-171-08 — The walk

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** HS-171-04, HS-171-05, HS-171-06, HS-171-07
- **Unblocks:** HS-171-09
- **Owner:** unassigned

## Problem

The owner's attended walk on his desk is the exit gate (Article IX.4).
The Heartbeat introduces new behavior (notifications, the shade
PROJECTS section, the recurring brief, the command-deck entries) that
must be proven on his real desk with his real projects. The walk is the
proof that the desk reaches him.

## Scope

- In:
  - The owner's attended walk on his desk, both widths (1440 + 393).
  - The walk covers:
    1. A macOS notification fires (a project has needs-you items).
    2. Clicking the notification opens the desk.
    3. The shade shows PROJECTS with the correct count and WHY.
    4. The dock badge carries the aggregate count.
    5. The Monday brief has regenerated without him opening the desk.
    6. The command deck lists his projects; selecting one opens the Room.
    7. Quiet hours: no notification fires during the configured window.
  - The stopwatch per face (Article IX.2).
  - His verdict (Article IX.4).
- Out:
  - Automated rig legs (those are in stories 02-07).
  - Linux walk (verified by unit tests; the .43 leg is optional).

## Acceptance criteria

- [ ] The owner walks all seven beats on his real desk (Article IX.1,
      IX.4).
- [ ] The notification arrives within 10 s of the edge (measured with
      the stopwatch).
- [ ] The shade PROJECTS section matches the artboard at both widths
      (Article IX.2).
- [ ] The dock badge matches the aggregate count.
- [ ] The Monday brief shows in the shade without him having opened the
      desk first.
- [ ] The command deck lists his projects; selecting one opens the Room.
- [ ] His word.

## Test plan

- Unit: n/a (walk story).
- Integration: n/a.
- Manual: the seven-beat walk on his desk; screenshots at both widths;
  the stopwatch per face; his verdict recorded verbatim.

## Notes / open questions

- The walk depends on his desk having at least one project with
  needs-you items. If his desk has zero projects at walk time, one must
  be created during the walk.
