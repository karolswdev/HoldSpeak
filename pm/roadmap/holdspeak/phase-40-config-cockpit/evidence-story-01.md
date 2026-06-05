# Evidence — HS-40-01 — Settings API: the missing knobs

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-40/hs-40-01-settings-api-knobs`
- **Owner:** unassigned

## What the codebase actually did (re-verified before editing)

The brief predicted the four Phase-39 knobs (`rewrite_passes`,
`corrections_enabled`, `target_detect_llm_enabled`, `target_detect_llm_below`)
were **silently dropped** by `PUT /api/settings` via `_coerce`. **That was
stale — the codebase wins.** `api_update_settings` builds `merged =
deepcopy(current.to_dict())` then `_merge_dict(merged, payload)`, so
`pipeline_data` already carries every pipeline field; the four knobs flow
through `DictationPipelineConfig(**pipeline_data)` unchanged, and the
dataclass's `__post_init__` is the single source of truth for the 1–5 / 0–1
bounds (`DictationConfigError` → caught → 400). `_coerce` is only on the
`load()` path, not PUT. An ad-hoc probe confirmed: the knobs **already**
round-tripped and out-of-range **already** 400'd — *before* this story.

The genuine gaps were therefore (a) a **confusing error** for a non-numeric
payload (`rewrite_passes: "three"` → `"'<=' not supported between instances of
'int' and 'str'"`) and (b) **zero test coverage** asserting the contract.

## Files touched

- `holdspeak/web/routes/system.py` — in `api_update_settings`, added an
  explicit coercion block for the four knobs after the `target_profile_override`
  block, mirroring the existing `max_total_latency_ms` pattern: `int(...)` for
  `rewrite_passes` and `float(...)` for `target_detect_llm_below` (each in a
  `try/except` → clean `"must be an integer"` / `"must be a number"` 400),
  `bool(...)` for the two flags. Defaults read from `current.dictation.pipeline.*`
  so an **omitted** knob is preserved, never reset. The 1–5 / 0–1 range bounds
  stay enforced by `DictationPipelineConfig.__post_init__` (one source of truth).
- `tests/integration/test_web_dictation_settings_api.py` — new
  `TestSettingsPipelineDepthKnobs` (12 tests): GET includes all four with
  defaults; full PUT→GET→reload round-trip; partial PUT preserves the unsent
  three; out-of-range `rewrite_passes` (0/6/99) and `target_detect_llm_below`
  (-0.1/1.5/2.0) → 400; non-numeric → clean-message 400; a rejected PUT does
  not mutate the on-disk value.

## Verification artifacts

> NB: `uv run` is broken on this machine (`platform.mac_ver()` empty); tests
> were run via `.venv/bin/python -m pytest` — same interpreter, same result.

- Targeted: `.venv/bin/python -m pytest -q tests/integration/test_web_dictation_settings_api.py`
  → `26 passed` (was 14; +12).
- Ruff (touched files) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2198 passed, 16 skipped` (was 2186/16 at Phase-39 close; +12).

## Acceptance criteria — re-checked

- [x] `GET /api/settings` includes `dictation.pipeline.rewrite_passes` /
      `corrections_enabled` / `target_detect_llm_enabled` /
      `target_detect_llm_below` with their current values —
      `test_get_includes_all_four_knobs`.
- [x] `PUT /api/settings` persists each knob; a follow-up `GET` returns the new
      value (round-trip) — `test_put_round_trips_all_four_knobs` (also reloads
      from disk).
- [x] Out-of-range `rewrite_passes` (0 or 6) and `target_detect_llm_below`
      (>1.0) are rejected 4xx, not clamped — `test_rewrite_passes_out_of_range_400`,
      `test_target_detect_below_out_of_range_400`, `test_out_of_range_put_does_not_persist`.
- [x] Omitting the knobs from a PUT leaves them at their current values —
      `test_partial_put_preserves_unsent_knobs`.
- [x] The test file covers round-trip + rejection — `TestSettingsPipelineDepthKnobs`.

## Deviations from plan

- The plan framed this as *adding* the knobs to the PUT validation. In fact the
  knobs already persisted + validated via the merge + dataclass construction;
  the substantive deliverables became (1) clean type-error messages (no raw
  `TypeError` leak) and (2) the missing test coverage. No re-implementation of
  the bounds — `__post_init__` stays the single source of truth, as the story's
  Notes recommended.
