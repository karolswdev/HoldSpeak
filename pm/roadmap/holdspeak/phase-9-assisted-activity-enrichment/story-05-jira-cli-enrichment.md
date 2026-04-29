# HS-9-05 - Jira CLI enrichment annotations

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-01
- **Unblocks:** richer local annotations for Jira tickets
- **Owner:** unassigned

## Problem

Jira ticket URLs identify work items, but local browser metadata usually
does not include status, assignee, sprint, labels, or project metadata.
The local `jira` CLI can provide those details when already configured by
the user.

## Scope

- **In:**
  - `jira` availability detection.
  - Preview command plan.
  - Read-only issue view enrichment.
  - Timeout and output-size caps.
  - Local annotation persistence.
- **Out:**
  - Jira writes.
  - New auth/token storage.
  - Hidden network calls without explicit enablement.

## Acceptance Criteria

- [x] `jira` connector is disabled by default.
- [x] Availability and command path are visible.
- [x] Preview runs before writing annotations.
- [x] Only read-only commands are allowed.
