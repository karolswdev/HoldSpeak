"""HS-157-03 -- ProjectService characterization: pin every public method's
current result shape and error behavior exactly as it stands today.

Change NO runtime code. Oddities are documented; the characterization is truth.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ValidationError
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "char-test-owner")

# ── Fixture ──────────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "project-char.db")
    svc = ProjectService(db)
    yield db, svc
    reset_database()


def _create_project(svc: ProjectService, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": "Test Project", **overrides}
    return svc.create_project(OWNER, payload)


def _save_meeting(db: Database, meeting_id: str, title: str = "Stand-up") -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=datetime(2025, 1, 15, 10, 0),
        title=title, capture_status="finalized",
    ))


# ── create_project ───────────────────────────────────────────────────────


class TestCreateProject:
    def test_success_shape(self, rig) -> None:
        _db, svc = rig
        result = _create_project(svc, name="Alpha", description="desc",
                                 keywords=["k1", "k2"], team_members=["Alice"],
                                 detection_threshold=0.5)
        assert isinstance(result, dict)
        # HS-157-03 legacy keys (unchanged)
        expected_keys = {"id", "name", "description", "keywords", "team_members",
                         "context", "detection_threshold", "is_archived",
                         "meeting_count", "created_at", "updated_at"}
        # HS-158-02 additive envelope keys
        additive_keys = {"result_kind", "project_revision", "changed_refs",
                         "project_id"}
        assert expected_keys <= set(result.keys())
        assert additive_keys <= set(result.keys())
        assert result["name"] == "Alpha"
        assert result["description"] == "desc"
        assert result["keywords"] == ["k1", "k2"]
        assert result["team_members"] == ["Alice"]
        assert result["detection_threshold"] == 0.5
        assert result["is_archived"] is False
        assert result["meeting_count"] == 0
        assert result["id"].startswith("proj-")
        # Timestamps are ISO strings
        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)

    def test_empty_name_raises_validation(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(ValidationError, match="name is required"):
            _create_project(svc, name="")

    def test_none_name_raises_validation(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(ValidationError, match="name is required"):
            svc.create_project(OWNER, {})

    def test_bad_threshold_raises_validation(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(ValidationError, match="detection_threshold"):
            _create_project(svc, detection_threshold="not-a-number")

    def test_threshold_out_of_range(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(ValidationError, match="detection_threshold"):
            _create_project(svc, detection_threshold=1.5)

    def test_keywords_from_csv_string(self, rig) -> None:
        """Keywords can be a comma-separated string."""
        _db, svc = rig
        result = _create_project(svc, keywords="a, b, c")
        assert result["keywords"] == ["a", "b", "c"]

    def test_default_values(self, rig) -> None:
        _db, svc = rig
        result = _create_project(svc)
        assert result["description"] == ""
        assert result["keywords"] == []
        assert result["team_members"] == []
        assert result["context"] == {}
        assert result["detection_threshold"] == 0.4  # service default


# ── list_projects ────────────────────────────────────────────────────────


class TestListProjects:
    def test_empty_list(self, rig) -> None:
        _db, svc = rig
        result = svc.list_projects(OWNER)
        assert result == []

    def test_returns_project_payloads(self, rig) -> None:
        _db, svc = rig
        _create_project(svc, name="P1")
        _create_project(svc, name="P2")
        result = svc.list_projects(OWNER)
        assert len(result) == 2
        assert all(isinstance(p, dict) for p in result)
        names = {p["name"] for p in result}
        assert names == {"P1", "P2"}

    def test_archived_excluded_by_default(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc, name="Archive Me")
        svc.archive_project(OWNER, proj["id"])
        result = svc.list_projects(OWNER)
        assert len(result) == 0

    def test_include_archived(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc, name="Archive Me")
        svc.archive_project(OWNER, proj["id"])
        result = svc.list_projects(OWNER, {"include_archived": True})
        assert len(result) == 1
        assert result[0]["is_archived"] is True


# ── get_project ──────────────────────────────────────────────────────────


class TestGetProject:
    def test_success_shape(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.get_project(OWNER, created["id"])
        assert result["id"] == created["id"]
        expected_keys = {"id", "name", "description", "keywords", "team_members",
                         "context", "detection_threshold", "is_archived",
                         "meeting_count", "created_at", "updated_at"}
        # get_project is a READ -- no additive envelope keys
        assert expected_keys <= set(result.keys())

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.get_project(OWNER, "proj-nonexistent")


# ── update_project ───────────────────────────────────────────────────────


class TestUpdateProject:
    def test_patch_name(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.update_project(OWNER, created["id"], {"name": "Renamed"})
        assert result["name"] == "Renamed"
        assert result["id"] == created["id"]

    def test_patch_description(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.update_project(OWNER, created["id"], {"description": "Updated"})
        assert result["description"] == "Updated"

    def test_patch_keywords_replaces(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc, keywords=["old"])
        result = svc.update_project(OWNER, created["id"], {"keywords": ["new"]})
        assert result["keywords"] == ["new"]

    def test_patch_threshold(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.update_project(OWNER, created["id"], {"detection_threshold": 0.8})
        assert result["detection_threshold"] == 0.8

    def test_empty_patch_is_noop(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.update_project(OWNER, created["id"], {})
        assert result["name"] == created["name"]

    def test_empty_name_raises(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        with pytest.raises(ValidationError, match="cannot be empty"):
            svc.update_project(OWNER, created["id"], {"name": ""})

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.update_project(OWNER, "proj-gone", {"name": "X"})

    def test_result_shape(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.update_project(OWNER, created["id"], {"name": "New"})
        expected_keys = {"id", "name", "description", "keywords", "team_members",
                         "context", "detection_threshold", "is_archived",
                         "meeting_count", "created_at", "updated_at"}
        # HS-158-02 additive: result_kind, project_revision, changed_refs, project_id
        assert expected_keys <= set(result.keys())
        assert "result_kind" in result
        assert "project_revision" in result


# ── archive_project ──────────────────────────────────────────────────────


class TestArchiveProject:
    def test_returns_true(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        result = svc.archive_project(OWNER, created["id"])
        assert result is True

    def test_project_becomes_archived(self, rig) -> None:
        _db, svc = rig
        created = _create_project(svc)
        svc.archive_project(OWNER, created["id"])
        after = svc.get_project(OWNER, created["id"])
        assert after["is_archived"] is True

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.archive_project(OWNER, "proj-gone")


# ── list_briefings ───────────────────────────────────────────────────────


class TestListBriefings:
    def test_empty_shape(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.list_briefings(OWNER, proj["id"])
        assert isinstance(result, dict)
        assert result["project_id"] == proj["id"]
        assert result["briefings"] == []

    def test_filters_by_project_id(self, rig) -> None:
        db, svc = rig
        p1 = _create_project(svc, name="P1")
        p2 = _create_project(svc, name="P2")
        # Seed a briefing annotation for p1
        db.activity.create_activity_annotation(
            source_connector_id="meeting_context",
            annotation_type="meeting_context_briefing",
            title="Briefing for P1",
            value={"project_id": p1["id"], "content": "some briefing"},
            confidence=0.9,
        )
        # Seed a briefing for p2
        db.activity.create_activity_annotation(
            source_connector_id="meeting_context",
            annotation_type="meeting_context_briefing",
            title="Briefing for P2",
            value={"project_id": p2["id"], "content": "other briefing"},
            confidence=0.9,
        )
        r1 = svc.list_briefings(OWNER, p1["id"])
        assert len(r1["briefings"]) == 1
        assert r1["briefings"][0]["title"] == "Briefing for P1"
        # Verify shape of each briefing entry
        b = r1["briefings"][0]
        assert set(b.keys()) == {"id", "title", "value", "created_at", "updated_at"}
        assert isinstance(b["value"], dict)
        assert b["value"]["project_id"] == p1["id"]

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.list_briefings(OWNER, "proj-gone")


# ── list_meetings ────────────────────────────────────────────────────────


class TestListMeetings:
    def test_empty_list(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.list_meetings(OWNER, proj["id"])
        assert result == []

    def test_returns_associated_meetings(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        _save_meeting(db, "m1", "Standup")
        svc.associate_meeting(OWNER, proj["id"], "m1")
        result = svc.list_meetings(OWNER, proj["id"])
        assert len(result) == 1
        row = result[0]
        expected_keys = {"id", "title", "started_at", "duration_seconds",
                         "intel_status", "source", "confidence"}
        assert set(row.keys()) == expected_keys
        assert row["id"] == "m1"
        assert row["title"] == "Standup"

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.list_meetings(OWNER, "proj-gone")


# ── list_resources ───────────────────────────────────────────────────────


class TestListResources:
    def test_empty_list(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.list_resources(OWNER, proj["id"])
        assert result == []

    def test_returns_resource_dicts(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        svc.add_resource(OWNER, proj["id"], "note:n1")
        result = svc.list_resources(OWNER, proj["id"])
        assert len(result) == 1
        row = result[0]
        expected_keys = {"id", "project_id", "resource_ref", "relationship",
                         "source", "confidence", "created_at", "last_modified",
                         "deleted"}
        assert set(row.keys()) == expected_keys
        assert row["project_id"] == proj["id"]
        assert row["resource_ref"] == "note:n1"
        assert row["relationship"] == "member"  # default

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.list_resources(OWNER, "proj-gone")


# ── add_resource ─────────────────────────────────────────────────────────


class TestAddResource:
    def test_success_shape(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.add_resource(OWNER, proj["id"], "note:n1")
        # HS-157-03 legacy keys
        expected_keys = {"id", "project_id", "resource_ref", "relationship",
                         "source", "confidence", "created_at", "last_modified",
                         "deleted"}
        # HS-158-02 additive envelope keys
        assert expected_keys <= set(result.keys())
        assert "result_kind" in result
        assert result["source"] == "manual"
        assert result["confidence"] == 1.0
        assert result["deleted"] is False

    def test_unqualified_ref_raises(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValueError, match="qualified"):
            svc.add_resource(OWNER, proj["id"], "bad-ref")

    def test_unknown_kind_raises(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValueError, match="unknown resource kind"):
            svc.add_resource(OWNER, proj["id"], "spaceship:x1")

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.add_resource(OWNER, "proj-gone", "note:n1")

    def test_custom_relationship(self, rig) -> None:
        """Valid relationships: member, source, output, related."""
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.add_resource(OWNER, proj["id"], "note:n1",
                                  {"relationship": "source"})
        assert result["relationship"] == "source"

    def test_invalid_relationship_raises(self, rig) -> None:
        """Pin: relationship is validated at the repo layer; service does not
        catch it, so a ValueError propagates (not a ValidationError)."""
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValueError, match="unknown project relationship"):
            svc.add_resource(OWNER, proj["id"], "note:n1",
                             {"relationship": "owner"})


# ── remove_resource ──────────────────────────────────────────────────────


class TestRemoveResource:
    def test_returns_bool(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        svc.add_resource(OWNER, proj["id"], "note:n1")
        result = svc.remove_resource(OWNER, proj["id"], "note:n1")
        assert isinstance(result, bool)

    def test_after_removal_list_is_empty(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        svc.add_resource(OWNER, proj["id"], "note:n1")
        svc.remove_resource(OWNER, proj["id"], "note:n1")
        assert svc.list_resources(OWNER, proj["id"]) == []

    def test_not_found_project(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.remove_resource(OWNER, "proj-gone", "note:n1")


# ── list_resource_relationships ──────────────────────────────────────────


class TestListResourceRelationships:
    def test_empty_shape(self, rig) -> None:
        _db, svc = rig
        result = svc.list_resource_relationships(OWNER, "note:n1")
        assert isinstance(result, dict)
        assert set(result.keys()) == {"resource_ref", "zone", "knowledge",
                                       "projects", "explanations"}
        assert result["resource_ref"] == "note:n1"
        assert result["zone"] is None
        assert result["knowledge"] == []
        assert result["projects"] == []
        assert isinstance(result["explanations"], dict)

    def test_shows_project_relationship(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        svc.add_resource(OWNER, proj["id"], "note:n1")
        result = svc.list_resource_relationships(OWNER, "note:n1")
        assert len(result["projects"]) == 1

    def test_unqualified_ref_raises(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(ValueError, match="qualified"):
            svc.list_resource_relationships(OWNER, "bad-ref")


# ── associate_meeting ────────────────────────────────────────────────────


class TestAssociateMeeting:
    def test_returns_true(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        _save_meeting(db, "m1")
        result = svc.associate_meeting(OWNER, proj["id"], "m1")
        assert result is True

    def test_project_not_found(self, rig) -> None:
        db, svc = rig
        _save_meeting(db, "m1")
        with pytest.raises(NotFound):
            svc.associate_meeting(OWNER, "proj-gone", "m1")

    def test_meeting_not_found(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(NotFound):
            svc.associate_meeting(OWNER, proj["id"], "m-gone")


# ── disassociate_meeting ─────────────────────────────────────────────────


class TestDisassociateMeeting:
    def test_returns_true(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        _save_meeting(db, "m1")
        svc.associate_meeting(OWNER, proj["id"], "m1")
        result = svc.disassociate_meeting(OWNER, proj["id"], "m1")
        assert result is True

    def test_project_not_found(self, rig) -> None:
        db, svc = rig
        _save_meeting(db, "m1")
        with pytest.raises(NotFound):
            svc.disassociate_meeting(OWNER, "proj-gone", "m1")

    def test_meeting_not_found(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(NotFound):
            svc.disassociate_meeting(OWNER, proj["id"], "m-gone")


# ── list_meeting_projects ────────────────────────────────────────────────


class TestListMeetingProjects:
    def test_empty_list(self, rig) -> None:
        db, svc = rig
        _save_meeting(db, "m1")
        result = svc.list_meeting_projects(OWNER, "m1")
        assert result == []

    def test_returns_associated_projects(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        _save_meeting(db, "m1")
        svc.associate_meeting(OWNER, proj["id"], "m1")
        result = svc.list_meeting_projects(OWNER, "m1")
        assert len(result) == 1
        row = result[0]
        expected_keys = {"project_id", "project_name", "source", "confidence",
                         "detected_at"}
        assert set(row.keys()) == expected_keys

    def test_meeting_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.list_meeting_projects(OWNER, "m-gone")


# ── since_last_meeting ───────────────────────────────────────────────────


class TestSinceLastMeeting:
    def test_no_meetings_shape(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.since_last_meeting(OWNER, proj["id"])
        assert isinstance(result, dict)
        # With no meetings associated, the result has project_id + null meetings
        assert result.get("project_id") == proj["id"]
        assert result.get("current_meeting") is None

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.since_last_meeting(OWNER, "proj-gone")


# ── summary ──────────────────────────────────────────────────────────────


class TestSummary:
    def test_empty_shape(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.summary(OWNER, proj["id"])
        assert isinstance(result, dict)
        expected_keys = {"meeting_count", "first_meeting", "last_meeting",
                         "action_items_by_status", "artifact_count"}
        assert set(result.keys()) == expected_keys
        assert result["meeting_count"] == 0
        assert result["first_meeting"] is None
        assert result["last_meeting"] is None
        assert result["action_items_by_status"] == {}
        assert result["artifact_count"] == 0

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.summary(OWNER, "proj-gone")


# ── list_action_items ────────────────────────────────────────────────────


class TestListActionItems:
    def test_empty_list(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.list_action_items(OWNER, proj["id"])
        assert result == []

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.list_action_items(OWNER, "proj-gone")


# ── list_artifacts ───────────────────────────────────────────────────────


class TestListArtifacts:
    def test_empty_list(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        result = svc.list_artifacts(OWNER, proj["id"])
        assert result == []

    def test_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.list_artifacts(OWNER, "proj-gone")
