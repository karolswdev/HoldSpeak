"""A displayed summary engine and its save revision come from one read."""
from contextlib import closing

from holdspeak.db import Database
from holdspeak.services import engine_door
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

JOB = "meeting.deferred_analysis"
SCOPE = {"kind": "capability", "capability_id": JOB}


def test_queue_selection_does_not_bind_old_content_to_a_new_revision(tmp_path, monkeypatch):
    with closing(Database(tmp_path / "snapshot.db")) as db:
        for name in ("before", "after"):
            _profile(db, name, claims=("language", _result_claim(JOB)))
        reader = InferenceAssignmentService(db)
        writer = InferenceAssignmentService(db)

        def save(profile, revision):
            return writer.set_assignment(OWNER, {
                "command_id": profile, "scope": SCOPE, "expected_revision": revision,
                "entries": [{"profile_id": profile, "profile_revision": 1}],
            })

        before = save("before", 0)
        original = reader._queue_resolution

        def resolve(conn, capability):
            result = original(conn, capability)
            # A separate connection commits while the display read is open.
            save("after", before["revision"])
            return result

        monkeypatch.setattr(reader, "_queue_resolution", resolve)
        shown = engine_door.summary_assignment(assignment_service=reader, principal=OWNER)
        assert shown["profileId"] == "before"
        assert shown["assignmentRevision"] == before["revision"]
        assert writer.saved_head(f"capability:{JOB}")["revision"] > shown["assignmentRevision"]


def test_clearing_a_summary_without_a_default_is_unassigned_and_keeps_its_revision(tmp_path):
    with closing(Database(tmp_path / "clear.db")) as db:
        _profile(db, "summary", claims=("language", _result_claim(JOB)))
        service = InferenceAssignmentService(db)
        selected = service.set_assignment(OWNER, {
            "command_id": "select", "scope": SCOPE, "expected_revision": 0,
            "entries": [{"profile_id": "summary", "profile_revision": 1}],
        })
        service.clear_assignment(OWNER, {
            "command_id": "clear", "scope": SCOPE, "capability_id": JOB,
            "expected_revision": selected["revision"],
        })
        shown = engine_door.summary_assignment(assignment_service=service, principal=OWNER)
        assert shown["status"] == "unassigned"
        assert shown["profileId"] is None
        assert shown["assignmentRevision"] == service.saved_head(f"capability:{JOB}")["revision"]
