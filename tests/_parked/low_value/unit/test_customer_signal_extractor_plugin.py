# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_customer_signal_extractor_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1/P3: reads the plugin's id/kind/mode constants and isinstance of the registered class; the run tests drive the real plugin
def test_attributes() -> None:
    p = CustomerSignalExtractorPlugin()
    assert p.id == "customer_signal_extractor"
    assert p.kind == "signals"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


# --- test_registrar_returns_real_plugin: P1/P3: reads the plugin's id/kind/mode constants and isinstance of the registered class; the run tests drive the real plugin
def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("customer_signal_extractor"), CustomerSignalExtractorPlugin)
