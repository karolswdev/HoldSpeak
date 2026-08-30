# HS-151-05 — The record book

- **Project:** holdspeak
- **Phase:** 151
- **Status:** done
- **Depends on:** HS-151-01, HS-151-02, HS-151-03, HS-151-04
- **Unblocks:** HS-151-06
- **Owner:** unassigned

## Problem

The dedicated docs story: the metal truth must read cold.

## Scope

### In

- MODELS/backend docs: the request-level structured-output
  behavior + the named-owner intel shape (labels/shapes verbatim
  from shipped code); the schema-pinned-server gotcha recorded
  where operators will find it.
- USER_GUIDE: what intel now does with named owners (the
  triage → map → brief loop closes from a REAL meeting); honest
  latency expectations from story 03's numbers.
- The .43 operator recipe where internal runbooks live
  (metal-probes.md content graduated): the 8081 relaunch line, the
  8080 pin fact, never-download-to-the-box.
- Doc-drift guards updated; entry points only where earned.

### Out

- README pitch unless honestly earned.

## Acceptance criteria

1. Cold reader can wire a fresh HOME to their own endpoint and
   understand what intel emits.
2. Doc guards green UNFILTERED (the 150 lesson).

## Test plan

Doc suites; read-through against the story-03/04 evidence.
