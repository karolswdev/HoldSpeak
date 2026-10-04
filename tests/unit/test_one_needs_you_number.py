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
    # Custody stays as it is: the owner's own route carries the commitment;
    # an MCP agent and the stored Brief get the count, never the text.
    assert "Review the promotion case" in [row["title"] for row in answer["items"]]
    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error and "Review the promotion case" not in str(mcp)
    assert minted["commitment"] not in str(mcp)
    assert minted["commitment"].removeprefix("people:") not in str(mcp)
    with hub.db._connection() as conn:
        stored = " ".join(str(r["text"]) for r in conn.execute("SELECT text FROM monday_brief_items"))
    assert "Review the promotion case" not in stored and "1:1 commitment" in stored
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


def test_an_owned_item_not_reviewed_yet_reads_to_review(hub: Hub) -> None:
    """Dana's item is pending review: it HAS an owner, so it is never "Unassigned"."""
    from datetime import datetime

    from holdspeak.meeting_session import IntelSnapshot, MeetingState

    started = datetime.now().replace(microsecond=0)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-to-review", started_at=started, ended_at=started, title="Staffing",
        intel=IntelSnapshot(timestamp=started.timestamp(), summary="", action_items=[
            {"id": "ai-owned", "task": "Draft the onboarding checklist", "owner": "Dana",
             "due": None, "status": "pending", "review_state": "pending",
             "source_timestamp": None, "created_at": started.isoformat()},
            {"id": "ai-no-owner", "task": "Book the room", "owner": None,
             "due": None, "status": "pending", "review_state": "pending",
             "source_timestamp": None, "created_at": started.isoformat()},
        ]),
        intel_status="completed", capture_status="finalized",
    ))
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    rows = {row["ref"]: row for row in answer["items"]}
    assert rows["ai-owned"]["why"] == "TO REVIEW"
    assert rows["ai-owned"]["_toReview"] is True and rows["ai-owned"]["_isUnassigned"] is False
    assert rows["ai-no-owner"]["why"] == "UNASSIGNED"
    assert rows["ai-no-owner"]["_isUnassigned"] is True and rows["ai-no-owner"]["_toReview"] is False

    brief = _ok(hub.client.post("/api/brief/generate"))
    waiting = [item["text"] for item in (brief.get("brief") or brief)["sections"]["waiting"]]
    assert "To review: Draft the onboarding checklist" in waiting
    assert "Unassigned: Book the room" in waiting
    assert "Unassigned: Draft the onboarding checklist" not in waiting


# ── People custody (Astra's review of #788, P1-1 and P1-2) ───────────────

SENTINEL = "ZQ-SENTINEL-7f3a91 promotion case for Dana"


def _commit(hub: Hub, body: str) -> str:
    """Mint one People commitment through the real People routes; its record id."""
    _ok(hub.client.post("/api/people/setup"))
    relationship = _ok(hub.client.post(
        "/api/people/relationships", json={"display_name": "Dana"}), 201)["relationship"]
    request = _ok(hub.client.post(
        f"/api/people/relationships/{relationship['id']}/requests", json={"body": body}), 201)["request"]
    return str(_ok(hub.client.post(f"/api/people/requests/{request['id']}/accept", json={}))["commitment"]["id"])


def _every_table_text(db: Any) -> dict[str, str]:
    out: dict[str, str] = {}
    with db._connection() as conn:
        tables = [str(r["name"]) for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for table in tables:
            try:
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
            except Exception:  # a virtual table's shadow that cannot be read
                continue
            out[table] = "\n".join(repr(tuple(row)) for row in rows)
    return out


def test_people_text_reaches_no_table_and_no_log(hub: Hub, caplog: pytest.LogCaptureFixture, tmp_path: Path) -> None:
    """A sentinel commitment, read through every reader, is in no plaintext store."""
    import logging

    from holdspeak.services.heartbeat_service import HeartbeatService

    caplog.set_level(logging.DEBUG)
    commitment_id = _commit(hub, SENTINEL)

    # Every reader. The owner's own route is the only one that may carry it.
    route = _ok(hub.client.get("/api/desk/needs-you"))
    fresh = _ok(hub.client.get("/api/desk/needs-you?fresh=1"))
    assert SENTINEL in str(route) and SENTINEL in str(fresh)
    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error, mcp
    heartbeat = HeartbeatService(hub.db)
    assert heartbeat.notification_count(OWNER) == route["count"] == mcp["count"]
    heartbeat.run_sweep(OWNER)
    brief = _ok(hub.client.post("/api/brief/generate"))
    latest = _ok(hub.client.get("/api/brief/latest"))
    # The service call itself (observed) withholds the text.
    direct = hub.root.project_service.needs_you(OWNER)

    leaks = [table for table, text in _every_table_text(hub.db).items()
             if SENTINEL in text or commitment_id in text]
    assert leaks == [], f"People text or id in plaintext tables: {leaks}"
    for name, value in (("mcp", mcp), ("brief", brief), ("latest", latest), ("service", direct)):
        assert SENTINEL not in str(value), name
        assert commitment_id not in str(value), name

    assert SENTINEL not in caplog.text and commitment_id not in caplog.text
    # No file under the hub's home holds it in the clear either (the People
    # sidecar is encrypted; the main database and its WAL are plaintext).
    needle = SENTINEL.encode("utf-8")
    holders = [str(path) for path in tmp_path.rglob("*") if path.is_file() and needle in path.read_bytes()]
    assert holders == [], holders


def test_a_people_row_never_merges_with_another_row(hub: Hub) -> None:
    """Astra's repro: a commitment and an overdue action share a normalized title."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    title = "Send the capacity plan"
    commitment_id = _commit(hub, title)
    is_error, action = hub.mcp("door.add_item", {"task": "send the  capacity plan", "owner": "Dana", "due": yesterday})
    assert not is_error, action

    route = _ok(hub.client.get("/api/desk/needs-you"))
    refs = [member["ref"] for member in route["members"]]
    # Two obligations, two members: no merge on the owner's route either.
    assert f"people:{commitment_id}" in refs and str(action["id"]) in refs
    assert not any(
        source.get("source") == "people_commitment"
        for row in route["items"] if row.get("source") != "people_commitment"
        for source in row.get("sources") or []
    )

    is_error, mcp = hub.mcp("desk.needs_you", {})
    assert not is_error, mcp
    assert mcp["count"] == route["count"]
    assert commitment_id not in str(mcp)
    people_rows = [row for row in mcp["items"] if row.get("source") == "people_commitment"]
    assert [row["title"] for row in people_rows] == ["1:1 commitment"]
    assert "sources" not in people_rows[0] and "_doorCard" not in people_rows[0]
    # The action item's own text is plain work data and stays readable.
    assert any(row.get("ref") == str(action["id"]) for row in mcp["items"])


def test_withhold_redacts_a_row_that_carries_people_in_a_merged_source() -> None:
    """Belt: even a merged row that holds a People projection is withheld whole."""
    from holdspeak.services.needs_you_membership import withhold_people_content

    merged = {
        "id": "door:ai_1", "ref": "ai_1", "source": "action_item", "title": "Send the plan",
        "sources": [
            {"id": "door:ai_1", "source": "action_item", "title": "Send the plan"},
            {"id": "door:people:c-9", "source": "people_commitment", "title": "Send the plan (private)"},
        ],
    }
    out = withhold_people_content({"items": [merged], "members": [{"ref": "ai_1", "kind": "attention"}], "count": 1})
    assert "private" not in str(out) and "c-9" not in str(out)
    assert out["count"] == 1 and len(out["members"]) == 1
    assert out["members"][0]["ref"] == out["items"][0]["ref"]
