# Evidence — HS-4-04: Dictation runtime config UI (`WFS-CFG-004`)

- **Phase:** 4 (Web Flagship Runtime + Configurability)
- **Story:** HS-4-04
- **Captured at HEAD:** `d85a48c` (pre-commit)
- **Date:** 2026-04-26

## What shipped

- **`holdspeak/web_server.py` GET `/api/settings`** — payload now carries a top-level `_runtime_status: {counters, session}` enrichment derived from `runtime_counters.get_counters()` + `get_session_status()`. Read-only (the PUT pops it before reconstructing `Config`).
- **`holdspeak/web_server.py` PUT `/api/settings`** — extended with a dictation-slice validation block before the `Config(...)` reconstruction. Validates `pipeline.enabled` (bool), `pipeline.max_total_latency_ms` (int > 0), `runtime.backend` ∈ `{auto, mlx, llama_cpp}`, `runtime.mlx_model` / `runtime.llama_cpp_model_path` (str), `runtime.warm_on_start` (bool). Surfaces `DictationConfigError` (e.g. unknown stage IDs) as 400. The `Config(...)` constructor now passes `dictation=DictationConfig(...)` so the previously-silent drop is fixed.
- **`holdspeak/static/dictation.html`** — added a third top-level section "Runtime" with two panels: (1) editable form (enabled toggle, backend dropdown, MLX / GGUF path inputs, `warm_on_start` toggle, latency slider 100–5000 ms with a live `× 5 = <N> ms` cap visualization, save/reset actions); (2) read-only runtime status panel showing the four counters + an OK/error session banner.
- **`tests/integration/test_web_dictation_settings_api.py`** — 11 tests: GET enrichment (3), PUT round-trip + omit-preserves + drop-echoed-runtime-status (3), validation rejection (4), page surface (1).

## Design calls made (and why)

| Call | Decision | Why |
|---|---|---|
| `_runtime_status` location | Top-level key on the GET payload (not nested under `dictation`) | Persisted config and live status are different concerns; nesting under `dictation` would invite a client to PUT it back. The PUT explicitly pops it. Documented in story stub Notes. |
| Read-only enforcement | `merged.pop("_runtime_status", None)` before validation | Cheaper than rejecting echoed payloads outright; preserves a "GET → mutate → PUT" workflow without surprises. Verified by `test_put_drops_runtime_status_if_echoed_back`. |
| Cache-invalidation wiring | Reuses the existing `on_settings_applied` callback (which controllers already wire to `apply_runtime_config()`) | The story Notes explicitly authorize "verify by test" rather than re-plumbing. The HS-4-02 `on_dictation_config_changed` callback remains for blocks/KB writes that don't go through `/api/settings`. |
| Latency slider scale | 100–5000 ms, step 50 | Covers DIR-O-001 latency-budget realism (DIR-01 §9.7 names 600 ms as the steady-state target; the cold-start cap multiplier means even a 1000 ms slider produces a 5 s cap, which is more lenient than DIR-R-003's intent). 5000 is upper-bound dogfood territory. |
| Advanced runtime knobs | Out per story stub (`n_ctx`, `n_threads`, `n_gpu_layers`, `eviction_idle_seconds`) | The 90% case is the four named fields; advanced knobs stay YAML/config.json for now. |

## Test output

### Targeted

```
$ uv run pytest tests/integration/test_web_dictation_settings_api.py -v --timeout=30
... (output snipped)
collected 11 items

tests/integration/test_web_dictation_settings_api.py::TestSettingsGetIncludesRuntimeStatus::test_get_returns_dictation_block PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsGetIncludesRuntimeStatus::test_get_includes_runtime_status PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsGetIncludesRuntimeStatus::test_get_surfaces_session_disabled_state PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutPersistsDictation::test_put_persists_pipeline_and_runtime_fields PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutPersistsDictation::test_put_omitting_dictation_preserves_existing PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutPersistsDictation::test_put_drops_runtime_status_if_echoed_back PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutValidatesDictation::test_invalid_backend_400 PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutValidatesDictation::test_zero_latency_400 PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutValidatesDictation::test_non_integer_latency_400 PASSED
tests/integration/test_web_dictation_settings_api.py::TestSettingsPutValidatesDictation::test_unknown_stage_id_400 PASSED
tests/integration/test_web_dictation_settings_api.py::test_dictation_page_includes_runtime_section PASSED

============================== 11 passed in 0.49s ==============================
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
1063 passed, 13 skipped in 18.97s
```

Pass delta vs. HS-4-03 baseline (1052 passed): **+11** (11 new tests). 13 skipped is unchanged.

## WFS-CFG-* coverage

| Requirement | How verified |
|---|---|
| WFS-CFG-004 | GET enrichment (3 tests), PUT round-trip incl. omit-preserves (3 tests), validation (4 tests), page surface (1 test). |
| `apply_runtime_config()` hook | `test_put_persists_pipeline_and_runtime_fields` asserts `on_settings_applied.assert_called_once()` after the PUT. The controller wires `on_settings_applied=self._on_web_settings_applied → self.apply_runtime_config()` (controller.py:461 + 339-350). |

## Pre-existing bug fixed in passing

The pre-HS-4-04 PUT silently dropped any `dictation.*` payload — line 1083's `Config(hotkey=..., model=..., ui=..., meeting=...)` omitted `dictation=`, so even though `Config.load` round-trips dictation correctly, the web settings PUT erased it on every save. This is now fixed by passing `dictation=dictation_cfg`. Documented here so it isn't a "where did that bug come from" surprise in the diff.

## Out-of-scope (deferred per story / phase shape)

- LLM model download UI — README documents `huggingface-cli`; baking that into the web UI is out.
- GPU/Metal-rebuild detection UI — DIR-DOC-001 doctor check covers this; surfacing in the UI is a polish story.
- `n_ctx` / `n_threads` / `n_gpu_layers` / `eviction_idle_seconds` — the 90% case is covered by the four named fields.
- Wiring `on_settings_applied` from `web_runtime.py`'s `_apply_updated_config` to invalidate a (non-existent) dictation pipeline — web-only path doesn't run dictation.
