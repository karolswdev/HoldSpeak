# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_scheduled_recording_routes.py to restore.

# ruff: noqa


# --- TestScheduledRecordingRoutes::test_full_round_trip: P5/P6: repeats the create/update/delete and zero-duration cases, and checks fields are str or None; the 9 am next-fire test stays
# (was a method of class TestScheduledRecordingRoutes)
def test_full_round_trip(self, client: TestClient) -> None:
    """Create -> list -> update -> delete full round-trip."""
    # Create
    resp = client.post("/api/scheduled-recordings", json={
        "title": "Retro",
        "cron_expr": "30 14 * * 5",
        "duration_minutes": 90,
        "one_shot": True,
    })
    assert resp.status_code == 201
    schedule_id = resp.json()["schedule"]["id"]

    # List
    resp = client.get("/api/scheduled-recordings")
    ids = [s["id"] for s in resp.json()["schedules"]]
    assert schedule_id in ids

    # Update
    resp = client.patch(f"/api/scheduled-recordings/{schedule_id}", json={
        "title": "Sprint Retro",
        "cron_expr": "0 15 * * 5",
    })
    assert resp.status_code == 200
    assert resp.json()["schedule"]["title"] == "Sprint Retro"

    # Delete
    resp = client.delete(f"/api/scheduled-recordings/{schedule_id}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


# --- TestScheduledRecordingValidation::test_negative_duration_returns_422: P5/P6: repeats the create/update/delete and zero-duration cases, and checks fields are str or None; the 9 am next-fire test stays
# (was a method of class TestScheduledRecordingValidation)
def test_negative_duration_returns_422(self, client: TestClient) -> None:
    resp = client.post("/api/scheduled-recordings", json={
        "title": "Neg dur",
        "cron_expr": "0 9 * * 1",
        "duration_minutes": -5,
    })
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "invalid_duration"


# --- TestScheduledRecordingTimestampSerialization::test_created_at_is_iso_string: P5/P6: repeats the create/update/delete and zero-duration cases, and checks fields are str or None; the 9 am next-fire test stays
# (was a method of class TestScheduledRecordingTimestampSerialization)
def test_created_at_is_iso_string(self, client: TestClient) -> None:
    resp = client.post("/api/scheduled-recordings", json={
        "title": "ISO check",
        "cron_expr": "0 9 * * 1",
    })
    assert resp.status_code == 201
    sched = resp.json()["schedule"]
    created = sched["created_at"]
    assert isinstance(created, str), f"created_at should be a string, got {type(created)}"
    # Must parse as a valid datetime (not a 1970 date from epoch-seconds)
    from datetime import datetime
    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
    assert dt.year >= 2026, f"created_at parsed to {dt} (expected recent date)"


# --- TestScheduledRecordingTimestampSerialization::test_all_timestamp_fields_are_strings_or_none: P5/P6: repeats the create/update/delete and zero-duration cases, and checks fields are str or None; the 9 am next-fire test stays
# (was a method of class TestScheduledRecordingTimestampSerialization)
def test_all_timestamp_fields_are_strings_or_none(self, client: TestClient) -> None:
    """Every timestamp field in the serialized dict is a string or None."""
    resp = client.post("/api/scheduled-recordings", json={
        "title": "Timestamp audit",
        "cron_expr": "0 9 * * 1",
        "enabled": True,
    })
    sched = resp.json()["schedule"]
    timestamp_fields = ["created_at", "next_fire_at", "last_fired_at", "armed_at", "deadline_at"]
    for field in timestamp_fields:
        val = sched.get(field)
        assert val is None or isinstance(val, str), (
            f"{field} should be str or None, got {type(val).__name__}: {val!r}"
        )
