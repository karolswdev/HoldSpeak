# Phase 19 — Intelligent Typing Daily-Use Hardening

**Last updated:** 2026-05-24 (HS-19-05 closed: real endpoint dogfood and phase exit).

## Goal

Make the intelligent-typing loop trustworthy for daily use. Phase 18 proved the substrate; Phase 19 hardens the experience with safe project-documentation suggestions, latency/fallback visibility, target-profile refinement, and real endpoint dogfooding.

## Scope

### In

- Local LLM suggestions for narrow `.hs/.../*.md` project documentation updates.
- Explicit no-auto-write policy for memory/docs suggestions.
- Runtime/fallback telemetry visible in the Dictation cockpit.
- Target-profile override/refinement for Codex, Claude, browser, editor, chat, and terminal targets.
- Real OpenAI-compatible endpoint dogfooding and known-good config notes.

### Out

- Silent mutation of `.hs/` files.
- Automatic commits or agent-settings edits.
- Meeting-side synthesizer work.
- AIPI-Lite device reach.

## Exit criteria

- [x] Coding-agent dictation can include a local LLM-generated context-preservation suggestion with a safe `.hs/.../*.md` target path.
- [x] Web UI can review and explicitly apply or dismiss suggested project documentation updates.
- [x] Dictation readiness/dry-run surfaces per-stage latency and fallback reasons.
- [x] Users can override target profile when OS/window detection is wrong.
- [x] At least one real OpenAI-compatible endpoint profile is dogfooded and documented.
- [x] Broad regression suite is green at phase close; evidence files capture commands and results.
- [x] `final-summary.md` records what became daily-use ready and what remains experimental.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-19-01 | Local LLM project documentation suggestions | done | [story-01-project-doc-suggestions.md](./story-01-project-doc-suggestions.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-19-02 | Web review/apply flow for suggested `.hs/` updates | done | [story-02-web-suggestion-review.md](./story-02-web-suggestion-review.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-19-03 | Dictation latency and fallback telemetry | done | [story-03-latency-fallback-telemetry.md](./story-03-latency-fallback-telemetry.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-19-04 | Target profile override and refinement | done | [story-04-target-profile-override.md](./story-04-target-profile-override.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-19-05 | Real endpoint dogfood and phase exit | done | [story-05-endpoint-dogfood-and-exit.md](./story-05-endpoint-dogfood-and-exit.md) | [evidence-story-05.md](./evidence-story-05.md) |

(Status values: `backlog`, `ready`, `in-progress`, `blocked`, `done`, `cancelled`.)

## Where we are

HS-19 is closed. HoldSpeak now has safe project documentation suggestions, explicit web review/apply/dismiss, normalized telemetry, a persisted target profile override for Codex, Claude, terminal, browser, editor, or chat, and real local OpenAI-compatible endpoint dogfood evidence. See [final-summary.md](./final-summary.md) for phase posture and handoff.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Suggestions become noisy or generic | medium | Require narrow `.hs/{memory,decisions,handoffs,workflows,issues}/*.md` targets and allow `NO_SUGGESTION`. | If suggestions appear on most trivial dictations, gate behind explicit command or web review only. |
| Suggested docs leak secrets | medium | Reject secret-looking content and never write automatically. | If a suggestion includes credentials or sensitive paths, disable injection until filters improve. |
| Added LLM call hurts typing latency | medium | Only run suggestions for coding-agent targets and fail open. Add telemetry in HS-19-03. | If p95 typing latency regresses materially, move suggestions to async/web-only. |
| Agent prompts become too bulky | medium | Keep suggestion content small and single-purpose. | If agents ignore the user's actual request due to suggestion noise, make injection opt-in per target. |

## Decisions made

- 2026-05-10 — **Suggestions are proposals, not writes.** HoldSpeak can inject or display a draft `.hs/.../*.md` update, but the user or agent chooses whether to write it.
- 2026-05-10 — **Use super-narrow files.** Prefer one fact, decision, workflow, handoff, or issue per Markdown file.
- 2026-05-10 — **Coding agents first.** Suggestion injection starts with Codex/Claude targets, not generic browser/editor typing.

## Decisions deferred

- Whether suggestions should be injected automatically, shown only in web review, or controlled per target.
- Exact web UI for accepting/dismissing suggestions.
- Whether accepted suggestions should update `.hs/memory.md` or directory-style `.hs/memory/*.md` by default.
