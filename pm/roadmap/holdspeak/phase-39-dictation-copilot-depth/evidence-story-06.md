# Evidence — HS-39-06 — Documentation

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `docs/INTELLIGENT_TYPING_GUIDE.md` — new **§10 "Copilot Depth"** (a knob table
  + JSON example + per-feature prose for multi-pass, correction memory,
  model-assisted target, the suggestion quality gate, and the `depth` readiness
  telemetry block); §8 reconciled to note dedup + dismissal-no-recur.

## Verification artifacts

- Doc guards: `uv run pytest -q -k "doc_drift or dangling or no_live_doc or link"`
  → `4 passed, 1 skipped`.
- Knob-name cross-check (doc ↔ code):
  - `rewrite_passes`, `corrections_enabled`, `target_detect_llm_enabled`,
    `target_detect_llm_below` — all present on `DictationPipelineConfig`
    (`holdspeak/config.py`).
  - `depth.stages` / `depth.guidance` / `depth.rewrite_pass_ms` /
    `depth.corrections` — match `build_depth_readiness`
    (`holdspeak/dictation_telemetry.py`).
  - `suggestion_status` values (`stored` / `already_covered` / `dismissed` /
    `no_suggestion`) — match `_store_project_doc_suggestion` + the rewriter.
  - `POST /api/dictation/corrections {kind, text, value}` — matches the route.
- Docs-only change: full suite unchanged from HS-39-05 (`2186 passed, 16 skipped`).

## Acceptance criteria — re-checked

- [x] Every new knob documented with default + example + opt-in posture (§10).
- [x] Stale single-pass / memoryless / heuristic-only framing reconciled.
- [x] Doc drift-guard passes.
- [x] Live-doc link-check passes.
- [x] Documented names match the shipped config fields / payload keys.

## Deviations from plan

- None. (The showcase doc `docs/DICTATION_COPILOT.md` was already added in
  HS-39-09; this story adds the comprehensive knob reference and cross-links it.)

## Follow-ups

- None for the phase. HS-39-07 closeout re-verifies the before/after and flips
  the README phase row to done.
