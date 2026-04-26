# HS-2-03 — Step 2: Windowing + multi-label scoring

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-02 (typed contracts)
- **Unblocks:** HS-2-04 (plugin host iterates `score_windows` output to dispatch chains), HS-2-06 (meeting runtime wiring), HS-2-07 (synthesis can carry transitions for narrative)
- **Owner:** unassigned

## Problem

Spec §9.3 calls for: rolling window builder, deterministic lexical
signal extractor, score normalization + threshold, hysteresis +
transition detection. Audit (post-HS-2-02): all four primitives
already exist as **dict-shaped** APIs from prior MIR-01 infra
(`build_intent_windows`, `extract_intent_signals`,
`normalize_intent_scores` / `select_active_intents`,
`detect_intent_transitions`). The actual gap is the typed-output
bridge HS-2-02's notes predicted: emitting `IntentScore` per window
and `IntentTransition` over a window sequence so HS-2-04+ have typed
values to consume.

## Scope

- **In:**
  - New module `holdspeak/plugins/scoring.py` with `score_window(window, *, threshold) -> IntentScore`, `score_windows(windows, *, threshold) -> list[IntentScore]`, and `iter_intent_transitions(scored_windows, *, hysteresis) -> list[IntentTransition]`. All built on the existing `extract_intent_signals` + `select_active_intents` (no duplication of lexical or hysteresis logic).
  - Re-exports from `holdspeak/plugins/__init__.py`.
  - Unit tests at `tests/unit/test_intent_scoring.py`: 8 cases covering MIR-F-001 (rolling windows pass through), MIR-F-002 (multi-label per window), MIR-F-004 (multiple intents above threshold), MIR-F-005 (hysteresis suppresses oscillation), tag-boost, ordering, empty input, and end-to-end with `build_intent_windows`.
- **Out:**
  - Replacing the dict-shaped APIs (`extract_intent_signals` returns `dict[str, float]`, `detect_intent_transitions` returns `list[dict]`) — they remain for the existing meeting-runtime callers; the typed surface is additive.
  - Plugin chain dispatch (HS-2-04).
  - Persistence schema for `IntentScore` rows (HS-2-05).

## Acceptance criteria

- [x] `score_window(IntentWindow, threshold=...)` returns an `IntentScore` whose `window_id` matches the input window and whose `scores` keys equal `SUPPORTED_INTENTS`.
- [x] `score_window` honors the `tags` field on `IntentWindow` (tag-boost path through `extract_intent_signals`).
- [x] `score_windows` preserves input order.
- [x] `iter_intent_transitions` emits `IntentTransition` events with correct `added` / `removed` sets at every dominant-set change; emits nothing on stable windows.
- [x] Hysteresis suppresses transitions when a previously-active intent dips into the band `[threshold - hysteresis, threshold)` (MIR-F-005).
- [x] `tests/unit/test_intent_scoring.py` ships with 8 cases, all pass.
- [x] Spec §9.3 verification gate green: `uv run pytest -q tests/unit/test_intent_router.py -k "window or label or hysteresis"` (covered by `test_select_active_intents_uses_threshold_and_hysteresis` + the new typed tests).
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 907 passed, 12 skipped, 0 failed in 16.29s. Pass delta vs. HS-2-02 (899): +8.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_intent_scoring.py -q` (8 cases).
- **Adjacent:** `uv run pytest tests/unit/test_intent_router.py tests/unit/test_intent_signals.py tests/unit/test_intent_timeline.py tests/unit/test_intent_contracts.py -q` — pre-existing 21 cases must remain green.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`. Metal excluded per the standing project memory.

## Notes / open questions

- Deliberate non-replacement: the dict-shaped `extract_intent_signals` and `detect_intent_transitions` are still used by live meeting-runtime callers (and the existing `preview_route` / `preview_route_from_transcript` surface). Replacing them in this story would be scope creep; the typed surface is what HS-2-04+ will consume going forward.
- `score_window` re-runs `normalize_intent_scores` on the lexical output even though the extractor already returns clamped values — this is belt-and-suspenders for the cases where callers pass raw scores from a future LLM scorer (placeholder for the MIR-01 LLM-backed path that will replace the lexical signal extractor in a later phase).
