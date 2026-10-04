"""Every HTTP write announces itself: one ``desk_changed`` frame, at the root.

A write used to reach the other open windows only when its service was built
with ``on_changed``. Most were not (action items, meeting rename, People,
follow-through, proposals, threads ...), so a second window stayed stale until
a reload. This middleware is the root for the routes that do not go through
``OperationRegistry.invoke``: a mutating ``/api`` request that answers 2xx sends
one frame, unless its service (or the registry) sent one during the request.

No route wires the bus for itself, so a new write route cannot be silent
(fence: ``tests/integration/test_every_write_announces.py``).
"""
from __future__ import annotations

from typing import Any

from holdspeak.runtime.composition import announce_scope

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

#: Not desk data, or a transport of its own. ``/api/mcp`` carries reads and
#: writes in one POST; its writes announce at ``OperationRegistry.invoke``.
#: Dictation, speech and device traffic is frequent and changes no desk object.
_QUIET_PREFIXES = (
    "/api/mcp",
    "/api/dictation",
    "/api/tts",
    "/api/mesh",
    "/api/delivery/node",
    "/api/kernel",
    "/api/principals",
    "/api/setup/runtime-test",
)

#: A POST that only reads or tests (the last path segment).
_QUIET_VERBS = frozenset({
    "preview", "probe", "resolve", "validate", "validate-repo", "validate-scope",
    "test", "check", "search", "evaluate", "dry-run", "suggest", "heartbeat",
    "preview-use-default",
})

_KIND = {"people": "person", "all_action_items": "action_item"}


def is_announced_write(method: str, path: str) -> bool:
    """A mutating ``/api`` request whose success changes something a window shows."""
    if method not in _WRITE_METHODS or not path.startswith("/api/"):
        return False
    if any(path == prefix or path.startswith(prefix + "/") for prefix in _QUIET_PREFIXES):
        return False
    return path.rstrip("/").rsplit("/", 1)[-1] not in _QUIET_VERBS


def changed(method: str, path: str, path_params: Any) -> tuple[str, str, str]:
    """``(kind, id, op)`` from the request: ``/api/meetings/{id}`` PUT is ``meeting <id> update``."""
    segment = path.split("/")[2].replace("-", "_") if path.count("/") >= 2 else ""
    kind = _KIND.get(segment) or (segment[:-1] if segment.endswith("s") and len(segment) > 3 else segment)
    params = list(path_params.values()) if isinstance(path_params, dict) else []
    obj_id = str(params[0]) if params else ""
    if method == "DELETE":
        op = "delete"
    elif method == "POST" and not params:
        op = "create"
    else:
        op = "update"
    return kind or "desk", obj_id, op


def install(app: Any) -> None:
    """Add the middleware to *app* (the hub calls this once)."""

    @app.middleware("http")
    async def _announce_writes(request: Any, call_next: Any) -> Any:
        method, path = request.method, request.url.path
        if not is_announced_write(method, path):
            return await call_next(request)
        with announce_scope() as announce:
            response = await call_next(request)
            if 200 <= response.status_code < 300:
                announce(*changed(method, path, request.scope.get("path_params")))
        return response
