# HS-18-06 — External Agent CLI Summarizer Bridge

- **Project:** holdspeak
- **Phase:** 18
- **Status:** done
- **Depends on:** HS-18-01
- **Unblocks:** richer project-aware dictation context
- **Owner:** unassigned

## Problem

Hook capture can tell HoldSpeak that Claude Code or Codex is active and can capture recent prompts or assistant questions. Sometimes that raw context is still too large or too messy to inject into a dictation rewrite. HoldSpeak should be able to ask a local agent CLI to summarize the last few captured messages into a compact, factual context block.

This is not a second autonomous coding agent loop. It is a bounded summarization bridge: recent captured agent context in, compact context out.

## Scope

### In

- Configurable summarizer providers for installed CLIs:
  - Codex: `codex exec` with safe defaults such as `--sandbox read-only`, `--ephemeral`, and bounded stdin.
  - Claude Code: `claude -p` with safe defaults such as `--tools ""`, `--no-session-persistence`, `--output-format json` or text, `--max-budget-usd`, and bounded stdin.
- Prompt contract: summarize recent captured prompts / assistant messages into facts useful for dictation, not instructions that override the user.
- Strict timeout, max input bytes, max output bytes, and fallback to no summary.
- Provider status in the web UI: installed, enabled, last run, last error, and permission mode.
- Tests with fake `codex` / `claude` binaries so CI does not need real agent accounts.

### Out

- Defaulting to `codex --dangerously-bypass-approvals-and-sandbox`, `codex --sandbox danger-full-access`, `claude --dangerously-skip-permissions`, or similar write-capable modes.
- Letting the summarizer edit files, run shell commands, or continue conversations autonomously.
- Sending full transcripts by default.
- Replacing the local OpenAI-compatible rewriter path. This is an optional context-compression provider, not the only intelligence path.

## Acceptance Criteria

- [ ] Summarizer config supports disabled/default-safe/custom command profiles.
- [ ] Built-in Codex profile invokes `codex exec` in read-only / ephemeral mode and passes bounded context via stdin.
- [ ] Built-in Claude profile invokes `claude -p` with tools disabled or an equivalent no-write profile and passes bounded context via stdin.
- [ ] Dangerous command strings are rejected unless the user enables an explicit advanced/unsafe override.
- [ ] Summary output is stored as derived context with timestamp, provider id, source session id, and truncation metadata.
- [ ] Dictation rewrite flow can include the summary when fresh and falls back cleanly when missing or failed.
- [ ] Web UI shows provider availability and whether unsafe override is enabled.

## Test Plan

- Unit tests for command building, unsafe-command detection, input/output bounding, timeout handling, and fallback.
- Integration-style tests using temporary fake `codex` and `claude` executables on `PATH`.
- Manual smoke test with real installed CLIs using a harmless summarization prompt and a throwaway context payload.

## Notes

- The user suggested bypass/yolo-style commands as possible power-user configuration. That can exist only as explicit user-owned advanced configuration, never as HoldSpeak's generated default.
- The summary should be factual: current project, open question, constraints, and what the agent appears to be waiting for. Avoid phrasing it as a system instruction.
- 2026-05-10 implementation start: `holdspeak/agent_summarizer.py` now builds safe default Codex/Claude commands, rejects dangerous flags by default, bounds prompt/output sizes, and invokes fake CLI fixtures in unit tests. `ProjectRewriter` can consume a precomputed `activity["agent"]["summary"]` before falling back to raw assistant text.
- 2026-05-10 continuation: `AgentSession` now persists a derived `summary`, `/api/dictation/agent-context/summarize` can generate/store one on demand, and the Dictation Agent Hooks tab has an explicit summarization control. Remaining work: provider availability/status polish, unsafe-override visibility if custom commands are introduced, full integration test run in the project dependency environment, and evidence.
- 2026-05-10 real CLI smoke: safe Codex execution worked with `codex exec --sandbox read-only --ephemeral -`; safe Claude execution worked with `claude -p --tools "" --no-session-persistence --output-format json --max-budget-usd 0.10`. No bypass/yolo modes were used.
- 2026-05-10 closeout: provider availability/status is exposed in `/api/dictation/agent-hooks` and the Dictation UI; focused `.venv` test slice passed (`72 passed`). See [evidence-story-06.md](./evidence-story-06.md).
