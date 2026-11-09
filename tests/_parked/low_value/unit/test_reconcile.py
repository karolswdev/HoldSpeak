# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_reconcile.py to restore.

# ruff: noqa


# --- test_reference_schema_contains_canonical_tables: P6: the reference schema has >=100 tables and three names
def test_reference_schema_contains_canonical_tables() -> None:
    """The in-memory reference DB has the expected table count."""
    ref = _build_reference_schema()
    assert len(ref) >= 100, f"Expected many tables, got {len(ref)}"
    assert "meetings" in ref
    assert "schema_version" in ref
    assert "decisions" in ref
