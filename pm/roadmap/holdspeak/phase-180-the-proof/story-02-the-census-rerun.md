# HS-180-02 — The census re-run

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** Phase 179 merged
- **Unblocks:** HS-180-09
- **Owner:** unassigned

## Problem

Phase 170 established the UX-CANON.md violation census and the ratchet
(scripts/ux_canon_scan.py). The ratchet ceiling tracks per-rule and
per-face violation counts; a branch-new violation fails the check.
Phase 180 re-runs the census on the final tree and verifies the
ratchet is at or below its 170 baseline floor.

## Scope

- In:
  - Run `scripts/ux_canon_scan.py` on the final tree.
  - Compare the output against the 170 baseline: per-rule counts and
    per-face counts.
  - Zero branch-new violations (the ratchet may only tighten, never
    loosen).
  - Report the total violation count, the per-rule breakdown, and the
    per-face breakdown.
  - If violations decreased (the ratchet tightened), record the new
    floor.
- Out:
  - Fixing violations found (180 proves, it does not build; violations
    are filed as backlog items).
  - Scanning surfaces outside web/src (the scan covers web/src only).

## Acceptance criteria

- [ ] `scripts/ux_canon_scan.py` runs on the final tree with zero
      errors (Article IX.3 -- evidence rides with the change).
- [ ] Zero branch-new violations from the 170 baseline.
- [ ] The per-rule and per-face breakdowns are filed as evidence.
- [ ] If the ratchet tightened, the new floor is recorded.

## Test plan

- Unit: n/a (the scanner itself is tested in 170).
- Integration: n/a.
- Manual: run the scanner; compare with the 170 baseline; file the
  output.

## Notes / open questions

- The 170 baseline file location depends on where 170 stores it. If
  the baseline is committed (e.g., as a JSON artifact in the 170 phase
  folder), the comparison is mechanical.
