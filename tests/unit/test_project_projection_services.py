from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ValidationError
from holdspeak.services.project_service import ProjectService
from holdspeak.services.projection_service import ProjectionService


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


def test_project_service_preserves_archive_relationship_and_meeting_validation(tmp_path) -> None:
    db = Database(tmp_path / "projects.db")
    service = ProjectService(db)
    project = service.create_project(OWNER, {"name": "Launch", "keywords": "ship, desk"})
    assert project["keywords"] == ["ship", "desk"]
    assert service.add_resource(OWNER, project["id"], "note:n1", {"relationship": "source"})["resource_ref"] == "note:n1"
    assert service.remove_resource(OWNER, project["id"], "note:n1") is True
    with pytest.raises(NotFound):
        service.associate_meeting(OWNER, project["id"], "missing")
    assert service.archive_project(OWNER, project["id"]) is True
    assert service.list_projects(OWNER) == []
    assert service.list_projects(OWNER, {"include_archived": True})[0]["is_archived"] is True


def test_project_service_validates_mutable_fields_and_projects_exist(tmp_path) -> None:
    service = ProjectService(Database(tmp_path / "projects.db"))
    with pytest.raises(ValidationError):
        service.create_project(OWNER, {"name": ""})
    project = service.create_project(OWNER, {"name": "Launch"})
    with pytest.raises(ValidationError):
        service.update_project(OWNER, project["id"], {"detection_threshold": 2})
    with pytest.raises(NotFound):
        service.summary(OWNER, "missing")


def test_projection_service_validates_filters_and_persists_presentation(tmp_path) -> None:
    db = Database(tmp_path / "projections.db")
    db.meetings.save_meeting(MeetingState(id="m1", started_at=datetime.now(), title="Daily", capture_status="recoverable"))
    service = ProjectionService(db)
    with pytest.raises(ValidationError):
        service.list(OWNER, {"kind": "other"})
    projection_id = service.list(OWNER)["projections"][0]["id"]
    assert service.set_presentation(OWNER, projection_id, {"action": "dismiss"})["success"] is True
    assert service.list(OWNER)["projections"] == []
    with pytest.raises(NotFound):
        service.set_presentation(OWNER, "missing", {"action": "dismiss"})
