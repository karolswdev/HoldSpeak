# Evidence - HS-131-15

- **Story:** HS-131-15 - Speech side doors become sessions or stay lexical
- **Status:** done
- **Date:** 2026-08-13

## Proof

### Captured run — 2026-08-13T13:58:43Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/home TMPDIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/tmp XDG_CACHE_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/cache XDG_CONFIG_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/config XDG_DATA_HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/data UV_CACHE_DIR=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/uv-cache .venv/bin/python -m pytest -q tests/integration/test_dictation_journal_replay.py tests/integration/test_dictation_journal_wiring.py tests/integration/test_dictation_moment_of_truth.py tests/integration/test_speech_side_door_entrypoints.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py tests/unit/test_decision_commitments.py tests/unit/test_decision_record_service.py tests/unit/test_dictation_cli.py tests/unit/test_dictation_pipeline_admission.py tests/unit/test_dictation_session_admission.py tests/unit/test_monday_brief_service.py tests/unit/test_one_path_cardinality.py tests/unit/test_one_path_census.py tests/unit/test_one_path_spine.py tests/unit/test_residual_service_admission.py tests/unit/test_schedule_delegations.py tests/unit/test_sequence_workflow_runner_migration.py tests/unit/test_meeting_session_admission.py tests/unit/test_speak_room_delivery.py tests/unit/test_speech_side_door_admission.py tests/unit/test_voice_resolve.py tests/unit/test_web_routes_remote_dictation.py tests/unit/test_workbench_runner_migration.py tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot tests/unit/test_backend_density_guard.py::test_runtime_modules_stay_single_concern tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget tests/unit/test_mesh_relay_provider.py::test_assembly_builds_the_mesh_runtime_from_the_frozen_admission tests/unit/test_dictation_runner.py::test_web_runtime_method_delegates tests/unit/test_voice_command_dispatch.py::test_web_runtime_delegate_injects_typer_and_activity --basetemp=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/e1d6e528-cf6e-4d45-84a6-efc08907ff0a/scratchpad/hs13115-evidence/pytest -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 49f8d31d0a129ccdb5c2a28ad611a5ee0910cb45

```text
........................................................................ [ 14%]
........................................................................ [ 28%]
........................................................................ [ 42%]
........................................................................ [ 56%]
........................................................................ [ 71%]
........................................................................ [ 85%]
........................................................................ [ 99%]
..                                                                       [100%]
506 passed in 103.50s (0:01:43)
```

## Verification narrative

### What shipped

- Browser rehearsal, journal replay, template preview, and the authenticated CLI
  command open one fresh bounded `dictation.session` exactly when the frozen
  configuration selects provider-backed pipeline work. Provider-free
  configurations stay lexical and mint no speech parent, provider runtime,
  inference child, disconnect watcher, or terminal receipt.
- CLI authority is derived only from `$HOLDSPEAK_TOKEN` against the hub's
  configured bearer through the central owner authenticator. Missing or invalid
  credentials refuse before runtime construction.
- Provider construction reads only the parent-bound frozen deployment revision;
  admitted construction disables warm-on-start and preserves exact endpoint,
  local artifact, mesh node, model, secret slot, and egress boundary.
- Admission, revision, liveness, revocation, child-budget, and provider controls
  escape broad raw-text degradation. Cancellation, route disconnect, command
  interruption, and expiry discard late output.
- Final response, journal, preview, typing, command, and remote-delivery handoff
  share a durable publication election. An exact SQLite claim serializes other
  processes, cancellation, revocation, expiry, and new children. Transient claim
  release failure retries only its exact token without replaying the callback.
- Kernel metadata stays content-free: no audio, dictated/input text, prompts,
  completions, token streams, rewritten bodies, API keys, bearer tokens, or raw
  provider exceptions enter operation, event, parent, or receipt rows.

### Fence result

The final census remains 105 executable/model-bearing sites while both speech
findings become admitted seams: 70 allowlist sites, 27 admitted-seam callers,
four pinned findings in four families, and **zero unregistered**. No speech scope
entered `ADAPTER_ALLOWLIST`. Both exact mutations — removing the admitted handoff
from browser dry-run and CLI command — fail by their named finding family before
the source is restored.

### Hostile counsel

The final independent hostile pass returned:

```text
SHIP-CANDIDATE
```

Its three prior P1s are repaired and regression-locked: plan/principal/context
are bound to durable parent metadata; publication release has live exact-token
recovery; generic expiry defers across the v58 trigger instead of leaking an
SQLite exception. See
[`assets/hs-131-15/hostile-verdict.md`](./assets/hs-131-15/hostile-verdict.md).

### Official gate accounting

The two-lane full gate remains inherited red and is not described as green. It
found five current-diff regressions during delivery: runtime and kernel density
guards, one obsolete unadmitted mesh-construction test, and two stale
monkeypatch locations after the required concern carve. All five were repaired
and pass together. The final backend lane's only apparent new names were three
unrelated Slack tests blocked behind one xdist worker's leaked append lock after
a timeout; they pass together immediately in serial. There is no current-diff
product failure. Full totals and classification are in
[`assets/hs-131-15/verification-summary.md`](./assets/hs-131-15/verification-summary.md).

### Additional read results

- Complete hostile suite: 501 passed.
- Full impacted speech suite: 304 passed.
- Web typecheck passed; focused web suite: 45 passed.
- `git diff --check` and Python `compileall` passed.
- Final Delivery Workbench capture above: 506 passed.
