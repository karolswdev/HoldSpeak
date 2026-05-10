# Evidence — HS-18-01 Agent Hooks + Target-Profile Context Capture

**Story:** [story-01-agent-hooks-target-profile.md](./story-01-agent-hooks-target-profile.md)  
**Status:** done  
**Date:** 2026-05-10

## What Shipped

- Target-profile detection
  - Detects Codex CLI, Claude Code, terminal shell, browser/generic text, editor/generic text, chat/generic text, explicit profile overrides, and unknown/no-hint cases.
- Agent hook intake
  - `holdspeak agent-hook ingest --agent claude|codex` records session id, cwd, repo root, project name, model, prompt, tool name, and transcript path.
  - `CwdChanged` events prefer `new_cwd`.
  - Malformed hook payloads are dropped silently by the CLI hook command so agent hooks do not break the source tool.
  - User prompts and assistant-message captures are bounded to 4 KB.
  - Assistant-message capture is opt-in and clears on the next user prompt.
- Captured-context API and web status
  - `/api/dictation/agent-context` returns the latest project-scoped awaiting agent message.
  - `/api/dictation/agent-context/clear` clears stale/wrong captured context.
  - `/api/dictation/agent-hooks` returns copy-ready Claude/Codex hook templates and recent hook status.
  - Dictation page shows the captured-agent banner, clear action, hook templates, and hook status.
- Dictation fallback
  - The controller only adds agent context when a recent awaiting session exists and matches the active dictation project.
  - Dictation continues normally when no agent context is present.

## Commands Run

```bash
.venv/bin/pytest -q tests/unit/test_agent_context.py tests/unit/test_target_profile.py tests/integration/test_web_project_kb_api.py tests/unit/test_dictation_project_rewriter.py
```

Result: `62 passed in 1.81s`.

## Acceptance Mapping

- Target-profile unit tests for generic, terminal, Claude Code, Codex, and unknown fixtures: `tests/unit/test_target_profile.py`.
- Hook intake validation / bounded storage / malformed payload safety: `tests/unit/test_agent_context.py`.
- Web/API captured context + clear action: `tests/integration/test_web_project_kb_api.py`.
- Copy-ready hook setup docs: `README.md` and `docs/USER_GUIDE.md`.
- Dictation no-agent fallback: controller logic plus project-rewriter no-context/fallback tests.

## Residual Notes

- Hooks are advisory and optional. Generic typing still works without Claude/Codex hooks.
- The UI does not write Claude/Codex settings files; users copy templates after review.
