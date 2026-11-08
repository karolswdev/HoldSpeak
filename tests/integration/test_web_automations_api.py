"""Owner web API coverage for an Automation's event starts and its resourceful policy."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.db import Database, reset_database
from holdspeak.db import core as db_module
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


def test_workbench_preset_facade_baselines_enables_tests_and_shows_history(
    client: TestClient, automations_db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The workbench automation routes, since 2026-11-08 over WatchService:
    a new event start is a watch, read (the quiet baseline) and on at once;
    test reads without moving the baseline; a new PR in the review queue is
    one review request, one Program run and one history row."""
    from holdspeak.services import program_prompt
    from holdspeak.services.watch_service import AUTOMATION_INTENT_PREFIX

    rows = {"now": [{"number": 23, "title": "Review me", "state": "open"}]}
    monkeypatch.setattr(
        "holdspeak.services.watch_sources.fetch_watch_snapshot",
        lambda *args, **kwargs: rows["now"],
    )
    ran: list = []

    # 2026-11-08: the start runs a Program of one prompt step; its model call is the seam.
    monkeypatch.setenv("HOLDSPEAK_PROGRAMS", "off")

    def fake_run(_runner, _program, step, **_kwargs):  # noqa: ANN001
        ran.append(step["id"])
        program_prompt.release(step["id"])

    monkeypatch.setattr(program_prompt, "run_claimed", fake_run)
    missing_repo = client.post("/api/workbenches/wb-review/automations", json={
        "preset_id": "github-review-requested",
    })
    assert missing_repo.status_code == 400

    created = client.post("/api/workbenches/wb-review/automations", json={
        "preset_id": "github-review-requested", "repository": "acme/widget",
    })
    assert created.status_code == 201, created.text
    automation = created.json()["automation"]
    automation_id = automation["id"]
    watch = automations_db.automations.get_watch(automation_id)
    assert watch["intent"] == AUTOMATION_INTENT_PREFIX + "wb-review"
    assert automations_db.automations.list_reactions() == []
    assert (automation["enabled"], automation["status"]) == (True, "active")
    assert automation["provider"] == "github"
    assert automation["repository"] == "acme/widget"
    assert automation["event_kind"] == "github.pr.review_requested"
    baseline = watch["snapshot"]

    tested = client.post(f"/api/workbenches/wb-review/automations/{automation_id}/test")
    assert tested.status_code == 200, tested.text
    assert automations_db.automations.get_watch(automation_id)["snapshot"] == baseline

    listed = client.get("/api/workbenches/wb-review/automations").json()["automations"]
    assert [row["id"] for row in listed] == [automation_id]

    paused = client.patch(
        f"/api/workbenches/wb-review/automations/{automation_id}", json={"enabled": False},
    )
    assert paused.status_code == 200 and paused.json()["automation"]["enabled"] is False
    enabled = client.patch(
        f"/api/workbenches/wb-review/automations/{automation_id}", json={"enabled": True},
    )
    assert enabled.status_code == 200
    assert enabled.json()["automation"]["status"] == "active"

    rows["now"] = rows["now"] + [{"number": 24, "title": "Second review", "state": "open"}]
    evaluated = client.post(f"/api/watches/{automation_id}/evaluate")
    assert evaluated.status_code == 200, evaluated.text
    assert len(ran) == 1

    history = client.get(f"/api/workbenches/wb-review/automations/{automation_id}/history")
    assert history.status_code == 200
    [entry] = history.json()["history"]
    assert entry["id"] == ran[0]
    assert entry["outcome"] == "added"
    assert entry["event_kind"] == "github.pr.review_requested"


def test_automations_routes_require_the_owner_principal(client: TestClient) -> None:
    client.headers.pop("x-holdspeak-token", None)

    response = client.get("/api/workbenches/wb-review/automations")

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


def test_jira_watch_adapter_status_is_ready() -> None:
    """Counsel S-1 (HS-166-07): jira graduated the watch_sources gate, so the
    automations read model must not call its adapter unavailable."""
    from holdspeak.web.routes.automations import _watch_automation_view

    jira = _watch_automation_view({"id": "w1", "connector_id": "jira", "state": "active"})
    assert jira["provider"] == "jira"
    assert jira["adapter_status"] == "ready"
    assert jira["status"] == "active"
    custom = _watch_automation_view({"id": "w2", "connector_id": "custom", "state": "active"})
    assert custom["adapter_status"] == "unavailable"
    assert custom["status"] == "unavailable"
