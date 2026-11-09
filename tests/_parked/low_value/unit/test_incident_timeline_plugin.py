# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_incident_timeline_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1: asserts four class constants (id, kind, mode, capabilities)
def test_attributes() -> None:
    p = IncidentTimelinePlugin()
    assert p.id == "incident_timeline"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]
