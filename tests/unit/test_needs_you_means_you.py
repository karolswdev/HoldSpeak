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
    from holdspeak.services.needs_you_membership import unread_source_groups

    route = _ok(hub.client.get("/api/desk/needs-you"))
    fresh = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error, mcp
    readers = {
        "route": int(route["count"]),
        # PHILO-15-09 (B11): the rows the desk draws under the head: the
        # members, each source not read, each recording that arms.
        # PHILO-15 B60: a source held by quiet hours is listed, never counted.
        # PHILO-17 (needsyou): the sources of one cause are one row.
        "route_rows": len(route["members"]) + len(
            unread_source_groups(route.get("coverage") or [])
        ) + len(route.get("arming") or []),
        "route_fresh": int(fresh["count"]),
        "mcp": int(mcp["count"]),
        "notifications": int(HeartbeatService(hub.db).notification_count(OWNER)),
    }
    if brief:
        # PHILO-15-09 (Astra r2): the Brief says an unread source once, as a
        # source not read, never also as a thing waiting; its number is both.
        headline = _headline(hub)
        unread = re.search(r"(\d+) sources? not read", headline)
        readers["brief"] = _phrase(headline, "thing") + (int(unread.group(1)) if unread else 0)
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


def _linked_meeting(hub: Hub, meeting_id: str, project: str) -> str:
    """A saved meeting, linked to a new Project through the real routes."""
    from datetime import datetime

    from holdspeak.meeting_session import IntelSnapshot, MeetingState

    started = datetime.now().replace(microsecond=0)
    hub.db.meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=started, ended_at=started, title="Planning",
        intel=IntelSnapshot(timestamp=started.timestamp(), summary="", action_items=[]),
        intel_status="completed", capture_status="finalized",
    ))
    created = _ok(hub.client.post("/api/projects", json={"name": project}))
    project_id = str(created["project"]["id"])
    _ok(hub.client.post(f"/api/projects/{project_id}/meetings/{meeting_id}", json={}))
    return project_id


def test_his_own_item_is_counted_when_it_merges_with_a_row_that_waits(hub: Hub) -> None:
    """Astra's repro on #818: his later-due action and Dana's Room commitment
    name the same thing. The merged row is his and is counted."""
    from datetime import date, timedelta

    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    later = (date.today() + timedelta(days=9)).isoformat()
    title = "Send the capacity plan"
    _linked_meeting(hub, "m-merge", "Capacity")
    hub.db.plugins.record_artifact(
        artifact_id="artifact-merge", meeting_id="m-merge", artifact_type="action_items",
        title="Actions", structured_json={"action_items": [{"task": title, "owner": "Dana", "due": ""}]},
        status="accepted", plugin_id="action_owner_enforcer", plugin_version="fence",
    )
    proposal = next(
        row for row in ProposalBridgeService(hub.db).bridge_meeting_artifacts("m-merge") if row.text == title)
    _ok(hub.client.post(f"/api/proposals/{proposal.id}/confirm", json={"owner": "Dana", "due": later}))

    before = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    dana = [row for row in before["items"] if row["title"] == title]
    assert len(dana) == 1 and dana[0]["why"] == "WAITING ON DANA" and dana[0]["waiting"] is True, dana

    is_error, action = hub.mcp("door.add_item", {"task": title, "owner": "Me", "due": later})
    assert not is_error, action

    after = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    rows = [row for row in after["items"] if row["title"] == title]
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["dedupCount"] == 2
    # One projection is his: the row is his, leads with his reason, is counted.
    assert row["waiting"] is False and row["why"] == "YOURS", row
    assert row["ref"] in [member["ref"] for member in after["members"]]
    # PHILO-15-09 (B11): the one number counts every row the desk draws: the
    # members and each source that could not be read (a Watch row is one).
    # PHILO-17 (needsyou): the sources of one cause are one row.
    from holdspeak.services.needs_you_membership import unread_source_groups

    def rows_of(answer):
        return len(answer["members"]) + len(unread_source_groups(answer["coverage"])) + len(answer.get("arming") or [])

    assert after["count"] == rows_of(after) and before["count"] == rows_of(before)
    assert len(after["members"]) == len(before["members"]) + 1, (before["coverage"], after["coverage"])
    assert after["waitingCount"] == before["waitingCount"] - 1
    assert _one_number(hub, brief=True) == after["count"]


def test_one_meeting_decision_with_its_proposal_is_one_member(hub: Hub) -> None:
    """Astra's repro on #818: the recorded decision and the proposal the
    bridge makes from the same artifact are ONE member; confirming settles both."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    _linked_meeting(hub, "m-bridge", "Release")
    base = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))

    hub.db.plugins.record_artifact(
        artifact_id="artifact-bridge", meeting_id="m-bridge", artifact_type="decisions",
        title="Decisions", structured_json={"decisions": [{"decision": "Ship on Friday"}]},
        plugin_id="decision_capture",
    )
    hub.db.decisions.reconcile_artifact("artifact-bridge")
    recorded = hub.db.decisions.list(lifecycle="recorded")
    assert [decision.text for decision in recorded] == ["Ship on Friday"]
    proposals = ProposalBridgeService(hub.db).bridge_meeting_artifacts("m-bridge")
    assert [(row.kind, row.text) for row in proposals] == [("decision", "Ship on Friday")]

    asked = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    named = [row for row in asked["items"] if "Ship on Friday" in row["title"]]
    # ONE member: the Room's proposal row. The recorded decision is not a second.
    assert len(named) == 1 and named[0].get("proposalId") == proposals[0].id, named
    assert f"decision:{recorded[0].id}" not in [member["ref"] for member in asked["members"]]
    assert asked["count"] == base["count"] + 1
    assert _one_number(hub) == asked["count"]

    # Confirming the proposal settles both: neither the proposal nor the
    # recorded decision asks again. The owner he names is waited on.
    from datetime import date, timedelta

    later = (date.today() + timedelta(days=9)).isoformat()
    _ok(hub.client.post(f"/api/proposals/{proposals[0].id}/confirm", json={"owner": "Dana", "due": later}))
    settled = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    assert not any(row.get("proposalId") == proposals[0].id for row in settled["items"])
    assert not any(str(member["ref"]).startswith("decision:") for member in settled["members"])
    assert settled["count"] == base["count"], [(r["title"], r["why"]) for r in settled["items"]]
    assert _one_number(hub, brief=True) == settled["count"]


def test_a_row_the_room_already_merged_is_his_when_one_projection_is(hub: Hub) -> None:
    """Astra's second repro on #818: Dana's later-due commitment and a PR that
    awaits HIS review name the same thing; the Room aggregate merges them
    before the rule reads them. The merged row is his and is counted."""
    import json
    from datetime import date, datetime, timedelta

    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    later = (date.today() + timedelta(days=9)).isoformat()
    title = "Send the capacity plan"
    project_id = _linked_meeting(hub, "m-premerged", "Capacity")
    hub.db.plugins.record_artifact(
        artifact_id="artifact-premerged", meeting_id="m-premerged", artifact_type="action_items",
        title="Actions", structured_json={"action_items": [{"task": title, "owner": "Dana", "due": ""}]},
        status="accepted", plugin_id="action_owner_enforcer", plugin_version="fence",
    )
    proposal = next(
        row for row in ProposalBridgeService(hub.db).bridge_meeting_artifacts("m-premerged")
        if row.text == title)
    _ok(hub.client.post(f"/api/proposals/{proposal.id}/confirm", json={"owner": "Dana", "due": later}))

    before = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    dana = [row for row in before["items"] if title in row["title"]]
    assert len(dana) == 1 and dana[0]["waiting"] is True, dana

    # A Watch's stored observation: a PR that asks the owner for changes. The
    # Room's own read (``ProjectService.room``) makes the attention row.
    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches (id, connector_id, query_kind, name, query_json, snapshot_json,"
            " enabled, last_success_at, last_error, project_id, created_at, updated_at)"
            " VALUES ('w-pr', 'gh', 'pull_requests', 'gh pull_requests', ?, ?, 1, ?, NULL, ?,"
            " datetime('now'), datetime('now'))",
            (json.dumps({"repository": "acme/app"}), json.dumps([{
                "number": 612, "title": title, "url": "https://github.com/acme/app/pull/612",
                "state": "OPEN", "isDraft": False, "reviewRequests": [],
                "reviewDecision": "CHANGES_REQUESTED", "checks": "passing",
                # Updated after the commitment: the Room's merge then leads
                # with Dana's row (longest waiting first), which is the case
                # that hid his work.
                "updatedAt": datetime.now().isoformat(),
            }]), datetime.now().isoformat(), project_id),
        )

    after = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    # The Room aggregate merged the two projections before the rule read them.
    room_rows = [row for row in after["roomItems"] if title in row["title"]]
    assert len(room_rows) == 1 and room_rows[0]["dedupCount"] == 2, room_rows
    assert {source["source"] for source in room_rows[0]["sources"]} == {"commitment", "github"}
    assert room_rows[0]["why"] == "WAITING ON DANA" and room_rows[0]["owner"] == "Dana", room_rows[0]
    rows = [row for row in after["items"] if title in row["title"]]
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["waiting"] is False, row
    assert row["why"].startswith("WAITING ON YOUR REVIEW"), row["why"]
    assert row["ref"] in [member["ref"] for member in after["members"]]
    # PHILO-15-09 (B11): the one number counts every row the desk draws: the
    # members and each source that could not be read (a Watch row is one).
    # PHILO-17 (needsyou): the sources of one cause are one row.
    from holdspeak.services.needs_you_membership import unread_source_groups

    def rows_of(answer):
        return len(answer["members"]) + len(unread_source_groups(answer["coverage"])) + len(answer.get("arming") or [])

    assert after["count"] == rows_of(after) and before["count"] == rows_of(before)
    assert len(after["members"]) == len(before["members"]) + 1, (before["coverage"], after["coverage"])
    assert after["waitingCount"] == before["waitingCount"] - 1
    assert _one_number(hub, brief=True) == after["count"]


@pytest.mark.parametrize("verb", ["confirm", "dismiss"])
def test_the_brief_does_not_ask_again_for_a_decision_he_settled(hub: Hub, verb: str) -> None:
    """Astra's second review of #818: after he confirms or dismisses the
    proposal, a new Brief has no decision-waiting line and no Review row."""
    from datetime import date, timedelta

    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    _linked_meeting(hub, "m-settled", "Release")
    hub.db.plugins.record_artifact(
        artifact_id="artifact-settled", meeting_id="m-settled", artifact_type="decisions",
        title="Decisions", structured_json={"decisions": [{"decision": "Ship on Friday"}]},
        plugin_id="decision_capture",
    )
    hub.db.decisions.reconcile_artifact("artifact-settled")
    assert [d.text for d in hub.db.decisions.list(lifecycle="recorded")] == ["Ship on Friday"]
    proposal = ProposalBridgeService(hub.db).bridge_meeting_artifacts("m-settled")[0]
    later = (date.today() + timedelta(days=9)).isoformat()
    body = {"owner": "Dana", "due": later} if verb == "confirm" else {}
    _ok(hub.client.post(f"/api/proposals/{proposal.id}/{verb}", json=body))
    # The recorded decision is still ``recorded``: the settlement is the proposal's.
    assert [d.text for d in hub.db.decisions.list(lifecycle="recorded")] == ["Ship on Friday"]

    brief = _ok(hub.client.post("/api/brief/generate"))
    brief = brief.get("brief") or brief
    assert "decision waiting" not in brief["headline"] and "decisions waiting" not in brief["headline"], brief["headline"]
    texts = [item["text"] for section in brief["sections"].values() for item in section]
    assert not any(text.startswith("Review decision") for text in texts), texts
    assert not any("Ship on Friday" in text and text.startswith("Review") for text in texts), texts
    answer = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    assert not any(str(member["ref"]).startswith("decision:") for member in answer["members"])
    assert _phrase(brief["headline"], "thing") == answer["count"]
