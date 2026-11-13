"""The desk on the one declared contract: its windows and its display requests (2026-11-08).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one
``DeskWindowService`` verb once: its call, its HTTP method and path, and (for
the tools an agent has) its MCP tool schema. ``web/routes/desk_windows.py``
produces the routes and ``mcp/families/declared.py`` the tools from these
rows, both through ``OperationRegistry.invoke``.

ONE display protocol. The hub drives the compositor two ways, both here:

* a WINDOW verb writes a row (open, close, move, ... arrange, the Stage
  shelf) and the service announces it: one ``desk_changed`` frame, kind
  ``windows``; a write that changed nothing sends none (``announces_changes``);
* a DISPLAY REQUEST (``desk.mark``, ``desk.press``, ``desk.say``,
  ``desk.scroll``) is no row: the service sends one ``desk_request`` frame
  ``{request_id, op, args}`` and answers ``{request_id}`` at once. The
  compositor (``web/src/desk/compositor/requests.ts``, the executor the Walk
  runs too) does it and posts ``{done, reason?}`` to
  ``desk.request.result``; ``desk.request.read`` returns it once it is there.

Admission: ``exempt``. A window is the owner's view, not a record: no receipt
per drag (the ledger-not-gate ruling). The arguments schema is any object: the
service validates, as it did behind the hand-written routes; an MCP call is
validated against its tool schema by the MCP transport. Every window verb is a
tool (``desk_window.<verb>``); the compositor's answer is a route only. ``desk.press`` is
owner-only (it presses a part of his desk); mark, say and scroll are ``work``.
Imported through ``holdspeak.operations`` first (it imports this module).
"""
from __future__ import annotations

from holdspeak.held_arguments import held_arguments, text, hidden, word_count, constant, normalizer

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver); the service checks none"
_EXEMPT = Admission("exempt", "A window is the owner's view of his desk, not a record: no receipt.")
_VALUE = {"anyOf": [{"type": "number"}, {"type": "string", "maxLength": 64}],
          "description": "Pixels (a number) or share+px (\"50% + 10\", \"-1/2\"); x and y from the view's centre."}
_RECT = {"type": "object", "properties": {"x": _VALUE, "y": _VALUE, "w": _VALUE, "h": _VALUE},
         "required": ["x", "y", "w", "h"], "additionalProperties": False}
_ID = {"type": "string", "minLength": 1, "maxLength": 200,
       "description": "The window id (for example chair:brief, zone:<id>, pullout:people:<id>)."}
_REV = {"type": ["integer", "null"], "description": "Refuse the write when the window's revision is another one."}
_REFUSALS = _CONTRACT_REFUSALS + (
    "window_unknown: the desk does not know the window id", "window_id_invalid",
    "not_found: the window is not open", "window_stale: the revision changed (read again)",
    "window_not_on_hub: no view can open this window from a row",
    "geometry_invalid",
)
_ROW = ("{id, app, object_ref, x, y, w, h (share+px values or null), depth, minimized, zoomed, zoom, "
        "arranged, room, front, revision, updated_at}")
_WINDOW_DONE = ("synchronous; desk_window.list reads the state back; a write sends one desk_changed "
                "frame (kind windows) and every open browser follows")
_W = "/api/desk/windows/{window_id}"


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        tool: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (), effect: str = "write",
        result: str = _ROW, completion: str = _WINDOW_DONE, refusals: tuple[str, ...] = _REFUSALS,
        owner_only: bool = False, authority: str = "work", thread: Optional[str] = None, facts: Optional[Mapping[str, Any]] = None) -> OperationDescriptor:
    """One verb. ``tool``: the MCP tool's properties (None: HTTP only); the
    path's ids are required, then ``required``."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool_name = name if name.startswith("desk.") else f"desk_window.{name.split('.', 1)[1]}"
    schema = None
    if tool is not None:
        properties = {**{key: (_ID if key == "window_id" else {"type": "string", "minLength": 1}) for key in ids},
                      **dict(tool)}
        schema = {**dict(facts or {}), "type": "object", "properties": properties, "required": ids + list(required),
                  "additionalProperties": False, "$id": f"holdspeak://mcp/{tool_name}@1"}
    exposure = (f"http:{http[0]} {http[1]}",) + ((f"mcp:{tool_name}",) if schema is not None else ())
    if name.startswith("windows.") and effect == "write" and name != "windows.restore":
        action = call
        call = lambda s, p, a: s.with_undo(name.split(".", 1)[1], lambda: action(s, p, a))
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect=effect, result=result, refusals=refusals, completion=completion, exposure=exposure,
        service="desk_window_service", method=method, admission=_EXEMPT, announces_changes=True,
        owner_only=owner_only, call=call, http=http, handler=handler, tool_schema=schema,
        authority=authority, thread=thread,
    )


def window_arguments(args: dict[str, Any], *, flag: str) -> dict[str, Any]:
    result = {**args, flag: bool(args.get(flag, True))}
    if flag == "zoomed" and not result[flag]:
        result.pop("rect", None)
    return result


def _rev(args: Mapping[str, Any]) -> Any:
    return args.get("expected_revision")


# ── the windows ──────────────────────────────────────────────────────────

WINDOW_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("windows.restore", "restore", ("POST", "/api/desk/windows/restore"), "api_desk_windows_restore",
        lambda s, p, a: s.restore(a),
        "Undo one captured window change. Keep later window changes. Owner only.", owner_only=True,
        authority="authority", refusals=_REFUSALS + ("owner_required",), result="{windows}"),
    _op("windows.list", "list", ("GET", "/api/desk/windows"), "api_desk_windows", lambda s, p, a: s.list(),
        "List the owner's open windows, back to front, with the front one marked. Use registry.static for canonical app window ids and registry.families for object windows; use a returned object's object_ref as its scope.",
        tool={}, effect="read", thread="evidence_read",
        result=("{windows: [" + _ROW + "], stage_shelf, shelf_revision, revision (the desk's), adopted, "
                "registry: {static, families, not_on_hub}}")),
    _op("windows.arrange", "arrange", ("POST", "/api/desk/windows/arrange"), "api_desk_windows_arrange",
        lambda s, p, a: s.arrange(a.get("rects") or {}, expected_revisions=a.get("expected_revisions")),
        "Arrange several listed windows in one atomic change. The x and y zero is the view centre. For two full-height side-by-side windows, use left {x:-1/2, y:-1/2, w:1/2, h:1/1} and right {x:0, y:-1/2, w:1/2, h:1/1}; x:1/2 starts at the far edge and is off-band, and y:0 is the vertical centre. Values are share+px strings such as 50% + 10 or -1/2; pass each window's current revision when available.",
        tool={"rects": {"type": "object", "additionalProperties": _RECT,
                        "description": "Window id to rect (at least one; an empty map is refused by name)."},
              "expected_revisions": {"type": ["object", "null"], "additionalProperties": {"type": "integer"}}},
        required=("rects",), thread="effect_proposal", result="{windows: [" + _ROW + "]}",
        facts=held_arguments('Arrange windows',
                constant('Scope', 'Listed windows'),
                hidden('rects', 'Windows and positions', 'secret'),
                hidden('expected_revisions', 'Saved revisions', 'token'))),
    _op("windows.stage_shelf", "set_stage_shelf", ("POST", "/api/desk/windows/stage-shelf"),
        "api_desk_windows_shelf",
        lambda s, p, a: s.set_stage_shelf(str(a.get("side") or ""), expected_revision=_rev(a)),
        "Put Stage's shelf on the left or the right of the desk.", result="{stage_shelf, revision}",
        tool={"side": {"enum": ["left", "right"]}, "expected_revision": _REV}, required=("side",),
        thread="effect_proposal", facts=held_arguments('Move the Stage shelf',
                text('side', 'Side'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.open", "open", ("POST", _W + "/open"), "api_desk_window_open",
        lambda s, p, a: s.open(a.get("window_id"), a.get("app"), a.get("object_ref"), a.get("geometry"),
                               a.get("room"), expected_revision=_rev(a)),
        "Open a registry window on the owner's desk, in front. Use window_id from registry.static or a registry.families prefix; use pullout:people:<id> with object_ref people:<id>:prep for a person's prep, or surface-meetings with meeting:<id>?view=review for a meeting; pass object_ref to scope it.",
        tool={"object_ref": {"type": ["string", "null"], "maxLength": 400},
              "geometry": {"anyOf": [_RECT, {"type": "null"}]}, "room": {"type": ["string", "null"], "maxLength": 200},
              "expected_revision": _REV}, thread="effect_proposal",
        facts=held_arguments('Open a window',
                hidden('window_id', 'Window', 'secret'),
                hidden('object_ref', 'Object ref', 'secret'),
                hidden('geometry', 'Geometry', 'secret'),
                hidden('room', 'Room', 'secret'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.close", "close", ("POST", _W + "/close"), "api_desk_window_close",
        lambda s, p, a: s.close(a.get("window_id"), expected_revision=_rev(a)),
        "Close one open window from the owner's desk. Use the id and revision returned by windows.list.",
        tool={"expected_revision": _REV}, thread="effect_proposal", result="{id, closed: true, revision}",
        facts=held_arguments('Close a window',
                hidden('window_id', 'Window', 'secret'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.move", "move", ("POST", _W + "/move"), "api_desk_window_move",
        lambda s, p, a: s.move(a.get("window_id"), a.get("x"), a.get("y"), expected_revision=_rev(a)),
        "Move one window (x and y, share+px values).",
        tool={"x": _VALUE, "y": _VALUE, "expected_revision": _REV}, required=("x", "y"), thread="effect_proposal", facts=held_arguments('Move a window',
                hidden('window_id', 'Window', 'secret'),
                text('x', 'Across'),
                text('y', 'Down'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.resize", "resize", ("POST", _W + "/resize"), "api_desk_window_resize",
        lambda s, p, a: s.resize(a.get("window_id"), a.get("w"), a.get("h"), expected_revision=_rev(a)),
        "Resize one window (w and h, share+px values).",
        tool={"w": _VALUE, "h": _VALUE, "expected_revision": _REV}, required=("w", "h"), thread="effect_proposal", facts=held_arguments('Resize a window',
                hidden('window_id', 'Window', 'secret'),
                text('w', 'Width'),
                text('h', 'Height'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.set_geometry", "set_geometry", ("POST", _W + "/set_geometry"), "api_desk_window_set_geometry",
        lambda s, p, a: s.set_geometry(a.get("window_id"), a.get("rect"), expected_revision=_rev(a)),
        "Set one window's whole rect, or none (the desk places it).",
        tool={"rect": {"anyOf": [_RECT, {"type": "null"}]}, "expected_revision": _REV}, required=("rect",),
        thread="effect_proposal", facts=held_arguments('Place a window',
                hidden('window_id', 'Window', 'secret'),
                text('rect.x', 'Across'),
                text('rect.y', 'Down'),
                text('rect.w', 'Width'),
                text('rect.h', 'Height'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.raise", "raise_", ("POST", _W + "/raise"), "api_desk_window_raise",
        lambda s, p, a: s.raise_(a.get("window_id"), expected_revision=_rev(a)),
        "Bring one listed window to the front of the owner's desk. Use its id and revision from windows.list.",
        tool={"expected_revision": _REV}, thread="effect_proposal",
        facts=held_arguments('Bring a window to the front',
                hidden('window_id', 'Window', 'secret'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.send_back", "send_back", ("POST", _W + "/send_back"), "api_desk_window_send_back",
        lambda s, p, a: s.send_back(a.get("window_id"), expected_revision=_rev(a)),
        "Send one window to the back of the desk.",
        tool={"expected_revision": _REV}, thread="effect_proposal", facts=held_arguments('Send a window to the back',
                hidden('window_id', 'Window', 'secret'),
                hidden('expected_revision', 'Saved revision', 'token'))),
    _op("windows.seat", "seat", ("POST", _W + "/seat"), "api_desk_window_seat",
        lambda s, p, a: s.seat(a.get("window_id"), window_arguments(a, flag="seated")["seated"], expected_revision=_rev(a)),
        "Seat a window on the Dock (seated: true) or show it again in front (seated: false).",
        tool={"seated": {"type": "boolean"}, "expected_revision": _REV}, required=("seated",),
        thread="effect_proposal", facts={**normalizer('holdspeak.desk_operations:window_arguments', flag='seated'), **held_arguments('Seat a window',
                hidden('window_id', 'Window', 'secret'),
                text('seated', 'On the Dock'),
                hidden('expected_revision', 'Saved revision', 'token'))}),
    _op("windows.zoom", "zoom", ("POST", _W + "/zoom"), "api_desk_window_zoom",
        lambda s, p, a: s.zoom(a.get("window_id"), window_arguments(a, flag="zoomed")["zoomed"], window_arguments(a, flag="zoomed").get("rect"),
                               expected_revision=_rev(a)),
        "Zoom one window (zoomed, optional rect) or take the zoom off.",
        tool={"zoomed": {"type": "boolean"}, "rect": {"anyOf": [_RECT, {"type": "null"}]}, "expected_revision": _REV},
        required=("zoomed",), thread="effect_proposal", facts={**normalizer('holdspeak.desk_operations:window_arguments', flag='zoomed'), **held_arguments('Zoom a window',
                hidden('window_id', 'Window', 'secret'),
                text('zoomed', 'Zoom'),
                hidden('rect', 'Position', 'secret'),
                hidden('expected_revision', 'Saved revision', 'token'))}),
)


# ── the display requests ─────────────────────────────────────────────────

_REQUEST_REFUSALS = _CONTRACT_REFUSALS + ("ValidationError: words or target missing",
                                          "NotFound: unknown desk request (the hub keeps the last 50)")
_REQUEST_SENT = "{request_id}"
_REQUEST_DONE = ("at once: one desk_request frame {request_id, op, args}; the desk answers "
                 "{done, reason?, spoken?} and desk.request.read returns it")
_PART = {"target": {"type": "string", "minLength": 1, "maxLength": 400,
                    "description": "A data-testid, or a CSS selector, of the part."},
         "window": {"type": "string", "maxLength": 200,
                    "description": "The window the part is in: an app key or a window id (chair:needs)."},
         "thing": {"type": "string", "maxLength": 80,
                   "description": "What the part is (\"people rows\"): the desk says \"No <thing> here yet\" when it is not there."}}
_WORDS = {"words": {"type": "string", "minLength": 1, "maxLength": 400}}


def _request(op: str) -> Call:
    return lambda s, p, a: s.request(op, a)


REQUEST_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("desk.presence", "presence", ("POST", "/api/desk/presence"), "desk_presence",
        lambda s, p, a: s.presence(a.get("front"), a.get("visible")),
        "The Desk reports its visible front window. HTTP only; owner only.", result="{ok: true}",
        owner_only=True, authority="authority", refusals=_REFUSALS + ("owner_required",), completion="synchronous"),
    _op("desk.arrivals.seen", "arrivals_seen", ("POST", "/api/desk/needs-you/seen"), "api_desk_needs_you_seen",
        lambda s, p, a: s.arrivals_seen(a.get("meeting_ids")),
        "The Desk marks the arrivals it showed. HTTP only; owner only.", result="{success: true, seen}",
        owner_only=True, authority="authority", refusals=_REFUSALS + ("owner_required",), completion="synchronous"),
    _op("desk.mark", "request", ("POST", "/api/desk/requests/mark"), "api_desk_request_mark", _request("mark"),
        "Mark one part of the owner's desk with the Walk's halo, with optional words, for a few seconds. The part is searched only in its window.",
        tool={**_PART, **_WORDS}, required=("target",), result=_REQUEST_SENT, completion=_REQUEST_DONE,
        refusals=_REQUEST_REFUSALS, thread="effect_proposal", facts=held_arguments('Mark a Desk part',
                hidden('target', 'Part', 'secret'),
                hidden('window', 'Window', 'secret'),
                text('thing', 'Thing'),
                word_count('words', 'Words'))),
    _op("desk.press", "request", ("POST", "/api/desk/requests/press"), "api_desk_request_press", _request("press"),
        "Press one part of the owner's desk as the Walk's guide does (the part looks pressed, then the click lands). Owner only.",
        tool={**_PART, **_WORDS}, required=("target",), result=_REQUEST_SENT, completion=_REQUEST_DONE,
        refusals=_REQUEST_REFUSALS + ("owner_required",), owner_only=True, authority="authority", facts=held_arguments('Press a Desk part',
                hidden('target', 'Part', 'secret'),
                hidden('window', 'Window', 'secret'),
                text('thing', 'Thing'),
                word_count('words', 'Words'),
                constant('Allowed', 'Press this part'),
                constant('For', "Owner's Desk"))),
    _op("desk.say", "request", ("POST", "/api/desk/requests/say"), "api_desk_request_say", _request("say"),
        "Show and speak one line through the Desk voice. With no voice, the words stay and spoken is false.",
        tool=_WORDS, required=("words",), result=_REQUEST_SENT, completion=_REQUEST_DONE,
        refusals=_REQUEST_REFUSALS, thread="effect_proposal", facts=held_arguments('Speak on the Desk',
                word_count('words', 'Words'))),
    _op("desk.scroll", "request", ("POST", "/api/desk/requests/scroll"), "api_desk_request_scroll",
        _request("scroll"), "Scroll one part of the owner's desk into view.",
        tool=_PART, required=("target",), result=_REQUEST_SENT, completion=_REQUEST_DONE,
        refusals=_REQUEST_REFUSALS, thread="effect_proposal", facts=held_arguments('Show a Desk part',
                hidden('target', 'Part', 'secret'),
                hidden('window', 'Window', 'secret'),
                text('thing', 'Thing'))),
    _op("desk.request.replay", "replay_request", ("POST", "/api/desk/requests/{request_id}/replay"),
        "api_desk_request_replay", lambda s, p, a: s.replay_request(a.get("request_id")),
        "Replay an unanswered mark, say or scroll after reconnect. The id stays the same. A press cannot replay.",
        tool={}, thread="effect_proposal", result=_REQUEST_SENT, completion=_REQUEST_DONE,
        refusals=_REQUEST_REFUSALS + ("request_not_replayable",), facts=held_arguments('Replay a Desk request',
                hidden('request_id', 'Request', 'secret'))),
    _op("desk.request.read", "read_request", ("GET", "/api/desk/requests/{request_id}"), "api_desk_request_read",
        lambda s, p, a: s.read_request(a.get("request_id")),
        "Read one display request: answered false until the desk answers, then done and the reason.",
        tool={}, effect="read", result="{request_id, op, answered} (then done, reason when not done, and spoken for say)",
        completion="synchronous",
        refusals=_REQUEST_REFUSALS, thread="evidence_read"),
    _op("desk.request.result", "request_result", ("POST", "/api/desk/requests/{request_id}/result"),
        "api_desk_request_result",
        lambda s, p, a: s.request_result(a.get("request_id"), a.get("done"), a.get("reason"), a.get("spoken")),
        "The desk's answer to one display request (the compositor posts it).",
        result="{request_id, op, answered: true, done} (plus spoken for say, and reason when not done)", completion="synchronous",
        refusals=_REQUEST_REFUSALS + ("owner_required",), owner_only=True, authority="authority"),
)

DESK_DISPLAY_OPERATIONS: tuple[OperationDescriptor, ...] = WINDOW_OPERATIONS + REQUEST_OPERATIONS

#: The window verbs on one window (the HTTP routes' last segment).
WINDOW_VERBS: tuple[str, ...] = tuple(d.http[1].rsplit("/", 1)[1] for d in WINDOW_OPERATIONS
                                      if d.http and d.http[1].startswith(_W))

#: MCP tool name -> operation name (``scripts/operation_parity.py`` reads this).
TOOL_OPERATIONS: dict[str, str] = {d.tool_name: d.name for d in DESK_DISPLAY_OPERATIONS if d.tool_schema is not None}

__all__ = ["DESK_DISPLAY_OPERATIONS", "REQUEST_OPERATIONS", "TOOL_OPERATIONS", "WINDOW_OPERATIONS", "WINDOW_VERBS"]
