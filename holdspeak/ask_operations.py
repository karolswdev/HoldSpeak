"""Ask reads and threaded answers on the shared operation registry.

The streaming HTTP request keeps its detached, shielded task. MCP runs the
same coroutine on the hub loop. The service owns saved-run projection.
"""
from __future__ import annotations

from holdspeak.operations import OperationDescriptor, _CONTRACT_REFUSALS

_EMPTY = {"type": "object", "properties": {}, "additionalProperties": False}
_THREAD = {"type": "object", "properties": {
    "prompt": {"type": "string"}, "grounding": {}, "thread_id": {"type": "string"},
    "lens": {"type": "string"}, "context": {"type": "array", "items": {"type": "object"}},
    "invocation_id": {"type": ["string", "null"]}, "source_snapshot": {},
}, "required": ["prompt"], "additionalProperties": False}


def _thread(service, principal, args):
    return service.ask_in_thread(principal, str(args.get("prompt") or ""), args.get("grounding"),
        thread_id=str(args.get("thread_id") or ""), lens=str(args.get("lens") or "Ask"),
        context=args.get("context") or [], invocation_id=args.get("invocation_id"),
        source_snapshot=args.get("source_snapshot"))


def _thread_mcp(service, principal, args):
    from holdspeak.mcp.aio import run_async

    return run_async(_thread(service, principal, args))


def _read(name, method, path, handler, call, description, schema=_EMPTY):
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema=schema,
        principal="the authenticated owner from the transport", effect="read",
        result="the Ask service answer in the HTTP envelope", refusals=_CONTRACT_REFUSALS + ("owner_required",),
        completion="synchronous", exposure=(f"http:GET {path}", f"mcp:{name}"),
        service="ask_service", method=method, call=call, blocking_io=True, owner_only=True,
        http=("GET", path), handler=handler, tool_schema=schema,
    )


ASK_OPERATIONS = (
    _read("ask.list_models", "list_models", "/api/models", "api_list_models",
          lambda s, p, a: {"models": s.list_models(p)}, "Read the Ask model choices."),
    _read("ask.engine_tools", "engine_tools", "/api/ask/engine", "api_ask_engine",
          lambda s, p, a: s.engine_tools(), "Read whether the Answers engine can use Desk tools."),
    _read("ask.runs", "get_runs", "/api/ask/runs", "api_ask_runs",
          lambda s, p, a: {"runs": s.get_runs(p, a.get("ids", ""))}, "Read the retained state of Ask runs.",
          {"type": "object", "properties": {"ids": {"type": "string", "description": "Up to 20 invocation ids, comma separated."}},
           "additionalProperties": False}),
    OperationDescriptor(
        name="ask.in_thread", version=1, description="Ask in a saved thread, or continue that thread.",
        args_schema=_THREAD, principal="the authenticated owner from the transport", effect="write",
        result="the Ask answer, thread id and invocation id", refusals=_CONTRACT_REFUSALS + ("owner_required",),
        completion="asynchronous; ask.runs retains the result when the HTTP window closes",
        exposure=("http:POST /api/ask", "mcp:ask.in_thread"), service="ask_service", method="ask_in_thread",
        call=_thread_mcp, web_call=_thread, owner_only=True, owner_press=True, authority="egress",
        tool_schema=_THREAD,
    ),
)
