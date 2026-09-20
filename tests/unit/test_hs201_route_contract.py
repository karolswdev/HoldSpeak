"""Phase 201's checked disclosure contract, observed through public reads."""
from datetime import datetime

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_service import MeetingService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim


@pytest.fixture
def meeting_db(tmp_path):
    db = Database(tmp_path / "disclosure.db")
    meeting = MeetingState(
        id="disclosure-meeting", title="Weekly review", started_at=datetime.now(),
        segments=[TranscriptSegment("We agreed to ship the report.", "Me", 0.0, 2.0)],
    )
    db.meetings.save_meeting(meeting)
    return db, meeting


def assign_summary(db, profiles, *, expected_revision=0, command="select-summary"):
    return InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": command, "expected_revision": expected_revision,
        "scope": {"kind": "capability", "capability_id": "meeting.deferred_analysis"},
        "entries": [{"profile_id": profile, "profile_revision": 1} for profile in profiles],
    })


def summary_profile(db, profile):
    _profile(db, profile, claims=("language", "structured_output", _result_claim("meeting.deferred_analysis")),
             modalities=("language", "text"))


@pytest.mark.parametrize("reader", ["detail", "ledger", "recovery"])
def test_unresolved_route_is_unavailable_never_local_before_post(meeting_db, reader):
    db, meeting = meeting_db
    if reader == "detail":
        value = MeetingService(db).get_meeting(OWNER, meeting.id)
    elif reader == "ledger":
        value = MeetingService(db).list_meetings(OWNER)["meetings"][0]
    else:
        value = MeetingIntelService(db).get_recovery(OWNER, meeting.id)
    route = value["planned_route"]
    assert route["status"] == "unavailable"
    assert route["selection_hash"] is None
    assert route["legs"] == []
    assert route["reason_code"] and "_" not in route["reason_code"]
    assert "local" not in str(route).lower()
    assert db.intel.get_intel_job(meeting.id) is None


def test_planned_route_discloses_all_ordered_legs_and_stable_revision_hash(meeting_db):
    db, meeting = meeting_db
    for profile in ("summary-first", "summary-fallback"):
        summary_profile(db, profile)
    assign_summary(db, ["summary-first", "summary-fallback"])
    service = MeetingIntelService(db)
    first = service.get_recovery(OWNER, meeting.id)["planned_route"]
    again = service.get_recovery(OWNER, meeting.id)["planned_route"]
    assert first == again  # generated plan IDs and timestamps do not enter the hash
    assert first["status"] == "ready" and first["selection_hash"]
    assert [leg["profile_id"] for leg in first["legs"]] == ["summary-first", "summary-fallback"]
    assert [leg["ordinal"] for leg in first["legs"]] == [1, 2]
    for leg in first["legs"]:
        assert set(leg) == {"ordinal", "host", "boundary", "profile_id", "profile_revision", "deployment_revision_id"}
        assert leg["host"] and leg["boundary"] == "local"
        assert leg["profile_revision"] == 1 and leg["deployment_revision_id"]
    assign_summary(db, ["summary-first", "summary-fallback"], expected_revision=1, command="reselect-summary")
    revised = service.get_recovery(OWNER, meeting.id)["planned_route"]
    assert revised["legs"] == first["legs"]
    assert revised["selection_hash"] != first["selection_hash"]


def test_group_assignment_cannot_be_disclosed_as_service_route(meeting_db):
    db, meeting = meeting_db
    summary_profile(db, "summary-group-only")
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "select-group", "expected_revision": 0,
        "scope": {"kind": "group", "group_id": "meetings"},
        "entries": [{"profile_id": "summary-group-only", "profile_revision": 1}],
    })
    route = MeetingIntelService(db).get_recovery(OWNER, meeting.id)["planned_route"]
    assert route["status"] == "unavailable" and route["legs"] == []
