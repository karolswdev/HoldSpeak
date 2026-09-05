# HS-173-03 — The health signals

- **Project:** holdspeak
- **Phase:** 173
- **Status:** in-progress
- **Depends on:** HS-173-01
- **Unblocks:** HS-173-04, HS-173-05
- **Owner:** unassigned

## Problem

Watch snapshots carry `reviewRequests`, `reviewDecision`, `updatedAt` on
PR entities (project_service.py:597-601) and `assignee`,
`time_in_status` candidates on Jira entities (watch_sources.py:368),
but no derivation computes reviewer latency (per-person median hours
from request to decision) or issue aging (time-in-status). The
`branch_ci` entity kind (project_service.py:61) exists in snapshots but
no flaky-CI detection or merge-queue depth computation exists. The arc
says: "reviewer-latency and issue-aging derivations at evaluation time
surfacing as NEEDS YOU rows and Room tokens."

## Scope

- In:
  - Reviewer-latency derivation: at evaluation time (or at read time
    from cached snapshots), compute per-person median hours from
    `reviewRequests` timestamp to `reviewDecision` timestamp across
    PR entities in Watch snapshots.
  - Issue-aging derivation: compute time-in-status from Jira entity
    `created` / `updated` timestamps and current status.
  - Flaky-CI detection: from `branch_ci` entity history (limit 10),
    count consecutive failures or failure/success alternation.
  - Merge-queue depth: count open PRs with passing CI that are not
    yet merged (derivable from PR entities + `branch_ci`).
  - These signals surface as NEEDS YOU rows when they exceed
    configurable thresholds (default: 48 h reviewer latency, 5 d
    issue aging, 3+ consecutive CI failures).
  - These signals surface as Room tokens (compact indicators in the
    Room's health area).
  - Reads only; no external writes (Article V.5).
- Out:
  - External notifications about these signals (the nudge is a
    separate story, HS-173-04).
  - New Watch evaluation logic (these derivations read from existing
    snapshots).
  - Cross-project aggregation (Phase 178).

## Acceptance criteria

- [ ] Reviewer-latency derivation computes per-person median hours;
      verified by a unit test with a seeded PR entity snapshot
      carrying `reviewRequests` and `reviewDecision` timestamps.
- [ ] Issue-aging derivation computes time-in-status; verified by a
      unit test with a seeded Jira entity snapshot.
- [ ] Flaky-CI detection identifies 3+ consecutive failures in
      `branch_ci` history; verified by a unit test.
- [ ] Merge-queue depth counts open PRs with passing CI; verified by
      a unit test.
- [ ] Signals exceeding thresholds appear as NEEDS YOU rows in the
      Room; verified at both widths.
- [ ] Signals appear as Room tokens (compact health indicators).
- [ ] No external writes (reads only; Article V.5).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k health_signals`
  - Reviewer latency with seeded snapshots.
  - Issue aging with seeded Jira snapshots.
  - Flaky CI detection with seeded branch_ci history.
  - Merge-queue depth computation.
  - Threshold-based NEEDS YOU row generation.
- Integration: n/a (derivations from cached snapshots).
- Manual: the owner's Room shows health tokens for his projects.

## Notes / open questions

- The `reviewRequests` field (watch_sources.py:108) carries reviewer
  logins. The `updatedAt` (project_service.py:601) on the PR entity is
  the last update time. The review request timestamp itself may not be
  directly available; the derivation may need to approximate from
  `createdAt` of the review request or the PR.
- The `branch_ci` entities carry `status` and `conclusion` fields
  (project_service.py:634-636). History requires reading multiple
  evaluation snapshots or the steward run history.

**Counsel C6 (design, 2026-09-05):** the test plan includes a glass rig
through `GET /api/projects/{id}/room` — seeded snapshots (PRs with
review requests + createdAt, Jira issues past the threshold, branch_ci
history) → the health payload → the four HEALTH rows on the face at
1440 + 393 (`tests/e2e/test_hs173_health_glass.py`). The 172 law: a
new entry point needs a production call site and one test through the
real seam.
