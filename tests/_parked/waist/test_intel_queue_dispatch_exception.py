# PARKED 2026-11-09 (door/own-choice-park-waist): the deferred queue's model call runs through the engine door; there is no route controller settlement to fail.
# Moved from tests/integration/test_intel_queue_dispatch_exception.py; its helpers are still there.

from tests.integration.test_intel_queue_dispatch_exception import *  # noqa: F401,F403


def test_settlement_failure_projects_dispatch_intent_as_indeterminate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, library, broker = _rig(tmp_path, monkeypatch)
    _provider(library, "settlement-exception", "192.168.1.41")
    _assign(db, ["settlement-exception"], expected_revision=0)
    meeting = _meeting(db, "hs201-settlement-exception")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 settlement exception",
        planned_route=route,
    )

    calls: list[str] = []
    _engine_leaf(monkeypatch, calls, set())

    def fail_after_kernel_receipt(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("route settlement failed")

    monkeypatch.setattr(
        broker.inference_adoption_service.controller,
        "settle_attempt",
        fail_after_kernel_receipt,
    )

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert calls == ["settlement-exception"]
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    assert receipt["outcome"] == "failed"
    assert len(receipt["attempts"]) == 1
    attempt = receipt["attempts"][0]
    assert attempt["leg_ordinal"] == 1
    assert attempt["host"] == "192.168.1.41"
    assert attempt["outcome"] == "indeterminate"
    assert attempt["operation_id"]


