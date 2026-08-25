"""Internal-only ToolTurn composition service for HS-143-09 Part B.

This is deliberately not a product adopter.  It wires the server-owned
``tool.turn`` parent, its exact tool-qualified route, private evidence owner, and
ToolTurnController so the foundation can be exercised on the production broker
path before Story 10 selects a real user-facing surface.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from ..inference_capabilities import process_inference_capability_registry
from ..principals import Principal, PrincipalKind
from .errors import ValidationError
from .inference_adoption_service import ProductionRouteEvidence
from .inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY
from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
from .inference_parent_route_bundle_service import InferenceParentRouteBundleService
from .tool_capability_service import ModelTurnCapabilityProjection, ToolCapabilityFoundation
from .tool_model_adapter import ToolModelAdapter, ToolModelProviderTransport
from .tool_turn_controller import (
    BrokerToolCallPort,
    TOOL_TURN_AUTHORITY,
    ToolTurnController,
    ToolTurnRefused,
)

_TOOL_CAPABILITY = "agent.tool_turn"
_EVIDENCE_PROVIDER_ID = "tool-turn-foundation"


class ToolTurnFoundationService:
    """Composition-owned ToolTurn executor behind the narrow agent façade.

    It remains absent from public registries and browser/MCP transports; the
    elected Recipe agent turn reaches it only through ``AgentTurnService``. The
    foundation does not emulate an engine or a tool: every model step uses the
    installed ``InferenceFallbackController`` / ``InferenceRunner`` singleton
    and every tool call is admitted by the real Broker through
    :class:`BrokerToolCallPort`.
    """

    def __init__(
        self,
        broker: Any,
        *,
        projection: ModelTurnCapabilityProjection,
        clock: Any,
    ) -> None:
        adoption = getattr(broker, "inference_adoption_service", None)
        if adoption is None:
            raise ToolTurnRefused("tool_turn_route_composition_missing")
        self._broker = broker
        self._adoption = adoption
        self._controller = ToolTurnController(
            broker.database,
            projection=projection,
            clock=clock,
            route_plan_service=adoption.plans,
            fallback_controller=adoption.controller,
            model_coordinator=adoption,
            tool_broker=BrokerToolCallPort(broker),
        )
        self._foundation = ToolCapabilityFoundation(projection, self._controller)
        adoption.plans.bind_tool_capability_foundation(self._foundation)
        self._evidence = ProductionRouteEvidence(
            broker.database,
            registry=broker.inference_capability_registry,
            capability_ids=(_TOOL_CAPABILITY,),
            provider_id=_EVIDENCE_PROVIDER_ID,
        )
        self._evidence.bind_route_plan_service(adoption.plans)
        adoption.plans.register_operation_evidence_provider(self._evidence.provider())
        self._bundles = InferenceParentRouteBundleService(broker, adoption)

    @property
    def controller(self) -> ToolTurnController:
        return self._controller

    def start(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        lease_terms: Mapping[str, Any],
        input_snapshot: Mapping[str, Any],
        deadline_at: float,
        subject_kind: str | None = None,
        subject_id: str | None = None,
    ) -> dict[str, Any]:
        """Freeze a `tool.turn` parent or record its exact pre-route refusal."""
        if principal.kind is not PrincipalKind.OWNER:
            raise ToolTurnRefused("tool_turn_owner_required")
        route_declaration: dict[str, str] = {
            "key": "model", "capability_id": _TOOL_CAPABILITY,
            "invocation_id": f"tool-turn:{turn_id}",
        }
        if (subject_kind is None) != (subject_id is None):
            raise ValidationError("ToolTurn subject evidence is incomplete.", code="tool_turn_invalid")
        if subject_kind is not None and subject_id is not None:
            route_declaration.update(subject_kind=str(subject_kind), subject_id=str(subject_id))
        try:
            started = self._bundles.start(
                principal,
                command_id=command_id,
                parent_kind="tool.turn",
                definition_ref="tool.turn:foundation",
                definition_revision="1",
                input_snapshot=dict(input_snapshot),
                deadline_at=float(deadline_at),
                routes=[route_declaration],
            )
        except ValidationError as exc:
            if exc.code != "tool_required_unavailable":
                raise
            refusal = self._bundles.record_pre_route_refusal(
                principal,
                command_id=command_id,
                parent_kind="tool.turn",
                definition_ref="tool.turn:foundation",
                definition_revision="1",
                input_snapshot=dict(input_snapshot),
                deadline_at=float(deadline_at),
                reason=exc.code,
            )
            return {
                "schema": "ToolTurnFoundationStart@1", "status": "refused",
                "reason_code": exc.code, "repair": "Use an AI with tool use",
                "parent": refusal["parent"], "receipt": refusal["receipt"],
            }
        bundle = started["bundle"]
        member = bundle["members"][0]
        turn = self._controller.start(
            TOOL_TURN_AUTHORITY,
            command_id=f"{command_id}:turn",
            turn_id=turn_id,
            parent_operation_id=started["parent"].operation_id,
            parent_bundle_id=bundle["id"],
            route_plan_id=member["route_plan_id"],
            route_plan_sha256=member["route_plan_sha256"],
            lease_terms=lease_terms,
        )
        route_plan = self._adoption.plans.get_route_plan(
            ROUTE_PLANNING_AUTHORITY, str(member["route_plan_id"]),
        )
        return {
            "schema": "ToolTurnFoundationStart@1", "status": "started",
            "parent": started["parent"], "bundle": bundle, "turn": turn,
            "route_plan": route_plan,
        }

    def stage_and_plan_model_step(
        self,
        *,
        command_id: str,
        turn_id: str,
        planning_reference: str,
        payload: Mapping[str, Any],
        reserved_output_tokens: int = 32,
    ) -> dict[str, Any]:
        """Persist private immutable model material, then reserve one step."""
        digest = hashlib.sha256(f"{turn_id}:{command_id}".encode()).hexdigest()[:32]
        capability = process_inference_capability_registry().require(_TOOL_CAPABILITY)
        self._evidence.stage(
            planning_reference=planning_reference,
            capability_id=capability.id,
            operation_id=f"tool-step-{digest}",
            contract=capability.operation_contract.name,
            contract_revision=str(capability.operation_contract.version),
            payload=dict(payload),
            reserved_output_tokens=reserved_output_tokens,
        )
        return self._controller.plan_model_step(
            TOOL_TURN_AUTHORITY,
            command_id=command_id,
            turn_id=turn_id,
            planning_reference=planning_reference,
        )

    def execute_model_step(
        self,
        *,
        command_id: str,
        turn_id: str,
        model_step_id: str,
        model_adapter: ToolModelAdapter,
        provider_transport: ToolModelProviderTransport,
        publish: Any = None,
    ) -> dict[str, Any]:
        return self._controller.execute_model_step(
            TOOL_TURN_AUTHORITY,
            command_id=command_id,
            turn_id=turn_id,
            model_step_id=model_step_id,
            model_adapter=model_adapter,
            provider_transport=provider_transport,
            publish=publish,
        )

    def completed_model_step_evidence(self, model_step: Mapping[str, Any]) -> dict[str, Any]:
        """Return the controller-elected route evidence for a completed step."""
        execution_id = str(model_step.get("route_execution_id") or "")
        receipt = self._adoption.controller.get_route_execution_receipt(
            INFERENCE_FALLBACK_AUTHORITY, execution_id=execution_id,
        )
        route = self._adoption.plans.get_route_plan(
            ROUTE_PLANNING_AUTHORITY, str(receipt["route_plan_id"]),
        )
        winning = None
        if receipt.get("outcome") == "succeeded":
            winning = self._adoption._winning_reservation(
                execution_id, str(receipt["winning_attempt_id"]),
            )
        return {"route_plan": route, "receipt": receipt, "winning_reservation": winning}

    def request_stop(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        bundle_id: str,
        provenance_ref: str,
    ) -> dict[str, Any]:
        """Fence the parent route first, then elect the ToolTurn terminal winner."""
        self._bundles.fence_cancel(principal, command_id=f"{command_id}:parent", bundle_id=bundle_id)
        return self._controller.request_stop(
            TOOL_TURN_AUTHORITY,
            command_id=f"{command_id}:turn",
            turn_id=turn_id,
            provenance_ref=provenance_ref,
        )


__all__ = ["ToolTurnFoundationService"]
