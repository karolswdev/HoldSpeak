"""HS-37-04 — guarded actuator executor tests.

The executor is where the side effect happens, so it's where the invariant is
enforced: only an approved proposal executes, the governance gate holds, what
executes equals what was approved (payload parity), every terminal state is
audited, and egress goes through an injected connector (a stub here — the
default suite makes no real outbound call).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.actuator_authority import authority_binding
from holdspeak.plugins.actuator_executor import (
    ActuatorExecutionError,
    ActuatorExecutor,
    ActuatorPolicyError,
)


class _SpyConnector:
    """Records calls and returns a canned result (or raises)."""

    def __init__(self, *, raises: bool = False):
        self.calls = []
        self._raises = raises

    def __call__(self, proposal):
        self.calls.append(proposal)
        if self._raises:
            raise RuntimeError("connector boom")
        return {"url": "https://example.test/issues/1", "target": proposal.target}


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "exec.db")
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="t", segments=[])
    )
    return db


def _approved(db: Database, *, key="k1", plugin_id="followup_ticket_actuator"):
    p = db.actuators.record_proposal(
        meeting_id="m1",
        window_id="w1",
        plugin_id=plugin_id,
        plugin_version="1.0.0",
        idempotency_key=key,
        target="github",
        action="create_issue",
        preview="Open a follow-up issue",
        payload={"repo": "acme/app", "title": "Follow up"},
        reversible=True,
        required_capabilities=["actuator"],
    )
    return db.actuators.transition_proposal(p.id, to_status="approved", actor="karol")


# ──────────────────────────── Happy path ──────────────────────────────


def test_execute_approved_proposal(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db)
    connector = _SpyConnector()
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(proposal.id)

    assert result.status == "executed"
    assert result.executed_at is not None
    assert result.result == {"url": "https://example.test/issues/1", "target": "github"}
    assert len(connector.calls) == 1
    # The connector saw the stored payload (source of truth), not caller input.
    assert connector.calls[0].payload == {"repo": "acme/app", "title": "Follow up"}

    # Audited: the executed transition is on the audit trail.
    audit = db.actuators.list_audit(proposal.id)
    assert audit[-1].to_status == "executed"
    assert "payload" in (audit[-1].detail or "")


# ──────────────────────────── Status gate ─────────────────────────────


@pytest.mark.parametrize("status", ["proposed", "rejected", "executed"])
def test_only_approved_executes(tmp_path, status) -> None:
    db = _db(tmp_path)
    p = db.actuators.record_proposal(
        meeting_id="m1", window_id="w1", plugin_id="a", plugin_version="1.0.0",
        idempotency_key="k", target="t", action="x", preview="p", payload={},
    )
    # Drive to the requested non-approved state.
    if status == "rejected":
        db.actuators.transition_proposal(p.id, to_status="rejected")
    elif status == "executed":
        db.actuators.transition_proposal(p.id, to_status="approved")
        db.actuators.transition_proposal(p.id, to_status="executed")
    connector = _SpyConnector()
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    with pytest.raises(ActuatorExecutionError):
        executor.execute(p.id)
    assert connector.calls == []  # no outbound call


# ──────────────────────────── Policy gate ─────────────────────────────


def test_master_gate_off_refuses_without_state_change(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db)
    connector = _SpyConnector()
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=False)

    with pytest.raises(ActuatorPolicyError):
        executor.execute(proposal.id)
    assert connector.calls == []
    # State unchanged — operator can enable the gate and retry.
    assert db.actuators.get_proposal(proposal.id).status == "approved"


def test_allow_list_blocks_unlisted_actuator(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db, plugin_id="some_actuator")
    connector = _SpyConnector()
    executor = ActuatorExecutor(
        db, connector=connector, allow_actuators=True, allowed_actuator_ids=["other_actuator"]
    )

    with pytest.raises(ActuatorPolicyError):
        executor.execute(proposal.id)
    assert connector.calls == []
    assert db.actuators.get_proposal(proposal.id).status == "approved"


def test_allow_list_permits_listed_actuator(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db, plugin_id="some_actuator")
    connector = _SpyConnector()
    executor = ActuatorExecutor(
        db, connector=connector, allow_actuators=True, allowed_actuator_ids=["some_actuator"]
    )
    result = executor.execute(proposal.id)
    assert result.status == "executed"
    assert len(connector.calls) == 1


# ─────────────────────────── Authority parity ─────────────────────────


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("payload_json", '{"repo":"other/repo","title":"Follow up"}'),
        ("target", "slack"),
        ("action", "delete_issue"),
        ("preview", "Delete the issue"),
        ("approved_payload_hash", "deadbeef" * 8),
        ("approved_destination", "github:sha256:changed"),
        ("approved_preview_hash", "deadbeef" * 8),
        ("preview_renderer_version", "actuator-preview/v0"),
        ("effect_class", "github/delete_issue"),
        ("policy_version", "actuator-policy/v0"),
    ],
)
def test_any_authority_change_aborts_to_failed_no_call(tmp_path, column, value) -> None:
    db = _db(tmp_path)
    proposal = _approved(db)
    with sqlite3.connect(db.db_path) as conn:
        conn.execute(
            f"UPDATE actuator_proposals SET {column} = ? WHERE id = ?",
            (value, proposal.id),
        )
    connector = _SpyConnector()
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(proposal.id)

    assert result.status == "failed"
    assert "authority" in (result.error or "").lower()
    assert connector.calls == []
    audit = db.actuators.list_audit(proposal.id)
    assert audit[-1].to_status == "failed"


def test_approval_records_complete_authority_binding(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db)
    expected = authority_binding(
        target=proposal.target,
        action=proposal.action,
        preview=proposal.preview,
        payload=proposal.payload,
    )
    assert proposal.approved_payload_hash == expected.payload_hash
    assert proposal.approved_destination == expected.normalized_destination
    assert proposal.approved_preview_hash == expected.preview_hash
    assert proposal.preview_renderer_version == expected.preview_renderer_version
    assert proposal.effect_class == expected.effect_class
    assert proposal.policy_version == expected.policy_version
    assert "authority bound" in (db.actuators.list_audit(proposal.id)[-1].detail or "")


def test_missing_legacy_binding_fails_closed(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db)
    with sqlite3.connect(db.db_path) as conn:
        conn.execute(
            "UPDATE actuator_proposals SET approved_payload_hash = NULL WHERE id = ?",
            (proposal.id,),
        )
    connector = _SpyConnector()
    result = ActuatorExecutor(
        db, connector=connector, allow_actuators=True
    ).execute(proposal.id)
    assert result.status == "failed"
    assert connector.calls == []


# ──────────────────────────── Connector failure ───────────────────────


def test_connector_error_marks_failed_and_audits(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db)
    connector = _SpyConnector(raises=True)
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(proposal.id)

    assert result.status == "failed"
    assert "boom" in (result.error or "")
    assert len(connector.calls) == 1  # it tried
    audit = db.actuators.list_audit(proposal.id)
    assert audit[-1].to_status == "failed"
    # Retryable: failed -> approved -> executed.
    db.actuators.transition_proposal(proposal.id, to_status="approved")
    ok = ActuatorExecutor(db, connector=_SpyConnector(), allow_actuators=True).execute(proposal.id)
    assert ok.status == "executed"


def test_unknown_proposal_raises(tmp_path) -> None:
    db = _db(tmp_path)
    executor = ActuatorExecutor(db, connector=_SpyConnector(), allow_actuators=True)
    with pytest.raises(KeyError):
        executor.execute("nope")


# ──────────────── Policy config (MeetingConfig home) ───────────────────


def test_config_actuator_policy_defaults_safe() -> None:
    from holdspeak.config import MeetingConfig

    cfg = MeetingConfig()
    assert cfg.allow_actuators is False
    assert cfg.allowed_actuators == []


def test_config_allowed_actuators_normalized() -> None:
    from holdspeak.config import MeetingConfig

    cfg = MeetingConfig(allowed_actuators=[" followup ", "followup", "", "poster"])
    assert cfg.allowed_actuators == ["followup", "poster"]


def test_config_allowed_actuators_rejects_non_list() -> None:
    from holdspeak.config import MeetingConfig

    with pytest.raises(ValueError, match="allowed_actuators"):
        MeetingConfig(allowed_actuators="followup")  # type: ignore[arg-type]
