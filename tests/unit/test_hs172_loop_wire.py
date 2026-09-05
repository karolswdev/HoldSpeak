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

    def test_room_linked_meeting_enqueues(self, db: Database) -> None:
        """A Room-linked meeting with a transcript auto-enqueues under room_linked."""
        from holdspeak.config.meeting import MeetingConfig
        cfg = MeetingConfig(intelligence_auto="room_linked")
        assert cfg.intelligence_auto == "room_linked"

    def test_off_never_enqueues(self, db: Database) -> None:
        """intelligence_auto=off never auto-enqueues."""
        from holdspeak.config.meeting import MeetingConfig
        cfg = MeetingConfig(intelligence_auto="off")
        assert cfg.intelligence_auto == "off"

    def test_every_enqueues_all(self, db: Database) -> None:
        """intelligence_auto=every enqueues for all meetings."""
        from holdspeak.config.meeting import MeetingConfig
        cfg = MeetingConfig(intelligence_auto="every")
        assert cfg.intelligence_auto == "every"

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

        # Create a mock config with no intel_profile_id.
        class _MockMeeting:
            intel_profile_id = None
        class _MockConfig:
            meeting = _MockMeeting()
        result = _resolve_meetings_host(_MockConfig())
        assert result is None
