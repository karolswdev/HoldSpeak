# HS-172-08 — The walk

- **Project:** holdspeak
- **Phase:** 172
- **Status:** done
- **Depends on:** HS-172-07
- **Unblocks:** HS-172-09
- **Owner:** unassigned

## Problem

The owner's attended walk on his desk is the exit gate (Article IX.4).
The Loop Closes introduces new behavior (auto-intel, proposals in NEEDS
YOU, the People card with Watch data, suggested sources) that must be
proven on his real desk with a real meeting. The walk is the proof that
meetings close their loop.

## Scope

- In:
  - The owner's attended walk on his desk, both widths (1440 + 393).
  - The walk covers:
    1. A meeting linked to a Room; capture stops; intelligence runs
       automatically.
    2. Extracted decisions and action items appear in NEEDS YOU as
       PROPOSALS.
    3. He confirms one decision; the decision_record and commitment
       exist.
    4. He drops one proposal; no record created.
    5. Before the 1:1: the People card shows PRs waiting, commitments,
       last meeting summary.
    6. A mentioned repo appears as a SUGGESTED source; he accepts or
       dismisses.
    7. People are reachable from the Room at 393.
  - The stopwatch per face (Article IX.2).
  - His verdict (Article IX.4).
- Out:
  - Automated rig legs (those are in stories 02-07).
  - Linux walk.

## Acceptance criteria

- [x] The owner walks all seven beats on his real desk (Article IX.1,
      IX.4).
- [x] Intelligence runs automatically after the meeting stops
      (measured with the stopwatch).
- [x] PROPOSALS appear in NEEDS YOU; Confirm and Drop work.
- [x] The People card shows Watch-derived data for a team member.
- [x] A suggested source appears and can be accepted or dismissed.
- [x] People are reachable from the Room at 393.
- [x] His word.

## Test plan

- Unit: n/a (walk story).
- Integration: n/a.
- Manual: the seven-beat walk on his desk; screenshots at both widths;
  the stopwatch per face; his verdict recorded verbatim.

## Notes / open questions

- The walk depends on: (a) at least one meeting linked to a Room, (b)
  at least one People relationship with a linked alias matching a Watch
  entity. If his desk has neither at walk time, they must be created
  during the walk.
