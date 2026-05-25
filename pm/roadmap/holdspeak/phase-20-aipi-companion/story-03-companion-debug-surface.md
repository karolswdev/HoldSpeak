# HS-20-03 — Companion Debug Surface

- **Project:** holdspeak
- **Phase:** 20
- **Status:** done
- **Depends on:** HS-20-01, HS-20-02
- **Unblocks:** HS-20-04
- **Owner:** unassigned

## Problem

AIPI companion setup crosses several local systems: device connection,
Claude/Codex hook capture, dictation pipeline configuration, and text
insertion runtime state. When the loop fails, users need one status surface
that identifies the missing piece instead of manually checking multiple pages
and logs.

## Scope

### In

- Browser-readable companion status endpoint.
- Device count and supported agent query names.
- Latest fresh awaiting-agent session summary.
- Dictation pipeline readiness summary.
- Runtime text-insertion status.
- Machine-readable blockers for incomplete setup.
- Focused integration coverage and install-guide documentation.

### Out

- New AIPI wire frames.
- Firmware UI changes.
- Autonomous agent replies.
- A dedicated browser companion panel.

## Acceptance Criteria

- [x] HoldSpeak exposes one companion status endpoint.
- [x] The endpoint reports whether the AIPI agent-reply loop is ready.
- [x] The endpoint reports device, agent, dictation, and runtime components.
- [x] The endpoint returns explicit blockers when setup is incomplete.
- [x] Tests cover ready and blocked companion states.

## Test Plan

- Integration tests for `/api/companion/status`.
- Focused web-server integration test run.
- `git diff --check`.

## Notes

- This story intentionally stays server-side. HS-20-04 can decide whether to
  add a dedicated browser panel or hand the endpoint to the companion UI.
