# MIR-01 Traceability (Incremental)

This checkpoint covers MIR Step 1/2/3 foundations.

- MIR-F-001 rolling windows:
  - tests/unit/test_intent_timeline.py::test_build_intent_windows_creates_overlapping_windows
- MIR-F-002 multi-label scoring output:
  - tests/unit/test_intent_signals.py::test_extract_intent_signals_returns_all_supported_intents
- MIR-F-005 hysteresis behavior:
  - tests/unit/test_intent_router.py::test_select_active_intents_uses_threshold_and_hysteresis
- MIR-F-008 idempotent execution key + duplicate suppression:
  - holdspeak/plugins/host.py::build_idempotency_key
  - tests/unit/test_plugin_host_idempotency.py::test_duplicate_plugin_run_returns_deduped_result
- MIR-R-002 plugin timeout enforcement:
  - tests/unit/test_plugin_host.py::test_plugin_host_returns_timeout_for_slow_plugin
- MIR-R-004 failure isolation:
  - tests/unit/test_plugin_host.py::test_plugin_host_chain_isolates_failure_and_continues
- MIR-A-000 web-first MIR control hooks:
  - tests/integration/test_web_server.py::TestIntentRoutingControlEndpoints

Not yet covered in this checkpoint: DB persistence and migrations, synthesis and lineage storage, timeline/run-history web APIs, full MIR evidence contract closure.
