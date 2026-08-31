"""HS-158-03 -- The items: typed workstreams, milestones, risks,
dependencies, signals under the revision law.

Tests:
- Five item types round-trip with closed details schema
- Closed-schema refusals (unknown fields, wrong types, missing required)
- Lifecycle verbs (incl. DOM-007 milestone guard)
- Ordering / pagination
- Revision-law compliance (atomicity via fault pattern, idempotent replay)
- Severity validation + room focus rank proof
- Integration route tests
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pcmd_id, generate_pitem_id
from holdspeak.services.errors import ConflictError, NotFound, ValidationError
from holdspeak.services.project_service import (
    ITEM_DEFAULT_LIFECYCLE,
    ITEM_LIFECYCLES,
    ITEM_TYPES,
    SEVERITY_LEVELS,
    SEVERITY_RANK,
    ProjectService,
)

OWNER = Principal(PrincipalKind.OWNER, "item-test")


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "items.db")
    svc = ProjectService(db)
    yield db, svc
    reset_database()


def _create_project(svc: ProjectService, name: str = "Item Test") -> dict[str, Any]:
    return svc.create_project(OWNER, {"name": name})


def _create_item(
    svc: ProjectService,
    project_id: str,
    item_type: str = "milestone",
    title: str = "Test Item",
    details: dict[str, Any] | None = None,
    **kw: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "item_type": item_type,
        "title": title,
    }
    if details is not None:
        payload["details"] = details
    payload.update(kw)
    return svc.create_item(OWNER, project_id, payload)


# ── Five types round-trip ──────────────────────────────────────────────

class TestFiveTypesRoundTrip:
    def test_milestone_round_trip(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1",
                            details={"completion_evidence_refs": ["note:abc"]})
        assert item["item_type"] == "milestone"
        assert item["lifecycle"] == "planned"
        loaded = svc.list_items(OWNER, proj["id"], item_type="milestone")
        assert len(loaded["items"]) == 1
        assert loaded["items"][0]["title"] == "M1"
        detail = json.loads(loaded["items"][0]["details_json"])
        assert detail["completion_evidence_refs"] == ["note:abc"]

    def test_risk_round_trip(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "risk", "R1",
                            details={"likelihood": "high", "impact": "severe",
                                     "mitigation": "none"})
        assert item["item_type"] == "risk"
        assert item["lifecycle"] == "open"

    def test_dependency_round_trip(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "dependency", "D1",
                            details={"direction": "upstream",
                                     "counterpart_ref": "project:proj-other"})
        assert item["item_type"] == "dependency"
        assert item["lifecycle"] == "healthy"

    def test_signal_round_trip(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "signal", "S1",
                            details={"metric": "velocity", "unit": "pts/wk",
                                     "latest_value": 42})
        assert item["item_type"] == "signal"
        assert item["lifecycle"] == "active"

    def test_workstream_round_trip(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "workstream", "W1",
                            details={})
        assert item["item_type"] == "workstream"
        assert item["lifecycle"] == "active"


# ── Closed-schema refusals ─────────────────────────────────────────────

class TestClosedSchemaRefusals:
    def test_unknown_item_type_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="Unknown item_type"):
            _create_item(svc, proj["id"], "imaginary", "Nope")

    def test_unknown_field_in_details_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="Unknown fields"):
            _create_item(svc, proj["id"], "risk", "R",
                         details={"likelihood": "high", "impact": "low",
                                  "surprise_field": "boom"})

    def test_missing_required_field_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="required"):
            _create_item(svc, proj["id"], "risk", "R",
                         details={"likelihood": "high"})  # impact is required

    def test_wrong_type_in_details_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="invalid type"):
            _create_item(svc, proj["id"], "risk", "R",
                         details={"likelihood": 42, "impact": "high"})

    def test_invalid_dependency_direction_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="invalid type"):
            _create_item(svc, proj["id"], "dependency", "D",
                         details={"direction": "sideways",
                                  "counterpart_ref": "project:other"})

    def test_empty_title_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="title"):
            _create_item(svc, proj["id"], "milestone", "")

    def test_invalid_severity_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="severity"):
            _create_item(svc, proj["id"], "risk", "R",
                         severity="apocalyptic",
                         details={"likelihood": "high", "impact": "bad"})

    def test_invalid_lifecycle_for_type_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="lifecycle"):
            _create_item(svc, proj["id"], "risk", "R",
                         lifecycle="reached",  # only valid for milestones
                         details={"likelihood": "high", "impact": "bad"})

    def test_invalid_provenance_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="provenance_kind"):
            _create_item(svc, proj["id"], "milestone", "M",
                         provenance_kind="proposal")  # P2 only

    def test_invalid_owner_ref_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="owner_ref"):
            _create_item(svc, proj["id"], "milestone", "M",
                         owner_ref="not-a-ref")


# ── Lifecycle verbs ────────────────────────────────────────────────────

class TestLifecycleVerbs:
    def test_milestone_transition_to_reached(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        assert item["lifecycle"] == "planned"
        result = svc.transition_item(OWNER, proj["id"], item["item_id"], "reached")
        assert result["lifecycle"] == "reached"

    def test_milestone_cannot_be_completed_via_update_dom_007(self, rig) -> None:
        """DOM-007: narrative prose cannot complete a milestone."""
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        with pytest.raises(ValidationError, match="DOM-007"):
            svc.update_item(OWNER, proj["id"], item["item_id"],
                            {"lifecycle": "reached"})

    def test_risk_lifecycle_transitions(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "risk", "R1",
                            details={"likelihood": "high", "impact": "bad"})
        assert item["lifecycle"] == "open"
        result = svc.transition_item(OWNER, proj["id"], item["item_id"], "mitigated")
        assert result["lifecycle"] == "mitigated"

    def test_transition_to_same_state_is_no_change(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        result = svc.transition_item(OWNER, proj["id"], item["item_id"], "planned")
        assert result["result_kind"] == "no_change"

    def test_transition_invalid_verb_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        with pytest.raises(ValidationError, match="lifecycle"):
            svc.transition_item(OWNER, proj["id"], item["item_id"], "vanished")

    def test_transition_wrong_project_not_found(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        proj2 = _create_project(svc, "Other")
        with pytest.raises(NotFound):
            svc.transition_item(OWNER, proj2["id"], item["item_id"], "reached")


# ── Ordering / pagination ──────────────────────────────────────────────

class TestOrderingPagination:
    def test_list_ordered_by_type_sort_key_created_at_id(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        _create_item(svc, proj["id"], "risk", "R1",
                     sort_key=2.0,
                     details={"likelihood": "high", "impact": "bad"})
        _create_item(svc, proj["id"], "milestone", "M1", sort_key=1.0)
        _create_item(svc, proj["id"], "risk", "R2",
                     sort_key=1.0,
                     details={"likelihood": "low", "impact": "low"})
        result = svc.list_items(OWNER, proj["id"])
        titles = [i["title"] for i in result["items"]]
        # milestone before risk (type ASC), then sort_key within type
        assert titles[0] == "M1"  # milestone
        assert titles[1] == "R2"  # risk sort_key=1
        assert titles[2] == "R1"  # risk sort_key=2

    def test_pagination_limit_offset(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        for i in range(5):
            _create_item(svc, proj["id"], "milestone", f"M{i}",
                         sort_key=float(i))
        page1 = svc.list_items(OWNER, proj["id"], limit=2, offset=0)
        page2 = svc.list_items(OWNER, proj["id"], limit=2, offset=2)
        assert len(page1["items"]) == 2
        assert len(page2["items"]) == 2
        assert page1["items"][0]["title"] == "M0"
        assert page2["items"][0]["title"] == "M2"

    def test_filter_by_type(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        _create_item(svc, proj["id"], "milestone", "M1")
        _create_item(svc, proj["id"], "risk", "R1",
                     details={"likelihood": "high", "impact": "bad"})
        result = svc.list_items(OWNER, proj["id"], item_type="milestone")
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "M1"

    def test_invalid_type_filter_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="Unknown item_type"):
            svc.list_items(OWNER, proj["id"], item_type="imaginary")

    def test_sort_key_nulls_last(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        _create_item(svc, proj["id"], "milestone", "no-key")
        _create_item(svc, proj["id"], "milestone", "with-key", sort_key=1.0)
        result = svc.list_items(OWNER, proj["id"], item_type="milestone")
        titles = [i["title"] for i in result["items"]]
        assert titles == ["with-key", "no-key"]


# ── Revision-law compliance ────────────────────────────────────────────

class TestRevisionLawCompliance:
    def test_create_item_increments_project_revision(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        rev_before = proj["project_revision"]
        _create_item(svc, proj["id"], "milestone", "M1")
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (proj["id"],),
            ).fetchone()
            assert row["revision"] == rev_before + 1

    def test_update_item_increments_project_revision(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        rev_after_create = item["project_revision"]
        svc.update_item(OWNER, proj["id"], item["item_id"],
                        {"title": "M1-updated"})
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (proj["id"],),
            ).fetchone()
            assert row["revision"] == rev_after_create + 1

    def test_transition_item_increments_project_revision(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        rev_after_create = item["project_revision"]
        svc.transition_item(OWNER, proj["id"], item["item_id"], "reached")
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (proj["id"],),
            ).fetchone()
            assert row["revision"] == rev_after_create + 1

    def test_create_item_appends_change_row(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)
        _create_item(svc, proj["id"], "milestone", "M1")
        changes = db.projects.list_project_changes(proj["id"])
        item_changes = [c for c in changes
                        if "item.created" in (c.get("summary_json") or "")]
        assert len(item_changes) == 1

    def test_stale_revision_on_create_item(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ConflictError) as exc_info:
            svc.create_item(OWNER, proj["id"],
                            {"item_type": "milestone", "title": "M"},
                            expected_revision=999)
        assert exc_info.value.code == "stale_revision"

    def test_stale_revision_on_update_item(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        with pytest.raises(ConflictError) as exc_info:
            svc.update_item(OWNER, proj["id"], item["item_id"],
                            {"title": "X"}, expected_revision=999)
        assert exc_info.value.code == "stale_revision"

    def test_stale_revision_on_transition_item(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        with pytest.raises(ConflictError) as exc_info:
            svc.transition_item(OWNER, proj["id"], item["item_id"],
                                "reached", expected_revision=999)
        assert exc_info.value.code == "stale_revision"

    def test_create_item_idempotent_replay(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        cmd_id = generate_pcmd_id()
        r1 = svc.create_item(
            OWNER, proj["id"],
            {"item_type": "milestone", "title": "M"},
            command_id=cmd_id,
        )
        r2 = svc.create_item(
            OWNER, proj["id"],
            {"item_type": "milestone", "title": "M"},
            command_id=cmd_id,
        )
        assert r2["result_kind"] == r1["result_kind"]
        assert r2["project_id"] == r1["project_id"]

    def test_create_item_idempotency_conflict(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        cmd_id = generate_pcmd_id()
        svc.create_item(OWNER, proj["id"],
                        {"item_type": "milestone", "title": "M"},
                        command_id=cmd_id)
        with pytest.raises(ConflictError) as exc_info:
            svc.create_item(OWNER, proj["id"],
                            {"item_type": "milestone", "title": "Different"},
                            command_id=cmd_id)
        assert exc_info.value.code == "idempotency_conflict"

    def test_fault_injection_create_item_atomicity(self, rig) -> None:
        """Force failure in event append; verify no orphan revision bump."""
        db, svc = rig
        proj = _create_project(svc)
        original_rev = proj["project_revision"]

        original_append = svc._ledger.append_in_transaction

        def exploding_append(*args, **kwargs):
            raise RuntimeError("simulated failure")

        svc._ledger.append_in_transaction = exploding_append
        try:
            with pytest.raises(RuntimeError, match="simulated"):
                svc.create_item(OWNER, proj["id"],
                                {"item_type": "milestone", "title": "Boom"})
        finally:
            svc._ledger.append_in_transaction = original_append

        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (proj["id"],),
            ).fetchone()
            assert row["revision"] == original_rev

    def test_changed_refs_carry_project(self, rig) -> None:
        """Items are Project-OWNED; changed_refs carries project:<id>."""
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        from holdspeak.refs import parse as parse_ref
        refs = item["changed_refs"]
        assert len(refs) >= 1
        parsed = parse_ref(refs[0])
        assert parsed.type == "project"
        assert parsed.id == proj["id"]


# ── Severity validation ────────────────────────────────────────────────

class TestSeverityValidation:
    def test_valid_severities_accepted(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        for sev in SEVERITY_LEVELS:
            item = _create_item(svc, proj["id"], "milestone", f"S-{sev}",
                                severity=sev)
            assert item["severity"] == sev

    def test_null_severity_accepted(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "No Sev")
        assert item["severity"] is None

    def test_invalid_severity_rejected(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(ValidationError, match="severity"):
            _create_item(svc, proj["id"], "milestone", "Bad",
                         severity="extreme")


# ── Room focus rank proof ──────────────────────────────────────────────

class TestRoomFocusRankProof:
    """Prove the CASE-based rank ordering: critical < high < medium < low < null."""

    def test_severity_rank_order_in_room_focus(self, rig) -> None:
        db, svc = rig
        proj = _create_project(svc)

        # Insert items with each severity, in reverse order
        for sev in [None, "low", "medium", "high", "critical"]:
            db.projects.insert_project_item(
                item_id=generate_pitem_id(),
                project_id=proj["id"],
                item_type="risk",
                title=f"sev-{sev}",
                severity=sev,
            )

        result = svc.room(OWNER, proj["id"])
        focus = result["items"]["focus"]
        titles = [i["title"] for i in focus]

        # Must be: critical, high, medium, low, null
        assert titles == [
            "sev-critical",
            "sev-high",
            "sev-medium",
            "sev-low",
            "sev-None",
        ]

    def test_rank_order_constants_match_case_expression(self, rig) -> None:
        """SEVERITY_RANK dict must assign lower numbers to higher severity."""
        assert SEVERITY_RANK["critical"] < SEVERITY_RANK["high"]
        assert SEVERITY_RANK["high"] < SEVERITY_RANK["medium"]
        assert SEVERITY_RANK["medium"] < SEVERITY_RANK["low"]


# ── Update item tests ──────────────────────────────────────────────────

class TestUpdateItem:
    def test_update_title(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "Original")
        result = svc.update_item(OWNER, proj["id"], item["item_id"],
                                 {"title": "Updated"})
        assert result["title"] == "Updated"

    def test_update_details(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "risk", "R1",
                            details={"likelihood": "high", "impact": "severe"})
        result = svc.update_item(OWNER, proj["id"], item["item_id"],
                                 {"details": {"likelihood": "low", "impact": "minor"}})
        detail = json.loads(result["details_json"])
        assert detail["likelihood"] == "low"

    def test_update_severity(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        result = svc.update_item(OWNER, proj["id"], item["item_id"],
                                 {"severity": "high"})
        assert result["severity"] == "high"

    def test_update_nonexistent_item_not_found(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        with pytest.raises(NotFound):
            svc.update_item(OWNER, proj["id"], "pitem_0" * 4 + "0" * 16,
                            {"title": "X"})

    def test_update_item_wrong_project(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        proj2 = _create_project(svc, "Other")
        item = _create_item(svc, proj["id"], "milestone", "M1")
        with pytest.raises(NotFound):
            svc.update_item(OWNER, proj2["id"], item["item_id"],
                            {"title": "X"})

    def test_update_no_fields_refused(self, rig) -> None:
        _db, svc = rig
        proj = _create_project(svc)
        item = _create_item(svc, proj["id"], "milestone", "M1")
        with pytest.raises(ValidationError, match="No updatable fields"):
            svc.update_item(OWNER, proj["id"], item["item_id"], {})


# ── Integration route tests ───────────────────────────────────────────

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

    def test_create_item_route(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Route Test"}).json()["project"]
        resp = client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone",
            "title": "M Route",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["item"]["item_type"] == "milestone"
        assert body["item"]["title"] == "M Route"

    def test_list_items_route(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "List Route"}).json()["project"]
        client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone", "title": "M1",
        })
        resp = client.get(f"/api/projects/{proj['id']}/items")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1

    def test_update_item_route(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Update Route"}).json()["project"]
        item = client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone", "title": "M1",
        }).json()["item"]
        resp = client.patch(
            f"/api/projects/{proj['id']}/items/{item['item_id']}",
            json={"title": "M1-updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["item"]["title"] == "M1-updated"

    def test_transition_item_route(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Trans Route"}).json()["project"]
        item = client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone", "title": "M1",
        }).json()["item"]
        resp = client.post(
            f"/api/projects/{proj['id']}/items/{item['item_id']}/transition",
            json={"verb": "reached"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["item"]["lifecycle"] == "reached"

    def test_transition_missing_verb_400(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "No Verb"}).json()["project"]
        item = client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone", "title": "M1",
        }).json()["item"]
        resp = client.post(
            f"/api/projects/{proj['id']}/items/{item['item_id']}/transition",
            json={},
        )
        assert resp.status_code == 400

    def test_create_item_validation_error_400(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Val Err"}).json()["project"]
        resp = client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "unknown_type", "title": "Nope",
        })
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_create_item_conflict_409(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Conflict"}).json()["project"]
        resp = client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone", "title": "M", "expected_revision": 999,
        })
        assert resp.status_code == 409

    def test_list_items_filter_by_type(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Filter"}).json()["project"]
        client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "milestone", "title": "M1",
        })
        client.post(f"/api/projects/{proj['id']}/items", json={
            "item_type": "risk", "title": "R1",
            "details": {"likelihood": "high", "impact": "bad"},
        })
        resp = client.get(f"/api/projects/{proj['id']}/items?item_type=risk")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["item_type"] == "risk"

    def test_list_items_not_found_404(self, rig, client) -> None:
        resp = client.get("/api/projects/proj-nope/items")
        assert resp.status_code == 404
