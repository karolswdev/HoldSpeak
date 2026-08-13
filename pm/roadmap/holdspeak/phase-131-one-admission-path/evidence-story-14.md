# Evidence - HS-131-14

- **Story:** HS-131-14 - Plugins receive admitted intelligence
- **Status:** done
- **Date:** 2026-08-13

## Proof

### Captured run — 2026-08-13T07:25:19Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/home TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/tmp XDG_CACHE_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/cache XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/data UV_CACHE_DIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/uv-cache .venv/bin/python -m pytest -q tests/unit/test_plugin_provider_admission.py tests/unit/test_one_path_census.py tests/unit/test_one_path_context.py tests/unit/test_one_path_spine.py tests/unit/test_one_path_cardinality.py tests/unit/test_one_path_provenance.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_meeting_plugins.py tests/unit/test_meeting_session_admission.py tests/unit/test_segment_probe.py tests/unit/test_plugin_host.py tests/unit/test_plugin_host_llm_capability.py tests/unit/test_plugin_host_idempotency.py tests/unit/test_plugin_queue.py tests/unit/test_plugin_disable.py tests/unit/test_intent_dispatch.py tests/unit/test_intent_pipeline.py tests/unit/test_action_owner_enforcer_plugin.py tests/unit/test_adr_drafter_plugin.py tests/unit/test_customer_signal_extractor_plugin.py tests/unit/test_decision_announcement_drafter_plugin.py tests/unit/test_decision_capture_plugin.py tests/unit/test_dependency_mapper_plugin.py tests/unit/test_incident_timeline_plugin.py tests/unit/test_mermaid_architecture_plugin.py tests/unit/test_milestone_planner_plugin.py tests/unit/test_requirements_extractor_plugin.py tests/unit/test_risk_heatmap_plugin.py tests/unit/test_runbook_delta_plugin.py tests/unit/test_scope_guard_plugin.py tests/unit/test_stakeholder_update_drafter_plugin.py tests/unit/test_intel_package.py tests/unit/test_intel_cloud.py tests/unit/test_intel_profile_resolution.py tests/unit/test_meeting_placement_policy.py tests/unit/test_mesh_relay_provider.py tests/unit/test_residual_service_admission.py tests/unit/test_dictation_pipeline_admission.py tests/unit/test_ask_grounding_claims.py tests/unit/test_ask_runner_migration.py tests/unit/test_capability_invocations.py tests/unit/test_engine_off_the_loop.py tests/unit/test_hs13103_remaining_obligations.py tests/unit/test_run_artifacts.py tests/unit/test_run_frames.py tests/unit/test_web_routes_ask.py tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_recipe_chat.py tests/unit/test_web_runtime.py tests/unit/test_intel_queue.py tests/unit/test_workbench_runner_migration.py tests/unit/test_deployment_identity.py tests/unit/test_fault_plane.py::test_named_plugin_fault_fails_exactly_that_key_then_exact_retry tests/integration/test_mermaid_architecture_pipeline.py tests/integration/test_presence_learning_aftercare_broadcasts.py tests/integration/test_multi_intent_routing.py tests/integration/test_artifact_synthesis_pipeline.py tests/integration/test_intent_failure_isolation.py --basetemp=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13114-evidence/pytest -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c3f68d6521c70e37732e8e64035d48d2d7819c6f

```text
........................................................................ [  8%]
........................................................................ [ 17%]
........................................................................ [ 26%]
........................................................................ [ 35%]
........................................................................ [ 44%]
........................................................................ [ 53%]
........................................................................ [ 62%]
........................................................................ [ 71%]
........................................................................ [ 79%]
........................................................................ [ 88%]
........................................................................ [ 97%]
...................                                                      [100%]
811 passed in 106.10s (0:01:46)
```

## Verification narrative

### What shipped

- **Plugins consume admitted intelligence.** All fourteen model-bearing builtin
  plugins and `segment_probe` use the host-issued `PluginDispatch` carried only
  in that invocation's private context. Host and plugin instances store no
  ambient engine or dispatch state, and the legacy `_cached_provider` plus
  `intel_call` production side doors are deleted.
- **One handle means one physical completion.** The handle binds the runner's
  exact opaque dispatch context, frozen revision, destination, warrant basis,
  positive ordinal, and child cancellation signal. One lock guards the
  `LIVE -> IN-FLIGHT -> SPENT` lifecycle, so sequential or concurrent replay and
  multi-plugin use refuse before a second physical call.
- **Timeout elects one honest outcome.** `release() -> bool` atomically revokes
  the handle and reports whether physical work was already claimed. A timeout
  before claim mechanically fences late dispatch; a timeout after claim is
  `ProviderIndeterminate`, and neither route publishes late plugin output.
- **Failure and retry remain visible.** Provider exceptions fail the admitted
  child rather than becoming a successful plugin error object. Compatibility
  retry propagates to the runner and receives a separate `_r2` child, context,
  handle, ordinal, and terminal receipt; only the successful projection
  materializes.
- **No pre-admission probe.** Meeting startup remains lexical until HS-131-17
  owns admitted MIR routing. It no longer constructs configured intelligence
  before session admission.
- **One configured construction entrance.** Public
  `build_configured_meeting_intel` is deleted. Private `_configured_engine` is
  called only after exact context/revision validation by
  `configured_meeting_intel`.

### Fence result

The executable census is now 105 sites: 70 allowlist sites, 25 admitted-seam
sites, six pinned findings in six families, and **zero unregistered**. Relative
to HS-131-13, this story removes all thirty `plugin-default-provider` findings
and both `legacy-uncontextual-factory` findings: 134→105 total, 38→6 findings,
and 8→6 families. No plugin builtin or segment-probe scope entered the adapter
allowlist. The updated exact ledger is
[`assets/hs-131-10/findings-inventory.md`](./assets/hs-131-10/findings-inventory.md).

### Hostile counsel

Hostile verification found three realistic blockers during implementation:
ambient host/plugin state could cross timed-out children, one handle allowed
several physical calls, and release raced both physical claim and timeout
classification. Each was repaired structurally with production-path
regressions. The fresh independent pass returned:

```text
RATIFY FOR STORY CLOSE
```

The report is
[`assets/hs-131-14/hostile-verdict.md`](./assets/hs-131-14/hostile-verdict.md).

### Official gate accounting

The final official two-lane gate ran on a quiet tree under isolated scratch
`HOME`, `TMPDIR`, XDG roots, pytest basetemp, and the explicit installed
Playwright browser cache. Its inherited-red totals were:

```text
67 failed, 5083 passed, 8 skipped in 176.76s
10 failed, 239 passed, 36 skipped, 16 deselected, 14 errors in 683.35s
```

The final 91-name ledger contains no current-diff product regression. The one
apparent new name versus HS-131-13's 90-name run is the inherited live-model
mesh canary flake: it was reproduced twice on this tree and, critically, both
passed and failed on an untouched detached HS-131-13 control tree at `190b1bed`
with the same successful response omitting `PYLON-CANARY-7`. Its exact name is
already present in earlier Phase-131 ledgers. The first quiet gate did find one
real current-diff regression—the fault-plane host test double did not accept the
new `dispatch` keyword. It was repaired and re-proved alone, in a 274-test set,
and in this captured 811-test suite; it is absent from the final gate ledger.
The red suite is not described as green. Full accounting is in
[`assets/hs-131-14/verification-summary.md`](./assets/hs-131-14/verification-summary.md).

### Discarded runs

One gate ran from the implementation worktree after shell cwd drift and was
harness-killed before a terminal result. Another overlapped the tail of hostile
verification and was deliberately stopped. Neither supports a story claim.
