# HS-159-06 - The walk: reload, resume, finalize, and the Room is not empty

- **Project:** holdspeak
- **Phase:** 159
- **Status:** backlog
- **Depends on:** HS-159-04
- **Unblocks:** HS-159-07
- **Owner:** unassigned

## Problem

§14 P1a's exit is a sentence: "setup resumes after reload and opens a
non-empty Project Room without external provider dependency." That
sentence must run on glass, end to end, deterministically — the
156-07/158 rig discipline.

## Scope

- **In:** `tests/e2e/test_hs159_interview_glass.py` on a rig-booted
  hub (own port, isolated HOME/DB; bundle rebuilt first — the law):
  (1) THE WALK: start the interview → answer the two questions →
  native suggestions appear from seeded desk facts (a meeting, a
  decision, an overdue Door item) → select + clarify one → test it
  (real bounded read; `Test passed · N current matches`) → RELOAD
  THE DESK mid-setup → Continue setup restores the stage → activation
  review → finalize → the Room opens scoped and NON-EMPTY (the
  watch binding + native material visible) → zero false historical
  events (assert via the API). (2) The Blank leg: blank path →
  active Project, no Watch, honest empty Room. (3) The abandon leg:
  abandon mid-way → no Project exists. Shots of the key stops into
  assets/story-06-shots/ (they feed 05's sheet too). Overflow
  assertions at 1440+393.
- **Out:** provider legs, scheduling, model paths.

## Acceptance criteria

- [ ] The walk passes deterministically (fixed seeds, testid waits, no sleep-only): resume-exact-stage proven, finalize atomic, Room populated, ledger free of false baselines.
- [ ] Blank and abandon legs pass (INT-002/006 on glass).
- [ ] Every leg asserts zero horizontal overflow; shots saved and non-trivial.

## Test plan

- **E2E:** the three legs above; run via the playwright-env scratch script.

## Notes / open questions

- Seed through the REAL API wherever reachable; DB-layer seeding only where no route exists yet — and note each such gap for the next phase (the 158 precedent that found the PATCH hole).
