# HS-60-04 — The false-accept measurement

- **Project:** holdspeak
- **Phase:** 60
- **Status:** backlog
- **Depends on:** HS-60-01
- **Unblocks:** HS-60-05, HS-60-06
- **Owner:** unassigned

## Problem
"Low false-accept" is a claim; the phase's safety posture requires a
number, measured by a committed, repeatable harness.

## Scope
- **In:** a dogfood harness that synthesizes a distractor corpus (≥20
  sentences × ≥2 `say` voices, adversarial near-misses included:
  "hey there…", "jarvis…", phonetic neighbors) and the wake phrase
  across the same voices, runs the REAL openwakeword model frame-by-
  frame, and reports max scores + detections at the default threshold.
  Zero distractor detections is the bar; the wake phrase must detect
  for every voice. The numbers land in evidence and the docs cite them
  with the honest caveat (synthetic speech; real rooms differ).
- **Out:** long-duration ambient testing (noted as future work).

## Acceptance criteria
- [ ] The committed harness reports per-utterance max scores; zero
      distractor detections at 0.5; wake detected across voices.
- [ ] The margin (best distractor vs. worst wake) is stated in evidence.

## Test plan
- The harness run on this machine (the real model is installed); its
  transcript committed. Full suite unaffected.
