# PARKED 2026-11-09 (door/thought-dictation-meeting): the write-fence re-check of the Thought placement is gone: the door's pick is the one claim.
# Moved from tests/unit/test_thought_workbench_backend.py; its helpers are still there.

from tests.unit.test_thought_workbench_backend import *  # noqa: F401,F403


def test_default_same_id_readiness_change_refuses_initial_and_composite_before_writes(rig, monkeypatch):
    db, service, thought = rig
    from holdspeak.inference_targets import resolve_placement
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    target = resolve_placement(db).target
    claim = {"target_id":target.id,"target_kind":target.kind,"boundary":target.boundary,
             "engine":target.engine,"model":target.model,"readiness":target.readiness_state,
             "reason":target.readiness_reason}
    epoch = service.claim_refinement_host("default-host", "web", lease_seconds=30)
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness",
                        lambda: ("unavailable", "model disappeared"))
    with pytest.raises(ConflictError) as initial_error:
        service.reserve_refinement_with_dispatch_claim(
            OWNER, thought["id"], request_id="default-race-initial",
            expected_aggregate_revision=1, expected_working_revision=1, expected_attachment_revision=0,
            dispatch_host_id="default-host", dispatch_lease_epoch=epoch,
            admission_claim=claim, validate_current_admission=True)
    assert initial_error.value.code == "refinement_continuation_unavailable"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM refinement_invocations WHERE thought_id=?", (thought["id"],)).fetchone()[0] == 0

    review_thought = service.create(OWNER, request_id="default-race-capture", raw_text="Race", source={"kind":"typed"})
    review_id = _review(db, service, review_thought, "default-race")
    cursor = service.get_workbench(OWNER, review_thought["id"], inference_available=True)["workspace_cursor"]
    with pytest.raises(ConflictError) as composite_error:
        service.answer_and_continue_with_dispatch_claim(
            OWNER, review_thought["id"], review_id, command_id="default-race-composite",
            answer="Mina", expected_aggregate_revision=1, expected_working_revision=1,
            expected_attachment_revision=0, workspace_cursor=cursor,
            dispatch_host_id="default-host", dispatch_lease_epoch=epoch,
            admission_claim=claim, validate_current_admission=True)
    assert composite_error.value.code == "refinement_continuation_unavailable"
    assert service.get(OWNER, review_thought["id"])["working_note"]["body_markdown"] == "Race"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM refinement_answer_continue_commands").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM refinement_review_actions").fetchone()[0] == 0
