# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_frozen_review.py to restore.

# ruff: noqa


# --- TestMaterialityFactors::test_outcome_relevance_risk: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_outcome_relevance_risk(self):
    assert score_outcome_relevance({"proposal_kind": "risk_attention"}) == 0.9


# --- TestMaterialityFactors::test_outcome_relevance_review: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_outcome_relevance_review(self):
    assert score_outcome_relevance({"proposal_kind": "review_flag"}) == 0.7


# --- TestMaterialityFactors::test_outcome_relevance_observation: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_outcome_relevance_observation(self):
    assert score_outcome_relevance({"proposal_kind": "observation_attention"}) == 0.5


# --- TestMaterialityFactors::test_outcome_relevance_conflict: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_outcome_relevance_conflict(self):
    assert score_outcome_relevance({"proposal_kind": "conflict"}) == 0.8


# --- TestMaterialityFactors::test_outcome_relevance_degraded: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_outcome_relevance_degraded(self):
    assert score_outcome_relevance({"proposal_kind": "coverage_degraded"}) == 0.6


# --- TestMaterialityFactors::test_outcome_relevance_unknown: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_outcome_relevance_unknown(self):
    assert score_outcome_relevance({"proposal_kind": "unknown"}) == 0.3


# --- TestMaterialityFactors::test_lifecycle_severity_overdue: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_lifecycle_severity_overdue(self):
    p = {"patch_json": '{"lane":"overdue"}'}
    assert score_lifecycle_severity(p) == 1.0


# --- TestMaterialityFactors::test_lifecycle_severity_broken: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_lifecycle_severity_broken(self):
    p = {"patch_json": '{"lifecycle":"broken"}'}
    assert score_lifecycle_severity(p) == 1.0


# --- TestMaterialityFactors::test_lifecycle_severity_at_risk: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_lifecycle_severity_at_risk(self):
    p = {"patch_json": '{"lifecycle":"at_risk"}'}
    assert score_lifecycle_severity(p) == 0.7


# --- TestMaterialityFactors::test_lifecycle_severity_active: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_lifecycle_severity_active(self):
    p = {"patch_json": '{"lifecycle":"active"}'}
    assert score_lifecycle_severity(p) == 0.3


# --- TestMaterialityFactors::test_overdue_blocked_overdue: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_overdue_blocked_overdue(self):
    p = {"proposal_kind": "risk_attention", "patch_json": '{"lane":"overdue"}'}
    assert score_overdue_blocked(p) == 1.0


# --- TestMaterialityFactors::test_overdue_blocked_stale: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_overdue_blocked_stale(self):
    p = {"patch_json": '{"stale_score":0.8}'}
    assert score_overdue_blocked(p) == 0.8


# --- TestMaterialityFactors::test_overdue_blocked_degraded: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_overdue_blocked_degraded(self):
    p = {"proposal_kind": "coverage_degraded"}
    assert score_overdue_blocked(p) == 0.8


# --- TestMaterialityFactors::test_overdue_blocked_none: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_overdue_blocked_none(self):
    p = {"proposal_kind": "review_flag"}
    assert score_overdue_blocked(p) == 0.0


# --- TestMaterialityFactors::test_decision_impact_review: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_decision_impact_review(self):
    assert score_decision_impact({"proposal_kind": "review_flag"}) == 0.8


# --- TestMaterialityFactors::test_decision_impact_conflict: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_decision_impact_conflict(self):
    assert score_decision_impact({"proposal_kind": "conflict"}) == 0.7


# --- TestMaterialityFactors::test_decision_impact_other: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_decision_impact_other(self):
    assert score_decision_impact({"proposal_kind": "risk_attention"}) == 0.1


# --- TestMaterialityFactors::test_novelty: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_novelty(self):
    assert score_novelty({}) == 0.8


# --- TestMaterialityFactors::test_evidence_confidence_observed: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_evidence_confidence_observed(self):
    assert score_evidence_confidence({"provenance_class": "observed_fact"}) == 1.0


# --- TestMaterialityFactors::test_evidence_confidence_assessment: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_evidence_confidence_assessment(self):
    assert score_evidence_confidence({"provenance_class": "assessment"}) == 0.7


# --- TestMaterialityFactors::test_evidence_confidence_proposal: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_evidence_confidence_proposal(self):
    assert score_evidence_confidence({"provenance_class": "proposal"}) == 0.5


# --- TestMaterialityFactors::test_weights_sum_to_one: P1: one lookup-table literal per test (0.9, 0.7, ...); the pinned materiality score test covers the ranking
# (was a method of class TestMaterialityFactors)
def test_weights_sum_to_one(self):
    assert abs(sum(_FACTOR_WEIGHTS.values()) - 1.0) < 1e-9


# --- TestStep11HookIdentity: P1/P8: an identity function returns its input; a rule table holds the constants it declares
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


# --- TestProposalRulesTable: P1/P8: an identity function returns its input; a rule table holds the constants it declares
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
