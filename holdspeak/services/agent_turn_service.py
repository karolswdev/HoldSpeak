"""Narrow product façade for the elected HS-143-10 ToolTurn adopter.

This module is the only product-facing bridge to ``ToolTurnFoundationService``.
It validates an incoming agent turn and delegates route choice, lease enforcement,
model-step admission, tool admission, retry, and physical execution to the Story
09 foundation.  It deliberately owns none of those authorities.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Mapping, Sequence

from ..principals import Principal
from .errors import ValidationError
from .tool_capability_service import CanonicalApplicationOperationDescriptor, ModelTurnCapabilityProjection
from .tool_model_adapter import ToolModelAdapter, ToolModelAnswerCandidate, ToolModelProviderTransport
from .tool_turn_service import ToolTurnFoundationService


class _PromptToolModelAdapter:
    """Native-tool bridge for the local text engine's answer-only first leg.

    The engine boundary remains the sole physical transport. A text response is
    represented as the closed no-tool candidate; it can never manufacture a tool
    name from a Recipe record or from the browser.
    """

    def render(self, frozen_request: Mapping[str, Any], provider_tools: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
        return {"messages": list(frozen_request["messages"]), "temperature": frozen_request.get("temperature", 0.2), "max_tokens": frozen_request.get("max_tokens", 800), "tools": list(provider_tools)}

    def parse(self, response: Mapping[str, Any]) -> ToolModelAnswerCandidate:
        return ToolModelAnswerCandidate({"summary": str(response.get("output") or ""), "tool_calls": []})


class _PromptToolProviderTransport:
    """The one physical local-engine request; no tool retry or fallback loop."""

    def dispatch(self, engine: Any, request: Mapping[str, Any], _cancellation: Any) -> Mapping[str, Any]:
        messages = [dict(item) for item in request["messages"]]
        system = "\n\n".join(str(item["content"]) for item in messages if item.get("role") == "system")
        user = "\n\n".join(str(item["content"]) for item in messages if item.get("role") != "system")
        return {"output": engine.run_prompt(system_prompt=system, user_prompt=user, temperature=float(request["temperature"]), max_tokens=int(request["max_tokens"]))}

    def cancel(self) -> str:
        return "cancelled"


class AgentTurnService:
    """Application boundary over one composed :class:`ToolTurnFoundationService`."""

    def __init__(self, foundation: ToolTurnFoundationService) -> None:
        if not isinstance(foundation, ToolTurnFoundationService):
            raise TypeError("ToolTurnFoundationService is required")
        self._foundation = foundation

    @classmethod
    def compose(cls, broker: Any) -> "AgentTurnService":
        """Install exactly one broker-owned product façade and its foundation."""
        existing = getattr(broker, "agent_turn_service", None)
        if isinstance(existing, cls):
            return existing
        descriptor = CanonicalApplicationOperationDescriptor(
            capability_id="evidence.note_lookup", revision=1,
            label="Find attached Note", description="Read one attached Note.",
            argument_schema={"type": "object", "additionalProperties": False, "properties": {"note_id": {"type": "string"}}, "required": ["note_id"]},
            service_operation="note.lookup", capability_class="evidence_read", effect_mode="read",
            allowed_data_classes=("note",), allowed_placements=("local", "private_network", "mesh", "cloud"),
            allowed_egress=("local", "private_network", "mesh", "cloud"), max_calls=1,
            max_result_bytes=1024, max_result_tokens=256, commutative_read=True,
        )
        foundation = ToolTurnFoundationService(
            broker, projection=ModelTurnCapabilityProjection([descriptor]), clock=time.time,
        )
        service = cls(foundation)
        service._recipe_descriptor = descriptor
        broker.tool_turn_foundation = foundation
        broker.agent_turn_service = service
        return service

    def run_recipe(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        recipe_id: str,
        messages: Sequence[Mapping[str, str]],
        deadline_at: float,
        publish: Any,
        max_tokens: int = 512,
    ) -> dict[str, Any]:
        """Run the elected Recipe surface using only server-owned route evidence."""
        descriptor = getattr(self, "_recipe_descriptor", None)
        if not isinstance(descriptor, CanonicalApplicationOperationDescriptor):
            raise ValidationError("Recipe ToolTurn composition is unavailable.", code="agent_turn_unavailable")
        lease_id = hashlib.sha256(f"{command_id}:{turn_id}".encode()).hexdigest()[:24]
        lease_terms = {
            "schema": "TurnCapabilityLease@1", "lease_id": f"lease-{lease_id}", "nonce": f"nonce-{lease_id}",
            "epoch": 1, "parent_turn_id": turn_id, "owner_principal_id": principal.identity,
            "deployment_revision": "route-frozen", "operation_kind": "recipe.chat", "operation_revision": "1",
            "owner_intent_receipt_id": None, "policy_revision": "recipe-qualified-manifest-1",
            "capabilities": [{
                "capability_id": descriptor.capability_id, "capability_revision": descriptor.revision,
                "descriptor_sha256": descriptor.descriptor_sha256, "schema_sha256": descriptor.schema_sha256,
                "service_operation": descriptor.service_operation, "class": "evidence_read", "effect_mode": "read",
                "scope": {"attached": True}, "data_classes": ["note"],
                "placement": ["local", "private_network", "mesh", "cloud"],
                "egress": ["local", "private_network", "mesh", "cloud"], "max_calls": 1,
                "max_result_bytes": 1024, "max_result_tokens": 256, "commutative_read": True,
            }],
            "max_provider_steps": 1, "max_tool_calls": 0, "max_effect_proposals": 0,
            "max_parallel_reads": 0, "aggregate_result_bytes": 0, "aggregate_result_tokens": 0,
            "wall_deadline": deadline_at, "expires_at": deadline_at,
        }
        return self.run(
            principal, command_id=command_id, turn_id=turn_id, lease_terms=lease_terms,
            messages=messages, deadline_at=deadline_at, model_adapter=_PromptToolModelAdapter(),
            provider_transport=_PromptToolProviderTransport(), max_tokens=max_tokens,
            subject_kind="recipe", subject_id=recipe_id, publish_factory=publish,
        )

    def run(
        self,
        principal: Principal,
        *,
        command_id: str,
        turn_id: str,
        lease_terms: Mapping[str, Any],
        messages: Sequence[Mapping[str, str]],
        deadline_at: float,
        model_adapter: ToolModelAdapter,
        provider_transport: ToolModelProviderTransport,
        temperature: float = 0.2,
        max_tokens: int = 800,
        subject_kind: str | None = None,
        subject_id: str | None = None,
        publish: Any = None,
        publish_factory: Any = None,
    ) -> dict[str, Any]:
        """Run one application turn through the real foundation ledger.

        ``lease_terms`` comes from the composed qualification/admission layer, not
        from a browser or plugin.  The façade only carries the bounded prompt into
        the foundation's private operation material.
        """
        clean_messages = self._messages(messages)
        command = self._id(command_id, "command_id")
        turn = self._id(turn_id, "turn_id")
        if type(max_tokens) is not int or not 1 <= max_tokens <= 16384:
            raise ValidationError("agent turn max_tokens is invalid", code="agent_turn_invalid")
        if not isinstance(temperature, (int, float)):
            raise ValidationError("agent turn temperature is invalid", code="agent_turn_invalid")
        started = self._foundation.start(
            principal, command_id=command, turn_id=turn, lease_terms=lease_terms,
            input_snapshot={"messages": clean_messages}, deadline_at=float(deadline_at),
            subject_kind=subject_kind, subject_id=subject_id,
        )
        if started["status"] == "refused":
            return {"schema": "AgentTurnResult@1", "status": "refused", "start": started, "model_step": None}
        reference = "agent-turn-material-" + hashlib.sha256(f"{command}:{turn}".encode()).hexdigest()[:24]
        step = self._foundation.stage_and_plan_model_step(
            command_id=f"{command}:model", turn_id=turn, planning_reference=reference,
            payload={"messages": clean_messages, "temperature": float(temperature), "max_tokens": max_tokens},
            reserved_output_tokens=max_tokens,
        )
        step_publish = publish if publish_factory is None else publish_factory(started["route_plan"])
        outcome = self._foundation.execute_model_step(
            command_id=f"{command}:execute", turn_id=turn, model_step_id=step["id"],
            model_adapter=model_adapter, provider_transport=provider_transport,
            publish=step_publish,
        )
        evidence = self._foundation.completed_model_step_evidence(outcome["model_step"])
        return {
            "schema": "AgentTurnResult@1", "status": "completed", "start": started,
            "model_step": outcome, "outcome": outcome["outcome"], **evidence,
        }

    @classmethod
    def dispatch_plugin(
        cls,
        dispatch: Any,
        messages: Sequence[dict[str, str]],
        *,
        temperature: float,
        max_tokens: int,
        plugin_id: str,
    ) -> str:
        """Consume an already-admitted legacy handle at the sole façade seam.

        A handle predating the ToolTurn contract is itself one exact Runner child
        and has no qualified palette to turn into a ToolTurn.  Its compatibility
        completion is kept at this *single* application façade, never in
        ``PluginDispatch``. Qualified product turns use :meth:`run`, which enters
        the ToolTurn foundation and creates its own route/controller receipt.
        """
        # The one-shot authority fence belongs to PluginDispatch itself.  This
        # compatibility leaf receives an already validated and claimed handle so
        # a pre-dispatch refusal cannot be misreported as a provider failure.
        engine = dispatch._engine
        result = engine._chat_completion_text(
            list(messages), temperature=float(temperature), max_tokens=int(max_tokens)
        )
        return result if isinstance(result, str) else str(result or "")

    @staticmethod
    def _id(value: Any, field: str) -> str:
        clean = str(value or "").strip()
        if not clean or len(clean) > 192 or not clean.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValidationError(f"agent turn {field} is invalid", code="agent_turn_invalid")
        return clean

    @staticmethod
    def _messages(value: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not 1 <= len(value) <= 64:
            raise ValidationError("agent turn messages are invalid", code="agent_turn_invalid")
        result: list[dict[str, str]] = []
        for item in value:
            if not isinstance(item, Mapping) or set(item) != {"role", "content"}:
                raise ValidationError("agent turn messages are invalid", code="agent_turn_invalid")
            role, content = str(item["role"]), str(item["content"])
            if role not in {"system", "user", "assistant", "tool"} or not content or len(content) > 24000:
                raise ValidationError("agent turn messages are invalid", code="agent_turn_invalid")
            result.append({"role": role, "content": content})
        return result


__all__ = ["AgentTurnService"]
