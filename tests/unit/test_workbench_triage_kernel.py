"""HS-119-02 regression — WorkbenchTriageCodec must be registered in the kernel."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused, OperationRequest
from holdspeak.kernel.runtime import _as_principal, _configure
from holdspeak.kernel.workbench_triage import WorkbenchTriageCodec
from holdspeak.principals import Principal, PrincipalKind


AGENT = Principal(PrincipalKind.AGENT, "agent:test")


@pytest.fixture
def broker(tmp_path: Path, monkeypatch):
    import holdspeak.db.core as db_core

    database = Database(tmp_path / "triage.db")
    monkeypatch.setattr(db_core, "_db", database)
    return _configure(database)


def test_workbench_triage_codec_registered(broker):
    assert ("workbench_triage", 1) in broker._specs


def _make_request(action="accept", **overrides):
    args = {
        "workbench_id": "wb-1",
        "item_id": "wbi-1",
        "artifact_id": "art-1",
        "action": action,
    }
    args.update(overrides)
    return OperationRequest(
        request_schema=1,
        request_id="r1",
        idempotency_key="k1",
        name="workbench_triage",
        version=1,
        target_ref="artifact:art-1",
        placement="propose",
        arguments=args,
    )


def test_triage_parse_accept():
    codec = WorkbenchTriageCodec()
    admission = codec.parse(_make_request("accept"))
    assert admission.action == "accept"
    assert admission.workbench_id == "wb-1"


def test_triage_parse_reject():
    codec = WorkbenchTriageCodec()
    admission = codec.parse(_make_request("reject"))
    assert admission.action == "reject"


def test_triage_parse_rework():
    codec = WorkbenchTriageCodec()
    admission = codec.parse(_make_request("rework"))
    assert admission.action == "rework"


def test_triage_parse_rejects_invalid_action():
    codec = WorkbenchTriageCodec()
    with pytest.raises(KernelRefused):
        codec.parse(_make_request("destroy"))


def test_triage_parse_rejects_missing_fields():
    codec = WorkbenchTriageCodec()
    req = OperationRequest(
        request_schema=1,
        request_id="r1",
        idempotency_key="k1",
        name="workbench_triage",
        version=1,
        target_ref="artifact:art-1",
        placement="propose",
        arguments={"action": "accept"},
    )
    with pytest.raises(KernelRefused):
        codec.parse(req)
