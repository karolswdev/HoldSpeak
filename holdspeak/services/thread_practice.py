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


def _resolve_deployment_revision(broker: Any, capability_id: str) -> str:
    """Look up the deployment revision for a capability from its assignment chain."""
    db = broker.database
    key = f"capability:{capability_id}"
    with db._connection() as conn:
        head = conn.execute(
            "SELECT assignment_id, revision FROM inference_assignment_heads "
            "WHERE assignment_key=? AND cleared=0",
            (key,),
        ).fetchone()
        if head is None:
            raise RuntimeError(f"No assignment for {capability_id}")
        entry = conn.execute(
            "SELECT profile_id FROM inference_assignments "
            "WHERE assignment_id=? AND assignment_revision=? ORDER BY ordinal LIMIT 1",
            (head["assignment_id"], head["revision"]),
        ).fetchone()
        if entry is None:
            raise RuntimeError(f"No entries in assignment for {capability_id}")
        profile_id = entry["profile_id"]
        rev = conn.execute(
            "SELECT id FROM deployment_revisions WHERE model=? LIMIT 1",
            (profile_id,),
        ).fetchone()
        if rev is None:
            raise RuntimeError(f"No deployment revision for profile {profile_id}")
        return str(rev["id"])


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
    import json as _json
    import time as _time
    from ..kernel.runtime import _as_principal

    runner = broker.inference_runner

    # Format for CanonicalPromptAdapter (system_prompt + user_prompt).
    instruction = guardrail.get("instruction", "")
    transcript_lines: list[str] = []
    for msg in messages:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        transcript_lines.append(f"[{role}]: {content}")
    for call in pending_calls:
        transcript_lines.append(
            f"[PENDING TOOL CALL]: {call.get('name', '')} — "
            f"{call.get('arguments_head', '')}"
        )
    transcript = "\n".join(transcript_lines)

    payload = {
        "thread_id": thread_id,
        "messages": messages,
        "pending_calls": pending_calls,
        "guardrail": guardrail,
        "system_prompt": (
            f"You are a guardrail evaluator. {instruction}\n"
            "Return a JSON object with keys 'violations' (list of strings) "
            "and 'warnings' (list of strings)."
        ),
        "user_prompt": transcript,
    }
    deployment_revision = _resolve_deployment_revision(broker, "chat.guardrail")

    request = InvocationRequest(
        deployment_revision=deployment_revision,
        definition_origin=ServiceContract.for_payload(
            "chat.guardrail", "1", payload,
        ),
        deadline_at=_time.time() + 120,
        payload=payload,
    )
    captured: list[Any] = []

    def _capture(value: Any) -> str:
        captured.append(value)
        return f"guardrail-result:{thread_id}"

    with _as_principal(principal):
        outcome = runner.invoke(request, CanonicalPromptAdapter(), publish=_capture)

    # Direct dict path (mocked runner).
    result = getattr(outcome, "result", None)
    if isinstance(result, dict):
        return {
            "violations": list(result.get("violations", [])),
            "warnings": list(result.get("warnings", [])),
        }

    # Real runner path: publish callback captured the adapter's result.
    if captured:
        adapter_result = captured[0]
        if isinstance(adapter_result, dict) and "output" in adapter_result:
            raw = str(adapter_result["output"])
            try:
                parsed = _json.loads(raw)
                if isinstance(parsed, dict):
                    return {
                        "violations": list(parsed.get("violations", [])),
                        "warnings": list(parsed.get("warnings", [])),
                    }
            except (ValueError, TypeError):
                pass

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
    import json as _json
    import time as _time
    from ..kernel.runtime import _as_principal

    runner = broker.inference_runner

    # Format messages into a user_prompt for CanonicalPromptAdapter.
    transcript_lines: list[str] = []
    for msg in messages:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        transcript_lines.append(f"[{role}]: {content}")
    transcript = "\n".join(transcript_lines)

    payload = {
        "thread_id": thread_id,
        "messages": messages,
        "system_prompt": (
            "Summarize the following conversation concisely. "
            "Return a JSON object with a single key 'summary' containing the summary text."
        ),
        "user_prompt": transcript,
    }
    # Resolve the deployment revision from the assignment chain.
    deployment_revision = _resolve_deployment_revision(broker, "chat.compact")

    request = InvocationRequest(
        deployment_revision=deployment_revision,
        definition_origin=ServiceContract.for_payload(
            "chat.compact", "1", payload,
        ),
        deadline_at=_time.time() + 120,
        payload=payload,
    )
    captured: list[Any] = []
    def _capture(value: Any) -> str:
        captured.append(value)
        return f"compact-result:{thread_id}"

    with _as_principal(principal):
        outcome = runner.invoke(request, CanonicalPromptAdapter(), publish=_capture)

    # Direct dict with "summary" key (mocked runner path).
    result = getattr(outcome, "result", None)
    if isinstance(result, dict) and "summary" in result:
        return {"summary": str(result["summary"])}

    # Real runner path: the publish callback captured the adapter's result.
    if captured:
        adapter_result = captured[0]
        if isinstance(adapter_result, dict) and "output" in adapter_result:
            raw = str(adapter_result["output"])
            try:
                parsed = _json.loads(raw)
                if isinstance(parsed, dict) and "summary" in parsed:
                    return {"summary": str(parsed["summary"])}
            except (ValueError, TypeError):
                pass
            if raw:
                return {"summary": raw}

    return {"summary": ""}
