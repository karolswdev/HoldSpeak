# HS-173-05 — The release-readiness scorecard

- **Project:** holdspeak
- **Phase:** 173
- **Status:** in-progress
- **Depends on:** HS-173-03
- **Unblocks:** HS-173-06
- **Owner:** unassigned

## Problem

No release-readiness concept exists in the Room today. The arc says: "a
release-readiness scorecard as a Room token row." The signals for
readiness are scattered: review latency (HS-173-03), CI health
(HS-173-03), open blockers (from Watch entities), overdue commitments
(from the People ledger). Composing them into one at-a-glance row
gives the owner the answer to "can I ship this week?" without opening
four views.

## Scope

- In:
  - A RELEASE READINESS row in the Room showing per-signal indicators
    (green / amber / red):
    - Review latency: green (all < 24 h), amber (any 24-48 h), red
      (any > 48 h).
    - CI health: green (last 3 runs pass), amber (1 failure in last
      3), red (2+ failures in last 3).
    - Open blockers: green (0), amber (1), red (2+).
    - Overdue commitments: green (0), amber (1), red (2+).
  - The thresholds are configurable per project via the steward
    policy.
  - The scorecard is a read-only derivation from existing data
    (Article V.5).
  - The face follows the HS-173-01 artboard.
- Out:
  - Automated release actions (no gate, no blocker enforcement).
  - Cross-project release readiness (Phase 178).
  - New data collection beyond existing Watch snapshots and
    commitments.

## Acceptance criteria

- [ ] The Room shows a RELEASE READINESS row with per-signal
      indicators; verified at both widths (1440 + 393).
- [ ] Each signal's indicator reflects the correct status from the
      underlying data; verified by a unit test with seeded data per
      signal.
- [ ] Thresholds are configurable per project via the steward policy.
- [ ] The scorecard is absent when no signals have data (UX-CANON.md
      rule A.8: no counters of zero).
- [ ] The scorecard is a read-only derivation; no writes (Article
      V.5).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k release_readiness`
  - Green/amber/red per signal with seeded data.
  - Configurable thresholds.
  - Absent when no data.
- Integration: n/a (read-only derivation).
- Manual: the owner's Room shows the scorecard for his project.

## Notes / open questions

- The signal set (review latency, CI health, open blockers, overdue
  commitments) is proposed; the owner may add or remove signals at
  design time.
- The row may be a compact token strip (green/amber/red dots per
  signal) or a ledger row with labels; the artboard decides.
