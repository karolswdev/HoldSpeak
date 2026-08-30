"""Intel JSON parsing / coercion helpers (HS-34-04)."""

from __future__ import annotations

import json
import re
import socket
from typing import Any, Optional

from ..logging_config import get_logger
from .models import ActionItem, DEFAULT_CLOUD_BASE_URL

log = get_logger("intel")


# HS-151-01 (counsel M2+M4): ONE schema constant — the prompt stringifies it,
# the response_format wraps it, the semantic adapter references it.  Carries
# the named-owner shape from the start (owner: string|null).
INTEL_SCHEMA: dict[str, Any] = {
    "topics": ["<short topic>"],
    "action_items": [
        {
            "task": "<task>",
            "owner": "<person's name as spoken>|Me|Remote|null",
            "due": "<date or null>",
        },
    ],
    "summary": "<short summary>",
}

# The JSON Schema used by the OpenAI response_format payload.  Derived once
# from the INTEL_SCHEMA constant so prompt and structured-output always agree.
INTEL_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "topics": {
            "type": "array",
            "items": {"type": "string"},
        },
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "owner": {"type": ["string", "null"]},
                    "due": {"type": ["string", "null"]},
                },
                "required": ["task", "owner", "due"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["topics", "action_items", "summary"],
    "additionalProperties": False,
}


def intel_response_format() -> dict[str, Any]:
    """Build the OpenAI ``response_format`` payload from the ONE schema constant.

    Returns the ``{type: "json_schema", json_schema: {name, strict, schema}}``
    dict ready to pass as ``response_format=`` to ``chat.completions.create``.
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "meeting_intel",
            "strict": True,
            "schema": INTEL_JSON_SCHEMA,
        },
    }


def _json_only_messages(transcript: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a meeting intelligence assistant.\n"
                "Return ONLY a single valid JSON object and nothing else.\n"
                "Do not wrap in markdown or code fences.\n"
                "Do not add explanations.\n"
                "If a field is unknown, use null or an empty list.\n"
            ),
        },
        {
            "role": "user",
            "content": (
                "Analyze this transcript and extract meeting intelligence.\n\n"
                "Output JSON with this exact shape:\n"
                f"{json.dumps(INTEL_SCHEMA, ensure_ascii=False)}\n\n"
                "For action_items owner: name the owner ONLY when the transcript names them. "
                "Use the person's name as spoken in the transcript. "
                "Me = the speaker/leader; Remote = the counterpart; null when unclear. "
                "Me and Remote are the ONLY reserved tokens — every other string is a literal person name.\n\n"
                "Transcript:\n"
                f"{transcript}\n"
            ),
        },
    ]


def _extract_json(text: str) -> Optional[dict]:
    s = text.strip()
    if not s:
        return None

    # Remove common wrappers like ```json ... ```
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)

    try:
        obj = json.loads(s)
        if not isinstance(obj, dict):
            return None
        # Some OpenAI-compatible local models wrap an otherwise schema-shaped
        # answer in a JSON ``line`` string. Recover its action array instead of
        # accepting a false-ready meeting with no extracted actions.
        embedded = obj.get("line")
        if isinstance(embedded, str) and "action_items:" in embedded:
            actions = re.search(
                r"action_items:\s*(\[.*?\])\s*,?\s*(?:[\"']?summary[\"']?:|$)",
                embedded,
                flags=re.DOTALL,
            )
            if actions:
                try:
                    obj["action_items"] = json.loads(actions.group(1))
                except json.JSONDecodeError:
                    pass
            summary = re.search(r'summary:\s*"(.*?)"\s*$', embedded, flags=re.DOTALL)
            if summary:
                obj["summary"] = summary.group(1)
        return obj
    except Exception:
        pass

    # Best-effort recovery: find the first JSON object in the text.
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = s[start : end + 1].strip()
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _coerce_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if item is None:
                continue
            out.append(str(item).strip())
        return [t for t in out if t]
    if value is None:
        return []
    return [str(value).strip()] if str(value).strip() else []


def _coerce_action_items(value: object) -> list[ActionItem]:
    if not isinstance(value, list):
        return []

    items: list[ActionItem] = []
    for entry in value:
        if not isinstance(entry, dict):
            continue
        task = str(entry.get("task", "")).strip()
        if not task:
            continue
        owner = entry.get("owner", None)
        due = entry.get("due", None)
        items.append(
            ActionItem(
                task=task,
                owner=(None if owner in (None, "", "null") else str(owner).strip()),
                due=(None if due in (None, "", "null") else str(due).strip()),
            )
        )
    return items


def _extract_openai_message_text(content: object) -> str:
    """Extract text from OpenAI SDK message content variants."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    parts.append(str(text_value))
                    continue
                nested = item.get("content")
                if nested:
                    parts.append(str(nested))
                    continue
                if "type" in item and item.get("type") == "output_text" and item.get("text"):
                    parts.append(str(item["text"]))
                    continue
            else:
                text_attr = getattr(item, "text", None)
                if text_attr:
                    parts.append(str(text_attr))
        return "".join(parts)
    return str(content)


def _extract_status_code(exc: BaseException) -> Optional[int]:
    for attr in ("status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value

    response = getattr(exc, "response", None)
    if response is not None:
        for attr in ("status_code", "status"):
            value = getattr(response, attr, None)
            if isinstance(value, int):
                return value
    return None


def _describe_cloud_exception(exc: BaseException, *, model: str, base_url: Optional[str]) -> str:
    endpoint = (base_url or DEFAULT_CLOUD_BASE_URL).strip() or DEFAULT_CLOUD_BASE_URL
    message = str(exc).strip() or exc.__class__.__name__
    message_lower = message.lower()
    exc_name = exc.__class__.__name__.lower()
    status_code = _extract_status_code(exc)

    if status_code in {401, 403} or "unauthorized" in message_lower or "forbidden" in message_lower:
        return f"Cloud auth failed for {endpoint}: {message}"

    if (
        "model" in message_lower
        and ("not found" in message_lower or "does not exist" in message_lower or "unknown" in message_lower)
    ) or (status_code == 404 and "model" in message_lower):
        return f"Cloud model '{model}' not found at {endpoint}: {message}"

    if status_code == 404:
        return f"Cloud endpoint not found at {endpoint}: {message}"

    if status_code == 429 or "rate limit" in message_lower:
        return f"Cloud rate limit hit at {endpoint}: {message}"

    if status_code is not None and status_code >= 500:
        return f"Cloud server error ({status_code}) at {endpoint}: {message}"

    if (
        isinstance(exc, (TimeoutError, socket.timeout))
        or "timeout" in exc_name
        or "timed out" in message_lower
        or "read timeout" in message_lower
    ):
        return f"Cloud request timed out to {endpoint}: {message}"

    if isinstance(exc, ConnectionRefusedError):
        return f"Cloud connection refused by {endpoint}: {message}"

    if isinstance(exc, socket.gaierror):
        return f"Cloud DNS resolution failed for {endpoint}: {message}"

    if (
        "connection" in exc_name
        or "connection" in message_lower
        or "name or service not known" in message_lower
        or "temporary failure in name resolution" in message_lower
        or "failed to establish a new connection" in message_lower
    ):
        return f"Cloud connection failed to {endpoint}: {message}"

    return f"Cloud request failed at {endpoint}: {message}"
