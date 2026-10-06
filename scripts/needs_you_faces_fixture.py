#!/usr/bin/env python3
"""One seeded desk for the "every face says the hub's number" fence.

The PHILO-13 oracle week (``philo13_needs_you_fixture.seed_week``: Door
cards, a Room commitment, a muted Room, a decision to review, a failed
summary, no engines) plus one Room commitment the owner WAITS on someone
else for, minted through the real proposal bridge. It prints the payloads
the faces read, each from its real route or producer:

    needsYou   GET /api/desk/needs-you?fresh=1 (the hub's one rule)
    needsYouAfterMute  the same read after the owner mutes "A2 oracle room"
    brief      the morning's Brief (``MondayBriefService.generate``), made
               before A1 is marked done (``PATCH /api/all-action-items/A1``)
    door       GET /api/door
    projects   GET /api/projects

Usage (always with an isolated ``HOME``)::

    HOME=/tmp/x uv run python scripts/needs_you_faces_fixture.py --home /tmp/x
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import philo13_needs_you_fixture as fx  # noqa: E402

WAITING_TASK = "W1 Priya sends the vendor quote"


def _waiting_room_commitment(db) -> str:
    """A Room commitment owned by Priya and due later: the owner waits on it."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db.plugins.record_artifact(
        artifact_id="faces-waiting-artifact",
        meeting_id=fx.MAIN_MEETING_ID,
        artifact_type="action_items",
        title="Waiting extraction",
        structured_json={"action_items": [{
            "task": WAITING_TASK, "owner": "Priya", "due": "", "source_timestamp": 5.0,
        }]},
        status="accepted",
        plugin_id="action_owner_enforcer",
        plugin_version="fixture",
    )
    bridge = ProposalBridgeService(db)
    proposal = next(
        row for row in bridge.bridge_meeting_artifacts(fx.MAIN_MEETING_ID) if row.text == WAITING_TASK
    )
    result = bridge.confirm_proposal(
        Principal(PrincipalKind.OWNER, fx.OWNER_IDENTITY), proposal.id,
        due=(date.today() + timedelta(days=5)).isoformat(),
    )
    if result.get("state") != "confirmed":
        raise RuntimeError(f"the waiting commitment was not confirmed: {result}")
    return str(result.get("action_item_id") or "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", required=True)
    args = parser.parse_args()
    home = Path(args.home)
    db_path = home / ".local" / "share" / "holdspeak" / "holdspeak.db"
    seeded = fx.seed_week(db_path, home=home)

    from holdspeak.db import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.web.routes.monday_brief import _generated_label, _period_label

    db = Database(db_path)
    try:
        _waiting_room_commitment(db)
        # The morning's Brief, then the day moves on: A1 is marked done
        # through the real route. The Brief is a snapshot; the hub is live.
        brief = asdict(MondayBriefService(db).generate(Principal(PrincipalKind.OWNER, fx.OWNER_IDENTITY)))
        brief["period_label"] = _period_label(brief)
        brief["generated_label"] = _generated_label(brief)
        with fx._route_client(db) as client:
            done = client.patch(f"/api/all-action-items/{fx.A1_ID}", json={"status": "done"})
            if done.status_code != 200:
                raise RuntimeError(f"the real action-item route failed: {done.status_code} {done.text}")
            needs_you = client.get("/api/desk/needs-you?fresh=1").json()
            door = client.get("/api/door").json()
            projects = client.get("/api/projects").json()
            # The owner mutes the counted Room (the service behind PUT
            # /api/settings/heartbeat); the hub's next answer drops it (a face
            # must follow, Astra #872).
            from holdspeak.services.heartbeat_service import HeartbeatService

            rows = projects if isinstance(projects, list) else projects.get("projects", [])
            room = next(row["id"] for row in rows if row.get("name") == "A2 oracle room")
            HeartbeatService(db).update_settings({"muted_projects": [room]})
            needs_you_after_mute = client.get("/api/desk/needs-you?fresh=1").json()
    finally:
        db.close()
    print(json.dumps({
        "ids": seeded["ids"], "needsYou": needs_you, "needsYouAfterMute": needs_you_after_mute,
        "brief": brief,
        "door": door, "projects": projects,
    }, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
