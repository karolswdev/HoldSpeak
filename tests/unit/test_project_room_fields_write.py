"""HS-158-02 -- Room fields write path: update_project accepts §5.1 fields,
validates them, writes them atomically under the revision law, and the room
projection reflects the written values.

Lifecycle enforcement decision (P1): CLOSED VOCABULARY only -- the five valid
states (proposed, active, paused, complete, cancelled) are enforced;
'archived' is rejected with a typed error pointing at archive_project;
unknown values are rejected.  Transition enforcement (e.g. "proposed can
only go to active") is NOT enforced in P1 -- the SRS diagram implies
transitions but P1a owns richer lifecycle UX.  Documented, not silent.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from holdspeak.services.project_service import (
    PROJECT_LIFECYCLES,
    ProjectService,
)

OWNER = Principal(PrincipalKind.OWNER, "room-fields-test")


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "room-fields.db")
    svc = ProjectService(db)
    yield db, svc
    reset_database()


def _create(svc: ProjectService, **kw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": "Room Fields Project", **kw}
    return svc.create_project(OWNER, payload)


def _room(svc: ProjectService, project_id: str) -> dict[str, Any]:
    return svc.room(OWNER, project_id)


# ── Round-trip: each field through service + room read ───────────────────

class TestRoomFieldRoundTrips:
    """Each room field round-trips through update_project and the room read."""

    def test_purpose_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"purpose": "Ship the MVP"})
        room = _room(svc, created["id"])
        assert room["project"]["purpose"] == "Ship the MVP"

    def test_outcome_text_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"outcome_text": "GA by Q3"})
        room = _room(svc, created["id"])
        assert room["project"]["outcome_text"] == "GA by Q3"

    def test_owner_ref_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"owner_ref": "people:alice"})
        room = _room(svc, created["id"])
        assert room["project"]["owner_ref"] == "people:alice"

    def test_lifecycle_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"lifecycle": "proposed"})
        room = _room(svc, created["id"])
        assert room["project"]["lifecycle"] == "proposed"

    def test_posture_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"posture": "YOLO"})
        room = _room(svc, created["id"])
        assert room["project"]["posture"] == "YOLO"

    def test_posture_reason_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"posture_reason": "Fast iteration phase"})
        room = _room(svc, created["id"])
        assert room["project"]["posture_reason"] == "Fast iteration phase"

    def test_start_at_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"start_at": "2026-09-01T00:00:00"})
        room = _room(svc, created["id"])
        assert room["project"]["start_at"] == "2026-09-01T00:00:00"

    def test_target_at_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"target_at": "2026-12-31T23:59:59"})
        room = _room(svc, created["id"])
        assert room["project"]["target_at"] == "2026-12-31T23:59:59"

    def test_next_review_at_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"next_review_at": "2026-09-15T10:00:00"})
        room = _room(svc, created["id"])
        assert room["project"]["next_review_at"] == "2026-09-15T10:00:00"

    def test_review_cadence_json_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        cadence = {"every_days": 14}
        svc.update_project(OWNER, created["id"],
                           {"review_cadence_json": cadence})
        room = _room(svc, created["id"])
        # review_cadence_json is stored as TEXT, read back as string
        raw = room["project"]["review_cadence_json"]
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        assert parsed == {"every_days": 14}

    def test_template_key_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"template_key": "weekly-standup"})
        room = _room(svc, created["id"])
        assert room["project"]["template_key"] == "weekly-standup"

    def test_modules_json_round_trip(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        modules = ["risks", "milestones", "signals"]
        svc.update_project(OWNER, created["id"],
                           {"modules_json": modules})
        room = _room(svc, created["id"])
        raw = room["project"]["modules_json"]
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        assert parsed == ["risks", "milestones", "signals"]


class TestNullClearing:
    """Null values clear fields where semantics allow."""

    def test_purpose_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"purpose": "Initial"})
        svc.update_project(OWNER, created["id"], {"purpose": None})
        room = _room(svc, created["id"])
        assert room["project"]["purpose"] is None

    def test_owner_ref_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"owner_ref": "people:bob"})
        svc.update_project(OWNER, created["id"], {"owner_ref": None})
        room = _room(svc, created["id"])
        assert room["project"]["owner_ref"] is None

    def test_posture_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"posture": "YOLO"})
        svc.update_project(OWNER, created["id"], {"posture": None})
        room = _room(svc, created["id"])
        assert room["project"]["posture"] is None

    def test_start_at_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"start_at": "2026-09-01T00:00:00"})
        svc.update_project(OWNER, created["id"], {"start_at": None})
        room = _room(svc, created["id"])
        assert room["project"]["start_at"] is None

    def test_review_cadence_json_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"review_cadence_json": {"every_days": 7}})
        svc.update_project(OWNER, created["id"],
                           {"review_cadence_json": None})
        room = _room(svc, created["id"])
        assert room["project"]["review_cadence_json"] is None

    def test_modules_json_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"modules_json": ["risks"]})
        svc.update_project(OWNER, created["id"], {"modules_json": None})
        room = _room(svc, created["id"])
        assert room["project"]["modules_json"] is None

    def test_template_key_null_clears(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"],
                           {"template_key": "sprint"})
        svc.update_project(OWNER, created["id"], {"template_key": None})
        room = _room(svc, created["id"])
        assert room["project"]["template_key"] is None


# ── Lifecycle vocabulary enforcement ─────────────────────────────────────

class TestLifecycleVocabulary:
    """Closed vocabulary: proposed|active|paused|complete|cancelled.
    'archived' rejected with typed error.  Unknown rejected.
    Transitions NOT enforced in P1 (P1a owns richer lifecycle UX)."""

    @pytest.mark.parametrize("lc", sorted(PROJECT_LIFECYCLES))
    def test_valid_lifecycle_accepted(self, rig, lc: str) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.update_project(OWNER, created["id"], {"lifecycle": lc})
        room = _room(svc, created["id"])
        assert room["project"]["lifecycle"] == lc

    def test_archived_rejected_with_typed_error(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"lifecycle": "archived"})
        assert exc_info.value.code == "invalid_lifecycle"
        assert "archive_project" in exc_info.value.detail

    def test_unknown_lifecycle_rejected(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"lifecycle": "banana"})
        assert exc_info.value.code == "invalid_lifecycle"

    def test_case_insensitive(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"lifecycle": "PROPOSED"})
        room = _room(svc, created["id"])
        assert room["project"]["lifecycle"] == "proposed"

    def test_transitions_not_enforced_p1(self, rig) -> None:
        """P1 does NOT enforce transition order -- any valid value accepted
        regardless of current state."""
        _db, svc = rig
        created = _create(svc)
        # active -> complete (valid in SRS)
        svc.update_project(OWNER, created["id"], {"lifecycle": "complete"})
        # complete -> proposed (would be invalid in SRS transition graph,
        # but P1 allows it -- vocabulary only, not transitions)
        svc.update_project(OWNER, created["id"], {"lifecycle": "proposed"})
        room = _room(svc, created["id"])
        assert room["project"]["lifecycle"] == "proposed"


# ── Validation refusals ──────────────────────────────────────────────────

class TestValidationRefusals:
    """Typed validation errors for invalid field values."""

    def test_invalid_owner_ref_malformed(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"owner_ref": "not-a-ref"})
        assert exc_info.value.code == "invalid_owner_ref"

    def test_posture_too_long(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"posture": "x" * 65})
        assert exc_info.value.code == "posture_too_long"

    def test_posture_reason_too_long(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"posture_reason": "x" * 501})
        assert exc_info.value.code == "posture_reason_too_long"

    def test_start_at_not_iso(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"start_at": "next-tuesday"})
        assert exc_info.value.code == "invalid_start_at"

    def test_target_at_not_iso(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"target_at": "soon"})
        assert exc_info.value.code == "invalid_target_at"

    def test_next_review_at_not_iso(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"next_review_at": "whenever"})
        assert exc_info.value.code == "invalid_next_review_at"

    def test_review_cadence_not_dict(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"review_cadence_json": "weekly"})
        assert exc_info.value.code == "invalid_review_cadence"

    def test_review_cadence_every_days_not_positive(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"review_cadence_json": {"every_days": 0}})
        assert exc_info.value.code == "invalid_review_cadence"

    def test_review_cadence_every_days_not_int(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"review_cadence_json": {"every_days": "abc"}})
        assert exc_info.value.code == "invalid_review_cadence"

    def test_template_key_too_long(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"template_key": "x" * 65})
        assert exc_info.value.code == "template_key_too_long"

    def test_modules_json_not_list(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"modules_json": "risks"})
        assert exc_info.value.code == "invalid_modules"

    def test_modules_json_entry_too_long(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ValidationError) as exc_info:
            svc.update_project(OWNER, created["id"],
                               {"modules_json": ["x" * 65]})
        assert exc_info.value.code == "invalid_modules"


# ── Revision law: one bump per patch ─────────────────────────────────────

class TestRevisionLaw:
    """Room fields participate in the same revision-law transaction as
    legacy fields: one revision bump, one change row, one event."""

    def test_room_field_bumps_revision_once(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.update_project(OWNER, created["id"],
                                    {"purpose": "Ship it"})
        assert result["project_revision"] == 2

    def test_mixed_legacy_and_room_fields_one_bump(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.update_project(OWNER, created["id"], {
            "name": "Renamed",
            "purpose": "The mission",
            "lifecycle": "proposed",
            "posture": "YOLO",
        })
        assert result["project_revision"] == 2

    def test_change_row_includes_room_fields(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {
            "purpose": "Ship it",
            "lifecycle": "proposed",
        })
        changes = db.projects.list_project_changes(created["id"])
        # Create + update = 2 changes; default order is revision DESC
        assert len(changes) == 2
        update_change = changes[0]  # most recent first
        assert update_change["change_kind"] == "project.updated"
        summary = json.loads(update_change["summary_json"])
        assert "purpose" in summary["fields"]
        assert "lifecycle" in summary["fields"]

    def test_multiple_room_updates_increment_sequentially(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"posture": "cautious"})
        result = svc.update_project(OWNER, created["id"],
                                    {"posture": "bold"})
        assert result["project_revision"] == 3


# ── Route pass-through (integration-level) ───────────────────────────────

class TestRouteLevelRoundTrip:
    """Verify the PATCH /api/projects/{id} route passes room fields through
    and the room route reflects them.

    The PATCH route is a transparent pass-through (no key filtering),
    so room fields flow from HTTP to service to DB unchanged.
    """

    @pytest.fixture
    def client(self, rig):
        """ASGI test client."""
        db, svc = rig
        from holdspeak.web.routes.projects import build_projects_router
        from holdspeak.web.context import WebContext
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        ctx = WebContext.__new__(WebContext)
        ctx.project_service = svc
        router = build_projects_router(ctx)
        app.include_router(router)
        return TestClient(app)

    def _create_via_route(self, client) -> dict[str, Any]:
        resp = client.post("/api/projects", json={"name": "Route Test"})
        assert resp.status_code == 200
        return resp.json()["project"]

    def test_patch_room_fields_via_route(self, rig, client) -> None:
        proj = self._create_via_route(client)
        resp = client.patch(f"/api/projects/{proj['id']}", json={
            "purpose": "via route",
            "lifecycle": "proposed",
            "posture": "YOLO",
            "start_at": "2026-10-01T00:00:00",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["project"]["project_revision"] == 2

        # Verify through room endpoint
        _db, svc = rig
        room = _room(svc, proj["id"])
        assert room["project"]["purpose"] == "via route"
        assert room["project"]["lifecycle"] == "proposed"
        assert room["project"]["posture"] == "YOLO"
        assert room["project"]["start_at"] == "2026-10-01T00:00:00"

    def test_lifecycle_archived_400_via_route(self, rig, client) -> None:
        proj = self._create_via_route(client)
        resp = client.patch(f"/api/projects/{proj['id']}", json={
            "lifecycle": "archived",
        })
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert "archive_project" in body["error"]

    def test_invalid_owner_ref_400_via_route(self, rig, client) -> None:
        proj = self._create_via_route(client)
        resp = client.patch(f"/api/projects/{proj['id']}", json={
            "owner_ref": "garbage",
        })
        assert resp.status_code == 400

    def test_room_route_reflects_patched_fields(self, rig, client) -> None:
        proj = self._create_via_route(client)
        client.patch(f"/api/projects/{proj['id']}", json={
            "outcome_text": "Delivered and loved",
            "template_key": "retro",
            "modules_json": ["risks", "signals"],
            "review_cadence_json": {"every_days": 7},
        })
        resp = client.get(f"/api/projects/{proj['id']}/room")
        assert resp.status_code == 200
        room = resp.json()
        assert room["project"]["outcome_text"] == "Delivered and loved"
        assert room["project"]["template_key"] == "retro"
        raw_mods = room["project"]["modules_json"]
        parsed_mods = json.loads(raw_mods) if isinstance(raw_mods, str) else raw_mods
        assert parsed_mods == ["risks", "signals"]
        raw_cadence = room["project"]["review_cadence_json"]
        parsed_cadence = json.loads(raw_cadence) if isinstance(raw_cadence, str) else raw_cadence
        assert parsed_cadence == {"every_days": 7}
