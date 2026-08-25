"""HS-143-09 A5 — native adapter bridge and provider-call ordering laws."""
from __future__ import annotations

import time
from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.tool_capability_service import ToolCallCandidate, ToolResultEnvelope, sha256
from holdspeak.services.tool_model_adapter import (
    DeterministicToolModelAdapter,
    DeterministicToolModelTransport,
    ToolModelAdapterError,
    ToolModelProviderAdapter,
)
from holdspeak.services.tool_turn_controller import (
    MODEL_TURN_TOOL_PRINCIPAL,
    TOOL_TURN_AUTHORITY,
)
from tests.unit.test_phase143_tool_turn_controller import _started
from tests.unit.test_phase143_tool_turn_model_steps import _stage_step_material


def test_reference_adapter_renders_once_dispatches_once_and_parses_one_candidate() -> None:
    """ORCH-CALL 9 is a closed single exchange, not an adapter-owned loop."""
    model = DeterministicToolModelAdapter()
    transport = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "tool_call", "provider_tool_call_id": "native-call-2",
                      "provider_call_ordinal": 2, "capability_id": "evidence.note_lookup",
                      "arguments": {"note_id": "note-2"}},
    })
    bridge = ToolModelProviderAdapter(model, transport, [{
        "schema": "ModelTurnProviderTool@1", "name": "evidence.note_lookup",
        "description": "Find attached Note.",
        "parameters": {"type": "object", "additionalProperties": False,
                       "properties": {"note_id": {"type": "string"}}, "required": ["note_id"]},
    }])

    result = bridge.dispatch(object(), {"question": "one frozen question", "tool_results": []}, object())
    candidate = bridge.terminal_candidate()

    assert transport.dispatch_count == 1
    assert transport.requests == [{
        "schema": "DeterministicToolModelRequest@1",
        "request": {"question": "one frozen question", "tool_results": []},
        "tools": [{
            "schema": "ModelTurnProviderTool@1", "name": "evidence.note_lookup",
            "description": "Find attached Note.",
            "parameters": {"type": "object", "additionalProperties": False,
                           "properties": {"note_id": {"type": "string"}}, "required": ["note_id"]},
        }],
    }]
    assert candidate.to_dict()["tool_call"]["provider_call_ordinal"] == 2
    assert result["tool_calls"][0]["name"] == "evidence.note_lookup"

    malformed = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"output": "one"}, "second": {"output": "two"}},
    })
    rejected = ToolModelProviderAdapter(model, malformed, [])
    try:
        rejected.dispatch(object(), {"question": "one", "tool_results": []}, object())
    except ToolModelAdapterError:
        pass
    else:  # pragma: no cover - an exact closed candidate must fail above
        raise AssertionError("adapter accepted more than one candidate")


def _close_tool_child(db: Database, tool_call_id: str) -> str:
    """Complete the actual separately admitted Broker child before settlement."""
    broker = _configure(db)
    with db._connection() as conn:
        operation = conn.execute(
            """SELECT operation_id,revision,native_id FROM kernel_operations
                 WHERE operation_id=(SELECT broker_child_id FROM tool_turn_tool_calls WHERE id=?)""",
            (tool_call_id,),
        ).fetchone()
    broker.decide(operation["operation_id"], "approve", operation["revision"], MODEL_TURN_TOOL_PRINCIPAL)
    node = Principal(PrincipalKind.NODE, "model-turn")
    broker.claim(node, operation["native_id"])
    receipt = broker.receipt(operation["operation_id"], "succeeded", f"tool-result:{tool_call_id}", node)
    return str(receipt["receipt_id"])


def test_parallel_read_results_keep_provider_ordinal_in_durable_next_request(tmp_path: Path) -> None:
    """A5: reverse completion cannot alter durable continuation/request identity."""
    now = [time.time()]
    db = Database(tmp_path / "parallel-provider-order.db")
    controller, turn = _started(
        db, now=now, compose_model_execution=True, compose_broker=True,
    )
    # Native/provider ordinal is intentionally the reverse of admission/completion.
    second = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-provider-two", turn_id=turn,
        candidate=ToolCallCandidate("provider-call-2", "evidence.note_lookup", {"note_id": "note-2"}, 2),
    )
    first = controller.admit_tool_call(
        TOOL_TURN_AUTHORITY, command_id="admit-provider-one", turn_id=turn,
        candidate=ToolCallCandidate("provider-call-1", "evidence.note_lookup", {"note_id": "note-1"}, 1),
    )
    # They finish in the opposite provider order: 2 then 1.
    second_result = {"note_id": "note-2", "body": "second provider call"}
    controller.settle_tool_call(
        TOOL_TURN_AUTHORITY, command_id="settle-provider-two", turn_id=turn,
        tool_call_id=second["id"], receipt_id=_close_tool_child(db, second["id"]),
        envelope=ToolResultEnvelope.available(second_result), result_material=second_result,
    )
    first_result = {"note_id": "note-1", "body": "first provider call"}
    controller.settle_tool_call(
        TOOL_TURN_AUTHORITY, command_id="settle-provider-one", turn_id=turn,
        tool_call_id=first["id"], receipt_id=_close_tool_child(db, first["id"]),
        envelope=ToolResultEnvelope.available(first_result), result_material=first_result,
    )

    ordered = controller.ordered_tool_results(TOOL_TURN_AUTHORITY, turn_id=turn)
    assert [item["provider_call_ordinal"] for item in ordered["tool_results"]] == [1, 2]
    assert [item["result"] for item in ordered["tool_results"]] == [first_result, second_result]
    with db._connection() as conn:
        durable = conn.execute(
            "SELECT provider_tool_ordinal FROM tool_turn_tool_call_results WHERE turn_id=? ORDER BY provider_tool_ordinal",
            (turn,),
        ).fetchall()
    assert [row["provider_tool_ordinal"] for row in durable] == [1, 2]

    # The next *real* model step freezes these durable rows and the reference
    # adapter sees them unchanged after routing/Runner child admission.
    _stage_step_material(
        db, turn_id=turn, command_id="ordered-next-step", reference="ordered-material",
        tool_results=ordered["tool_results"],
    )
    step = controller.plan_model_step(
        TOOL_TURN_AUTHORITY, command_id="ordered-next-step", turn_id=turn,
        planning_reference="ordered-material",
    )
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    transport = DeterministicToolModelTransport({
        "schema": "DeterministicToolModelResponse@1",
        "candidate": {"kind": "answer", "answer": {"output": "ordered continuation"}},
    })
    outcome = controller.execute_model_step(
        TOOL_TURN_AUTHORITY, command_id="ordered-next-step", turn_id=turn,
        model_step_id=step["id"], model_adapter=DeterministicToolModelAdapter(),
        provider_transport=transport,
    )

    assert outcome["outcome"] == "succeeded"
    assert transport.requests[0]["request"]["tool_results"] == ordered["tool_results"]


def _next_request_identity(path: Path, completion_order: tuple[int, int]) -> tuple[str, list[int]]:
    """Build the next frozen request after either lawful completion ordering."""
    now = [time.time()]
    db = Database(path)
    controller, turn = _started(db, now=now, compose_broker=True)
    calls = {
        1: controller.admit_tool_call(
            TOOL_TURN_AUTHORITY, command_id="identity-admit-one", turn_id=turn,
            candidate=ToolCallCandidate("identity-provider-one", "evidence.note_lookup", {"note_id": "note-1"}, 1),
        ),
        2: controller.admit_tool_call(
            TOOL_TURN_AUTHORITY, command_id="identity-admit-two", turn_id=turn,
            candidate=ToolCallCandidate("identity-provider-two", "evidence.note_lookup", {"note_id": "note-2"}, 2),
        ),
    }
    materials = {
        1: {"note_id": "note-1", "body": "first provider call"},
        2: {"note_id": "note-2", "body": "second provider call"},
    }
    for ordinal in completion_order:
        call, material = calls[ordinal], materials[ordinal]
        controller.settle_tool_call(
            TOOL_TURN_AUTHORITY, command_id=f"identity-settle-{ordinal}", turn_id=turn,
            tool_call_id=call["id"], receipt_id=_close_tool_child(db, call["id"]),
            envelope=ToolResultEnvelope.available(material), result_material=material,
        )
    ordered = controller.ordered_tool_results(TOOL_TURN_AUTHORITY, turn_id=turn)
    next_request = {"question": "Frozen MODEL_TURN material", "tool_results": ordered["tool_results"]}
    return sha256(next_request), [item["provider_call_ordinal"] for item in ordered["tool_results"]]


def test_reverse_parallel_completion_has_identical_next_request_identity(tmp_path: Path) -> None:
    """Architecture §Tool-bearing fallback: completion never chooses request bytes."""
    forward_hash, forward_order = _next_request_identity(tmp_path / "forward.db", (1, 2))
    reverse_hash, reverse_order = _next_request_identity(tmp_path / "reverse.db", (2, 1))

    assert forward_order == reverse_order == [1, 2]
    assert forward_hash == reverse_hash
