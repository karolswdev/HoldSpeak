# HS-8-06 - Privacy controls and retention

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-03, HS-8-05
- **Unblocks:** trustworthy local activity intelligence
- **Owner:** unassigned

## Problem

Browser history ingestion is sensitive. Users need explicit control over
whether it runs, which domains are included/excluded, how long records
are retained, and how to delete imported data.

## Scope

- **In:**
  - Opt-in setting and visible enabled/paused state.
  - Domain allowlist/denylist.
  - Retention controls.
  - Delete imported activity controls.
  - Tests for privacy settings and deletion.
- **Out:**
  - Hidden background collection.
  - Remote telemetry.

## Acceptance Criteria

- [ ] Activity ingestion is opt-in.
- [ ] User can pause ingestion.
- [ ] User can exclude domains.
- [ ] User can delete imported activity.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-8-05.
