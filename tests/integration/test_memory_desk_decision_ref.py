"""A decision made with Decide stays findable in its Project.

Inventory C, gap 1 (2026-10-03): the Decide button and the decision
window's filing strip filed a desk decision into a Project as
``decision:<id>``; memory's project filter read ``desk_decision:<id>``.
Project search, Ask's grounding and MCP with ``project_id`` lost it.

One ref name now: ``desk_decision:<id>``. A row stored under the old name
keeps working. Every case goes through the real routes and the real
grounding call; nothing is doubled.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.grounding import hydrate_refs_detailed
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


def _hub(tmp_path: Path, monkeypatch) -> tuple[TestClient, Database]:
    db = Database(tmp_path / "hub.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={"id": "desk-decision-ref"}),
        ),
        host="127.0.0.1",
        auth_token="owner-secret",
    )
    return TestClient(server.app), db


def _project(client: TestClient) -> str:
    made = client.post("/api/projects", json={"name": "Atlas"})
    assert made.status_code in (200, 201), made.text
    body = made.json()
    return str((body.get("project") or body)["id"])


def _decide(client: TestClient) -> str:
    made = client.post(
        "/api/decisions",
        json={"title": "Adopt quorumdb for the ledger", "status": "proposed"},
    )
    assert made.status_code == 201, made.text
    return str(made.json()["decision"]["id"])


def _project_hits(client: TestClient, project_id: str) -> list[str]:
    found = client.get(
        "/api/memory/search", params={"query": "quorumdb", "project_id": project_id}
    )
    assert found.status_code == 200, found.text
    return [hit["source_ref"] for hit in found.json()["hits"]]


@pytest.mark.parametrize("sent_kind", ["desk_decision", "decision"])
def test_decide_then_project_memory_and_ask_grounding_find_it(
    tmp_path: Path, monkeypatch, sent_kind: str
) -> None:
    """`desk_decision:` is what Decide sends now; `decision:` is what the
    decision window's filing strip (and an old bundle) sends."""
    client, db = _hub(tmp_path, monkeypatch)
    project_id = _project(client)
    decision_id = _decide(client)

    filed = client.put(
        f"/api/projects/{project_id}/resources/{sent_kind}:{decision_id}",
        json={"relationship": "member"},
    )
    assert filed.status_code == 200, filed.text

    # One name in the store, whichever name the face sent.
    stored = [row.resource_ref for row in db.project_relationships.list_for_project(project_id)]
    assert stored == [f"desk_decision:{decision_id}"]

    assert _project_hits(client, project_id) == [f"desk_decision:{decision_id}"]

    # What Ask and desk chat call with the Project attached.
    asked = hydrate_refs_detailed(
        db, [], [], "summary",
        qualified_refs=[f"project:{project_id}"],
        query="what did we decide about quorumdb",
    )
    assert asked.unknown == []
    assert asked.source_refs == [f"desk_decision:{decision_id}"]
    assert "quorumdb" in asked.blocks[0].title

    # The Project attached with no question: a member, never an unknown ref.
    listed = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=[f"project:{project_id}"]
    )
    assert listed.unknown == []
    assert [block.title for block in listed.blocks] == ["Adopt quorumdb for the ledger"]

    # The decision window shows where it is filed, and can take it out.
    axes = client.get(f"/api/desk/relationships/decision:{decision_id}")
    assert axes.status_code == 200, axes.text
    assert [row["project_id"] for row in axes.json()["projects"]] == [project_id]
    removed = client.delete(f"/api/projects/{project_id}/resources/decision:{decision_id}")
    assert removed.status_code == 200, removed.text
    assert _project_hits(client, project_id) == []


def test_a_row_filed_under_the_old_name_keeps_working(tmp_path: Path, monkeypatch) -> None:
    client, db = _hub(tmp_path, monkeypatch)
    project_id = _project(client)
    decision_id = _decide(client)
    # The row as the product wrote it before the fix (web/src/desk/decide.ts:88).
    db.project_relationships.upsert(
        project_id=project_id, resource_ref=f"decision:{decision_id}"
    )

    assert _project_hits(client, project_id) == [f"desk_decision:{decision_id}"]

    asked = hydrate_refs_detailed(
        db, [], [], "summary",
        qualified_refs=[f"project:{project_id}"],
        query="quorumdb",
    )
    assert asked.unknown == []
    assert asked.source_refs == [f"desk_decision:{decision_id}"]

    listed = hydrate_refs_detailed(
        db, [], [], "summary", qualified_refs=[f"project:{project_id}"]
    )
    assert listed.unknown == []
    assert [block.title for block in listed.blocks] == ["Adopt quorumdb for the ledger"]

    axes = client.get(f"/api/desk/relationships/decision:{decision_id}")
    assert [row["project_id"] for row in axes.json()["projects"]] == [project_id]
    removed = client.delete(f"/api/projects/{project_id}/resources/decision:{decision_id}")
    assert removed.status_code == 200, removed.text
    assert _project_hits(client, project_id) == []
