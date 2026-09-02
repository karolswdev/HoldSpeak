# HS-163-05 - The face: the Steward posture — run, watch, stop, receipts

- **Project:** holdspeak
- **Phase:** 163
- **Status:** backlog
- **Depends on:** HS-163-04 (scaffold may start against 04's frozen wire)
- **Unblocks:** HS-163-07
- **Owner:** unassigned

## Problem

The Room's steward section has said "not_yet_built" since 158. The
owner needs: press the hand, watch it work, stop it, read the
receipts — with zero prose and honest states.

## Scope

- **In:** the Steward posture in the project-room feature (the
  Updates-posture architecture: a verb in the Room chrome — MOUNTED
  path proven, the 161/162 law): Run once (busy/disabled per
  STW-002 with the honest reason when a run is active), the live
  run view (phase progression, step rows with effect kind + state +
  verification, polling the 04 wire), STOP (consequential styling;
  honest stopping→interrupted states), the run history list
  (designed rows — the 162 row scars: full labels, no fragments,
  chevron affordance, no raw ids EVER — pstrun_/pststep_ ids stay
  in title/aria), receipts that open their subjects (items/updates/
  observations via the house citation opener), the policy editor
  (bounds + eligible effects; no modals; mic on text inputs).
  Egress badge wherever a model-touching effect is configured.
  Fixtures mined from 04's integration tests. Then beauty + shots →
  THE OWNER'S VERDICT closes this story.
- **Out:** scheduling UI (P5).

## Acceptance criteria

- [ ] Mounted-path proof by real clicks; the run walk through the mounted tree (run → phases advance → steps land → receipts open).
- [ ] Stop honest on glass; STW-002's refusal rendered as a reason, not an error toast; no raw ids (regex law); designed rows at both viewports.
- [ ] check green; baseline zero unexplained; SHOTS + THE OWNER'S VERDICT recorded verbatim.

## Test plan

- **Web unit:** mounted walk, run states, stop, receipts, policy. **Glass:** rides 06. **Manual:** the owner's verdict.
