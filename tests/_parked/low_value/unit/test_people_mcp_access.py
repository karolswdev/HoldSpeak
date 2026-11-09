# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_people_mcp_access.py to restore.

# ruff: noqa


# --- test_the_default_is_on: P1: asserts a config default literal
def test_the_default_is_on(config_file) -> None:
    assert access_source({}) == ("write", "default")
    from holdspeak.config import Config

    assert Config().people.mcp_access == "write"
