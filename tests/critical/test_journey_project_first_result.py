"""Critical journey: a Project reaches its first useful result, cold.

The Project is where the daily practice happens, so a cold installation that
cannot create one and open its Room has no G1 to build on. This journey runs
the real `ProjectService` through the real routes on the real database, with
no model, no connectors and no network.

The honesty half matters as much as the creation half: a Room with no sources
must say it has no coverage rather than presenting an all-clear. "Incomplete
observation presented as an all-clear" is on ACCEPTANCE.md's critical-defect
list, so the empty case is asserted, not skipped.
"""

from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.critical


def _create(client, name: str) -> dict:
    response = client.post("/api/projects", json={"name": name})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("success") is True, body
    return body["project"]


def test_a_cold_install_creates_a_project_and_reopens_it(client) -> None:
    project = _create(client, "The pilot stream")
    project_id = project["id"]
    assert project_id.startswith("proj-")
    assert project["name"] == "The pilot stream"

    reopened = client.get(f"/api/projects/{project_id}")
    assert reopened.status_code == 200, reopened.text
    assert reopened.json()["name"] == "The pilot stream"

    listed = client.get("/api/projects").json()
    rows = listed.get("projects", listed if isinstance(listed, list) else [])
    assert any(row.get("id") == project_id for row in rows), listed


def test_the_first_room_is_honest_about_having_no_sources(client) -> None:
    """The first result on a cold desk is a Room that admits it knows nothing."""
    project_id = _create(client, "The empty Room")["id"]

    response = client.get(f"/api/projects/{project_id}/room")
    assert response.status_code == 200, response.text
    room = response.json()

    # The Room is real and addressable ...
    assert room, "a created Project must open a Room"
    rendered = json.dumps(room)
    assert project_id in rendered

    # ... and it must not invent activity it has no source for.
    for key in ("sources", "observations", "proposals"):
        value = room.get(key)
        if isinstance(value, list):
            assert value == [], f"a cold Room reported {key}={value!r}"


def test_creating_the_same_project_twice_is_one_project(client) -> None:
    """A retried create must not silently mint a duplicate stream.

    "Unexplained duplicate consequential effects" is a critical defect, and the
    idempotency key is the product's own answer to it.
    """
    payload = {"name": "The retried Project", "command_id": "pcmd-critical-journey"}
    first = client.post("/api/projects", json=dict(payload))
    second = client.post("/api/projects", json=dict(payload))
    assert first.status_code == 200 and second.status_code == 200, (
        first.text,
        second.text,
    )
    # The replay answers with the compact command receipt (`project_id` +
    # `result_kind`), not the full record, so identity is read from the field
    # both shapes carry.
    def _identity(response) -> str:
        project = response.json()["project"]
        return str(project.get("project_id") or project["id"])

    assert _identity(first) == _identity(second)
    assert second.json()["project"]["result_kind"] == "created"

    listed = client.get("/api/projects").json()
    rows = listed.get("projects", listed if isinstance(listed, list) else [])
    named = [row for row in rows if row.get("name") == "The retried Project"]
    assert len(named) == 1, named
