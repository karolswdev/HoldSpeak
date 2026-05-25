# HS-19-02 — Web Review Flow for Suggested `.hs/` Updates

- **Project:** holdspeak
- **Phase:** 19
- **Status:** done
- **Depends on:** HS-19-01
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Injected suggestions are useful for coding-agent handoff, but users also need a cockpit flow to review, edit, apply, or dismiss project documentation suggestions deliberately.

## Scope

### In

- Dictation web panel for latest project documentation suggestion.
- Explicit apply/edit/dismiss buttons.
- Writes only to validated `.hs/.../*.md` paths.
- Audit-friendly success/failure messages.

### Out

- Silent writes.
- Full document browser.
- Git commits.

## Acceptance Criteria

- [x] Web UI shows the latest suggestion path/rationale/content.
- [x] User can edit content before applying.
- [x] Apply writes only validated `.hs/.../*.md` paths.
- [x] Dismiss clears suggestion without touching disk.
- [x] API tests cover apply/dismiss/validation.

## Test Plan

- API tests for suggestion state and safe write endpoint.
- Web build marker test.
