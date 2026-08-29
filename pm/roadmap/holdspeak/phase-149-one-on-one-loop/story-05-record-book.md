# HS-149-05 — The record book

- **Project:** holdspeak
- **Phase:** 149
- **Status:** done
- **Depends on:** HS-149-01, HS-149-02, HS-149-03, HS-149-04
- **Unblocks:** HS-149-06
- **Owner:** unassigned

## Problem

The dedicated docs story: the 1:1 Loop must read cold, and
docs/PEOPLE_INTEGRATION.md must record its contract as FULFILLED
by this exact shape.

## Scope

### In

- docs/PEOPLE_INTEGRATION.md: the deliberate-association section
  updated — the calendar-series link IS the first sanctioned
  association; the gesture, the evidence, the read-time-only rule,
  what remains deferred (participants, inference: still
  forbidden).
- USER_GUIDE: the manager's loop in user words — link your 1:1,
  the person chip, PREP, Record this, where it all lands; the dev
  keystore documented as walk/test-only with the doctor warning.
- SECURITY.md: the People rows updated ONLY if claims changed
  (the link lives encrypted; resolution read-time; verify and
  touch minimally).
- Doc-drift guards updated where claims change.

### Out

- Marketing/README (judge honestly — likely no).

## Acceptance criteria

1. A cold reader can run the whole loop from the docs alone.
2. PEOPLE_INTEGRATION.md's contract section names this phase's
   shape and the still-forbidden inferences.
3. Doc guards green.

## Test plan

Doc-drift suites; read-through against story 03/04 shots.
