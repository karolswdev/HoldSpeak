"""HS-158-02 -- The revision law: every write increments revision exactly
once, appends a change row, appends a ledger event, atomically.

Tests:
- Exactly-one-increment per command
- Conflict paths (stale_revision)
- Idempotent replay (same command_id + hash => stored result)
- Idempotency conflict (same command_id, different hash)
- Restore round-trip (archive -> restore -> verify)
- Restore of non-archived project => no_change
- Fault injection: forced failure between change-append and commit
  leaves no orphan rows / no revision bump
- changed_refs parse through holdspeak.refs
- Legacy calls without new params behave exactly as before (additive keys only)
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import ResultKind, generate_pcmd_id
from holdspeak.refs import parse as parse_ref
from holdspeak.services.errors import ConflictError, NotFound
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "revision-law-test")


# ── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "revision-law.db")
    svc = ProjectService(db)
    yield db, svc
    reset_database()


def _create(svc: ProjectService, command_id: str | None = None, **kw: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": "Rev Law Project", **kw}
    return svc.create_project(OWNER, payload, command_id=command_id)


def _save_meeting(db: Database, mid: str, title: str = "Standup") -> None:
    db.meetings.save_meeting(MeetingState(
        id=mid, started_at=datetime(2026, 1, 15, 10, 0),
        title=title, capture_status="finalized",
    ))


# ── Exactly-one-increment per command ────────────────────────────────────

class TestExactlyOneIncrement:
    def test_create_starts_at_revision_1(self, rig) -> None:
        _db, svc = rig
        result = _create(svc)
        assert result["project_revision"] == 1

    def test_update_increments_by_one(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        updated = svc.update_project(OWNER, created["id"], {"name": "V2"})
        assert updated["project_revision"] == 2

    def test_archive_increments_by_one(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        # Check DB directly
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == 2

    def test_restore_increments_by_one(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        result = svc.restore_project(OWNER, created["id"])
        assert result["project_revision"] == 3

    def test_add_resource_increments(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.add_resource(OWNER, created["id"], "note:n1")
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == 2

    def test_remove_resource_increments(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.add_resource(OWNER, created["id"], "note:n1")
        svc.remove_resource(OWNER, created["id"], "note:n1")
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == 3

    def test_associate_meeting_increments(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        _save_meeting(db, "m1")
        svc.associate_meeting(OWNER, created["id"], "m1")
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == 2

    def test_disassociate_meeting_increments(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        _save_meeting(db, "m1")
        svc.associate_meeting(OWNER, created["id"], "m1")
        svc.disassociate_meeting(OWNER, created["id"], "m1")
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == 3


# ── Change rows ──────────────────────────────────────────────────────────

class TestChangeRows:
    def test_create_appends_change_row(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        changes = db.projects.list_project_changes(created["id"])
        assert len(changes) == 1
        assert changes[0]["change_kind"] == "project.created"
        assert changes[0]["project_revision"] == 1

    def test_update_appends_change_row(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.update_project(OWNER, created["id"], {"name": "V2"})
        changes = db.projects.list_project_changes(created["id"])
        assert len(changes) == 2
        # Most recent first (DESC ordering)
        assert changes[0]["change_kind"] == "project.updated"
        assert changes[0]["project_revision"] == 2

    def test_archive_appends_change_row(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        changes = db.projects.list_project_changes(created["id"])
        assert any(c["change_kind"] == "project.archived" for c in changes)

    def test_restore_appends_change_row(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        svc.restore_project(OWNER, created["id"])
        changes = db.projects.list_project_changes(created["id"])
        assert any(c["change_kind"] == "project.restored" for c in changes)


# ── Conflict paths (stale_revision) ─────────────────────────────────────

class TestStaleRevisionConflict:
    def test_update_with_wrong_revision(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ConflictError) as exc_info:
            svc.update_project(OWNER, created["id"], {"name": "X"},
                               expected_revision=999)
        assert exc_info.value.code == "stale_revision"

    def test_archive_with_wrong_revision(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        with pytest.raises(ConflictError) as exc_info:
            svc.archive_project(OWNER, created["id"], expected_revision=999)
        assert exc_info.value.code == "stale_revision"

    def test_restore_with_wrong_revision(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        with pytest.raises(ConflictError) as exc_info:
            svc.restore_project(OWNER, created["id"], expected_revision=999)
        assert exc_info.value.code == "stale_revision"

    def test_no_partial_mutation_on_stale(self, rig) -> None:
        """A stale revision check leaves the revision unchanged."""
        db, svc = rig
        created = _create(svc)
        original_rev = created["project_revision"]
        with pytest.raises(ConflictError):
            svc.update_project(OWNER, created["id"], {"name": "X"},
                               expected_revision=999)
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == original_rev

    def test_correct_revision_succeeds(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.update_project(
            OWNER, created["id"], {"name": "OK"},
            expected_revision=created["project_revision"],
        )
        assert result["project_revision"] == created["project_revision"] + 1


# ── Idempotent replay (API-002) ──────────────────────────────────────────

class TestIdempotentReplay:
    def test_same_command_id_same_hash_returns_stored(self, rig) -> None:
        _db, svc = rig
        cmd_id = generate_pcmd_id()
        result1 = _create(svc, name="Idem", command_id=cmd_id)
        result2 = svc.create_project(OWNER, {"name": "Idem"},
                                     command_id=cmd_id)
        # Replay returns the stored result
        assert result2["result_kind"] == result1["result_kind"]
        assert result2["project_id"] == result1["project_id"]

    def test_same_command_id_different_hash_raises(self, rig) -> None:
        _db, svc = rig
        cmd_id = generate_pcmd_id()
        _create(svc, name="First", command_id=cmd_id)
        with pytest.raises(ConflictError) as exc_info:
            svc.create_project(OWNER, {"name": "Different"},
                               command_id=cmd_id)
        assert exc_info.value.code == "idempotency_conflict"

    def test_update_replay(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        cmd_id = generate_pcmd_id()
        r1 = svc.update_project(OWNER, created["id"], {"name": "Up"},
                                command_id=cmd_id)
        r2 = svc.update_project(OWNER, created["id"], {"name": "Up"},
                                command_id=cmd_id)
        assert r2["result_kind"] == r1["result_kind"]


# ── Restore round-trip ───────────────────────────────────────────────────

class TestRestoreRoundTrip:
    def test_archive_then_restore(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        after_archive = svc.get_project(OWNER, created["id"])
        assert after_archive["is_archived"] is True

        result = svc.restore_project(OWNER, created["id"])
        assert result["result_kind"] == "restored"
        assert result["is_archived"] is False

    def test_restore_non_archived_returns_no_change(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.restore_project(OWNER, created["id"])
        assert result["result_kind"] == "no_change"
        assert result["project_revision"] == 1  # unchanged

    def test_restore_not_found(self, rig) -> None:
        _db, svc = rig
        with pytest.raises(NotFound):
            svc.restore_project(OWNER, "proj-nonexistent")

    def test_restore_double_is_no_change(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.archive_project(OWNER, created["id"])
        svc.restore_project(OWNER, created["id"])
        result = svc.restore_project(OWNER, created["id"])
        assert result["result_kind"] == "no_change"


# ── changed_refs parse through holdspeak.refs ────────────────────────────

class TestChangedRefs:
    def test_create_changed_refs(self, rig) -> None:
        _db, svc = rig
        result = _create(svc)
        refs = result["changed_refs"]
        assert len(refs) >= 1
        # Each ref must be parseable
        for ref_str in refs:
            parsed = parse_ref(ref_str)
            assert parsed.is_registered

    def test_update_changed_refs(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.update_project(OWNER, created["id"], {"name": "V2"})
        refs = result["changed_refs"]
        assert len(refs) >= 1
        parsed = parse_ref(refs[0])
        assert parsed.type == "project"
        assert parsed.id == created["id"]

    def test_associate_meeting_changed_refs(self, rig) -> None:
        """Meeting association adds both project and meeting refs."""
        db, svc = rig
        created = _create(svc)
        _save_meeting(db, "m1")
        # We can check the envelope stored in project_commands
        cmd_id = generate_pcmd_id()
        svc.associate_meeting(OWNER, created["id"], "m1", command_id=cmd_id)
        cmd = db.projects.get_project_command(cmd_id)
        assert cmd is not None
        stored = json.loads(cmd["result_json"])
        refs = stored["changed_refs"]
        types = {parse_ref(r).type for r in refs}
        assert "project" in types
        assert "meeting" in types


# ── Fault injection: atomicity ───────────────────────────────────────────

class TestFaultInjection:
    def test_failure_in_event_append_leaves_no_orphan(self, rig) -> None:
        """Force failure between change-append and commit; assert no orphan
        rows and no revision bump (DOM-003, DOM-004, API-004)."""
        db, svc = rig
        created = _create(svc)
        original_rev = created["project_revision"]

        # Monkeypatch the ledger to blow up
        original_append = svc._ledger.append_in_transaction

        def exploding_append(*args, **kwargs):
            raise RuntimeError("simulated event-ledger failure")

        svc._ledger.append_in_transaction = exploding_append
        try:
            with pytest.raises(RuntimeError, match="simulated"):
                svc.update_project(OWNER, created["id"], {"name": "Boom"})
        finally:
            svc._ledger.append_in_transaction = original_append

        # Revision should NOT have advanced
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == original_rev

        # No orphan change row for the failed revision
        changes = db.projects.list_project_changes(created["id"])
        failed_rev_changes = [c for c in changes
                              if c["project_revision"] == original_rev + 1]
        assert len(failed_rev_changes) == 0

    def test_failure_in_command_record_leaves_no_orphan(self, rig) -> None:
        """Force failure in command recording; revision and changes should
        be rolled back."""
        db, svc = rig
        created = _create(svc)
        original_rev = created["project_revision"]

        original_record = svc._record_command

        def exploding_record(*args, **kwargs):
            raise RuntimeError("simulated command-record failure")

        svc._record_command = exploding_record
        try:
            with pytest.raises(RuntimeError, match="simulated"):
                svc.update_project(OWNER, created["id"], {"name": "Boom2"})
        finally:
            svc._record_command = original_record

        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision FROM projects WHERE id = ?",
                (created["id"],),
            ).fetchone()
            assert row["revision"] == original_rev


# ── Legacy calls without new params ──────────────────────────────────────

class TestLegacyBehavior:
    def test_create_without_command_id(self, rig) -> None:
        """Legacy create (no command_id) still works."""
        _db, svc = rig
        result = _create(svc)
        assert result["id"].startswith("proj-")
        assert result["name"] == "Rev Law Project"
        # Legacy keys present
        assert "is_archived" in result
        assert "meeting_count" in result
        # Additive keys also present
        assert "result_kind" in result
        assert result["result_kind"] == "created"

    def test_update_without_expected_revision(self, rig) -> None:
        """Legacy update (no expected_revision) always succeeds."""
        _db, svc = rig
        created = _create(svc)
        result = svc.update_project(OWNER, created["id"], {"name": "V2"})
        assert result["name"] == "V2"
        assert result["result_kind"] == "updated"

    def test_archive_without_params(self, rig) -> None:
        """Legacy archive (no expected_revision/command_id) returns True."""
        _db, svc = rig
        created = _create(svc)
        assert svc.archive_project(OWNER, created["id"]) is True

    def test_add_resource_without_params(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        result = svc.add_resource(OWNER, created["id"], "note:n1")
        assert result["resource_ref"] == "note:n1"
        assert "result_kind" in result
        assert result["result_kind"] == "linked"

    def test_remove_resource_without_params(self, rig) -> None:
        _db, svc = rig
        created = _create(svc)
        svc.add_resource(OWNER, created["id"], "note:n1")
        assert svc.remove_resource(OWNER, created["id"], "note:n1") is True

    def test_associate_meeting_without_params(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        _save_meeting(db, "m1")
        assert svc.associate_meeting(OWNER, created["id"], "m1") is True

    def test_disassociate_meeting_without_params(self, rig) -> None:
        db, svc = rig
        created = _create(svc)
        _save_meeting(db, "m1")
        svc.associate_meeting(OWNER, created["id"], "m1")
        assert svc.disassociate_meeting(OWNER, created["id"], "m1") is True


# ── Route-level pass-through ─────────────────────────────────────────────

class TestRouteLevelPassThrough:
    """Integration: verify restore route and conflict responses."""

    @pytest.fixture
    def client(self, rig):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import holdspeak.db as hsdb

        db, _svc = rig
        from unittest.mock import patch as mp
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

    def test_restore_route_success(self, rig, client) -> None:
        db, _svc = rig
        proj = client.post("/api/projects", json={"name": "Restore Me"}).json()["project"]
        client.delete(f"/api/projects/{proj['id']}")
        resp = client.post(f"/api/projects/{proj['id']}/restore", json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["project"]["result_kind"] == "restored"
        assert body["project"]["is_archived"] is False

    def test_restore_route_not_found_404(self, rig, client) -> None:
        resp = client.post("/api/projects/proj-nope/restore", json={})
        assert resp.status_code == 404

    def test_restore_route_not_archived_no_change(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Active"}).json()["project"]
        resp = client.post(f"/api/projects/{proj['id']}/restore", json={})
        assert resp.status_code == 200
        assert resp.json()["project"]["result_kind"] == "no_change"

    def test_update_conflict_409(self, rig, client) -> None:
        proj = client.post("/api/projects", json={"name": "Conflict"}).json()["project"]
        resp = client.patch(
            f"/api/projects/{proj['id']}",
            json={"name": "X", "expected_revision": 999},
        )
        assert resp.status_code == 409
        body = resp.json()
        assert body["success"] is False
        assert body["error_code"] == "stale_revision"
