# HS-8-05 - Project activity linking and surface

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-03, HS-8-04
- **Unblocks:** usable recent work context
- **Owner:** unassigned

## Problem

Imported activity needs to be visible and useful inside HoldSpeak. Users
should be able to see recent work objects for a project and use that
context in dictation, meeting review, or handoff exports.

## Scope

- **In:**
  - Project-linking rules by domain, Jira key prefix, repo/org, or manual
    mapping.
  - Recent activity API for project/global scopes.
  - Browser surface for recent activity records.
  - Copyable local activity context bundle.
- **Out:**
  - External sync.
  - Automatic Project KB mutation without user action.

## Acceptance Criteria

- [ ] Recent activity is visible from a browser surface.
- [ ] Activity can be filtered or scoped by project.
- [ ] User can copy/export a local activity context bundle.
- [ ] No external network calls are required.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-8-04.
