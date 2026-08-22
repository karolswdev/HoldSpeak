# Story 143-07 evidence — Thoughts, Ask, and Writing adoption

**Status:** done
**Captured:** 2026-08-22

## Production waist

`RoutedInferenceCoordinator` is composed once on the process broker. It owns the
Story-05 evidence provider, immutable route/operation freeze, Story-06 execution
start, controller reservation loop, Runner dispatch, route receipt, Stop fence,
next-run summary, and invocation override seam. Ask, Thought interview, intent
classification, and rewrite reach providers only through that coordinator after
the one-way family migration marker exists.

Operation material is private, immutable, restart-reconstructable JSON. For each
resolved leg the evidence stores the exact serialized payload, deployment
revision, input reservation under `utf8-byte-upper-bound@1`, output reservation,
and preflight eligibility. One `BEGIN IMMEDIATE` publishes material, operation
plan, and controller execution start; composite admission rolls every member
back when any constituent cannot freeze. Thought's logical reservation and
each continuation commit those identities in the same transaction. Startup
settles controller dispatch evidence before projection recovery and resumes an
admitted pre-dispatch Thought using its exact stored route execution.
Recovery atomically transfers the expired dispatch lease to the replacement
host, so Stop still fences and signals that recovered physical child.

Speech freezes its selected intent/rewrite route at session admission, then uses
Story-05 `freeze_operation_for_route` when prompt material exists. The physical
child remains a trusted child of the speech parent. The old application-owned
intent loop, response-format retry, and generic advance-on-failed helper no
longer create retry authority. The current punctuation stage is lexical, so
`speech.punctuate` is recorded as non-executing and model admission refuses it.
If route-set persistence refuses after broker admission, the exact parent is
receipted refused; startup receipts a crash-window parent lacking its context as
indeterminate, so the cross-service boundary cannot leave a live orphan.

Thought interview and Ask are capability revision 2. Thought's Runner boundary
validates the real question-or-synthesis union. Ask normalizes provider output
to the semantic `{output}` contract; provider/model placement metadata comes
only from the frozen deployment and controller receipt. Refinement stages one
projection against each actual controller child and will materialize a review
only when that child is the controller receipt's sole winning attempt.
The immutable producer reference carries the typed semantic-result digest; Ask
and Thought additionally bind it to the receipt-gated STAGED candidate, so
winner replay does not depend on an optional published application row.

## Focused proof

- `tests/unit/test_phase143_production_adoption.py`
  - immutable per-leg evidence and assignment-edit freeze
  - atomic composite rollback and late speech-operation attachment
  - real controller fallback and saved local-to-cloud boundary crossing
  - an available but unsaved cloud profile receives zero calls when the saved
    local-only route fails, proving that availability is not egress authority
  - routed speech rewrite remains parented to the admitted speech session
  - routed Stop persists `stopping` before signalling the exact child and never advances
  - routed Thought refinement materializes only the controller winner
  - exact routed Thought pre-dispatch restart/resume without a new execution
  - next-run summary, one-run override, atomic migration rollback/idempotence,
    and no post-marker Config selector
- `tests/unit/test_refinement_coordinator.py` and
  `tests/unit/test_refinement_thought_service.py`: receipt-gated restart,
  cancellation, stale-source, and review correlation laws.
- `tests/unit/test_dictation_pipeline_admission.py`,
  `tests/unit/test_dictation_intent_router.py`, and
  `tests/unit/test_one_path_cardinality.py`: one physical request per authority
  and retirement of application-owned retry paths.
- Phase-143 capability, routing-authority, and fallback-surface censuses were
  updated for the sealed coordinator and selected-revision speech binding.

## Deliberate boundary

Story 13 glass is absent. Adding/downloading/connecting models remains separate
from assignment mutation. Meeting, transcription, background, tools, agents,
Workbench, Recipe, and workflow adopters remain owned by Stories 08–10.

## Captured verification

```text
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q \
  tests/unit/test_phase143_production_adoption.py \
  tests/unit/test_phase143_inference_capability_registry.py \
  tests/unit/test_phase143_inference_route_plans.py \
  tests/unit/test_phase143_inference_fallback_controller.py \
  tests/unit/test_phase143_inference_assignments.py \
  tests/unit/test_refinement_coordinator.py \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_dictation_pipeline_admission.py \
  tests/unit/test_dictation_intent_router.py \
  tests/unit/test_one_path_cardinality.py \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot \
  tests/unit/test_db_schema_policy.py

277 passed in 65.89s
```

```text
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q \
  tests/unit/test_sequence_workflow_runner_migration.py \
  -k 'reconcile or abandoned'

2 passed, 29 deselected in 0.84s
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m ruff check --select F \
  holdspeak/kernel/parent_run.py \
  holdspeak/kernel/projection_stager.py \
  holdspeak/services/inference_adoption_service.py \
  holdspeak/services/refinement_coordinator.py \
  holdspeak/services/refinement_thought_service.py \
  holdspeak/speech_session/session.py \
  tests/unit/test_phase143_production_adoption.py \
  tests/unit/test_phase143_inference_assignments.py

All checks passed!
```

`git diff --check` was clean. Four successive cold audits reduced the remaining
authority findings to zero; the final verdict was **RATIFY**.
