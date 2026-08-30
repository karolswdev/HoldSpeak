"""Chat thread practice capabilities: guardrail evaluation and compaction.

HS-153-03/05: these runner-facing entry functions admit and execute through
the adoption service exactly like AskService (non-streaming ``execute``).
Each function composes a request for its capability, invokes the runner,
and returns the structured JSON result.
"""
from __future__ import annotations

import json as _json
import re as _re
from typing import Any

from ..kernel.inference_runner import InvocationRequest, ServiceContract
from ..kernel.prompt_adapter import CanonicalPromptAdapter
from ..principals import Principal


# HS-153-06: robust structured-output extraction for models that wrap JSON in
# think-blocks, markdown fences, or trailing prose (Qwen3.6 on .43).
_THINK_RE = _re.compile(r"<think>.*?</think>", _re.DOTALL)
_FENCE_RE = _re.compile(r"```(?:json)?\s*(.*?)\s*```", _re.DOTALL)


def _extract_structured_json(raw: str) -> dict[str, Any] | None:
    """Best-effort extraction of a JSON object from an LLM response.

    Strips ``<think>...</think>`` blocks (Qwen reasoning traces), tries
    markdown-fenced JSON first, then scans for the first balanced ``{...}``
    substring. Returns ``None`` when no valid JSON dict is found.
    """
    if not raw:
        return None
    # Strip reasoning traces.
    cleaned = _THINK_RE.sub("", raw).strip()
    # Try markdown-fenced JSON first.
    fence = _FENCE_RE.search(cleaned)
    if fence:
        try:
            obj = _json.loads(fence.group(1))
            if isinstance(obj, dict):
                return obj
        except (ValueError, TypeError):
            pass
    # Scan for first balanced {...} in the cleaned text.
    depth = 0
    start = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    obj = _json.loads(cleaned[start : i + 1])
                    if isinstance(obj, dict):
                        return obj
                except (ValueError, TypeError):
                    pass
                start = -1
    return None


def _resolve_deployment_revision(broker: Any, capability_id: str) -> tuple[str, str]:
    """Look up the deployment revision AND boundary for a capability.

    Returns ``(deployment_revision_id, boundary)`` where *boundary* is the
    ``deployment_revisions.boundary`` column value (e.g. ``"same_device"``,
    ``"cloud"``, ``"external_service"``).

    HS-153 close counsel M1: the boundary is needed so the caller can apply
    M1 redaction scoped to THIS capability's egress, not the chat.turn
    thread egress.
    """
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
            "SELECT id, boundary FROM deployment_revisions WHERE model=? LIMIT 1",
            (profile_id,),
        ).fetchone()
        if rev is None:
            raise RuntimeError(f"No deployment revision for profile {profile_id}")
        return str(rev["id"]), str(rev["boundary"] or "")


def run_guardrail(
    broker: Any,
    principal: Principal,
    thread_id: str,
    messages: list[dict[str, Any]],
    pending_calls: list[dict[str, Any]],
    guardrail: dict[str, Any],
    *,
    sensitive_texts: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate pending tool calls against an admitted guardrail.

    Returns ``{violations: [str], warnings: [str]}``.

    *sensitive_texts*: when provided, these are People-sensitive strings
    that must be redacted if the chat.guardrail capability routes through
    a cloud boundary (HS-153 close counsel M1).
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

    payload: dict[str, Any] = {
        "thread_id": thread_id,
        "messages": messages,
        "pending_calls": pending_calls,
        "guardrail": guardrail,
        "system_prompt": (
            "You are a guardrail evaluator.\n\n"
            f"RULE: {instruction}\n\n"
            "For each PENDING TOOL CALL below, check the RULE.\n"
            "If a call violates the rule, add a one-sentence explanation to "
            "the violations list.\n"
            "If no call violates the rule, the violations list is empty.\n\n"
            "Respond with ONLY a JSON object:\n"
            '{"violations": ["..."], "warnings": ["..."]}'
        ),
        "user_prompt": transcript,
        # HS-153-06: json_schema response_format constrains the output to the
        # exact guardrail schema.  The engine's grammar:"" override clears any
        # server-side default grammar so this schema takes effect.  The robust
        # parser stays as belt-and-suspenders.
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "guardrail",
                "schema": {
                    "type": "object",
                    "properties": {
                        "violations": {"type": "array", "items": {"type": "string"}},
                        "warnings": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["violations", "warnings"],
                },
            },
        },
    }
    if sensitive_texts:
        payload["_sensitive_texts"] = list(sensitive_texts)
    deployment_revision, boundary = _resolve_deployment_revision(broker, "chat.guardrail")

    # HS-153 close counsel M1: apply M1 redaction based on the CAPABILITY's
    # own boundary, not the thread's chat.turn egress scope.
    if boundary in ("cloud", "external_service"):
        sensitive_texts = payload.get("_sensitive_texts", [])
        if sensitive_texts:
            redacted_messages: list[dict[str, Any]] = []
            for msg_dict in payload.get("messages", []):
                if not isinstance(msg_dict, dict):
                    redacted_messages.append(msg_dict)
                    continue
                content = str(msg_dict.get("content", ""))
                for st in sensitive_texts:
                    if st and st in content:
                        content = content.replace(st, "[people content withheld]")
                redacted_messages.append({**msg_dict, "content": content})
            payload = {**payload, "messages": redacted_messages}
            # Also redact the user_prompt (the transcript) and pending calls
            user_prompt = payload.get("user_prompt", "")
            if isinstance(user_prompt, str):
                for st in sensitive_texts:
                    if st and st in user_prompt:
                        user_prompt = user_prompt.replace(st, "[people content withheld]")
                payload = {**payload, "user_prompt": user_prompt}
    # Remove _sensitive_texts sentinel before dispatch.
    payload.pop("_sensitive_texts", None)

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
            # HS-153-06: robust extraction handles think-blocks, fences,
            # and trailing prose from models like Qwen3.6.
            parsed = _extract_structured_json(raw)
            if parsed is not None:
                return {
                    "violations": list(parsed.get("violations", [])),
                    "warnings": list(parsed.get("warnings", [])),
                }

    return {"violations": [], "warnings": []}


def run_compact(
    broker: Any,
    principal: Principal,
    thread_id: str,
    messages: list[dict[str, Any]],
    *,
    sensitive_texts: list[str] | None = None,
) -> dict[str, Any]:
    """Summarize a chat thread prefix for compaction.

    Returns ``{summary: str}``.

    *sensitive_texts*: when provided, these are People-sensitive strings
    that must be redacted if the chat.compact capability routes through
    a cloud boundary (HS-153 close counsel M1).
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

    payload: dict[str, Any] = {
        "thread_id": thread_id,
        "messages": messages,
        "system_prompt": (
            "Summarize the following conversation concisely. "
            "Return a JSON object with a single key 'summary' containing the summary text."
        ),
        "user_prompt": transcript,
        # HS-153-06: json_schema response_format constrains the output to the
        # exact compaction schema.  Same grammar:"" + schema pattern as guardrail.
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "compaction",
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                    },
                    "required": ["summary"],
                },
            },
        },
    }
    if sensitive_texts:
        payload["_sensitive_texts"] = list(sensitive_texts)
    # Resolve the deployment revision AND boundary from the assignment chain.
    deployment_revision, boundary = _resolve_deployment_revision(broker, "chat.compact")

    # HS-153 close counsel M1: apply M1 redaction based on the CAPABILITY's
    # own boundary, not the thread's chat.turn egress scope.
    if boundary in ("cloud", "external_service"):
        sensitive_texts = payload.get("_sensitive_texts", [])
        if sensitive_texts:
            redacted_messages_c: list[dict[str, Any]] = []
            for msg_dict in payload.get("messages", []):
                if not isinstance(msg_dict, dict):
                    redacted_messages_c.append(msg_dict)
                    continue
                content = str(msg_dict.get("content", ""))
                for st in sensitive_texts:
                    if st and st in content:
                        content = content.replace(st, "[people content withheld]")
                redacted_messages_c.append({**msg_dict, "content": content})
            payload = {**payload, "messages": redacted_messages_c}
            user_prompt = payload.get("user_prompt", "")
            if isinstance(user_prompt, str):
                for st in sensitive_texts:
                    if st and st in user_prompt:
                        user_prompt = user_prompt.replace(st, "[people content withheld]")
                payload = {**payload, "user_prompt": user_prompt}
    # Remove _sensitive_texts sentinel before dispatch.
    payload.pop("_sensitive_texts", None)

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
            # HS-153-06: robust extraction handles think-blocks, fences,
            # and trailing prose from models like Qwen3.6.
            parsed = _extract_structured_json(raw)
            if parsed is not None and "summary" in parsed:
                return {"summary": str(parsed["summary"])}
            if raw:
                return {"summary": raw}

    return {"summary": ""}
