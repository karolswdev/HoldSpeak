# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_web_slack_export.py to restore.

# ruff: noqa


# --- test_old_meeting_export_route_is_parked: P5/P8: the parked export route is checked (with no-post) in test_slack_channel::test_posture_aftercare_route_is_parked_and_never_posts; a removed route answers 404
def test_old_meeting_export_route_is_parked(client: TestClient) -> None:
    response = client.post(
        "/api/meetings/any-meeting/export/slack", json={"what": "digest"}
    )
    assert response.status_code == 400
    assert response.json() == {"success": False, "error": "slack_moved_to_channel"}
    assert URL not in response.text


# --- test_old_secret_operation_is_absent: P5/P8: the parked export route is checked (with no-post) in test_slack_channel::test_posture_aftercare_route_is_parked_and_never_posts; a removed route answers 404
def test_old_secret_operation_is_absent(client: TestClient) -> None:
    response = client.put(
        "/api/settings/secrets/slack_webhook_url", json={"value": URL}
    )
    assert response.status_code == 404
    assert URL not in response.text
