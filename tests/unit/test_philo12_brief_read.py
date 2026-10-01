"""PHILO-12-01 -- the brief projection keeps the exact stored id.

The Floor can open a brief after a newer producer-day exists.  These fences use
the real MeetingWebServer and its authenticated HTTP client, with the producer
clock moved by the test rather than by the machine clock.  The parameter route
is registered last so the existing ``latest`` and ``shelf`` routes remain
reachable.
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot


DAY_ONE = datetime.datetime(2026, 9, 28, 9, 30)


class MovableClock:
    def __init__(self, now: datetime.datetime) -> None:
        self.now = now

    def __call__(self) -> datetime.datetime:
        return self.now


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    clock = MovableClock(DAY_ONE)
    hub = _boot(tmp_path, monkeypatch, clock=clock)
    yield hub, clock
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_exact_id_read_keeps_an_older_brief_after_a_newer_brief_exists(rig) -> None:
    hub, clock = rig
    first_response = hub.client.post("/api/brief/generate")
    assert first_response.status_code == 200, first_response.text
    first = first_response.json()

    hub.db.desk_decisions.upsert(
        decision_id="philo12-read-decision",
        title="Use the exact brief id",
        status="proposed",
    )
    clock.now += datetime.timedelta(days=1)
    second_response = hub.client.post("/api/brief/generate")
    assert second_response.status_code == 200, second_response.text
    second = second_response.json()
    assert second["id"] != first["id"]

    exact = hub.client.get(f"/api/brief/{first['id']}")
    assert exact.status_code == 200, exact.text
    assert exact.json() == first
    assert hub.client.get("/api/brief/latest").json()["id"] == second["id"]


def test_unknown_exact_id_is_a_404_and_static_routes_keep_priority(rig) -> None:
    hub, _clock = rig
    generated = hub.client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text

    missing = hub.client.get("/api/brief/brief-does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["detail"] == "brief_not_found"

    latest = hub.client.get("/api/brief/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == generated.json()["id"]

    shelf = hub.client.get("/api/brief/shelf")
    assert shelf.status_code == 200
    assert shelf.json() == {}


def test_exact_id_route_requires_the_hub_authenticated_principal(rig) -> None:
    hub, _clock = rig
    generated = hub.client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text

    unauthenticated = TestClient(
        hub.server.app, client=("127.0.0.1", 50001), raise_server_exceptions=False
    )
    unauthenticated.headers.pop("x-holdspeak-token", None)
    unauthenticated.headers.pop("authorization", None)
    response = unauthenticated.get(f"/api/brief/{generated.json()['id']}")
    assert response.status_code == 401, response.text
    assert response.json()["error"] == "principal_right_required"
