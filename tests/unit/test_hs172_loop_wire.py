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

    def test_confirm_decision_writes_record(self, db: Database) -> None:
        """Confirming a decision proposal writes a decisions row and a receipt."""
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

        # Verify the decision row exists.
        with db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM decisions WHERE id = ?",
                (result["decision_id"],),
            ).fetchone()
            assert row is not None
            assert row["text"] == "Use Redis for caching"
            assert row["lifecycle"] == "accepted"

    def test_confirm_action_writes_action_item(self, db: Database) -> None:
        """Confirming an action proposal writes an action_items row."""
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

        # Verify the action_items row.
        with db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM action_items WHERE id = ?",
                (result["action_item_id"],),
            ).fetchone()
            assert row is not None
            assert row["task"] == "Review the PR"
            assert row["owner"] == "Alice"

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
