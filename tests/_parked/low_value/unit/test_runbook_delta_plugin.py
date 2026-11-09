# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_runbook_delta_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1/P6: re-types the plugin's id, kind and mode attributes and checks isinstance after registration
def test_attributes() -> None:
    p = RunbookDeltaPlugin()
    assert p.id == "runbook_delta"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


# --- test_registrar_returns_real_plugin: P1/P6: re-types the plugin's id, kind and mode attributes and checks isinstance after registration
def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("runbook_delta"), RunbookDeltaPlugin)
