"""Thought family -- exact MCP commands for one-turn refinement."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.mcp.refinement_runtime import SidecarRefinementRuntime
from holdspeak.principals import Principal
from holdspeak.services.errors import ValidationError
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
_WORKSPACE_CURSOR = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "hub_id": _ID, "thought_id": _ID,
        "aggregate_revision": _REV, "continuity_revision": _REV,
    },
    "required": ["hub_id", "thought_id", "aggregate_revision", "continuity_revision"],
}
_ACTION_REQUIRED = [
    "thought_id",
    "review_result_id",
    "request_id",
    "expected_aggregate_revision",
    "expected_working_revision",
    "expected_attachment_revision",
]
_SOURCE = {
    "type": "object", "additionalProperties": False,
    "properties": {"kind": {"type": "string", "enum": ["typed", "voice", "note"]},
                   "ref": {"type": ["string", "null"]}},
    "required": ["kind"],
}
_INITIAL_NOTE = {
    "type": "object", "additionalProperties": False,
    "properties": {"id": _ID, "title": {"type": "string"},
                   "body_markdown": {"type": "string"},
                   "tags": {"type": "array", "items": {"type": "string"}}},
}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "thought.create",
        "description": "Create one durable Thought. The server applies this hub's owner-configured default AI-context refs atomically; no context body or model turn is accepted.",
        "inputSchema": _schema(
            {"request_id": _ID, "raw_text": {"type": "string", "minLength": 1},
             "source": _SOURCE, "initial_note": _INITIAL_NOTE},
            ["request_id", "raw_text"],
        ),
    },
    {
        "name": "thought.adopt_note",
        "description": "Adopt one existing Note as a durable Thought under exact source preconditions and this hub's default AI-context policy. Never invokes a model.",
        "inputSchema": _schema(
            {"request_id": _ID, "note_id": _ID,
             "expected_source_content_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
             "expected_source_last_modified": _ID},
            ["request_id", "note_id", "expected_source_content_sha256", "expected_source_last_modified"],
        ),
    },
    {
        "name": "thought.get_default_context",
        "description": "Read this hub's owner-only default AI-context qualified refs and safe labels. Returns no Note bodies.",
        "inputSchema": _schema({}, []),
    },
    {
        "name": "thought.replace_default_context",
        "description": "Atomically replace the complete hub-local default AI-context SET. Qualified refs and its own revision only; never invokes a model.",
        "inputSchema": _schema(
            {"request_id": _ID, "expected_revision": _REV,
             "refs": {"type": "array", "maxItems": 8,
                      "items": {"type": "string", "pattern": "^(note|knowledge):.+$"}}},
            ["request_id", "expected_revision", "refs"],
        ),
    },
    {
        "name": "thought.list_context",
        "description": "List safe Note/Everyday-context attachment metadata for one Thought. Returns no context bodies.",
        "inputSchema": _schema(
            {**_THOUGHT, "query": {"type": "string", "maxLength": 500},
             "view": {"type": "string", "enum": ["compact", "browse"]},
             "cursor": _ID, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
            ["thought_id"],
        ),
    },
    {
        "name": "thought.refine",
        "description": "MODEL-INVOKING: ask exactly one useful question about a durable Thought. The server loads authoritative content and context; this tool accepts no prompt, model, raw text, working text, or context payload.",
        "inputSchema": _schema(
            {**_THOUGHT, "request_id": _ID, **_CURSORS, "workspace_cursor": _WORKSPACE_CURSOR},
            ["thought_id", "request_id", *_CURSORS],
        ),
    },
    {
        "name": "thought.reconcile",
        "description": "Reconcile one known durable refinement result. Never dispatches or retries a model turn.",
        "inputSchema": _schema(
            {**_THOUGHT, "expected_aggregate_revision": _REV, "invocation_id": _ID,
             "workspace_cursor": _WORKSPACE_CURSOR},
            ["thought_id", "expected_aggregate_revision"],
        ),
    },
    {
        "name": "thought.stop_refinement",
        "description": "Durably suppress one exact refinement invocation, then best-effort cancel its physical call. Never retries.",
        "inputSchema": _schema(
            {**_THOUGHT, "invocation_id": _ID, "expected_aggregate_revision": _REV,
             "workspace_cursor": _WORKSPACE_CURSOR},
            ["thought_id", "invocation_id", "expected_aggregate_revision"],
        ),
    },
]

for _context_action in ("attach", "detach", "refresh"):
    TOOLS.append({
        "name": f"thought.{_context_action}_context",
        "description": f"{_context_action.capitalize()} one qualified context ref. Refs and Thought cursors only; copied context is rejected.",
        "inputSchema": _schema(
            {**_THOUGHT, "ref": _ID, "request_id": _ID, **_CURSORS,
             "workspace_cursor": _WORKSPACE_CURSOR},
            ["thought_id", "ref", "request_id", *_CURSORS],
        ),
    })

for _action in ("answer", "accept", "reject"):
    _properties = {
        **_THOUGHT,
        "review_result_id": _ID,
        "request_id": _ID,
        **_CURSORS,
        "workspace_cursor": _WORKSPACE_CURSOR,
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

TOOLS.extend([
    {
        "name": "thought.answer_and_continue",
        "description": "MODEL-INVOKING: atomically add one question answer to the Note and reserve exactly one next refinement turn.",
        "inputSchema": _schema(
            {**_THOUGHT, "review_result_id": _ID, "command_id": _ID,
             "answer": {"type":"string","maxLength":12000}, **_CURSORS,
             "workspace_cursor": _WORKSPACE_CURSOR},
            ["thought_id","review_result_id","command_id","answer",*_CURSORS,"workspace_cursor"],
        ),
    },
    {
        "name": "thought.update_working",
        "description": "Update the live working Note under Thought CAS. Never invokes a model.",
        "inputSchema": _schema(
            {**_THOUGHT,"expected_aggregate_revision":_REV,"expected_working_revision":_REV,
             "title":{"type":"string"},"body_markdown":{"type":"string"},
             "tags":{"type":"array","items":{"type":"string"}},"workspace_cursor":_WORKSPACE_CURSOR},
            ["thought_id","expected_aggregate_revision","expected_working_revision"],
        ),
    },
    {
        "name": "thought.complete",
        "description": "Finish one Thought directly with a durable receipt. Never invokes a model.",
        "inputSchema": _schema(
            {**_THOUGHT,"request_id":_ID,"expected_aggregate_revision":_REV,
             "expected_lifecycle_revision":_REV,"workspace_cursor":_WORKSPACE_CURSOR},
            ["thought_id","request_id","expected_aggregate_revision","expected_lifecycle_revision"],
        ),
    },
    {
        "name": "thought.resume",
        "description": "Resume one completed Thought. Never invokes a model.",
        "inputSchema": _schema(
            {**_THOUGHT,"expected_aggregate_revision":_REV,"expected_lifecycle_revision":_REV,
             "workspace_cursor":_WORKSPACE_CURSOR},
            ["thought_id","expected_aggregate_revision","expected_lifecycle_revision"],
        ),
    },
])


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
    spec = next((item for item in TOOLS if item["name"] == name), None)
    if spec is None:
        raise LookupError(name)
    allowed = set(spec["inputSchema"]["properties"])
    if set(arguments) - allowed:
        raise ValidationError("Thought MCP command schema is closed",
                              code="mcp_invalid_params")
    svc = _service()
    if name == "thought.create":
        return svc.create_thought(
            principal, request_id=arguments.get("request_id"),
            raw_text=arguments.get("raw_text"), source=arguments.get("source"),
            initial_note=arguments.get("initial_note"),
        )
    if name == "thought.adopt_note":
        return svc.adopt_note(
            principal, request_id=arguments.get("request_id"),
            note_id=arguments.get("note_id"),
            expected_source_content_sha256=arguments.get("expected_source_content_sha256"),
            expected_source_last_modified=arguments.get("expected_source_last_modified"),
        )
    if name == "thought.get_default_context":
        return svc.get_default_context(principal)
    if name == "thought.replace_default_context":
        return svc.replace_default_context(
            principal, request_id=arguments.get("request_id"),
            expected_revision=arguments.get("expected_revision"),
            refs=arguments.get("refs"),
        )
    common = {
        "thought_id": arguments.get("thought_id"),
        "expected_aggregate_revision": arguments.get("expected_aggregate_revision"),
    }
    if name == "thought.list_context":
        return svc.list_context(
            principal, thought_id=arguments.get("thought_id"),
            query=arguments.get("query", ""), view=arguments.get("view", "compact"),
            cursor=arguments.get("cursor"), limit=arguments.get("limit", 20),
        )
    context_action = {
        "thought.attach_context": "attach",
        "thought.detach_context": "detach",
        "thought.refresh_context": "refresh",
    }.get(name)
    if context_action is not None:
        return svc.mutate_context(
            principal, action=context_action, **common,
            ref=arguments.get("ref"), request_id=arguments.get("request_id"),
            expected_working_revision=arguments.get("expected_working_revision"),
            expected_attachment_revision=arguments.get("expected_attachment_revision"),
            workspace_cursor=arguments.get("workspace_cursor"),
        )
    if name == "thought.refine":
        return _run(svc.refine(
            principal,
            **common,
            request_id=arguments.get("request_id"),
            expected_working_revision=arguments.get("expected_working_revision"),
            expected_attachment_revision=arguments.get("expected_attachment_revision"),
            workspace_cursor=arguments.get("workspace_cursor"),
        ))
    if name == "thought.reconcile":
        return svc.reconcile(
            principal, **common, invocation_id=arguments.get("invocation_id"),
            workspace_cursor=arguments.get("workspace_cursor"),
        )
    if name == "thought.stop_refinement":
        return _run(svc.stop(
            principal, **common, invocation_id=arguments.get("invocation_id"),
            workspace_cursor=arguments.get("workspace_cursor"),
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
            workspace_cursor=arguments.get("workspace_cursor"),
        )
    if name == "thought.answer_and_continue":
        return _run(svc.answer_and_continue(
            principal, **common, review_result_id=arguments.get("review_result_id"),
            command_id=arguments.get("command_id"), answer=arguments.get("answer"),
            expected_working_revision=arguments.get("expected_working_revision"),
            expected_attachment_revision=arguments.get("expected_attachment_revision"),
            workspace_cursor=arguments.get("workspace_cursor"),
        ))
    if name == "thought.update_working":
        return svc.update_working(
            principal, **common, expected_working_revision=arguments.get("expected_working_revision"),
            title=arguments.get("title"), body_markdown=arguments.get("body_markdown"),
            tags=arguments.get("tags"), workspace_cursor=arguments.get("workspace_cursor"),
        )
    if name == "thought.complete":
        return svc.complete(
            principal, **common, request_id=arguments.get("request_id"),
            expected_lifecycle_revision=arguments.get("expected_lifecycle_revision"),
            workspace_cursor=arguments.get("workspace_cursor"),
        )
    if name == "thought.resume":
        return svc.resume(
            principal, **common,
            expected_lifecycle_revision=arguments.get("expected_lifecycle_revision"),
            workspace_cursor=arguments.get("workspace_cursor"),
        )
    raise LookupError(name)
