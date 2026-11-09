# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_stakeholder_update_drafter_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1/P5: declared plugin constants; the capability block is the same host path test_scope_guard_plugin covers
def test_attributes() -> None:
    p = StakeholderUpdateDrafterPlugin()
    assert p.id == "stakeholder_update_drafter"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]


