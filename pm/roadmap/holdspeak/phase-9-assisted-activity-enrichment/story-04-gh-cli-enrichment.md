# HS-9-04 - GitHub CLI enrichment annotations

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-01
- **Unblocks:** richer local annotations for GitHub PRs and issues
- **Owner:** unassigned

## Problem

GitHub URLs identify PRs and issues, but browser metadata often lacks
state, labels, reviewers, branch, and merge status. The local `gh` CLI
can provide that metadata when already authenticated by the user.

## Scope

- **In:**
  - `gh` availability detection.
  - Preview command plan.
  - Read-only `gh pr view` and `gh issue view` enrichment.
  - Timeout and output-size caps.
  - Local annotation persistence.
- **Out:**
  - `gh` writes.
  - New auth/token storage.
  - Hidden network calls without explicit enablement.

## Acceptance Criteria

- [x] `gh` connector is disabled by default.
- [x] Availability and command path are visible.
- [x] Preview runs before writing annotations.
- [x] Only read-only commands are allowed.
