# HS-168-05 - The Tuesday walk, face-driven: the owner's real desk under the stopwatch

- **Project:** holdspeak
- **Phase:** 168
- **Status:** backlog
- **Depends on:** HS-168-03, HS-168-04
- **Unblocks:** HS-168-07
- **Owner:** unassigned

## Problem

The 167 walk drove setup through the wire and shot the desk; the
owner walked the face himself and got confused. This walk drives the
FACE, shoots the WINDOW at every step, and reads the stopwatch
against the 01 baseline.

## Scope

- **In:** assets/walk-script.md (the steps, what is asserted, both
  widths) and the runner tests/e2e/live168_walk.py (HS168_WALK=1;
  HS168_WALK_DB=isolated|real; real HOME; skip-guarded on gh + acli;
  build-first): from a cold state (the isolated leg: nothing
  connected; the real leg: his gh + acli) — open Settings →
  Connections, read the state, Recheck; New Project → the interview
  → Sources → the connect card round trip (isolated leg) → the
  GitHub wizard scope-only on `karolswdev/HoldSpeak` → Test → the
  Jira wizard on KAN → Test → the known-scope offer on a second
  same-provider suggestion → Review → Activate → the Room lands.
  Every step: click the window, wait on the face, shoot the window
  at 1440 and 393; clicks and seconds recorded to a transcript and
  compared with assets/audit-today.md. The real leg archives the
  project in a finally with unattended OFF BEFORE archive (the 167
  law) and reverts any KAN touch. Then the owner's attended walk and
  his verdict, verbatim, in this story and the record. Every defect
  found live gets a failing-then-passing test under tests/unit/
  test_hs168_walk_fixes.py or the owner's word that it is ledgered.
- **Out:** steward / update steps (167 proved them).

## Acceptance criteria

- [ ] The runner drives the face and shoots the window; no step may be skipped; a step that cannot be asserted fails the walk (a hash-identical pair of step shots fails the walk).
- [ ] The stopwatch: clicks and seconds for cold → two tested Watches, recorded beside the 01 baseline; one terminal visit per tool at most.
- [ ] The owner's verdict recorded verbatim; his word on "no longer confuses me" is the exit.

## Test plan

- **Live:** `HS168_WALK=1 HS168_WALK_DB=isolated uv run pytest -q tests/e2e/live168_walk.py` (real HOME, from a real shell); then `HS168_WALK_DB=real` on his desk; the transcript + PNGs under assets/story-05-walk/.
