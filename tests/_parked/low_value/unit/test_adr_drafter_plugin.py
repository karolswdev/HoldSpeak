# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_adr_drafter_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1: asserts the plugin's id/kind/mode literals; the capability gate is tested in test_host_blocks_without_llm_capability
def test_attributes() -> None:
    p = AdrDrafterPlugin()
    assert p.id == "adr_drafter"
    assert p.kind == "artifact_generator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]
