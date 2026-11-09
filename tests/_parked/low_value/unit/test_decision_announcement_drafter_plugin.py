# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_decision_announcement_drafter_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1/P3: reads the plugin's id/kind/mode constants and isinstance of the registered class; the run tests drive the real plugin
def test_attributes() -> None:
    p = DecisionAnnouncementDrafterPlugin()
    assert p.id == "decision_announcement_drafter"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


# --- test_registrar_returns_real_plugin: P1/P3: reads the plugin's id/kind/mode constants and isinstance of the registered class; the run tests drive the real plugin
def test_registrar_returns_real_plugin() -> None:
    host = PluginHost(default_timeout_seconds=0.5, enabled_capabilities={"llm"})
    register_builtin_plugins(host)
    assert isinstance(host.get_plugin("decision_announcement_drafter"), DecisionAnnouncementDrafterPlugin)
