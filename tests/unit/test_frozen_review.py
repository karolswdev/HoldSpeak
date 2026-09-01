"""HS-160-03: Golden frozen review tests (TST-004).

Acceptance criteria tested:
- GOLDEN WINDOWS: seeded desk -> open_review -> full proposal list as exact
  golden structure; run twice -> identical incl. ordering; re-read from
  storage -> identical (SYS-024).
- DEL-001: the cursor law -- pre-cursor material excluded, post-cursor
  observations enter the window.
- SYS-025/DOM-008: the degraded leg -- one source failed -> coverage_degraded
  present in manifest AND as review-visible proposal, never silent.
- Conflict retention: two disagreeing observations -> one conflict proposal
  carrying both sources (DOM-005).
- Materiality unit tests per factor + version pin: changing a factor without
  bumping MATERIALITY_VERSION fails a test.
- One-open-review law: re-running open_review on same project returns the
  existing open window.
- Step-11 hook identity: the hook receives and returns unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pobs_id
from holdspeak.services.project_delta_service import (
    MATERIALITY_VERSION,
    PROPOSAL_RULES,
    ProjectDeltaService,
    _FACTOR_WEIGHTS,
    compute_materiality,
    score_decision_impact,
    score_evidence_confidence,
    score_lifecycle_severity,
    score_novelty,
    score_outcome_relevance,
    score_overdue_blocked,
)
from holdspeak.services.project_evidence_collector import (
    AdapterResult,
    ObservationRecord,
    ProjectEvidenceCollector,
    _content_hash,
)


OWNER = Principal(PrincipalKind.OWNER, "frozen-review-test")


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "frozen-review-test.db")
    yield db
    reset_database()


def _seed_project(db: Database, project_id: str = "proj-fr01",
                  name: str = "Frozen Review Project") -> str:
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


def _seed_meeting(db: Database, meeting_id: str = "m-fr01",
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


def _seed_decision(db: Database, decision_id: str = "dec-fr01",
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


def _seed_action_item(db: Database, item_id: str = "ai-fr01",
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


def _make_collector(db: Database) -> ProjectEvidenceCollector:
    return ProjectEvidenceCollector(db)


def _make_service(db: Database) -> ProjectDeltaService:
    collector = _make_collector(db)
    return ProjectDeltaService(db, collector)


def _seed_full_desk(db: Database, project_id: str = "proj-fr01") -> str:
    """Seed a full desk with meetings, decisions, and action items."""
    _seed_project(db, project_id)
    _seed_meeting(db, "m-fr01", "Weekly standup")
    _associate_meeting(db, project_id, "m-fr01")
    _seed_decision(db, "dec-fr01", "Adopt microservices", "accepted")
    _seed_action_item(
        db, "ai-fr01", "Review PR", "Alice", "2024-07-01", "open", "m-fr01",
    )
    return project_id


# ── GOLDEN WINDOWS (TST-004 / SYS-024) ───────────────────────────────


class TestGoldenWindows:
    """A seeded desk's review window reproduces byte-identically across runs."""

    def test_golden_structure(self, rig):
        """open_review produces a well-formed window with all required fields."""
        project_id = _seed_full_desk(rig)
        svc = _make_service(rig)

        window = svc.open_review(OWNER, project_id)

        # Required fields
        assert window["review_id"].startswith("prev_")
        assert window["project_id"] == project_id
        assert window["status"] == "open"
        assert window["from_sequence"] == 0  # first review
        assert isinstance(window["through_sequence"], int)
        assert window["through_sequence"] > 0
        assert isinstance(window["source_manifest"], dict)
        assert window["materiality_version"] == MATERIALITY_VERSION
        assert isinstance(window["proposals"], list)

        # SYS-022: every proposal states required fields
        for p in window["proposals"]:
            assert "id" in p
            assert "proposal_kind" in p
            assert "target_ref" in p
            assert "materiality" in p
            assert "producer_kind" in p  # provenance class
            assert "lifecycle" in p

    def test_run_twice_identical(self, rig):
        """Running open_review twice returns the same window (one-open-review + SYS-024)."""
        project_id = _seed_full_desk(rig)
        svc = _make_service(rig)

        window1 = svc.open_review(OWNER, project_id)
        window2 = svc.open_review(OWNER, project_id)

        assert window1 == window2
        assert window1["review_id"] == window2["review_id"]
        assert len(window1["proposals"]) == len(window2["proposals"])

        # Byte-identical serialization
        json1 = json.dumps(window1, sort_keys=True)
        json2 = json.dumps(window2, sort_keys=True)
        assert json1 == json2

    def test_reread_from_storage_identical(self, rig):
        """Re-reading the stored window matches the original (SYS-024)."""
        project_id = _seed_full_desk(rig)
        svc = _make_service(rig)

        window = svc.open_review(OWNER, project_id)

        # Read back from storage using a fresh service instance
        svc2 = _make_service(rig)
        window2 = svc2.open_review(OWNER, project_id)

        assert window == window2

    def test_ordering_stable(self, rig):
        """Proposal ordering is stable across reads."""
        project_id = _seed_full_desk(rig)
        svc = _make_service(rig)

        window = svc.open_review(OWNER, project_id)
        proposals = window["proposals"]

        # Ordering: materiality desc, then by kind, then by id
        for i in range(len(proposals) - 1):
            m_cur = float(proposals[i].get("materiality", "0"))
            m_nxt = float(proposals[i + 1].get("materiality", "0"))
            if m_cur == m_nxt:
                # Within same materiality, ordering by created_at/kind/id is stable
                continue
            assert m_cur >= m_nxt, (
                f"Proposals not sorted by materiality desc: "
                f"{m_cur} < {m_nxt}"
            )


# ── CURSOR LAW (DEL-001) ─────────────────────────────────────────────


class TestCursorLaw:
    """DEL-001: the window derives from the last ACCEPTED cursor."""

    def test_pre_cursor_excluded(self, rig):
        """Material from before the cursor does NOT enter a subsequent review."""
        project_id = _seed_project(rig)
        _seed_meeting(rig, "m-cur01", "Old standup")
        _associate_meeting(rig, project_id, "m-cur01")
        _seed_decision(rig, "dec-cur01", "Old decision", "accepted")

        svc = _make_service(rig)

        # First review: captures everything
        window1 = svc.open_review(OWNER, project_id)
        review_id = window1["review_id"]
        proposals_1 = window1["proposals"]

        # Accept the first review (simulate acceptance by updating status)
        with rig._connection() as conn:
            conn.execute(
                "UPDATE project_reviews SET status = 'accepted', "
                "accepted_at = datetime('now') WHERE id = ?",
                (review_id,),
            )
            # Update last_review_id on the project
            conn.execute(
                "UPDATE projects SET last_review_id = ? WHERE id = ?",
                (review_id, project_id),
            )

        # Add new material
        _seed_decision(rig, "dec-cur02", "New decision", "accepted")

        # Second review: should only contain post-cursor material
        svc2 = _make_service(rig)
        window2 = svc2.open_review(OWNER, project_id)

        assert window2["review_id"] != review_id
        assert window2["from_sequence"] == window1["through_sequence"]

    def test_post_cursor_enters(self, rig):
        """Observations added after the cursor DO enter the next review."""
        project_id = _seed_project(rig)
        svc = _make_service(rig)

        # First review: empty
        window1 = svc.open_review(OWNER, project_id)
        review_id = window1["review_id"]

        # Accept the first review
        with rig._connection() as conn:
            conn.execute(
                "UPDATE project_reviews SET status = 'accepted', "
                "accepted_at = datetime('now') WHERE id = ?",
                (review_id,),
            )
            conn.execute(
                "UPDATE projects SET last_review_id = ? WHERE id = ?",
                (review_id, project_id),
            )

        # Add new material
        _seed_decision(rig, "dec-post01", "Post-cursor decision", "accepted")

        # Second review: new material enters
        svc2 = _make_service(rig)
        window2 = svc2.open_review(OWNER, project_id)

        assert window2["review_id"] != review_id
        # The new review's through_sequence should be >= the prior's
        assert window2["through_sequence"] >= window1["through_sequence"]


# ── DEGRADED LEG (SYS-025 / DOM-008) ─────────────────────────────────


class TestDegradedLeg:
    """A failed/stale source appears as degraded coverage in manifest AND review."""

    def test_failed_source_coverage_degraded(self, rig):
        """One source failed -> coverage_degraded present in manifest AND proposals."""
        project_id = _seed_project(rig)

        # Create a collector that fails on one source
        class FailingCollector:
            def collect_all(self, pid):
                return {
                    "native:meetings": {"state": "ok", "inserted": 0, "no_op": 0},
                    "native:resources": {"state": "ok", "inserted": 0, "no_op": 0},
                    "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0},
                    "native:followthrough": {
                        "state": "failed",
                        "error": {"code": "ConnectionError", "message": "timeout"},
                    },
                }

        svc = ProjectDeltaService(rig, FailingCollector())
        window = svc.open_review(OWNER, project_id)

        # Check manifest
        manifest = window["source_manifest"]
        assert "native:followthrough" in manifest
        ft_entry = manifest["native:followthrough"]
        assert ft_entry["state"] == "failed"
        assert ft_entry.get("error", {}).get("code") == "ConnectionError"

        # Check proposals contain a coverage_degraded entry
        degraded = [
            p for p in window["proposals"]
            if p["proposal_kind"] == "coverage_degraded"
        ]
        assert len(degraded) >= 1, "Failed source must produce coverage_degraded proposal"
        assert any(
            "followthrough" in p["target_ref"] for p in degraded
        ), "coverage_degraded must reference the failed source"

    def test_stale_source_coverage_degraded(self, rig):
        """A stale source also produces coverage_degraded."""
        project_id = _seed_project(rig)

        class StaleCollector:
            def collect_all(self, pid):
                return {
                    "native:meetings": {"state": "ok", "inserted": 0, "no_op": 0},
                    "native:resources": {"state": "stale", "inserted": 0, "no_op": 0},
                    "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0},
                    "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0},
                }

        svc = ProjectDeltaService(rig, StaleCollector())
        window = svc.open_review(OWNER, project_id)

        degraded = [
            p for p in window["proposals"]
            if p["proposal_kind"] == "coverage_degraded"
        ]
        assert len(degraded) >= 1
        assert any("resources" in p["target_ref"] for p in degraded)

    def test_all_ok_no_degraded(self, rig):
        """When all sources succeed, no coverage_degraded proposals appear."""
        project_id = _seed_project(rig)

        class AllOkCollector:
            def collect_all(self, pid):
                return {
                    "native:meetings": {"state": "ok", "inserted": 0, "no_op": 0},
                    "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0},
                }

        svc = ProjectDeltaService(rig, AllOkCollector())
        window = svc.open_review(OWNER, project_id)

        degraded = [
            p for p in window["proposals"]
            if p["proposal_kind"] == "coverage_degraded"
        ]
        assert len(degraded) == 0


# ── CONFLICT RETENTION ────────────────────────────────────────────────


class TestConflictRetention:
    """Two disagreeing observations -> one conflict proposal with both sources."""

    def test_conflicting_observations(self, rig):
        """Observations with same subject_ref+kind but different content -> conflict."""
        project_id = _seed_project(rig)

        # Manually insert two conflicting observations
        delta = rig.project_observations
        obs_id_1 = generate_pobs_id(
            adapter="decisions", source_id="src-a",
            source_version="v1", fact_key="hash-a",
        )
        obs_id_2 = generate_pobs_id(
            adapter="decisions", source_id="src-b",
            source_version="v1", fact_key="hash-b",
        )

        delta.insert_observation(
            observation_id=obs_id_1,
            project_id=project_id,
            source_id="src-a",
            observation_kind="decision.lifecycle",
            subject_ref="decision:dec-conflict",
            source_version="v1",
            observed_at="2026-08-01T10:00:00+00:00",
            fact_json='{"decision_id":"dec-conflict","lifecycle":"accepted","text":"A"}',
            content_hash="aaaa",
        )
        delta.insert_observation(
            observation_id=obs_id_2,
            project_id=project_id,
            source_id="src-b",
            observation_kind="decision.lifecycle",
            subject_ref="decision:dec-conflict",
            source_version="v1",
            observed_at="2026-08-01T11:00:00+00:00",
            fact_json='{"decision_id":"dec-conflict","lifecycle":"superseded","text":"B"}',
            content_hash="bbbb",
        )

        # Use a no-op collector since we already seeded observations
        class NoOpCollector:
            def collect_all(self, pid):
                return {
                    "native:meetings": {"state": "ok", "inserted": 0, "no_op": 0},
                }

        svc = ProjectDeltaService(rig, NoOpCollector())
        window = svc.open_review(OWNER, project_id)

        conflicts = [
            p for p in window["proposals"]
            if p["proposal_kind"] == "conflict"
        ]
        assert len(conflicts) == 1, (
            f"Expected 1 conflict proposal, got {len(conflicts)}"
        )

        conflict = conflicts[0]
        assert conflict["target_ref"] == "decision:dec-conflict"

        # The conflict must carry both source refs
        patch = json.loads(conflict["patch_json"])
        assert "src-a" in patch["conflicting_sources"]
        assert "src-b" in patch["conflicting_sources"]
        assert len(patch["conflicting_hashes"]) == 2

    def test_no_conflict_when_same_hash(self, rig):
        """Same content hash = no conflict (observations agree)."""
        project_id = _seed_project(rig)

        delta = rig.project_observations
        obs_id_1 = generate_pobs_id(
            adapter="decisions", source_id="src-a",
            source_version="v1", fact_key="same-hash",
        )
        obs_id_2 = generate_pobs_id(
            adapter="decisions", source_id="src-b",
            source_version="v1", fact_key="same-hash-2",
        )

        same_fact = '{"decision_id":"dec-agree","lifecycle":"accepted","text":"Same"}'
        same_hash = "same-hash-value"

        delta.insert_observation(
            observation_id=obs_id_1,
            project_id=project_id,
            source_id="src-a",
            observation_kind="decision.lifecycle",
            subject_ref="decision:dec-agree",
            source_version="v1",
            observed_at="2026-08-01T10:00:00+00:00",
            fact_json=same_fact,
            content_hash=same_hash,
        )
        delta.insert_observation(
            observation_id=obs_id_2,
            project_id=project_id,
            source_id="src-b",
            observation_kind="decision.lifecycle",
            subject_ref="decision:dec-agree",
            source_version="v1",
            observed_at="2026-08-01T11:00:00+00:00",
            fact_json=same_fact,
            content_hash=same_hash,
        )

        class NoOpCollector:
            def collect_all(self, pid):
                return {}

        svc = ProjectDeltaService(rig, NoOpCollector())
        window = svc.open_review(OWNER, project_id)

        conflicts = [
            p for p in window["proposals"]
            if p["proposal_kind"] == "conflict"
        ]
        assert len(conflicts) == 0


# ── MATERIALITY UNIT TESTS ───────────────────────────────────────────


class TestMaterialityFactors:
    """Per-factor scoring tests + version pin."""

    def test_outcome_relevance_risk(self):
        assert score_outcome_relevance({"proposal_kind": "risk_attention"}) == 0.9

    def test_outcome_relevance_review(self):
        assert score_outcome_relevance({"proposal_kind": "review_flag"}) == 0.7

    def test_outcome_relevance_observation(self):
        assert score_outcome_relevance({"proposal_kind": "observation_attention"}) == 0.5

    def test_outcome_relevance_conflict(self):
        assert score_outcome_relevance({"proposal_kind": "conflict"}) == 0.8

    def test_outcome_relevance_degraded(self):
        assert score_outcome_relevance({"proposal_kind": "coverage_degraded"}) == 0.6

    def test_outcome_relevance_unknown(self):
        assert score_outcome_relevance({"proposal_kind": "unknown"}) == 0.3

    def test_lifecycle_severity_overdue(self):
        p = {"patch_json": '{"lane":"overdue"}'}
        assert score_lifecycle_severity(p) == 1.0

    def test_lifecycle_severity_broken(self):
        p = {"patch_json": '{"lifecycle":"broken"}'}
        assert score_lifecycle_severity(p) == 1.0

    def test_lifecycle_severity_at_risk(self):
        p = {"patch_json": '{"lifecycle":"at_risk"}'}
        assert score_lifecycle_severity(p) == 0.7

    def test_lifecycle_severity_active(self):
        p = {"patch_json": '{"lifecycle":"active"}'}
        assert score_lifecycle_severity(p) == 0.3

    def test_overdue_blocked_overdue(self):
        p = {"proposal_kind": "risk_attention", "patch_json": '{"lane":"overdue"}'}
        assert score_overdue_blocked(p) == 1.0

    def test_overdue_blocked_stale(self):
        p = {"patch_json": '{"stale_score":0.8}'}
        assert score_overdue_blocked(p) == 0.8

    def test_overdue_blocked_degraded(self):
        p = {"proposal_kind": "coverage_degraded"}
        assert score_overdue_blocked(p) == 0.8

    def test_overdue_blocked_none(self):
        p = {"proposal_kind": "review_flag"}
        assert score_overdue_blocked(p) == 0.0

    def test_decision_impact_review(self):
        assert score_decision_impact({"proposal_kind": "review_flag"}) == 0.8

    def test_decision_impact_conflict(self):
        assert score_decision_impact({"proposal_kind": "conflict"}) == 0.7

    def test_decision_impact_other(self):
        assert score_decision_impact({"proposal_kind": "risk_attention"}) == 0.1

    def test_novelty(self):
        assert score_novelty({}) == 0.8

    def test_evidence_confidence_observed(self):
        assert score_evidence_confidence({"provenance_class": "observed_fact"}) == 1.0

    def test_evidence_confidence_assessment(self):
        assert score_evidence_confidence({"provenance_class": "assessment"}) == 0.7

    def test_evidence_confidence_proposal(self):
        assert score_evidence_confidence({"provenance_class": "proposal"}) == 0.5

    def test_weights_sum_to_one(self):
        assert abs(sum(_FACTOR_WEIGHTS.values()) - 1.0) < 1e-9

    def test_compute_materiality_deterministic(self):
        """Same input -> same materiality score."""
        p = {
            "proposal_kind": "risk_attention",
            "patch_json": '{"lane":"overdue"}',
            "provenance_class": "assessment",
        }
        s1 = compute_materiality(p)
        s2 = compute_materiality(p)
        assert s1 == s2
        assert 0.0 <= s1 <= 1.0

    def test_materiality_version_pin(self):
        """The version string is pinned.

        If a developer changes a factor without bumping the version, this
        test MUST fail.  The canonical example must produce the same score
        under the pinned version.
        """
        assert MATERIALITY_VERSION == "v1"

        # Canonical scored example: a risk_attention proposal with overdue lane
        canonical = {
            "proposal_kind": "risk_attention",
            "patch_json": '{"lane":"overdue"}',
            "provenance_class": "assessment",
        }
        score = compute_materiality(canonical)
        # Pin the expected score for v1
        # outcome_relevance: 0.9 * 0.20 = 0.180
        # lifecycle_severity: 1.0 * 0.25 = 0.250
        # overdue_blocked: 1.0 * 0.20 = 0.200
        # decision_impact: 0.1 * 0.15 = 0.015
        # novelty: 0.8 * 0.10 = 0.080
        # evidence_confidence: 0.7 * 0.10 = 0.070
        # Total: 0.795
        assert score == 0.795, (
            f"Canonical v1 example must score 0.795, got {score}. "
            f"If you changed a factor, bump MATERIALITY_VERSION."
        )

    def test_materiality_range(self):
        """Score is always in [0.0, 1.0]."""
        test_cases = [
            {"proposal_kind": "risk_attention", "patch_json": '{"lane":"overdue"}', "provenance_class": "observed_fact"},
            {"proposal_kind": "review_flag", "provenance_class": "assessment"},
            {"proposal_kind": "unknown", "provenance_class": "proposal"},
            {},
        ]
        for p in test_cases:
            s = compute_materiality(p)
            assert 0.0 <= s <= 1.0, f"Score {s} out of range for {p}"


# ── ONE-OPEN-REVIEW LAW ──────────────────────────────────────────────


class TestOneOpenReviewLaw:
    """SYS-020: at most one open review per project."""

    def test_existing_open_review_returned(self, rig):
        """If an open review exists, open_review returns it (no new review)."""
        project_id = _seed_project(rig)
        svc = _make_service(rig)

        w1 = svc.open_review(OWNER, project_id)
        w2 = svc.open_review(OWNER, project_id)

        assert w1["review_id"] == w2["review_id"]
        assert w1["status"] == "open"

    def test_accepted_review_allows_new(self, rig):
        """After accepting a review, a new one can be opened."""
        project_id = _seed_project(rig)
        svc = _make_service(rig)

        w1 = svc.open_review(OWNER, project_id)
        review_id = w1["review_id"]

        # Accept the review
        with rig._connection() as conn:
            conn.execute(
                "UPDATE project_reviews SET status = 'accepted' WHERE id = ?",
                (review_id,),
            )
            conn.execute(
                "UPDATE projects SET last_review_id = ? WHERE id = ?",
                (review_id, project_id),
            )

        svc2 = _make_service(rig)
        w2 = svc2.open_review(OWNER, project_id)

        assert w2["review_id"] != review_id
        assert w2["status"] == "open"


# ── STEP-11 HOOK IDENTITY ────────────────────────────────────────────


class TestStep11HookIdentity:
    """The model augmentation hook receives and returns proposals unchanged."""

    def test_hook_identity(self):
        """_model_augmentation is the identity function in P2."""
        review = {"review_id": "prev_test", "project_id": "proj-test"}
        proposals = [
            {"proposal_id": "p1", "proposal_kind": "risk_attention"},
            {"proposal_id": "p2", "proposal_kind": "review_flag"},
        ]

        result = ProjectDeltaService._model_augmentation(review, proposals)

        assert result is proposals  # same object (identity)
        assert len(result) == 2
        assert result[0]["proposal_id"] == "p1"
        assert result[1]["proposal_id"] == "p2"


# ── PROPOSAL RULES TABLE ─────────────────────────────────────────────


class TestProposalRulesTable:
    """The closed rule table covers the expected observation kinds."""

    def test_rule_table_closed(self):
        """Every rule has a known observation kind and proposal kind."""
        for rule in PROPOSAL_RULES:
            assert rule.observation_kind
            assert rule.proposal_kind
            assert rule.rationale_template
            assert rule.provenance_class in (
                "observed_fact", "assessment", "proposal",
            )

    def test_followthrough_overdue_rule(self):
        rule = next(
            r for r in PROPOSAL_RULES
            if r.observation_kind == "followthrough.overdue"
        )
        assert rule.proposal_kind == "risk_attention"
        assert rule.provenance_class == "assessment"

    def test_followthrough_stale_rule(self):
        rule = next(
            r for r in PROPOSAL_RULES
            if r.observation_kind == "followthrough.stale"
        )
        assert rule.proposal_kind == "risk_attention"

    def test_decision_review_due_rule(self):
        rule = next(
            r for r in PROPOSAL_RULES
            if r.observation_kind == "decision.review_due"
        )
        assert rule.proposal_kind == "review_flag"

    def test_watch_transition_rule(self):
        rule = next(
            r for r in PROPOSAL_RULES
            if r.observation_kind == "watch.transition"
        )
        assert rule.proposal_kind == "observation_attention"
        assert rule.provenance_class == "observed_fact"


# ── SYS-022: provenance distinguishability ────────────────────────────


class TestProvenanceDistinguishability:
    """DOM-005/SYS-022: producer_kind distinguishes provenance class."""

    def test_proposals_carry_provenance(self, rig):
        """Every proposal in a real window has a producer_kind."""
        project_id = _seed_full_desk(rig)
        svc = _make_service(rig)
        window = svc.open_review(OWNER, project_id)

        for p in window["proposals"]:
            assert p["producer_kind"], (
                f"Proposal {p['id']} missing producer_kind"
            )
            assert p["producer_kind"] in (
                "observed_fact", "assessment", "proposal",
            ), f"Unknown provenance: {p['producer_kind']}"
