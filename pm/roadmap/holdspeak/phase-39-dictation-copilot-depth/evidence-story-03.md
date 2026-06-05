# Evidence — HS-39-03 — Model-assisted target detection

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `holdspeak/config.py` — `target_detect_llm_enabled: bool = False` +
  `target_detect_llm_below: float = 0.8` on `DictationPipelineConfig`;
  `__post_init__` validates the threshold is in `[0.0, 1.0]`.
- `holdspeak/target_profile.py` — `apply_model_assisted_target` (the gated
  fallback) + `_build_model_target_prompt` + `_parse_target_choice` +
  `_MODEL_TARGET_PROFILES`.
- `holdspeak/plugins/dictation/assembly.py` — `BuildResult.runtime` exposes the
  loaded runtime (None when unavailable).
- `holdspeak/web/routes/dictation/_helpers.py` — dry-run applies the
  model-assisted step after the correction step, gated on the config flag.
- `holdspeak/web_runtime.py` — live `_maybe_run_dictation_pipeline` collects
  hints once, then detect → correction → model-assisted (runtime via
  `getattr(result, "runtime", None)`).
- Tests: 8 cases in `tests/unit/test_target_profile.py` + 2 in
  `tests/unit/test_config.py`.

## Verification artifacts

- Targeted: `uv run pytest -q tests/unit/test_target_profile.py tests/unit/test_config.py::TestDictationPipelineValidation tests/unit/test_dictation_assembly.py`
  → `36 passed`.
- Ruff (touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2167 passed, 15 skipped` (was 2157/15 at HS-39-02; +10). One pre-existing
  web-runtime test (`test_device_voice_reply_uses_waiting_agent_target_profile`)
  used a `FakeBuildResult` without the new `runtime` attr; fixed by reading the
  runtime via `getattr(result, "runtime", None)` in the live path.

## Acceptance criteria — re-checked

- [x] Config flags exist + validate — `test_target_detect_llm_defaults`,
      `test_target_detect_llm_below_out_of_range_rejected`.
- [x] Flag-off ⇒ byte-identical (same object) — `test_model_assisted_disabled_is_noop`.
- [x] Below threshold ⇒ LLM consulted, enum result used —
      `test_model_assisted_fires_below_threshold`.
- [x] At/above threshold ⇒ LLM not called — `test_model_assisted_skips_at_or_above_threshold`.
- [x] Override + correction outrank the LLM —
      `test_model_assisted_override_always_wins`, `test_model_assisted_skips_user_correction`.
- [x] Failure / no-runtime / invalid ⇒ degrade to heuristic, never raise —
      `test_model_assisted_degrades_on_runtime_error`,
      `test_model_assisted_no_runtime_is_noop`,
      `test_model_assisted_ignores_unparseable_choice`.
- [x] Decision source + confidence on `TargetProfile.to_dict()`; dry-run returns
      it as `target` (now possibly source `llm`).

## Deviations from plan

- Enum constraint is enforced at **parse** (`_parse_target_choice`), not at
  decode — the runtime's constrained `classify` is block-shaped, so the
  fallback uses the freeform `rewrite` seam and validates the answer, degrading
  on anything invalid. Decode-time enum constraint is a possible later refinement.
- Order is detect → correction → model-assisted, so a user correction is never
  overridden by the model. Recorded in the story Notes.

## Reality check — NOT yet run against a real endpoint

Every test in this story (and HS-39-01/02) uses **injected fake runtimes**. The
model-assisted fallback has **not** been exercised against the real `.43`
OpenAI-compatible endpoint (Qwen3.5-9B-Q6). That real dogfood — multi-pass +
corrections + model-assisted detection end-to-end through `.43` — is the
**HS-39-07 closeout** deliverable. Nothing here proves real-endpoint behavior;
it proves the contract + graceful degradation.

## Follow-ups

- HS-39-05 telemetry can surface which detector decided (`hints` / `llm` /
  `override` / `correction`) over recent runs.
- Optionally include recent agent context as a model-assisted signal in the
  live path (currently hints + text only); the function already accepts it.
