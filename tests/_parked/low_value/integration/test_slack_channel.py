# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_slack_channel.py to restore.

# ruff: noqa


# --- test_legacy_slack_connector_is_removed: P8: asserts a removed function stays absent (hasattr); a phase-era rule, no user outcome
def test_legacy_slack_connector_is_removed() -> None:
    import holdspeak.slack_export as slack_export

    assert not hasattr(slack_export, "build_slack_connector")
    assert document_markdown_for(
        {"meeting_title": "A meeting", "meeting_date": "2026-09-30", "is_empty": False},
        "digest",
    ).startswith("# A meeting")
