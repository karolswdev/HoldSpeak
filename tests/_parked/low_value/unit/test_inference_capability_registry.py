# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_inference_capability_registry.py to restore.

# ruff: noqa


# --- test_registry_names_the_semantic_capabilities: P1: the registry holds a literal set of ids and two visibility constants
def test_registry_names_the_semantic_capabilities() -> None:
    # The fast diet (2026-10-12) parked the Phase 143 site census this test
    # also read (tests/_parked/unit/test_phase143_inference_capability_census.py);
    # tests/unit/test_one_path_census.py keeps the fail-closed site fence.
    registry = _registry()
    assert {
        "thought.interview",
        "ask.answer",
        "agent.plan",
        "agent.code",
        "project_doc.suggest_update",
        "speech.target_classify",
        "internal.semantic_dispatch",
    } <= set(registry.capability_ids)
    assert registry.require("speech.preload").owner_visibility == "internal"
    assert registry.require("apple.workbench.workflow").owner_visibility == "future"
