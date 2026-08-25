"""HS-143-09 A4 — real durable boundaries survive process reconstruction."""
from __future__ import annotations

import time
from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.tool_capability_service import ModelTurnCapabilityProjection, ToolCallCandidate
from holdspeak.services.tool_turn_controller import (
    BrokerToolCallPort,
    MODEL_TURN_TOOL_PRINCIPAL,
    TOOL_TURN_AUTHORITY,
    ToolTurnController,
)
from tests.unit.test_phase143_tool_turn_controller import (
    _effect_descriptor,
    _effect_lease,
    _started,
)


def _restart(db: Database, *, descriptor, now: list[float]) -> ToolTurnController:
    """A new production controller object reads no mutable owner route state."""
    return ToolTurnController(
        db, projection=ModelTurnCapabilityProjection([descriptor]), clock=lambda: now[0],
        tool_broker=BrokerToolCallPort(_configure(db)),
    )


def test_restart_adopts_known_effect_receipt_never_reexecutes_it(tmp_path: Path) -> None:
    now = [time.time()]
    descriptor = _effect_descriptor()
    db = Database(tmp_path / "known-effect-restart.db")
    controller, turn = _started(
        db, now=now, compose_broker=True, descriptor=descriptor,
        lease_terms=_effect_lease(descriptor, turn="turn-1", now=now[0]),
    )
    call = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="boundary-effect", turn_id=turn,
        candidate=ToolCallCandidate("boundary-effect-call", descriptor.capability_id, {"note_id": "note-1"}),
    )
    broker = _configure(db)
    with db._connection() as conn:
        operation = conn.execute(
            "SELECT operation_id,revision,native_id FROM kernel_operations WHERE operation_id=(SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?)",
            (call["id"],),
        ).fetchone()
    broker.decide(operation["operation_id"], "approve", operation["revision"], MODEL_TURN_TOOL_PRINCIPAL)
    node = Principal(PrincipalKind.NODE, "model-turn")
    broker.claim(node, operation["native_id"])
    broker.receipt(operation["operation_id"], "succeeded", "effect:note-1", node)

    restarted = _restart(db, descriptor=descriptor, now=now)
    assert restarted.reconstruct(TOOL_TURN_AUTHORITY, turn_id=turn)["state"] == "tool_receipted"
    adopted = restarted.reconcile_effect_child(TOOL_TURN_AUTHORITY, turn_id=turn, tool_call_id=call["id"])
    assert adopted["state"] == "adopted"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 1


def test_restart_unknown_effect_completion_elects_terminal_without_model_egress(tmp_path: Path) -> None:
    now = [time.time()]
    descriptor = _effect_descriptor()
    db = Database(tmp_path / "unknown-effect-restart.db")
    controller, turn = _started(
        db, now=now, compose_broker=True, descriptor=descriptor,
        lease_terms=_effect_lease(descriptor, turn="turn-1", now=now[0]),
    )
    call = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="boundary-unknown", turn_id=turn,
        candidate=ToolCallCandidate("boundary-unknown-call", descriptor.capability_id, {"note_id": "note-2"}),
    )
    restarted = _restart(db, descriptor=descriptor, now=now)
    terminal = restarted.reconcile_effect_child(TOOL_TURN_AUTHORITY, turn_id=turn, tool_call_id=call["id"])
    assert terminal["state"] == "indeterminate"
    assert restarted.reconstruct(TOOL_TURN_AUTHORITY, turn_id=turn)["terminal_code"] == "effect_indeterminate"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        assert conn.execute("SELECT state FROM tool_turn_effect_children").fetchone()[0] == "indeterminate"
