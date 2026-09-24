"""Resolve the canvas c1 question through the real production writers."""
import datetime as dt
import json
from pathlib import Path
import tempfile

from holdspeak.db import Database
from holdspeak.meeting_session.models import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.monday_brief_service import MondayBriefService


with tempfile.TemporaryDirectory(prefix="philo402-this-week-") as temp:
    db = Database(Path(temp) / "probe.db")
    owner = Principal(PrincipalKind.OWNER, "philo402-probe")
    db.meetings.save_meeting(MeetingState(
        id="canvas-meeting", title="Plan review",
        started_at=dt.datetime(2026, 9, 21, 10),
        ended_at=dt.datetime(2026, 9, 21, 11),
    ))
    db.plugins.record_artifact(
        artifact_id="canvas-decision", meeting_id="canvas-meeting",
        artifact_type="decisions", title="Decisions",
        structured_json={"decisions": [{"decision": "Send the Q4 plan to Dana"}]},
        plugin_id="decision_capture",
    )
    decision = db.decisions.list()[0]
    DecisionLifecycleService(db).transition(owner, decision.id, "accept")
    commitment = FollowThroughService(db).commit_decision(
        owner, decision.id, owner="Karol", due_at="2026-09-25",
    )
    outputs = []
    for day in (dt.datetime(2026, 9, 23, 17, 40), dt.datetime(2026, 9, 24, 8, 2)):
        service = MondayBriefService(db, clock=lambda day=day: day)
        unexcluded = service._collect_decisions(owner)
        assert any(item.text.startswith("Commitment due 2026-09-25:") for item in unexcluded)
        brief = service.generate(owner)
        counted = [item for item in brief.sections["this_week"]
                   if item.source_ref == "meeting_watch:commitments_due"]
        assert len(counted) == 1 and counted[0].text == "1 commitment due this week"
        assert not any(item.text.startswith("Commitment due") for item in brief.sections["decisions"])
        outputs.append({
            "producer_day": day.isoformat(), "brief_id": brief.id,
            "this_week": {"text": counted[0].text, "detail": counted[0].detail},
            "decisions": [item.text for item in brief.sections["decisions"]],
            "without_this_week_exclusion": [item.text for item in unexcluded],
        })
    print(json.dumps({"decision_id": decision.id, "commitment_id": commitment["id"],
                      "days": outputs, "verdict": "PASS: c1 belongs to THIS WEEK"}, indent=2))
