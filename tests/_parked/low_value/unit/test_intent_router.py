# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intent_router.py to restore.

# ruff: noqa


# --- test_available_profiles_include_balanced_and_domain_profiles: P1: asserts five literal names are in a constant profile list
def test_available_profiles_include_balanced_and_domain_profiles() -> None:
    profiles = available_profiles()
    assert "balanced" in profiles
    assert "architect" in profiles
    assert "delivery" in profiles
    assert "product" in profiles
    assert "incident" in profiles
