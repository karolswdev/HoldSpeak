# HS-7-02 - Saved meeting export API

- **Project:** holdspeak
- **Phase:** 7
- **Status:** backlog
- **Depends on:** HS-7-01
- **Unblocks:** browser handoff export actions
- **Owner:** unassigned

## Problem

The browser can inspect saved meetings and artifacts, but there is no
saved-meeting export API that returns the shared handoff renderer output.

## Scope

- **In:**
  - Saved meeting export endpoint for Markdown and JSON.
  - Include synthesized artifacts where available.
  - Tests for status codes, content type, and payload content.
- **Out:**
  - Writing files to arbitrary user paths from the browser.
  - External publishing.

## Acceptance Criteria

- [ ] A saved meeting can be exported through a local API.
- [ ] Markdown and JSON outputs use the shared handoff renderer.
- [ ] Invalid formats fail clearly.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-7-01.
