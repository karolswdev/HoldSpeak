# Story 143-06 evidence — Fallback Controller and Failure Law

- **Status:** done
- **Captured:** 2026-08-22
- **Implementation:** `353081c6` (merged by `d1be6beb`)
- **Deferred acceptance closure:** Story 143-07, merged by `8fc6e476`

## Durable controller law

`InferenceFallbackController` is the sole route-attempt election authority for
an activated frozen route. It transactionally reserves each physical attempt,
settles only typed Runner evidence, applies the closed retry/fallback policy,
fences Stop/deadline/budget advancement, and reconstructs an immutable
`RouteExecutionReceipt`. Unknown post-send completion becomes indeterminate and
cannot advance. Provider dialect attempts remain separately admitted physical
children rather than hidden model fallback.

The remaining generic v1 entrances are census-pinned exceptions awaiting their
own adopter stories. Story 07 supplies the first production composition of the
Story 05/06 waist; request code cannot inject a controller or retarget a frozen
execution from current settings.

## Deferred local-to-cloud acceptance proof

`tests/unit/test_phase143_production_adoption.py::test_saved_local_to_cloud_boundary_crossing_and_unsaved_zero_egress`
closes the deferred Story 06 criterion through the first cloud-capable adopter:

- A saved ordered local-to-cloud chain fails on the frozen local leg, advances
  once to the exact saved cloud leg, and receipts both attempted boundaries and
  the cloud winner.
- A ready cloud profile that is installed but absent from the saved assignment
  receives zero physical calls when the saved local-only route fails. Merely
  available infrastructure is not egress authority.

## Focused verification

The closeout gate covers the controller state machine, frozen-route
reconstruction, Runner receipt evidence, assignment/census authority, the
Story 07 production adopter, one-path cardinality, schema reconciliation, and
the retired Swift Workbench retry/fallback loops.

Fresh verification from `origin/main@8fc6e476`:

- `PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q -x tests/unit/test_phase143_inference_fallback_controller.py tests/unit/test_phase143_inference_route_plans.py tests/unit/test_inference_runner.py`
  — `144 passed`.
- `PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q -x tests/unit/test_dictation_runtime.py tests/unit/test_endpoint_health_wiring.py tests/unit/test_intel_cloud.py tests/unit/test_phase143_inference_assignments.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py`
  — `91 passed`.
- `PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q -x tests/unit/test_phase143_production_adoption.py tests/unit/test_one_path_cardinality.py tests/unit/test_db_schema_policy.py`
  — `50 passed`.
- `PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_phase143_production_adoption.py::test_saved_local_to_cloud_boundary_crossing_and_unsaved_zero_egress`
  — `1 passed` (the deferred criterion itself).
- `swift test --package-path apple --filter 'BlueprintInterpreterTests|BlueprintWireTests|WorkflowRunnerTests'`
  — `34 passed`.

The repository `dw` contract is also run before this status transition is
committed.

## Scope boundary

This closes only Story 06. Later adopter stories still own migration of their
production call families, and Stories 13–14 retain owner glass and final chaos
closure. No implementation code changes are part of this closeout.

### Captured run — 2026-08-22T15:14:51Z

- **Command:** `env PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_phase143_production_adoption.py::test_saved_local_to_cloud_boundary_crossing_and_unsaved_zero_egress`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9859969974488992ffd78f7e67fbd4978b1d0ac7

```text
.                                                                        [100%]
1 passed in 0.84s
```
