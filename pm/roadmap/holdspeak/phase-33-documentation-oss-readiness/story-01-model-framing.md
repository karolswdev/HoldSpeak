# HS-33-01 — Model framing + `MODELS.md`

- **Status:** done (2026-06-03). Evidence: [evidence-story-01.md](./evidence-story-01.md).

## Goal

Stop painting the project into a corner with aging, prescribed model names.
HoldSpeak's LLM layer is already well-abstracted (dictation: an `LLMRuntime`
Protocol over `auto|mlx|llama_cpp|openai_compatible`; intel: `local` GGUF + a
`cloud` provider that takes a configurable `base_url`, i.e. any OpenAI-compatible
endpoint). The problem is *framing*: user-facing strings say "Download exactly
`Qwen2.5-3B-Instruct-Q4_K_M.gguf`", and defaults pin `Mistral-7B-Instruct-v0.3` /
`Qwen3-8B-MLX` — all 2–3 generations stale (Qwen is at 3.5/3.6; the project's own
`.43` box already runs Qwen3.5-9B). **GGUF is fine** — it's the current standard;
only the model *names* and the *prescription* are the problem.

## Scope

- **De-prescribe** the user-facing strings — `plugins/dictation/guidance.py`,
  `plugins/dictation/runtime_llama_cpp.py`, `runtime_mlx.py` error/guidance text:
  "Download exactly X" → "point this at **any** GGUF chat model (e.g. a current
  small instruct model like Qwen3.5-4B); or use any OpenAI-compatible endpoint."
- **Refresh the example/default model values** to the current Qwen3.5 family,
  aligned with what the project actually runs:
  - dictation `llama_cpp_model_path` (`config.py`, `runtime.py`): `Qwen2.5-3B-…`
    → a current small instruct GGUF (e.g. `Qwen3.5-4B-Instruct-Q4_K_M.gguf`).
  - intel `intel_realtime_model` (`config.py`, `intel.py` default): `Mistral-7B-
    Instruct-v0.3-Q6_K` → e.g. `Qwen3.5-9B-…` (what `.43` runs).
  - mlx `mlx_model`: `Qwen3-8B-MLX-4bit` → a current Qwen3.5 MLX build.
  - Update any pinned test assertions in the **same** commit.
- **Clarify the intel `cloud` naming.** Document (and/or alias) that intel's
  `cloud` provider means "any OpenAI-compatible endpoint" — local LAN, Ollama,
  vLLM, llama.cpp-server, or actual cloud — it already honors `cloud_base_url`
  and treats the key as optional for self-hosted. (Dictation already names this
  well: `openai_compatible`.)
- **Add `docs/MODELS.md`** — the bring-your-own contract: GGUF in-process · MLX on
  Apple · any OpenAI-compatible endpoint; current *suggestions* (not
  requirements) with a "these are a moving target, refreshed periodically" note;
  how to point each consumer (dictation / intel) at your own model.

## Test plan

- `grep` tests for the old model paths; update any pinned assertions.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green.
- `holdspeak doctor` still resolves backends (no behavior change).

## Done when

- [x] No user-facing string tells the user to download one specific model;
      they're framed as suggestions, with the OpenAI-compatible escape hatch.
- [x] Example/default model names are current (Qwen3.5 family).
- [x] `docs/MODELS.md` exists and documents the bring-your-own contract; intel
      `cloud` is clearly "OpenAI-compatible endpoint."
- [x] Full suite green; ruff clean.
