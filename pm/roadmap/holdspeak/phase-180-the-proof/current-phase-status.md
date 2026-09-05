# Phase 180 - The Proof

**Last updated:** 2026-09-05.

## Goal

"HoldSpeak not really released" becomes released. Phase 180 is not a
build phase; it is the measured proof that 170-179 delivered. A week of
real use on his desk is the measured artifact. The Tuesday question is
answered per face with his verdict. The census re-runs at the ratchet's
floor. The Constitution is audited article by article with evidence.
The full suite and every live leg are green. Performance is ledgered.
The positioning is re-read against the shipped product. The arc is
retrospected. The last PR closes the road to 180.

## Status

**PLANNED 0/10.**

**Depends on:** Phase 179 merged (the last build phase; 180 proves the
whole arc).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

The answer is no longer a projection. It is a measured week.

Tuesday through Monday. He uses HoldSpeak for his real work: the desk,
the door, the Rooms, the notifications, the brief, the steward's
updates, the companion on his phone, the dictation, the meetings. At
the end of the week, per face: did he use it? Did it help? Did it
break? Did he turn it off? His verdicts, verbatim, are the exit
criteria. The census re-runs: every UX-CANON.md rule measured against
every surface, the ratchet at or below its floor (zero branch-new
violations from the 170 baseline). The Constitution is audited:
every article, every clause, with evidence that the shipped product
satisfies or honestly fails it. The full suite is green. Every live
leg (the .43 runner, the companion, the metal walk) is green. The
performance ledger shows response times, memory use, and startup time.
The positioning is re-read: does the shipped product match the claims?
The arc retrospective names what worked, what hurt, what carries
forward. The last PR opens; his word merges it; the release candidate
is tagged.

Census facts: the UAT framework exists (uat/ directory with campaigns,
scenarios, seeds, features.yaml, stage.py, conductor, and the
holdspeak-uat roadmap with 4 phases); the UX canon scan
(scripts/ux_canon_scan.py) runs mechanically and produces violations
per face per rule; every phase from 169 to 179 has a walk story whose
evidence records the owner's verbatim verdict.

## Scope

- In:
  - The owner's measured week: seven days of real use on his real desk
    with his real projects, his real team, his real meetings.
  - Per-face verdict: did he use it, did it help, did it break, did he
    turn it off; his words verbatim.
  - The census re-run: `scripts/ux_canon_scan.py` at the ratchet's
    floor; zero branch-new violations from the 170 baseline.
  - The Constitution audit: every article, every clause, with evidence
    (a test, a screenshot, a receipt, a walk result) that the shipped
    product satisfies or honestly names a gap.
  - The full suite + live legs: `HOME=$(mktemp -d) uv run pytest -q
    --ignore=tests/e2e/test_metal.py -n auto` green; the .43 runner
    live leg green; the companion live leg green; `cd apple && swift
    test` green.
  - The performance ledger: response times for key routes (the Room,
    the portfolio, the needs-you aggregate), memory use at steady
    state, startup time from cold.
  - The positioning re-read: POSITIONING.md claims compared against
    the shipped product; gaps named honestly.
  - The arc retrospective: what worked, what hurt, what carries
    forward; filed in the phase folder.
  - The last PR: the release candidate tag; the merge on his word.
- Out:
  - New features (180 proves, it does not build).
  - Bug fixes beyond what the measured week surfaces (those become
    backlog items or a follow-up phase).
  - App Store submission (out of scope for this arc).
  - Marketing or launch material.

## Exit criteria (evidence required)

- [ ] The owner's measured week is complete: seven days, per-face
      verdicts verbatim (Article IX.4).
- [ ] The census re-run shows zero branch-new violations from the 170
      baseline; the ratchet is at or below its floor.
- [ ] Every Constitution article is audited with evidence; gaps named
      (Article X.3 -- drift is named, never ignored).
- [ ] The full Python suite is green with zero branch-new failures.
- [ ] The Swift test suite is green.
- [ ] The .43 runner live leg is green (receipts on the desk).
- [ ] The companion live leg is green (discovery, portfolio, Room,
      notification on the real device).
- [ ] The performance ledger shows no regressions from the 170
      baseline.
- [ ] The positioning re-read names no unaddressed gaps.
- [ ] The arc retrospective is filed.
- [ ] The release candidate is tagged; the last PR merged on his word.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-180-01 | The measured week (the owner's seven days of real use; per-face verdicts) | backlog | [story-01-the-measured-week](./story-01-the-measured-week.md) | -- |
| HS-180-02 | The census re-run (ux_canon_scan.py; the ratchet at its floor; zero branch-new) | backlog | [story-02-the-census-rerun](./story-02-the-census-rerun.md) | -- |
| HS-180-03 | The Constitution audit (every article, every clause, with evidence) | backlog | [story-03-the-constitution-audit](./story-03-the-constitution-audit.md) | -- |
| HS-180-04 | The full suite and live legs (Python, Swift, .43 runner, companion) | backlog | [story-04-the-full-suite](./story-04-the-full-suite.md) | -- |
| HS-180-05 | The performance ledger (response times, memory, startup) | backlog | [story-05-the-performance-ledger](./story-05-the-performance-ledger.md) | -- |
| HS-180-06 | The positioning re-read (claims vs shipped product) | backlog | [story-06-the-positioning-reread](./story-06-the-positioning-reread.md) | -- |
| HS-180-07 | The arc retrospective (what worked, what hurt, what carries forward) | backlog | [story-07-the-arc-retrospective](./story-07-the-arc-retrospective.md) | -- |
| HS-180-08 | Gate B partner feedback (a second pair of eyes on the shipped product) | backlog | [story-08-gate-b-partner-feedback](./story-08-gate-b-partner-feedback.md) | -- |
| HS-180-09 | The release candidate (the tag, the last PR, the merge on his word) | backlog | [story-09-the-release-candidate](./story-09-the-release-candidate.md) | -- |
| HS-180-10 | The close (the doctor's honest bill of health; the final summary; the arc is complete) | backlog | [story-10-the-close](./story-10-the-close.md) | -- |

## Where we are

PLANNED. Waiting for Phase 179 (the last build phase). The recon is
complete:

**Walk stories from 169-179:** every build phase has a walk story
whose acceptance criterion is the owner's verbatim verdict (169
story-05, 170 story-05, 171 story-08, 172 story-08, 173 story-06).
Phase 180's measured week is the comprehensive version: not one walk
per phase but a continuous week across all faces.

**The UAT framework (uat/ directory):** exists with campaigns,
scenarios, seeds, features.yaml, stage.py, conductor, and the
holdspeak-uat roadmap (4 phases: mechanics, inventory, harness/engine,
owner functional pass). The UAT framework provides the harness for
the measured week's data collection.

**The census method (scripts/ux_canon_scan.py):** the mechanical
scanner from Phase 170 scans web/src for UX-CANON.md violations per
face per rule. The ratchet ceiling tracks per-rule and per-face
counts; a branch-new violation fails the check. Phase 180 re-runs the
scan and verifies the ratchet is at or below its 170 baseline floor.

**The Constitution:** 11 articles (I-XI) with clauses. The audit is
per-clause, not per-article. Each clause needs evidence: a test that
locks the claim, a screenshot that shows the face, a receipt that
proves the kernel admitted the operation, or a walk result that proves
the user experience.

**The doctor:** `holdspeak doctor` reports what is actually broken
(Article VI). The doctor's honest bill of health is the close story's
first step.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| The measured week reveals a face he does not use | High | That is the point: an unused face is an honest gap, documented and backlogged, not papered over; the Tuesday question is answered per face | All faces unused (the product failed its thesis) |
| Constitution audit reveals a clause gap | Medium | A gap is named and filed, not fixed in this phase (180 proves, it does not build); the release candidate ships with named gaps, not hidden ones (Article X.3) | A gap in Article III or Article V (privacy or consent) blocks the release candidate |
| Performance regression since 170 | Low | The performance ledger is comparative (180 vs 170 baseline); a regression is named and filed; the release candidate ships with the ledger, not a promise | Startup time > 10 s or Room response > 2 s from cache |
| Partner feedback blocks | Low | Gate B is a second opinion, not a veto; the owner's word is the exit (Article IX.4); partner findings are filed as backlog | The partner finds a privacy or consent violation |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- The release candidate version number (semantic versioning; the first
  non-0.x version if the proof passes) -- decided at close time.
- Whether Gate B partner feedback blocks the release candidate or is
  advisory -- decided at charter time (proposed: advisory, with
  privacy/consent findings blocking).
- The measured week's data collection method (manual journal vs UAT
  framework automated) -- decided at charter time from UAT framework
  readiness.
