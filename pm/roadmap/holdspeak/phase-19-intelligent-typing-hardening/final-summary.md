# Phase 19 — Final Summary

- **Phase opened:** 2026-05-10
- **Phase closed:** 2026-05-24
- **Chunks shipped:** 5

## Goal — was it met?

Original goal:

> Make the intelligent-typing loop trustworthy for daily use. Phase 18 proved the substrate; Phase 19 hardens the experience with safe project-documentation suggestions, latency/fallback visibility, target-profile refinement, and real endpoint dogfooding.

**Yes.** HoldSpeak now has a daily-use intelligent-typing loop with safe `.hs/.../*.md` documentation suggestions, explicit web review/apply/dismiss, normalized latency/fallback telemetry, manual target-profile override, and a real local OpenAI-compatible endpoint smoke.

Evidence per story:
[01](./evidence-story-01.md) ·
[02](./evidence-story-02.md) ·
[03](./evidence-story-03.md) ·
[04](./evidence-story-04.md) ·
[05](./evidence-story-05.md).

## Exit criteria — final state

- [x] Coding-agent dictation can include a local LLM-generated context-preservation suggestion with a safe `.hs/.../*.md` target path — [evidence-story-01](./evidence-story-01.md).
- [x] Web UI can review and explicitly apply or dismiss suggested project documentation updates — [evidence-story-02](./evidence-story-02.md).
- [x] Dictation readiness/dry-run surfaces per-stage latency and fallback reasons — [evidence-story-03](./evidence-story-03.md).
- [x] Users can override target profile when OS/window detection is wrong — [evidence-story-04](./evidence-story-04.md).
- [x] At least one real OpenAI-compatible endpoint profile is dogfooded and documented — [evidence-story-05](./evidence-story-05.md).
- [x] Broad regression suite is green at phase close; evidence files capture commands and results — [evidence-story-05](./evidence-story-05.md).
- [x] `final-summary.md` records what became daily-use ready and what remains experimental — this file.

## Stories shipped

| ID | Title | Commit/PR | Date |
|---|---|---|---|
| HS-19-01 | Local LLM project documentation suggestions | this working set | 2026-05-10 |
| HS-19-02 | Web review/apply flow for suggested `.hs/` updates | this working set | 2026-05-10 |
| HS-19-03 | Dictation latency and fallback telemetry | this working set | 2026-05-10 |
| HS-19-04 | Target profile override and refinement | this working set | 2026-05-10 |
| HS-19-05 | Real endpoint dogfood and phase exit | this working set | 2026-05-24 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | Hosted endpoint certification | Phase only needed one real OpenAI-compatible smoke. Hosted providers have auth, privacy, and cost differences that need their own matrix. | Future runtime compatibility matrix |
| — | Silent project-memory writes | Still too risky for prompt injection, secrets, and repo hygiene. | Not planned without explicit review flow |
| — | Per-app automation rules for target profile | Manual override solves the immediate daily-use issue without adding brittle OS-specific automation. | Future target detection hardening |

## Surprises and lessons

- **The optional dependency is part of the real setup.** The local endpoint was reachable, but HoldSpeak could not use it until `openai` was installed. Docs should keep the `.[dictation-openai]` install path prominent.
- **The dry-run loop is the right dogfood surface.** It exposes endpoint configuration, runtime load status, stage latency, metadata, and final text without typing into another app.
- **Suggestion writes need to stay explicit.** The safety posture still holds: HoldSpeak can propose small `.hs/.../*.md` updates, but users or agents decide whether to write them.
- **Target-profile override is necessary even after detection improves.** Terminals, Wayland, and agent CLIs make active-window inference unreliable enough that a visible manual override should remain first-class.

## Ready for daily use

- Basic voice typing with punctuation cleanup.
- `/dictation` readiness, runtime setup, project context, dry-run, target override, and project-doc suggestion review.
- OpenAI-compatible dictation runtime against local `/v1/chat/completions` endpoints.
- Safe `.hs/.../*.md` project documentation suggestions with explicit apply/dismiss.
- Fallback visibility when a runtime is unavailable, slow, malformed, or disabled.

## Still experimental

- Quality/performance across every OpenAI-compatible endpoint family.
- Automatic target-profile detection on constrained Linux/Wayland setups.
- Project-doc suggestion quality thresholds under long, noisy coding sessions.
- Any automatic mutation of project memory.

## Handoff

The next intelligent-typing work should be compatibility and quality, not more UI knobs: a small endpoint matrix, provider-specific quirks, latency budgets, prompt quality checks, and real daily dogfood.

The next product conversation should move to AIPI-Lite as a physical companion surface: same-LAN reliability, LCD state, gestures, meeting status, and useful query/response flows before cross-network reach.

## Final asset / test posture

- Real endpoint smoke: `http://127.0.0.1:8080/v1`, model `Qwen3.5-9B-UD-Q6_K_XL.gguf`, direct `/v1/chat/completions` and HoldSpeak `dictation dry-run` both passed.
- Broad regression: `.venv/bin/pytest -q -m 'not metal'` — `1809 passed, 5 skipped, 16 deselected in 123.71s`.
- Unit baseline: `.venv/bin/pytest -q tests/unit` — `1403 passed, 1 skipped in 70.26s`.
- Integration baseline: `.venv/bin/pytest -q tests/integration` — `394 passed, 3 skipped in 54.15s`.
- Mock E2E voice flow: `.venv/bin/pytest -q tests/e2e/test_voice_typing_flow.py` — `12 passed in 0.08s`.
- Web build: `cd web && npm run build` — 7 static pages built into `holdspeak/static/_built/`.
- Diff hygiene: `git diff --check` — passed.
