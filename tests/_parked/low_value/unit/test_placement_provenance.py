# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_placement_provenance.py to restore.

# ruff: noqa


# --- test_placement_dict_source_vocabulary: P1/P5: re-types the PLACEMENT_SOURCES tuple (also in the resolver file)
def test_placement_dict_source_vocabulary():
    """placement_dict source is always one of PLACEMENT_SOURCES."""
    assert set(PLACEMENT_SOURCES) == {"invocation", "workbench", "agent", "global"}
