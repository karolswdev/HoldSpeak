"""HS-143-09 B1/B2 — qualified routing and native adapter composition laws."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
from holdspeak.services.model_profile_service import ModelProfileService
from holdspeak.services.tool_capability_service import (
    ModelTurnCapabilityProjection,
    ToolCallCandidate,
    ToolQualification,
    ToolResultEnvelope,
    sha256,
)
from holdspeak.services.tool_model_adapter import (
    DeterministicToolModelAdapter,
    DeterministicToolModelTransport,
    ToolModelAdapterError,
    ToolModelProviderAdapter,
)
from holdspeak.services.tool_turn_controller import (
    MODEL_TURN_TOOL_PRINCIPAL,
    TOOL_TURN_AUTHORITY,
    ToolTurnRefused,
    classify_tool_turn_disposition,
)
from holdspeak.services.tool_turn_service import ToolTurnFoundationService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim
from tests.unit.test_phase143_tool_turn_controller import _descriptor, _lease, _started
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


@pytest.mark.parametrize(
    ("disposition", "limitation_allowed", "terminal", "correction", "continuation", "qualified"),
    [
        ("invalid_tool_call", False, False, True, False, True),
        ("available", False, False, False, True, True),
        # A service/network outage is typed tool evidence, not a provider error.
        ("tool_unavailable_or_stale", False, False, False, False, False),
        ("tool_unavailable_or_stale", True, False, False, True, True),
        ("permission_denied", False, True, False, False, False),
        ("policy_refused", False, True, False, False, False),
        ("approval_refused", False, True, False, False, False),
        ("owner_cancelled", False, True, False, False, False),
        ("lease_expired", False, True, False, False, False),
        ("effect_indeterminate", False, True, False, False, False),
        ("provider_permanent", False, False, False, True, True),
    ],
)
def test_ruled_tool_fallback_table_is_closed_and_never_launders_tool_events(
    disposition: str,
    limitation_allowed: bool,
    terminal: bool,
    correction: bool,
    continuation: bool,
    qualified: bool,
) -> None:
    """B3: each admissible tool-bearing disposition has one ruled outcome."""
    decision = classify_tool_turn_disposition(
        disposition, final_answer_may_name_limitation=limitation_allowed,
    )
    assert decision.terminal is terminal
    assert decision.allow_corrective_model_step is correction
    assert decision.allow_model_continuation is continuation
    assert decision.requires_tool_qualified_fallback is qualified
    with pytest.raises(ToolTurnRefused, match="tool_turn_disposition_unknown"):
        classify_tool_turn_disposition("unclassified_tool_failure")


def _qualified_started_turn(
    db: Database, *, now: list[float], turn_id: str, max_provider_steps: int = 4,
) -> ToolTurnFoundationService:
    foundation = _tool_foundation(db, now)
    _profile(
        db, "qualified-correction-model",
        claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_manifest(
            "language", _result_claim("agent.tool_turn"), "tool_turn"
        ),
    )
    _set_global_chain(
        db, command_id=f"qualified-correction-chain-{turn_id}",
        profiles=["qualified-correction-model"], foundation=foundation,
    )
    lease = _lease(_descriptor(), turn=turn_id, now=now[0])
    lease["max_provider_steps"] = max_provider_steps
    started = foundation.start(
        OWNER, command_id=f"qualified-correction-start-{turn_id}", turn_id=turn_id,
        lease_terms=lease, input_snapshot={"schema": "ToolTurnFoundationInput@1"},
        deadline_at=now[0] + 20,
    )
    assert started["status"] == "started"
    _configure(db).inference_runner._engine_factory = lambda _revision, **_kwargs: object()
    return foundation


def test_malformed_native_call_consumes_one_correction_without_tool_dispatch(tmp_path: Path) -> None:
    """B3: malformed candidates use one bounded correction; Broker sees zero calls."""
    now = [time.time()]
    db = Database(tmp_path / "malformed-native-correction.db")
    service = _qualified_started_turn(db, now=now, turn_id="correction-turn")

    def malformed_step(command: str, reference: str) -> dict[str, object]:
        step = service.stage_and_plan_model_step(
            command_id=command, turn_id="correction-turn", planning_reference=reference,
            payload={"question": "Validate native candidate", "tool_results": []},
        )
        return service.execute_model_step(
            command_id=command, turn_id="correction-turn", model_step_id=step["id"],
            model_adapter=DeterministicToolModelAdapter(),
            provider_transport=DeterministicToolModelTransport({
                "schema": "DeterministicToolModelResponse@1",
                "candidate": {"kind": "tool_call", "provider_tool_call_id": f"{command}-call",
                              "provider_call_ordinal": 1, "capability_id": "evidence.unknown_lookup",
                              "arguments": {"note_id": "note-1"}},
            }),
        )

    first = malformed_step("malformed-first", "malformed-first-material")
    assert first["tool_call"] is None
    assert first["tool_disposition"]["corrective_model_step_allowed"] is True
    assert service.controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id="correction-turn")["state"] == "tool_receipted"

    # The correction itself is another separately receipted model child. A
    # second malformed native call elects the terminal winner rather than looping.
    second = malformed_step("malformed-second", "malformed-second-material")
    assert second["tool_disposition"]["corrective_model_step_allowed"] is False
    terminal = service.controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id="correction-turn")
    assert terminal["terminal_code"] == "invalid_tool_call_correction_exhausted"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='tool.call'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 2


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


def _qualified_manifest(*claims: str, palette: int = 1) -> dict[str, object]:
    qualification = ToolQualification("qualified", palette, "hs143-tool-eval-r1", "openai")
    material: dict[str, object] = {
        "revision": "fixture-tool-v2",
        "claims": list(claims),
        "tool_qualification": qualification.to_dict(),
    }
    return {**material, "sha256": sha256(material)}


def _tool_foundation(db: Database, now: list[float]) -> ToolTurnFoundationService:
    broker = _configure(db)
    return ToolTurnFoundationService(
        broker,
        projection=ModelTurnCapabilityProjection([_descriptor()]),
        clock=lambda: now[0],
    )


def _set_global_chain(db: Database, *, command_id: str, profiles: list[str], foundation: ToolTurnFoundationService) -> None:
    InferenceAssignmentService(
        db, tool_capability_foundation=foundation._foundation
    ).set_assignment(OWNER, {
        "command_id": command_id,
        "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": profile, "profile_revision": 1} for profile in profiles],
    })


def test_required_tool_routes_filter_to_exact_qualified_deployment_only(tmp_path: Path) -> None:
    """B1/AC4: an unqualified revision remains no-tool lawful but is invisible here."""
    now = [time.time()]
    db = Database(tmp_path / "qualified-only.db")
    foundation = _tool_foundation(db, now)
    _profile(
        db, "plain-model", claims=("language", _result_claim("ask.answer")),
    )
    _profile(
        db, "tool-model",
        claims=("language", _result_claim("ask.answer"), _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=_qualified_manifest(
            "language", _result_claim("ask.answer"), _result_claim("agent.tool_turn"), "tool_turn"
        ),
    )
    _set_global_chain(db, command_id="qualified-chain", profiles=["plain-model", "tool-model"], foundation=foundation)

    plans = foundation._adoption.plans
    tool_route = plans.resolve_route_plan(
        ROUTE_PLANNING_AUTHORITY, capability_id="agent.tool_turn"
    )
    plain_route = plans.resolve_route_plan(
        ROUTE_PLANNING_AUTHORITY, capability_id="ask.answer"
    )

    assert [entry["profile_id"] for entry in tool_route["entries"]] == ["tool-model"]
    assert tool_route["entries"][0]["source_assignment_ordinal"] == 2
    assert tool_route["entries"][0]["tool_qualification"]["qualified_palette"] == 1
    assert [entry["profile_id"] for entry in plain_route["entries"]] == ["plain-model", "tool-model"]


def test_required_tool_preflight_refuses_without_qualified_profile_and_zero_children(tmp_path: Path) -> None:
    """B1/AC4: no qualified frozen deployment records a parent refusal, no egress."""
    now = [time.time()]
    db = Database(tmp_path / "no-qualified-route.db")
    foundation = _tool_foundation(db, now)
    _profile(db, "plain-model", claims=("language", _result_claim("ask.answer")))
    _set_global_chain(db, command_id="plain-global", profiles=["plain-model"], foundation=foundation)

    refused = foundation.start(
        OWNER,
        command_id="tool-parent-refusal",
        turn_id="tool-parent-refusal",
        lease_terms=_lease(_descriptor(), turn="tool-parent-refusal", now=now[0]),
        input_snapshot={"schema": "ToolTurnFoundationInput@1"},
        deadline_at=now[0] + 20,
    )

    assert refused["status"] == "refused"
    assert refused["reason_code"] == "tool_required_unavailable"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM tool_turn_tool_calls").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name IN ('inference.invoke','tool.call')").fetchone()[0] == 0


def test_frozen_qualified_manifest_cannot_retarget_after_profile_manifest_revision(tmp_path: Path) -> None:
    """B1: a later qualified manifest revision cannot alter an already frozen route."""
    now = [time.time()]
    db = Database(tmp_path / "manifest-freeze.db")
    foundation = _tool_foundation(db, now)
    initial = _qualified_manifest("language", _result_claim("agent.tool_turn"), "tool_turn")
    _profile(
        db, "tool-model", claims=("language", _result_claim("agent.tool_turn"), "tool_turn"),
        capability_manifest=initial,
    )
    _set_global_chain(db, command_id="tool-global", profiles=["tool-model"], foundation=foundation)
    frozen = foundation._adoption.plans.freeze_route_plan(
        ROUTE_PLANNING_AUTHORITY,
        command_id="freeze-tool-route",
        capability_id="agent.tool_turn",
    )

    revised = _qualified_manifest("language", _result_claim("agent.tool_turn"), "tool_turn", palette=4)
    ModelProfileService(db).create_profile(OWNER, {
        "profile_id": "tool-model", "expected_revision": 1,
        "label": "Tool Model", "provider_family": "local",
        "runtime_family": "llama_cpp_prompt_v1", "model_or_artifact_identity": "artifact-tool-model",
        "supported_modalities": ["language"], "context_support": "bounded",
        "tokenizer_template_requirements": {}, "capability_manifest": revised,
        "safe_presentation": {"summary": "Fixture"},
    })

    reconstructed = foundation._adoption.plans.get_route_plan(
        ROUTE_PLANNING_AUTHORITY, frozen["id"]
    )
    assert reconstructed["entries"][0]["profile_revision"] == 1
    assert reconstructed["entries"][0]["tool_qualification"]["sha256"] == initial["tool_qualification"]["sha256"]
    assert reconstructed["entries"][0]["tool_qualification"]["sha256"] != revised["tool_qualification"]["sha256"]


def test_tool_turn_foundation_has_one_precise_product_facade_allowlist() -> None:
    """HS-143-10 permits exactly AgentTurnService, never a broad public carve-out."""
    root = Path(__file__).resolve().parents[2]
    facade = root / "holdspeak" / "services" / "agent_turn_service.py"
    facade_text = facade.read_text(encoding="utf-8")
    assert facade_text.count("ToolTurnFoundationService") >= 2
    public_roots = [
        root / "holdspeak" / "services" / "ask_service.py",
        root / "holdspeak" / "services" / "recipe_service.py",
        root / "holdspeak" / "services" / "workbench_service.py",
        root / "holdspeak" / "services" / "workbench_runner.py",
        root / "holdspeak" / "mcp",
    ]
    offenders: list[str] = []
    for location in public_roots:
        files = [location] if location.is_file() else sorted(location.rglob("*.py"))
        for source in files:
            text = source.read_text(encoding="utf-8")
            if "tool_turn_service" in text or "ToolTurnFoundationService" in text:
                offenders.append(str(source.relative_to(root)))
    assert offenders == []
