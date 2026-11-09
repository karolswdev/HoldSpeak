# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_desk_seed.py to restore.

# ruff: noqa


# --- test_mode_recipe_census_matches_its_authoritative_source: P2: checks the test's own hand-kept census against the constant it copies
def test_mode_recipe_census_matches_its_authoritative_source() -> None:
    """HS-200-03: the census above is regenerated, never hand-maintained.

    `MODE_SEEDS` is what `seed_modes` actually applies. When the two disagree
    the fixture is stale, and that staleness used to surface as two red seed
    tests rather than as the one-line census edit it is.
    """
    from holdspeak.services.thread_modes import MODE_SEEDS

    assert {mode.id for mode in MODE_SEEDS} == MODE_RECIPES
