"""HTTP routes produced from declared operations (2026-11-08, one contract).

A descriptor that declares ``http`` gets one handler here: the path
parameters over the JSON body (the query for a GET) are its arguments, the
call is ``OperationRegistry.invoke(..., shape="web")`` off the event loop, and
the answer is wrapped by the route module's own envelope (``answer``). The
handler keeps the name and the path-parameter signature a hand-written one
had, so the OpenAPI document and the API-surface module do not change.
"""
from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Iterable, Mapping

from fastapi import APIRouter, Request

from holdspeak.principals import UNAUTHENTICATED

Answer = Callable[..., Awaitable[Any]]


def _principal(request: Request) -> Any:
    """The edge's principal; none on the request is UNAUTHENTICATED, never the
    owner (Codex on #2051): the registry then refuses an owner-only operation
    with ``owner_required``."""
    return getattr(request.state, "principal", UNAUTHENTICATED)


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    return body if isinstance(body, dict) else {}


def _endpoint(descriptor: Any, registry: Callable[[], Any], answer: Answer, module: str) -> Callable[..., Any]:
    method, path = descriptor.http
    names = [part[1:-1] for part in path.split("/") if part.startswith("{")]

    async def endpoint(request: Request, **params: str) -> Any:
        principal = _principal(request)
        # A DELETE carries its arguments in the query (``?at=``), under any body.
        query = dict(request.query_params) if method in ("GET", "DELETE") else {}
        source = query if method == "GET" else {**query, **await _body(request)}
        args = {**source, **params}
        return await answer(lambda: registry().invoke(principal, descriptor.name, args, shape="web"),
                            status=descriptor.http_status)

    # FastAPI reads the path parameters and the operation id from the
    # signature and the name.
    endpoint.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
        [inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, annotation=str) for name in names]
        + [inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)],
        return_annotation=Any,
    )
    endpoint.__name__ = endpoint.__qualname__ = descriptor.handler or descriptor.name.replace(".", "_")
    endpoint.__module__ = module
    return endpoint


def operation_router(
    descriptors: Iterable[Any], registry: Callable[[], Any], answer: Answer, *, module: str,
    hand_written: Mapping[str, Callable[[Any], Callable[..., Any]]] | None = None,
) -> APIRouter:
    """One route per descriptor with ``http``, in the descriptors' order.

    ``registry``: the route module's ``OperationRegistry`` (``operations.for_context``),
    read at each call. ``hand_written``: descriptor name -> a builder of a
    handler the producer cannot make (an answer that is a file)."""
    router = APIRouter()
    for descriptor in descriptors:
        if descriptor.http is None:
            continue
        method, path = descriptor.http
        build = (hand_written or {}).get(descriptor.name)
        endpoint = build(descriptor) if build else _endpoint(descriptor, registry, answer, module)
        router.add_api_route(path, endpoint, methods=[method])
    return router


__all__ = ["operation_router"]
