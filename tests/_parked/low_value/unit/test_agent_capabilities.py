# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_agent_capabilities.py to restore.

# ruff: noqa


# --- test_ledger_matches_the_pinned_matrix_exactly: P1/P8: a hand-pinned copy of the LEDGER constant compared cell by cell; the refusal tests below cover enforcement
def test_ledger_matches_the_pinned_matrix_exactly() -> None:
    assert set(LEDGER) == set(EXPECTED) == set(ADAPTERS)
    for adapter, row in EXPECTED.items():
        assert dict(LEDGER[adapter]) == row, adapter
        assert set(LEDGER[adapter]) == set(Capability), adapter


# --- test_every_cell_answers: P1/P8: a hand-pinned copy of the LEDGER constant compared cell by cell; the refusal tests below cover enforcement
@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("capability", list(Capability))
def test_every_cell_answers(adapter: str, capability: Capability) -> None:
    assert standing_for(adapter, capability) is EXPECTED[adapter][capability]
