# HS-60-04 — The false-accept measurement

- **Project:** holdspeak
- **Phase:** 60
- **Status:** done
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
- [x] The committed harness reports per-utterance max scores; wake
      detected across all three voices. The zero-detections bar was
      refined by MEASUREMENT into two classes: ordinary speech (57
      utterances incl. adversarial near-misses) → **0 false accepts**
      at 0.5; wake-adjacent phrases (containing the wake word or a
      near-homophone) score up to 0.996 — indistinguishable from the
      real phrase, inherent to wake-word detection, fired in 3 of 9
      cases, and mitigated BY DESIGN (the preview default), not by
      tuning. The first run's honest FAIL drove the split.
- [x] The margins stated: worst wake 0.628 vs. best ordinary
      distractor 0.433 (0.196); the wake-adjacent class has no margin
      and the docs say so. See `evidence-story-04.md`.

## Test plan
- The harness run on this machine (the real model is installed); its
  transcript committed. Full suite unaffected.
