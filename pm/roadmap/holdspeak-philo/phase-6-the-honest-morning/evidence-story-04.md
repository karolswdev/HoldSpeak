# Evidence - PHILO-6-04

- **Story:** PHILO-6-04 - One cause, one row
- **Status:** done
- **Date:** 2026-09-24

## Proof

### Captured run — 2026-09-25T02:45:45Z

- **Command:** `bash -c set -o pipefail; export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export HOME=$(mktemp -d); uv run --extra dev pytest --collect-only -q tests/unit/test_philo6_04_one_cause_one_row.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo3_01_decision_route.py; uv run --extra dev pytest -q tests/unit/test_philo6_04_one_cause_one_row.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo3_01_decision_route.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
tests/unit/test_philo6_04_one_cause_one_row.py::test_missing_id_has_one_real_observer_failure_row
tests/unit/test_philo6_04_one_cause_one_row.py::test_desk_id_uses_one_registry_read
tests/unit/test_philo6_04_one_cause_one_row.py::test_lifecycle_only_id_uses_one_observed_lineage_read
tests/unit/test_philo6_04_one_cause_one_row.py::test_desk_owner_wins_when_real_producers_share_an_id
tests/unit/test_philo6_04_one_cause_one_row.py::test_each_real_service_failure_keeps_its_observer_receipt
tests/unit/test_philo5_one_decision.py::TestOneInstanceInTheHub::test_both_transports_hold_the_one_registry_bound_to_the_hubs_instance
tests/unit/test_philo5_one_decision.py::TestOneInstanceInTheHub::test_every_decision_call_over_http_and_mcp_goes_through_invoke
tests/unit/test_philo5_one_decision.py::TestOneInstanceInTheHub::test_the_http_envelopes_are_unchanged
tests/unit/test_philo5_one_decision.py::test_durable_state_survives_a_new_hub_over_the_same_database
tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors
tests/unit/test_philo5_one_decision.py::test_unknown_operation_is_a_named_refusal
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[actor]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[as_principal]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[authority]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[identity]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[on_behalf_of]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[owner]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[principal]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[principal_identity]
tests/unit/test_philo5_one_decision.py::test_an_authority_field_in_the_arguments_is_refused[principal_kind]
tests/unit/test_philo5_one_decision.py::test_authority_is_refused_through_the_mcp_transport_too
tests/unit/test_philo5_one_decision.py::test_binding_fails_at_composition_not_on_first_call
tests/unit/test_philo5_one_decision.py::test_mcp_decisions_branch_validates_with_the_descriptor_schema
tests/unit/test_philo5_one_decision.py::test_published_desk_tool_schemas_are_unchanged_and_admit_every_contract_payload
tests/unit/test_philo5_one_decision.py::test_palette_refusal_through_dispatch_writes_nothing
tests/unit/test_philo5_one_decision.py::test_palette_refusal_through_the_http_jsonrpc_handler_is_mcp_005
tests/unit/test_philo5_one_decision.py::test_other_kinds_still_take_the_generic_path
tests/unit/test_philo5_one_decision.py::test_operations_export_matches_the_catalogue
tests/unit/test_philo5_one_decision.py::test_the_residual_set_equals_the_trees_census
tests/unit/test_philo5_one_decision.py::test_the_residual_set_shrank_by_exactly_the_paid_decision_entries
tests/unit/test_philo5_one_decision.py::test_the_residual_fence_names_a_new_identity_and_a_stale_one
tests/unit/test_philo3_01_decision_route.py::test_post_decision_through_the_real_route_reads_back
tests/unit/test_philo3_01_decision_route.py::test_pre_fix_route_answers_500_on_create

33 tests collected in 0.68s
.................................                                        [100%]
33 passed in 11.73s
```

### Captured run — 2026-09-25T02:48:00Z

- **Command:** `bash -c set -o pipefail; export HOME=$(mktemp -d); export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; .venv/bin/python docs/internal/philo/phase-6/rows/walk_one_row.py --case case.philo504.decision_missing.refusal.op --viewport 1440 --out docs/internal/philo/phase-6/rows/green-op-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
PASS: live
BRAIN: astra
SOURCE: 66205729332ef66a6d16a186c04ae4801311734a dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-C1ztUjnF.js'] hub=http://127.0.0.1:65477 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rjhpqdwc/.local/share/holdspeak/holdspeak.db engine=none
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: operation refused by name 'not_found': Unknown decision: philo504-deliberately-absent
{
  "db_path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rjhpqdwc/.local/share/holdspeak/holdspeak.db",
  "home": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rjhpqdwc",
  "rows": [
    {
      "id": 6,
      "event_id": "1b6e7b5a-f818-428d-a097-7fe1e5cb0ef7",
      "timestamp": 1790304482.267755,
      "service": "PrimitiveService",
      "method": "get_decision",
      "principal_kind": "owner",
      "principal_identity": "owner-session",
      "args_summary": "{\"decision_id\":\"philo504-deliberately-absent\"}",
      "result_summary": "",
      "error": "NotFound('Unknown decision: philo504-deliberately-absent')",
      "error_code": "not_found",
      "duration_ms": 0.1049041748046875,
      "correlation_id": "1e830503-f700-4452-b363-936bf2921606",
      "is_async": 0,
      "origin": "local",
      "caller": "127.0.0.1",
      "caller_identity": "owner-session"
    }
  ],
  "count": 1,
  "case": "case.philo504.decision_missing.refusal.op",
  "viewport": 1440,
  "source_root": "/Users/karol/dev/tools/wt-philo-6-b",
  "route_sha256": "10958dbee864c15f07ed1983b65c3cf2cd19e0d4f2d0934ab20e5d6b11982457",
  "source": {
    "revision": "66205729332ef66a6d16a186c04ae4801311734a",
    "dirty": true,
    "frontend_build": {
      "built": true,
      "index_sha256": "28476b885ae1530c12cf9c4ac834e9df153bc5dcbcaede75f3d94aa62cea17c1",
      "assets": [
        "index-C1ztUjnF.js"
      ]
    },
    "hub": {
      "url": "http://127.0.0.1:65477",
      "port": 65477,
      "pid": 33180,
      "home": "/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rjhpqdwc",
      "scheduler_thread": false
    },
    "db_path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-rjhpqdwc/.local/share/holdspeak/holdspeak.db",
    "fixture_hashes": {},
    "clock": {
      "tz": null,
      "started_utc": "2026-09-25T02:48:00.715291+00:00",
      "mechanism": "none \u2014 the real clock; no case may claim an advance",
      "scheduler_thread": false
    },
    "engine_mode": "none",
    "engine_identity": null,
    "boundary_substitutions": [],
    "restarts": [],
    "rig_version": "1.2.0",
    "brief_sha256": "ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800",
    "atlas": {
      "path": "/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/graph/atlas-phase3.json",
      "sha256": "b9e5bb7453460e3894320394cf039899168d9c923b89a95b7a25dfd28f00423b",
      "version": "phase3-closure"
    },
    "product_wiring": {
      "has": [
        "MeetingWebServer routes",
        "the database owner lock (port published)",
        "the intelligence queue drainer"
      ],
      "lacks": [
        "AudioRecorder (the microphone is forbidden to this rig)",
        "HotkeyListener (no native keystrokes)",
        "voice_session / device registry",
        "transcriber warm-up",
        "the deferred plugin-queue thread",
        "the Cadence Engine tick",
        "the brief producer clock seam (not requested; the wall clock)",
        "the heartbeat conductor loop (not requested by the case)"
      ]
    },
    "engine_replay_sha256": null
  },
  "rig_verdict": "pass",
  "one_cause_one_row": true
}
ONE CAUSE ONE ROW: PASS (1 failure rows; expected 1)
```

### Captured run — 2026-09-25T02:49:33Z

- **Command:** `bash -c set -o pipefail; export HOME=$(mktemp -d); export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; .venv/bin/python docs/internal/philo/phase-6/rows/walk_one_row.py --case case.philo504.decision_missing.refusal --viewport 393 --out docs/internal/philo/phase-6/rows/green-http-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
PASS: live
BRAIN: astra
SOURCE: 66205729332ef66a6d16a186c04ae4801311734a dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-C1ztUjnF.js'] hub=http://127.0.0.1:49205 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-eb28nca2/.local/share/holdspeak/holdspeak.db engine=none
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: ['/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/phase-6/rows/green-http-393/20260925T024933Z-case.philo504.decision_missing.refusal-astra-393/before.png', '/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/phase-6/rows/green-http-393/20260925T024933Z-case.philo504.decision_missing.refusal-astra-393/after.png']
NOTE: predicate: GET /api/decisions/philo504-deliberately-absent answered 404, wanted 404 (body sha256 e96c1febd835); response body contains the declared admission facts
{
  "db_path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-eb28nca2/.local/share/holdspeak/holdspeak.db",
  "home": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-eb28nca2",
  "rows": [
    {
      "id": 67,
      "event_id": "f8f78ba9-a5e0-4d86-8230-e05524e51421",
      "timestamp": 1790304579.91679,
      "service": "PrimitiveService",
      "method": "get_decision",
      "principal_kind": "owner",
      "principal_identity": "owner-session",
      "args_summary": "{\"decision_id\":\"philo504-deliberately-absent\"}",
      "result_summary": "",
      "error": "NotFound('Unknown decision: philo504-deliberately-absent')",
      "error_code": "not_found",
      "duration_ms": 0.07510185241699219,
      "correlation_id": "440e3c05-838f-4b56-b300-7deee988bfa1",
      "is_async": 0,
      "origin": "local",
      "caller": "",
      "caller_identity": ""
    }
  ],
  "count": 1,
  "case": "case.philo504.decision_missing.refusal",
  "viewport": 393,
  "source_root": "/Users/karol/dev/tools/wt-philo-6-b",
  "route_sha256": "10958dbee864c15f07ed1983b65c3cf2cd19e0d4f2d0934ab20e5d6b11982457",
  "source": {
    "revision": "66205729332ef66a6d16a186c04ae4801311734a",
    "dirty": true,
    "frontend_build": {
      "built": true,
      "index_sha256": "28476b885ae1530c12cf9c4ac834e9df153bc5dcbcaede75f3d94aa62cea17c1",
      "assets": [
        "index-C1ztUjnF.js"
      ]
    },
    "hub": {
      "url": "http://127.0.0.1:49205",
      "port": 49205,
      "pid": 34351,
      "home": "/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-eb28nca2",
      "scheduler_thread": false
    },
    "db_path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-eb28nca2/.local/share/holdspeak/holdspeak.db",
    "fixture_hashes": {},
    "clock": {
      "tz": null,
      "started_utc": "2026-09-25T02:49:33.587205+00:00",
      "mechanism": "none \u2014 the real clock; no case may claim an advance",
      "scheduler_thread": false
    },
    "engine_mode": "none",
    "engine_identity": null,
    "boundary_substitutions": [],
    "restarts": [],
    "rig_version": "1.2.0",
    "brief_sha256": "ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800",
    "atlas": {
      "path": "/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/graph/atlas-phase3.json",
      "sha256": "b9e5bb7453460e3894320394cf039899168d9c923b89a95b7a25dfd28f00423b",
      "version": "phase3-closure"
    },
    "product_wiring": {
      "has": [
        "MeetingWebServer routes",
        "the database owner lock (port published)",
        "the intelligence queue drainer"
      ],
      "lacks": [
        "AudioRecorder (the microphone is forbidden to this rig)",
        "HotkeyListener (no native keystrokes)",
        "voice_session / device registry",
        "transcriber warm-up",
        "the deferred plugin-queue thread",
        "the Cadence Engine tick",
        "the brief producer clock seam (not requested; the wall clock)",
        "the heartbeat conductor loop (not requested by the case)"
      ]
    },
    "engine_replay_sha256": null
  },
  "rig_verdict": "pass",
  "one_cause_one_row": true
}
ONE CAUSE ONE ROW: PASS (1 failure rows; expected 1)
```

### Captured run — 2026-09-25T02:50:16Z

- **Command:** `bash -c set -o pipefail; export HOME=$(mktemp -d); export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; export PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright; export HOLDSPEAK_EVIDENCE_WRITE=1; .venv/bin/python docs/internal/philo/phase-6/rows/walk_one_row.py --case case.philo504.decision_missing.refusal.op --viewport 393 --out docs/internal/philo/phase-6/rows/green-op-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
PASS: live
BRAIN: astra
SOURCE: 66205729332ef66a6d16a186c04ae4801311734a dirty=True
CONTRACT: rig=1.2.0 brief=ba5477fd07db atlas=/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/graph/atlas-phase3.json
RUNTIME: build=['index-C1ztUjnF.js'] hub=http://127.0.0.1:49254 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sd9z9bpz/.local/share/holdspeak/holdspeak.db engine=none
JOB: a1
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: predicate: operation refused by name 'not_found': Unknown decision: philo504-deliberately-absent
{
  "db_path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sd9z9bpz/.local/share/holdspeak/holdspeak.db",
  "home": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sd9z9bpz",
  "rows": [
    {
      "id": 6,
      "event_id": "d8172a70-a06a-46a3-b08d-68d08ddedd0d",
      "timestamp": 1790304618.062285,
      "service": "PrimitiveService",
      "method": "get_decision",
      "principal_kind": "owner",
      "principal_identity": "owner-session",
      "args_summary": "{\"decision_id\":\"philo504-deliberately-absent\"}",
      "result_summary": "",
      "error": "NotFound('Unknown decision: philo504-deliberately-absent')",
      "error_code": "not_found",
      "duration_ms": 0.12087821960449219,
      "correlation_id": "7ca258c0-ad48-4551-9401-372d2b83f9d2",
      "is_async": 0,
      "origin": "local",
      "caller": "127.0.0.1",
      "caller_identity": "owner-session"
    }
  ],
  "count": 1,
  "case": "case.philo504.decision_missing.refusal.op",
  "viewport": 393,
  "source_root": "/Users/karol/dev/tools/wt-philo-6-b",
  "route_sha256": "10958dbee864c15f07ed1983b65c3cf2cd19e0d4f2d0934ab20e5d6b11982457",
  "source": {
    "revision": "66205729332ef66a6d16a186c04ae4801311734a",
    "dirty": true,
    "frontend_build": {
      "built": true,
      "index_sha256": "28476b885ae1530c12cf9c4ac834e9df153bc5dcbcaede75f3d94aa62cea17c1",
      "assets": [
        "index-C1ztUjnF.js"
      ]
    },
    "hub": {
      "url": "http://127.0.0.1:49254",
      "port": 49254,
      "pid": 34943,
      "home": "/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sd9z9bpz",
      "scheduler_thread": false
    },
    "db_path": "/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-sd9z9bpz/.local/share/holdspeak/holdspeak.db",
    "fixture_hashes": {},
    "clock": {
      "tz": null,
      "started_utc": "2026-09-25T02:50:16.503749+00:00",
      "mechanism": "none \u2014 the real clock; no case may claim an advance",
      "scheduler_thread": false
    },
    "engine_mode": "none",
    "engine_identity": null,
    "boundary_substitutions": [],
    "restarts": [],
    "rig_version": "1.2.0",
    "brief_sha256": "ba5477fd07dba564a4e38fcf479838a511444eed3ed0c02e61aaa522358c7800",
    "atlas": {
      "path": "/Users/karol/dev/tools/wt-philo-6-b/docs/internal/philo/graph/atlas-phase3.json",
      "sha256": "b9e5bb7453460e3894320394cf039899168d9c923b89a95b7a25dfd28f00423b",
      "version": "phase3-closure"
    },
    "product_wiring": {
      "has": [
        "MeetingWebServer routes",
        "the database owner lock (port published)",
        "the intelligence queue drainer"
      ],
      "lacks": [
        "AudioRecorder (the microphone is forbidden to this rig)",
        "HotkeyListener (no native keystrokes)",
        "voice_session / device registry",
        "transcriber warm-up",
        "the deferred plugin-queue thread",
        "the Cadence Engine tick",
        "the brief producer clock seam (not requested; the wall clock)",
        "the heartbeat conductor loop (not requested by the case)"
      ]
    },
    "engine_replay_sha256": null
  },
  "rig_verdict": "pass",
  "one_cause_one_row": true
}
ONE CAUSE ONE ROW: PASS (1 failure rows; expected 1)
```

### Captured run — 2026-09-25T02:52:18Z

- **Command:** `bash -c set -o pipefail; python3 docs/internal/philo/phase-6/rows/verify_parity.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
red-http-1440-import-corrected rows: [(67, 'PrimitiveService', 'get_decision', 'not_found'), (68, 'DecisionLifecycleService', 'get_decision', 'not_found')]
red-op-1440 rows: [(6, 'PrimitiveService', 'get_decision', 'not_found')]
green-http-1440 rows: [(67, 'PrimitiveService', 'get_decision', 'not_found')]
green-op-1440 rows: [(6, 'PrimitiveService', 'get_decision', 'not_found')]
1440: missing-decision parity FAIL 2:1 -> PASS 1:1
red-http-393-atlas-width rows: [(67, 'PrimitiveService', 'get_decision', 'not_found'), (68, 'DecisionLifecycleService', 'get_decision', 'not_found')]
red-op-393 rows: [(6, 'PrimitiveService', 'get_decision', 'not_found')]
green-http-393 rows: [(67, 'PrimitiveService', 'get_decision', 'not_found')]
green-op-393 rows: [(6, 'PrimitiveService', 'get_decision', 'not_found')]
393: missing-decision parity FAIL 2:1 -> PASS 1:1
PASS: both real atlas transports at both widths; no missing-id observation retry
```

### Captured run — 2026-09-25T02:59:29Z

- **Command:** `bash -c set -euo pipefail; export HOME=$(mktemp -d); export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH; uv run --extra dev pytest --collect-only -q tests/unit/test_api_surface.py tests/unit/test_philo_architecture.py; uv run --extra dev pytest -q tests/unit/test_api_surface.py tests/unit/test_philo_architecture.py; python3 scripts/philo_graph_reference.py --check; python3 scripts/philo_api_reference.py --check; python3 scripts/philo_boundary_census.py --check; python3 scripts/generate_capability_docs.py --check; git diff --check; test -z "$(git status --porcelain -- pm/roadmap/holdspeak/)"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eee00cbfe7b337d71fc8dff713579e73365a2f14

```text
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest
tests/unit/test_api_surface.py::test_clients_only_call_served_routes
tests/unit/test_api_surface.py::test_manifest_is_not_vacuous
tests/unit/test_api_surface.py::test_extractors_see_the_real_call_sites
tests/unit/test_api_surface.py::test_committed_openapi_matches_reference_app
tests/unit/test_philo_architecture.py::test_valid_metadata_resolves_python_symbols_and_test_nodes
tests/unit/test_philo_architecture.py::test_invalid_metadata_reports_path_node_enum_and_egress
tests/unit/test_philo_architecture.py::test_duplicate_ids_and_snapshot_drift_are_errors
tests/unit/test_philo_architecture.py::test_generation_and_coverage_are_deterministic_and_do_not_promote_paths
tests/unit/test_philo_architecture.py::test_typescript_token_and_test_title_fallback_is_static
tests/unit/test_philo_architecture.py::test_coverage_requires_assertion_and_execution_on_same_test
tests/unit/test_philo_architecture.py::test_explicit_api_reference_checks_method_and_route
tests/unit/test_philo_architecture.py::test_requirement_catalogue_checks_its_own_source_references
tests/unit/test_philo_architecture.py::test_existing_build_copy_is_not_source_evidence

15 tests collected in 0.16s
...............                                                          [100%]
15 passed in 2.32s
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
API reference checked
Boundary candidate census checked
Architecture documentation checked (10 outputs).
```
