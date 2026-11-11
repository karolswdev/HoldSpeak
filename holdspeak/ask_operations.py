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
        http=("GET", path), handler=handler, tool_schema=schema, thread="evidence_read",
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
        # The coroutine owns its Ask/thread frames after it writes state.
        # Returning a coroutine must not announce a completed write.
        tool_schema=_THREAD, announces_changes=True,
    ),
)


def _mcp_simple(method, web_call):
    def call(service, principal, args):
        if method == "resolve_grounding":
            if not isinstance(args.get("refs"), list):
                raise ValueError("refs is required and must be an array")
        elif method == "cancel":
            if not isinstance(args.get("invocation_id"), str) or not args["invocation_id"].strip():
                raise ValueError("invocation_id is required")
        elif method == "keep":
            if not isinstance(args.get("output"), str) or not args["output"].strip():
                raise ValueError("output is required")
            return service.keep(principal, output=args["output"], sources=args.get("sources") or [],
                **{key: args[key] for key in ("lens", "prompt", "grounding") if key in args})
        return web_call(service, principal, args)
    return call


def _simple(name, method, path, handler, properties, call, *, write=False, status=200):
    schema = {"type": "object", "properties": properties, "additionalProperties": False,
              "required": [{"resolve_grounding": "refs", "keep": "output", "cancel": "invocation_id"}[method]]}
    return OperationDescriptor(
        name=name, version=1, description="Use the shared Ask service to " + method.replace("_", " ") + ".",
        args_schema={"type": "object"}, principal="authenticated owner from the transport", effect="write" if write else "read",
        result="the Ask service result", refusals=_CONTRACT_REFUSALS + ("owner_required",), completion="synchronous",
        service="ask_service", method=method, owner_only=True, http=("POST", path), handler=handler,
        exposure=(f"http:POST {path}", f"mcp:{name}"), tool_schema=schema, call=_mcp_simple(method, call), web_call=call, http_status=status,
        authority="authority" if write else "work", announces_changes=False,
    )

ASK_OPERATIONS += (
    _simple("ask.resolve_grounding", "resolve_grounding", "/api/grounding/resolve", "api_resolve_grounding",
        {"refs": {"type": "array", "items": {"type": "string"}, "maxItems": 20}},
        lambda s, p, a: s.resolve_grounding(p, a.get("refs") if isinstance(a.get("refs"), list) else [])),
    _simple("ask.keep", "keep", "/api/ask/keep", "api_ask_keep",
        {"output": {"type": "string"}, "sources": {"type": "array", "items": {"type": "object"}},
         "lens": {"type": "string"}, "prompt": {"type": "string"}, "grounding": {"type": "object"}},
        lambda s, p, a: s.keep(p, str(a.get("output") or ""), a.get("context") if isinstance(a.get("context"), list) else [],
            lens=str(a.get("lens") or "Ask"), prompt=str(a.get("prompt") or ""), grounding=a.get("grounding")), write=True, status=201),
    _simple("ask.cancel", "cancel", "/api/ask/{invocation_id}/cancel", "api_cancel_ask",
        {"invocation_id": {"type": "string"}}, lambda s, p, a: s.cancel(p, str(a.get("invocation_id") or "")), write=True),
)
