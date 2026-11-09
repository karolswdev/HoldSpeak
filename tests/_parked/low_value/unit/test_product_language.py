# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_product_language.py to restore.

# ruff: noqa


# --- test_registry_is_versioned_complete_and_strict: P1/P8: pins the registry's version, labels and classification tuple as literals, and keeps a hand-kept exception list tidy
def test_registry_is_versioned_complete_and_strict() -> None:
    registry = load_product_language(REGISTRY_PATH)

    assert registry.version == 2
    # Betterment AG1 (DECISIONS #3): a saved persona is a Mode; "Agent" means
    # only a coding agent session (was HS-100-10: recipe -> Agent).
    assert registry.label("recipe") == "Mode"
    assert registry.label("agent", plural=True) == "Modes"
    assert registry.label("coder") == "Agent"
    assert registry.label("directory") == "Zone"
    assert registry.label("kb") == "Knowledge"
    assert registry.label("chain") == "Sequence"
    assert registry.label("profile") == "Engine"  # Betterment E6
    assert registry.label("connector") == "Integration"
    assert registry.destination_classes == tuple(DestinationClass)
    assert registry.decision_kinds == tuple(DecisionKind)
    assert registry.control_modes == tuple(ControlMode)
    assert registry.meeting_projections == (
        "summary",
        "action_items",
        "transcript",
        "topics",
    )
    assert registry.control_mode_label("safe") == "Secure"
    assert registry.control_mode_label("Normal") == "Normal"
    assert registry.control_mode_description("yolo").startswith("Runs eligible")
    assert registry.destination_label("paired_device") == "Paired device"
    assert registry.lifecycle_label("sync", "pending_sync") == "Pending sync"
    assert registry.copy_contract.version == 1
    assert registry.copy_contract.classifications == (
        "label",
        "state",
        "supporting_line",
        "detail",
        "error_recovery",
        "marketing_sdk_exception",
    )
    with pytest.raises(ProductLanguageError, match="unknown product-language term"):
        registry.label("generic_thing")
    with pytest.raises(ProductLanguageError, match="unknown sync lifecycle value"):
        registry.lifecycle_value("sync", "pending")


# --- test_compatibility_exceptions_are_explicit_and_bounded: P1/P8: pins the registry's version, labels and classification tuple as literals, and keeps a hand-kept exception list tidy
def test_compatibility_exceptions_are_explicit_and_bounded() -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    exceptions = raw["compatibility_exceptions"]
    assert exceptions
    ids = {exception["id"] for exception in exceptions}
    assert len(ids) == len(exceptions)
    for exception in exceptions:
        assert exception["path"].startswith(("holdspeak/", "web/", "apple/"))
        assert exception["registry_version"] == 2
        assert exception["kind"] in {"wire", "migration", "sdk"}
        assert not exception["path"].endswith("/**")
        assert exception["terms"]
        assert len(exception["reason"].strip()) >= 24
