"""Every HTTP write announces itself: one ``desk_changed`` frame, at the root.

A write used to reach the other open windows only when its service was built
with ``on_changed``. Most were not (action items, meeting rename, People,
follow-through, proposals, threads ...), so a second window stayed stale until
a reload. This middleware is the root for the routes that do not go through
``OperationRegistry.invoke``: a mutating ``/api`` request that answers 2xx sends
one frame. Announcements made by its services or by the registry during the
request are held and leave in that same frame (``changes`` names each).

No route wires the bus for itself, so a new write route cannot be silent
(fence: ``tests/integration/test_every_write_announces.py``).
"""
from __future__ import annotations

from typing import Any

from holdspeak.runtime.announce_scope import announce_scope

_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

#: The ONLY mutating routes that send no frame of their own, each by its exact
#: method and route template, with the reason. No prefix and no suffix rule: a
#: route that is not named here announces. A service announcement made inside
#: one of these requests still goes out (as one frame).
QUIET_ROUTES: dict[tuple[str, str], str] = {
    # A transport, not a write: reads and writes share this POST. Its writes
    # announce at OperationRegistry.invoke or in their services.
    ("POST", "/api/mcp"): "MCP transport; writes announce at the registry",
    # Read-like: the POST carries a question; nothing a window shows is stored.
    ("POST", "/api/activity/project-rules/preview"): "read-like: previews a rule",
    ("POST", "/api/authority/evaluate"): "read-like: evaluates an operation",
    ("POST", "/api/channels/preview"): "read-like: channel.preview is effect=read",
    ("POST", "/api/dictation/dry-run"): "read-like: runs the pipeline on text, stores nothing",
    ("POST", "/api/grounding/resolve"): "read-like: resolves references",
    ("POST", "/api/inference/assignments/preview-use-default"): "read-like: previews an assignment",
    ("POST", "/api/intents/preview"): "read-like: previews a route",
    ("POST", "/api/providers/confluence/validate"): "read-like: asks the provider",
    ("POST", "/api/providers/github/validate-repo"): "read-like: asks the provider",
    ("POST", "/api/providers/jira/search"): "read-like: asks the provider",
    ("POST", "/api/providers/jira/validate-scope"): "read-like: asks the provider",
    # Noise: voice and machine traffic, many per minute, no desk object changes.
    ("POST", "/api/dictation/transcribe"): "noise: one per utterance",
    ("POST", "/api/dictation/remote"): "noise: one per utterance",
    ("POST", "/api/dictation/floor/claim"): "noise: microphone floor",
    ("POST", "/api/dictation/floor/release"): "noise: microphone floor",
    ("POST", "/api/dictation/mic/open"): "noise: microphone state",
    ("POST", "/api/dictation/mic/close"): "noise: microphone state",
    ("POST", "/api/dictation/preview/type"): "noise: types the preview text",
    ("POST", "/api/dictation/preview/discard"): "noise: drops the preview text",
    ("POST", "/api/dictation/wake/type"): "noise: types the wake text",
    ("POST", "/api/tts"): "noise: speech output",
    ("POST", "/api/tts/download"): "noise: speech model download",
    ("POST", "/api/delivery/node/hello"): "noise: node traffic",
    ("POST", "/api/delivery/node/heartbeat"): "noise: node traffic, periodic",
    ("POST", "/api/delivery/node/disconnect"): "noise: node traffic",
    ("POST", "/api/mesh/relay/claim"): "noise: node polling",
    ("POST", "/api/mesh/relay/{job_id}/complete"): "noise: node traffic",
    ("POST", "/api/mesh/relay/{job_id}/fail"): "noise: node traffic",
    ("POST", "/api/kernel/executor/claim"): "noise: executor polling",
    ("POST", "/api/kernel/executor/operations/{operation_id}/receipt"): "noise: executor traffic",
    ("POST", "/api/setup/first-value/{attempt_id}/event"): "noise: setup progress ticks",
    # Each Room writes this by itself when it opens. No window shows it live,
    # and a frame for it made the Room re-read and erase its catch-up list.
    ("POST", "/api/projects/{project_id}/room/read"): "noise: the Room's own read marker",
}

_KIND = {"people": "person", "all_action_items": "action_item"}


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
        if method not in _WRITE_METHODS or not path.startswith("/api/"):
            return await call_next(request)
        # One scope for the request: every announcement inside it is held and
        # leaves as ONE frame when the request ends.
        with announce_scope() as announce:
            response = await call_next(request)
            route = getattr(request.scope.get("route"), "path", None)
            if 200 <= response.status_code < 300 and (method, route) not in QUIET_ROUTES:
                announce(*changed(method, path, request.scope.get("path_params")))
        return response
