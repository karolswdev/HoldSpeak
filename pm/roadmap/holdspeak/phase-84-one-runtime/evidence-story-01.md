# Evidence — HS-84-01 — Meeting intelligence runs on a profile

- **Shipped:** 2026-07-07
- **Commit:** branch `hs-84-01-meeting-intel-on-a-profile` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `holdspeak/config.py` — `MeetingConfig.intel_profile_id: Optional[str] = None`
  beside the `intel_cloud_*` block; `_coerce` makes it config-version-safe for
  older files.
- `holdspeak/intel/providers.py` — the seam: `EffectiveIntelCloud` (frozen
  dataclass), `_lookup_profile_record` (best-effort DB lookup),
  `effective_intel_cloud(meeting_cfg, get_profile=None)` with the pinned
  resolution order (valid `openAICompatible` profile → legacy `intel_cloud_*`
  shape, named `reason` on every fallback, key env =
  `HOLDSPEAK_PROFILE_<ID>_KEY` when set else the legacy env);
  `build_configured_meeting_intel` and `resolve_llm_capability` now read it.
- `holdspeak/runtime/meeting_glue.py` — the live `MeetingSession` receives the
  effective triple; a profile fallback logs its reason at start.
- `holdspeak/web/routes/meetings/intel.py` — the deferred-queue drain runs on
  the effective triple.
- `holdspeak/commands/intel.py` — the CLI runs on the effective triple and
  prints the fallback reason when there is one.
- `holdspeak/web/routes/system/settings.py` — `intel_profile_id` normalized on
  save (strip; empty ⇒ `None`); a dangling id never blocks saving.
- `tests/unit/test_intel_profile_resolution.py` — new, 14 tests.

## Verification artifacts

- `uv run pytest -q tests/unit/test_intel_profile_resolution.py` →
  **14 passed in 0.66s**.
- Neighboring suites (`test_intel_cloud.py`, `test_intel_package.py`,
  `test_plugin_host_llm_capability.py`, `test_config.py`,
  `test_dictation_preview.py`, `test_doctor_command.py`,
  `test_setup_status_doctor_drift.py`) → **136 passed in 1.07s**, unmodified.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **3226 passed, 37 skipped, 2 warnings in 253.20s** (skips are the standing
  environment-gated fixtures: mock meeting WAV, local GGUF/MLX models).

## Acceptance criteria — re-checked

- [x] `intel_profile_id` unset ⇒ byte-identical construction — proven by
  `test_unset_profile_is_the_legacy_shape_verbatim`,
  `test_build_configured_unset_is_byte_identical`, and
  `test_cfg_without_the_field_at_all_is_legacy` (a config object without the
  field at all resolves legacy too).
- [x] Valid `openAICompatible` profile ⇒ its base_url/model, per-profile key
  env preferred with legacy fallback —
  `test_valid_endpoint_profile_shapes_the_cloud_leg`,
  `test_profile_key_env_wins_when_set`,
  `test_profile_without_model_keeps_the_legacy_model`.
- [x] Dangling / deleted / `onDevice`-kind / lookup-failure ⇒ legacy fallback
  with a machine-readable reason, never a crash —
  `test_dangling_profile_falls_back_with_a_named_reason`,
  `test_deleted_profile_counts_as_missing`,
  `test_ondevice_profile_runs_on_the_hub_engine`,
  `test_lookup_failure_degrades_never_raises`.
- [x] The resolution-order matrix is test-pinned in one place —
  `tests/unit/test_intel_profile_resolution.py` (the matrix section), plus
  `test_llm_capability_judges_the_effective_endpoint` for the capability probe.
- [x] No existing intel test needed modification — the neighboring-suite run
  above passed verbatim.

## Deviations from plan

The story's In-list named only `build_configured_meeting_intel`; implementation
found the identical config→cloud-triple derivation in three more consumer
sites (live session construction, deferred-queue drain route, CLI). All four
adopted the seam in this story — shipping one would have split meeting intel
across two worlds. Recorded in the story's Notes. Settings round-trip grew a
route-level test (clear-to-`None` included) beyond the sparse plan. Doctor and
status *wording* deliberately untouched (HS-84-04 owns it), though the story's
plan already said so.

## Follow-ups

- HS-84-04 consumes `EffectiveIntelCloud.reason` for the doctor/status lines —
  the reasons are already machine-readable strings.
- `setup_status.py:104` still displays the raw `intel_cloud_base_url` for the
  meeting-intel row; HS-84-04's honesty pass covers it (the dictation
  equivalent is already in HS-84-02's AC).
