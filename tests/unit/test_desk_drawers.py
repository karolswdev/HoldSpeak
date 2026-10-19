"""Drawers, hub half (Betterment Q10 "Knowledge becomes drawers").

A knowledge collection reads as a drawer of its members: ``/api/kbs`` (the
read the desk draws each collection as a drawer from) lists the stored members
AND the live member edges ``kb.add_member`` writes, and a member
``kb.remove_member`` took away is not listed. Before, a collection filled
through MCP read empty on the desk. The kb data and the kb.* tools stay.
"""
from __future__ import annotations

from typing import Any

from tests.unit.test_philo5_the_loop import hub  # noqa: F401  (fixture)


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:300])
    return response.json()


def _kb(hub: Any, kb_id: str) -> dict[str, Any]:
    kbs = _ok(hub.client.get("/api/kbs"))["kbs"]
    return next(kb for kb in kbs if kb["id"] == kb_id)


def test_a_collection_reads_as_a_drawer_of_its_members(hub) -> None:  # noqa: F811
    first = _ok(hub.client.post("/api/notes", json={"title": "Cutover plan", "body_markdown": "x", "tags": []}), 201)["note"]
    second = _ok(hub.client.post("/api/notes", json={"title": "Rollback plan", "body_markdown": "y", "tags": []}), 201)["note"]
    made = _ok(hub.client.post("/api/kbs", json={"name": "Reference", "member_ids": [f"note:{first['id']}"]}), 201)["kb"]
    assert _kb(hub, made["id"])["member_ids"] == [f"note:{first['id']}"]

    # A member added through MCP (the edge store) is in the drawer.
    is_error, out = hub.mcp("kb.add_member", {"kb_id": made["id"], "ref": f"note:{second['id']}"})
    assert not is_error, out
    both = {f"note:{first['id']}", f"note:{second['id']}"}
    assert set(_kb(hub, made["id"])["member_ids"]) == both
    assert set(_ok(hub.client.get(f"/api/kbs/{made['id']}"))["kb"]["member_ids"]) == both

    # A member taken away through MCP leaves it, even one the stored list holds.
    is_error, out = hub.mcp("kb.remove_member", {"kb_id": made["id"], "ref": f"note:{first['id']}"})
    assert not is_error, out
    assert _kb(hub, made["id"])["member_ids"] == [f"note:{second['id']}"]
