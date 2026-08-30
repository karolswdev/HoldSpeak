"""Chat thread practice capabilities: guardrail evaluation and compaction.

HS-153-03/05: these runner-facing entry functions admit and execute through
the adoption service exactly like AskService (non-streaming ``execute``).
Each function composes a request for its capability, invokes the runner,
and returns the structured JSON result.
"""
from __future__ import annotations

from typing import Any

from ..kernel.inference_runner import InvocationRequest, ServiceContract
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal


def run_guardrail(
    broker: Any,
    principal: Principal,
    thread_id: str,
    messages: list[dict[str, Any]],
    pending_calls: list[dict[str, Any]],
    guardrail: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate pending tool calls against an admitted guardrail.

    Returns ``{violations: [str], warnings: [str]}``.
    """
    from ..kernel.runtime import _as_principal

    runner = broker.inference_runner
    payload = {
        "thread_id": thread_id,
        "messages": messages,
        "pending_calls": pending_calls,
        "guardrail": guardrail,
    }
    request = InvocationRequest(
        deployment_revision="",
        definition_origin=ServiceContract.for_payload(
            "chat.guardrail", "1", payload,
        ),
        deadline_at=0,
        payload=payload,
    )
    with _as_principal(principal):
        outcome = runner.invoke(request, CanonicalPromptAdapter())
    result = getattr(outcome, "result", None)
    if isinstance(result, dict):
        return {
            "violations": list(result.get("violations", [])),
            "warnings": list(result.get("warnings", [])),
        }
    return {"violations": [], "warnings": []}


def run_compact(
    broker: Any,
    principal: Principal,
    thread_id: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize a chat thread prefix for compaction.

    Returns ``{summary: str}``.
    """
    from ..kernel.runtime import _as_principal

    runner = broker.inference_runner
    payload = {
        "thread_id": thread_id,
        "messages": messages,
    }
    request = InvocationRequest(
        deployment_revision="",
        definition_origin=ServiceContract.for_payload(
            "chat.compact", "1", payload,
        ),
        deadline_at=0,
        payload=payload,
    )
    with _as_principal(principal):
        outcome = runner.invoke(request, CanonicalPromptAdapter())
    result = getattr(outcome, "result", None)
    if isinstance(result, dict) and "summary" in result:
        return {"summary": str(result["summary"])}
    return {"summary": ""}
