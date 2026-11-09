# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_one_path_provenance.py to restore.

# ruff: noqa


# --- test_the_provenance_matrix_covers_every_named_surface: P1/P8: asserts a hand-kept driver table has 10 entries and a literal name set
def test_the_provenance_matrix_covers_every_named_surface() -> None:
    """The parametrization above is the whole fence, not a sample of it.

    DESIGN-HS-131-10.md §2 and Sol's open-question ruling 3 require all FIFTEEN
    named entry forms. This is the guard against the matrix quietly shrinking
    back to a convenient subset.
    """
    # HS-151-02: Recipe chat retired (was 16); 2026-11-08: Sequence and
    # Workflow parked with their runner (was 15), and the item queue (manual
    # and scheduled Workbench, memory writeback) parked (was 13).
    assert len(SURFACE_DRIVERS) == 10
    assert ROOT_SHAPED_SURFACES | CHILD_SHAPED_SURFACES == set(SURFACE_DRIVERS)
    assert set(SURFACE_DRIVERS) == {
        "Ask", "Recipe run",
        "Rails",
        "Decision promotion", "Delivery review", "voice", "meeting live",
        "meeting deferred", "dictation pipeline",
        # HS-131-13's migration; the story's other two families were deleted as
        # duplicates of "Decision promotion" and "Delivery review" above.
        "cadence next action",
    }
