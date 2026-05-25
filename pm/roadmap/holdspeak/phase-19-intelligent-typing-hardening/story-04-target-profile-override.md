# HS-19-04 — Target Profile Override and Refinement

- **Project:** holdspeak
- **Phase:** 19
- **Status:** done
- **Depends on:** HS-18-01
- **Unblocks:** —
- **Owner:** unassigned

## Problem

OS/window detection can be wrong, especially in terminals and Wayland environments. Users need a visible manual override when HoldSpeak cannot infer the target correctly.

## Scope

### In

- Manual target-profile override in the Dictation cockpit.
- Override included in dry-run/live dictation activity context.
- Clear reset-to-auto affordance.

### Out

- Per-app automation rules.
- System accessibility permission automation.

## Acceptance Criteria

- [x] User can select Codex, Claude, terminal, browser, editor, chat, or auto.
- [x] Dry-run reflects the selected override.
- [x] Live dictation uses the override when set.
- [x] Tests cover API/config flow.

## Test Plan

- API/config tests.
- Target-profile unit tests.
- Web build marker test.
