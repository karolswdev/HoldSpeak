"""One rule, one number, every face.

Proved on a real hub before this fence: the Brief said "1 thing waiting, 1
decision waiting" while ``GET /api/desk/needs-you`` said ``count: 0``. The
bell counted the Door cards; notifications, the palette, the system shade
and MCP counted Room rows only.

This fence boots the real hub on an isolated HOME, mints a decision that
waits for review, an overdue action and a People commitment through their
real producers, and asserts that every reader reports the same number.
"""
from __future__ import annotations

import re
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

OWNER = Principal(PrincipalKind.OWNER, "one-number")


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    monkeypatch.setenv("HOME", str(tmp_path))
    hub = _boot(tmp_path, monkeypatch)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def _mint(hub: Hub) -> dict[str, str]:
    """A decision waiting, an overdue action and a People commitment."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    is_error, action = hub.mcp("door.add_item", {
        "task": "Send the capacity plan", "owner": "Dana", "due": yesterday,
    })
    assert not is_error, action
    is_error, decision = hub.mcp("desk.create", {
        "kind": "decisions", "data": {"title": "Adopt the queue", "status": "proposed"},
    })
    assert not is_error, decision

    _ok(hub.client.post("/api/people/setup"))
    relationship = _ok(hub.client.post(
        "/api/people/relationships", json={"display_name": "Dana"}), 201)["relationship"]
    request = _ok(hub.client.post(
        f"/api/people/relationships/{relationship['id']}/requests",
        json={"body": "Review the promotion case"}), 201)["request"]
    commitment = _ok(hub.client.post(f"/api/people/requests/{request['id']}/accept", json={}))["commitment"]
    return {"action": str(action["id"]), "commitment": f"people:{commitment['id']}"}


def minted_brief_headline(hub: Hub) -> str:
    brief = _ok(hub.client.post("/api/brief/generate"))
    return str((brief.get("brief") or brief)["headline"])


def _brief_waiting(headline: str) -> int:
    match = re.search(r"(\d+) things? waiting", headline)
    return int(match.group(1)) if match else 0


def _readers(hub: Hub) -> dict[str, int]:
    """Every backend reader of ``needs you``, by the face it feeds."""
    from holdspeak.services.heartbeat_service import HeartbeatService

    route = _ok(hub.client.get("/api/desk/needs-you"))
    fresh = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error, mcp
    brief = _ok(hub.client.post("/api/brief/generate"))
    return {
        # The bell, the Chair window, the Dock badge, the system shade and
        # the palette all read this answer (web/src/desk/needsYou.ts,
        # SystemShade.tsx, DeskToolShelf.tsx).
        "route": int(route["count"]),
        "route_members": len(route.get("members", route["items"])),
        "route_fresh": int(fresh["count"]),
        "mcp": int(mcp["count"]),
        "notifications": int(HeartbeatService(hub.db).notification_count(OWNER)),
        "brief": _brief_waiting(str((brief.get("brief") or brief)["headline"])),
    }


def test_every_reader_reports_the_same_number(hub: Hub) -> None:
    minted = _mint(hub)
    readers = _readers(hub)
    assert len(set(readers.values())) == 1, readers
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    refs = sorted(member["ref"] for member in answer["members"])
    # The overdue action and the People commitment are members; a hub with no
    # summary engine has the one meeting-path blocker. A decision that waits for
    # review is not a member of the R1-R3 rule: the Brief counts it under its
    # own noun ("1 decision waiting").
    assert refs == sorted([minted["action"], "blocker:summary", minted["commitment"]]), refs
    assert readers["route"] == 3, readers
    assert "1 decision waiting" in minted_brief_headline(hub)
    assert answer["peopleStoreState"] == "ready"
    assert answer["sourceErrors"] == {}


def test_the_number_follows_the_door_without_a_fresh_read(hub: Hub) -> None:
    """The Room read is cached; the Door part of the rule is not."""
    before = _ok(hub.client.get("/api/desk/needs-you"))["count"]
    is_error, action = hub.mcp("door.add_item", {"task": "Call the vendor"})
    assert not is_error, action
    after = _ok(hub.client.get("/api/desk/needs-you"))
    assert after["count"] == before + 1
    assert str(action["id"]) in [member["ref"] for member in after["members"]]
