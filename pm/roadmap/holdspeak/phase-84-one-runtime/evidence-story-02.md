# Evidence — HS-84-02 — Dictation runs on a profile

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-84-02-dictation-on-a-profile` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `holdspeak/config.py` — `LLMRuntimeConfig.profile_id: Optional[str] = None`
  beside the `openai_compatible_*` block.
- `holdspeak/intel/providers.py` — the HS-84-01 adoption logic extracted as
  `_apply_runtime_profile(legacy, profile_id, get_profile)` (ONE rule); the
  shared dataclass renamed `EffectiveIntelCloud` → `EffectiveEndpoint`; two
  thin config-shape wrappers: `effective_intel_cloud` (unchanged behavior)
  and the new `effective_dictation_llm`.
- `holdspeak/plugins/dictation/assembly.py` — `_try_build_runtime` builds the
  LLM leg from the effective shape; an ADOPTED profile also selects the
  `openai_compatible` backend; every fallback keeps the configured backend.
- `holdspeak/setup_runtime.py` — `probe_runtime` probes the ADOPTED
  endpoint's `/models` (skips local-backend resolution when adopted); the
  openai_compatible branch reads the effective base URL + key env.
- `holdspeak/setup_status.py` — the trust block's `configured_endpoints`
  lists the EFFECTIVE dictation endpoint (adopted profile ⇒ its base URL).
- `holdspeak/web/routes/system/settings.py` — `dictation.runtime.profile_id`
  normalized on save (strip; empty ⇒ `None`); dangling never blocks saving.
- `tests/unit/test_dictation_profile_resolution.py` — new, 11 tests.
- `tests/unit/test_intel_profile_resolution.py` — the dataclass rename only.

## Verification artifacts

- `uv run pytest -q tests/unit/test_dictation_profile_resolution.py
  tests/unit/test_intel_profile_resolution.py` → **25 passed in 0.84s**.
- Neighbors: `uv run pytest -q tests/unit -k "dictation or setup or assembly
  or runtime"` → **437 passed, 2089 deselected in 4.97s**, unmodified.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3237 passed, 37 skipped, 2 warnings in 246.58s** (standing env-gated
  skips: local GGUF/MLX models etc.).

## Acceptance criteria — re-checked

- [x] Knob unset ⇒ assembled runtime kwargs byte-identical —
  `test_assembly_unset_is_byte_identical` (backend `mlx` stays `mlx`, the
  `openai_compatible_*` kwargs carry the config defaults verbatim).
- [x] Valid `openAICompatible` profile ⇒ the LLM leg carries its
  base_url/model, per-profile key env preferred —
  `test_valid_endpoint_profile_shapes_the_llm_leg`,
  `test_assembly_adopted_profile_selects_the_endpoint_backend` (assembly-seam
  capture, no model loaded).
- [x] Dangling id / lookup unavailable ⇒ legacy shape + named reason, never a
  crash — `test_dangling_profile_falls_back_with_a_named_reason`,
  `test_assembly_dangling_profile_keeps_the_configured_backend`,
  `test_ondevice_profile_runs_on_the_configured_backend` (+ the
  lookup-failure path is pinned by the shared-rule tests in
  `test_intel_profile_resolution.py`).
- [x] `setup_runtime.py` / `setup_status.py` report the *effective* shape —
  `test_probe_runtime_tests_the_adopted_profile_endpoint` (the probe GETs
  `http://192.168.1.43:8080/v1/models` under `backend: mlx` + an adopted
  profile) and `test_setup_status_reports_the_effective_dictation_endpoint`
  (trust block lists the profile's URL; a local backend with the knob unset
  still contributes none).
- [x] No existing dictation test needed modification — the 437-test neighbor
  run passed verbatim; the only touched test file was HS-84-01's own (the
  dataclass rename, same phase).

## Deviations from plan

One design decision beyond the sparse plan, recorded in the story Notes and
the phase status: an ADOPTED profile also selects the `openai_compatible`
backend (shape-only adoption would be dead code under a local backend);
every fallback path leaves the configured backend untouched. The HS-84-01
dataclass rename (`EffectiveEndpoint`) rides here because the shape stopped
being intel-specific — the write-once evidence-story-01 remains accurate as
a record of what shipped then.

## Follow-ups

- HS-84-03: present backend + profile as ONE "runs on" choice in the
  settings picker (the recorded decision makes the two knobs coherent).
- HS-84-04: surface `EffectiveEndpoint.reason` (both pipelines) in doctor /
  setup status wording.
