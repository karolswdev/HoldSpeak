# HS-177-01 — The measured decision

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** Phase 172 merged
- **Unblocks:** HS-177-02, HS-177-03, HS-177-04, HS-177-05, HS-177-06, HS-177-07
- **Owner:** unassigned

## Problem

The arc says: "The Thread as a work tool (10 test threads, none for
work) and the Workbench (1, never run) -- 170--172 give them an
engine; then a week of use decides whether they stay." Build work is
conditional on adoption. This story measures whether the Thread and
the Workbench have earned their place after Phases 170--172 ship.

This is a decision story: it observes, measures, and records the
owner's verdict. If the verdict is CUT, stories 02--07 are cancelled
and the phase closes with adoption support only. If the verdict is
GO, the build stories proceed.

## Scope

- In:
  - A one-week measured period after Phases 170--172 merge, during
    which the owner uses HoldSpeak on his real desk with the Thread
    and Workbench available.
  - The metric (queried from the owner's real DB, read-only):
    - Work threads created (threads table, excluding test threads --
      threads with > 3 turns and a grounding ref, or a mode other
      than Desk).
    - Workbench runs completed (workbench_runs table, status =
      completed).
    - Room-grounded questions asked (threads with grounding refs
      pointing to project/Watch entities, if any exist by then).
  - The kill criterion: if the owner creates 0 qualifying work
    threads AND 0 workbench runs in the measured week, the phase is
    cut to adoption support only. The owner may override the
    criterion in either direction (his word outranks the metric --
    Article IX.4).
  - The owner's verdict: GO (proceed to stories 02--07) or CUT
    (stories 02--07 cancelled; the phase closes with the measured
    decision as its only evidence).
- Out:
  - Implementation work (that is stories 02--07, conditional on GO).
  - Modifying the Thread or Workbench during the measured week (the
    measurement is of what exists, not of a prototype).
  - Coaching the owner to use the Thread (the measured week is
    observation, not promotion).

## Acceptance criteria

- [ ] The one-week measured period completed after Phases 170--172
      merged.
- [ ] The metric is queried from the owner's real DB with the exact
      counts documented (Article VI: honest at zero).
- [ ] The kill criterion is evaluated honestly: zero qualifying work
      threads AND zero workbench runs = CUT; any nonzero = GO
      candidate; the owner's word is final.
- [ ] The owner's verdict is recorded (GO or CUT) with his words
      verbatim (Article IX.4).
- [ ] If CUT: stories 02--07 are marked cancelled in
      current-phase-status.md; the phase proceeds directly to the
      close (story 08).

## Test plan

- Unit: n/a (decision story).
- Integration: n/a.
- Manual: the metric is queried from the real DB; the owner's verdict
  is recorded verbatim.

## Notes / open questions

- The measured week starts only after 170--172 are merged and the
  owner has had at least one sitting with the new Door, the Concierge,
  and the Heartbeat. If those phases are delayed, the measured week
  is delayed.
- The owner may run work threads before the measured week (during
  170--172 development); those count toward the metric if they fall
  within the designated measurement window.
- "Adoption support only" means: bug fixes, small UX improvements to
  the existing Thread/Workbench, but no new Room grounding, no
  palette widening, no new grounding ref types.
