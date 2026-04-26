# HS-4-04 — Dictation runtime config UI (`WFS-CFG-004`)

- **Project:** holdspeak
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-4-03 (existing pattern of dictation-side panels established)
- **Unblocks:** opting the dictation pipeline in / configuring backend without editing `~/.config/holdspeak/config.json`
- **Owner:** unassigned

## Problem

Today, enabling DIR-01 means editing
`~/.config/holdspeak/config.json` to set `dictation.pipeline.enabled
= true` and possibly `dictation.runtime.backend`,
`dictation.runtime.warm_on_start`, etc. The existing `/api/settings`
PUT covers a slice of `meeting.*` config but not `dictation.*`.

This story extends the settings API + UI to cover all dictation
fields a user might want to flip in dogfood, surfaces the live
`runtime_counters` snapshot inline, and visualises the cold-start
cap (`max_total_latency_ms × 5`) so the trap from HS-3-05 is
visible from the UI.

## Scope

- **In:**
  - Extend `/api/settings` GET to include `dictation.pipeline.enabled`, `dictation.pipeline.max_total_latency_ms`, `dictation.runtime.backend`, `dictation.runtime.mlx_model`, `dictation.runtime.llama_cpp_model_path`, `dictation.runtime.warm_on_start`, plus `_runtime_status: {counters: {...}, session: {llm_disabled_for_session: bool, disabled_reason: str | None}}` derived from `runtime_counters.get_counters()` + `get_session_status()`.
  - Extend `/api/settings` PUT to accept the same fields (validation: backend ∈ `{auto, mlx, llama_cpp}`; max_total_latency_ms > 0; paths exist or warning).
  - Web UI panel "Dictation pipeline" with: enabled toggle, backend dropdown (auto/mlx/llama_cpp), model-path inputs (one shown based on backend), warm_on_start toggle, max_total_latency_ms slider 100–5000 with a visible "× 5 = <N>ms cold-start cap" indicator, live counter snapshot panel (`model_loads`, `classify_calls`, `classify_failures`, `constrained_retries`), session-disabled banner when `llm_disabled_for_session=True` with the cap-breach reason.
  - On save, controller's `apply_runtime_config()` is invoked so the next utterance picks up the new settings (already wired today; verify by test).
  - Integration tests covering GET (counters appear), PUT (each field round-trips), validation (bad backend rejected), apply-runtime-config invalidation.
- **Out:**
  - LLM model download UI — the README documents `huggingface-cli` flow; baking that into the UI is out.
  - GPU/Metal-rebuild detection UI — DIR-DOC-001 doctor check covers this; surfacing in the UI is a polish story.
  - n_ctx / n_threads / n_gpu_layers (the lower-level runtime knobs from `DictationRuntimeConfig`). The four named above cover the 90% case; advanced knobs stay YAML for now.

## Acceptance criteria

- [x] `/api/settings` GET includes the dictation block + `_runtime_status`; existing meeting-side fields unchanged (verified by `test_get_returns_dictation_block`, `test_get_includes_runtime_status`, and pre-existing `test_settings_get_and_put_apply_runtime_callback`).
- [x] `/api/settings` PUT accepts the dictation fields, validates, persists atomically, and fires `on_settings_applied` (which calls `apply_runtime_config()` in the controller path). `test_put_persists_pipeline_and_runtime_fields` asserts both round-trip + callback fire.
- [x] UI panel shipped on `/dictation` "Runtime" section: enabled toggle, backend dropdown, model paths, warm_on_start toggle, latency slider with `× 5 = <N> ms` indicator, counter snapshot, session-disabled banner.
- [x] Session-disabled banner asserted by `test_get_surfaces_session_disabled_state` (sets `_SESSION_DISABLED` and reads back via the API).
- [x] 11 new integration tests in `tests/integration/test_web_dictation_settings_api.py`.
- [x] Full regression: 1063 passed, +11 vs. HS-4-03 baseline 1052.

## Test plan

- **Integration:** `tests/integration/test_web_dictation_settings_api.py`.
- **Regression:** documented full-suite command (metal excluded).

## Notes / open questions

- `_runtime_status` is read-only on the GET (clients shouldn't try to PUT it back). Document this in the API.
- Counter snapshot is process-scoped — restarting `holdspeak` resets to zero. Don't show it as historical; show as "since runtime start".
- The cap × 5 visualization is a small UX detail but lands the "what does this slider actually do" beat that HS-3-05's evidence flagged.
