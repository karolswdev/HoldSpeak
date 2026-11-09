"""HTTP routes produced from declared operations (2026-11-08, one contract).

A descriptor that declares ``http`` gets one handler here: the path
parameters over the JSON body over the query are its arguments, the
call is ``OperationRegistry.invoke(..., shape="web")`` off the event loop, and
the answer is wrapped by the route module's own envelope (``answer``). The
handler keeps the name and the path-parameter signature a hand-written one
had, so the OpenAPI document and the API-surface module do not change.
"""
from __future__ import annotations

import inspect
from typing import Any, Awaitable, Callable, Iterable, Mapping

from fastapi import APIRouter, Request

from holdspeak.operations import OperationRefused
from holdspeak.principals import UNAUTHENTICATED
from holdspeak.services.errors import ValidationError

Answer = Callable[..., Awaitable[Any]]


def _principal(request: Request) -> Any:
    """The edge's principal; none on the request is UNAUTHENTICATED, never the
    owner (Codex on #2051): the registry then refuses an owner-only operation
    with ``owner_required``."""
    return getattr(request.state, "principal", UNAUTHENTICATED)


class ContractRefusal(ValidationError, OperationRefused):
    """A contract refusal (``authority_in_arguments``, ``invalid_arguments``)
    as every route envelope already reads one: a ValidationError with status
    400 (the meeting, intel and aftercare envelopes; phone's ServiceError
    path, whose body keeps ``error``/``code``/``detail``), and still an
    OperationRefused (People). Before this a module whose envelope did not
    name OperationRefused answered the refusal with a 500 (#2066)."""

    def __init__(self, refused: OperationRefused) -> None:
        Exception.__init__(self, refused.detail)
        self.code, self.detail, self.operation = refused.code, refused.detail, refused.operation
        self.context = {"status": 400}
        # The refusal receipt of an admitted operation rides on the refusal.
        if getattr(refused, "kernel", None) is not None:
            self.kernel = refused.kernel


def _invoke(registry: Callable[[], Any], principal: Any, name: str, args: dict[str, Any],
            receipted: bool = False) -> Any:
    try:
        if not receipted:
            return registry().invoke(principal, name, args, shape="web")
        # An admitted operation answers with its ``operation_id`` and terminal
        # ``receipt`` beside its own answer (PHILO-9-02, ``_room_kernel``).
        result, kernel = registry().invoke_receipted(principal, name, args, shape="web")
        if isinstance(result, dict) and isinstance(kernel, dict):
            return {**result, **{key: kernel[key] for key in ("operation_id", "receipt") if key in kernel}}
        return result
    except ContractRefusal:
        raise
    except OperationRefused as refused:
        raise ContractRefusal(refused) from refused


def _typed_query(descriptor: Any, query: dict[str, str]) -> dict[str, Any]:
    """A query string's flags and counts as the schema types them (``?include_parked=true``)."""
    properties = descriptor.args_schema.get("properties") or {}
    typed: dict[str, Any] = {}
    for key, value in query.items():
        kind = (properties.get(key) or {}).get("type")
        kinds = set(kind) if isinstance(kind, (list, tuple)) else {kind}
        if "boolean" in kinds and value.strip().lower() in {"1", "true", "yes", "on", "0", "false", "no", "off"}:
            typed[key] = value.strip().lower() in {"1", "true", "yes", "on"}
        elif "integer" in kinds and value.strip().lstrip("-").isdigit():
            typed[key] = int(value)
        else:
            typed[key] = value
    return typed


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    return body if isinstance(body, dict) else {}


def _endpoint(descriptor: Any, registry: Callable[[], Any], answer: Answer, module: str,
              receipted: bool = False) -> Callable[..., Any]:
    method, path = descriptor.http
    # ``{resource_ref:path}``: the parameter is ``resource_ref`` (a path converter).
    names = [part[1:-1].split(":", 1)[0] for part in path.split("/") if part.startswith("{")]

    async def endpoint(request: Request, **params: str) -> Any:
        principal = _principal(request)
        # The query (``?at=``, ``?scope=``) is arguments on every method, under
        # any body: a DELETE carries them there, and a POST or PUT may name its
        # target there (the dictation blocks' ``?scope=&project_root=``); its
        # flags and counts are typed by the schema.
        query = _typed_query(descriptor, dict(request.query_params))
        source = query if method == "GET" else {**query, **await _body(request)}
        args = {**source, **params}

        def run() -> Any:
            # A body or query that names a path parameter with another value is a
            # conflicting request, refused by name inside the envelope, never
            # resolved in the path's favour (Codex on #2122: the old kernel decide
            # and receipt routes rejected a body ``operation_id``; the produced
            # route overwrote it).
            for name, value in params.items():
                if name in source and str(source[name]) != str(value):
                    raise ContractRefusal(OperationRefused(
                        "path_body_mismatch", descriptor.name,
                        f"{name} in the body ({source[name]!r}) is not the one in the path ({value!r})"))
            return _invoke(registry, principal, descriptor.name, args, receipted)

        return await answer(run, status=descriptor.http_status)

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
    hand_written: Mapping[str, Callable[[Any], Callable[..., Any]]] | None = None, receipted: bool = False,
) -> APIRouter:
    """One route per descriptor with ``http``, in the descriptors' order.

    ``registry``: the route module's ``OperationRegistry`` (``operations.for_context``),
    read at each call. ``hand_written``: descriptor name -> a builder of a
    handler the producer cannot make (an answer that is a file, an input the
    transport holds). ``receipted``: an admitted call's answer carries its
    ``operation_id`` and ``receipt``."""
    router = APIRouter()
    for descriptor in descriptors:
        if descriptor.http is None:
            continue
        method, path = descriptor.http
        build = (hand_written or {}).get(descriptor.name)
        endpoint = build(descriptor) if build else _endpoint(descriptor, registry, answer, module, receipted)
        router.add_api_route(path, endpoint, methods=[method])
    return router


__all__ = ["operation_router"]
