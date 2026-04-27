# HS-8-06 - Privacy controls and retention

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-03, HS-8-05
- **Unblocks:** trustworthy local activity intelligence
- **Owner:** unassigned

## Problem

Browser history ingestion is sensitive even for a personal local tool.
The feature should ship enabled by default, but users still need explicit
visibility and control over whether it is running, which domains are
included/excluded, how long records are retained, and how to delete
imported data.

## Scope

- **In:**
  - Default-enabled setting with visible enabled/paused state.
  - First-run/browser-surface copy that names the active local sources.
  - Domain allowlist/denylist.
  - Retention controls.
  - Delete imported activity controls.
  - Tests for privacy settings and deletion.
- **Out:**
  - Hidden background collection.
  - Remote telemetry.

## Acceptance Criteria

- [ ] Activity ingestion is enabled by default when local sources are readable.
- [ ] UI/API visibly reports that ingestion is enabled.
- [ ] User can pause ingestion.
- [ ] User can exclude domains.
- [ ] User can delete imported activity.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-8-05.
