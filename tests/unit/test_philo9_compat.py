"""PHILO-9-01 compatibility: the Room's existing names, envelopes and refusals are kept.

Imports nothing the story adds, so it runs unchanged on an export of main
(base) and on the branch (built): the three-state table in the evidence reads
this file's result in each state. It pins, for the eighteen MCP tools the story
moves onto the contract and their HTTP routes: the tool names, the answer's
envelope keys, the refusal code (MCP) and the status and envelope keys (HTTP)
of an unknown project, update or item, and ``project_request_invalid`` for an
empty id. Values that differ run to run (ids, times) are never compared.

PHILO-9-02 (the named difference): an ADMITTED call's answer -- and a refusal
of one -- also carries its kernel ``operation_id`` and ``receipt`` (a
superset; the steward beat, section 6). The envelope keys are compared
without those two.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _call(hub: Hub, name: str, args: dict[str, Any]) -> tuple[bool, Any]:
    return hub.mcp(name, args)


#: PHILO-9-02: the kernel fields an admitted call (or its refusal) adds.
_KERNEL = {"operation_id", "receipt"}


def _keys(value: dict[str, Any]) -> set[str]:
    return set(value) - _KERNEL


@pytest.fixture
def room(hub: Hub) -> dict[str, str]:
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Compat"}).json()["project"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    meeting = "m-compat"
    with hub.db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES (?, datetime('now'), 'Compat meeting')", (meeting,))
    return {"pid": pid, "update": update, "meeting": meeting}


def test_the_eighteen_mcp_answers_keep_their_envelopes(hub: Hub, room: dict[str, str]) -> None:
    pid, update, meeting = room["pid"], room["update"], room["meeting"]
    shapes: list[tuple[str, dict[str, Any], set[str] | None]] = [
        ("project.list", {}, {"projects"}),
        ("project.get", {"project_id": pid}, None),
        ("project.get_room", {"project_id": pid}, None),
        ("project.create", {"name": "Another"}, {"success", "project"}),
        ("project.update", {"project_id": pid, "patch": {"description": "d"}}, {"success", "project"}),
        ("project.link", {"project_id": pid, "meeting_id": meeting}, {"success"}),
        ("project.unlink", {"project_id": pid, "meeting_id": meeting}, {"success"}),
        ("project.open_review", {"project_id": pid}, None),
        ("project.get_delta", {"project_id": pid}, None),
        ("project.list_updates", {"project_id": pid}, {"updates"}),
        ("project.update_draft", {"update_id": update, "body_md": "Text"}, {"success", "update"}),
        ("project.publish_update", {"update_id": update}, {"success", "update"}),
        ("project.draft_update", {"project_id": pid}, {"success", "update"}),
        ("desk.needs_you", {}, None),
        ("project.archive", {"project_id": pid}, {"success"}),
        ("project.restore", {"project_id": pid}, {"success", "project"}),
    ]
    for name, args, keys in shapes:
        is_error, value = _call(hub, name, args)
        assert not is_error, (name, value)
        if keys is not None:
            assert _keys(value) == keys, (name, sorted(value))
    _, got = _call(hub, "project.get", {"project_id": pid})
    assert got["id"] == pid and "name" in got
    _, the_room = _call(hub, "project.get_room", {"project_id": pid})
    assert {"project_id", "revision", "project", "items", "needsYou", "health", "receipts"} <= set(the_room)
    _, needs = _call(hub, "desk.needs_you", {})
    assert {"count", "projects", "items", "coverage", "complete"} <= set(needs)


def test_the_eighteen_mcp_refusals_keep_their_codes(hub: Hub, room: dict[str, str]) -> None:
    cases = [
        ("project.get", {"project_id": "proj-none"}, "not_found"),
        ("project.get_room", {"project_id": "proj-none"}, "not_found"),
        ("project.update", {"project_id": "proj-none", "patch": {"description": "d"}}, "not_found"),
        ("project.archive", {"project_id": "proj-none"}, "not_found"),
        ("project.link", {"project_id": room["pid"], "meeting_id": "m-none"}, "not_found"),
        ("project.get_delta", {"project_id": "proj-none"}, "not_found"),
        ("project.list_updates", {"project_id": "proj-none"}, "not_found"),
        ("project.update_draft", {"update_id": "upd-none", "body_md": "x"}, "not_found"),
        ("project.get", {"project_id": " "}, "project_request_invalid"),
        ("project.publish_update", {"update_id": ""}, "project_request_invalid"),
    ]
    for name, args, code in cases:
        is_error, value = _call(hub, name, args)
        assert is_error and value.get("code") == code, (name, value)


def test_the_http_routes_keep_their_envelopes_and_statuses(hub: Hub, room: dict[str, str]) -> None:
    c, pid = hub.client, room["pid"]
    ok = [
        ("GET", "/api/projects", None, {"projects"}),
        ("GET", f"/api/projects/{pid}/items", None, {"items", "limit", "offset"}),
        ("POST", f"/api/projects/{pid}/items", {"item_type": "milestone", "title": "M"}, {"success", "item"}),
        ("GET", f"/api/projects/{pid}/resources", None, {"resources"}),
        # PHILO-10: the envelope gained ``latest_published_update_id`` (additive).
        ("GET", f"/api/projects/{pid}/updates", None, {"updates", "latest_published_update_id"}),
        ("PATCH", f"/api/projects/{pid}", {"description": "d"}, {"success", "project"}),
    ]
    for method, path, body, keys in ok:
        resp = c.request(method, path, json=body) if body is not None else c.request(method, path)
        assert resp.status_code == 200, (path, resp.text)
        assert _keys(resp.json()) == keys, (path, sorted(resp.json()))
    refused = [
        ("GET", "/api/projects/proj-none", None, 404, {"error"}),
        ("GET", "/api/projects/proj-none/room", None, 404, {"error"}),
        ("PATCH", "/api/projects/proj-none", {"description": "d"}, 404, {"error", "success"}),
        ("GET", "/api/projects/proj-none/items", None, 404, {"error"}),
        ("GET", f"/api/projects/{pid}/items?item_type=bogus", None, 400, {"error"}),
        ("POST", f"/api/projects/{pid}/items", {"item_type": "bogus", "title": "x"}, 400, {"error", "success"}),
        ("GET", "/api/projects/proj-none/resources", None, 404, {"error"}),
        ("PUT", f"/api/projects/{pid}/resources/github:example/payments", {}, 400, {"error"}),
        ("GET", "/api/projects/proj-none/delta", None, 404, {"code", "message"}),
        ("GET", "/api/projects/proj-none/updates", None, 404, {"code", "message"}),
        ("POST", "/api/updates/upd-none/publish", {}, 404, {"success", "code", "message"}),
    ]
    for method, path, body, status, keys in refused:
        resp = c.request(method, path, json=body) if body is not None else c.request(method, path)
        assert resp.status_code == status, (path, resp.status_code, resp.text)
        assert _keys(resp.json()) == keys, (path, sorted(resp.json()))
    json.dumps(room)  # the fixture's values are plain
