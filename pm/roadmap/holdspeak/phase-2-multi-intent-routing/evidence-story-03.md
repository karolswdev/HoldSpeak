# Evidence — HS-2-03 (Windowing + multi-label scoring)

**Story:** [story-03-windowing.md](./story-03-windowing.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/scoring.py` (new) — `score_window`,
  `score_windows`, `iter_intent_transitions`. Built on existing
  `extract_intent_signals` + `select_active_intents` (no duplication
  of lexical or hysteresis logic).
- `holdspeak/plugins/__init__.py` — re-exports the three new helpers.
- `tests/unit/test_intent_scoring.py` (new) — 8 cases.

## Test output

### New unit tests (this story)

```
$ uv run pytest tests/unit/test_intent_scoring.py -q
........                                                                 [100%]
8 passed in 0.05s
```

### Adjacent intent suite (regression on shared infra)

```
$ uv run pytest tests/unit/test_intent_scoring.py tests/unit/test_intent_router.py \
                tests/unit/test_intent_timeline.py tests/unit/test_intent_signals.py \
                tests/unit/test_intent_contracts.py -q
.............................                                            [100%]
29 passed in 0.06s
```

The eight new cases:

1. `test_score_window_returns_typed_intent_score_with_window_id` — typed wrapper, supported-intents key set, architecture > delivery on architecture-heavy text.
2. `test_score_window_supports_multi_label_above_threshold_mir_f_002` — both `architecture` and `incident` above a permissive 0.4 gate (MIR-F-002, MIR-F-004).
3. `test_score_window_tag_boost_promotes_intent` — `tags=["incident"]` ≥ no-tag baseline.
4. `test_score_windows_preserves_input_order` — output `window_id`s in document order.
5. `test_iter_intent_transitions_emits_typed_events_on_change` — typed `IntentTransition`s with correct `added`/`removed`/`previous_active`/`current_active` across a 3-window arc.
6. `test_iter_intent_transitions_hysteresis_suppresses_oscillation_mir_f_005` — score dipping into `[threshold-hysteresis, threshold)` produces *no* transition (MIR-F-005).
7. `test_iter_intent_transitions_empty_input_returns_empty` — degenerate input safe.
8. `test_score_windows_works_end_to_end_with_build_intent_windows` — smoke wiring scoring on top of the actual `build_intent_windows` output.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
907 passed, 12 skipped in 16.29s
```

Pass delta vs. HS-2-02 baseline (899 passed): **+8** (the new
`test_intent_scoring.py` cases). Skip count unchanged at 12. Metal
excluded per the standing project memory
(`feedback_pytest_metal_exclusion.md`).

## Acceptance criteria — re-checked

All checked in [story-03-windowing.md](./story-03-windowing.md).

## Deviations from plan

- Spec §9.3 listed four targets (window builder, signal extractor,
  normalization/threshold, hysteresis/transitions). All four already
  existed as dict-shaped APIs from prior MIR-01 infra. This story
  added the typed-output bridge HS-2-02 predicted, rather than
  re-implementing primitives; the dict APIs remain in place for
  back-compat with live meeting-runtime callers.

## Follow-ups

- HS-2-04 — `PluginHost` should consume `score_windows(...)` output
  and dispatch chains per `IntentScore.labels_above_threshold()`,
  emitting typed `PluginRun` records.
- Future phase (post-MIR-01) — replace the lexical
  `extract_intent_signals` with the LLM-backed scorer; `score_window`
  is the swap point (its `IntentScore` output stays the same).

## Files in this commit

- `holdspeak/plugins/scoring.py` (new)
- `holdspeak/plugins/__init__.py` (re-exports)
- `tests/unit/test_intent_scoring.py` (new)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-03-windowing.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-03.md` (this file)
- `pm/roadmap/holdspeak/README.md` ("Last updated" line)
