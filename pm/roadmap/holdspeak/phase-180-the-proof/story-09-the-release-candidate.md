# HS-180-09 — The release candidate

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** HS-180-02, HS-180-03, HS-180-04, HS-180-05, HS-180-06, HS-180-07, HS-180-08
- **Unblocks:** HS-180-10
- **Owner:** unassigned

## Problem

"HoldSpeak not really released" becomes released. The release
candidate is a git tag on main after all proof stories are complete.
The tag carries the version, the proof summary, and the Constitution
audit result.

## Scope

- In:
  - The release candidate PR: all proof evidence in the phase folder,
    the Constitution audit document, the census re-run output, the
    performance ledger, the positioning re-read, the arc
    retrospective, the measured week journal and verdicts, the Gate B
    feedback.
  - The git tag: the version number (decided at close time), the
    proof summary in the tag message.
  - The merge on the owner's word.
- Out:
  - Distribution (PyPI, Homebrew, etc.) -- out of scope for this arc.
  - Marketing or launch material.
  - Post-release support processes.

## Acceptance criteria

- [ ] All proof stories (HS-180-01 through HS-180-08) are complete
      with evidence filed.
- [ ] The release candidate PR is opened with all evidence.
- [ ] The git tag carries the version and the proof summary.
- [ ] The owner's word to merge and tag (Article IX.4).

## Test plan

- Unit: n/a.
- Integration: CI passes on the PR.
- Manual: the owner's word.

## Notes / open questions

- The version number is a deferred decision. If the proof passes
  cleanly, 1.0.0 is the candidate. If gaps are named but not blocking,
  0.x.0 with a roadmap to 1.0 is honest.
