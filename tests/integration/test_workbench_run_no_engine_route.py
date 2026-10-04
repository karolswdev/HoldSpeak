"""Run on a workbench with no engine is a named refusal, never an HTTP 500.

Scar (inventory 2026-10-03): the hub answered `POST /api/workbenches/{id}/run`
with HTTP 500 when no model assignment existed. The face printed
"RUN FAILED · HTTP 500" and the reason stayed on the server.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.db import get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def client(tmp_path):
    reset_database()
    get_database(tmp_path / "holdspeak.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    yield TestClient(server.app)
    reset_database()


def test_run_with_no_engine_is_a_named_409(client) -> None:
    recipe = client.post("/api/recipes", json={"name": "Chase", "system_prompt": "Do the work."})
    assert recipe.status_code in (200, 201), recipe.text
    recipe_id = recipe.json()["recipe"]["id"]
    bench = client.post("/api/workbenches", json={"name": "Cutover bench", "recipe_id": recipe_id})
    assert bench.status_code in (200, 201), bench.text
    bench_id = bench.json()["workbench"]["id"]
    item = client.post(f"/api/workbenches/{bench_id}/items", json={"title": "Draft the runbook"})
    assert item.status_code in (200, 201), item.text

    run = client.post(f"/api/workbenches/{bench_id}/run", json={})

    assert run.status_code == 409, run.text
    body = run.json()
    assert body["code"] == "no_assignment"
    assert body["error"] == "No engine is set for this workbench."
    # Nothing ran and nothing was spent: the item is still pending.
    items = client.get(f"/api/workbenches/{bench_id}").json()
    statuses = [row["status"] for row in items["workbench"]["items"]]
    assert statuses == ["pending"]


def _bench(client) -> str:
    recipe_id = client.post("/api/recipes", json={"name": "Chase", "system_prompt": "Do the work."}).json()["recipe"]["id"]
    return client.post("/api/workbenches", json={"name": "Cutover bench", "recipe_id": recipe_id}).json()["workbench"]["id"]


def test_the_window_fact_is_the_assignment_resolved_for_this_workbench(client) -> None:
    """The face ghosts Run on `assignment_summary`; it must see a workbench-level
    assignment (Astra, PR #779 P1: the editor's `effective` omits the subject)."""
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    bench_id = _bench(client)
    before = client.get(f"/api/workbenches/{bench_id}").json()["workbench"]["assignment_summary"]
    assert before["status"] == "no_assignment"

    # A real model profile with a deployment, and a real subject-scope
    # assignment, through the producers the assignment suite uses.
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, _set

    db = get_database()
    _profile(db, "bench-engine", claims=("language", _result_claim("workbench.item")))
    scope = {
        "kind": "subject", "subject_kind": "workbench", "subject_id": bench_id,
        "capability_id": "workbench.item",
    }
    _set(InferenceAssignmentService(db), "bench-engine-set", scope, "bench-engine")

    after = client.get(f"/api/workbenches/{bench_id}").json()["workbench"]["assignment_summary"]
    assert after["status"] == "assigned"
    assert after["source"] == "subject"
    # No capability, group or global assignment exists: the editor's
    # subject-blind `effective` still says no_assignment. The face must not read it.
    editor = client.post(
        "/api/inference/assignments/editor",
        json={"scope": scope, "capability_id": "workbench.item"},
    ).json()
    assert editor["effective"]["status"] == "no_assignment"
    # And the runner agrees with the summary: Run is no longer refused for no engine.
    client.post(f"/api/workbenches/{bench_id}/items", json={"title": "Draft the runbook"})
    run = client.post(f"/api/workbenches/{bench_id}/run", json={})
    assert not (run.status_code == 409 and run.json().get("code") == "no_assignment"), run.text
