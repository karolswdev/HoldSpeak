"""Thought family -- exact MCP commands for one-turn refinement."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.mcp.refinement_runtime import SidecarRefinementRuntime
from holdspeak.principals import Principal
from holdspeak.services.refinement_application_service import RefinementApplicationService


def _schema(
    properties: dict[str, Any], required: list[str]
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


_ID = {"type": "string", "minLength": 1}
_REV = {"type": "integer", "minimum": 0}
_THOUGHT = {"thought_id": _ID}
_CURSORS = {
    "expected_aggregate_revision": _REV,
    "expected_working_revision": _REV,
    "expected_attachment_revision": _REV,
}
_ACTION_REQUIRED = [
    "thought_id",
    "review_result_id",
    "request_id",
    "expected_aggregate_revision",
    "expected_working_revision",
    "expected_attachment_revision",
]

TOOLS: list[dict[str, Any]] = [
    {
        "name": "thought.refine",
        "description": "MODEL-INVOKING: ask exactly one useful question about a durable Thought. The server loads authoritative content and context; this tool accepts no prompt, model, raw text, working text, or context payload.",
        "inputSchema": _schema(
            {**_THOUGHT, "request_id": _ID, **_CURSORS},
            ["thought_id", "request_id", *_CURSORS],
        ),
    },
    {
        "name": "thought.reconcile",
        "description": "Reconcile one known durable refinement result. Never dispatches or retries a model turn.",
        "inputSchema": _schema(
            {**_THOUGHT, "expected_aggregate_revision": _REV, "invocation_id": _ID},
            ["thought_id", "expected_aggregate_revision"],
        ),
    },
    {
        "name": "thought.stop_refinement",
        "description": "Durably suppress one exact refinement invocation, then best-effort cancel its physical call. Never retries.",
        "inputSchema": _schema(
            {**_THOUGHT, "invocation_id": _ID, "expected_aggregate_revision": _REV},
            ["thought_id", "invocation_id", "expected_aggregate_revision"],
        ),
    },
]

for _action in ("answer", "accept", "reject"):
    _properties = {
        **_THOUGHT,
        "review_result_id": _ID,
        "request_id": _ID,
        **_CURSORS,
    }
    _required = list(_ACTION_REQUIRED)
    if _action == "answer":
        _properties["answer"] = {"type": "string", "maxLength": 12000}
        _required.append("answer")
    TOOLS.append(
        {
            "name": f"thought.{_action}_review",
            "description": (
                f"{_action.capitalize()} one exact receipt-gated review. "
                "This is an immediate owner action and never starts another model turn."
            ),
            "inputSchema": _schema(_properties, _required),
        }
    )


_runtime: SidecarRefinementRuntime | None = None


def configure_runtime(runtime: SidecarRefinementRuntime | None) -> None:
    global _runtime
    _runtime = runtime


def _service() -> RefinementApplicationService:
    return RefinementApplicationService(
        get_database(), coordinator=_runtime.coordinator if _runtime else None
    )


def _run(awaitable: Any) -> Any:
    if _runtime is None:
        if hasattr(awaitable, "close"):
            awaitable.close()
        raise RuntimeError("MCP refinement runtime is not started")
    return _runtime.call(awaitable)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    svc = _service()
    common = {
        "thought_id": arguments.get("thought_id"),
        "expected_aggregate_revision": arguments.get("expected_aggregate_revision"),
    }
    if name == "thought.refine":
        return _run(svc.refine(
            principal,
            **common,
            request_id=arguments.get("request_id"),
            expected_working_revision=arguments.get("expected_working_revision"),
            expected_attachment_revision=arguments.get("expected_attachment_revision"),
        ))
    if name == "thought.reconcile":
        return svc.reconcile(
            principal, **common, invocation_id=arguments.get("invocation_id")
        )
    if name == "thought.stop_refinement":
        return _run(svc.stop(
            principal, **common, invocation_id=arguments.get("invocation_id")
        ))
    action_by_name = {
        "thought.answer_review": "answer",
        "thought.accept_review": "accept",
        "thought.reject_review": "reject",
    }
    action = action_by_name.get(name)
    if action is not None:
        return svc.act_on_review(
            principal,
            **common,
            review_result_id=arguments.get("review_result_id"),
            request_id=arguments.get("request_id"),
            expected_working_revision=arguments.get("expected_working_revision"),
            expected_attachment_revision=arguments.get("expected_attachment_revision"),
            action=action,
            answer=arguments.get("answer", ""),
        )
    raise LookupError(name)
