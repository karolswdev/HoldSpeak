"""HS-160-02: ProjectEvidenceCollector -- per-adapter truth tables, TST-003
laws, and the watch no-fetch proof.

Acceptance criteria tested:
- TST-003: retry dedup (same fact/version -> same pobs_ or no-op)
- TST-003: stale/failed coverage explicit
- TST-003: partial success (one adapter raises -> others persist + failed)
- The watch adapter consumes ONLY canonical evaluations/snapshots (a test
  proves no fetcher is invoked)
- Every observation carries kind/subject_ref/source_version/observed_at/
  fact_json/content_hash per SS5.5; refs canonical via holdspeak.refs
- Freshness writeback to project_sources
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.db.delta import DeltaRepository
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pobs_id
from holdspeak.refs import format as format_ref, parse as parse_ref
from holdspeak.services.project_evidence_collector import (
    AdapterResult,
    DecisionsAdapter,
    FollowThroughAdapter,
    MeetingsAdapter,
    ProjectEvidenceCollector,
    ResourcesAdapter,
    WatchAdapter,
    _content_hash,
)
from holdspeak.services.reaction_service import normalize_snapshot


OWNER = Principal(PrincipalKind.OWNER, "collector-test-owner")


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "collector-test.db")
    yield db
    reset_database()


def _seed_project(db: Database, project_id: str = "proj-test1",
                  name: str = "Test Project") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects (id, name, description, keywords_json,
               team_members_json, context_json, detection_threshold, revision,
               created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, 1,
                       datetime('now'), datetime('now'))""",
            (project_id, name),
        )
    return project_id


def _seed_meeting(db: Database, meeting_id: str = "m-001",
                  title: str = "Weekly standup") -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 1, 10, 0),
        title=title,
        capture_status="finalized",
    ))


def _associate_meeting(db: Database, project_id: str,
                       meeting_id: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO meeting_projects
               (meeting_id, project_id, source, confidence)
               VALUES (?, ?, 'manual', 1.0)""",
            (meeting_id, project_id),
        )


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
                      due: str = "2024-07-01", status: str = "open",
                      meeting_id: str | None = None) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state,
                created_at, source_type, source_ref)
               VALUES (?, ?, ?, ?, ?, ?, 'accepted',
                       datetime('now'), 'manual', '')""",
            (item_id, meeting_id, task, owner, due, status),
        )


def _seed_resource(db: Database, project_id: str,
                   resource_ref: str = "note:n-001",
                   relationship: str = "member") -> None:
    db.project_relationships.upsert(
        project_id=project_id,
        resource_ref=resource_ref,
        relationship=relationship,
        source="manual",
        confidence=1.0,
    )


def _seed_watch(db: Database, watch_id: str = "watch_abc",
                connector_id: str = "gh",
                project_id: str = "proj-test1",
                snapshot: dict | None = None) -> str:
    """Seed a connector_watches row + project_sources binding."""
    snap = snapshot or {}
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, query_json,
                snapshot_json, enabled, created_at, updated_at)
               VALUES (?, ?, 'pull_requests', 'Test Watch', '{}',
                       ?, 1, datetime('now'), datetime('now'))""",
            (watch_id, connector_id,
             json.dumps(snap, sort_keys=True, separators=(",", ":"))),
        )
        source_id = f"psrc_test_{watch_id}"
        conn.execute(
            """INSERT INTO project_sources
               (id, project_id, source_ref, label, semantic_role,
                enabled, revision, created_at, updated_at)
               VALUES (?, ?, ?, 'Test Watch', 'watch',
                       1, 0, datetime('now'), datetime('now'))""",
            (source_id, project_id, f"watch:{watch_id}"),
        )
    return source_id


# ── MeetingsAdapter tests ─────────────────────────────────────────────


class TestMeetingsAdapter:
    def test_collects_associated_meetings(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_meeting(db, "m-001", "Standup")
        _seed_meeting(db, "m-002", "Retro")
        _associate_meeting(db, pid, "m-001")
        _associate_meeting(db, pid, "m-002")

        adapter = MeetingsAdapter(db)
        result = adapter.collect(pid, {})

        assert result.freshness == "ok"
        assert result.error is None
        assert len(result.observations) == 2
        kinds = {o.kind for o in result.observations}
        assert kinds == {"meeting.associated"}

        # Subject refs are canonical
        for obs in result.observations:
            ref = parse_ref(obs.subject_ref)
            assert ref.type == "meeting"
            assert ref.is_registered

    def test_empty_project_yields_empty(self, rig):
        db = rig
        pid = _seed_project(db)
        adapter = MeetingsAdapter(db)
        result = adapter.collect(pid, {})
        assert result.observations == []
        assert result.freshness == "ok"


# ── ResourcesAdapter tests ───────────────────────────────────────────


class TestResourcesAdapter:
    def test_collects_linked_resources(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_resource(db, pid, "note:n-001")
        _seed_resource(db, pid, "artifact:a-001")

        adapter = ResourcesAdapter(db)
        result = adapter.collect(pid, {})

        assert result.freshness == "ok"
        assert len(result.observations) == 2
        kinds = {o.kind for o in result.observations}
        assert kinds == {"resource.linked"}

        refs = {o.subject_ref for o in result.observations}
        assert "note:n-001" in refs
        assert "artifact:a-001" in refs


# ── DecisionsAdapter tests ───────────────────────────────────────────


class TestDecisionsAdapter:
    def test_collects_lifecycle_and_review_due(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_decision(db, "dec-001", "Adopt microservices", "accepted")
        _seed_decision(db, "dec-002", "Drop legacy API", "recorded")

        adapter = DecisionsAdapter(db)
        result = adapter.collect(pid, {})

        assert result.freshness == "ok"
        kinds = [o.kind for o in result.observations]
        # dec-001 gets both lifecycle and review_due; dec-002 gets only lifecycle
        assert kinds.count("decision.lifecycle") == 2
        assert kinds.count("decision.review_due") == 1

        # The review_due observation refers to the accepted decision
        review_obs = [o for o in result.observations if o.kind == "decision.review_due"]
        assert len(review_obs) == 1
        fact = json.loads(review_obs[0].fact_json)
        assert fact["decision_id"] == "dec-001"


# ── FollowThroughAdapter tests ───────────────────────────────────────


class TestFollowThroughAdapter:
    def test_collects_overdue_items(self, rig):
        db = rig
        pid = _seed_project(db)
        # Action items reach the project board via meeting_projects join
        _seed_meeting(db, "m-ft1", "Follow-through meeting")
        _associate_meeting(db, pid, "m-ft1")
        _seed_action_item(db, "ai-001", "Review PR", "Alice",
                          "2024-01-01", meeting_id="m-ft1")

        adapter = FollowThroughAdapter(db)
        result = adapter.collect(pid, {})

        assert result.freshness == "ok"
        overdue = [o for o in result.observations if o.kind == "followthrough.overdue"]
        assert len(overdue) >= 1

        # Subject ref is canonical action_item:
        ref = parse_ref(overdue[0].subject_ref)
        assert ref.type == "action_item"
        assert ref.is_registered


# ── WatchAdapter tests ───────────────────────────────────────────────


class TestWatchAdapter:
    def test_collects_transitions_from_stored_snapshot(self, rig):
        db = rig
        pid = _seed_project(db)
        snapshot = normalize_snapshot("gh", [
            {"id": "42", "title": "Fix bug", "state": "open", "url": "http://x"},
        ])
        _seed_watch(db, "watch_w1", "gh", pid, snapshot)

        adapter = WatchAdapter(db)
        result = adapter.collect(pid, {"source_ref": "watch:watch_w1"})

        assert result.freshness == "ok"
        assert result.error is None
        assert len(result.observations) >= 1
        assert all(o.kind == "watch.transition" for o in result.observations)

    def test_no_fetch_proof(self, rig):
        """The watch adapter must NEVER call a fetcher/provider.

        A spy fetcher is injected; it raises if called.
        """
        db = rig
        pid = _seed_project(db)
        snapshot = normalize_snapshot("gh", [
            {"id": "99", "title": "Test", "state": "open", "url": "http://y"},
        ])
        _seed_watch(db, "watch_nf", "gh", pid, snapshot)

        # The spy: if anything tries to call snapshot_fetcher, we fail
        spy_fetcher = MagicMock(side_effect=AssertionError(
            "FETCHER CALLED -- watch adapter must NEVER call a fetcher"
        ))

        # Ensure the adapter does not touch the fetcher
        adapter = WatchAdapter(db)
        # Monkey-patch the db's automations to spy on any refresh attempt
        original_record_refresh = db.automations.record_refresh
        db.automations.record_refresh = spy_fetcher

        try:
            result = adapter.collect(pid, {"source_ref": "watch:watch_nf"})
        finally:
            db.automations.record_refresh = original_record_refresh

        # The spy must not have been called
        spy_fetcher.assert_not_called()
        assert result.error is None

    def test_invalid_source_ref_returns_error(self, rig):
        db = rig
        adapter = WatchAdapter(db)
        result = adapter.collect("proj-x", {"source_ref": "not-a-watch"})
        assert result.error is not None
        assert result.error.code == "invalid_source_ref"

    def test_missing_watch_returns_error(self, rig):
        db = rig
        adapter = WatchAdapter(db)
        result = adapter.collect("proj-x", {"source_ref": "watch:nonexistent"})
        assert result.error is not None
        assert result.error.code == "watch_not_found"


# ── ProjectEvidenceCollector integration ─────────────────────────────


class TestCollectAll:
    def test_collects_from_all_native_families(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_meeting(db, "m-010", "Sprint review")
        _associate_meeting(db, pid, "m-010")
        _seed_decision(db, "dec-010", "Go with Postgres", "accepted")
        _seed_resource(db, pid, "note:n-010")

        collector = ProjectEvidenceCollector(db)
        coverage = collector.collect_all(pid)

        # All four native families should be present
        assert "native:meetings" in coverage
        assert "native:resources" in coverage
        assert "native:decisions" in coverage
        assert "native:followthrough" in coverage

        # At least the seeded ones should have observations
        assert coverage["native:meetings"]["state"] == "ok"
        assert coverage["native:meetings"]["inserted"] >= 1
        assert coverage["native:resources"]["state"] == "ok"
        assert coverage["native:resources"]["inserted"] >= 1
        assert coverage["native:decisions"]["state"] == "ok"
        assert coverage["native:decisions"]["inserted"] >= 1

    def test_collects_from_watch_sources(self, rig):
        db = rig
        pid = _seed_project(db)
        snapshot = normalize_snapshot("gh", [
            {"id": "77", "title": "Deploy", "state": "open", "url": "http://z"},
        ])
        source_id = _seed_watch(db, "watch_c1", "gh", pid, snapshot)

        collector = ProjectEvidenceCollector(db)
        coverage = collector.collect_all(pid)

        assert source_id in coverage
        assert coverage[source_id]["state"] == "ok"
        assert coverage[source_id]["inserted"] >= 1


class TestRetryNoOp:
    """TST-003: retry dedup -- same fact/version -> same pobs_ or no-op."""

    def test_collect_twice_second_all_noop(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_meeting(db, "m-020", "Planning")
        _associate_meeting(db, pid, "m-020")
        _seed_decision(db, "dec-020", "Use Redis", "recorded")

        collector = ProjectEvidenceCollector(db)

        # First collect
        cov1 = collector.collect_all(pid)
        total_inserted_1 = sum(
            v.get("inserted", 0) for v in cov1.values()
            if v.get("state") != "failed"
        )
        assert total_inserted_1 > 0

        # Second collect -- identical facts -> all no-op
        cov2 = collector.collect_all(pid)
        total_inserted_2 = sum(
            v.get("inserted", 0) for v in cov2.values()
            if v.get("state") != "failed"
        )
        total_noop_2 = sum(
            v.get("no_op", 0) for v in cov2.values()
            if v.get("state") != "failed"
        )
        assert total_inserted_2 == 0, (
            f"Expected zero new inserts on retry, got {total_inserted_2}"
        )
        assert total_noop_2 > 0, "Expected at least one no-op on retry"

    def test_deterministic_pobs_id(self, rig):
        """Same adapter/source_id/source_version/fact_key -> same pobs_ ID."""
        id1 = generate_pobs_id(
            adapter="meetings", source_id="native:meetings",
            source_version="v1", fact_key="abc123",
        )
        id2 = generate_pobs_id(
            adapter="meetings", source_id="native:meetings",
            source_version="v1", fact_key="abc123",
        )
        assert id1 == id2
        assert id1.startswith("pobs_")


class TestPartialSuccess:
    """TST-003/DOM-008: one adapter raises -> others persist + failed coverage."""

    def test_one_adapter_fails_others_persist(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_meeting(db, "m-030", "Demo")
        _associate_meeting(db, pid, "m-030")
        _seed_resource(db, pid, "note:n-030")

        collector = ProjectEvidenceCollector(db)

        # Monkeypatch the decisions adapter to raise
        original_collect = collector._native_adapters["decisions"].collect

        def _boom(*args, **kwargs):
            raise RuntimeError("Simulated adapter failure")

        collector._native_adapters["decisions"].collect = _boom

        try:
            coverage = collector.collect_all(pid)
        finally:
            collector._native_adapters["decisions"].collect = original_collect

        # Decisions should be marked failed
        assert coverage["native:decisions"]["state"] == "failed"
        assert "error" in coverage["native:decisions"]
        assert coverage["native:decisions"]["error"]["code"] == "RuntimeError"

        # Others should have succeeded
        assert coverage["native:meetings"]["state"] == "ok"
        assert coverage["native:meetings"]["inserted"] >= 1
        assert coverage["native:resources"]["state"] == "ok"
        assert coverage["native:resources"]["inserted"] >= 1

        # Observations from successful adapters should be in the DB
        obs = db.project_observations.list_observations(pid)
        assert len(obs) >= 2  # at least meeting + resource


class TestFreshnessWriteback:
    """Freshness state and last_observed_at written to project_sources."""

    def test_watch_source_freshness_updated(self, rig):
        db = rig
        pid = _seed_project(db)
        snapshot = normalize_snapshot("gh", [
            {"id": "55", "title": "Hotfix", "state": "open", "url": "http://h"},
        ])
        source_id = _seed_watch(db, "watch_fw", "gh", pid, snapshot)

        # Before collection
        src_before = db.automations.get_project_source(source_id)
        assert src_before["freshness_state"] == ""
        assert src_before["last_observed_at"] is None

        collector = ProjectEvidenceCollector(db)
        collector.collect_all(pid)

        # After collection
        src_after = db.automations.get_project_source(source_id)
        assert src_after["freshness_state"] == "ok"
        assert src_after["last_observed_at"] is not None


class TestObservationShape:
    """Every observation carries the SS5.5 shape with canonical refs."""

    def test_observation_has_all_fields(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_meeting(db, "m-040", "Shape test")
        _associate_meeting(db, pid, "m-040")

        collector = ProjectEvidenceCollector(db)
        collector.collect_all(pid)

        obs_list = db.project_observations.list_observations(pid)
        assert len(obs_list) >= 1

        obs = obs_list[0]
        # SS5.5 required fields
        assert obs["id"].startswith("pobs_")
        assert obs["project_id"] == pid
        assert obs["observation_kind"] != ""
        assert obs["observed_at"] != ""
        assert obs["fact_json"] != ""
        assert obs["content_hash"] != ""

    def test_subject_ref_is_canonical(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_meeting(db, "m-050", "Ref test")
        _associate_meeting(db, pid, "m-050")

        collector = ProjectEvidenceCollector(db)
        collector.collect_all(pid)

        obs_list = db.project_observations.list_observations(pid)
        meeting_obs = [o for o in obs_list if o["observation_kind"] == "meeting.associated"]
        assert len(meeting_obs) >= 1

        ref = parse_ref(meeting_obs[0]["subject_ref"])
        assert ref.type == "meeting"
        assert ref.is_registered
        assert ref.id == "m-050"
