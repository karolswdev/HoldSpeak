#!/usr/bin/env python3
"""HS-49-06 dogfood: meeting aftercare, end to end, no mic / no LLM.

Drives the same HTTP endpoints the browser calls to prove the loop closes:

  1. seed a prior + a current meeting (decisions + action items), no mic,
  2. read the aftercare digest -> what's still open (by owner), what was decided,
     and a real since-last-meeting diff,
  3. read a result's transcript provenance -> the segment that justifies it,
  4. accept an action -> file it as a GitHub-issue actuator PROPOSAL (recorded
     only; nothing sent),
  5. approve the proposal -> execute it through the existing guarded executor
     (stub connector) -> it executes and is audited,
  6. generate the local follow-up draft -> decisions + open items + owners.

Every number comes from `holdspeak/meeting_aftercare.py` over real DB rows, and
the actuator path is the real `ActuatorExecutor` (a stub connector stands in for
`gh`, the same pattern the integration tests use). A temp DB keeps the developer's
real state untouched.

    .venv/bin/python scripts/dogfood_meeting_aftercare.py
    .venv/bin/python scripts/dogfood_meeting_aftercare.py <transcript.txt>
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

ISSUE_ACTUATOR_ID = "github_issue_actuator"


def _action(item_id, task, *, owner=None, status="pending", review_state="pending", source_timestamp=None):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": "Friday",
        "status": status,
        "review_state": review_state,
        "source_timestamp": source_timestamp,
        "created_at": datetime(2026, 6, 5, 10, 0, 0).isoformat(),
    }


def main(argv: list[str]) -> int:
    from fastapi.testclient import TestClient

    from holdspeak.db import get_database, reset_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.plugins.actuator_executor import ActuatorExecutionError, ActuatorExecutor
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out_path = Path(argv[0]) if argv else None
    lines: list[str] = []

    def say(msg: str) -> None:
        print(msg)
        lines.append(msg)

    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "aftercare.db")

    say("HS-49-06 dogfood - meeting aftercare, end to end (no mic / no LLM)")
    say("")
    try:
        # 1. seed a prior + a current meeting.
        db.meetings.save_meeting(
            MeetingState(
                id="prior",
                started_at=datetime(2026, 6, 2, 9, 0, 0),
                title="API design kickoff",
                intel=IntelSnapshot(
                    timestamp=0.0,
                    action_items=[_action("p1", "Stand up the staging cluster", owner="Priya", status="done")],
                ),
            )
        )
        db.plugins.record_artifact(
            artifact_id="prior-decisions", meeting_id="prior", artifact_type="decisions",
            title="Decisions", plugin_id="decision_capture",
            structured_json={"decisions": [{"decision": "Use Postgres for the primary store"}]},
        )
        db.meetings.save_meeting(
            MeetingState(
                id="current",
                started_at=datetime(2026, 6, 5, 10, 0, 0),
                title="API design follow-up",
                segments=[
                    TranscriptSegment(text="Let's open the follow-up.", speaker="Me", start_time=0.0, end_time=60.0),
                    TranscriptSegment(text="Priya owns the rate limiter.", speaker="Sam", start_time=60.0, end_time=140.0),
                ],
                intel=IntelSnapshot(
                    timestamp=0.0,
                    action_items=[
                        _action("c1", "Wire the rate limiter", owner="Priya", source_timestamp=72.0),
                        _action("c2", "Pick a service name"),
                    ],
                ),
            )
        )
        db.plugins.record_artifact(
            artifact_id="current-decisions", meeting_id="current", artifact_type="decisions",
            title="Decisions", plugin_id="decision_capture",
            structured_json={"decisions": [
                {"decision": "Use Postgres for the primary store", "rationale": "Transactions"},
                {"decision": "Adopt feature flags for the rollout"},
            ]},
        )
        say("1. seeded prior (API design kickoff) + current (API design follow-up)")

        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        )
        client = TestClient(server.app)

        # 2. the aftercare digest: open / decided / changed.
        digest = client.get("/api/meetings/current/aftercare").json()
        owners = ", ".join(
            f"{g['owner'] or 'Unassigned'} ({g['count']})" for g in digest["open_items"]["by_owner"]
        )
        say("")
        say("2. aftercare digest:")
        say(f"   still open ({digest['open_items']['total']}): {owners}")
        say(f"   decided: {[d['decision'] for d in digest['decisions']]}")
        since = digest["since_last_meeting"]
        say(f"   since '{since['previous_meeting']['title']}': "
            f"new_decisions={[d['decision'] for d in since['new_decisions']]} "
            f"new_actions={[a['task'] for a in since['new_actions']]} "
            f"closed={[a['task'] for a in since['closed_actions']]}")
        assert digest["open_items"]["total"] == 2
        assert since["changed"] is True
        assert [d["decision"] for d in since["new_decisions"]] == ["Adopt feature flags for the rollout"]
        assert [a["task"] for a in since["closed_actions"]] == ["Stand up the staging cluster"]

        # 3. provenance: the transcript moment that justifies the open item.
        priya = next(g for g in digest["open_items"]["by_owner"] if g["owner"] == "Priya")["items"][0]
        prov = priya["provenance"]
        say("")
        say(f"3. provenance for '{priya['task']}': source {prov['source_timestamp']}s "
            f"-> segment #{prov['segment_index']} (\"{prov['text_preview']}\")")
        assert prov["segment_index"] == 1  # 72.0 falls in the second segment [60, 140)

        # 4. accept the action, then file it as a proposal (recorded only).
        client.patch("/api/all-action-items/c1/review", json={"review_state": "accepted"})
        filed = client.post(
            "/api/meetings/current/aftercare/file-issue",
            json={"action_item_id": "c1", "repo": "acme/app"},
        ).json()["proposal"]
        say("")
        say(f"4. accepted 'Wire the rate limiter' -> filed proposal {filed['id'][:8]} "
            f"({filed['action']} -> {filed['target']}, status={filed['status']})")
        assert filed["status"] == "proposed"

        # 5. approve + execute through the real guarded executor (stub connector).
        calls: list = []

        def stub_connector(view):
            calls.append(view)
            return {"url": "https://github.com/acme/app/issues/12", "issue": 12}

        executor = ActuatorExecutor(
            db, connector=stub_connector, allow_actuators=True, allowed_actuator_ids=[ISSUE_ACTUATOR_ID]
        )
        try:
            executor.execute(filed["id"])
            raise AssertionError("a proposed proposal must NOT execute")
        except ActuatorExecutionError:
            say("   guard: a proposed (un-approved) proposal is refused by the executor (no egress)")
        assert calls == []

        client.post(
            "/api/meetings/current/proposals/" + filed["id"] + "/decision",
            json={"decision": "approved", "decided_by": "dogfood"},
        )
        result = executor.execute(filed["id"])
        audit = [a.to_status for a in db.actuators.list_audit(filed["id"])]
        say(f"5. approved -> executed via connector: issue #{result.result['issue']}; audit {audit}")
        assert result.status == "executed"
        assert audit == ["proposed", "approved", "executed"]

        # 6. the local follow-up draft.
        draft = client.get("/api/meetings/current/followup-draft").json()["markdown"]
        say("")
        say("6. follow-up draft (local, preview + copy):")
        for line in draft.splitlines():
            say(f"   | {line}")
        assert "## What we decided" in draft and "## Open items" in draft
        assert "- Priya: Wire the rate limiter" in draft

        say("")
        say("PASS: open/decided/changed -> show me the moment -> accept + file -> "
            "approve + execute (audited) -> draft the follow-up. Nothing ran without "
            "approval; nothing was sent by the draft.")
    finally:
        reset_database()

    if out_path is not None:
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote transcript: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
