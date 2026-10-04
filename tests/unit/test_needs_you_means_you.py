"""``Needs you`` means the owner (owner rulings 2026-10-04).

A. What he is WAITING ON someone else for is listed and is not counted. The
   answer gives ``count`` (needs him) and ``waitingCount`` (waiting on
   others), and each row says which it is (``waiting``).
B. A decision that waits for his review is a member and is counted. Review
   opens it (``openRef``); a decided decision is no member. The Brief counts
   it once.

Each fence boots the real hub on an isolated HOME and writes through the
real producers (MCP tools and HTTP routes).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

OWNER = Principal(PrincipalKind.OWNER, "needs-you-means-you")


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


def _headline(hub: Hub) -> str:
    brief = _ok(hub.client.post("/api/brief/generate"))
    return str((brief.get("brief") or brief)["headline"])


def _phrase(headline: str, noun: str) -> int:
    match = re.search(rf"(\d+) {noun}s? waiting", headline)
    return int(match.group(1)) if match else 0


def _readers(hub: Hub, *, brief: bool) -> dict[str, int]:
    """Every backend reader of the number, by the face it feeds.

    The hub keeps one Brief for a week, so a fence reads it once, at the
    state it asserts (``brief=True``).
    """
    from holdspeak.services.heartbeat_service import HeartbeatService

    route = _ok(hub.client.get("/api/desk/needs-you"))
    fresh = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error, mcp
    readers = {
        "route": int(route["count"]),
        "route_members": len(route["members"]),
        "route_fresh": int(fresh["count"]),
        "mcp": int(mcp["count"]),
        "notifications": int(HeartbeatService(hub.db).notification_count(OWNER)),
    }
    if brief:
        readers["brief"] = _phrase(_headline(hub), "thing")
    return readers


def _one_number(hub: Hub, *, brief: bool = False) -> int:
    readers = _readers(hub, brief=brief)
    assert len(set(readers.values())) == 1, readers
    return readers["route"]


def test_an_item_with_a_named_owner_is_waiting_and_is_not_counted(hub: Hub) -> None:
    is_error, action = hub.mcp("door.add_item", {"task": "Call the vendor"})
    assert not is_error, action
    ref = str(action["id"])

    before = _ok(hub.client.get("/api/desk/needs-you"))
    row = next(item for item in before["items"] if item["ref"] == ref)
    assert row["why"] == "UNASSIGNED" and row["waiting"] is False
    assert ref in [member["ref"] for member in before["members"]]
    assert before["waitingCount"] == 0
    number = _one_number(hub)

    # The Chair's "name an owner" write: the Door card's lawful delegate verb.
    _ok(hub.client.post("/api/follow-through/complete", json={
        "card_id": ref, "verb": "delegate", "payload": {"to": "Dana"},
    }))

    after = _ok(hub.client.get("/api/desk/needs-you"))
    row = next(item for item in after["items"] if item["ref"] == ref)
    # The row stays listed (the Chair's WAITING filter shows it) and is marked.
    assert row["why"] == "WAITING ON DANA" and row["waiting"] is True
    assert ref not in [member["ref"] for member in after["members"]]
    assert after["count"] == before["count"] - 1
    assert after["waitingCount"] == 1
    assert _one_number(hub, brief=True) == number - 1
    brief = _ok(hub.client.post("/api/brief/generate"))
    waiting = [item["text"] for item in (brief.get("brief") or brief)["sections"]["waiting"]]
    assert not any("Call the vendor" in text for text in waiting), waiting

    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error, mcp
    assert mcp["waitingCount"] == 1
    assert next(item for item in mcp["items"] if item["ref"] == ref)["waiting"] is True


def test_a_waiting_row_fires_no_notification(hub: Hub) -> None:
    from holdspeak.services.heartbeat_service import HeartbeatService

    is_error, action = hub.mcp("door.add_item", {"task": "Send the estimate", "owner": "Priya"})
    assert not is_error, action
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    row = next(item for item in answer["items"] if item["ref"] == str(action["id"]))
    assert row["waiting"] is True
    heartbeat = HeartbeatService(hub.db)
    assert heartbeat.notification_count(OWNER) == answer["count"]
    aggregate = heartbeat.get_aggregate(OWNER)
    assert aggregate["waitingCount"] == 1 and aggregate["count"] == answer["count"]


def test_a_decision_that_waits_for_review_is_a_member_until_it_is_decided(hub: Hub) -> None:
    base = _one_number(hub)
    is_error, decision = hub.mcp("desk.create", {
        "kind": "decisions", "data": {"title": "Adopt the queue", "status": "proposed"},
    })
    assert not is_error, decision
    ref = f"decision:{decision['id']}"

    answer = _ok(hub.client.get("/api/desk/needs-you"))
    assert ref in [member["ref"] for member in answer["members"]]
    row = next(item for item in answer["items"] if item["ref"] == ref)
    assert row["title"] == "Adopt the queue" and row["why"] == "TO REVIEW"
    assert row["source"] == "decision" and row["waiting"] is False
    # Review opens the decision: the ref is the Desk route token of its window,
    # and the hub reads the decision back by it.
    assert row["openRef"] == ref
    read = _ok(hub.client.get(f"/api/decisions/{decision['id']}"))
    assert read["decision"]["title"] == "Adopt the queue"

    # Every reader counts it, once. The Brief says it in the one number and
    # does not say it again under "decision waiting"; its row stays in DECISIONS.
    assert _one_number(hub, brief=True) == base + 1
    brief = _ok(hub.client.post("/api/brief/generate"))
    brief = brief.get("brief") or brief
    assert _phrase(brief["headline"], "decision") == 0, brief["headline"]
    assert [item["text"] for item in brief["sections"]["decisions"]] == ["Review decision: Adopt the queue"]
    assert not any("Adopt the queue" in item["text"] for item in brief["sections"]["waiting"])

    # Deciding it removes it.
    _ok(hub.client.put(f"/api/decisions/{decision['id']}/status", json={"status": "accepted"}))
    after = _ok(hub.client.get("/api/desk/needs-you"))
    assert ref not in [member["ref"] for member in after["members"]]
    assert ref not in [item["ref"] for item in after["items"]]
    assert _one_number(hub) == base


def test_a_meeting_decision_is_a_member_until_it_is_accepted(hub: Hub) -> None:
    """A decision a meeting recorded waits for review until accept or reject."""
    from datetime import datetime

    from holdspeak.meeting_session import IntelSnapshot, MeetingState

    started = datetime.now().replace(microsecond=0)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-decision", started_at=started, ended_at=started, title="Planning",
        intel=IntelSnapshot(timestamp=started.timestamp(), summary="", action_items=[]),
        intel_status="completed", capture_status="finalized",
    ))
    # The decision-capture plugin's artifact, reconciled into ``decisions``
    # (the producer the synthesis persistence calls).
    hub.db.plugins.record_artifact(
        artifact_id="artifact-decision", meeting_id="m-decision", artifact_type="decisions",
        title="Decisions", structured_json={"decisions": [{"decision": "Ship on Friday"}]},
        plugin_id="decision_capture",
    )
    hub.db.decisions.reconcile_artifact("artifact-decision")
    decision_id = str(hub.db.decisions.list(lifecycle="recorded")[0].id)
    ref = f"decision:{decision_id}"

    base = _one_number(hub, brief=True)
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    assert ref in [member["ref"] for member in answer["members"]]
    row = next(item for item in answer["items"] if item["ref"] == ref)
    assert row["title"] == "Ship on Friday" and row["openRef"] == ref

    _ok(hub.client.post(f"/api/decisions/{decision_id}/accept"))
    after = _ok(hub.client.get("/api/desk/needs-you"))
    assert ref not in [member["ref"] for member in after["members"]]
    assert _one_number(hub) == base - 1


def test_an_item_the_owner_himself_holds_is_his_and_is_counted(hub: Hub) -> None:
    """``Me`` is the owner (the meeting speaker label; the People store reserves it)."""
    from datetime import date, timedelta

    today = date.today().isoformat()
    later = (date.today() + timedelta(days=9)).isoformat()
    made = {}
    for key, args in {
        "mine_today": {"task": "Sign the contract", "owner": "Me", "due": today},
        "mine_later": {"task": "Write the review", "owner": "Me", "due": later},
        "priya": {"task": "Send the estimate", "owner": "Priya", "due": later},
    }.items():
        is_error, action = hub.mcp("door.add_item", args)
        assert not is_error, action
        made[key] = str(action["id"])

    # A 1:1 commitment he owes (direction ``leader_owes``), through People.
    _ok(hub.client.post("/api/people/setup"))
    relationship = _ok(hub.client.post(
        "/api/people/relationships", json={"display_name": "Dana"}), 201)["relationship"]
    request = _ok(hub.client.post(
        f"/api/people/relationships/{relationship['id']}/requests",
        json={"body": "Review the promotion case"}), 201)["request"]
    commitment = _ok(hub.client.post(f"/api/people/requests/{request['id']}/accept", json={}))["commitment"]
    assert commitment["direction"] == "leader_owes"
    made["commitment"] = f"people:{commitment['id']}"

    answer = _ok(hub.client.get("/api/desk/needs-you"))
    rows = {row["ref"]: row for row in answer["items"]}
    members = [member["ref"] for member in answer["members"]]
    # His own items count and read as his, at any due date.
    assert rows[made["mine_today"]]["why"] == "DUE TODAY" and rows[made["mine_today"]]["waiting"] is False
    assert rows[made["mine_later"]]["why"] == "YOURS" and rows[made["mine_later"]]["waiting"] is False
    assert rows[made["commitment"]]["waiting"] is False
    for key in ("mine_today", "mine_later", "commitment"):
        assert made[key] in members, key
    # Priya's is waited on.
    assert rows[made["priya"]]["why"] == "WAITING ON PRIYA" and rows[made["priya"]]["waiting"] is True
    assert made["priya"] not in members
    assert answer["waitingCount"] == 1
    assert "me" in answer["ownerNames"]
    assert _one_number(hub, brief=True) == answer["count"]
