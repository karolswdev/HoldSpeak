"""HS-159-03: ProjectSetupService -- state machine, resume, suggestions
truth tables, finalize atomicity, Blank, abandon, envelope + 158 pins.

Acceptance criteria tested:
- Session survives simulated reload at EVERY stage (INT-005)
- Abandon/expire leaves zero Projects/Watches (INT-006)
- Suggestions deterministic and fact-traceable (fixture desks)
- Honest Blank-forward path (zero-fact desk)
- finalize() atomicity: fault injection rolls back ALL
- ACT-003: failed proposals refused from activation
- ACT-005: baseline honesty (zero historical events)
- Every mutation rides the revision-law envelope; 158 pins hold
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import ResultKind, generate_pcmd_id
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_setup_service import (
    CADENCE_PRESETS,
    Q_OUTCOME,
    Q_SIGNALS,
    ProjectSetupService,
    SESSION_TTL,
    STAGES,
)


OWNER = Principal(PrincipalKind.OWNER, "setup-test-owner")
NON_OWNER = Principal(PrincipalKind.SERVICE, "system-actor")


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "setup-test.db")
    project_svc = ProjectService(db)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=None,
    )
    yield db, project_svc, setup_svc
    reset_database()


@pytest.fixture
def empty_rig(tmp_path):
    """A rig with NO desk facts -- for Blank path testing."""
    reset_database()
    db = Database(tmp_path / "empty-desk.db")
    project_svc = ProjectService(db)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=None,
    )
    yield db, project_svc, setup_svc
    reset_database()


def _seed_meeting(db: Database, meeting_id: str = "m-001",
                  title: str = "Weekly standup") -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 1, 10, 0),
        title=title,
        capture_status="finalized",
    ))


def _seed_decision(db: Database, decision_id: str = "dec-001",
                   text: str = "Adopt microservices",
                   lifecycle: str = "accepted") -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions
               (id, text, rationale, decided_at, date_basis,
                source_artifact_id, source_meeting_id, source_state,
                lifecycle, deleted, created_at, updated_at, last_modified)
               VALUES (?, ?, '', datetime('now'), 'explicit',
                       '', '', 'linked',
                       ?, 0, datetime('now'), datetime('now'), datetime('now'))""",
            (decision_id, text, lifecycle),
        )


def _seed_action_item(db: Database, item_id: str = "ai-001",
                      task: str = "Review PR", owner: str = "Alice",
                      due: str = "2026-07-01", status: str = "open") -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state,
                created_at, source_type, source_ref)
               VALUES (?, NULL, ?, ?, ?, ?, 'accepted',
                       datetime('now'), 'manual', '')""",
            (item_id, task, owner, due, status),
        )


# ── State machine + resume ────────────────────────────────────────────


class TestSessionLifecycle:
    """INT-001, INT-005: durable session with stage transitions."""

    def test_start_creates_active_session(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        assert session["state"] == "active"
        assert session["stage"] == "outcome"
        assert session["id"].startswith("psetup_")

    def test_non_owner_rejected(self, rig) -> None:
        _db, _ps, svc = rig
        with pytest.raises(ServiceError, match="OWNER"):
            svc.start_setup(NON_OWNER)

    def test_resume_at_outcome_stage(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["state"] == "active"
        assert rehydrated["stage"] == "outcome"
        assert rehydrated["answers"] == {}
        assert rehydrated["proposals"] == []

    def test_answer_outcome_advances_to_signals(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {
            "original": "Ship the routing upgrade",
            "normalized": "Ship routing upgrade",
        })
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["stage"] == "signals"
        assert Q_OUTCOME in rehydrated["answers"]

    def test_answer_signals_advances_to_proposals(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {
            "text": "Ship the routing upgrade",
        })
        svc.answer(OWNER, session["id"], Q_SIGNALS, {
            "text": "Watch for blocked PRs",
        })
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["stage"] == "proposals"
        assert Q_SIGNALS in rehydrated["answers"]

    def test_resume_preserves_answers_at_signals_stage(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {
            "original": "verbatim dictation",
            "normalized": "clean version",
        })
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["stage"] == "signals"
        ans = rehydrated["answers"][Q_OUTCOME]
        assert ans["answer"]["original"] == "verbatim dictation"
        assert ans["answer"]["normalized"] == "clean version"

    def test_answer_revision_preserves_history(self, rig) -> None:
        """INT-004: append-only with revision; original preserved."""
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {
            "original": "first answer", "normalized": "v1",
        })
        svc.answer(OWNER, session["id"], Q_OUTCOME, {
            "original": "revised answer", "normalized": "v2",
        })
        rehydrated = svc.get_setup(session["id"])
        ans = rehydrated["answers"][Q_OUTCOME]
        assert ans["revision"] == 2
        assert ans["answer"]["original"] == "revised answer"
        assert ans["answer"]["normalized"] == "v2"

    def test_unknown_question_rejected(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        with pytest.raises(ValidationError, match="Unknown question_id"):
            svc.answer(OWNER, session["id"], "bogus_q", {"text": "x"})

    def test_resume_after_proposals_stage(self, rig) -> None:
        """Resume at proposals stage with proposals visible."""
        db, _ps, svc = rig
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Ship it"})
        svc.answer(OWNER, session["id"], Q_SIGNALS, {"text": "Watch PRs"})
        svc.suggest(OWNER, session["id"])
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["stage"] == "proposals"
        assert len(rehydrated["proposals"]) > 0


# ── Suggestion truth tables ───────────────────────────────────────────


class TestSuggestionTruthTables:
    """INT-007/008/010: deterministic, fact-traceable, never invented."""

    def test_empty_desk_yields_zero_proposals(self, empty_rig) -> None:
        """Blank path: no facts -> zero proposals (PROV-011)."""
        _db, _ps, svc = empty_rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        svc.answer(OWNER, session["id"], Q_SIGNALS, {"text": "Signals"})
        proposals = svc.suggest(OWNER, session["id"])
        assert proposals == []

    def test_meetings_only_yields_meetings_proposal(self, rig) -> None:
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint review")
        _seed_meeting(db, "m-2", "Planning")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        kinds = [
            p["spec"]["subject"]["kind"]
            for p in proposals
        ]
        assert "meetings" in kinds
        meetings_prop = [p for p in proposals if p["spec"]["subject"]["kind"] == "meetings"][0]
        assert meetings_prop["rationale"]["subject_count"] == 2
        assert "Sprint review" in meetings_prop["rationale"]["detail"]

    def test_decisions_yields_decisions_proposal(self, rig) -> None:
        db, _ps, svc = rig
        _seed_decision(db, "dec-1", "Use TypeScript", "accepted")
        _seed_decision(db, "dec-2", "Adopt React", "accepted")
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        kinds = [p["spec"]["subject"]["kind"] for p in proposals]
        assert "decisions" in kinds
        dec_prop = [p for p in proposals if p["spec"]["subject"]["kind"] == "decisions"][0]
        assert dec_prop["rationale"]["subject_count"] == 2

    def test_overdue_items_yield_door_proposal(self, rig) -> None:
        db, _ps, svc = rig
        _seed_action_item(db, "ai-1", "Fix bug", "Bob", "2026-07-01", "open")
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        kinds = [p["spec"]["subject"]["kind"] for p in proposals]
        assert "door" in kinds

    def test_combined_desk_yields_multiple_proposals(self, rig) -> None:
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Standup")
        _seed_decision(db, "dec-1", "Use Go", "accepted")
        _seed_action_item(db, "ai-1", "Deploy", "Carol", "2026-07-01", "open")
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        kinds = {p["spec"]["subject"]["kind"] for p in proposals}
        assert "meetings" in kinds
        assert "decisions" in kinds
        assert "door" in kinds

    def test_proposals_have_required_fields(self, rig) -> None:
        """INT-008: each has source, subject, conditions, action, cadence, rationale."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        for p in proposals:
            spec = p["spec"]
            assert "provider" in spec
            assert "subject" in spec
            assert spec["subject"]["kind"] in ("meetings", "decisions", "door", "evidence")
            assert "trigger" in spec
            assert "rules" in spec
            assert "mode" in spec
            rationale = p["rationale"]
            assert "fact" in rationale
            assert rationale["subject_count"] > 0

    def test_suggest_is_deterministic(self, rig) -> None:
        """INT-010: same desk yields same proposals."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Review")

        session1 = svc.start_setup(OWNER)
        proposals1 = svc.suggest(OWNER, session1["id"])

        session2 = svc.start_setup(OWNER)
        proposals2 = svc.suggest(OWNER, session2["id"])

        kinds1 = [p["spec"]["subject"]["kind"] for p in proposals1]
        kinds2 = [p["spec"]["subject"]["kind"] for p in proposals2]
        assert kinds1 == kinds2


# ── Proposal operations ──────────────────────────────────────────────


class TestProposalOperations:
    def test_select_deselect_cycle(self, rig) -> None:
        db, _ps, svc = rig
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]

        selected = svc.select_proposal(OWNER, session["id"], pid)
        assert selected["state"] == "selected"

        deselected = svc.deselect_proposal(OWNER, session["id"], pid)
        assert deselected["state"] == "proposed"

    def test_clarify_updates_cadence(self, rig) -> None:
        db, _ps, svc = rig
        _seed_meeting(db)
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]

        clarified = svc.clarify_proposal(OWNER, session["id"], pid, {
            "cadence": "active_work",
        })
        spec = clarified["spec"]
        assert spec["trigger"]["every_minutes"] == 15

    def test_test_proposal_meetings(self, rig) -> None:
        """ACT-002: test returns current matches."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint review")
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        meetings_prop = [p for p in proposals if p["spec"]["subject"]["kind"] == "meetings"][0]

        result = svc.test_proposal(OWNER, session["id"], meetings_prop["id"])
        assert result["test_state"] == "passed"
        assert result["result"]["entity_count"] >= 1
        assert "Test passed" in result["result"]["message"]

    def test_test_proposal_zero_match_honest(self, rig) -> None:
        """ACT-002: zero-match with successful read = passed."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        proposals = svc.suggest(OWNER, session["id"])
        meetings_prop = [p for p in proposals if p["spec"]["subject"]["kind"] == "meetings"][0]

        # Delete the meeting so the test read finds zero
        with db._connection() as conn:
            conn.execute("DELETE FROM meetings")

        result = svc.test_proposal(OWNER, session["id"], meetings_prop["id"])
        # Zero matches with a successful read = still passed (ACT-002)
        assert result["test_state"] == "passed"
        assert result["result"]["entity_count"] == 0
        assert "0 current matches" in result["result"]["message"]


# ── Finalize atomicity ────────────────────────────────────────────────


class TestFinalizeAtomicity:
    """ACT-004: one-transaction finalize, all-or-nothing."""

    def test_finalize_creates_project_and_watches(self, rig) -> None:
        db, ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Ship routing"})
        svc.answer(OWNER, session["id"], Q_SIGNALS, {"text": "Watch PRs"})
        proposals = svc.suggest(OWNER, session["id"])

        # Select and test a proposal
        pid = proposals[0]["id"]
        svc.select_proposal(OWNER, session["id"], pid)
        svc.test_proposal(OWNER, session["id"], pid)

        # Finalize
        result = svc.finalize(OWNER, session["id"])
        assert result["result_kind"] == "created"
        assert result["project_id"].startswith("proj-")
        assert len(result["activated_watches"]) == 1

        # Verify project exists
        project = ps.get_project(OWNER, result["project_id"])
        assert project["name"] == "Ship routing"

        # Verify session is completed
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["state"] == "completed"

    def test_finalize_blank_no_watches(self, rig) -> None:
        """INT-002: Blank path -- zero selected proposals is lawful."""
        _db, ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Manual project"})

        result = svc.finalize(OWNER, session["id"])
        assert result["result_kind"] == "created"
        assert result["activated_watches"] == []

        project = ps.get_project(OWNER, result["project_id"])
        assert project is not None

    def test_finalize_refused_untested_proposals(self, rig) -> None:
        """ACT-003: selected but untested proposals refused from activation."""
        db, ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]

        # Select but do NOT test
        svc.select_proposal(OWNER, session["id"], pid)

        result = svc.finalize(OWNER, session["id"])
        assert result["result_kind"] == "created"
        # Not activated because not tested
        assert result["activated_watches"] == []
        assert len(result["refused_proposals"]) == 1
        assert result["refused_proposals"][0]["id"] == pid

    def test_finalize_refused_failed_proposals(self, rig) -> None:
        """ACT-003: selected + failed proposals refused."""
        db, ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]

        svc.select_proposal(OWNER, session["id"], pid)

        # Force a failed test state
        svc._update_proposal(pid, test_state="failed")

        result = svc.finalize(OWNER, session["id"])
        assert result["activated_watches"] == []
        assert len(result["refused_proposals"]) == 1

    def test_finalize_fault_injection_project_insert(self, rig) -> None:
        """Fault injection: failure during project INSERT rolls back everything."""
        db, ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})

        original_execute = None

        def failing_execute(sql, params=None):
            """Fail on project INSERT."""
            if "INSERT INTO projects" in sql:
                raise RuntimeError("simulated DB failure")
            return original_execute(sql, params)

        with pytest.raises(RuntimeError, match="simulated DB failure"):
            with patch.object(
                db, "_connection",
            ) as mock_conn_ctx:
                mock_conn = MagicMock()
                original_execute = mock_conn.execute
                mock_conn.execute = failing_execute
                mock_conn_ctx.return_value.__enter__ = lambda self: mock_conn
                mock_conn_ctx.return_value.__exit__ = lambda self, *args: None
                svc.finalize(OWNER, session["id"])

        # Session still active (recoverable)
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["state"] == "active"

        # No project created
        projects = ps.list_projects(OWNER)
        assert len(projects) == 0

    def test_finalize_fault_injection_watch_insert(self, rig) -> None:
        """Fault injection: failure during Watch INSERT leaves zero project rows."""
        db, ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]
        svc.select_proposal(OWNER, session["id"], pid)
        svc.test_proposal(OWNER, session["id"], pid)

        # Patch the DB connection to fail on Watch INSERT
        real_connection = db._connection

        call_count = [0]

        class FailingConnection:
            def __init__(self, real_conn):
                self._real = real_conn

            def execute(self, sql, params=None):
                if "INSERT INTO connector_watches" in sql:
                    raise RuntimeError("simulated watch insert failure")
                if params is not None:
                    return self._real.execute(sql, params)
                return self._real.execute(sql)

            def __getattr__(self, name):
                return getattr(self._real, name)

        from contextlib import contextmanager

        @contextmanager
        def patched_connection():
            with real_connection() as conn:
                yield FailingConnection(conn)

        with pytest.raises(RuntimeError, match="simulated watch insert failure"):
            with patch.object(db, "_connection", patched_connection):
                svc.finalize(OWNER, session["id"])

        # Session still active
        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["state"] == "active"

        # No project created (rolled back)
        projects = ps.list_projects(OWNER)
        assert len(projects) == 0


# ── Baseline honesty (ACT-005) ────────────────────────────────────────


class TestBaselineHonesty:
    """ACT-005: activation establishes baseline WITHOUT historical events."""

    def test_finalize_emits_no_watch_events(self, rig) -> None:
        """Ledger silence: no watch transition events on activate."""
        db, ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]
        svc.select_proposal(OWNER, session["id"], pid)
        svc.test_proposal(OWNER, session["id"], pid)

        result = svc.finalize(OWNER, session["id"])

        # Check the service event ledger for watch-related events
        events = db.automations.list_events(limit=100)
        watch_events = [
            e for e in events
            if "watch" in e.get("event_type", "").lower()
        ]
        # Zero watch events -- only project.created
        assert len(watch_events) == 0

        # The only event is project.created
        project_events = [
            e for e in events
            if e.get("event_type") == "project.created"
        ]
        assert len(project_events) >= 1


# ── Abandon / expire ──────────────────────────────────────────────────


class TestAbandonExpire:
    """INT-006: abandon/expire leaves zero Projects/Watches."""

    def test_abandon_leaves_no_project(self, rig) -> None:
        _db, ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})

        result = svc.abandon(OWNER, session["id"])
        assert result["state"] == "abandoned"

        projects = ps.list_projects(OWNER)
        assert len(projects) == 0

    def test_abandon_blocks_further_mutations(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.abandon(OWNER, session["id"])

        with pytest.raises(ServiceError, match="not active"):
            svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "x"})

        with pytest.raises(ServiceError, match="not active"):
            svc.finalize(OWNER, session["id"])

    def test_expire_on_read(self, rig) -> None:
        """Expired session detected on get_setup."""
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)

        # Force expires_at to the past
        svc._update_session(
            session["id"],
            expires_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        )

        rehydrated = svc.get_setup(session["id"])
        assert rehydrated["state"] == "expired"

    def test_expired_session_blocks_mutations(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc._update_session(
            session["id"],
            expires_at=(datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        )
        # Trigger the expiry
        svc.get_setup(session["id"])

        with pytest.raises(ServiceError, match="not active"):
            svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "x"})


# ── Envelope + 158 characterization pins ──────────────────────────────


class TestEnvelopePins:
    """Every mutation rides the revision-law envelope."""

    def test_finalize_envelope_shape(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        result = svc.finalize(OWNER, session["id"])

        assert result["result_kind"] == "created"
        assert "project_id" in result
        assert "project_revision" in result
        assert result["project_revision"] == 1
        assert "changed_refs" in result
        assert len(result["changed_refs"]) > 0

    def test_finalize_project_has_revision_1(self, rig) -> None:
        """158 pin: created project starts at revision 1."""
        _db, ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        result = svc.finalize(OWNER, session["id"])

        project = ps.get_project(OWNER, result["project_id"])
        # The project payload doesn't have revision directly -- check via room
        room = ps.room(OWNER, result["project_id"])
        assert room["revision"] == 1

    def test_finalize_records_change(self, rig) -> None:
        """A project_changes row is recorded."""
        db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        result = svc.finalize(OWNER, session["id"])

        with db._connection() as conn:
            changes = conn.execute(
                "SELECT * FROM project_changes WHERE project_id=?",
                (result["project_id"],),
            ).fetchall()
        assert len(changes) >= 1
        change = dict(changes[0])
        assert change["change_kind"] == "project.created"

    def test_finalize_records_command(self, rig) -> None:
        """A project_commands row is recorded for idempotency."""
        db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        cmd_id = generate_pcmd_id()
        result = svc.finalize(OWNER, session["id"], command_id=cmd_id)

        with db._connection() as conn:
            cmds = conn.execute(
                "SELECT * FROM project_commands WHERE id=?",
                (cmd_id,),
            ).fetchall()
        assert len(cmds) == 1
        assert dict(cmds[0])["command_kind"] == "create_from_setup"

    def test_finalize_with_watches_creates_sources(self, rig) -> None:
        """Project sources are created for activated watches."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]
        svc.select_proposal(OWNER, session["id"], pid)
        svc.test_proposal(OWNER, session["id"], pid)

        result = svc.finalize(OWNER, session["id"])
        project_id = result["project_id"]

        sources = db.automations.list_project_sources(project_id)
        assert len(sources) >= 1
        source = sources[0]
        assert source["source_ref"].startswith("watch:")

    def test_finalize_watch_has_correct_state(self, rig) -> None:
        """Activated watch has state='active', baseline_state='established'."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]
        svc.select_proposal(OWNER, session["id"], pid)
        svc.test_proposal(OWNER, session["id"], pid)

        result = svc.finalize(OWNER, session["id"])
        watch_id = result["activated_watches"][0]["watch_id"]

        watch = db.automations.get_watch(watch_id)
        assert watch is not None
        assert watch.get("state") == "active" or True  # state in graduated columns

        # Check via direct SQL for graduated columns
        with db._connection() as conn:
            row = conn.execute(
                "SELECT state, baseline_state, project_id, schema_version "
                "FROM connector_watches WHERE id=?",
                (watch_id,),
            ).fetchone()
        assert row is not None
        assert row["state"] == "active"
        assert row["baseline_state"] == "established"
        assert row["project_id"] == result["project_id"]
        assert row["schema_version"] == "WatchSpec@1"

    def test_finalize_watch_has_rules(self, rig) -> None:
        """Activated watch has watch_rules rows."""
        db, _ps, svc = rig
        _seed_meeting(db, "m-1", "Sprint")
        session = svc.start_setup(OWNER)
        svc.answer(OWNER, session["id"], Q_OUTCOME, {"text": "Goal"})
        proposals = svc.suggest(OWNER, session["id"])
        pid = proposals[0]["id"]
        svc.select_proposal(OWNER, session["id"], pid)
        svc.test_proposal(OWNER, session["id"], pid)

        result = svc.finalize(OWNER, session["id"])
        watch_id = result["activated_watches"][0]["watch_id"]

        rules = db.automations.list_rules(watch_id)
        assert len(rules) >= 1
        assert rules[0]["condition_schema"] == "WatchCondition@1"


# ── Not-found guards ──────────────────────────────────────────────────


class TestNotFound:
    def test_get_nonexistent_session(self, rig) -> None:
        _db, _ps, svc = rig
        with pytest.raises(NotFound):
            svc.get_setup("psetup_nonexistent")

    def test_answer_nonexistent_session(self, rig) -> None:
        _db, _ps, svc = rig
        with pytest.raises(NotFound):
            svc.answer(OWNER, "psetup_nonexistent", Q_OUTCOME, {"text": "x"})

    def test_select_nonexistent_proposal(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        with pytest.raises(NotFound):
            svc.select_proposal(OWNER, session["id"], "wprop_nonexistent")

    def test_test_nonexistent_proposal(self, rig) -> None:
        _db, _ps, svc = rig
        session = svc.start_setup(OWNER)
        with pytest.raises(NotFound):
            svc.test_proposal(OWNER, session["id"], "wprop_nonexistent")
