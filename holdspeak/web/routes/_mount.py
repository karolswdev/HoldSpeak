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
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
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
        parent.include_router(child, **kwargs)
        return
    for route in child.routes:
        path = getattr(route, "path", None)
        if path is not None and not path:
            name = getattr(route, "name", "unknown")
            raise FastAPIError(f"Prefix and path cannot be both empty (path operation: {name})")
    target.routes.extend(child.routes)
