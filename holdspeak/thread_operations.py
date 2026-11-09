"""The chat threads' verbs (``/api/threads``) on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb
once: its call, its HTTP method and path, and its MCP tool schema.
``web/routes/threads.py`` produces the routes and ``mcp/families/declared.py``
the tools from these rows, both through ``OperationRegistry.invoke``.

The rows bind to ``hub_thread_service``: the hub's ThreadService FACTORY
(``services/thread_service.hub_thread_service`` over the hub's bus), called
once per verb as the hand-written routes did. A turn, a branch, a regenerate
and a todo are coroutines: the HTTP call (``web_call``) answers the coroutine
and the route awaits it on the hub's loop; the MCP call runs it there
(``mcp/aio.run_async``). The threads are the owner's conversations: every
verb is owner only, and a launched agent calls none
(``conductor_launch._family_rules``). A read is MCP and HTTP only
(``thread_modes._family_reads``). The interview control
(``POST /api/threads/{thread_id}/interview``) stays a browser-only route
(HS-200-10: no model mints a canonical record).
Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver); the owner only"
_REFUSALS = _CONTRACT_REFUSALS + ("owner_required", "thread_not_found", "validation_error")
_ID = {"type": "string", "minLength": 1}
_TEXT = {"type": "string", "minLength": 1}
_T = "/api/threads/{thread_id}"


def _refs(raw: Any) -> Optional[list[str]]:
    """Refs as ``["kind:id", ...]`` or ``[{ref_kind, ref_id}, ...]`` (the composer's shape), as ``kind:id``."""
    if not isinstance(raw, list):
        return None
    result: list[str] = []
    for item in raw:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and item.get("ref_kind") and item.get("ref_id"):
            result.append(f"{item['ref_kind']}:{item['ref_id']}")
        elif isinstance(item, dict) and item.get("kind") and item.get("id"):
            result.append(f"{item['kind']}:{item['id']}")
    return result or None


def _turn(make: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.services.thread_service import _UNSET

    return make().start_turn(principal, args.get("thread_id"), str(args.get("text") or ""),
                             refs=_refs(args.get("refs")),
                             parent_id=args["parent_id"] if "parent_id" in args else _UNSET)


def _sync(web: Call) -> Call:
    """The MCP face of a coroutine verb: run it on the hub's loop."""
    def call(make: Any, principal: Any, args: dict[str, Any]) -> Any:
        from holdspeak.mcp.aio import run_async

        return run_async(web(make, principal, args))

    return call


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = False, status: int = 200, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = (), coroutine: bool = False, refusals: tuple[str, ...] = (),
        result: str = "the ThreadService answer") -> OperationDescriptor:
    """One verb of the hub's ThreadService; its tool requires the path's ids and ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_REFUSALS + refusals,
        completion=("the answer names the turn; the thread_* frames on the hub bus carry it to done"
                    if coroutine else "synchronous; a write is one desk_changed frame on the hub bus"),
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service="hub_thread_service", method=method,
        owner_only=True, call=_sync(call) if coroutine else call, web_call=call if coroutine else None,
        http=http, http_status=status, handler=handler, tool_schema=tool,
        thread="effect_proposal" if write else "evidence_read",
    )


THREAD_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("thread.create", "create", ("POST", "/api/threads"), "api_create_thread",
        lambda m, p, a: m().create(title=str(a.get("title") or ""), recipe_id=str(a.get("recipe_id") or ""),
                                   seed_refs=a.get("seed_refs") if isinstance(a.get("seed_refs"), list) else None,
                                   profile_override=str(a.get("profile_override") or "")),
        "Start a new thread: a title, an optional recipe or mode, seed references and an engine override.",
        write=True, status=201,
        properties={"title": {"type": "string"}, "recipe_id": {"type": "string"},
                    "seed_refs": {"type": "array", "items": {"type": "string"}},
                    "profile_override": {"type": "string"}}),
    _op("thread.list", "list_threads", ("GET", "/api/threads"), "api_list_threads",
        lambda m, p, a: {"threads": m().list_threads(limit=int(a.get("limit") or 100), ref_id=str(a.get("ref_id") or ""))},
        "List the threads, newest first. ref_id: only the threads that cite this record.",
        properties={"limit": {"type": "integer", "minimum": 1, "maximum": 500}, "ref_id": {"type": "string"}},
        result="{threads: [...]}"),
    _op("thread.get", "get", ("GET", _T), "api_get_thread", lambda m, p, a: m().get(a.get("thread_id")),
        "Read one thread with its messages."),
    _op("thread.update", "edit", ("PATCH", _T), "api_patch_thread",
        lambda m, p, a: m().edit(a.get("thread_id"), title=a.get("title"), profile_override=a.get("profile_override"),
                                 recipe_id=a.get("recipe_id"), call_mode=a.get("call_mode"),
                                 toggle_guardrail=a.get("toggle_guardrail"),
                                 toggle_guardrail_enable=a.get("toggle_guardrail_enable", True)),
        "Change a thread: its title, engine override, recipe or mode, call mode (0 or 1), or turn one "
        "guardrail of its mode on or off.", write=True, refusals=("invalid_call_mode",),
        properties={"title": {"type": "string"}, "profile_override": {"type": "string"}, "recipe_id": {"type": "string"},
                    "call_mode": {"type": "integer", "enum": [0, 1]}, "toggle_guardrail": {"type": "string"},
                    "toggle_guardrail_enable": {"type": "boolean"}}),
    _op("thread.delete", "delete", ("DELETE", _T), "api_delete_thread", lambda m, p, a: m().delete(a.get("thread_id")),
        "Delete a thread (it can be restored from the database).", write=True, result="{deleted: true}"),
    _op("thread.turn", "start_turn", ("POST", _T + "/turns"), "api_start_turn", _turn,
        "Send a message on a thread and start the answer. The answer streams on the hub bus.",
        write=True, status=201, coroutine=True, required=("text",),
        properties={"text": _TEXT, "refs": {"type": "array", "items": {"type": "string"}},
                    "parent_id": {"type": ["string", "null"]}}),
    _op("thread.abort", "abort", ("POST", _T + "/abort"), "api_abort", lambda m, p, a: m().abort(a.get("thread_id")),
        "Stop the running answer of a thread.", write=True, result="{aborted, message_id}"),
    _op("thread.branch", "branch", ("POST", _T + "/branch"), "api_branch",
        lambda m, p, a: m().branch(p, a.get("thread_id"), str(a.get("message_id") or ""), str(a.get("text") or "")),
        "Edit an earlier message: a new branch from it, with a new answer.", write=True, status=201, coroutine=True,
        required=("message_id", "text"), properties={"message_id": _ID, "text": _TEXT}),
    _op("thread.regenerate", "regenerate", ("POST", _T + "/regenerate"), "api_regenerate",
        lambda m, p, a: m().regenerate(p, a.get("thread_id"), str(a.get("message_id") or "")),
        "Answer a message again.", write=True, status=201, coroutine=True, required=("message_id",),
        properties={"message_id": _ID}),
    _op("thread.keep", "keep", ("POST", _T + "/keep"), "api_keep",
        lambda m, p, a: m().keep(p, a.get("thread_id"), str(a.get("message_id") or ""), as_kind=str(a.get("as") or "note")),
        "Keep an answer as a desk note (the default) or an artifact.", write=True, status=201,
        required=("message_id",), properties={"message_id": _ID, "as": {"enum": ["note", "artifact"]}},
        result="{kind, id, note_id or artifact_id}"),
    _op("thread.import", "import_threads", ("POST", "/api/threads/import"), "api_import_threads",
        lambda m, p, a: {"imported": m().import_threads(a.get("threads") if isinstance(a.get("threads"), list) else [])},
        "Import threads from another chat tool.", write=True, required=("threads",),
        properties={"threads": {"type": "array", "items": {"type": "object"}}}, result="{imported: {old id: new id}}"),
    _op("thread.decide", "decide_tool", ("POST", _T + "/decide"), "api_decide_tool",
        lambda m, p, a: m().decide_tool(a.get("thread_id"), a.get("call_id"), a.get("decision"),
                                        answer=a.get("answer"), always=a.get("always", False)),
        "Approve or deny a tool call the thread holds for the owner; always: allow this tool from now on.",
        write=True, required=("call_id", "decision"),
        refusals=("tool_executor_unavailable", "tool_call_not_found", "tool_call_not_pending"),
        properties={"call_id": _ID, "decision": {"enum": ["approve", "deny"]}, "answer": {"type": "string"},
                    "always": {"type": "boolean"}}, result="{call_id, decision, always, state}"),
    _op("thread.annotation.add", "add_annotation", ("POST", _T + "/annotations"), "api_add_annotation",
        lambda m, p, a: m().add_annotation(a.get("thread_id"), a.get("message_id"), a.get("quote"), a.get("comment")),
        "Annotate a quote of a message: the note joins the thread's draft message.", write=True, status=201,
        required=("message_id", "quote"), refusals=("message_not_found",),
        properties={"message_id": _ID, "quote": _TEXT, "comment": {"type": "string"}}),
    _op("thread.annotation.delete", "delete_annotation", ("DELETE", _T + "/annotations/{part_id}"),
        "api_delete_annotation", lambda m, p, a: m().delete_annotation(a.get("thread_id"), a.get("part_id")),
        "Delete one draft annotation of a thread.", write=True, refusals=("annotation_not_found",),
        result="{deleted: true}"),
    _op("thread.todo", "todo_from_thread", ("POST", _T + "/todo"), "api_todo",
        lambda m, p, a: m().todo_from_thread(p, a.get("thread_id"), str(a.get("text") or "").strip()),
        "Make a task from a thread: its words, with the thread as the source.", write=True, coroutine=True,
        required=("text",), properties={"text": _TEXT}),
)

__all__ = ["THREAD_OPERATIONS"]
