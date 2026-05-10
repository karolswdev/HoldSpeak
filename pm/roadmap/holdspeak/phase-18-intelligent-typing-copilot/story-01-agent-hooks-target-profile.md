# HS-18-01 — Agent Hooks + Target-Profile Context Capture

- **Project:** holdspeak
- **Phase:** 18
- **Status:** done
- **Depends on:** existing dictation runtime and web runtime
- **Unblocks:** HS-18-02, HS-18-03
- **Owner:** unassigned

## Problem

HoldSpeak cannot reliably know where dictated text is going. For generic apps that is fine; for Claude Code, Codex, and terminal-based LLM workflows, the current working directory, project root, and recent assistant questions materially change what the user meant. Hooks give HoldSpeak a practical path to learn that context without guessing from the OS alone.

## Scope

### In

- Target-profile detector that can classify at least generic typing, terminal, Claude Code, Codex, and unknown.
- Hook-compatible context intake for agent CLIs that can provide `cwd`, session id, prompt text, and recent assistant-message context.
- Captured-context API and web status surface so users can see what HoldSpeak currently believes the target/project is.
- Clear controls for stale or wrong captured context.
- Safe fallback when hooks are absent, disabled, stale, or malformed.

### Out

- Automatically editing Claude Code or Codex configuration files.
- Blocking user prompts or agent tool calls.
- Long-term cloud memory or cross-device sync.

## Acceptance Criteria

- [ ] Target-profile detection has unit tests for generic, terminal, Claude Code, Codex, and unknown fixtures.
- [ ] Hook intake validates payloads, stores bounded context, and rejects oversized/malformed data without breaking dictation.
- [ ] Web/API surface shows captured agent context and includes a clear action.
- [ ] Documentation includes copy-ready Claude Code and Codex hook setup examples where applicable.
- [ ] Dictation continues normally when no agent context is present.

## Test Plan

- Unit tests for target-profile detection and hook payload validation.
- API tests for captured-context read/clear endpoints.
- Manual web runtime check for status display and stale-context clearing.

## Notes

- Hook context should be treated as advisory. The user's spoken text remains the primary input.
- Prefer small factual context blocks over instruction-like injected prompts.
- 2026-05-10 closeout: hook capture, target-profile detection, captured-context API/UI, clear action, copy-ready docs, and no-agent fallback are covered. See [evidence-story-01.md](./evidence-story-01.md).
