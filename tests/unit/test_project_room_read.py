"""HS-158-04 -- The room read: one coherent, honest, bounded projection.

Tests:
- Composition completeness: every SS6.2 section present
- Caps enforced: seed >N items; exactly N in focus + true totals
- Deterministic ordering (severity/due_at/sort_key/created_at/id)
- Absent markers exact-shape
- Per-section fault injection (monkeypatch one sub-read -> degraded, others ok, HTTP 200)
- Revision stamping (write bumps revision -> room reflects it)
- Byte-determinism of consecutive reads (no writes between)
- 404 on unknown project
- Non-owner behavior matching sibling routes
- Integration test through the real app for the route
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pitem_id
from holdspeak.services.errors import NotFound
from holdspeak.services.project_service import (
    ROOM_CHANGES_CAP,
    ROOM_FOCUS_CAP,
    ProjectService,
)

OWNER = Principal(PrincipalKind.OWNER, "room-read-test")

# ── SS6.2 sections that MUST be present ─────────────────────────────────
REQUIRED_SECTIONS = {
    "project", "items", "meetings", "resources", "changes",
    "review", "sources", "updates", "steward",
    # HS-169-04: the four questions
    "needsYou", "health", "sinceRead", "decisions", "commitments", "target",
    "receipts",  # HS-174: the Room's RECEIPTS section (remote receipts wear REMOTE · host)
}
TOP_LEVEL_KEYS = {"project_id", "revision", "observed_at", "nextCheckAt"} | REQUIRED_SECTIONS


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "room-read.db")
    svc = ProjectService(db)
    yield db, svc
    reset_database()


def _create(svc: ProjectService, name: str = "Room Test Project",
            **kw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, **kw}
    return svc.create_project(OWNER, payload)


def _save_meeting(db: Database, mid: str, title: str = "Standup") -> None:
    db.meetings.save_meeting(MeetingState(
        id=mid, started_at=datetime(2026, 1, 15, 10, 0),
        title=title, capture_status="finalized",
    ))


def _seed_items(db: Database, project_id: str, n: int,
                prefix: str = "item") -> list[str]:
    """Seed *n* project items with varying severity/due_at and return IDs."""
    severities = ["critical", "high", "medium", "low", None]
    ids = []
    for i in range(n):
        item_id = generate_pitem_id()
        sev = severities[i % len(severities)]
        due = f"2026-03-{(i % 28) + 1:02d}" if i % 3 != 0 else None
        db.projects.insert_project_item(
            item_id=item_id,
            project_id=project_id,
            item_type="risk" if i % 2 == 0 else "milestone",
            title=f"{prefix}-{i}",
            severity=sev,
            due_at=due,
            sort_key=float(i),
        )
        ids.append(item_id)
    return ids


# ── Composition completeness ─────────────────────────────────────────────

class TestCompositionCompleteness:
    def test_all_sections_present(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert set(result.keys()) == TOP_LEVEL_KEYS

    def test_project_id_matches(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert result["project_id"] == proj["id"]

    def test_project_orientation_has_identity(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc, name="Orient Test")
        result = svc.room(OWNER, proj["id"])
        orientation = result["project"]
        assert orientation["id"] == proj["id"]
        assert orientation["name"] == "Orient Test"

    def test_project_orientation_has_room_fields(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        orientation = result["project"]
        # SS5.1 fields should be present (nullable)
        for field in ("purpose", "outcome_text", "owner_ref", "lifecycle",
                      "posture", "posture_reason", "start_at", "target_at",
                      "review_cadence_json", "next_review_at", "template_key",
                      "modules_json", "revision", "last_review_id", "last_review_at"):
            assert field in orientation, f"missing room field: {field}"


# ── Caps enforced ────────────────────────────────────────────────────────

class TestCapsEnforced:
    def test_focus_capped_at_constant(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        n = ROOM_FOCUS_CAP + 5
        _seed_items(db, proj["id"], n)
        result = svc.room(OWNER, proj["id"])
        items = result["items"]
        assert items["state"] == "ok"
        assert len(items["focus"]) == ROOM_FOCUS_CAP
        assert items["total"] == n

    def test_totals_by_type_reflect_all_items(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        _seed_items(db, proj["id"], 8)
        result = svc.room(OWNER, proj["id"])
        items = result["items"]
        total_from_types = sum(items["totals_by_type"].values())
        assert total_from_types == items["total"] == 8

    def test_changes_capped(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        # Create enough writes to exceed ROOM_CHANGES_CAP
        for i in range(ROOM_CHANGES_CAP + 5):
            svc.update_project(OWNER, proj["id"], {"name": f"V{i}"})
        result = svc.room(OWNER, proj["id"])
        changes = result["changes"]
        assert changes["state"] == "ok"
        assert len(changes["recent"]) <= ROOM_CHANGES_CAP


# ── Deterministic ordering ───────────────────────────────────────────────

class TestDeterministicOrdering:
    def test_severity_desc_nulls_last(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        # Seed items with known severities
        db.projects.insert_project_item(
            item_id=generate_pitem_id(), project_id=proj["id"],
            item_type="risk", title="no-severity", severity=None,
        )
        db.projects.insert_project_item(
            item_id=generate_pitem_id(), project_id=proj["id"],
            item_type="risk", title="high-sev", severity="high",
        )
        db.projects.insert_project_item(
            item_id=generate_pitem_id(), project_id=proj["id"],
            item_type="risk", title="critical-sev", severity="critical",
        )
        result = svc.room(OWNER, proj["id"])
        titles = [i["title"] for i in result["items"]["focus"]]
        # HS-158-03: explicit CASE rank (critical=0 < high=1 < medium=2
        # < low=3 < null=999); critical comes first, null comes last.
        assert titles[0] == "critical-sev", "critical must be first"
        assert titles[1] == "high-sev", "high must be second"
        assert titles[-1] == "no-severity", "null severity should be last"

    def test_severity_rank_order_all_four_levels(self, rig) -> None:
        """HS-158-03 inherited duty: prove explicit rank order with all
        four severity levels + null (CASE expression, not free-text DESC).
        """
        db, svc = rig
        proj = _create(svc)
        for sev in [None, "low", "medium", "high", "critical"]:
            db.projects.insert_project_item(
                item_id=generate_pitem_id(), project_id=proj["id"],
                item_type="risk", title=f"sev-{sev}", severity=sev,
            )
        result = svc.room(OWNER, proj["id"])
        titles = [i["title"] for i in result["items"]["focus"]]
        assert titles == [
            "sev-critical", "sev-high", "sev-medium", "sev-low", "sev-None",
        ]

    def test_due_at_asc_nulls_last_within_same_severity(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        db.projects.insert_project_item(
            item_id=generate_pitem_id(), project_id=proj["id"],
            item_type="risk", title="no-due", severity="high", due_at=None,
        )
        db.projects.insert_project_item(
            item_id=generate_pitem_id(), project_id=proj["id"],
            item_type="risk", title="late-due", severity="high",
            due_at="2026-12-01",
        )
        db.projects.insert_project_item(
            item_id=generate_pitem_id(), project_id=proj["id"],
            item_type="risk", title="early-due", severity="high",
            due_at="2026-01-01",
        )
        result = svc.room(OWNER, proj["id"])
        titles = [i["title"] for i in result["items"]["focus"]]
        assert titles == ["early-due", "late-due", "no-due"]

    def test_id_tiebreaker_makes_order_fully_deterministic(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        # All items identical except id
        ids = []
        for _ in range(3):
            item_id = generate_pitem_id()
            db.projects.insert_project_item(
                item_id=item_id, project_id=proj["id"],
                item_type="risk", title="same",
            )
            ids.append(item_id)
        r1 = svc.room(OWNER, proj["id"])
        r2 = svc.room(OWNER, proj["id"])
        focus_ids_1 = [i["id"] for i in r1["items"]["focus"]]
        focus_ids_2 = [i["id"] for i in r2["items"]["focus"]]
        assert focus_ids_1 == focus_ids_2


# ── Absent markers ───────────────────────────────────────────────────────

class TestAbsentMarkers:
    EXPECTED_SHAPE = {"state": "absent", "reason": "not_yet_built"}

    def test_review_absent(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert result["review"] == self.EXPECTED_SHAPE

    def test_sources_live(self, rig) -> None:
        """HS-169-04: sources is now a live section, not absent."""
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert result["sources"]["state"] == "ok"

    def test_updates_absent(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert result["updates"] == self.EXPECTED_SHAPE

    def test_steward_absent(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert result["steward"] == self.EXPECTED_SHAPE

    def test_absent_markers_grep_proof(self, rig) -> None:
        """Remaining absent sections (Art VI). sources graduated HS-169-04."""
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        for section_name in ("review", "updates", "steward"):
            section = result[section_name]
            assert section["state"] == "absent"
            assert "reason" in section
            # Must NOT have any data-like keys (empty lists/dicts/etc.)
            assert set(section.keys()) == {"state", "reason"}


# ── Per-section fault injection ──────────────────────────────────────────

class TestFaultIsolation:
    def test_items_fault_degrades_only_items(self, rig, monkeypatch) -> None:
        _db, svc = rig
        proj = _create(svc)

        def _explode(*a, **kw):
            raise RuntimeError("DB gone")

        monkeypatch.setattr(svc, "_read_room_items", _explode)
        result = svc.room(OWNER, proj["id"])

        assert result["items"]["state"] == "degraded"
        assert result["items"]["error_code"] == "items_read_failed"
        # Other sections remain ok
        assert result["meetings"]["state"] == "ok"
        assert result["resources"]["state"] == "ok"
        assert result["changes"]["state"] == "ok"

    def test_meetings_fault_degrades_only_meetings(self, rig, monkeypatch) -> None:
        _db, svc = rig
        proj = _create(svc)

        def _explode(*a, **kw):
            raise RuntimeError("DB gone")

        monkeypatch.setattr(svc, "_read_room_meetings", _explode)
        result = svc.room(OWNER, proj["id"])

        assert result["meetings"]["state"] == "degraded"
        assert result["meetings"]["error_code"] == "meetings_read_failed"
        assert result["items"]["state"] == "ok"

    def test_resources_fault_degrades_only_resources(self, rig, monkeypatch) -> None:
        _db, svc = rig
        proj = _create(svc)

        def _explode(*a, **kw):
            raise RuntimeError("DB gone")

        monkeypatch.setattr(svc, "_read_room_resources", _explode)
        result = svc.room(OWNER, proj["id"])

        assert result["resources"]["state"] == "degraded"
        assert result["items"]["state"] == "ok"

    def test_changes_fault_degrades_only_changes(self, rig, monkeypatch) -> None:
        _db, svc = rig
        proj = _create(svc)

        def _explode(*a, **kw):
            raise RuntimeError("DB gone")

        monkeypatch.setattr(svc, "_read_room_changes", _explode)
        result = svc.room(OWNER, proj["id"])

        assert result["changes"]["state"] == "degraded"
        assert result["items"]["state"] == "ok"

    def test_degraded_section_still_http_200(self, rig, monkeypatch) -> None:
        """Fault injection: HTTP 200 even with degraded sections."""
        db, svc = rig
        proj = _create(svc)

        def _explode(*a, **kw):
            raise RuntimeError("boom")

        monkeypatch.setattr(svc, "_read_room_items", _explode)

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from holdspeak.web.routes import build_projects_router
        from holdspeak.web.context import WebContext

        app = FastAPI()
        app.include_router(build_projects_router(WebContext(
            get_state=lambda: {},
            project_service=svc,
        )))
        client = TestClient(app)
        resp = client.get(f"/api/projects/{proj['id']}/room")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"]["state"] == "degraded"
        assert body["meetings"]["state"] == "ok"


# ── Revision stamping ───────────────────────────────────────────────────

class TestRevisionStamping:
    def test_create_room_has_revision(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        assert "revision" in result
        assert result["revision"] == proj.get("project_revision", 1)

    def test_update_bumps_revision_in_room(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        r1 = svc.room(OWNER, proj["id"])
        rev1 = r1["revision"]

        svc.update_project(OWNER, proj["id"], {"name": "V2"})
        r2 = svc.room(OWNER, proj["id"])
        assert r2["revision"] == rev1 + 1


# ── Byte-determinism ────────────────────────────────────────────────────

class TestByteDeterminism:
    def test_consecutive_reads_byte_identical(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        _seed_items(db, proj["id"], 3)
        _save_meeting(db, "m-det-1", "Det Meeting")
        svc.associate_meeting(OWNER, proj["id"], "m-det-1")

        r1 = svc.room(OWNER, proj["id"])
        r2 = svc.room(OWNER, proj["id"])

        j1 = json.dumps(r1, sort_keys=True, ensure_ascii=True, default=str)
        j2 = json.dumps(r2, sort_keys=True, ensure_ascii=True, default=str)
        assert j1 == j2

    def test_observed_at_is_deterministic(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        r1 = svc.room(OWNER, proj["id"])
        r2 = svc.room(OWNER, proj["id"])
        assert r1["observed_at"] == r2["observed_at"]

    def test_observed_at_changes_after_write(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        r1 = svc.room(OWNER, proj["id"])
        svc.update_project(OWNER, proj["id"], {"name": "Changed"})
        r2 = svc.room(OWNER, proj["id"])
        assert r2["observed_at"] != r1["observed_at"]


# ── 404 ──────────────────────────────────────────────────────────────────

class TestNotFound:
    def test_unknown_project_raises_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.room(OWNER, "proj-nonexistent")


# ── Populated sections ──────────────────────────────────────────────────

class TestPopulatedSections:
    def test_items_section_with_data(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        _seed_items(db, proj["id"], 2)
        result = svc.room(OWNER, proj["id"])
        items = result["items"]
        assert items["state"] == "ok"
        assert len(items["focus"]) == 2
        assert items["total"] == 2

    def test_meetings_section_with_data(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        _save_meeting(db, "m-pop-1", "First")
        svc.associate_meeting(OWNER, proj["id"], "m-pop-1")
        result = svc.room(OWNER, proj["id"])
        meetings = result["meetings"]
        assert meetings["state"] == "ok"
        assert meetings["count"] >= 1
        assert meetings["latest"] is not None
        assert meetings["latest"]["title"] == "First"

    def test_resources_section_with_data(self, rig) -> None:
        db, svc = rig
        proj = _create(svc)
        svc.add_resource(OWNER, proj["id"], "note:abc123")
        result = svc.room(OWNER, proj["id"])
        resources = result["resources"]
        assert resources["state"] == "ok"
        assert resources["count"] >= 1
        assert resources["latest"] is not None

    def test_changes_section_has_create_change(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        changes = result["changes"]
        assert changes["state"] == "ok"
        assert len(changes["recent"]) >= 1

    def test_empty_project_has_zero_items(self, rig) -> None:
        _db, svc = rig
        proj = _create(svc)
        result = svc.room(OWNER, proj["id"])
        items = result["items"]
        assert items["state"] == "ok"
        assert items["focus"] == []
        assert items["total"] == 0
        assert items["totals_by_type"] == {}


# ── Integration: route through the real app ──────────────────────────────

class TestRouteIntegration:
    @pytest.fixture
    def client(self, rig):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import holdspeak.db as hsdb
        from unittest.mock import patch as mp

        db, _svc = rig
        with mp.object(hsdb, "get_database", return_value=db):
            svc = ProjectService(db)
            app = FastAPI()
            from holdspeak.web.routes import build_projects_router
            from holdspeak.web.context import WebContext
            app.include_router(build_projects_router(WebContext(
                get_state=lambda: {},
                project_service=svc,
            )))
            yield TestClient(app)

    def test_room_route_200(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Route Test"}).json()["project"]
        resp = client.get(f"/api/projects/{proj['id']}/room")
        assert resp.status_code == 200
        body = resp.json()
        assert body["project_id"] == proj["id"]
        assert set(body.keys()) == TOP_LEVEL_KEYS

    def test_room_route_404(self, rig, client) -> None:
        resp = client.get("/api/projects/proj-nope/room")
        assert resp.status_code == 404

    def test_room_route_absent_markers(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Absent Test"}).json()["project"]
        resp = client.get(f"/api/projects/{proj['id']}/room")
        body = resp.json()
        # HS-169-04: sources graduated to live; only these remain absent
        for section_name in ("review", "updates", "steward"):
            assert body[section_name] == {"state": "absent", "reason": "not_yet_built"}

    def test_room_route_has_revision(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Rev Route"}).json()["project"]
        resp = client.get(f"/api/projects/{proj['id']}/room")
        body = resp.json()
        assert "revision" in body
        assert isinstance(body["revision"], int)
