# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_review_decisions.py to restore.

# ruff: noqa


# --- TestAcceptReview::test_envelope_correct: P1/P6: two keys are in a dict, the dict's values are in a set of three strings, and an answer's keys are non-empty
# (was a method of class TestAcceptReview)
def test_envelope_correct(self, rig) -> None:
    """accept_review returns a correct envelope."""
    db, project_svc, delta_svc = rig
    pid = _seed_project(db)
    _seed_meeting(db)
    _associate_meeting(db, pid, "m-dec01")

    review = _open_review_with_proposals(
        db, delta_svc, pid,
        observation_kinds=["followthrough.overdue"],
    )
    for p in review["proposals"]:
        if p["lifecycle"] == "open":
            kind = p["proposal_kind"]
            if HANDLER_MAP.get(kind) == "refuse":
                delta_svc.decide_proposal(
                    OWNER, pid, p["id"], "dismiss",
                )
            else:
                delta_svc.decide_proposal(
                    OWNER, pid, p["id"], "accept",
                )

    result = delta_svc.accept_review(OWNER, pid, review["review_id"])
    assert result["result_kind"] == "review_accepted"
    assert result["project_id"] == pid
    assert result["project_revision"] > 0
    assert result["review_id"] == review["review_id"]
    assert result["accepted_at"] is not None
    assert result["accepted_by_ref"] is not None


# --- TestHandlerMap::test_conflict_and_degraded_mapped: P1/P6: two keys are in a dict, the dict's values are in a set of three strings, and an answer's keys are non-empty
# (was a method of class TestHandlerMap)
def test_conflict_and_degraded_mapped(self) -> None:
    """conflict and coverage_degraded have handler entries."""
    assert "conflict" in HANDLER_MAP
    assert "coverage_degraded" in HANDLER_MAP


# --- TestHandlerMap::test_handler_map_closed: P1/P6: two keys are in a dict, the dict's values are in a set of three strings, and an answer's keys are non-empty
# (was a method of class TestHandlerMap)
def test_handler_map_closed(self) -> None:
    """The handler map only contains known actions."""
    valid_actions = {"create_item", "record_only", "refuse"}
    for kind, action in HANDLER_MAP.items():
        assert action in valid_actions, (
            f"Unknown handler action {action!r} for {kind!r}"
        )
