# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_dependency_mapper_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1: asserts four class constants (id, kind, mode, capabilities)
def test_attributes() -> None:
    p = DependencyMapperPlugin()
    assert p.id == "dependency_mapper"
    assert p.kind == "synthesizer"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]
