# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_philo9_03_receipt_scope.py to restore.

# ruff: noqa


# --- test_mutation_a_producer_without_a_declaration_is_caught: P2: tests the test's own census helper
def test_mutation_a_producer_without_a_declaration_is_caught() -> None:
    mutated = dict(ps._RECEIPT_SCOPE)
    mutated.pop("create_item")
    assert census(mutated) == ["create_item: no project-identity declaration"]
