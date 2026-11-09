# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_residual_service_admission.py to restore.

# ruff: noqa


# --- test_the_legacy_uncontextual_target_factory_no_longer_exists: P8: asserts removed functions stay removed (hasattr, signature and AST-name scans); no user outcome
def test_the_legacy_uncontextual_target_factory_no_longer_exists() -> None:
    """No factory, no shim, no re-export. Importing it must fail."""
    import holdspeak.inference_targets as targets

    assert not hasattr(targets, "build_intel_for_target")
    with pytest.raises(ImportError):
        from holdspeak.inference_targets import build_intel_for_target  # noqa: F401


# --- test_the_dormant_delivery_review_helper_no_longer_exists: P8: asserts removed functions stay removed (hasattr, signature and AST-name scans); no user outcome
def test_the_dormant_delivery_review_helper_no_longer_exists() -> None:
    from holdspeak.services.delivery_service import DeliveryService

    assert not hasattr(DeliveryService, "prepare_pr_review")


# --- test_the_decisions_route_holds_no_model_seam: P8: asserts removed functions stay removed (hasattr, signature and AST-name scans); no user outcome
def test_the_decisions_route_holds_no_model_seam() -> None:
    """The route may compose the service; it may not execute a model.

    Checked structurally rather than by grep-for-a-string: every call and every
    first-class reference in the module is inspected, so a renamed local or a
    bound method handed to a thread pool is caught as readily as a direct call.
    """
    source = (REPO / "holdspeak/web/routes/decisions.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        "build_intel_for_target", "build_intel_for_revision", "run_prompt",
        "build_configured_meeting_intel", "MeetingIntel", "_chat_completion_text",
    }
    named = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    assert not (named & forbidden), sorted(named & forbidden)
    assert "model_generator" not in source


# --- test_the_decision_service_no_longer_takes_a_model_generator: P8: asserts removed functions stay removed (hasattr, signature and AST-name scans); no user outcome
def test_the_decision_service_no_longer_takes_a_model_generator() -> None:
    """The injection point is gone, so a second Decision seam cannot be wired back."""
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

    parameters = inspect.signature(DecisionLifecycleService.__init__).parameters
    assert "model_generator" not in parameters
    assert set(parameters) == {"self", "db", "kernel", "observer"}


# --- test_the_cadence_service_constructs_no_engine_of_its_own: P8: asserts removed functions stay removed (hasattr, signature and AST-name scans); no user outcome
def test_the_cadence_service_constructs_no_engine_of_its_own() -> None:
    """Domain shaping stays; construction left. The service names no engine verb."""
    source = (REPO / "holdspeak/services/cadence_service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    named = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    assert not (named & {
        "build_configured_meeting_intel", "configured_meeting_intel", "run_prompt",
        "build_intel_for_target", "build_intel_for_revision", "MeetingIntel",
    }), sorted(named)
    # It DOES still own the domain half — the prompt and the validation — which is
    # what keeps the generic runner from branching on Cadence.
    assert "next_action_prompt" in source and "next_action_from_output" in source
