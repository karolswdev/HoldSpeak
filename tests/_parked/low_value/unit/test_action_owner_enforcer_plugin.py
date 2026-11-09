# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_action_owner_enforcer_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1: asserts the plugin's id/kind/mode literals; the capability gate is tested in test_host_blocks_without_llm_capability
def test_attributes() -> None:
    p = ActionOwnerEnforcerPlugin()
    assert p.id == "action_owner_enforcer"
    assert p.kind == "validator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]
