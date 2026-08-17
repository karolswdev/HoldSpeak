"""Owner web API coverage for Watches, service events, and Reactions."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.db import Database, reset_database
from holdspeak.db import core as db_module
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.service_event_ledger import ServiceEventLedger
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

pytestmark = [pytest.mark.requires_meeting]


@pytest.fixture
def automations_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    reset_database()
    db_path = tmp_path / "automations-web.db"
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", db_path)
    database = Database(db_path)
    recipe = database.recipes.upsert(recipe_id="recipe-review", name="Reviewer")
    database.workbenches.upsert(
        workbench_id="wb-review", name="Review queue", recipe_id=recipe.id,
    )
    yield database
    reset_database()


@pytest.fixture
def client(automations_db: Database) -> TestClient:
    del automations_db
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


def test_owner_can_test_and_baseline_a_watch_without_client_snapshots(
    client: TestClient, automations_db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "holdspeak.services.watch_sources.fetch_watch_snapshot",
        lambda *args, **kwargs: [{"number": 17, "title": "Ship it", "state": "open"}],
    )
    created = client.post("/api/automations/watches", json={
        "connector_id": "github", "query_kind": "pull_requests",
        "name": "My requested reviews", "query": {"repository": "acme/widget"},
        "watch_id": "watch-review",
    })
    assert created.status_code == 201
    assert created.json()["watch"]["connector_id"] == "gh"

    paused = client.put("/api/automations/watches/watch-review/enabled", json={"enabled": False})
    assert paused.status_code == 200
    assert paused.json()["watch"]["enabled"] is False
    enabled = client.put("/api/automations/watches/watch-review/enabled", json={"enabled": True})
    assert enabled.status_code == 200

    tested = client.post("/api/automations/watches/watch-review/test")
    assert tested.status_code == 200
    assert tested.json()["baseline"] is True
    assert automations_db.automations.get_watch("watch-review")["snapshot"] == {}

    baseline = client.post("/api/automations/watches/watch-review/baseline")
    assert baseline.status_code == 200
    assert baseline.json()["baseline"] is True
    assert baseline.json()["events"] == []

    reaction = client.post("/api/automations/reactions", json={
        "reaction_id": "reaction-review", "watch_id": "watch-review",
        "event_pattern": "github.pr.review_requested", "workbench_id": "wb-review",
        "enabled": False,
    })
    assert reaction.status_code == 201
    assert reaction.json()["reaction"]["enabled"] is False
    enabled_reaction = client.put(
        "/api/automations/reactions/reaction-review/enabled", json={"enabled": True},
    )
    assert enabled_reaction.status_code == 200

    event = ServiceEventLedger(automations_db).append(
        Principal(PrincipalKind.OWNER, "test-owner"),
        event_type="github.pr.review_requested", producer="connector.gh.watch",
        subject_ref="gh:pull_requests:17", source_revision="v2",
        facts={"entity_title": "Ship it"}, refs=["watch:watch-review"],
    )

    watches = client.get("/api/automations/watches")
    assert watches.status_code == 200
    assert watches.json()["watches"][0]["last_success_at"]
    events = client.get("/api/automations/events?event_type=github.pr.review_requested")
    assert events.status_code == 200
    assert len(events.json()["events"]) == 1
    assert events.json()["events"][0]["id"] == event["id"]
    reactions = client.get("/api/automations/reactions")
    assert reactions.status_code == 200
    assert reactions.json()["reactions"][0]["id"] == "reaction-review"

    process = client.post("/api/automations/reactions/process", json={"limit": 10})
    assert process.status_code == 200
    assert process.json()["projections"][0]["reaction_id"] == "reaction-review"


def test_workbench_preset_facade_baselines_enables_tests_and_shows_history(
    client: TestClient, automations_db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "holdspeak.services.watch_sources.fetch_watch_snapshot",
        lambda *args, **kwargs: [{"number": 23, "title": "Review me", "state": "open"}],
    )
    presets = client.get("/api/automations/presets")
    assert presets.status_code == 200
    assert presets.json()["presets"][0]["id"] == "github-review-requested"

    missing_repo = client.post("/api/workbenches/wb-review/automations", json={
        "preset_id": "github-review-requested",
    })
    assert missing_repo.status_code == 400

    created = client.post("/api/workbenches/wb-review/automations", json={
        "preset_id": "github-review-requested", "repository": "acme/widget",
    })
    assert created.status_code == 201
    automation = created.json()["automation"]
    automation_id = automation["id"]
    stored_reaction = automations_db.automations.get_reaction(automation_id)
    assert stored_reaction is not None
    watch_id = stored_reaction["watch_id"]
    assert stored_reaction["auto_run"] is False
    assert automation["enabled"] is False
    assert automation["provider"] == "github"
    assert automation["repository"] == "acme/widget"

    tested = client.post(f"/api/workbenches/wb-review/automations/{automation_id}/test")
    assert tested.status_code == 200
    assert tested.json()["baseline"] is True
    assert automations_db.automations.get_watch(watch_id)["snapshot"] == {}

    enabled = client.patch(
        f"/api/workbenches/wb-review/automations/{automation_id}", json={"enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["automation"]["enabled"] is True
    assert enabled.json()["automation"]["status"] == "active"
    assert automations_db.automations.get_watch(watch_id)["enabled"] is True
    assert automations_db.automations.get_reaction(automation_id)["enabled"] is True

    event = ServiceEventLedger(automations_db).append(
        Principal(PrincipalKind.OWNER, "test-owner"),
        event_type="github.pr.review_requested", producer="connector.gh.watch",
        subject_ref="gh:pull_requests:23", source_revision="v2",
        facts={"entity_title": "Review me"}, refs=[f"watch:{watch_id}"],
    )
    processed = client.post("/api/automations/reactions/process")
    assert processed.status_code == 200
    assert processed.json()["projections"][0]["reaction_id"] == automation_id

    history = client.get(f"/api/workbenches/wb-review/automations/{automation_id}/history")
    assert history.status_code == 200
    entry = history.json()["history"][0]
    assert event["id"] in entry["id"]
    assert entry["outcome"] == "added"
    assert entry["event_kind"] == "github.pr.review_requested"


def test_automations_routes_require_the_owner_principal(client: TestClient) -> None:
    client.headers.pop("x-holdspeak-token", None)

    response = client.get("/api/automations/watches")

    assert response.status_code == 401
    assert response.json()["error"] == "principal_right_required"


def test_owner_can_enable_six_hour_two_per_night_resourcefulness(
    client: TestClient,
) -> None:
    initial = client.get("/api/workbenches/wb-review/resourceful")
    assert initial.status_code == 200
    assert initial.json()["policy"]["cooldown_hours"] == 6
    assert initial.json()["policy"]["nightly_target"] == 2

    configured = client.put("/api/workbenches/wb-review/resourceful", json={
        "enabled": True,
        "idle_after_minutes": 30,
        "cooldown_hours": 6,
        "nightly_target": 2,
        "night_only": True,
        "night_start_hour": 22,
        "night_end_hour": 7,
        "routines": ["loose_ideas", "failed_work"],
    })

    assert configured.status_code == 200
    policy = configured.json()["policy"]
    assert policy["enabled"] is True
    assert policy["routines"] == ["loose_ideas", "failed_work"]
    assert client.get("/api/workbenches/wb-review/resourceful/history").json() == {
        "history": []
    }
