# HS-2-02 — Step 1: Contracts + router skeleton

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-1-11 (DIR-01 closed; phase-2 scaffold landed at `29a4b5f`)
- **Unblocks:** HS-2-03 (windowing extends `IntentScore`), HS-2-04 (plugin host emits `PluginRun`), HS-2-05 (persistence stores `PluginRun` + `ArtifactLineage`), HS-2-07 (synthesis carries `ArtifactLineage`)
- **Owner:** unassigned

## Problem

Spec §9.2 calls for typed contracts in `holdspeak/plugins/contracts.py`,
timeline entities in `holdspeak/intent_timeline.py`, and a router skeleton
in `holdspeak/plugins/router.py`. On audit, the router skeleton, the
timeline window builder, and a substantial deterministic router already
exist from prior MIR-01 infra (predates this roadmap). The actual gap
versus spec §5.1 is the four typed entities that nothing ships yet:
`IntentScore`, `IntentTransition`, `PluginRun`, `ArtifactLineage`. This
story fills exactly that gap so the later steps (HS-2-03..HS-2-07) have
typed values to pass around.

## Scope

- **In:**
  - Add `IntentScore`, `IntentTransition`, `PluginRun`, `ArtifactLineage` as `@dataclass(frozen=True)` in `holdspeak/plugins/contracts.py`, matching the field shapes implied by spec §5.1 + §6.1–§6.2.
  - `PluginRun.status` validated against the existing host-side status vocabulary (`success | error | timeout | deduped | blocked | queued`) — exposed as `PLUGIN_RUN_STATUSES` so callers don't drift.
  - Re-export the four new types + the status set from `holdspeak/plugins/__init__.py` so external callers can `from holdspeak.plugins import PluginRun`.
  - Unit tests at `tests/unit/test_intent_contracts.py` covering construction, immutability, status-validation, ordering invariants, and round-trip-to-dict.
- **Out:**
  - Refactoring or replacing the existing `PluginRunResult` (`holdspeak/plugins/host.py`) — it serves a different purpose (runtime execution-result wrapper) and is HS-2-04's territory.
  - Wiring the new contracts into `intent_timeline.detect_intent_transitions` (still returns `dict`s — HS-2-03 owns the typed conversion).
  - Persistence schema for `PluginRun`/`ArtifactLineage` (HS-2-05).
  - Synthesis logic that emits `ArtifactLineage` (HS-2-07).

## Acceptance criteria

- [x] `holdspeak/plugins/contracts.py` defines `IntentScore`, `IntentTransition`, `PluginRun`, `ArtifactLineage` as `@dataclass(frozen=True)`.
- [x] `PluginRun.__post_init__` rejects unknown statuses with a `ValueError` naming the offender + the canonical set.
- [x] `IntentScore.labels_above_threshold()` returns labels at-or-above `self.threshold`, ordered by descending score then alphabetical.
- [x] `holdspeak/plugins/__init__.py` re-exports all four types + `PLUGIN_RUN_STATUSES`.
- [x] `tests/unit/test_intent_contracts.py` ships with 7 cases, all pass: `uv run pytest tests/unit/test_intent_contracts.py tests/unit/test_intent_router.py tests/unit/test_intent_timeline.py -q` → `17 passed in 0.04s`.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q` clean modulo the documented pre-existing hardware-only Whisper-loader failure (`tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads`).

## Test plan

- **Unit:** `uv run pytest tests/unit/test_intent_contracts.py -q` (7 cases).
- **Spec verification gate (§9.2):** `uv run pytest -q tests/unit/test_intent_timeline.py tests/unit/test_intent_router.py` — must remain green.
- **Regression:** `uv run pytest tests/ --timeout=30 -q` — known baseline only.

## Notes / open questions

- Deliberate non-refactor: `holdspeak/plugins/host.py::PluginRunResult` and `holdspeak/db.py::PluginRunSummary`/`PluginRunJob` are *implementation* shapes (in-process result, persisted summary, queue record). The new `PluginRun` is the *contract* shape per spec §5.1 — it's the canonical entity HS-2-05 will persist and HS-2-07 will reference from `ArtifactLineage.plugin_run_keys`. Do not collapse them in this story; the contract type comes first, adapters in HS-2-04/HS-2-05.
- `intent_timeline.detect_intent_transitions` still returns `list[dict[str, Any]]` for backwards compatibility with the existing meeting-runtime callers. HS-2-03 will add a typed sibling (e.g. `iter_intent_transitions(...) -> list[IntentTransition]`) without removing the dict surface.
