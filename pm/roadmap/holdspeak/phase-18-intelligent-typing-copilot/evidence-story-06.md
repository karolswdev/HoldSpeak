# Evidence — HS-18-06 External Agent CLI Summarizer Bridge

**Story:** [story-06-external-agent-summarizer.md](./story-06-external-agent-summarizer.md)  
**Status:** done  
**Date:** 2026-05-10

## What Shipped

- `holdspeak/agent_summarizer.py`
  - Builds safe default external-agent commands for Codex and Claude.
  - Rejects dangerous bypass / write-capable flags by default.
  - Supports disabled, default-safe, and custom command profiles.
  - Bounds prompt input and summary output.
  - Invokes external CLIs with `shell=False`.
- `AgentSession.summary`
  - Persists derived summarizer output on captured agent sessions.
  - Clears stale summary when the user submits a new prompt or clears agent context.
- `/api/dictation/agent-context/summarize`
  - Generates and stores a bounded summary for the latest captured awaiting agent message.
- `/api/dictation/agent-hooks`
  - Reports summarizer provider availability, safe-default command, and unsafe-override state.
- Dictation web UI
  - Adds an explicit “External agent summary” control.
  - Shows provider availability/safe command status.
  - Displays generated summaries in the captured-agent banner.
- Project rewriter
  - Prefers `activity["agent"]["summary"]` when present, then falls back to the raw captured assistant question.

## Commands Run

```bash
npm run build
```

Result: passed. Astro built 7 static pages into `holdspeak/static/_built/`.

```bash
.venv/bin/pytest -q tests/unit/test_agent_summarizer.py tests/unit/test_agent_context.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_target_profile.py tests/integration/test_web_project_kb_api.py
```

Result: `72 passed in 1.86s`.

```bash
python3 -m pytest -q tests/unit/test_agent_summarizer.py tests/unit/test_agent_context.py tests/unit/test_dictation_project_rewriter.py tests/unit/test_target_profile.py
```

Result: `45 passed, 2 warnings`.

## Real CLI Smoke

Safe Codex smoke:

```text
codex exec --sandbox read-only --ephemeral -
```

Result: passed. Returned a compact factual summary for the manual captured context. No bypass/yolo flags were used.

Safe Claude smoke:

```text
claude -p --tools "" --no-session-persistence --output-format json --max-budget-usd 0.10
```

Result: passed. Returned a compact factual summary for the manual captured context. No bypass/yolo flags were used.

## Acceptance Mapping

- Disabled/default-safe/custom command profiles: covered by `SummarizerCommandProfile` tests.
- Built-in Codex profile: covered by unit tests and real CLI smoke.
- Built-in Claude profile: covered by unit tests and real CLI smoke.
- Dangerous command rejection: covered by unit tests for dangerous Codex/Claude modes.
- Summary persistence: covered by `test_set_agent_session_summary_persists_derived_context`.
- Rewriter summary handoff: covered by `test_project_rewriter_prefers_agent_summary_over_raw_question`.
- Web provider status and summarize endpoint: covered by `tests/integration/test_web_project_kb_api.py`.

## Residual Notes

- The UI does not expose unsafe override configuration. This is intentional for v1. The API/status reports unsafe override as disabled.
- Full repository regression was not run as part of this story close; the targeted unit + web integration slice covers the changed surfaces.
