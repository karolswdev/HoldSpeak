"""PHILO-16 (16b): the desk's windows on the one declared contract (the MCP rows).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), the way ``agent_operations.py`` carries Hand to agent. Each
row names its method on the hub's ``DeskWindowService``
(``services/desk_window_service.py``); the MCP family
``mcp/families/desk_windows.py`` invokes them, so an agent and the owner reach
one service. The HTTP routes (``web/routes/desk_windows.py``) call the same
service directly: the browser's verbs are a superset (move, resize, zoom,
send back, the Stage shelf) of the six tools here.

Admission: ``exempt``. A window is the owner's view, not a record: no kernel
operation and no receipt per drag (the owner's ledger-not-gate ruling: ceremony
only where it buys a receipt, provenance or undo). Every write announces itself
(one ``desk_changed`` frame, kind ``windows``).
"""
from __future__ import annotations

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

_PRINCIPAL = "derived by the transport (the MCP auth resolver); the service performs no principal check"
_EXEMPT = Admission("exempt", "A window is the owner's view of his desk, not a record: no receipt.")
_VALUE = {"anyOf": [{"type": "number"}, {"type": "string", "maxLength": 64}],
          "description": "Pixels (a number) or share+px (\"50% + 10\", \"-1/2\"); x and y from the view's centre."}
_RECT = {"type": "object", "properties": {"x": _VALUE, "y": _VALUE, "w": _VALUE, "h": _VALUE},
         "required": ["x", "y", "w", "h"], "additionalProperties": False}
_ID = {"type": "string", "minLength": 1, "maxLength": 200,
       "description": "The window id (for example chair:brief, zone:<id>, surface-people)."}
_REV = {"type": ["integer", "null"], "description": "Refuse the write when the window's revision is another one."}
_REFUSALS = _CONTRACT_REFUSALS + (
    "window_unknown: the desk does not know the window id", "window_id_invalid",
    "not_found: the window is not open", "window_stale: the revision changed (read again)",
    "geometry_invalid",
)
_ROW = ("{id, app, object_ref, x, y, w, h (share+px values or null), depth, minimized, zoomed, zoom, "
        "arranged, room, front, revision, updated_at}")


def _row(name: str, method: str, description: str, properties: dict, required: list, *,
         effect: str = "write", result: str = _ROW) -> OperationDescriptor:
    return OperationDescriptor(
        name=name,
        version=1,
        description=description,
        args_schema={"type": "object", "properties": properties, "required": required,
                     "additionalProperties": False},
        principal=_PRINCIPAL,
        effect=effect,
        result=result,
        refusals=_REFUSALS,
        completion=("synchronous; windows.list reads the state back; a write sends one desk_changed "
                    "frame (kind windows) and every open browser follows"),
        exposure=(f"mcp:desk_window.{name.split('.', 1)[1]}",),
        service="desk_window_service",
        method=method,
        admission=_EXEMPT,
    )


WINDOWS_LIST = _row(
    "windows.list", "list_windows",
    "List the open windows on the owner's desk, back to front, with the front one marked.",
    {}, [], effect="read",
    result="{windows: [" + _ROW + "], stage_shelf, revision, registry: {static, families}}",
)
WINDOWS_OPEN = _row(
    "windows.open", "open_window",
    "Open a window on the owner's desk, in front. An open window comes to the front.",
    {"window_id": _ID, "object_ref": {"type": ["string", "null"], "maxLength": 400},
     "geometry": {"anyOf": [_RECT, {"type": "null"}]}, "room": {"type": ["string", "null"], "maxLength": 200},
     "expected_revision": _REV},
    ["window_id"],
)
WINDOWS_CLOSE = _row(
    "windows.close", "close_window", "Close a window on the owner's desk.",
    {"window_id": _ID, "expected_revision": _REV}, ["window_id"], result="{id, closed: true}",
)
WINDOWS_RAISE = _row(
    "windows.raise", "raise_window", "Bring a window to the front of the owner's desk.",
    {"window_id": _ID, "expected_revision": _REV}, ["window_id"],
)
WINDOWS_ARRANGE = _row(
    "windows.arrange", "arrange_windows",
    "Set the rects of several windows in one change (a tile, a layout).",
    {"rects": {"type": "object", "additionalProperties": _RECT, "minProperties": 1,
               "description": "Window id to rect."},
     "expected_revisions": {"type": ["object", "null"], "additionalProperties": {"type": "integer"}}},
    ["rects"], result="{windows: [" + _ROW + "]}",
)
WINDOWS_SEAT = _row(
    "windows.seat", "seat_window",
    "Seat a window on the Dock (seated: true) or show it again in front (seated: false).",
    {"window_id": _ID, "seated": {"type": "boolean"}, "expected_revision": _REV}, ["window_id", "seated"],
)

DESK_WINDOW_OPERATIONS = (
    WINDOWS_LIST, WINDOWS_OPEN, WINDOWS_CLOSE, WINDOWS_RAISE, WINDOWS_ARRANGE, WINDOWS_SEAT,
)

#: MCP tool name -> operation name.
TOOL_OPERATIONS: dict[str, str] = {
    f"desk_window.{d.name.split('.', 1)[1]}": d.name for d in DESK_WINDOW_OPERATIONS
}

__all__ = ["DESK_WINDOW_OPERATIONS", "TOOL_OPERATIONS"]
