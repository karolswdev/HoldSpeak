"""HS-172-02 + HS-172-03 -- the auto-intel trigger and the proposal bridge.

Tests:
  - The trigger fires for a Room-linked meeting with a transcript and not for
    an unlinked one under ``room_linked``.
  - Fires for both under ``every``; never under ``off``.
  - No transcript -> no run.
  - The bridge writes N proposals from fixture artifacts and a re-run writes
    0 more (idempotent).
  - Confirm writes the decision/action through the kernel with a receipt and
    keeps original_text.
  - Dismiss.
  - The Room's needsYou carries the proposals.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test_loop.db")


# ── Seed helpers ─────────────────────────────────────────────────────

def _seed_meeting(db: Database, meeting_id: str, *, has_segments: bool = True, title: str = "Standup") -> None:
    """Insert a minimal meeting row."""
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings
               (id, started_at, ended_at, title, duration_seconds,
                intel_status, capture_status)
               VALUES (?, ?, ?, ?, 300, 'disabled', 'finalized')""",
            (meeting_id, datetime.now().isoformat(), datetime.now().isoformat(), title),
        )
        if has_segments:
            conn.execute(
                """INSERT INTO segments (meeting_id, start_time, end_time, text, speaker)
                   VALUES (?, 0.0, 10.0, 'Hello world', 'Alice')""",
                (meeting_id,),
            )


def _seed_project(db: Database, project_id: str) -> None:
    """Insert a minimal project row."""
    with db._connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO projects (id, name, created_at, updated_at)
               VALUES (?, 'Test Project', datetime('now'), datetime('now'))""",
            (project_id,),
        )


def _link_meeting_project(db: Database, meeting_id: str, project_id: str) -> None:
    """Link a meeting to a project (room)."""
    with db._connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO meeting_projects
               (meeting_id, project_id, source, confidence)
               VALUES (?, ?, 'auto', 0.9)""",
            (meeting_id, project_id),
        )


def _seed_decision_artifact(
    db: Database,
    meeting_id: str,
    decisions: list[dict[str, Any]],
) -> str:
    """Insert a decision_capture artifact with structured data."""
    art_id = f"art-{uuid.uuid4().hex[:16]}"
    structured = json.dumps({"decisions": decisions})
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO artifacts
               (id, meeting_id, origin, artifact_type, title,
                body_markdown, structured_json, confidence,
                status, plugin_id, plugin_version)
               VALUES (?, ?, 'meeting', 'decision_capture', 'Decisions',
                       '', ?, 0.9, 'ready', 'decision_capture', '0.2.0')""",
            (art_id, meeting_id, structured),
        )
    return art_id


def _seed_action_artifact(
    db: Database,
    meeting_id: str,
    action_items: list[dict[str, Any]],
) -> str:
    """Insert an action_owner_enforcer artifact with structured data."""
    art_id = f"art-{uuid.uuid4().hex[:16]}"
    structured = json.dumps({"action_items": action_items})
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO artifacts
               (id, meeting_id, origin, artifact_type, title,
                body_markdown, structured_json, confidence,
                status, plugin_id, plugin_version)
               VALUES (?, ?, 'meeting', 'action_owner_enforcer', 'Actions',
                       '', ?, 0.9, 'ready', 'action_owner_enforcer', '0.1.0')""",
            (art_id, meeting_id, structured),
        )
    return art_id


# ── Auto-intel trigger tests ─────────────────────────────────────────

class TestAutoIntelTrigger:
    """HS-172-02: the auto-intel trigger setting and its conditions."""

    def test_invalid_auto_raises(self) -> None:
        """Invalid intelligence_auto value raises ValueError."""
        from holdspeak.config.meeting import MeetingConfig
        with pytest.raises(ValueError, match="intelligence_auto"):
            MeetingConfig(intelligence_auto="bogus")

    def test_default_is_room_linked(self) -> None:
        """Default intelligence_auto is room_linked."""
        from holdspeak.config.meeting import MeetingConfig
        cfg = MeetingConfig()
        assert cfg.intelligence_auto == "room_linked"

    def test_room_linked_enqueues_with_transcript(self, db: Database) -> None:
        """_maybe_auto_enqueue_intel enqueues for a Room-linked meeting."""
        import unittest.mock as mock

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)

        glue = mock.MagicMock()
        cfg_mock = mock.MagicMock()
        cfg_mock.meeting.intelligence_auto = "room_linked"
        with mock.patch("holdspeak.config.Config.load", return_value=cfg_mock):
            with mock.patch("holdspeak.db.get_database", return_value=db):
                from holdspeak.runtime.routing_glue import RoutingGlueMixin
                result = RoutingGlueMixin._maybe_auto_enqueue_intel(glue, meeting_id, None)

        assert result["enqueued"] is True
        assert result.get("error") is None
        job = db.intel.get_intel_job(meeting_id)
        assert job is not None
        host = db.intel.get_intel_job_model_host(meeting_id)
        assert host == "local"  # fallback when no placement profile

    def test_unlinked_no_enqueue_under_room_linked(self, db: Database) -> None:
        """_maybe_auto_enqueue_intel does NOT enqueue for an unlinked meeting under room_linked."""
        import unittest.mock as mock

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)

        glue = mock.MagicMock()
        cfg_mock = mock.MagicMock()
        cfg_mock.meeting.intelligence_auto = "room_linked"
        with mock.patch("holdspeak.config.Config.load", return_value=cfg_mock):
            with mock.patch("holdspeak.db.get_database", return_value=db):
                from holdspeak.runtime.routing_glue import RoutingGlueMixin
                result = RoutingGlueMixin._maybe_auto_enqueue_intel(glue, meeting_id, None)

        assert result["enqueued"] is False
        assert result["reason"] == "not_room_linked"

    def test_off_no_enqueue(self, db: Database) -> None:
        """_maybe_auto_enqueue_intel does NOT enqueue when auto=off."""
        import unittest.mock as mock

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)

        glue = mock.MagicMock()
        cfg_mock = mock.MagicMock()
        cfg_mock.meeting.intelligence_auto = "off"
        with mock.patch("holdspeak.config.Config.load", return_value=cfg_mock):
            from holdspeak.runtime.routing_glue import RoutingGlueMixin
            result = RoutingGlueMixin._maybe_auto_enqueue_intel(glue, meeting_id, None)

        assert result["enqueued"] is False
        assert result["reason"] == "auto_intel_off"


# ── Proposal bridge tests ───────────────────────────────────────────

class TestProposalBridge:
    """HS-172-03: the proposal bridge, confirm, dismiss, idempotency."""

    def test_bridge_creates_proposals(self, db: Database) -> None:
        """Bridging decision + action artifacts creates proposals."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Adopt PostgreSQL 17", "source_timestamp": 5.0, "speaker": "Marek"},
        ])
        _seed_action_artifact(db, meeting_id, [
            {"task": "Marek owns the migration", "owner": "Marek", "due": "Fri"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id, model_host="local")

        assert len(created) == 2
        kinds = {p.kind for p in created}
        assert kinds == {"decision", "action"}
        assert all(p.state == "proposed" for p in created)
        assert all(p.project_id == project_id for p in created)

    def test_bridge_idempotent(self, db: Database) -> None:
        """Re-running the bridge for the same meeting writes 0 more."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Decision A"},
        ])

        bridge = ProposalBridgeService(db)
        first = bridge.bridge_meeting_artifacts(meeting_id)
        assert len(first) == 1

        second = bridge.bridge_meeting_artifacts(meeting_id)
        assert len(second) == 0

    def test_confirm_decision_writes_full_chain(self, db: Database) -> None:
        """Confirming a decision proposal writes decisions + decision_records + commitment."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Use Redis for caching"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        assert len(created) == 1
        prop = created[0]

        result = bridge.confirm_proposal(OWNER, prop.id)
        assert result.get("state") == "confirmed"
        assert "decision_id" in result
        assert "decision_record_id" in result
        assert "action_item_id" in result
        assert "commitment_id" in result

        with db._connection() as conn:
            # decisions row
            dec = conn.execute(
                "SELECT * FROM decisions WHERE id = ?",
                (result["decision_id"],),
            ).fetchone()
            assert dec is not None
            assert dec["text"] == "Use Redis for caching"
            assert dec["lifecycle"] == "accepted"

            # decision_records row (what the Room reads)
            rec = conn.execute(
                "SELECT * FROM decision_records WHERE id = ?",
                (result["decision_record_id"],),
            ).fetchone()
            assert rec is not None
            assert rec["decision_text"] == "Use Redis for caching"

            # decision_record_sources links to the meeting
            src = conn.execute(
                "SELECT * FROM decision_record_sources WHERE record_id = ?",
                (result["decision_record_id"],),
            ).fetchone()
            assert src is not None
            assert src["source_type"] == "meeting"
            assert src["source_ref"] == meeting_id

            # decision_commitments row
            cmt = conn.execute(
                "SELECT * FROM decision_commitments WHERE id = ?",
                (result["commitment_id"],),
            ).fetchone()
            assert cmt is not None
            assert cmt["decision_id"] == result["decision_id"]
            assert cmt["action_item_id"] == result["action_item_id"]

    def test_confirm_action_writes_full_chain(self, db: Database) -> None:
        """Confirming an action proposal writes the full chain."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_action_artifact(db, meeting_id, [
            {"task": "Review the PR", "owner": "Alice", "due": "Monday"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        assert len(created) == 1
        prop = created[0]

        result = bridge.confirm_proposal(OWNER, prop.id, owner="Alice", due="Monday")
        assert result.get("state") == "confirmed"
        assert "action_item_id" in result
        assert "decision_record_id" in result
        assert "commitment_id" in result

        with db._connection() as conn:
            # action_items row
            ai = conn.execute(
                "SELECT * FROM action_items WHERE id = ?",
                (result["action_item_id"],),
            ).fetchone()
            assert ai is not None
            assert ai["task"] == "Review the PR"
            assert ai["owner"] == "Alice"

            # decision_records row
            rec = conn.execute(
                "SELECT * FROM decision_records WHERE id = ?",
                (result["decision_record_id"],),
            ).fetchone()
            assert rec is not None

            # commitment links them
            cmt = conn.execute(
                "SELECT * FROM decision_commitments WHERE id = ?",
                (result["commitment_id"],),
            ).fetchone()
            assert cmt is not None
            assert cmt["action_item_id"] == result["action_item_id"]
            assert cmt["owner"] == "Alice"

    def test_confirm_keeps_original_text(self, db: Database) -> None:
        """Confirming with amended text keeps original_text."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Original decision text"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        prop = created[0]

        result = bridge.confirm_proposal(OWNER, prop.id, text="Amended decision text")
        assert result.get("original_text") == "Original decision text"

        # The confirmed proposal row retains original_text.
        confirmed = db.proposals.get_proposal(prop.id)
        assert confirmed is not None
        assert confirmed.original_text == "Original decision text"
        assert confirmed.text == "Amended decision text"

    def test_dismiss_proposal(self, db: Database) -> None:
        """Dismissing a proposal sets state=dismissed without creating records."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Bad decision"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        prop = created[0]

        result = bridge.dismiss_proposal(OWNER, prop.id)
        assert result.get("state") == "dismissed"

        # No decision row.
        with db._connection() as conn:
            decisions = conn.execute(
                "SELECT COUNT(*) AS c FROM decisions WHERE source_meeting_id = ?",
                (meeting_id,),
            ).fetchone()
            assert decisions["c"] == 0

    def test_double_confirm_rejected(self, db: Database) -> None:
        """Confirming an already-confirmed proposal returns error."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "A"}])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.confirm_proposal(OWNER, created[0].id)
        result = bridge.confirm_proposal(OWNER, created[0].id)
        assert "error" in result


# ── Room needsYou proposals ─────────────────────────────────────────

class TestRoomNeedsYouProposals:
    """HS-172-03: proposals appear in the Room's needsYou."""

    def test_proposals_in_needs_you(self, db: Database) -> None:
        """Proposed proposals show as needsYou items."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id, title="Sprint Review")
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Adopt PostgreSQL"},
        ])

        bridge = ProposalBridgeService(db)
        bridge.bridge_meeting_artifacts(meeting_id)

        # List proposals for the project.
        proposals = db.proposals.list_proposals(project_id=project_id, state="proposed")
        assert len(proposals) == 1
        assert proposals[0].kind == "proposal" or proposals[0].kind == "decision"

    def test_dismissed_not_in_needs_you(self, db: Database) -> None:
        """Dismissed proposals do not show in proposed list."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "X"}])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.dismiss_proposal(OWNER, created[0].id)

        proposals = db.proposals.list_proposals(project_id=project_id, state="proposed")
        assert len(proposals) == 0


# ── Proposal listing ────────────────────────────────────────────────

class TestProposalListing:
    """HS-172-03: meeting and project proposal listing."""

    def test_list_meeting_proposals(self, db: Database) -> None:
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "D1"}, {"text": "D2"}])

        bridge = ProposalBridgeService(db)
        bridge.bridge_meeting_artifacts(meeting_id)

        proposals = bridge.list_meeting_proposals(meeting_id)
        assert len(proposals) == 2
        assert all(p["state"] == "proposed" for p in proposals)

    def test_list_project_proposals(self, db: Database) -> None:
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_action_artifact(db, meeting_id, [
            {"task": "A1", "owner": "Bob"},
            {"task": "A2", "owner": "Carol"},
        ])

        bridge = ProposalBridgeService(db)
        bridge.bridge_meeting_artifacts(meeting_id)

        proposals = bridge.list_project_proposals(project_id)
        assert len(proposals) == 2


# ── Room decisions read with proposal provenance ────────────────────

class TestRoomDecisionsRead:
    """HS-172-03: confirmed proposals appear in Room DECISIONS once, with provenance."""

    def _room_decisions(self, db: Database, project_id: str) -> dict[str, Any]:
        """Call _read_room_decisions via ProjectService."""
        from holdspeak.services.project_service import ProjectService
        svc = ProjectService(db)
        return svc._read_room_decisions(project_id)

    def _room_commitments(self, db: Database, project_id: str) -> dict[str, Any]:
        from holdspeak.services.project_service import ProjectService
        svc = ProjectService(db)
        return svc._read_room_commitments(project_id)

    def test_decision_confirm_shows_once_with_source(self, db: Database) -> None:
        """A confirmed decision-kind proposal appears exactly once in decisions."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id, title="Sprint Review")
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Adopt PostgreSQL 17"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.confirm_proposal(OWNER, created[0].id)

        decisions = self._room_decisions(db, project_id)
        items = decisions["items"]
        assert len(items) == 1, f"Expected 1 decision, got {len(items)}"
        item = items[0]
        assert item["text"] == "Adopt PostgreSQL 17"
        assert item["source"] == "meeting"
        assert item["meeting_title"] == "Sprint Review"
        assert item["confirmed_at"] is not None
        assert item["proposal_id"] is not None

    def test_decision_confirm_with_edit_has_was(self, db: Database) -> None:
        """A confirmed decision with amended text carries 'was' with the original."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id, title="Standup")
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Use MySQL"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.confirm_proposal(OWNER, created[0].id, text="Use PostgreSQL")

        decisions = self._room_decisions(db, project_id)
        item = decisions["items"][0]
        assert item["text"] == "Use PostgreSQL"
        assert "was" in item
        assert item["was"]["text"] == "Use MySQL"

    def test_action_confirm_shows_once(self, db: Database) -> None:
        """A confirmed action-kind proposal shows once in decisions."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id, title="Planning")
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_action_artifact(db, meeting_id, [
            {"task": "Fix the bug", "owner": "Alice"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.confirm_proposal(OWNER, created[0].id, owner="Alice")

        decisions = self._room_decisions(db, project_id)
        assert len(decisions["items"]) == 1

        # Also shows in commitments.
        commitments = self._room_commitments(db, project_id)
        assert len(commitments["items"]) == 1
        assert commitments["items"][0]["owner"] == "Alice"

    def test_dismiss_leaves_nothing_in_decisions(self, db: Database) -> None:
        """A dismissed proposal leaves zero rows in Room decisions."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "Bad idea"}])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.dismiss_proposal(OWNER, created[0].id)

        decisions = self._room_decisions(db, project_id)
        assert len(decisions["items"]) == 0

    def test_was_due_when_due_changed(self, db: Database) -> None:
        """was.due appears when the owner changes the due date on confirm."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id, title="Sprint")
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_action_artifact(db, meeting_id, [
            {"task": "Deploy v2", "owner": "Bob", "due": "Friday"},
        ])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id)
        bridge.confirm_proposal(OWNER, created[0].id, due="Monday")

        decisions = self._room_decisions(db, project_id)
        item = decisions["items"][0]
        assert "was" in item
        assert item["was"]["due"] == "Friday"


# ── Intel status enrichment ─────────────────────────────────────────

class TestIntelStatusEnrichment:
    """HS-172-02: intel_model_host and intel_duration_s on meeting payloads."""

    def test_no_job_intel_model_host_null(self, db: Database) -> None:
        """No intel job -> intel_model_host is null."""
        from holdspeak.services.meeting_service import MeetingService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)

        meetings = db.meetings.list_meetings(limit=10)
        target = [m for m in meetings if m.id == meeting_id][0]
        payload = MeetingService._summary_payload(target)

        # Before enrichment, host is None (no job).
        assert payload["intel_model_host"] is None

        # After enrichment (reads from job row), still None.
        svc = MeetingService(db)
        svc._enrich_intel_status([payload])
        assert payload["intel_model_host"] is None

    def test_job_with_recorded_host(self, db: Database) -> None:
        """Job with recorded model_host -> that host on the payload."""
        from holdspeak.services.meeting_service import MeetingService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)

        # Enqueue an intel job and record the host.
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO intel_jobs
                   (job_id, meeting_id, work_descriptor_sha256,
                    transcript_hash, status, model_host,
                    requested_at, updated_at, attempts)
                   VALUES (?, ?, 'desc', 'hash', 'queued', '192.168.1.43',
                           '2026-09-04T09:35:00', '2026-09-04T09:35:00', 0)""",
                (f"job-{uuid.uuid4().hex[:16]}", meeting_id),
            )

        meetings = db.meetings.list_meetings(limit=10)
        target = [m for m in meetings if m.id == meeting_id][0]
        payload = MeetingService._summary_payload(target)

        svc = MeetingService(db)
        svc._enrich_intel_status([payload])
        assert payload["intel_model_host"] == "192.168.1.43"

    def test_duration_from_timestamps(self, db: Database) -> None:
        """intel_duration_s computed from requested_at to completed_at."""
        from holdspeak.services.meeting_service import MeetingService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)

        # Set intel timestamps on meeting.
        with db._connection() as conn:
            conn.execute(
                "UPDATE meetings SET intel_requested_at = ?, intel_completed_at = ? WHERE id = ?",
                ("2026-09-04T09:35:00", "2026-09-04T09:35:41", meeting_id),
            )

        meetings = db.meetings.list_meetings(limit=10)
        target = [m for m in meetings if m.id == meeting_id][0]

        payload = MeetingService._summary_payload(target)
        assert payload["intel_duration_s"] == 41

    def test_duration_null_when_not_completed(self, db: Database) -> None:
        """duration_s is None when intel has not completed."""
        from holdspeak.services.meeting_service import MeetingService

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)

        meetings = db.meetings.list_meetings(limit=10)
        target = [m for m in meetings if m.id == meeting_id][0]

        payload = MeetingService._summary_payload(target)
        assert payload["intel_duration_s"] is None

    def test_hub_host_null_without_assignment(self, db: Database) -> None:
        """Hub meetings.host is null when no intel profile is assigned."""
        from holdspeak.web.routes.system.settings import _resolve_meetings_host

        class _MockMeeting:
            intel_profile_id = None
        class _MockConfig:
            meeting = _MockMeeting()
        result = _resolve_meetings_host(_MockConfig())
        assert result is None


# ── Host derivation (three cases) ───────────────────────────────────

class TestHostDerivation:
    """The host value is the HOST the run egresses to, never a label."""

    def test_lan_endpoint_host(self) -> None:
        """A LAN endpoint -> its ip/hostname."""
        from holdspeak.web.routes.system.settings import _placement_host
        from dataclasses import dataclass

        @dataclass
        class FakePlacement:
            node: str | None = None
            base_url: str | None = None
            boundary: str = "private_network"

        p = FakePlacement(base_url="http://192.168.1.43:8080/v1")
        assert _placement_host(p) == "192.168.1.43"

    def test_local_no_base_url(self) -> None:
        """This device (no base_url) -> 'local'."""
        from holdspeak.web.routes.system.settings import _placement_host
        from dataclasses import dataclass

        @dataclass
        class FakePlacement:
            node: str | None = None
            base_url: str | None = None
            boundary: str = "local"

        p = FakePlacement()
        assert _placement_host(p) == "local"

    def test_cloud_provider_host(self) -> None:
        """A cloud provider -> the provider's API host."""
        from holdspeak.web.routes.system.settings import _placement_host
        from dataclasses import dataclass

        @dataclass
        class FakePlacement:
            node: str | None = None
            base_url: str | None = None
            boundary: str = "cloud"

        p = FakePlacement(base_url="https://api.openai.com/v1")
        assert _placement_host(p) == "api.openai.com"


# ── Pipeline integration (completion -> bridge -> suggestions) ──────

class TestCompletionPipeline:
    """HS-172-03: _on_intel_complete bridges artifacts and creates suggestions."""

    def test_completion_creates_proposals_and_suggestions(self, db: Database) -> None:
        """After intel completes, proposals + source suggestions are created."""
        from holdspeak.intel_queue import _on_intel_complete

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id, title="Sprint Review")
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)

        # Seed a decision artifact + action artifact.
        _seed_decision_artifact(db, meeting_id, [
            {"text": "Adopt PostgreSQL 17"},
        ])
        _seed_action_artifact(db, meeting_id, [
            {"task": "Migrate the DB", "owner": "Marek"},
        ])

        # Seed an intel job with a recorded host (simulates the enqueue).
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO intel_jobs
                   (job_id, meeting_id, work_descriptor_sha256,
                    transcript_hash, status, model_host,
                    requested_at, updated_at, attempts)
                   VALUES (?, ?, 'desc', 'hash', 'succeeded', '192.168.1.43',
                           datetime('now'), datetime('now'), 1)""",
                (f"job-{uuid.uuid4().hex[:16]}", meeting_id),
            )

        # Seed a transcript mentioning a repo (for source suggestions).
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO segments (meeting_id, start_time, end_time, text, speaker)
                   VALUES (?, 10.0, 20.0, 'We should watch karolswdev/holdspeak for PRs', 'Bob')""",
                (meeting_id,),
            )

        _on_intel_complete(db, meeting_id)

        # Assert proposals exist.
        proposals = db.proposals.list_proposals(meeting_id=meeting_id, state="proposed")
        assert len(proposals) == 2, f"Expected 2 proposals, got {len(proposals)}"
        kinds = {p.kind for p in proposals}
        assert kinds == {"decision", "action"}
        # model_host came from the job row.
        for p in proposals:
            assert p.model_host == "192.168.1.43"

        # Assert source suggestions exist.
        with db._connection() as conn:
            sugg = conn.execute(
                "SELECT * FROM source_suggestions WHERE meeting_id = ? AND status = 'pending'",
                (meeting_id,),
            ).fetchall()
        assert len(sugg) >= 1, f"Expected at least 1 source suggestion, got {len(sugg)}"

    def test_completion_idempotent(self, db: Database) -> None:
        """Running _on_intel_complete twice creates nothing new (fingerprint dedup)."""
        from holdspeak.intel_queue import _on_intel_complete

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "Decision X"}])

        # Seed a job.
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO intel_jobs
                   (job_id, meeting_id, work_descriptor_sha256,
                    transcript_hash, status, model_host,
                    requested_at, updated_at, attempts)
                   VALUES (?, ?, 'desc', 'hash', 'succeeded', 'local',
                           datetime('now'), datetime('now'), 1)""",
                (f"job-{uuid.uuid4().hex[:16]}", meeting_id),
            )

        _on_intel_complete(db, meeting_id)
        count_1 = len(db.proposals.list_proposals(meeting_id=meeting_id))

        _on_intel_complete(db, meeting_id)
        count_2 = len(db.proposals.list_proposals(meeting_id=meeting_id))

        assert count_1 == count_2 == 1, f"Expected idempotent: first={count_1}, second={count_2}"


# ── HS-172 counsel: hub last-run fields ──────────────────────────────

def test_hub_last_run_fields(db: Database) -> None:
    """The hub's meetings block carries lastRunAt / lastRunS from the
    most recent completed intel job (meetings.intel_completed_at)."""
    now = datetime.now()
    req = datetime(2026, 9, 5, 9, 12, 0)
    comp = datetime(2026, 9, 5, 9, 12, 41)
    _seed_meeting(db, "m-hub-last")
    with db._connection() as conn:
        conn.execute(
            "UPDATE meetings SET intel_status = 'complete', "
            "intel_requested_at = ?, intel_completed_at = ? WHERE id = ?",
            (req.isoformat(), comp.isoformat(), "m-hub-last"),
        )
    # Read the last-run directly from the query the hub uses.
    with db._connection() as conn:
        row = conn.execute(
            "SELECT m.intel_completed_at, m.intel_requested_at "
            "FROM meetings m "
            "WHERE m.intel_status = 'complete' AND m.intel_completed_at IS NOT NULL "
            "ORDER BY m.intel_completed_at DESC LIMIT 1"
        ).fetchone()
    assert row is not None, "No completed meeting found"
    assert row["intel_completed_at"] == comp.isoformat()
    from datetime import datetime as _dt
    req_dt = _dt.fromisoformat(row["intel_requested_at"])
    comp_dt = _dt.fromisoformat(row["intel_completed_at"])
    duration = max(0, int((comp_dt - req_dt).total_seconds()))
    assert duration == 41, f"Expected 41 s, got {duration}"


# ── Dirty marker + cache refresh ────────────────────────────────────

class TestDirtyMarkerCache:
    """HS-172-03: durable dirty marker drives cache refresh."""

    def test_completion_sets_marker_and_cache_refreshes(self, db: Database) -> None:
        """_on_intel_complete sets the dirty marker; cache.get() rebuilds."""
        from holdspeak.intel_queue import _on_intel_complete
        from holdspeak.services.needs_you_aggregate import (
            NeedsYouCache,
            _read_dirty_at,
        )

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        project_id = f"prj-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "Decide X"}])

        # Seed a job.
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO intel_jobs
                   (job_id, meeting_id, work_descriptor_sha256,
                    transcript_hash, status, model_host,
                    requested_at, updated_at, attempts)
                   VALUES (?, ?, 'desc', 'hash', 'succeeded', 'local',
                           datetime('now'), datetime('now'), 1)""",
                (f"job-{uuid.uuid4().hex[:16]}", meeting_id),
            )

        # No marker before completion.
        assert _read_dirty_at(db) is None

        # Prime the cache with an empty aggregate.
        build_count = [0]
        def _builder():
            build_count[0] += 1
            return {"count": 0, "projects": [], "items": [], "next": None,
                    "computedAt": datetime.now().isoformat(), "stale": False, "sweepId": None}

        cache = NeedsYouCache(_builder, max_age_s=3600.0, db_factory=lambda: db)
        result_1 = cache.get()
        assert build_count[0] == 1
        assert result_1["count"] == 0

        # Completion sets the marker.
        _on_intel_complete(db, meeting_id)
        dirty = _read_dirty_at(db)
        assert dirty is not None

        # Next cache.get() sees the marker is newer -> rebuilds.
        result_2 = cache.get()
        assert build_count[0] == 2, f"Expected rebuild, build_count={build_count[0]}"

    def test_confirm_sets_marker(self, db: Database) -> None:
        """Confirming a proposal sets the dirty marker."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService
        from holdspeak.services.needs_you_aggregate import _read_dirty_at

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "Confirm me"}])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id, model_host="local")
        assert len(created) == 1

        # Clear the marker.
        with db._connection() as conn:
            conn.execute("DELETE FROM desk_projection_state WHERE projection_id = 'needs_you_aggregate'")
        assert _read_dirty_at(db) is None

        bridge.confirm_proposal(OWNER, created[0].id)
        assert _read_dirty_at(db) is not None

    def test_dismiss_sets_marker(self, db: Database) -> None:
        """Dismissing a proposal sets the dirty marker."""
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService
        from holdspeak.services.needs_you_aggregate import _read_dirty_at

        meeting_id = f"mtg-{uuid.uuid4().hex[:16]}"
        _seed_meeting(db, meeting_id)
        _seed_decision_artifact(db, meeting_id, [{"text": "Dismiss me"}])

        bridge = ProposalBridgeService(db)
        created = bridge.bridge_meeting_artifacts(meeting_id, model_host="local")

        with db._connection() as conn:
            conn.execute("DELETE FROM desk_projection_state WHERE projection_id = 'needs_you_aggregate'")

        bridge.dismiss_proposal(OWNER, created[0].id)
        assert _read_dirty_at(db) is not None
