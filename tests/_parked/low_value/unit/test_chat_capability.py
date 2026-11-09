# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_chat_capability.py to restore.

# ruff: noqa


# --- test_chat_turn_seals_in_registry: P1: reads label, group and source-module constants off the registry
def test_chat_turn_seals_in_registry() -> None:
    """chat.turn is present in the sealed registry."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.turn")
    assert definition.id == "chat.turn"
    assert definition.label == "Desk chat"
    assert definition.group_id == "thoughts_notes"
    assert definition.output_kind == "chat_turn_answer"
    assert definition.source_module == "holdspeak.services.thread_service"


# --- test_chat_turn_is_assignable: P1: reads label, group and source-module constants off the registry
def test_chat_turn_is_assignable() -> None:
    """chat.turn has owner visibility (not future/internal)."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    definition = registry.require("chat.turn")
    assert definition.owner_visibility == "owner"


# --- test_recipe_chat_raises_unknown_in_registry: P8: phase-era removal fence (recipe.chat gone); the backfill tests cover the migration
def test_recipe_chat_raises_unknown_in_registry() -> None:
    """recipe.chat is no longer in the sealed registry."""
    registry = InferenceCapabilityRegistry.compose(
        capabilities=builtin_capability_definitions(),
        retry_policies=builtin_retry_policy_definitions(),
    )
    with pytest.raises(UnknownInferenceCapability, match="recipe.chat"):
        registry.require("recipe.chat")
