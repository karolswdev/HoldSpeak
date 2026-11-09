# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_product_copy.py to restore.

# ruff: noqa


# --- test_every_declared_primary_surface_expands_and_is_classified: P1/P6: re-states the copy contract's own tuples, counts the inventory (>=250) and its client names; the drift fence and rule cases stay
def test_every_declared_primary_surface_expands_and_is_classified() -> None:
    paths = list(iter_surface_paths(REPO))
    assert paths
    assert {client for client, _ in paths} == {
        "web",
        "swift",
        "hub",
        "cli_and_guides",
    }
    assert len(paths) == len(set(paths))

    candidates = inventory(REPO)
    assert len(candidates) >= 250
    assert {candidate.client for candidate in candidates} == {
        "web",
        "swift",
        "hub",
        "cli_and_guides",
    }
    assert {candidate.classification for candidate in candidates} <= COPY_CLASSIFICATIONS
    assert {candidate.classification for candidate in candidates} <= set(
        PRODUCT_LANGUAGE.copy_contract.classifications
    )


# --- test_copy_contract_covers_postures_failures_and_bounded_exceptions: P1/P6: re-states the copy contract's own tuples, counts the inventory (>=250) and its client names; the drift fence and rule cases stay
def test_copy_contract_covers_postures_failures_and_bounded_exceptions() -> None:
    contract = PRODUCT_LANGUAGE.copy_contract
    assert contract.generic_consequential_verbs == (
        "Approve",
        "Apply",
        "Open",
        "Run",
    )
    assert contract.failure_requirements == (
        "failed_operation",
        "retained_work",
        "next_action",
        "destination_when_relevant",
    )
    assert {pattern.id for pattern in contract.prohibited_operational_patterns} == {
        "legacy-product-nouns",
        "raw-control-mode-labels",
        "unqualified-state",
        "promotional-narration",
        "paired-as-local",
    }
    exception_ids: set[str] = set()
    for exception in contract.exceptions:
        exception_id = str(exception["id"])
        assert exception_id not in exception_ids
        exception_ids.add(exception_id)
        assert str(exception["path"]).endswith((".swift", ".tsx", ".md"))
        # HS-100-10: an exception carries literals OR terms (a staged
        # vocabulary migration names whole words instead).
        assert exception.get("literals") or exception.get("terms")
        assert len(str(exception["reason"]).strip()) >= 40


# --- test_inventory_contains_shared_product_language_in_real_surfaces: P1/P6: re-states the copy contract's own tuples, counts the inventory (>=250) and its client names; the drift fence and rule cases stay
def test_inventory_contains_shared_product_language_in_real_surfaces() -> None:
    values = {(item.client, item.text) for item in inventory(REPO)}
    assert ("web", "Secure") in values
    assert ("web", "Normal") in values
    assert ("swift", "Secure") in values
    assert ("swift", "Normal") in values
    assert any(client == "web" and "Engines" in text for client, text in values)
    assert any(client == "swift" and "Coder session" in text for client, text in values)
