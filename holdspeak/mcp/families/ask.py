"""Ask family — MCP tools for the AskService surface."""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.ask_service import AskService

TOOLS: list[dict[str, Any]] = [
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
                "tools": {
                    "type": "string", "enum": ["none"],
                    "description": "'none': the engine gets no tools in this run (an agent CLI gets no desk tools), and the result carries 'provenance' (the refs the answer was given). It only takes tools away.",
                },
            },
            "required": ["question"],
            "additionalProperties": False,
        },
    }
]


# The one helper every family shares (holdspeak/mcp/aio.py).
from holdspeak.mcp.aio import run_async as _run  # noqa: E402


def _build_service() -> AskService:
    """Construct AskService per spec: db + observer, no broadcast, no rails_hydrator."""
    return AskService(
        db=db_or(get_database),
        broadcast=None,
        rails_hydrator=None,
        observer=observer_or(get_observer),
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name == "ask.run":
        allowed = {"question", "lens", "context", "grounding", "max_tokens", "temperature", "tools"}
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
        if "tools" in arguments:
            if arguments["tools"] != "none":
                raise ValueError("tools can only be 'none'")
            kwargs["no_tools"] = True
        return _run(svc.ask(principal, **kwargs))

    raise LookupError(name)


# HS-200-45 R1: _service asks the ONE composition root first. Inside the hub that
# returns the instance the HTTP routes use -- composed with broadcast= and the rails hydrator.
# Outside a hub (a unit test's bare root, or the standalone diagnosis hatch) the
# root holds nothing and the bare builder above runs, producing exactly the
# object the pre-HS-200-45 code produced.
def _service() -> AskService:
    """The hub's live service, else the bare composition above."""
    return runtime_service("ask_service", _build_service)
