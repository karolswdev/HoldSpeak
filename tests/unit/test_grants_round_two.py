"""PHILO-7-02 round two (Astra's check on built, findings 1-3): one fence per path.

Each fence drives the REAL hub over its real transports and asserts three
things: the response fields (the named error kept, plus ``operation_id`` and
``receipt``), the durable receipt (read back through ``GET /api/kernel/read``),
and the unchanged domain state. Red on round one (``86ec4ee5``):
``docs/internal/philo/phase-7/article-xi/red-round-two.txt``.
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
from test_philo7_article_xi import _agent, _rpc, _thought_note  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    store = hub.server.app.state.agent_credentials
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _receipt_of(hub: Hub, body: dict[str, Any]) -> dict[str, Any]:
    """The response's receipt, and the same receipt read back durably."""
    assert body.get("operation_id") and isinstance(body.get("receipt"), dict), f"no receipt in the response: {body}"
    read = hub.client.get("/api/kernel/read", params={"refs": f"operation:{body['operation_id']}", "view": "receipt"})
    durable = read.json()["objects"][0]["receipt"]
    assert durable == body["receipt"], (durable, body["receipt"])
    return durable


def _grants(hub: Hub) -> list[tuple[str, str]]:
    with hub.db._connection() as conn:
        return [tuple(r) for r in conn.execute("SELECT agent_identity, state FROM kernel_desk_delegations")]


def _decisions(hub: Hub) -> list[tuple[str, str]]:
    return sorted((d.id, d.status) for d in hub.db.desk_decisions.list(limit=2000))


def _tool_body(response: dict[str, Any]) -> dict[str, Any]:
    assert response["result"]["isError"] is True, response
    return json.loads(response["result"]["content"][0]["text"])


# ── finding 1: the path names the agent; the body never does ─────────────


def test_a_grant_body_cannot_name_another_agent(hub: Hub) -> None:
    resp = hub.client.put("/api/settings/remote/delegations/path-agent", json={"agent_identity": "body-agent"})
    assert resp.status_code == 400 and resp.json()["error"] == "invalid_arguments", resp.text
    receipt = _receipt_of(hub, resp.json())
    assert (receipt["state"], receipt["outcome"], receipt["target_ref"]) == ("refused", "invalid_arguments", "agent:path-agent")
    assert _grants(hub) == [], "a grant row was written"


# ── finding 2: identifiable consequential refusals leave their receipt ───


def test_http_supersede_of_a_missing_decision_leaves_a_receipt(hub: Hub) -> None:
    resp = hub.client.post("/api/decisions/nope/supersede")
    assert resp.status_code == 404 and resp.json()["error"] == "decision_not_found", resp.text
    receipt = _receipt_of(hub, resp.json())
    assert (receipt["state"], receipt["outcome"]) == ("refused", "not_found")
    assert _decisions(hub) == []


def test_http_supersede_with_a_non_object_body_leaves_a_receipt(hub: Hub) -> None:
    decision_id = hub.client.post("/api/decisions", json={"title": "D"}).json()["decision"]["id"]
    before = _decisions(hub)
    resp = hub.client.post(f"/api/decisions/{decision_id}/supersede", content=b"[1]", headers={"Content-Type": "application/json"})
    assert resp.status_code == 422, resp.text
    receipt = _receipt_of(hub, resp.json())
    assert (receipt["state"], receipt["outcome"], receipt["target_ref"]) == ("refused", "invalid_arguments", f"decision:{decision_id}")
    assert _decisions(hub) == before


def test_http_decision_create_with_non_list_tags_leaves_a_receipt(hub: Hub) -> None:
    resp = hub.client.post("/api/decisions", json={"title": "x", "tags": 42})
    assert resp.status_code == 400 and "tags" in resp.json()["error"], resp.text
    receipt = _receipt_of(hub, resp.json())
    assert (receipt["state"], receipt["outcome"]) == ("refused", "invalid_arguments")
    assert _decisions(hub) == []


@pytest.mark.parametrize("extra, code", [({"bogus": 1}, "invalid_arguments"), ({"owner": "forged"}, "authority_in_arguments")])
def test_mcp_delete_of_a_thoughts_note_with_a_bad_field_leaves_a_receipt(hub: Hub, extra: dict[str, Any], code: str) -> None:
    thought = _thought_note(hub, f"bad-{code}")
    note_id = thought["working_note"]["id"]
    data = {"expected_aggregate_revision": thought["aggregate_revision"],
            "expected_lifecycle_revision": thought["lifecycle_revision"], **extra}
    body = _tool_body(_rpc(hub.client, "desk.delete", {"kind": "notes", "id": note_id, "data": data}))
    assert "Invalid arguments for note.delete" in body["error"], body
    receipt = _receipt_of(hub, body)
    assert (receipt["state"], receipt["outcome"], receipt["target_ref"]) == ("refused", code, f"note:{note_id}")
    assert hub.client.get(f"/api/thoughts/{thought['id']}").json()["thought"]["state"] != "tombstoned"


# ── finding 3: every refusal response of an admitted operation carries its receipt ──


def test_http_non_object_decision_create_returns_its_receipt(hub: Hub) -> None:
    resp = hub.client.post("/api/decisions", content=b"[]", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400 and resp.json()["error"] == "expected a JSON object"
    assert _receipt_of(hub, resp.json())["outcome"] == "invalid_arguments"
    assert _decisions(hub) == []


def test_mcp_schema_refusal_returns_its_receipt(hub: Hub) -> None:
    body = _tool_body(_rpc(hub.client, "zone.file", {"primitive_id": "note:x"}))
    assert "directory_id" in body["error"]
    assert _receipt_of(hub, body)["outcome"] == "invalid_arguments"


def test_mcp_non_object_arguments_return_their_receipt(hub: Hub) -> None:
    body = _tool_body(_rpc(hub.client, "zone.file", ["z", "n"]))
    assert body["error"] == "Tool arguments must be an object"
    assert _receipt_of(hub, body)["outcome"] == "invalid_arguments"


def test_mcp_contract_refusal_returns_its_receipt(hub: Hub) -> None:
    body = _tool_body(_rpc(hub.client, "desk.create", {"kind": "decisions", "data": {"title": "x", "owner": "forged"}}))
    assert "owner cannot be an argument" in body["error"]
    assert _receipt_of(hub, body)["outcome"] == "authority_in_arguments"
    assert _decisions(hub) == []


def test_the_palette_refusal_of_an_admitted_tool_returns_its_receipt(hub: Hub) -> None:
    project = _agent(hub, palette="PROJECT", identity="project-agent")
    refused = _rpc(project, "zone.file", {"directory_id": "z", "primitive_id": "note:x"})
    data = refused["error"]["data"]
    assert (data["code"], data["tool"]) == ("MCP-005", "zone.file")
    assert data["receipt"]["outcome"] == "mcp_palette_refused" and data["operation_id"] == data["receipt"]["operation_id"]


def test_the_http_filing_of_a_tombstoned_thoughts_note_returns_its_receipt(hub: Hub) -> None:
    """The inherited 500 stays (BACKLOG); the refusal's receipt is carried now."""
    zone = hub.client.post("/api/directories", json={"name": "Zone"}).json()["directory"]["id"]
    thought = _thought_note(hub, "tomb-500")
    note_id = thought["working_note"]["id"]
    assert hub.client.request("DELETE", f"/api/notes/{note_id}", json={
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_lifecycle_revision": thought["lifecycle_revision"]}).status_code == 200
    resp = hub.client.put(f"/api/directories/{zone}/members/note:{note_id}")
    assert resp.status_code == 500
    assert _receipt_of(hub, resp.json())["outcome"] == "thought_tombstoned"
    assert hub.db.directory_memberships.list_for_directory(zone) == []
