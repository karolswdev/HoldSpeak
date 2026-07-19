# HS-100-08 — B4: Meetings

- **Project:** holdspeak
- **Phase:** 100
- **Status:** done
- **Depends on:** HS-100-07
- **Unblocks:** HS-100-09

## Problem

Meeting→filed-actions costs nine concepts and two Settings detours
(trace A). Thesis §1.2: outcomes first.

## Scope

- In: HistoryCore rebuilt — the opening face is "what your meetings
  produced": needs-you actions (approve verb + egress badge inline),
  decided, still-open; the meeting list as a rail; transcript as a
  receipt disclosure; routing/queues behind the door. LiveCore becomes
  the Record wing; Artifacts the third wing.
- Out: intel pipeline changes.

## Acceptance criteria

- [ ] Approving a proposed action is ONE verb on the opening face,
      badge visible at the point of decision.
- [ ] Flow budget pinned: meeting detail ≤ 4 concepts on the opening
      face; arrival → approve ≤ 5 clicks with intel live.
- [ ] Live screenshots at 1440 and 393.

## Test plan

- vitest; the flow-budget walk against a staged hub with the imported
  trace meeting; integration pins.

## Evidence required

- Suite output; the walk trace; the screenshots.
