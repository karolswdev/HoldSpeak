"""Ask family — MCP tools for the AskService surface."""
from __future__ import annotations

import asyncio
from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.ask_service import AskService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "ask.resolve_grounding",
        "description": "Resolve grounding references and return their hydrated titles and character counts without running inference.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "refs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 20,
                    "description": "Qualified grounding references (e.g. 'note:abc', 'meeting:xyz').",
                },
            },
            "required": ["refs"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ask.run",
        "description": "Ask the desk a question. MODEL-INVOKING: rides the admitted RunLifecycle path. The result carries the receipt (model, provider, egress, actual_placement) so the caller knows what ran and where.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The prompt to ask."},
                "lens": {"type": "string", "description": "Label for this Ask turn (default 'Ask')."},
                "context": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Material context entries [{id, kind, title}].",
                },
                "grounding": {
                    "type": "object",
                    "description": "Grounding payload: meeting_ids, artifact_ids, refs, expand.",
                },
                "max_tokens": {"type": "integer", "minimum": 1},
                "temperature": {"type": "number", "minimum": 0, "maximum": 2},
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ask.cancel",
        "description": "Cancel an in-flight Ask invocation by its invocation_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "invocation_id": {"type": "string", "description": "The invocation_id returned by ask.run."},
            },
            "required": ["invocation_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ask.keep",
        "description": "Persist an Ask answer as a desk artifact. Not model-invoking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "description": "The answer text to persist."},
                "sources": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Source entries [{id, kind, title, ref}].",
                },
                "lens": {"type": "string"},
                "prompt": {"type": "string"},
                "grounding": {"type": "object"},
            },
            "required": ["output"],
            "additionalProperties": False,
        },
    },
]


def _run(coro: Any) -> Any:
    """Run an async coroutine synchronously; mirrors tools.py:411-416."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ValueError("async MCP tools cannot execute inside an active event loop")


def _service() -> AskService:
    """Construct AskService per spec: db + observer, no broadcast, no rails_hydrator."""
    return AskService(
        db=get_database(),
        broadcast=None,
        rails_hydrator=None,
        observer=get_observer(),
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name == "ask.resolve_grounding":
        refs = arguments.get("refs")
        if not isinstance(refs, list):
            raise ValueError("refs is required and must be an array")
        return _service().resolve_grounding(principal, refs)

    if name == "ask.run":
        allowed = {"question", "lens", "context", "grounding", "max_tokens", "temperature"}
        if set(arguments) - allowed:
            raise ValueError("ask.run has an invalid request shape")
        question = arguments.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question is required")
        svc = _service()
        kwargs: dict[str, Any] = {"question": question}
        if "lens" in arguments:
            kwargs["lens"] = arguments["lens"]
        if "context" in arguments:
            kwargs["context"] = arguments["context"]
        if "grounding" in arguments:
            kwargs["grounding"] = arguments["grounding"]
        if "max_tokens" in arguments:
            kwargs["max_tokens"] = arguments["max_tokens"]
        if "temperature" in arguments:
            kwargs["temperature"] = arguments["temperature"]
        return _run(svc.ask(principal, **kwargs))

    if name == "ask.cancel":
        invocation_id = arguments.get("invocation_id")
        if not isinstance(invocation_id, str) or not invocation_id.strip():
            raise ValueError("invocation_id is required")
        return _service().cancel(principal, invocation_id)

    if name == "ask.keep":
        output = arguments.get("output")
        if not isinstance(output, str) or not output.strip():
            raise ValueError("output is required")
        kwargs_keep: dict[str, Any] = {
            "output": output,
            "sources": arguments.get("sources") or [],
        }
        if "lens" in arguments:
            kwargs_keep["lens"] = arguments["lens"]
        if "prompt" in arguments:
            kwargs_keep["prompt"] = arguments["prompt"]
        if "grounding" in arguments:
            kwargs_keep["grounding"] = arguments["grounding"]
        return _service().keep(principal, **kwargs_keep)

    raise LookupError(name)
