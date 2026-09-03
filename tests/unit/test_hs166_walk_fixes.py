"""HS-166-05 unit tests for the four product fixes.

(a) Baseline: finalize populates snapshot_json; first evaluate_due = 0 transitions.
(b) Risk rule: due-risk transition -> risk_attention with severity; plain -> observation_attention.
(c) Composition: the web context's delta service can create items from decide_proposal.
(d) Watermark helper: find_run_by_watermark finds/misses correctly (Gate 4 drain helper).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-166-05")


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    _db = Database(tmp_path / "test-166-05.db")
    yield _db
    _db.close()
    reset_database()


# ── (a) Baseline: finalize populates snapshot_json ──────────────────


class TestBaselinePopulation:
    """After finalize, the watch's snapshot_json is non-empty and the
    first evaluate_due yields 0 transitions / 0 effects."""

    def _setup_rig(self, db: Any):
        from holdspeak.meeting_session.models import MeetingState
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService
        from holdspeak.services.watch_service import WatchService

        db.meetings.save_meeting(MeetingState(
            id="m-baseline-test",
            started_at=datetime(2026, 8, 20, 10, 0),
            title="Sprint Review",
            capture_status="finalized",
        ))

        # Fake fetcher that returns canned entities
        def fake_fetcher(principal, *, connector_id, query_kind, query):
            return [
                {"key": "ITEM-1", "title": "Test Item", "status": "Open",
                 "due_at": "2026-09-10", "updated_at": "2026-09-01T00:00:00Z"},
            ]

        watch_svc = WatchService(db, snapshot_fetcher=fake_fetcher)
        project_svc = ProjectService(db)
        setup_svc = ProjectSetupService(
            db,
            project_service=project_svc,
            watch_service=watch_svc,
        )
        return project_svc, setup_svc, watch_svc

    def test_finalize_populates_snapshot_json(self, db: Any) -> None:
        """After finalize, snapshot_json is non-empty on every activated watch."""
        project_svc, setup_svc, watch_svc = self._setup_rig(db)

        # Create a setup session with a native proposal
        session = setup_svc.start_setup(OWNER)
        sid = session["id"]
        setup_svc.answer(OWNER, sid, "outcome", {"text": "Test project"})
        setup_svc.answer(OWNER, sid, "signals", {"text": "Test signals"})
        proposals = setup_svc.suggest(OWNER, sid)
        assert len(proposals) >= 1, "Need at least 1 proposal"

        # Select the first proposal
        pid = proposals[0]["id"]
        setup_svc.select_proposal(OWNER, sid, pid)

        # Test the proposal
        setup_svc.test_proposal(OWNER, sid, pid)

        # Finalize
        result = setup_svc.finalize(OWNER, sid)
        activated = result.get("activated_watches", [])
        assert len(activated) >= 1

        # Check snapshot_json is populated
        for aw in activated:
            wid = aw["watch_id"]
            watch = db.automations.get_watch(wid)
            snapshot = watch.get("snapshot", {})
            assert snapshot and snapshot != {}, (
                f"Watch {wid} snapshot should be non-empty after finalize, "
                f"got {snapshot}"
            )

    def test_first_evaluate_due_zero_transitions(self, db: Any) -> None:
        """First evaluate_due after finalize yields 0 transitions, 0 effects."""
        project_svc, setup_svc, watch_svc = self._setup_rig(db)

        session = setup_svc.start_setup(OWNER)
        sid = session["id"]
        setup_svc.answer(OWNER, sid, "outcome", {"text": "Test project"})
        setup_svc.answer(OWNER, sid, "signals", {"text": "Test signals"})
        proposals = setup_svc.suggest(OWNER, sid)
        pid = proposals[0]["id"]
        setup_svc.select_proposal(OWNER, sid, pid)
        setup_svc.test_proposal(OWNER, sid, pid)
        result = setup_svc.finalize(OWNER, sid)

        activated = result.get("activated_watches", [])
        assert len(activated) >= 1
        watch_id = activated[0]["watch_id"]

        # Make the watch due
        past = (datetime.now() - timedelta(minutes=5)).isoformat()
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
                (past, watch_id),
            )

        # Run evaluate_due
        outcomes = watch_svc.evaluate_due(OWNER)

        # Count transitions and effects
        total_transitions = sum(o.get("transitions", 0) for o in outcomes)
        effects_count = 0
        with db._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM watch_effects").fetchone()
            effects_count = row[0] if row else 0

        assert total_transitions == 0, (
            f"First evaluate should see 0 transitions (baseline populated), "
            f"got {total_transitions}"
        )
        assert effects_count == 0, (
            f"First evaluate should produce 0 effects, got {effects_count}"
        )

    def test_fetch_failure_sets_pending(self, db: Any) -> None:
        """If the baseline fetch fails, baseline_state becomes 'pending'."""
        from holdspeak.meeting_session.models import MeetingState
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService
        from holdspeak.services.watch_service import WatchService

        db.meetings.save_meeting(MeetingState(
            id="m-fetch-fail",
            started_at=datetime(2026, 8, 20, 10, 0),
            title="Sprint Review",
            capture_status="finalized",
        ))

        # Fetcher that fails
        def failing_fetcher(principal, *, connector_id, query_kind, query):
            raise RuntimeError("Fetch failed")

        watch_svc = WatchService(db, snapshot_fetcher=failing_fetcher)
        project_svc = ProjectService(db)
        setup_svc = ProjectSetupService(
            db,
            project_service=project_svc,
            watch_service=watch_svc,
        )

        session = setup_svc.start_setup(OWNER)
        sid = session["id"]
        setup_svc.answer(OWNER, sid, "outcome", {"text": "Test"})
        setup_svc.answer(OWNER, sid, "signals", {"text": "Signals"})
        proposals = setup_svc.suggest(OWNER, sid)
        if not proposals:
            pytest.skip("No proposals generated")
        pid = proposals[0]["id"]
        setup_svc.select_proposal(OWNER, sid, pid)
        setup_svc.test_proposal(OWNER, sid, pid)
        result = setup_svc.finalize(OWNER, sid)

        activated = result.get("activated_watches", [])
        if activated:
            wid = activated[0]["watch_id"]
            watch = db.automations.get_watch(wid)
            assert watch.get("baseline_state") == "pending", (
                f"Fetch failure should set baseline_state='pending', "
                f"got {watch.get('baseline_state')}"
            )


# ── (b) Risk rule: condition-matcher-based classification ───────────


class TestRiskRule:
    """A due-risk transition -> risk_attention; plain -> observation_attention."""

    def test_due_risk_transition_yields_risk_attention(self, db: Any) -> None:
        """A status_changed transition on a watch with due_within_days clause
        produces a risk_attention proposal with severity."""
        from holdspeak.services.project_delta_service import (
            _resolve_watch_transition_rule,
        )

        # Create a watch with a due_risk rule
        watch_id = "cw_risk_test_001"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO connector_watches
                   (id, connector_id, query_kind, name, query_json, enabled,
                    state, revision, baseline_state)
                   VALUES (?, ?, ?, ?, ?, 1, 'active', 1, 'established')""",
                (watch_id, "jira", "issues", "Due risk watch",
                 json.dumps({"due_within_days": 7})),
            )
            conn.execute(
                """INSERT INTO watch_rules
                   (id, watch_id, ordinal, condition_schema, condition_json,
                    action_schema, action_json, enabled, revision)
                   VALUES (?, ?, 0, 'WatchCondition@1', ?,
                           'WatchAction@1', ?, 1, 0)""",
                ("wrule_risk_001", watch_id,
                 json.dumps({
                     "schema": "WatchCondition@1",
                     "operator": "any",
                     "clauses": [
                         {"field": "due_at", "comparison": "due_within_days",
                          "value": 7},
                         {"field": "due_at", "comparison": "overdue"},
                     ],
                 }),
                 json.dumps([{"schema": "WatchAction@1",
                              "kind": "project.steward.run_once"}])),
            )

        obs = {
            "observation_kind": "watch.transition",
            "source_id": f"watch:{watch_id}",
            "fact_json": json.dumps({
                "event_type": "jira.issue.status_changed",
                "entity_ref": "KAN-1",
                "changed": {"status": ["In Progress", "Done"]},
            }),
        }

        rule, severity = _resolve_watch_transition_rule(obs, db=db)
        assert rule.proposal_kind == "risk_attention", (
            f"Due-risk watch transition should produce risk_attention, "
            f"got {rule.proposal_kind}"
        )
        assert severity is not None, "Severity should be set"

    def test_plain_transition_yields_observation_attention(self, db: Any) -> None:
        """A watch with no risk-class clauses -> observation_attention."""
        from holdspeak.services.project_delta_service import (
            _resolve_watch_transition_rule,
        )

        watch_id = "cw_plain_test_001"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO connector_watches
                   (id, connector_id, query_kind, name, query_json, enabled,
                    state, revision, baseline_state)
                   VALUES (?, ?, ?, ?, ?, 1, 'active', 1, 'established')""",
                (watch_id, "jira", "issues", "Plain watch", "{}"),
            )
            conn.execute(
                """INSERT INTO watch_rules
                   (id, watch_id, ordinal, condition_schema, condition_json,
                    action_schema, action_json, enabled, revision)
                   VALUES (?, ?, 0, 'WatchCondition@1', ?,
                           'WatchAction@1', ?, 1, 0)""",
                ("wrule_plain_001", watch_id,
                 json.dumps({
                     "schema": "WatchCondition@1",
                     "operator": "any",
                     "clauses": [
                         {"field": "assignee", "comparison": "changed"},
                     ],
                 }),
                 json.dumps([{"schema": "WatchAction@1",
                              "kind": "project.observe"}])),
            )

        obs = {
            "observation_kind": "watch.transition",
            "source_id": f"watch:{watch_id}",
            "fact_json": json.dumps({
                "event_type": "jira.issue.assigned",
                "entity_ref": "KAN-2",
                "changed": {"assignee": ["", "alice"]},
            }),
        }

        rule, severity = _resolve_watch_transition_rule(obs, db=db)
        assert rule.proposal_kind == "observation_attention", (
            f"Plain watch transition should produce observation_attention, "
            f"got {rule.proposal_kind}"
        )
        assert severity is None

    def test_determinism_x2(self, db: Any) -> None:
        """Same input twice -> same output (DEL-007)."""
        from holdspeak.services.project_delta_service import (
            _resolve_watch_transition_rule,
        )

        watch_id = "cw_determ_001"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO connector_watches
                   (id, connector_id, query_kind, name, query_json, enabled,
                    state, revision, baseline_state)
                   VALUES (?, ?, ?, ?, ?, 1, 'active', 1, 'established')""",
                (watch_id, "jira", "issues", "Determ watch", "{}"),
            )
            conn.execute(
                """INSERT INTO watch_rules
                   (id, watch_id, ordinal, condition_schema, condition_json,
                    action_schema, action_json, enabled, revision)
                   VALUES (?, ?, 0, 'WatchCondition@1', ?,
                           'WatchAction@1', ?, 1, 0)""",
                ("wrule_det_001", watch_id,
                 json.dumps({
                     "operator": "any",
                     "clauses": [
                         {"field": "due_at", "comparison": "overdue"},
                     ],
                 }),
                 json.dumps([{"kind": "project.steward.run_once"}])),
            )

        obs = {
            "observation_kind": "watch.transition",
            "source_id": f"watch:{watch_id}",
            "fact_json": json.dumps({
                "event_type": "jira.issue.due_changed",
                "entity_ref": "KAN-3",
                "changed": {"due_at": ["2026-09-15", "2026-09-01"]},
            }),
        }

        r1, s1 = _resolve_watch_transition_rule(obs, db=db)
        r2, s2 = _resolve_watch_transition_rule(obs, db=db)
        assert r1.proposal_kind == r2.proposal_kind
        assert s1 == s2


# ── (c) Composition: delta service can create items ─────────────────


class TestDeltaComposition:
    """The delta service with an attached project_service can create
    items from decide_proposal (the exact defect that hid item creation)."""

    def test_risk_attention_accept_creates_item(self, db: Any) -> None:
        """Accepting a risk_attention proposal creates a project item."""
        from holdspeak.services.project_delta_service import ProjectDeltaService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_service import ProjectService

        project_svc = ProjectService(db)
        delta_svc = ProjectDeltaService(
            db, collector=ProjectEvidenceCollector(db),
        )
        delta_svc.attach_project_service(project_svc)

        # Create a project
        project = project_svc.create_project(OWNER, {"name": "Test composition"})
        project_id = project["project_id"]

        # Insert an observation and proposal manually
        now = datetime.now(timezone.utc).isoformat()
        from holdspeak.project_contracts import generate_prev_id, generate_pprop_id
        review_id = generate_prev_id()

        with db._connection() as conn:
            db.project_observations.insert_review_in_transaction(
                conn,
                review_id=review_id,
                project_id=project_id,
                from_sequence=0,
                through_sequence=1,
                source_manifest_json="{}",
                project_revision_opened=1,
                opened_at=now,
                summary_json="{}",
            )
            proposal_id = generate_pprop_id(
                project_id=project_id,
                review_window_key=review_id,
                proposal_kind="risk_attention",
                target_ref=f"watch:test_watch",
                normalized_patch="{}",
            )
            db.project_observations.insert_proposal_in_transaction(
                conn,
                proposal_id=proposal_id,
                project_id=project_id,
                review_window_key=review_id,
                proposal_kind="risk_attention",
                target_ref="watch:test_watch",
                title="KAN-1 status In Progress -> Done",
                rationale="Risk-bearing transition",
                patch_json=json.dumps({
                    "event_type": "jira.issue.status_changed",
                    "entity_ref": "KAN-1",
                    "changed": {"status": ["In Progress", "Done"]},
                    "severity": "medium",
                    "item_type": "dependency",
                    "lifecycle": "at_risk",
                    "title": "KAN-1 status In Progress -> Done",
                }),
                materiality="0.55",
                lifecycle="open",
            )

        # Accept the proposal
        result = delta_svc.decide_proposal(
            OWNER, project_id, proposal_id, "accept",
        )

        assert result.get("item_id"), (
            f"Accepting risk_attention should create an item, got {result}"
        )

        # Verify the item exists
        items = project_svc.list_items(OWNER, project_id)
        assert len(items.get("items", [])) >= 1, (
            f"Project should have at least 1 item after accept"
        )


# ── (d) Watermark dedup ────────────────────────────────────────────


class TestWatermarkDedup:
    """Gate 4 drain helper: find_run_by_watermark finds/misses correctly."""

    def test_find_run_by_watermark_returns_existing(self, db: Any) -> None:
        """A run with a matching watermark is found."""
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_delta_service import ProjectDeltaService
        from holdspeak.services.project_service import ProjectService

        project_svc = ProjectService(db)
        project = project_svc.create_project(OWNER, {"name": "Watermark test"})
        project_id = project["project_id"]

        svc = ProjectStewardService(
            db,
            ProjectEvidenceCollector(db),
            ProjectDeltaService(db, ProjectEvidenceCollector(db)),
            project_service=project_svc,
        )

        # Create a policy so insert_run works
        db.steward_policies.insert_policy(
            policy_id="pol_wm_001",
            project_id=project_id,
            eligible_effect_kinds_json="[]",
            enabled=1,
        )

        # Insert a run with a specific watermark
        run_id = svc.insert_run(
            OWNER, project_id, watermark="watch:cw1:rev123",
        )

        # Find by watermark
        found = svc.find_run_by_watermark(project_id, "watch:cw1:rev123")
        assert found is not None
        assert found["id"] == run_id

    def test_empty_watermark_returns_none(self, db: Any) -> None:
        """An empty watermark never matches."""
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_delta_service import ProjectDeltaService

        svc = ProjectStewardService(
            db,
            ProjectEvidenceCollector(db),
            ProjectDeltaService(db, ProjectEvidenceCollector(db)),
        )

        result = svc.find_run_by_watermark("proj-xxx", "")
        assert result is None

    def test_unknown_watermark_returns_none(self, db: Any) -> None:
        """A watermark that doesn't match any run returns None."""
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_delta_service import ProjectDeltaService

        svc = ProjectStewardService(
            db,
            ProjectEvidenceCollector(db),
            ProjectDeltaService(db, ProjectEvidenceCollector(db)),
        )

        result = svc.find_run_by_watermark("proj-xxx", "watch:cw99:rev999")
        assert result is None


# ── (e) Risk title ──────────────────────────────────────────────────


class TestRiskTitle:
    """The door item title is human and specific, never category keys."""

    def test_status_change_title(self) -> None:
        from holdspeak.services.project_delta_service import _build_risk_title
        title = _build_risk_title({
            "entity_ref": "KAN-1",
            "changed": {"status": ["In Progress", "Done"]},
        })
        assert "KAN-1" in title
        assert "In Progress" in title
        assert "Done" in title

    def test_status_preferred_over_category(self) -> None:
        """When both status and status_category are in changed,
        status names are used, category keys are suppressed."""
        from holdspeak.services.project_delta_service import _build_risk_title
        title = _build_risk_title({
            "entity_ref": "KAN-1",
            "changed": {
                "status": ["In Progress", "Done"],
                "status_category": ["indeterminate", "done"],
            },
        })
        assert "In Progress" in title
        assert "Done" in title
        # Category keys must NOT appear
        assert "indeterminate" not in title.lower()

    def test_category_only_maps_to_human_labels(self) -> None:
        """When only category keys are available, they map to human labels."""
        from holdspeak.services.project_delta_service import _build_risk_title
        title = _build_risk_title({
            "entity_ref": "KAN-1",
            "changed": {"status_category": ["indeterminate", "done"]},
        })
        assert "KAN-1" in title
        assert "In progress" in title
        assert "Done" in title
        assert "indeterminate" not in title.lower()

    def test_due_change_title(self) -> None:
        from holdspeak.services.project_delta_service import _build_risk_title
        title = _build_risk_title({
            "entity_ref": "PROJ-42",
            "changed": {"due_at": ["2026-09-15", "2026-09-01"]},
        })
        assert "PROJ-42" in title
        assert "due" in title.lower()

    def test_no_entity_ref(self) -> None:
        from holdspeak.services.project_delta_service import _build_risk_title
        title = _build_risk_title({
            "changed": {"status": ["Open", "Closed"]},
        })
        assert "Open" in title
        assert "Closed" in title
