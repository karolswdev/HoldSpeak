# Evidence — HS-33-01 (Model framing + `MODELS.md`)

**Shipped:** 2026-06-03. Stopped prescribing aging, hard-coded model names in
user-facing strings; refreshed example/default values to the current **Qwen3.5**
family; documented the bring-your-own contract in a new `docs/MODELS.md`; and
clarified that the intel `cloud` provider is "any OpenAI-compatible endpoint."
No runtime behavior changed — only default *values*, guidance *strings*, and
docs.

## De-prescribing — user-facing strings reframed

- `holdspeak/plugins/dictation/runtime_llama_cpp.py` — the missing-GGUF error
  no longer says "Download `Qwen2.5-3B-…`"; it now says "point this at **any**
  GGUF chat model (e.g. a current small instruct model like Qwen3.5-4B-Instruct)
  … or use an OpenAI-compatible endpoint. See docs/MODELS.md."
- `holdspeak/plugins/dictation/runtime_mlx.py` — the missing-MLX error now says
  "point this at **any** MLX chat model (e.g. a current Qwen3.5 MLX build) … or
  set an HF repo id. See docs/MODELS.md."
- `holdspeak/plugins/dictation/guidance.py` — `runtime_model_download_command`
  gained a docstring stating the named model is a *suggestion*; the missing-model
  command label is now **"Download a suggested model"** (was "Download default
  model"); `doctor_model_fix` now phrases it "download a model (e.g. {name})".
- `holdspeak/intel.py` — module docstring rewritten: providers are "local
  (in-process GGUF)" and "any OpenAI-compatible endpoint" with a note that the
  `cloud` name is historical and the API key is optional for self-hosted.

## Refreshed example/default model values (Qwen3.5 family)

| Setting | Old | New |
|---|---|---|
| `LLMRuntimeConfig.mlx_model` | `Qwen3-8B-MLX-4bit` | `Qwen3.5-8B-MLX-4bit` |
| `LLMRuntimeConfig.llama_cpp_model_path` | `Qwen2.5-3B-Instruct-Q4_K_M.gguf` | `Qwen3.5-4B-Instruct-Q4_K_M.gguf` |
| `LLMRuntimeConfig.openai_compatible_model` | `qwen2.5-7b-instruct` | `qwen3.5-8b-instruct` |
| `MeetingConfig.intel_realtime_model` | `Mistral-7B-Instruct-v0.3-Q6_K.gguf` | `Qwen3.5-9B-Instruct-Q6_K.gguf` |
| `intel.DEFAULT_INTEL_MODEL_PATH` | `Mistral-7B-Instruct-v0.3-Q6_K.gguf` | `Qwen3.5-9B-Instruct-Q6_K.gguf` |
| `build_runtime()` defaults (`runtime.py`) | same trio as above | refreshed to match |
| MLX runtime `__init__` default (`runtime_mlx.py`) | `Qwen3-8B-MLX-4bit` | `Qwen3.5-8B-MLX-4bit` |
| guidance download commands (`guidance.py`) | bartowski/Qwen2.5-3B-GGUF, mlx-community/Qwen3-8B-MLX-4bit | bartowski/Qwen3.5-4B-GGUF, mlx-community/Qwen3.5-8B-MLX-4bit |

The intel default aligns with what the project actually runs (the `.43` box →
Qwen3.5-9B-Q6). The intel `cloud` provider already honors `intel_cloud_base_url`
and treats the key as optional — no code change needed, only documentation.

## Web docs page (rebuilt)

- `web/src/pages/docs/dictation-runtime.astro` — model names refreshed to the
  Qwen3.5 family; the lede and each backend section now frame the named model as
  a *suggestion* (with `# Example — swap for …` comments and a pointer to
  `docs/MODELS.md`). Rebuilt via `cd web && npm run build` (Node 22.21) so the
  served `holdspeak/static/_built/docs/dictation-runtime/index.html` matches.
  Verified: built HTML has **3×** `Qwen3.5-4B-Instruct-Q4_K_M.gguf` + **5×**
  `Qwen3.5-8B-MLX-4bit`, **zero** stale `Qwen2.5`/`Qwen3-8B-MLX`.

## New: `docs/MODELS.md`

The bring-your-own contract — the three ways to bring an LLM (GGUF in-process ·
MLX on Apple · any OpenAI-compatible endpoint), a "names are a moving target,
treat as suggestions" banner, a per-consumer "where to set it" table, sizing
intuition, and an explicit "the intel `cloud` provider is **not** necessarily a
hosted/paid API — point it at a self-hosted LAN server and it stays local; the
API key is optional for keyless endpoints" note.

## Canon doc refreshed

- `docs/MEETING_MODE_GUIDE.md` — "Recommended: Qwen2.5-32B or Mistral-7B" →
  bring-your-own framing + a link to MODELS.md; the model table is now a *size
  tier* shape guide (not named checkpoints); the `curl` hard-link to a specific
  Mistral GGUF was removed in favor of a swap-the-repo `hf download` example; the
  config-reference default and "Mistral path"/"Mistral-7B vs Qwen-32B" mentions
  de-prescribed.

## Test assertions updated in the same commit

- `tests/unit/test_config.py` — `intel_realtime_model` default assertion.
- `tests/unit/test_doctor_command.py`, `tests/unit/test_dictation_runtime_guidance.py`
  — doctor/guidance fix model-name assertions.
- `tests/integration/test_web_dictation_readiness_api.py` — built-docs body assertion.
- `tests/integration/test_web_dictation_settings_api.py` — roundtrip payload values.
- `tests/integration/test_runtime_llama_cpp.py`, `test_dictation_llama_cpp_e2e.py`,
  `test_runtime_mlx.py` — gated-integration `DEFAULT_MODEL` constants + docstring.
- `tests/e2e/test_meeting_transcription.py` — intel-model fallback candidate.
- `web/scripts/capture-gallery.py` — gallery screenshot config model path.

## Tests ran

- `uv run pytest -q tests/unit/test_config.py tests/unit/test_doctor_command.py
  tests/unit/test_dictation_runtime_guidance.py
  tests/integration/test_web_dictation_readiness_api.py
  tests/integration/test_web_dictation_settings_api.py` → **122 passed**.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1953 passed, 15 skipped**
  (skips are model-/backend-gated integration + missing WAV fixtures; the doc-drift
  guard from HS-32-06 is in this run and passed).
- `uv run ruff check` on every touched `holdspeak/` file → **All checks passed!**
  (the 12 pre-existing ruff findings elsewhere in `holdspeak/` are untouched files —
  `commands/dictation.py`, `main.py`, `meeting_session.py`, etc.)

## Done-when

- [x] No user-facing string tells the user to download one specific model; framed
      as suggestions with the OpenAI-compatible escape hatch.
- [x] Example/default model names are current (Qwen3.5 family).
- [x] `docs/MODELS.md` exists and documents the bring-your-own contract; intel
      `cloud` is clearly "OpenAI-compatible endpoint."
- [x] Full suite green; touched files ruff-clean.

## Deviations

- **GGUF stays** (per the phase decision) — only model *names* + *prescription*
  changed, not the format.
- Illustrative size references with no version (e.g. "Qwen 32B in ~8s",
  "~14–32B tier") were kept — they don't rot the way a pinned checkpoint does.
- Internal/historical plan docs (`docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`)
  were **not** touched — they're historical spec, and `docs/` reorg (HS-33-03)
  owns that surface.
