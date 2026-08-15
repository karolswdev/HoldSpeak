# Evidence - HS-131-16

- **Story:** HS-131-16 - The mesh receiver proves authority locally
- **Status:** done
- **Date:** 2026-08-14

## Proof

### Captured run — 2026-08-15T04:26:05Z

- **Command:** `env -u HOLDSPEAK_HUB_TOKEN -u HOLDSPEAK_NODE_TOKEN HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs131-evidence-home USERPROFILE=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6742e364-3fad-4eaf-beab-c763cd42042b/scratchpad/hs131-evidence-home uv --directory /Users/karol/dev/tools/HoldSpeak run --extra dev pytest -q --no-header -p no:cacheprovider tests/unit/test_mesh_receiver_authority.py tests/unit/test_mesh_serve_worker.py tests/unit/test_mesh_two_process.py tests/unit/test_mesh_relay_queue.py tests/unit/test_mesh_relay_provider.py tests/unit/test_mesh_liveness_surfaces.py tests/unit/test_mesh_inbox.py tests/unit/test_mesh_discovery.py tests/unit/test_delivery_node_link.py tests/unit/test_delivery_commands.py tests/unit/test_delivery_terminal_routes.py tests/unit/test_node_serve_worker.py tests/unit/test_node_link_two_process.py tests/unit/test_db.py tests/unit/test_one_path_census.py tests/unit/test_one_path_cardinality.py tests/unit/test_one_path_context.py tests/unit/test_one_path_provenance.py tests/unit/test_one_path_spine.py tests/unit/test_web_runtime.py tests/unit/test_sqlite_observer.py tests/unit/test_pipeline_observer.py tests/unit/test_observed_decorator.py tests/unit/test_inference_runner.py tests/unit/test_inference_kernel.py tests/unit/test_inference_targets.py tests/unit/test_deployment_revisions.py tests/unit/test_deployment_identity.py tests/unit/test_web_routes_core.py tests/unit/test_web_auth.py tests/unit/test_delivery_node_routes.py tests/unit/test_delivery_attempts.py tests/unit/test_delivery_registry.py tests/unit/test_delivery_read_model.py tests/unit/test_delivery_receipts_db.py tests/unit/test_delivery_factory_routes.py tests/unit/test_delivery_dossiers.py tests/unit/test_delivery_attempts_correlation.py tests/unit/test_delivery_attempts_sweep.py tests/unit/test_delivery_terminal_stream.py tests/unit/test_db_schema_policy.py tests/unit/test_kernel_broker.py tests/unit/test_kernel_effect_fence.py tests/unit/test_decision_commitments.py tests/unit/test_decision_record_service.py tests/unit/test_monday_brief_service.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b6d46a2687f4b1624582094aafb0ea759573b6bb

```text
........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 25%]
........................................................................ [ 33%]
........................................................................ [ 41%]
........................................................................ [ 50%]
........................................................................ [ 58%]
........................................................................ [ 66%]
........................................................................ [ 75%]
........................................................................ [ 83%]
........................................................................ [ 91%]
........................................................................ [100%]
864 passed in 164.65s (0:02:44)
```
