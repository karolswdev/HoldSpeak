# MIR-01 Traceability (Incremental)

This checkpoint covers MIR Step 1/2 foundations only.

- MIR-F-001 rolling windows:
  - tests/unit/test_intent_timeline.py::test_build_intent_windows_creates_overlapping_windows
- MIR-F-002 multi-label scoring output:
  - tests/unit/test_intent_signals.py::test_extract_intent_signals_returns_all_supported_intents
- MIR-F-003 required intent set coverage:
  - holdspeak/plugins/signals.py::SUPPORTED_INTENTS
  - tests/unit/test_intent_signals.py
- MIR-F-005 hysteresis behavior:
  - tests/unit/test_intent_router.py::test_select_active_intents_uses_threshold_and_hysteresis
- MIR-A-000 web-first MIR control hooks:
  - tests/integration/test_web_server.py::TestIntentRoutingControlEndpoints
  - tests/unit/test_web_runtime.py::test_runtime_meeting_control_callbacks_are_wired

Not yet covered in this checkpoint: plugin host execution, synthesis, DB persistence, timeline/run-history APIs, full MIR evidence contract.
