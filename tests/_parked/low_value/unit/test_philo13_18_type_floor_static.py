# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_philo13_18_type_floor_static.py to restore.

# ruff: noqa


# --- test_every_glyph_exemption_is_still_a_live_declaration: P8: keeps a hand-kept exemption list tidy; no user outcome
def test_every_glyph_exemption_is_still_a_live_declaration() -> None:
    """The list only shrinks: a healed glyph line leaves the list."""
    live = {(p, sel) for p, _n, _px, sel in under_floor()}
    stale = sorted(GLYPHS - live)
    assert not stale, f"glyph exemptions with no sub-12 declaration left (remove them): {stale}"
