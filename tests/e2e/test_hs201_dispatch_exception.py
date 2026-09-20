"""HS-201 follow-up: retain durable dispatch evidence on queue exceptions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.kernel.model import KernelRefused
from holdspeak.services.meeting_route_projection import project_route
from tests.e2e.test_hs201_route_execution import (
    _assign,
    _engine_leaf,
    _meeting,
    _provider,
    _rig,
)


pytestmark = pytest.mark.timeout(90, method="signal")


def test_finalize_failure_keeps_the_contacted_host_in_the_public_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, library, broker = _rig(tmp_path, monkeypatch)
    _provider(library, "dispatch-exception", "192.168.1.40")
    _assign(db, ["dispatch-exception"], expected_revision=0)
    meeting = _meeting(db, "hs201-dispatch-exception")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 dispatch exception",
        planned_route=route,
    )

    calls: list[str] = []
    _engine_leaf(monkeypatch, calls, set())

    def fail_after_provider(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("projection finalization failed")

    monkeypatch.setattr(broker.projection_stager, "finalize", fail_after_provider)

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert calls == ["dispatch-exception"]
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    assert receipt["outcome"] == "failed"
    assert len(receipt["attempts"]) == 1
    attempt = receipt["attempts"][0]
    assert attempt["leg_ordinal"] == 1
    assert attempt["host"] == "192.168.1.40"
    assert attempt["outcome"] == "succeeded"
    assert attempt["operation_id"]


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


def test_pre_send_refusal_keeps_the_receipt_empty_and_does_not_call_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db, library, broker = _rig(tmp_path, monkeypatch)
    _provider(library, "presend-refusal", "192.168.1.42")
    _assign(db, ["presend-refusal"], expected_revision=0)
    meeting = _meeting(db, "hs201-presend-refusal")
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    db.intel.enqueue_intel_job(
        meeting.id,
        transcript_hash=meeting.transcript_hash(),
        reason="HS-201 pre-send refusal",
        planned_route=route,
    )

    calls: list[str] = []
    _engine_leaf(monkeypatch, calls, set())

    def refuse_before_provider(*_args: Any, **_kwargs: Any) -> None:
        raise KernelRefused("fixture_pre_send_refusal")

    monkeypatch.setattr(broker.inference_runner, "_engine_factory", refuse_before_provider)

    from holdspeak.intel_queue import process_next_intel_job

    assert process_next_intel_job() is True
    assert calls == []
    receipt = db.intel.get_run_receipt(meeting.id)
    assert receipt is not None
    assert receipt["outcome"] == "refused"
    assert receipt["attempts"] == []
