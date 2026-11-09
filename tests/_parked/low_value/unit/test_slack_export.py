# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_slack_export.py to restore.

# ruff: noqa


# --- test_old_slack_connector_is_not_exported: P8: asserts a removed function name stays removed (hasattr)
def test_old_slack_connector_is_not_exported():
    import holdspeak.slack_export as slack_export

    assert not hasattr(slack_export, "build_slack_connector")
