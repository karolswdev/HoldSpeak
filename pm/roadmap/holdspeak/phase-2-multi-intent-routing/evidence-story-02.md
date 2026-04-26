# Evidence — HS-2-02 (Contracts + router skeleton)

**Story:** [story-02-contracts-router.md](./story-02-contracts-router.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/contracts.py` — added `IntentScore`,
  `IntentTransition`, `PluginRun`, `ArtifactLineage` (all
  `@dataclass(frozen=True)`) plus the `PLUGIN_RUN_STATUSES` frozenset.
  `PluginRun.__post_init__` rejects unknown statuses with a
  `ValueError` naming the offender + the canonical set.
- `holdspeak/plugins/__init__.py` — re-exports the four new types
  + `PLUGIN_RUN_STATUSES` so external callers can `from
  holdspeak.plugins import PluginRun`.
- `tests/unit/test_intent_contracts.py` (new) — 7 cases covering
  construction, immutability (`FrozenInstanceError`), status
  validation, score-ordering invariants, dict round-trip, and
  re-export sanity.

## Why router/timeline files weren't touched

Spec §9.2 names router skeleton (`holdspeak/plugins/router.py`) and
timeline (`holdspeak/intent_timeline.py`) as targets. Both already
exist from prior MIR-01 infrastructure with substantial implementation
(deterministic preview routing, profile chains, hysteresis, counters,
window builder, transition detector). The actual gap versus spec §5.1
was the four typed entities — that's what this story fills. The
existing files needed no changes for this step; HS-2-03 will extend
`detect_intent_transitions` to emit typed `IntentTransition`s without
removing the dict-shaped surface (back-compat for live meeting-runtime
callers).

## Test output

### New unit tests (this story)

```
$ uv run pytest tests/unit/test_intent_contracts.py -q
.......                                                                  [100%]
7 passed in 0.04s
```

### Spec §9.2 verification gate

```
$ uv run pytest -q tests/unit/test_intent_timeline.py tests/unit/test_intent_router.py
..........                                                               [100%]
10 passed in 0.04s
```

### Combined (new + spec gate)

```
$ uv run pytest tests/unit/test_intent_contracts.py tests/unit/test_intent_router.py tests/unit/test_intent_timeline.py -q
.................                                                        [100%]
17 passed in 0.04s
```

The seven new cases:

1. `test_intent_score_labels_above_threshold_orders_by_score_then_label` — descending-score then alphabetical ordering, ties handled deterministically.
2. `test_intent_score_is_frozen` — `FrozenInstanceError` on field mutation.
3. `test_intent_transition_round_trips_to_dict` — typed → dict preserves all fields.
4. `test_plugin_run_accepts_known_statuses` — `success` status passes `__post_init__`; `to_dict` round-trip preserves `duration_ms`.
5. `test_plugin_run_rejects_unknown_status` — `ValueError` with `"status='bogus'"` substring.
6. `test_artifact_lineage_preserves_window_and_plugin_run_links` — `window_ids` + `plugin_run_keys` round-trip cleanly.
7. `test_contracts_re_exported_from_plugins_package` — `from holdspeak.plugins import …` resolves to the same object as `from holdspeak.plugins.contracts import …`.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
899 passed, 12 skipped in 15.26s
```

`tests/e2e/test_metal.py` is excluded because it contains the
documented hardware-only baseline (`TestWhisperTranscription::test_model_loads`,
carried since HS-1-03) and a sibling `test_record_and_transcribe_live`
that hangs without an interactive mic device — the first pass at this
sweep blocked indefinitely on it (4+ minutes of zero CPU progress)
and had to be killed. The exclusion matches the carried-baseline
posture documented in the HS-1-11 phase summary; non-hardware coverage
is unchanged. Pass delta vs. the post-DIR-01 baseline: **+7** (the
new `test_intent_contracts.py` cases). Skip count unchanged at 12.

## Acceptance criteria — re-checked

All checked in [story-02-contracts-router.md](./story-02-contracts-router.md).

## Deviations from plan

- Spec §9.2 listed `holdspeak/intent_timeline.py` and
  `holdspeak/plugins/router.py` as edit targets. They were not touched
  in this commit — both already met the Step-1 surface from prior
  infra, and editing them speculatively would be scope creep. HS-2-03
  picks up the typed-`IntentTransition` integration as part of its
  windowing work.
- `tests/unit/test_intent_router.py` and `tests/unit/test_intent_timeline.py`
  also untouched (the pre-existing 10 cases already cover the Step-1
  router-skeleton surface).

## Follow-ups

- HS-2-03 — `detect_intent_transitions` should grow a typed sibling
  returning `list[IntentTransition]`; multi-label scorer should emit
  `IntentScore` per window.
- HS-2-04 — `PluginHost` should populate `PluginRun` records (likely
  via an adapter from `PluginRunResult` + the active window/profile).
- HS-2-05 — DB schema for `PluginRun` + `ArtifactLineage` rows;
  re-evaluate whether `PluginRunSummary` collapses into the `PluginRun`
  contract type or stays as a query-projection.

## Files in this commit

- `holdspeak/plugins/contracts.py` (extended)
- `holdspeak/plugins/__init__.py` (re-exports)
- `tests/unit/test_intent_contracts.py` (new)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-02-contracts-router.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table, "Where we are", "Decisions made", "Last updated")
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-02.md` (this file)
- `pm/roadmap/holdspeak/README.md` ("Last updated" line)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-01-baseline.md` (deleted — HS-2-01 dropped)
