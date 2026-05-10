# Phase 18 — Final Summary

- **Phase opened:** 2026-05-10
- **Phase closed:** 2026-05-10
- **Chunks shipped:** 6

## Goal — was it met?

Original goal:

> Make HoldSpeak excellent at local intelligent typing, not just meeting intelligence. The product outcome is a voice-to-text loop that understands where the user is typing, can rewrite dictation before injection, can target Claude Code / Codex / generic text fields differently, and can use simple project-local conventions to add relevant context without requiring the user to repeat themselves.

**Yes — for the phase scope.** HoldSpeak now has the product substrate for project-aware local intelligent typing: target-profile detection, Claude/Codex hook context capture, project-local `.hs/` conventions, safe flat `.hs_*` compatibility reads, web maintenance affordances, OpenAI-compatible runtime support, and an optional bounded external-agent summarizer bridge.

Evidence per story:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md) ·
[03](./evidence-story-03.md) ·
[04](./evidence-story-04.md) ·
[05](./evidence-story-05.md) ·
[06](./evidence-story-06.md).

## Exit criteria — final state

- [x] Hook capture path documented and implemented for Claude Code and Codex-compatible environments where hook support exists; unsupported environments fail open with a visible status — [evidence-story-01](./evidence-story-01.md), [evidence-story-03](./evidence-story-03.md).
- [x] Web Dictation interface exposes agent-hook status, captured context, and project-context maintenance affordances — [evidence-story-03](./evidence-story-03.md).
- [x] Project context convention documented with safe file names, precedence rules, size limits, and write policy — [evidence-story-02](./evidence-story-02.md), [evidence-story-05](./evidence-story-05.md).
- [x] External-agent summarizer bridge can invoke configured Claude/Codex CLI commands in a bounded, read-only/no-tools mode to produce compact context from recent captured messages; dangerous modes require explicit opt-in and visible UI state — [evidence-story-06](./evidence-story-06.md).
- [x] Dictation rewriter supports generic OpenAI-compatible endpoints and local endpoints with clear timeout / fallback behavior — [evidence-story-04](./evidence-story-04.md).
- [x] User guide and README explain intelligent typing as a primary product surface, not an appendix to meetings — [evidence-story-05](./evidence-story-05.md).
- [x] Regression suite green at the phase baseline; evidence files capture commands, results, and manual web checks — [evidence-story-05](./evidence-story-05.md). Baseline: `1622 passed, 5 skipped` with `tests/e2e/test_metal.py` ignored.
- [x] `final-summary.md` records what shipped, what remains speculative, and which product surfaces are ready for daily use — this file.

## Stories shipped

| ID | Title | Commit/PR | Date |
|---|---|---|---|
| HS-18-01 | Agent hooks + target-profile context capture | this working set | 2026-05-10 |
| HS-18-02 | Project context conventions + safe maintenance contract | this working set | 2026-05-10 |
| HS-18-03 | Web cockpit for intelligent typing and project context | this working set | 2026-05-10 |
| HS-18-04 | Runtime provider flexibility for OpenAI-compatible endpoints | this working set | 2026-05-10 |
| HS-18-05 | Product documentation and phase exit | this working set | 2026-05-10 |
| HS-18-06 | External agent CLI summarizer bridge | this working set | 2026-05-10 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | Manual smoke against the user's real LAN OpenAI-compatible endpoint | Contract behavior is covered by fake-server tests; real endpoint availability is environment-specific. | Daily dogfood / next runtime hardening phase |
| — | Automatic mutation of Claude/Codex settings | Explicitly out of scope for safety; the web UI provides copy-ready templates instead. | Not planned unless a later phase defines a reviewed consent flow |
| — | Automatic edits to `.hs/memory.md` during dictation | Prompt-injection and accidental persistence risk; phase 18 keeps writes user-initiated. | Future memory-management phase |

## Surprises and lessons

- **Hooks are the right context channel, not a dependency.** Claude/Codex hooks solve `cwd` and active-session ambiguity, but generic typing must still work when no hook exists.
- **Flat `.hs_*` files are useful as an adoption bridge.** The safe contract is canonical `.hs/` writes, read-only flat compatibility reads, explicit precedence, and warnings for binary/large/secret-looking files.
- **External-agent summarization needs hard permission posture.** The useful version is bounded, read-only/no-tools/ephemeral by default. Dangerous CLI flags must remain blocked unless a future advanced mode deliberately owns the risk.
- **OpenAI-compatible support is table stakes.** Users already run llama.cpp server, LM Studio, Ollama bridges, vLLM, and LiteLLM. The implementation should target the common chat/completions shape and fail open to original dictation.
- **The web cockpit is now the product surface.** `/dictation` is where users can inspect readiness, runtime, project context, hooks, dry-run output, and rewrite behavior before turning the pipeline on.

## Handoff to phase 19

- What is now available that was not before: project-aware intelligent typing with target-profile detection, `.hs/` context, Claude/Codex hook capture, optional external-agent summaries, OpenAI-compatible runtime support, and web maintenance UI.
- What changed in the contract/canon: HoldSpeak is documented as a local-first voice workspace with two primary surfaces: meeting intelligence and intelligent typing.
- What the next phase should read first: `docs/USER_GUIDE.md`, `README.md`, `holdspeak/agent_context.py`, `holdspeak/target_profile.py`, `holdspeak/plugins/dictation/builtin/project_rewriter.py`, `holdspeak/plugins/dictation/runtime_openai_compatible.py`, `web/src/pages/dictation.astro`, and `web/src/scripts/dictation-app.js`.
- Recommended next phase: daily-use hardening of intelligent typing. Focus on real endpoint dogfooding, latency telemetry, target-profile refinements, manual browser smoke scripts, and safe user-controlled memory editing.

## Final asset / test posture

- Broad regression: `.venv/bin/pytest -q --ignore=tests/e2e/test_metal.py` — `1622 passed, 5 skipped in 120.72s`.
- Web build: `cd web && npm run build` — 7 static pages built into `holdspeak/static/_built/`.
- Markdown sanity: README/User Guide/HS-18 status local links passed.
- Evidence files: `evidence-story-01.md` through `evidence-story-06.md`, except no `evidence-story-00.md` because HS-18 had six named stories.
- Ready for daily use: voice typing, `/dictation` readiness/runtime/project context/hooks/dry-run, Claude/Codex hook templates, OpenAI-compatible runtime configuration, and user-reviewed `.hs/` project context.
- Still speculative: automatic memory mutation, real-LAN endpoint performance across provider families, automatic agent-settings writes, and cross-app target detection on constrained Wayland environments.
