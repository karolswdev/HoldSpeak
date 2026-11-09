# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_web_activity_api.py to restore.

# ruff: noqa


# --- test_connector_dry_run_returns_uniform_shape_per_connector: P6: checks eleven key names per connector; the values are tested in tests/unit/test_activity_connector_preview.py
def test_connector_dry_run_returns_uniform_shape_per_connector(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    """HS-9-13: every connector returns the same dry-run payload shape."""
    activity_db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/anthropic/holdspeak/pull/7",
        title="PR 7",
        domain="github.com",
        last_seen_at=datetime(2026, 4, 28, 9, 0),
        entity_type="github_pull_request",
        entity_id="anthropic/holdspeak#7",
    )

    for connector_id in ("gh", "jira", "calendar_activity"):
        response = test_client.get(
            f"/api/activity/enrichment/connectors/{connector_id}/dry-run"
        )
        assert response.status_code == 200, response.text
        payload = response.json()["dry_run"]
        assert payload["connector_id"] == connector_id
        for key in (
            "kind",
            "capabilities",
            "enabled",
            "cli_required",
            "cli_available",
            "commands",
            "proposed_annotations",
            "proposed_candidates",
            "warnings",
            "permission_notes",
            "truncated",
        ):
            assert key in payload, f"missing key {key} for {connector_id}"
