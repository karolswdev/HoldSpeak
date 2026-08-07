"""Shared composition and policy helpers for the Coder steering routes."""

from __future__ import annotations

import asyncio
import re
import uuid
from typing import Any, Mapping, Optional

from fastapi.responses import JSONResponse

from ....services.coder_service import CoderService

_PANE_ID_RE = re.compile(r"^%[0-9]+$")


def canonical_pane_id(value: Any) -> Optional[str]:
    pane_id = str(value or "").strip()
    return pane_id if _PANE_ID_RE.fullmatch(pane_id) else None


def active_policy_grant(key: str) -> Optional[dict[str, Any]]:
    from .... import coder_steering

    return coder_steering.policy_grant(key)


def expected_pane_id(
    key: str,
    body: Mapping[str, Any],
    grant: Optional[Mapping[str, Any]],
) -> Optional[str]:
    supplied = canonical_pane_id(body.get("expected_pane_id"))
    if supplied:
        return supplied
    if key.startswith("pane:"):
        return canonical_pane_id(key[len("pane:") :])
    if grant:
        return canonical_pane_id(grant.get("pane_id"))
    return None


def steering_policy(
    key: str,
    pane_id: Optional[str],
    *,
    operation_kind: str,
    data_classes: tuple[str, ...],
    registered: bool,
    grant: Optional[Mapping[str, Any]] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Describe one exact pane effect and consume the central resolver."""
    from ....config import Config
    from ....operation_policy import describe_operation, resolve_policy

    operation = describe_operation(
        operation_id=f"coder:{key}:{operation_kind}",
        family="coder_steering",
        effect_class="terminal/type_text_and_keys",
        actor="owner",
        destination=pane_id or "unresolved_pane",
        data_classes=data_classes,
        resource_scope=key,
        fixed_destination=bool(registered and pane_id),
        consequence="execute_now",
    )
    decision = resolve_policy(
        operation,
        mode=Config.load().control_mode,
        source="config",
        grant=grant,
    )
    return operation.to_dict(), decision.to_dict()


def steering_commitment(
    operation: Mapping[str, Any], policy: Mapping[str, Any]
) -> dict[str, str]:
    pane = str(operation.get("destination") or "unresolved pane")
    return {
        "effect": "Send text or allowed keys",
        "destination": f"pane {pane}" if pane.startswith("%") else pane,
        "authority_basis": str(policy.get("authority_basis") or "none"),
        "next_state": str(policy.get("next_state") or "refused"),
        "receipt": "A Receipt is recorded after every attempt.",
    }


def compose_from_body(
    body: dict[str, Any], *, principal: Any, service: CoderService
) -> dict[str, Any] | JSONResponse:
    """Hydrate bounded Desk/rails grounding into the exact steer payload."""
    from ....grounding import (
        GROUNDING_EXPANDS,
        GROUNDING_MAX_REFS,
        compose_steer,
    )

    text = body.get("text")
    if not isinstance(text, str) or not text.strip():
        return JSONResponse({"error": "text is required"}, status_code=400)
    grounding = body.get("grounding")
    if grounding is None:
        return compose_steer(text, [])
    if not isinstance(grounding, dict):
        return JSONResponse({"error": "grounding must be an object"}, status_code=400)
    raw_m = grounding.get("meeting_ids")
    raw_a = grounding.get("artifact_ids")
    raw_r = grounding.get("rails")
    meeting_ids = (
        [str(item).strip() for item in raw_m if str(item).strip()]
        if isinstance(raw_m, list)
        else []
    )
    artifact_ids = (
        [str(item).strip() for item in raw_a if str(item).strip()]
        if isinstance(raw_a, list)
        else []
    )
    rails_refs = (
        [item for item in raw_r if isinstance(item, dict)]
        if isinstance(raw_r, list)
        else []
    )
    expand = str(grounding.get("expand") or "summary").strip() or "summary"
    if expand not in GROUNDING_EXPANDS:
        return JSONResponse(
            {"error": f"expand {expand!r} is not one of {list(GROUNDING_EXPANDS)}"},
            status_code=400,
        )
    if len(meeting_ids) + len(artifact_ids) + len(rails_refs) > GROUNDING_MAX_REFS:
        return JSONResponse(
            {"error": f"grounding is capped at {GROUNDING_MAX_REFS} refs"},
            status_code=400,
        )
    blocks, unknown = service.hydrate_refs(
        principal, meeting_ids, artifact_ids, expand
    )
    if rails_refs:
        from ....grounding_rails import hydrate_rails_refs

        rail_blocks, rail_unknown = hydrate_rails_refs(
            rails_refs, principal=principal
        )
        blocks = list(blocks) + rail_blocks
        unknown = list(unknown) + rail_unknown
    if unknown:
        return JSONResponse(
            {"error": "grounding ids not on this hub", "unknown_ids": unknown},
            status_code=400,
        )
    return compose_steer(text, blocks)


class ProcessInputServices:
    """Lazy shared native services for the coder route's kernel adapter."""

    def __init__(
        self,
        *,
        service: CoderService,
        commands: Any = None,
        targets: Any = None,
    ) -> None:
        self._service = service
        self._commands = commands
        self._targets = targets

    def targets(self) -> Any:
        if self._targets is None:
            from .... import coder_steering
            from ....delivery.terminal import TerminalTargetRegistry

            self._targets = TerminalTargetRegistry(
                resolver=lambda target, runner=None: coder_steering.resolve_pane_identity(
                    target, runner=runner
                )
            )
        return self._targets

    def commands(self) -> Any:
        if self._commands is None:
            self._commands = self._service.process_input_commands(self.targets())
        return self._commands


async def deliver_process_input(
    services: ProcessInputServices,
    *,
    key: str,
    target: str,
    agent: str,
    pane_id: Optional[str],
    verb: str,
    payload: Mapping[str, Any],
    policy: Mapping[str, Any],
    principal: Any,
) -> dict[str, Any]:
    """Adapt one terminal-input act onto ``process.input@1``."""
    issued = await asyncio.to_thread(services.targets().issue, target)
    command_payload = dict(payload)
    command_payload.update(
        {
            "session_key": key,
            "agent": agent,
            "expected_pane_id": pane_id or "",
        }
    )
    command = {
        "node_id": "local",
        "target_id": issued.get("target_id") or f"route_{uuid.uuid4().hex[:16]}",
        "target_generation": issued.get("target_generation") or "unresolved",
        "operation": {"family": "coder_steering", "verb": verb},
        "payload": command_payload,
    }
    adapted = await asyncio.to_thread(
        services.commands().submit_process_input,
        command,
        principal,
        authority_snapshot=policy,
        include_result=True,
    )
    result = dict(adapted.get("result") or {})
    result["operation_id"] = adapted["operation_id"]
    return result


__all__ = [
    "active_policy_grant",
    "canonical_pane_id",
    "compose_from_body",
    "deliver_process_input",
    "expected_pane_id",
    "ProcessInputServices",
    "steering_commitment",
    "steering_policy",
]
