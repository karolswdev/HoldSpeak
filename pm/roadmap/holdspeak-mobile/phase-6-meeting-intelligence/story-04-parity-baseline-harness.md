# HSM-6-04 — The parity baseline harness

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** done (harness + rubric framework; the live verdict run is HSM-6-05)
- **Depends on:** HSM-6-02, HSM-6-03
- **Unblocks:** HSM-6-05
- **Owner:** unassigned

## Problem

The Track G gate is "parity with desktop quality baseline" — meaningless until
parity is operationally defined. Intel is non-deterministic, so a string diff
won't work. The phase needs a harness that captures a desktop baseline and judges
mobile output against it on substance, repeatably.

## Scope

- **In:** a fixed set of baseline meetings (transcripts) processed on the desktop
  product to capture the baseline artifacts; a substance rubric (per-artifact-type
  coverage of what's actually in the transcript); a harness that runs mobile
  generation over the same inputs and scores it against the rubric/baseline,
  tolerant of phrasing variance and stable across reruns.
- **Out:** the gate verdict itself (HSM-6-05 runs the harness and records the
  result). The artifact generators (HSM-6-01..03). MIR (Phase 7).

## Acceptance criteria

- [x] A documented baseline-meeting set: the **Phase-67 dogfood transcripts**
      (owner-agreed). NOTE: *capturing* the desktop artifacts on that set + the
      live mobile run is the HSM-6-05 verdict (it needs the desktop intel pipeline
      and, on the mobile side, the device/dep-gated inference engine — Phase 5).
- [x] A substance rubric defines what "covered" means per artifact type and the
      pass threshold — `ParityRubric` (per-`ParityCategory` `mustCover` facts) +
      threshold **0.8 overall coverage, reported per-type** (owner-agreed default).
- [x] The harness scores output against the rubric and is **stable across reruns**:
      `ParityScorer.score` is a pure function — `testScorerIsDeterministic` (run
      twice → identical `ParityReport`). The non-determinism is in generation, not
      in judging.
- [x] The harness **reports per-category** (`ParityReport.perCategory`) with the
      `missing` facts, so a gap is attributable to a specific type, not one opaque
      score (`testThresholdFailsAndAttributes`).

## Test plan

- Unit: the rubric/scorer over fixed mobile + baseline artifact fixtures → a
  deterministic score; rerun → identical verdict.
- Manual: capture the desktop baseline on the chosen meeting set; sanity-check the
  rubric against human judgment on one meeting.

## Notes / open questions

- Define parity (rubric + threshold + baseline set) before HSM-6-05 judges, so the
  gate isn't a vibe (phase risk). Get owner sign-off on the rubric.
- The baseline meetings can reuse the desktop dogfood fixtures (Phase 67's say-
  rendered meetings) so both runtimes are judged on the same believable data.
