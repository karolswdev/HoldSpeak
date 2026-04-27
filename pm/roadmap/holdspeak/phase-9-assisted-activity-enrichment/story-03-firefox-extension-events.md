# HS-9-03 - Firefox companion extension events

- **Project:** holdspeak
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HS-9-01
- **Unblocks:** opt-in active-tab metadata capture
- **Owner:** unassigned

## Problem

Browser history is useful but delayed and sometimes sparse. A local
Firefox companion extension can provide visible, opt-in active-tab
events through loopback without reading page bodies or credentials.

## Scope

- **In:**
  - Loopback event API.
  - Event normalization into `activity_records`.
  - Entity extraction and project mapping reuse.
  - Local installation/development guide.
- **Out:**
  - Extension store distribution.
  - Safari extension.
  - Cookies, credentials, form values, page bodies, screenshots, or
    private browsing data.

## Acceptance Criteria

- [ ] Extension events can be posted to localhost.
- [ ] Events create or merge activity records.
- [ ] Project mapping applies to extension records.
- [ ] Tests prove private/page-body data is not accepted.
