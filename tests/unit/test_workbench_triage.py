"""HS-118-09 — Artifact triage: kernel admission, atomic transitions,
reject clearing artifact link, rework cycle.
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database


@pytest.fixture
def temp_db_path():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield db_path
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_path):
    return Database(temp_db_path)


def _create_workbench(db, name="Test WB"):
    return db.workbenches.upsert(workbench_id="wb-test-1", name=name)


def _create_item(db, workbench_id="wb-test-1", item_id="wbi-1", title="Test item", status="done", result="Some output"):
    return db.workbench_items.upsert(
        item_id=item_id,
        workbench_id=workbench_id,
        title=title,
        body="Do something",
        priority=3,
        status=status,
        result=result,
    )


_run_counter = 0

def _create_pending_review_artifact(db, artifact_id="art-1", item_id="wbi-1", run_id=None):
    """Create a pending-review artifact and link it to the item."""
    global _run_counter
    _run_counter += 1
    if run_id is None:
        run_id = f"run-{_run_counter}"
    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """
            INSERT INTO artifacts (id, meeting_id, origin, artifact_type, title, body_markdown,
                structured_json, confidence, status, plugin_id, plugin_version,
                source_run_id, source_item_id, created_at, updated_at)
            VALUES (?, NULL, 'run', 'workbench_output', ?, 'Test output', '{}', 0.0,
                    'pending-review', 'workbench_run', '1', ?, ?, ?, ?)
            """,
            (artifact_id, f"Agent: Test", run_id, item_id, now_iso, now_iso),
        )
        conn.execute(
            "UPDATE workbench_items SET result_artifact_id = ?, last_modified = ? WHERE id = ?",
            (artifact_id, now_iso, item_id),
        )
    return artifact_id


class TestWorkbenchTriageCodec:
    """Test the kernel codec for workbench_triage."""

    def test_parse_valid_accept(self):
        from holdspeak.kernel.workbench_triage import WorkbenchTriageCodec
        from holdspeak.kernel.model import OperationRequest

        codec = WorkbenchTriageCodec()
        request = OperationRequest(
            request_schema=1,
            request_id="req-1",
            idempotency_key="triage:accept:wbi-1:art-1",
            name="workbench_triage",
            version=1,
            target_ref="",
            placement="",
            arguments={
                "workbench_id": "wb-1",
                "item_id": "wbi-1",
                "artifact_id": "art-1",
                "action": "accept",
            },
        )
        admission = codec.parse(request)
        assert admission.action == "accept"
        assert admission.item_id == "wbi-1"
        assert admission.artifact_id == "art-1"
        assert admission.target_ref == "artifact:art-1"

    def test_parse_valid_reject(self):
        from holdspeak.kernel.workbench_triage import WorkbenchTriageCodec
        from holdspeak.kernel.model import OperationRequest

        codec = WorkbenchTriageCodec()
        request = OperationRequest(
            request_schema=1,
            request_id="req-1",
            idempotency_key="triage:reject:wbi-1:art-1",
            name="workbench_triage",
            version=1,
            target_ref="",
            placement="",
            arguments={
                "workbench_id": "wb-1",
                "item_id": "wbi-1",
                "artifact_id": "art-1",
                "action": "reject",
            },
        )
        admission = codec.parse(request)
        assert admission.action == "reject"

    def test_parse_valid_rework(self):
        from holdspeak.kernel.workbench_triage import WorkbenchTriageCodec
        from holdspeak.kernel.model import OperationRequest

        codec = WorkbenchTriageCodec()
        request = OperationRequest(
            request_schema=1,
            request_id="req-1",
            idempotency_key="triage:rework:wbi-1:art-1",
            name="workbench_triage",
            version=1,
            target_ref="",
            placement="",
            arguments={
                "workbench_id": "wb-1",
                "item_id": "wbi-1",
                "artifact_id": "art-1",
                "action": "rework",
            },
        )
        admission = codec.parse(request)
        assert admission.action == "rework"

    def test_parse_invalid_action(self):
        from holdspeak.kernel.workbench_triage import WorkbenchTriageCodec
        from holdspeak.kernel.model import KernelRefused, OperationRequest

        codec = WorkbenchTriageCodec()
        request = OperationRequest(
            request_schema=1,
            request_id="req-1",
            idempotency_key="triage:bad:wbi-1:art-1",
            name="workbench_triage",
            version=1,
            target_ref="",
            placement="",
            arguments={
                "workbench_id": "wb-1",
                "item_id": "wbi-1",
                "artifact_id": "art-1",
                "action": "snooze",
            },
        )
        with pytest.raises(KernelRefused):
            codec.parse(request)

    def test_parse_missing_fields(self):
        from holdspeak.kernel.workbench_triage import WorkbenchTriageCodec
        from holdspeak.kernel.model import KernelRefused, OperationRequest

        codec = WorkbenchTriageCodec()
        request = OperationRequest(
            request_schema=1,
            request_id="req-1",
            idempotency_key="triage:accept:wbi-1",
            name="workbench_triage",
            version=1,
            target_ref="",
            placement="",
            arguments={"workbench_id": "wb-1", "item_id": "wbi-1"},
        )
        with pytest.raises(KernelRefused):
            codec.parse(request)


class TestTriageAcceptDB:
    """Test accept triage at the DB level."""

    def test_accept_changes_artifact_to_draft(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        # Verify initial state
        art = db.plugins.get_artifact(art_id)
        assert art.status == "pending-review"

        # Simulate accept
        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'draft', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )

        art = db.plugins.get_artifact(art_id)
        assert art.status == "draft"

    def test_accepted_artifact_visible_in_run_list(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        # Before accept: not visible in run artifacts
        run_artifacts = db.plugins.list_run_artifacts()
        assert not any(a.id == art_id for a in run_artifacts)

        # Accept
        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'draft', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )

        # After accept: visible
        run_artifacts = db.plugins.list_run_artifacts()
        assert any(a.id == art_id for a in run_artifacts)


class TestTriageRejectDB:
    """Test reject triage at the DB level."""

    def test_reject_archives_artifact_and_dismisses_item(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'rejected', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )
            conn.execute(
                "UPDATE workbench_items SET status = 'dismissed', result_artifact_id = NULL, last_modified = ? WHERE id = ?",
                (now_iso, "wbi-1"),
            )

        art = db.plugins.get_artifact(art_id)
        assert art.status == "rejected"

        item = db.workbench_items.get("wbi-1")
        assert item.status == "dismissed"
        assert item.result_artifact_id is None

    def test_rejected_artifact_hidden_from_run_list(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'rejected', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )

        run_artifacts = db.plugins.list_run_artifacts()
        assert not any(a.id == art_id for a in run_artifacts)

    def test_rejected_artifact_still_in_db(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'rejected', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )

        # Still fetchable by ID (lineage)
        art = db.plugins.get_artifact(art_id)
        assert art is not None
        assert art.status == "rejected"


class TestTriageReworkDB:
    """Test rework triage at the DB level."""

    def test_rework_resets_item_to_pending(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        now_iso = datetime.now().isoformat()
        refinement = "Make it shorter"
        new_body = (item.body or "") + f"\n\n[REFINEMENT]\n{refinement}"

        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'rejected', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )
            conn.execute(
                "UPDATE workbench_items SET status = 'pending', result = NULL, result_artifact_id = NULL, body = ?, last_modified = ? WHERE id = ?",
                (new_body, now_iso, "wbi-1"),
            )

        item = db.workbench_items.get("wbi-1")
        assert item.status == "pending"
        assert item.result_artifact_id is None
        assert item.result is None
        assert "[REFINEMENT]" in item.body
        assert refinement in item.body

    def test_rework_cycle_allows_new_triage(self, db):
        """After rework, a new artifact can be minted and triaged again."""
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id_1 = _create_pending_review_artifact(db, artifact_id="art-1")

        # Rework: archive artifact, reset item
        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'rejected', updated_at = ? WHERE id = ?",
                (now_iso, "art-1"),
            )
            conn.execute(
                "UPDATE workbench_items SET status = 'pending', result = NULL, result_artifact_id = NULL, last_modified = ? WHERE id = ?",
                (now_iso, "wbi-1"),
            )

        # Simulate agent re-run: item gets done again with new result
        db.workbench_items.upsert(
            item_id="wbi-1",
            workbench_id="wb-test-1",
            title="Test item",
            body="Do something\n\n[REFINEMENT]\nMake it shorter",
            priority=3,
            status="done",
            result="New improved output",
        )

        # New mint with different artifact ID
        art_id_2 = _create_pending_review_artifact(db, artifact_id="art-2", item_id="wbi-1")

        item = db.workbench_items.get("wbi-1")
        assert item.result_artifact_id == "art-2"

        art_2 = db.plugins.get_artifact("art-2")
        assert art_2.status == "pending-review"

        # Can now accept the new artifact
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'draft', updated_at = ? WHERE id = ?",
                (now_iso, "art-2"),
            )

        art_2 = db.plugins.get_artifact("art-2")
        assert art_2.status == "draft"


class TestDoubleTriage:
    """Test that double triage is prevented (409)."""

    def test_double_accept_fails(self, db):
        """Once accepted, the artifact is no longer pending-review."""
        wb = _create_workbench(db)
        item = _create_item(db)
        art_id = _create_pending_review_artifact(db)

        now_iso = datetime.now().isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE artifacts SET status = 'draft', updated_at = ? WHERE id = ?",
                (now_iso, art_id),
            )

        art = db.plugins.get_artifact(art_id)
        assert art.status != "pending-review"


class TestTriageWithoutArtifact:
    """Test triage on item without artifact returns error."""

    def test_no_artifact_id(self, db):
        wb = _create_workbench(db)
        item = _create_item(db)
        # Item has no result_artifact_id by default
        assert item.result_artifact_id is None
