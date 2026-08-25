"""HS-143-10 elected agent-turn production façade proof."""
from __future__ import annotations

import time
from pathlib import Path

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_turn_service import AgentTurnService
from holdspeak.services.tool_model_adapter import DeterministicToolModelAdapter, DeterministicToolModelTransport
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_phase143_tool_turn_controller import _lease
from tests.unit.test_phase143_tool_turn_routing import _descriptor, _qualified_manifest, _set_global_chain, _tool_foundation


OWNER = Principal(PrincipalKind.OWNER, "owner")


def test_agent_turn_facade_uses_foundation_route_lease_attempt_and_receipt(tmp_path: Path) -> None:
    now = [time.time()]
    db = Database(tmp_path / "agent-turn.db")
    foundation = _tool_foundation(db, now)
    _profile(
        db, "tool-model", claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_manifest("language", _result_claim("agent.tool_turn"), "tool_turn"),
    )
    _set_global_chain(db, command_id="agent-turn-route", profiles=["tool-model"], foundation=foundation)
    broker = foundation._broker
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    transport = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"summary": "one admitted answer", "tool_calls": []}},
    })

    result = AgentTurnService(foundation).run(
        OWNER, command_id="agent-turn-one", turn_id="agent-turn-one",
        lease_terms=_lease(_descriptor(), turn="agent-turn-one", now=now[0]),
        messages=[{"role": "user", "content": "Answer with the known result."}],
        deadline_at=now[0] + 20, model_adapter=DeterministicToolModelAdapter(),
        provider_transport=transport,
    )

    assert result["status"] == "completed"
    assert result["model_step"]["outcome"] == "succeeded"
    assert transport.dispatch_count == 1
    with db._connection() as conn:
        parent = conn.execute("SELECT operation_id FROM kernel_parent_runs WHERE kind='tool.turn'").fetchone()
        attempt = conn.execute("SELECT child_operation_id,child_receipt_sha256 FROM inference_route_attempts").fetchone()
        receipt = conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?", (attempt["child_operation_id"],)).fetchone()
    assert parent is not None
    assert attempt["child_operation_id"] and attempt["child_receipt_sha256"]
    assert receipt["outcome"] == "succeeded"
