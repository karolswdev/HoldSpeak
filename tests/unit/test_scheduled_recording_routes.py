"""HS-136-02: HTTP route tests for scheduled recording CRUD + cancel-armed.

Tests the full round-trip: create -> list -> get -> update -> cancel -> delete,
plus typed refusals for bad cron and non-positive duration.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database
from holdspeak.web.context import WebContext
from holdspeak.web.routes.scheduled_recordings import build_scheduled_recordings_router


@pytest.fixture()
def tmp_db(tmp_path: Path) -> Database:
    db = Database(db_path=tmp_path / "test.db")
    return db


@pytest.fixture()
def client(tmp_db: Database, monkeypatch: Any) -> TestClient:
    monkeypatch.setattr(
        "holdspeak.web.routes.scheduled_recordings.get_database", lambda: tmp_db
    )
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})
    app.include_router(build_scheduled_recordings_router(ctx))
    return TestClient(app)


class TestScheduledRecordingRoutes:
    """CRUD + cancel-armed over HTTP, each with a scoped route test."""

    def test_list_empty(self, client: TestClient) -> None:
        resp = client.get("/api/scheduled-recordings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["schedules"] == []

    def test_create_and_list(self, client: TestClient) -> None:
        # Create
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Standup",
            "cron_expr": "0 9 * * 1",
            "duration_minutes": 30,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        sched = body["schedule"]
        assert sched["title"] == "Standup"
        assert sched["cron_expr"] == "0 9 * * 1"
        assert sched["duration_minutes"] == 30
        assert sched["enabled"] is False
        assert "receipt_id" in sched
        schedule_id = sched["id"]

        # List
        resp = client.get("/api/scheduled-recordings")
        assert resp.status_code == 200
        schedules = resp.json()["schedules"]
        assert len(schedules) == 1
        assert schedules[0]["id"] == schedule_id

    def test_get(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Weekly",
            "cron_expr": "0 10 * * 1",
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.get(f"/api/scheduled-recordings/{schedule_id}")
        assert resp.status_code == 200
        assert resp.json()["schedule"]["title"] == "Weekly"

    def test_get_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/scheduled-recordings/sr_nonexistent")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert body["code"] == "not_found"

    def test_update(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Daily",
            "cron_expr": "0 8 * * *",
            "duration_minutes": 60,
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.patch(f"/api/scheduled-recordings/{schedule_id}", json={
            "title": "Morning Daily",
            "duration_minutes": 45,
        })
        assert resp.status_code == 200
        sched = resp.json()["schedule"]
        assert sched["title"] == "Morning Daily"
        assert sched["duration_minutes"] == 45

    def test_update_not_found(self, client: TestClient) -> None:
        resp = client.patch("/api/scheduled-recordings/sr_ghost", json={
            "title": "Nope",
        })
        assert resp.status_code == 404

    def test_delete(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "ToDelete",
            "cron_expr": "0 12 * * 5",
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.delete(f"/api/scheduled-recordings/{schedule_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["deleted"] is True
        assert "receipt_id" in body

        # Verify deleted
        resp = client.get(f"/api/scheduled-recordings/{schedule_id}")
        assert resp.status_code == 404

    def test_delete_not_found(self, client: TestClient) -> None:
        resp = client.delete("/api/scheduled-recordings/sr_phantom")
        assert resp.status_code == 404

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


class TestScheduledRecordingValidation:
    """Typed refusals for bad input: bad cron -> 422, non-positive duration -> 422."""

    def test_bad_cron_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Bad cron",
            "cron_expr": "not a cron",
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["code"] == "invalid_cron"

    def test_empty_cron_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "No cron",
            "cron_expr": "",
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "invalid_cron"

    def test_non_positive_duration_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Zero dur",
            "cron_expr": "0 9 * * 1",
            "duration_minutes": 0,
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "invalid_duration"

    def test_negative_duration_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Neg dur",
            "cron_expr": "0 9 * * 1",
            "duration_minutes": -5,
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "invalid_duration"

    def test_bad_cron_on_update_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Valid",
            "cron_expr": "0 9 * * 1",
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.patch(f"/api/scheduled-recordings/{schedule_id}", json={
            "cron_expr": "xxx",
        })
        assert resp.status_code == 422
        assert resp.json()["code"] == "invalid_cron"

    def test_non_positive_duration_on_update_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Valid",
            "cron_expr": "0 9 * * 1",
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.patch(f"/api/scheduled-recordings/{schedule_id}", json={
            "duration_minutes": 0,
        })
        assert resp.status_code == 422
        assert resp.json()["code"] == "invalid_duration"


class TestScheduledRecordingDelegation:
    """Enabling a schedule writes the bounded-delegation receipt."""

    def test_create_enabled_writes_delegation_receipt(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Enabled",
            "cron_expr": "0 9 * * 1",
            "duration_minutes": 60,
            "enabled": True,
        })
        assert resp.status_code == 201
        sched = resp.json()["schedule"]
        assert sched["enabled"] is True
        assert "delegation_receipt_id" in sched
        assert sched["delegation_receipt_id"].startswith("sr_rcpt_")
        # next_fire_at should be computed
        assert sched["next_fire_at"] is not None

    def test_enable_via_update_writes_delegation_receipt(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Disabled",
            "cron_expr": "0 9 * * 1",
            "enabled": False,
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.patch(f"/api/scheduled-recordings/{schedule_id}", json={
            "enabled": True,
        })
        assert resp.status_code == 200
        sched = resp.json()["schedule"]
        assert sched["enabled"] is True
        assert "delegation_receipt_id" in sched
        assert sched["delegation_receipt_id"].startswith("sr_rcpt_")


class TestScheduledRecordingCancelArmed:
    """Cancel-armed returns 409 when not armed (no live conductor)."""

    def test_cancel_not_armed_returns_409(self, client: TestClient, tmp_db: Database) -> None:
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Idle",
            "cron_expr": "0 9 * * 1",
        })
        schedule_id = resp.json()["schedule"]["id"]

        resp = client.post(f"/api/scheduled-recordings/{schedule_id}/cancel")
        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        # Not armed: state is 'idle', not 'arming'
        assert body["code"] == "not_armed"

    def test_cancel_not_found(self, client: TestClient) -> None:
        resp = client.post("/api/scheduled-recordings/sr_ghost/cancel")
        assert resp.status_code == 404

    def test_delete_while_arming_returns_409(self, client: TestClient, tmp_db: Database) -> None:
        """Cannot delete a schedule that is in 'arming' state."""
        resp = client.post("/api/scheduled-recordings", json={
            "title": "Arming",
            "cron_expr": "0 9 * * 1",
        })
        schedule_id = resp.json()["schedule"]["id"]

        # Manually set state to arming to test the guard
        tmp_db.scheduled_recordings.set_state(schedule_id, "arming")

        resp = client.delete(f"/api/scheduled-recordings/{schedule_id}")
        assert resp.status_code == 409
        assert resp.json()["code"] == "schedule_in_progress"
