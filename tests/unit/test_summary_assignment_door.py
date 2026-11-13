"""Concierge reads the summary selection from the engine door's owner ports."""
from __future__ import annotations

import pytest
from contextlib import closing

from holdspeak.db import Database
from holdspeak.services import concierge_service, engine_door
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

JOB = "meeting.deferred_analysis"
SCOPE = {"kind": "capability", "capability_id": JOB}


def test_summary_selection_keeps_inheritance_exact_revision_and_off(tmp_path):
    with closing(Database(tmp_path / "summary.db")) as db:
        _profile(db, "summary", claims=("language", _result_claim(JOB)))
        assignments = InferenceAssignmentService(db)

        def read():
            return engine_door.summary_assignment(assignment_service=assignments, principal=OWNER)

        def save(scope, revision, key):
            return assignments.set_assignment(OWNER, {
                "command_id": key, "scope": scope, "expected_revision": revision,
                "entries": [{"profile_id": "summary", "profile_revision": 1}],
            })

        assert read()["status"] == "unassigned"
        assert read()["assignmentRevision"] == 0
        save({"kind": "global"}, 0, "default")
        assert read()["inheritedFrom"] == "global"
        assert read()["assignmentRevision"] == 0
        exact = save(SCOPE, 0, "exact")
        assert read()["assignmentRevision"] == exact["revision"]
        assert "inheritedFrom" not in read()
        assignments.clear_assignment(OWNER, {
            "command_id": "clear", "scope": SCOPE, "capability_id": JOB,
            "expected_revision": exact["revision"],
        })
        cleared = read()
        assert cleared["status"] == "assigned"
        assert cleared["inheritedFrom"] == "global"
        assert cleared["assignmentRevision"] > exact["revision"]
        save(SCOPE, cleared["assignmentRevision"], "again")
        assignments.set_capability_off(OWNER, capability_id=JOB)
        off = read()
        assert off["status"] == "off"
        assert off["profileId"] is None
        assert assignments.resolve_for_queue(OWNER, capability_id=JOB)["status"] == "off"


def test_concierge_uses_the_door_in_its_selection_receipt(tmp_path, monkeypatch):
    with closing(Database(tmp_path / "receipt.db")) as db:
        _profile(db, "summary", claims=("language", _result_claim(JOB)))
        assignments = InferenceAssignmentService(db)
        reads = []
        original = engine_door.summary_assignment

        def read(**kwargs):
            reads.append(kwargs)
            return original(**kwargs)

        monkeypatch.setattr(engine_door, "summary_assignment", read)
        result = concierge_service.assign_summary(
            assignment_service=assignments, principal=OWNER, db=db,
            profile_id="summary", profile_revision=1, expected_assignment_revision=0,
            command_id="select-summary",
        )
        assert result["status"] == "succeeded"
        assert reads == [{"assignment_service": assignments, "principal": OWNER}]
        assert result["summaryAssignment"]["profileId"] == "summary"


def test_summary_selection_keeps_the_assignment_owners_access_check(tmp_path):
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError

    with closing(Database(tmp_path / "owner.db")) as db:
        with pytest.raises(ServiceError) as denied:
            engine_door.summary_assignment(assignment_service=InferenceAssignmentService(db),
                                          principal=Principal(PrincipalKind.AGENT, "worker"))
        assert denied.value.context["status"] == 403
