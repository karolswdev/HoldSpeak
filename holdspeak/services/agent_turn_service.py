"""Narrow product façade for the elected HS-143-10 ToolTurn adopter.

This module is the only product-facing bridge to ``ToolTurnFoundationService``.
It validates an incoming agent turn and delegates route choice, lease enforcement,
model-step admission, tool admission, retry, and physical execution to the Story
09 foundation.  It deliberately owns none of those authorities.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from ..principals import Principal
from .errors import ValidationError
from .tool_model_adapter import ToolModelAdapter, ToolModelProviderTransport
from .tool_turn_service import ToolTurnFoundationService


class AgentTurnService:
    """Application boundary over one composed :class:`ToolTurnFoundationService`."""

    def __init__(self, foundation: ToolTurnFoundationService) -> None:
        if not isinstance(foundation, ToolTurnFoundationService):
            raise TypeError("ToolTurnFoundationService is required")
        self._foundation = foundation

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
        )
        if started["status"] == "refused":
            return {"schema": "AgentTurnResult@1", "status": "refused", "start": started, "model_step": None}
        reference = "agent-turn-material-" + hashlib.sha256(f"{command}:{turn}".encode()).hexdigest()[:24]
        step = self._foundation.stage_and_plan_model_step(
            command_id=f"{command}:model", turn_id=turn, planning_reference=reference,
            payload={"messages": clean_messages, "temperature": float(temperature), "max_tokens": max_tokens},
            reserved_output_tokens=max_tokens,
        )
        outcome = self._foundation.execute_model_step(
            command_id=f"{command}:execute", turn_id=turn, model_step_id=step["id"],
            model_adapter=model_adapter, provider_transport=provider_transport,
        )
        return {"schema": "AgentTurnResult@1", "status": "completed", "start": started, "model_step": outcome}

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
