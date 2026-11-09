"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/integration/test_web_activity_api.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


def test_activity_project_rule_api_creates_previews_updates_and_deletes(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    activity_db.projects.create_project(project_id="holdspeak", name="HoldSpeak")
    activity_db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://example.atlassian.net/browse/HS-123",
        title="HS-123 mapping",
        domain="example.atlassian.net",
        last_seen_at=datetime(2026, 4, 26, 12, 0),
        entity_type="jira_ticket",
        entity_id="HS-123",
    )

    create_response = test_client.post(
        "/api/activity/project-rules",
        json={
            "project_id": "holdspeak",
            "name": "HoldSpeak Jira",
            "match_type": "entity_id_prefix",
            "entity_type": "jira_ticket",
            "pattern": "HS-",
            "priority": 200,
            "enabled": True,
        },
    )
    assert create_response.status_code == 200
    rule = create_response.json()["rule"]
    assert rule["project_name"] == "HoldSpeak"

    preview_response = test_client.post(
        "/api/activity/project-rules/preview",
        json={
            "project_id": "holdspeak",
            "match_type": "entity_id_prefix",
            "entity_type": "jira_ticket",
            "pattern": "HS-",
        },
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["count"] == 1
    assert preview_response.json()["matches"][0]["entity_id"] == "HS-123"

    update_response = test_client.put(
        f"/api/activity/project-rules/{rule['id']}",
        json={"enabled": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["rule"]["enabled"] is False

    delete_response = test_client.delete(f"/api/activity/project-rules/{rule['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True


def test_activity_meeting_candidate_api_persists_lists_and_deletes(
    test_client: TestClient,
    activity_db: Database,
) -> None:
    record = activity_db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://outlook.office.com/calendar/item/customer-sync",
        title="Customer sync meeting",
        domain="outlook.office.com",
        last_seen_at=datetime(2026, 4, 27, 9, 0),
    )
    body = {
        "source_connector_id": "calendar_activity",
        "source_activity_record_id": record.id,
        "title": "Customer sync meeting",
        "meeting_url": record.url,
        "confidence": 0.8,
    }

    create_response = test_client.post("/api/activity/meeting-candidates", json=body)
    assert create_response.status_code == 200
    candidate = create_response.json()["candidate"]
    assert candidate["status"] == "candidate"
    duplicate_response = test_client.post(
        "/api/activity/meeting-candidates",
        json={**body, "title": "Customer sync meeting updated", "confidence": 0.9},
    )
    assert duplicate_response.status_code == 200
    duplicate = duplicate_response.json()["candidate"]
    assert duplicate["id"] == candidate["id"]
    assert duplicate["title"] == "Customer sync meeting updated"

    list_response = test_client.get("/api/activity/meeting-candidates")
    assert list_response.status_code == 200
    assert list_response.json()["count"] == 1

    delete_response = test_client.delete("/api/activity/meeting-candidates?status=candidate")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] == 1
