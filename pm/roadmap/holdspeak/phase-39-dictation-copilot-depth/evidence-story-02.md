# Evidence — HS-39-02 — Correction memory (session learning)

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `holdspeak/plugins/dictation/corrections.py` (**new**) — `Correction`,
  `CorrectionStore` (bounded ring, `threading.Lock`, gist-only +
  secret-rejected), `similarity` (Jaccard), `best_match_in` (newest-first,
  recency tie-break).
- `holdspeak/project_doc_suggestions.py` — public `looks_like_secret` wrapper.
- `holdspeak/config.py` — `corrections_enabled: bool = False` on
  `DictationPipelineConfig`.
- `holdspeak/plugins/dictation/builtin/intent_router.py` — `corrections` ctor
  param + `_apply_correction_nudge` (reinforce/redirect to a known block;
  `correction_nudge` metadata).
- `holdspeak/target_profile.py` — `apply_target_correction` (override always
  wins; redirect only to a user-selectable, different profile).
- `holdspeak/plugins/dictation/assembly.py` — `build_pipeline(corrections=…)`,
  passed to `IntentRouter` only when `corrections_enabled` + non-empty.
- `holdspeak/web/context.py` — `WebContext.corrections`.
- `holdspeak/web_server.py` — `MeetingWebServer.dictation_corrections` +
  passed into the `WebContext`.
- `holdspeak/web/routes/dictation/pipeline.py` — `GET/POST
  /api/dictation/corrections`; dry-run passes `corrections=ctx.corrections`.
- `holdspeak/web/routes/dictation/_helpers.py` — dry-run snapshots corrections
  (gated), feeds `build_pipeline` + `apply_target_correction`.
- `holdspeak/web_runtime.py` — live `_maybe_run_dictation_pipeline` consumes
  `self.server.dictation_corrections` (gated) for routing + target.
- Tests: `tests/unit/test_dictation_correction_store.py` (**new**, 9),
  `tests/integration/test_web_dictation_corrections_api.py` (**new**, 5),
  + nudge cases in `test_dictation_intent_router.py` (5) /
  `test_target_profile.py` (4) / `test_config.py` (2); route-table invariant
  `test_dictation_routes_split.py` updated 26 → 28.

## Verification artifacts

- New + affected units:
  `uv run pytest -q tests/unit/test_dictation_correction_store.py tests/unit/test_dictation_intent_router.py tests/unit/test_target_profile.py tests/unit/test_config.py::TestDictationPipelineValidation tests/integration/test_web_dictation_corrections_api.py`
  → `55 passed`.
- Ruff (all touched files) → `All checks passed!`.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2157 passed, 15 skipped in 58.56s` (was 2132/15 at HS-39-01; +25).

## Acceptance criteria — re-checked

- [x] Bounded, thread-safe `CorrectionStore`, one per session (on the server,
      shared with the runtime) — `test_dictation_correction_store.py` incl.
      `test_thread_safe_concurrent_records` (800 records, no loss).
- [x] Record via the web surface + retrieve; cap evicts oldest —
      `test_web_dictation_corrections_api.py`, `test_ring_evicts_oldest_past_cap`.
- [x] Flag-off (default) or empty store ⇒ byte-identical routing + target —
      `test_no_corrections_is_byte_identical`,
      `test_target_correction_noop_without_corrections`.
- [x] Intent correction nudges a later similar utterance (fake runtime) —
      `test_correction_nudge_redirects_to_corrected_block` (+ reinforce case).
- [x] Target correction biases detection; manual override wins —
      `test_target_correction_redirects_for_similar_context`,
      `test_target_correction_never_overrides_manual_override`.
- [x] Gist-only + secret rejection — `test_record_rejects_secret_like_gist`,
      `test_record_silently_drops_secret`.
- [x] No DB schema change; in-process only.

## Deviations from plan

- Store lives on `MeetingWebServer` (shared with `WebRuntime` via
  `self.server`), not literally on `WebRuntime`. Nudge is a deterministic
  post-classification step (prompt unchanged), not a prompt hint. Target
  corrections key on the utterance gist. All recorded in the story's
  "Deviations" + the phase "Decisions made".

## Follow-ups

- HS-39-05 (telemetry) will surface correction-store state (size / recent
  gists / enabled) on `/api/dictation/readiness`.
- Whether corrections should ever persist across sessions stays deferred to the
  HS-39-07 dogfood (default: in-process only).
- A web UI affordance to *record* a correction from the dry-run / live surface
  is a natural HS-39-06-era polish; the API + store are ready.
