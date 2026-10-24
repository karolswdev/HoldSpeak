"""The daily-surface week (Betterment daily/RECIPE.md, the fixture of every slice).

Three meetings of one week, three people (Mira Okafor, Theo Park, Jun Sato),
seeded on an isolated hub through the product's own producers:

- ``POST /api/people/setup`` and ``POST /api/people/relationships`` (no alias);
- ``db.meetings.save_meeting`` with the summary's action items (the said dues);
- ``write_summary_items`` (the summary's decisions and actions artifact) and
  ``ProposalBridgeService.bridge_meeting_artifacts`` (the proposals);
- ``POST /api/proposals/{id}/confirm`` for the recon's nine keeps.

``seed(hub, monday=...)`` moves the week so that ``monday`` is its Monday.
On the recon's own week (2026-10-19) the said dues stay words. On another
week a said weekday would name a different day, so each said due is written
as the ISO day it names on the recon's week, moved by the same days.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from holdspeak.due_dates import resolve_due

WEEK = json.loads((Path(__file__).parent / "week.json").read_text())
MONDAY = date.fromisoformat(WEEK["monday"])
UNKEPT = set(WEEK["kept"]["unkept_decisions"])


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def _said(due: str | None, start: datetime, shift: timedelta) -> str | None:
    if due is None or not shift:
        return due
    day = resolve_due(due, start.date())
    return (day + shift).isoformat() if day is not None else due


def seed_people(client: Any) -> dict[str, str]:
    """Mira, Theo and Jun, through the People routes. No alias is set."""
    _ok(client.post("/api/people/setup", json={}))
    ids: dict[str, str] = {}
    for person in WEEK["people"]:
        created = _ok(client.post("/api/people/relationships", json={
            "display_name": person["display_name"], "relationship_kind": "direct_report",
        }), 201)
        ids[person["display_name"].split()[0]] = created["relationship"]["id"]
    return ids


def seed_meetings(db: Any, *, monday: date = MONDAY, file_into: Any = None, arrival: bool = False) -> None:
    """The three meetings, their summaries and their proposals (nothing kept).

    ``file_into(meeting_id)`` files each meeting before its summary is
    bridged (the recon's Project held all three). ``arrival``: the summary
    ends through the hub's own post-summary hook (``intel_queue
    ._on_intel_complete``), which keeps the promises on arrival (D3).
    """
    from holdspeak.intel.models import ActionItem
    from holdspeak.kernel.summary_items_projection import write_summary_items
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    shift = timedelta(days=(monday - MONDAY).days)
    for meeting in WEEK["meetings"]:
        start = datetime.fromisoformat(meeting["started_at"])
        moved = start + shift
        segments = []
        at = 0.0
        for speaker, text in meeting["segments"]:
            segments.append(TranscriptSegment(text=text, speaker=speaker, start_time=at, end_time=at + 20.0))
            at += 20.0
        actions = [
            {"task": a["task"], "owner": a["owner"], "due": _said(a["due"], start, shift)}
            for a in meeting["actions"]
        ]
        items = [ActionItem(task=a["task"], owner=a["owner"], due=a["due"]) for a in actions]
        db.meetings.save_meeting(MeetingState(
            id=meeting["id"], started_at=moved, ended_at=moved + timedelta(minutes=meeting["minutes"]),
            title=meeting["title"], segments=segments,
            intel=IntelSnapshot(timestamp=at, summary=meeting["summary"], action_items=items),
            intel_status="complete", intel_completed_at=moved + timedelta(minutes=meeting["minutes"] + 2),
        ))
        with db._connection() as conn:
            write_summary_items(
                conn, {"job_id": f"job-{meeting['id']}", "decisions": meeting["decisions"]},
                meeting["id"], [{**a, "id": item.id} for a, item in zip(actions, items)],
            )
        if file_into is not None:
            file_into(meeting["id"])
        if arrival:
            from holdspeak.intel_queue import _on_intel_complete

            _on_intel_complete(db, meeting["id"])
        else:
            ProposalBridgeService(db).bridge_meeting_artifacts(meeting["id"])


def seed_engine(client: Any) -> None:
    """The recon's engine: the LAN model, added to the Model Library and made
    the Default (``Default engine`` → the LAN row). Nothing is called."""
    defined = _ok(client.post("/api/inference/model-library/define-endpoint", json={"draft": {
        "request_id": "daily-week-engine", "profile_id": "lan-qwen", "expected_profile_revision": 0,
        "label": "192.168.1.43:8080", "provider_family": "openai_compatible", "model": "qwen3.8-27b",
        "endpoint": "http://192.168.1.43:8080/v1", "requires_key": False,
    }, "secret": None}))
    provider = defined["provider"]
    rows = {row["id"]: row for row in _ok(client.get("/api/inference/assignments"))["rows"]}
    _ok(client.post("/api/inference/assignments/set", json={
        "command_id": "daily-week-default", "expected_revision": rows["global"]["expected_revision"],
        "scope": {"kind": "global"},
        "entries": [{"profile_id": provider["profile_id"], "profile_revision": int(provider["profile_revision"])}],
    }))


def keep_nine(client: Any) -> list[str]:
    """The recon's nine Confirm presses, through the route the row's verb posts."""
    kept: list[str] = []
    for meeting in WEEK["meetings"]:
        proposals = _ok(client.get(f"/api/meetings/{meeting['id']}/follow-through-proposals"))["proposals"]
        for proposal in proposals:
            if proposal["state"] != "proposed" or proposal["text"] in UNKEPT:
                continue
            _ok(client.post(f"/api/proposals/{proposal['id']}/confirm"))
            kept.append(proposal["text"])
    assert len(kept) == 9, kept
    return kept


def seed(hub: Any, *, monday: date = MONDAY, keep: bool = True, engine: bool = False,
         arrival: bool = False) -> dict[str, str]:
    """The whole week on ``hub`` (a ``tests/unit/test_desk_needs_you.py`` Hub).

    Returns the People ids by first name, and the Project's id (``project``).

    ``engine``: the recon's LAN engine is the Default (no "No engine" row).
    ``arrival``: the summaries end through the hub's hook (D3: the promises
    are kept on arrival; ``keep`` is then ignored).
    """
    if engine:
        seed_engine(hub.client)
    people = seed_people(hub.client)
    project = _ok(hub.client.post("/api/projects", json={
        "name": WEEK["project"], "command_id": "daily-week-project"}))["project"]["id"]
    people["project"] = project
    seed_meetings(hub.db, monday=monday, arrival=arrival, file_into=lambda meeting_id: _ok(
        hub.client.post(f"/api/projects/{project}/meetings/{meeting_id}")))
    if keep and not arrival:
        keep_nine(hub.client)
    return people


# The frontend's recorded Tuesday remains one producer day as calendar time
# advances. These seams affect only the isolated rig that writes/checks its wire.
WIRE_DAY = date(2026, 10, 20)


def pin_wire_day(hub: Any, monkeypatch: Any, *, brief: bool = False) -> None:
    from holdspeak.services import (
        attention_ranking, follow_through_service, needs_you_aggregate,
        needs_you_membership, project_service,
    )

    class WireDate(date):
        @classmethod
        def today(cls) -> date:
            return WIRE_DAY

    monkeypatch.setattr(follow_through_service, "date", WireDate)
    wire_now = lambda: datetime(2026, 10, 20, 10, 0).astimezone()
    for module in (attention_ranking, needs_you_aggregate, needs_you_membership, project_service):
        monkeypatch.setattr(module, "local_wall", wire_now)
    if brief:
        hub.root.monday_brief_service._clock = wire_now


def normalize_wire_change_stamps(hub: Any, project_id: str) -> None:
    """Place only this isolated seed's four Changed facts in Tuesday's window."""
    from contextlib import closing
    from holdspeak.people import production_people_store

    stamp = "2026-10-20T07:40:00+00:00"
    with hub.db._connection() as conn:
        project = conn.execute("UPDATE projects SET created_at=? WHERE id=?", (stamp, project_id))
        decisions = conn.execute(
            "UPDATE follow_through_proposals SET decided_at=? "
            "WHERE state='confirmed' AND kind='decision' AND meeting_id IN (?, ?)",
            (stamp, "m-daily-architecture-review", "m-daily-platform-sync"),
        )
        assert project.rowcount == 1 and decisions.rowcount == 2
    store = production_people_store()
    with closing(store._connect()) as conn:
        people = conn.execute("UPDATE records SET created_at=? WHERE kind='relationship'", (stamp,))
        assert people.rowcount == 3
        conn.commit()
