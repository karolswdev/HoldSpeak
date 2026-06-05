# HS-40-01 — Settings API: the missing knobs

- **Project:** holdspeak
- **Phase:** 40
- **Status:** done (2026-06-05)
- **Depends on:** none
- **Unblocks:** HS-40-03
- **Owner:** unassigned
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## Problem

The four Phase-39 pipeline knobs (`rewrite_passes`, `corrections_enabled`,
`target_detect_llm_enabled`, `target_detect_llm_below`) exist on
`DictationPipelineConfig` but **cannot be set through the web settings API** —
`PUT /api/settings` validates/coerces a fixed set of pipeline fields and omits
these four, so `_coerce` silently drops them on save. The cockpit UI (HS-40-03)
can't wire controls to fields the API won't persist. This story is the backend
foundation.

## Scope

- In:
  - In `holdspeak/web/routes/system.py` `api_update_settings` (PUT), add
    validation + coercion for the four knobs, mirroring the existing pipeline
    field handling (e.g. the `max_total_latency_ms` block):
    - `rewrite_passes` — int, `1 <= n <= 5` (matches `DictationPipelineConfig`).
    - `corrections_enabled` — bool.
    - `target_detect_llm_enabled` — bool.
    - `target_detect_llm_below` — float, `0.0 <= x <= 1.0`.
  - Confirm `GET /api/settings` returns them (they're dataclass fields, so
    `Config.to_dict()` already includes them — assert it).
  - Reject out-of-range values with a clear 4xx (don't silently clamp).
- Out:
  - Any UI control (HS-40-03).
  - New knobs / behavior changes — this only exposes existing fields.

## Acceptance criteria

- [x] `GET /api/settings` includes `dictation.pipeline.rewrite_passes` /
      `corrections_enabled` / `target_detect_llm_enabled` /
      `target_detect_llm_below` with their current values.
- [x] `PUT /api/settings` persists each knob; a follow-up `GET` returns the new
      value (round-trip).
- [x] Out-of-range `rewrite_passes` (0 or 6) and `target_detect_llm_below`
      (>1.0) are rejected with a 4xx, not clamped or dropped.
- [x] Default behavior unchanged: omitting the knobs from a PUT leaves them at
      their current values (no accidental reset).
- [x] `tests/integration/test_web_dictation_settings_api.py` covers the
      round-trip + the rejection cases.

## Outcome

The four knobs **already** round-tripped + 4xx'd (the PUT merges the full
current dict, then constructs `DictationPipelineConfig(**pipeline_data)` whose
`__post_init__` enforces the bounds) — the brief's "`_coerce` drops them" was
stale. Real gaps closed: a **clean type-error** for non-numeric payloads
(explicit `int()`/`float()` coercion mirroring `max_total_latency_ms`) and the
**missing test coverage** (`TestSettingsPipelineDepthKnobs`, 12 tests). Suite
2198/16. See [evidence-story-01.md](./evidence-story-01.md).

## Test plan

- Integration: `uv run pytest -q tests/integration/test_web_dictation_settings_api.py`.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- The validation should reuse `DictationPipelineConfig.__post_init__`'s ranges
  (1–5 for passes, 0–1 for the threshold) — consider constructing a
  `DictationPipelineConfig` and catching `DictationConfigError` rather than
  re-implementing the bounds, to keep one source of truth.
- Check whether the PUT merges partial pipeline payloads or replaces the whole
  pipeline block — the round-trip test must confirm un-sent fields are preserved.
