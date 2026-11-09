# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mermaid_architecture_plugin.py to restore.

# ruff: noqa


# --- test_plugin_attributes_match_contract: P1/P6: reads class constants (id, version 0.1.0, kind) back and checks isinstance of the registered plugin
def test_plugin_attributes_match_contract() -> None:
    plugin = MermaidArchitecturePlugin()
    assert plugin.id == "mermaid_architecture"
    assert plugin.version == "0.1.0"
    assert plugin.kind == "artifact_generator"
    assert plugin.execution_mode == "deferred"
    assert plugin.required_capabilities == ["llm"]


# --- test_register_builtin_plugins_uses_real_class: P1/P6: reads class constants (id, version 0.1.0, kind) back and checks isinstance of the registered plugin
def test_register_builtin_plugins_uses_real_class() -> None:
    host = PluginHost()
    registered = register_builtin_plugins(host)

    assert "mermaid_architecture" in registered
    plugin = host.get_plugin("mermaid_architecture")
    assert plugin is not None
    assert isinstance(plugin, MermaidArchitecturePlugin)
    assert not isinstance(plugin, DeterministicPlugin)

    # As of HS-29-03 every built-in is real — no DeterministicPlugin stubs remain.
    sibling = host.get_plugin("stakeholder_update_drafter")
    assert sibling is not None
    assert not isinstance(sibling, DeterministicPlugin)
