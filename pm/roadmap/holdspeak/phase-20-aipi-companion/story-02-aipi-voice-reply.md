# HS-20-02 — AIPI Voice Reply To Waiting Agent

- **Project:** holdspeak
- **Phase:** 20
- **Status:** done
- **Depends on:** HS-20-01, HS-18 agent hooks, HS-19 target-profile hardening
- **Unblocks:** HS-20-03
- **Owner:** unassigned

## Problem

AIPI can show that Claude or Codex is waiting, but speaking into the device still needs to become a useful reply to that waiting agent. The reply must be shaped for the correct target profile instead of relying on fragile active-window detection.

## Scope

### In

- Device-originated voice typing checks for a fresh awaiting Claude/Codex session.
- The web runtime routes captured device speech through the dictation pipeline when enabled.
- Waiting Codex sessions force `codex_cli`; waiting Claude sessions force `claude_code`.
- The latest waiting-agent context is attached to the dictation utterance.
- Focused regression coverage.

### Out

- Autonomous replies without user speech.
- Direct agent transport or API submission.
- Firmware gesture redesign.
- Cross-network device reach.

## Acceptance Criteria

- [x] Device voice capture can use the latest waiting-agent session as reply context.
- [x] Codex waiting sessions force the `codex_cli` target profile.
- [x] Claude waiting sessions force the `claude_code` target profile.
- [x] If the dictation pipeline is disabled or unavailable, voice typing preserves the existing raw processed-text behavior.
- [x] Tests cover the agent target override path.

## Test Plan

- Unit tests for agent-to-target override mapping.
- Web runtime unit test proving device voice capture passes waiting-agent target and context into the dictation pipeline.
- Focused agent/device/web-runtime tests.

## Notes

- This story uses the existing device start/stop audio flow. It does not add a new wire frame.
- Voice replies require `dictation.pipeline.enabled = true` to rewrite the transcript; otherwise HoldSpeak still types the processed transcript as before.
