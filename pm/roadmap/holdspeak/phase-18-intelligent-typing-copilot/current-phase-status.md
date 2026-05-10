# Phase 18 — Intelligent Typing Copilot

**Phase closed:** 2026-05-10. See [final-summary.md](./final-summary.md). This file is now frozen per PMO contract §6.
**Last updated:** 2026-05-10 (HS-18-05 shipped — phase closed with final summary and broad regression evidence).

## Goal

Make HoldSpeak excellent at local intelligent typing, not just meeting intelligence. The product outcome is a voice-to-text loop that understands where the user is typing, can rewrite dictation before injection, can target Claude Code / Codex / generic text fields differently, and can use simple project-local conventions to add relevant context without requiring the user to repeat themselves.

This phase captures the work already started around target-profile detection, agent CLI hooks, OpenAI-compatible local endpoints, `.hs` project files, and the web cockpit needed to maintain those settings.

## Scope

### In

- Target profile detection for likely surfaces: generic typing, terminal, Claude Code, Codex, and project-aware LLM CLI sessions.
- Agent-hook integration guidance for Claude Code and Codex so HoldSpeak can learn the current `cwd`, active project, and recent assistant questions when those tools expose hook context.
- Project-local context conventions such as `.hs_context`, `.hs_issues`, `.hs_memory`, and equivalent `.hs/` layouts, with a safe read/write contract.
- Dictation intelligence flows: rewrite, clarify, expand, compress, preserve-verbatim, and project-context injection before keyboard output.
- Runtime provider flexibility: local llama.cpp and any OpenAI-compatible endpoint, not only a packaged local model.
- Optional external-agent summarizer bridge: HoldSpeak can ask a local Claude Code / Codex CLI process to summarize the last few captured agent messages into compact context for dictation, using read-only / no-tools defaults unless the user explicitly opts into stronger permissions.
- Web interface support for viewing and maintaining project context files, hook setup status, target profiles, and intelligent-typing behavior.
- User-facing documentation that explains the product plainly: install, dictate, configure runtimes, enable agent hooks, manage project context, and troubleshoot.

### Out

- AIPI-Lite active-device upstream frames (`device_health`, `query`) — HS-17 owns that scaffold.
- Cross-network device reach — HS-15 owns that.
- Realizing the remaining meeting synthesizer stubs — HS-16 owns that.
- Hosted sync, team accounts, or cloud memory.
- Automatically mutating Claude Code / Codex settings without explicit user action.
- Defaulting to `--dangerously-skip-permissions`, `--dangerously-bypass-approvals-and-sandbox`, or equivalent write-capable agent modes for background summarization.

## Exit criteria (evidence required)

- [x] Hook capture path documented and implemented for Claude Code and Codex-compatible environments where hook support exists; unsupported environments fail open with a visible status.
- [x] Web Dictation interface exposes agent-hook status, captured context, and project-context maintenance affordances.
- [x] Project context convention documented with safe file names, precedence rules, size limits, and write policy.
- [x] External-agent summarizer bridge can invoke configured Claude/Codex CLI commands in a bounded, read-only/no-tools mode to produce compact context from recent captured messages; dangerous modes require explicit opt-in and visible UI state.
- [x] Dictation rewriter supports generic OpenAI-compatible endpoints and local endpoints with clear timeout / fallback behavior.
- [x] User guide and README explain intelligent typing as a primary product surface, not an appendix to meetings.
- [x] Regression suite green at the phase baseline; evidence files capture commands, results, and manual web checks.
- [x] `final-summary.md` records what shipped, what remains speculative, and which product surfaces are ready for daily use.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-18-01 | Agent hooks + target-profile context capture | done | [story-01-agent-hooks-target-profile.md](./story-01-agent-hooks-target-profile.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-18-02 | Project context conventions + safe maintenance contract | done | [story-02-project-context-conventions.md](./story-02-project-context-conventions.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-18-03 | Web cockpit for intelligent typing and project context | done | [story-03-web-intelligent-typing-cockpit.md](./story-03-web-intelligent-typing-cockpit.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-18-04 | Runtime provider flexibility for OpenAI-compatible endpoints | done | [story-04-openai-compatible-runtimes.md](./story-04-openai-compatible-runtimes.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-18-05 | Product documentation and phase exit | done | [story-05-docs-and-phase-exit.md](./story-05-docs-and-phase-exit.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-18-06 | External agent CLI summarizer bridge | done | [story-06-external-agent-summarizer.md](./story-06-external-agent-summarizer.md) | [evidence-story-06.md](./evidence-story-06.md) |

(Status values: `backlog`, `ready`, `in-progress`, `blocked`, `done`, `cancelled`.)

## Where we are

Phase 18 is closed. HoldSpeak now has an evidence-backed intelligent-typing layer: target profiles, Claude/Codex hook context, `.hs/` project context, OpenAI-compatible runtime support, external-agent summaries, and a web cockpit for daily use. See [final-summary.md](./final-summary.md) for the handoff to phase 19.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Hook support differs across Claude Code, Codex, and generic terminals | high | Treat hooks as optional accelerators; detect support and show clear setup/status in the web UI. Always preserve generic typing mode. | If hook APIs churn or are unavailable, reduce scope to manual project selection plus paste-target detection. |
| Project-context files become prompt-injection or data-leak surfaces | medium | Keep conventions local, explicit, size-limited, and user-reviewable. Never auto-send secrets. Prefer factual context over instruction-like content. | If context injection causes wrong or unsafe rewrites, disable automatic injection by default and require explicit profile opt-in. |
| Rewriter latency makes voice typing feel worse than plain transcription | medium | Default to fast local/no-op path; use timeouts and fall back to original transcript. Make rewrite mode visible and easy to disable. | If p95 rewrite latency exceeds the typing loop budget during daily use, gate rewriters behind explicit commands. |
| Web cockpit grows into a settings maze | medium | Start with status, setup, and project files only. Do not expose every internal knob. | If users cannot explain what a setting does in one sentence, remove or hide it behind advanced mode. |
| OpenAI-compatible endpoints vary in schema quality | medium | Use conservative request shapes and provider probes; document known-good llama.cpp / vLLM / Ollama-compatible setups separately. | If endpoint variance breaks normal dictation, disable the provider and surface exact compatibility failure. |
| External agent CLI calls mutate the repo or leak more context than intended | medium | Default to read-only/no-tools/ephemeral invocation profiles and pass only bounded excerpts. Dangerous bypass flags are never generated by default. | If a summarizer attempts writes, shell commands, network expansion, or full transcript exfiltration, disable the bridge and require explicit user reconfiguration. |

## Decisions made

- 2026-05-10 — **Phase 18 is the current product phase.** HS-17 remains scaffolded for AIPI-Lite hardware; the active HoldSpeak push is intelligent typing.
- 2026-05-10 — **Hooks are a context channel, not a hard dependency.** They improve project detection for Claude Code / Codex, but HoldSpeak must still work in generic apps.
- 2026-05-10 — **OpenAI-compatible endpoint support is first-class.** HoldSpeak should not imply that local intelligence requires one bundled llama.cpp package.
- 2026-05-10 — **Project files must be simple and inspectable.** Favor `.hs_context`, `.hs_issues`, `.hs_memory`, or a small `.hs/` directory over opaque databases for user-authored project context.
- 2026-05-10 — **External agent summarization belongs in phase 18, but with safe defaults.** Codex / Claude CLI calls can compress recent agent context, but HoldSpeak must default to read-only or no-tools invocation and treat bypass flags as explicit user-owned advanced configuration.

## Decisions deferred

- Exact project-file layout: flat dotfiles vs `.hs/` directory. Default until decided: support read-only discovery of both, write through the web UI only after an explicit policy is documented.
- Whether HoldSpeak should edit project memory automatically. Default until decided: propose edits in the web UI; do not silently mutate memory files.
- Which target profiles ship enabled by default. Default until decided: generic typing enabled; agent profiles available but opt-in.
- Whether agent context is stored per session, per project, or only in-memory. Default until decided: in-memory with explicit clear controls.
- Whether the summarizer should call Codex, Claude, a local OpenAI-compatible endpoint, or all of them as ranked providers. Default until decided: provider order is user-configured and disabled unless explicitly enabled.
