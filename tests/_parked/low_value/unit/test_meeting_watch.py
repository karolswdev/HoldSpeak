# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_meeting_watch.py to restore.

# ruff: noqa


# --- TestMeetingWatchSource::test_zero_egress: P5: named 'zero egress' but asserts only len(entities)==1, which test_entities_from_seeded_meetings already asserts
# (was a method of class TestMeetingWatchSource)
def test_zero_egress(self, db):
    """The adapter makes no CLI or network calls -- pure DB reads."""
    project_id = _seed_project(db)
    mid = _seed_meeting(db, title="Standup")
    _link_meeting_to_project(db, mid, project_id)

    # The adapter takes db= and makes only DB calls.
    # If it tried CLI/network, it would fail in this env.
    entities = MeetingWatchSource(db=db).snapshot(
        OWNER, query_kind="meetings", query={"project_id": project_id},
    )
    assert len(entities) == 1


# --- TestMeetingWatchSource::test_entity_shape: P6: asserts required keys are present, not their values
# (was a method of class TestMeetingWatchSource)
def test_entity_shape(self, db):
    project_id = _seed_project(db)
    mid = _seed_meeting(db, title="Sprint Planning")
    _link_meeting_to_project(db, mid, project_id)

    entities = MeetingWatchSource(db=db).snapshot(
        OWNER, query_kind="meetings", query={"project_id": project_id},
    )

    assert len(entities) == 1
    entity = entities[0]
    required_keys = {
        "id", "entity_type", "title", "date", "participants",
        "decisions_count", "commitments_count", "intel_status", "updated_at",
    }
    assert required_keys <= set(entity.keys())
    assert entity["entity_type"] == "meeting"


# --- TestProjectServiceMeetingMaps: P1: looks up one key in two private constant dicts and asserts the literal
class TestProjectServiceMeetingMaps:

    def test_provider_to_connector(self):
        from holdspeak.services.project_service import _PROVIDER_TO_CONNECTOR
        assert _PROVIDER_TO_CONNECTOR["meeting"] == "meeting"

    def test_subject_to_query_kind(self):
        from holdspeak.services.project_service import _SUBJECT_TO_QUERY_KIND
        assert _SUBJECT_TO_QUERY_KIND["meeting"] == "meetings"
