"""HS-37-05 — reference actuator end-to-end.

Drives the whole loop with the `followup_ticket_actuator`: host PROPOSES →
persisted → approved → guarded executor runs the connector → `executed` +
audit. The side effect is a real, observable file written to a temp outbox
(CI-safe — no network, no creds). The critical negatives are asserted: nothing
runs without approval, with the gate off, when not allow-listed, or without the
`actuator` capability.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.actuator_executor import (
    ActuatorExecutionError,
    ActuatorExecutor,
    ActuatorPolicyError,
)
from holdspeak.plugins.builtin.followup_ticket_actuator import (
    FollowupTicketActuator,
    build_outbox_connector,
    register_followup_actuator,
)
from holdspeak.plugins.contracts import PluginRun
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.persistence import record_actuator_proposal

ACTUATOR_ID = FollowupTicketActuator.id

_CONTEXT = {
    "meeting_title": "Onboarding sync",
    "action_items": [
        {"task": "Define the welcome screen copy", "owner": "Ana", "due": "Fri"},
        {"task": "Wire the sample project content", "owner": None, "due": None},  # unowned
    ],
}


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "ref.db")
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Onboarding sync", segments=[])
    )
    return db


def _propose(db: Database, host: PluginHost) -> str:
    """Run the actuator through the host and persist the proposal; return its id."""
    result = host.execute(
        ACTUATOR_ID,
        context=dict(_CONTEXT),
        meeting_id="m1",
        window_id="w1",
        transcript_hash="h1",
    )
    assert result.status == "proposed", result
    run = PluginRun(
        plugin_id=result.plugin_id,
        plugin_version=result.plugin_version,
        window_id="w1",
        meeting_id="m1",
        profile="balanced",
        status="proposed",
        idempotency_key=result.idempotency_key,
        started_at=0.0,
        finished_at=0.1,
        duration_ms=result.duration_ms,
        output=result.output,
    )
    record_actuator_proposal(db, run)
    proposals = db.actuators.list_proposals("m1")
    assert len(proposals) == 1
    return proposals[0].id


# ──────────────────────── The proposal is faithful ────────────────────


def test_actuator_proposes_faithful_followup() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_followup_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "proposed"
    out = result.output
    assert out["target"] == "outbox"
    assert out["action"] == "write_followup_ticket"
    # preview names the unowned task; the payload body carries it too (parity of meaning).
    assert "Wire the sample project content" in out["preview"]
    assert "Wire the sample project content" in out["payload"]["body"]
    assert out["payload"]["filename"].endswith(".md")


def test_actuator_with_nothing_to_propose_is_error_not_a_proposal() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_followup_actuator(host)
    result = host.execute(
        ACTUATOR_ID,
        context={"action_items": [{"task": "owned", "owner": "Ana"}]},  # nothing unowned
        meeting_id="m1",
        window_id="w1",
        transcript_hash="h",
    )
    assert result.status == "error"  # run() raised → no proposal, no side effect


# ──────────────────────── Capability gate (proposing) ─────────────────


def test_actuator_capability_off_blocks_proposing() -> None:
    host = PluginHost(default_timeout_seconds=1.0)  # no `actuator` capability
    register_followup_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "blocked"


# ──────────────────────── Full loop (real side effect) ────────────────


def test_full_loop_approve_execute_audit(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_followup_actuator(host)
    outbox = tmp_path / "outbox"
    connector = build_outbox_connector(outbox)

    pid = _propose(db, host)

    # Negative #1 — execute BEFORE approval: refused, no file written.
    executor = ActuatorExecutor(
        db, connector=connector, allow_actuators=True, allowed_actuator_ids=[ACTUATOR_ID]
    )
    with pytest.raises(ActuatorExecutionError):
        executor.execute(pid)
    assert not outbox.exists() or list(outbox.iterdir()) == []
    assert db.actuators.get_proposal(pid).status == "proposed"

    # Approve, then execute → the real file appears.
    db.actuators.transition_proposal(pid, to_status="approved", actor="karol")
    executed = executor.execute(pid)

    assert executed.status == "executed"
    written_path = executed.result["path"]
    from pathlib import Path

    assert Path(written_path).exists()  # the observable external side effect
    content = Path(written_path).read_text()
    assert "Wire the sample project content" in content

    audit = db.actuators.list_audit(pid)
    assert [a.to_status for a in audit] == ["proposed", "approved", "executed"]


# ──────────────────────── Negative: gate / allow-list ─────────────────


def test_gate_off_means_no_side_effect(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_followup_actuator(host)
    outbox = tmp_path / "outbox"
    connector = build_outbox_connector(outbox)
    pid = _propose(db, host)
    db.actuators.transition_proposal(pid, to_status="approved")

    # allow_actuators OFF → refused, no file.
    with pytest.raises(ActuatorPolicyError):
        ActuatorExecutor(db, connector=connector, allow_actuators=False).execute(pid)
    assert not outbox.exists() or list(outbox.iterdir()) == []
    assert db.actuators.get_proposal(pid).status == "approved"


def test_not_allow_listed_means_no_side_effect(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_followup_actuator(host)
    outbox = tmp_path / "outbox"
    connector = build_outbox_connector(outbox)
    pid = _propose(db, host)
    db.actuators.transition_proposal(pid, to_status="approved")

    with pytest.raises(ActuatorPolicyError):
        ActuatorExecutor(
            db, connector=connector, allow_actuators=True, allowed_actuator_ids=["other"]
        ).execute(pid)
    assert not outbox.exists() or list(outbox.iterdir()) == []


# ──────────────────────── Default set unaffected ──────────────────────


def test_reference_actuator_not_in_default_builtins() -> None:
    from holdspeak.plugins.builtin import register_builtin_plugins

    host = PluginHost(default_timeout_seconds=1.0)
    registered = register_builtin_plugins(host)
    assert ACTUATOR_ID not in registered  # gated/opt-in, never in the default set
