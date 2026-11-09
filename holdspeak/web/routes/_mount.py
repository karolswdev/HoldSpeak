"""Mount a router without building each route a second time.

`APIRouter.include_router` builds a new `APIRoute` for every route of the
child (the dependency analysis and the pydantic adapters again), once per
level of nesting. The hub has about 700 routes at up to three levels, so one
`MeetingWebServer` built each route about 2.5 times: 0.47 s of CPU per hub,
paid by every test that builds a hub (measured 2026-10-03).

When the include changes nothing on the routes (no prefix, tags, dependencies,
responses, response class or operation-id function on the call, the parent or
the child), the child's route objects are
already the final routes, so they are moved to the parent as they are. Any
other case goes to the real `include_router`.

One difference: a moved route does not read `app.dependency_overrides`.
Nothing in this repository uses it.

Two more costs of a route are paid once per process, not once per hub
(:func:`_build_once`, 2026-11-09): the pydantic adapter of each parameter and
answer type, and the path regex. Every hub builds the same 777 routes, so the
second hub and every later one (each test) builds no adapter and compiles no
regex.
"""
from __future__ import annotations

import functools
import typing
from typing import Any

import fastapi.routing
import starlette.routing
from fastapi import APIRouter
from fastapi._compat import v2 as _fastapi_v2
from fastapi.datastructures import DefaultPlaceholder
from fastapi.exceptions import FastAPIError
from starlette.routing import _DefaultLifespan


def mount_router(parent: Any, child: APIRouter, **kwargs: Any) -> None:
    """Add ``child``'s routes to ``parent`` (an app or a router)."""
    target: APIRouter = getattr(parent, "router", parent)
    plain = (
        not kwargs
        and not target.prefix
        and not target.tags
        and not target.dependencies
        and not target.responses
        and not target.callbacks
        and not target.deprecated
        and target.include_in_schema
        # A response class or an operation-id function set on the parent or
        # on the child changes each route at include time (Astra on #763).
        and all(
            isinstance(setting, DefaultPlaceholder)
            for router in (target, child)
            for setting in (router.default_response_class, router.generate_unique_id_function)
        )
        and not child.on_startup
        and not child.on_shutdown
        and isinstance(child.lifespan_context, _DefaultLifespan)
    )
    if not plain:
        before = target.lifespan_context
        parent.include_router(child, **kwargs)
        if not child.on_startup and not child.on_shutdown and isinstance(child.lifespan_context, _DefaultLifespan):
            # The include wrapped the parent's lifespan around a child's that
            # runs nothing; keep the plain one, so the parent mounts plain later.
            target.lifespan_context = before
        return
    for route in child.routes:
        path = getattr(route, "path", None)
        if path is not None and not path:
            name = getattr(route, "name", "unknown")
            raise FastAPIError(f"Prefix and path cannot be both empty (path operation: {name})")
    target.routes.extend(child.routes)


def _pydantic_schemas(annotation: Any, seen: list | None = None) -> list:
    """Each pydantic class inside ``annotation``, with its current core schema."""
    seen = [] if seen is None else seen
    if isinstance(annotation, type):
        schema = annotation.__dict__.get("__pydantic_core_schema__")
        if schema is not None:
            seen.append((annotation, schema))
    for inner in typing.get_args(annotation):
        _pydantic_schemas(inner, seen)
    return seen


def _build_once() -> None:
    """Share the adapters and path regexes a route build makes (once per process).

    FastAPI's ``ModelField`` builds one pydantic ``TypeAdapter`` for each
    parameter and answer of each route from three inputs: the annotation, the
    metadata and the field settings (``fastapi._compat.v2.asdict``). An
    adapter has no state, so two fields with equal inputs share one. The key
    holds the annotation object itself (two classes never share) and every
    other input by ``repr`` (a value with no ``repr`` of its own carries its
    address, so it never matches another). A class made inside a function is
    not kept; a model rebuilt after its adapter was made (a new constraint)
    has a new core schema, so it gets a new adapter (Astra on #763).
    ``compile_path`` is a pure function of the path string; Python's ``re``
    cache holds 512 patterns, fewer than the hub's routes, so each build
    compiled every regex again.

    This was a test-only seam in ``tests/conftest.py`` (2026-10-03); the hub
    start pays the same cost, so it lives here for both (2026-11-09).
    """
    model_field = _fastapi_v2.ModelField
    if getattr(model_field.__post_init__, "_holdspeak_shared", False):
        return
    build_adapter = model_field.__post_init__
    kept: dict[Any, tuple[Any, list]] = {}

    def shared_adapter(self: Any) -> None:
        try:
            info = _fastapi_v2.asdict(self.field_info)
            annotation = info["annotation"]
            if "<locals>" in repr(annotation) or len(kept) > 5000:
                raise TypeError
            key = (
                annotation,
                tuple(repr(item) for item in info["metadata"]),
                tuple(sorted((name, repr(value)) for name, value in info["attributes"].items())),
                repr(self.config),
            )
            entry = kept.get(key)
        except Exception:  # an unhashable, local or unexpected input: its own adapter
            return build_adapter(self)
        if entry is not None and all(
            cls.__dict__.get("__pydantic_core_schema__") is schema for cls, schema in entry[1]
        ):
            self._type_adapter = entry[0]
            return
        build_adapter(self)
        kept[key] = (self._type_adapter, _pydantic_schemas(annotation))

    shared_adapter._holdspeak_shared = True  # type: ignore[attr-defined]
    model_field.__post_init__ = shared_adapter  # type: ignore[method-assign]
    compile_path = functools.lru_cache(maxsize=None)(starlette.routing.compile_path)
    starlette.routing.compile_path = compile_path  # type: ignore[assignment]
    fastapi.routing.compile_path = compile_path  # type: ignore[attr-defined]


_build_once()
