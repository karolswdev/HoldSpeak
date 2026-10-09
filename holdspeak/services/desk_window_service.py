"""PHILO-16 (16b): the hub owns the desk's windows (COMPOSITOR.md §13 L1).

Every browser is one view of the same desk, and an agent reaches the same
windows over MCP. One row per open window of the one owner desk
(``desk_windows``), and one desk row (``desk_window_desk``) for the depth
counter and Stage's shelf side.

* L3: depth is a counter the hub increments (``depth = ++highest``); the front
  window is derived (the shown window with the greatest depth). Nothing
  reorders a list, so a reload keeps the planes.
* L5: geometry is share+px values (``{"x","y","w","h"}``: a number of pixels
  or a string like ``"50% + 10"`` or ``"-1/2"``), resolved by each view.
  :func:`parse_value` is the browser's ``geometry.ts parseValue`` grammar.
* L2: every write bumps the row's ``revision`` and takes an optional
  ``expected_revision``; a stale one is refused (``window_stale``, HTTP 409),
  so a browser that anticipated a change re-reads and follows the hub.
* One write sends ONE ``desk_changed`` frame, kind ``windows``, one change per
  window id (``arrange`` names every id in the same frame). A write that
  changes nothing sends nothing.
* L10: the transports (``web/routes/desk_windows.py``, the MCP family
  ``mcp/families/desk_windows.py``) validate and serialize; this module is the
  behaviour. A window id the registry (:data:`STATIC_WINDOWS`,
  :data:`WINDOW_FAMILIES`) does not know is refused here.
"""
from __future__ import annotations

import json
import math
import re
import threading
from typing import Any, Callable, Iterable, Mapping, Optional

from .errors import ConflictError, NotFound, ValidationError

# ── the registry: the window ids the desk knows ─────────────────────────────
#
# The static windows: id -> the application (web/src/desk/applications.ts
# ``action`` where the window is an application; else the window's own name).
# ``tests/unit/test_desk_window_service.py`` fences that every ``windowId`` in
# applications.ts is here.
STATIC_WINDOWS: dict[str, str] = {
    "surface-places": "change-places",
    "intelligence:desk": "open-intelligence",
    "surface-dictation": "dictate",
    "ask:desk": "ask",
    "surface-meetings": "review-meetings",
    "conductor": "open-conductor",
    "surface-companion": "inspect-personas-and-coders",
    "surface-settings": "configure-settings",
    "surface-live": "record-live",
    "surface-cadence": "configure-cadence",
    "surface-setup": "configure-setup",
    "surface-constitutional-context": "open-constitutional-context",
    "surface-workbenches": "open-workbenches",
    "surface-components": "design-components",
    "surface-activity": "inspect-activity",
    "surface-project-memory": "open-project-memory",
    "surface-concierge": "open-concierge",
    "surface-project-setup": "project-setup",
    "surface-processes": "inspect-processes",
    "surface-commands": "configure-commands",
    "surface-people": "open-people",
    "surface-calendar-snapshot": "review-calendar-snapshot",
    # The Chair's four windows (chair/chairWindows.ts).
    "chair:needs": "chair",
    "chair:brief": "chair",
    "chair:week": "chair",
    "chair:capture": "chair",
    # Windows with a fixed id outside the application table.
    "ask": "ask",
    "attention": "attention",
    "inspector": "inspector",
    "session": "session",
    "trust": "trust",
    "lane": "lane",
    "agent-hand": "agent-hand",
    "delivery-board": "delivery",
    "delivery-terminal": "delivery",
    "delivery-dossier": "delivery",
    "drawer:parked": "drawer",
}

#: Object windows: an id prefix -> the application; the rest of the id is the
#: object the window shows (its ``object_ref``). Longest prefix first.
WINDOW_FAMILIES: dict[str, str] = {
    "drawer:project:": "drawer",
    "drawer-info:": "drawer-info",
    "conductor-info:": "conductor-info",
    "pullout:": "pullout",
    "zone:": "zone",
    "info:": "info",
    "roadmap:": "roadmap",
    "repository:": "repository",
    "workbench:": "workbench",
    "editor:": "editor",
    "schedule:": "schedule",
}

_WINDOW_ID = re.compile(r"^[A-Za-z0-9:_-]{1,200}$")
_MAX_REF = 400
_ROOM = re.compile(r"^[A-Za-z0-9:_.-]{0,200}$")


def window_app(window_id: str) -> tuple[str, Optional[str]]:
    """``(app, object_ref)`` of a known window id; refuses an unknown one."""
    wid = str(window_id or "")
    if not _WINDOW_ID.match(wid):
        raise ValidationError(f"Not a window id: {wid!r}", code="window_id_invalid")
    if wid in STATIC_WINDOWS:
        return STATIC_WINDOWS[wid], None
    for prefix in sorted(WINDOW_FAMILIES, key=len, reverse=True):
        if wid.startswith(prefix) and len(wid) > len(prefix):
            return WINDOW_FAMILIES[prefix], wid[len(prefix):]
    raise ValidationError(
        f"The desk does not know the window {wid!r}", code="window_unknown",
        context={"window_id": wid},
    )


def registry() -> dict[str, Any]:
    """The registry as data (the browser reads it with the window list)."""
    return {"static": dict(STATIC_WINDOWS), "families": dict(WINDOW_FAMILIES)}


# ── L5: share+px values (geometry.ts ``parseValue``, ported) ────────────────

_SHARE = re.compile(r"^([+-]?\d+(?:\.\d+)?)(?:\s*/\s*(\d+(?:\.\d+)?)|(%))$")
_PX = re.compile(r"^([+-]?\d+(?:\.\d+)?)(?:px)?$")
_VALUE_MAX_CHARS = 64
_PX_LIMIT = 100_000.0
_SHARE_LIMIT = 100.0


def parse_value(value: Any) -> tuple[float, float]:
    """``(share, px)`` of one geometry value; refuses what it does not read.

    A value is a finite number of pixels, or a string of at most one share
    term (``"50%"``, ``"-1/2"``) and at most one pixel term (``"10"``,
    ``"10px"``), joined by a spaced ``+`` or ``-``: ``"50% + 10"``,
    ``"1/2 - 4"``. The grammar of ``web/src/desk/compositor/geometry.ts``.
    """
    if isinstance(value, bool):
        raise ValidationError(f"Not a geometry value: {value!r}", code="geometry_invalid")
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number) or abs(number) > _PX_LIMIT:
            raise ValidationError(f"Not a geometry value: {value!r}", code="geometry_invalid")
        return 0.0, number
    if not isinstance(value, str) or not value.strip() or len(value) > _VALUE_MAX_CHARS:
        raise ValidationError(f"Not a geometry value: {value!r}", code="geometry_invalid")
    text = re.sub(r"\s+", " ", value).strip()
    terms = [re.sub(r"^([+-]) ", r"\1", term) for term in re.split(r" (?=[+-] )", text)]
    share = px = 0.0
    seen_share = seen_px = False
    for term in terms:
        match = _SHARE.match(term)
        if match:
            if seen_share:
                raise ValidationError(f"Two shares in {value!r}", code="geometry_invalid")
            seen_share = True
            number = float(match.group(1))
            if match.group(3):
                share = number / 100
            else:
                denominator = float(match.group(2))
                if denominator == 0:
                    raise ValidationError(f"A share over zero in {value!r}", code="geometry_invalid")
                share = number / denominator
            continue
        match = _PX.match(term)
        if match:
            if seen_px:
                raise ValidationError(f"Two pixel terms in {value!r}", code="geometry_invalid")
            seen_px = True
            px = float(match.group(1))
            continue
        raise ValidationError(f"Cannot read the geometry value {value!r}", code="geometry_invalid")
    if abs(share) > _SHARE_LIMIT or abs(px) > _PX_LIMIT:
        raise ValidationError(f"Geometry value out of range: {value!r}", code="geometry_invalid")
    return share, px


def _value(value: Any) -> Any:
    """A validated value, kept as written (a number stays a number)."""
    parse_value(value)
    return value if isinstance(value, str) else (int(value) if float(value).is_integer() else float(value))


def validate_rect(rect: Any, *, keys: Iterable[str] = ("x", "y", "w", "h")) -> dict[str, Any]:
    """The named axes of *rect*, each a valid share+px value."""
    if not isinstance(rect, Mapping):
        raise ValidationError("A rect is an object of x, y, w, h", code="geometry_invalid")
    wanted = tuple(keys)
    extra = set(rect) - {"x", "y", "w", "h"}
    if extra:
        raise ValidationError(f"Unknown rect keys: {sorted(extra)}", code="geometry_invalid")
    missing = [key for key in wanted if key not in rect]
    if missing:
        raise ValidationError(f"The rect needs {', '.join(missing)}", code="geometry_invalid")
    return {key: _value(rect[key]) for key in wanted}


# ── the service ─────────────────────────────────────────────────────────────

DESK_ID = "desk"
SHELF_SIDES = ("left", "right")
CHANGE_KIND = "windows"

#: One writer at a time in this process (the hub); each write is also one
#: ``BEGIN IMMEDIATE`` transaction, so a second process cannot interleave.
_WRITE_LOCK = threading.RLock()

Changes = Callable[[str, list[str]], None]


def _announce(op: str, ids: list[str]) -> None:
    """ONE ``desk_changed`` frame for one write: kind ``windows``, one change
    per id. Inside a write root (an HTTP request, an MCP call) it joins that
    root's frame; outside one this scope is the root. No hub, no bus: no-op."""
    from holdspeak.runtime.announce_scope import announce_scope
    from holdspeak.runtime.composition import notify_desk_changed

    with announce_scope():
        for window_id in ids:
            notify_desk_changed(CHANGE_KIND, window_id, op)


class WindowStale(ConflictError):
    """The caller's revision is not the row's: re-read and follow."""

    def __init__(self, window_id: str, expected: int, actual: int) -> None:
        super().__init__(
            f"The window {window_id} changed (revision {actual}, not {expected}); read it again",
            code="window_stale",
            context={"window_id": window_id, "expected_revision": expected, "revision": actual},
        )


class DeskWindowService:
    """The desk's windows. Construct per call or keep one: the state is the
    database; the write lock is shared by every instance in the process."""

    def __init__(self, db: Any, *, on_changed: Optional[Changes] = None) -> None:
        self._db = db
        self._on_changed = on_changed or _announce

    # ---- reads ---------------------------------------------------------

    def list(self) -> dict[str, Any]:
        """Every open window, back to front, the front derived; the desk row."""
        with self._db._connection() as conn:
            rows = self._rows(conn)
            desk = self._desk(conn)
        front = _front_id(rows)
        return {
            "windows": [_serialize(row, front) for row in rows],
            "stage_shelf": desk["stage_shelf"],
            "revision": desk["revision"],
            "registry": registry(),
        }

    def get(self, window_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            row = self._row(conn, window_id)
            if row is None:
                raise NotFound("window", window_id)
            front = _front_id(self._rows(conn))
        return _serialize(row, front)

    # ---- writes --------------------------------------------------------

    def open(
        self,
        window_id: str,
        app: Optional[str] = None,
        object_ref: Optional[str] = None,
        geometry: Optional[Mapping[str, Any]] = None,
        room: Optional[str] = None,
        *,
        expected_revision: Optional[int] = None,
    ) -> dict[str, Any]:
        """Open a window on top. Idempotent: an open window returns its row,
        shown (restored) and raised to the front."""
        known_app, known_ref = window_app(window_id)
        if app is not None and str(app) != known_app:
            raise ValidationError(
                f"The window {window_id} is a {known_app} window, not {app}",
                code="window_app_mismatch",
                context={"window_id": window_id, "app": known_app},
            )
        ref = known_ref if object_ref is None else str(object_ref)
        if ref is not None and len(ref) > _MAX_REF:
            raise ValidationError("object_ref is too long", code="window_ref_invalid")
        rect = validate_rect(geometry) if geometry is not None else None
        if room is not None and not _ROOM.match(str(room)):
            raise ValidationError(f"Not a room tag: {room!r}", code="window_room_invalid")

        def write(conn: Any, row: Optional[dict[str, Any]]) -> bool:
            if row is not None:
                changed = False
                if row["minimized"]:
                    conn.execute("UPDATE desk_windows SET minimized = 0 WHERE id = ?", (window_id,))
                    row["minimized"] = 0
                    changed = True
                rows = self._rows(conn)
                if _front_id(rows) != window_id:
                    self._set_depth(conn, window_id, self._next_depth(conn))
                    changed = True
                if rect is not None:
                    conn.execute(
                        "UPDATE desk_windows SET geometry_json = ?, arranged = 1 WHERE id = ?",
                        (json.dumps(rect), window_id),
                    )
                    changed = True
                if room is not None and room != row["room"]:
                    conn.execute("UPDATE desk_windows SET room = ? WHERE id = ?", (room, window_id))
                    changed = True
                return changed
            conn.execute(
                "INSERT INTO desk_windows (id, app, object_ref, geometry_json, depth, minimized,"
                " zoomed, arranged, room, revision) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, 0)",
                (window_id, known_app, ref, json.dumps(rect) if rect else None,
                 self._next_depth(conn), 1 if rect else 0, room),
            )
            return True

        return self._write("open", window_id, write, expected_revision, create=True)

    def close(self, window_id: str, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        """Close a window: its row leaves. Answers ``{"id", "closed": True}``."""
        window_app(window_id)
        with _WRITE_LOCK, self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row(conn, window_id)
            if row is None:
                raise NotFound("window", window_id)
            _check(window_id, row, expected_revision)
            conn.execute("DELETE FROM desk_windows WHERE id = ?", (window_id,))
        self._on_changed("close", [window_id])
        return {"id": window_id, "closed": True}

    def move(self, window_id: str, x: Any, y: Any, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        return self._geometry("move", window_id, validate_rect({"x": x, "y": y}, keys=("x", "y")), expected_revision)

    def resize(self, window_id: str, w: Any, h: Any, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        return self._geometry("resize", window_id, validate_rect({"w": w, "h": h}, keys=("w", "h")), expected_revision)

    def set_geometry(
        self, window_id: str, rect: Optional[Mapping[str, Any]], *, expected_revision: Optional[int] = None
    ) -> dict[str, Any]:
        """Set the whole rect (the user arranged it); ``None`` forgets it, and
        each view places the window at its default home again."""
        if rect is None:
            def forget(conn: Any, row: Optional[dict[str, Any]]) -> bool:
                assert row is not None
                if row["geometry_json"] is None and not row["arranged"]:
                    return False
                conn.execute(
                    "UPDATE desk_windows SET geometry_json = NULL, arranged = 0 WHERE id = ?", (window_id,)
                )
                return True

            return self._write("set_geometry", window_id, forget, expected_revision)
        return self._geometry("set_geometry", window_id, validate_rect(rect), expected_revision)

    def raise_(self, window_id: str, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        """``depth = ++highest``; a no-op when the window is already front."""
        def write(conn: Any, row: Optional[dict[str, Any]]) -> bool:
            if _front_id(self._rows(conn)) == window_id:
                return False
            self._set_depth(conn, window_id, self._next_depth(conn))
            return True

        return self._write("raise", window_id, write, expected_revision)

    def send_back(self, window_id: str, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        """The window goes under the lowest shown window (planes.ts ``sendBack``)."""
        def write(conn: Any, row: Optional[dict[str, Any]]) -> bool:
            assert row is not None
            shown = [r["depth"] for r in self._rows(conn) if r["id"] != window_id and not r["minimized"]]
            if not shown:
                return False
            lowest = min(shown)
            if row["depth"] < lowest:
                return False
            self._set_depth(conn, window_id, lowest - 1)
            return True

        return self._write("send_back", window_id, write, expected_revision)

    def seat(self, window_id: str, seated: bool, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        """Seat (minimize) keeps the depth; unseat shows the window and raises
        it to the front (planes.ts ``seat``/``unseat``)."""
        seated = bool(seated)

        def write(conn: Any, row: Optional[dict[str, Any]]) -> bool:
            assert row is not None
            if seated:
                if row["minimized"]:
                    return False
                conn.execute("UPDATE desk_windows SET minimized = 1 WHERE id = ?", (window_id,))
                return True
            changed = bool(row["minimized"])
            if changed:
                conn.execute("UPDATE desk_windows SET minimized = 0 WHERE id = ?", (window_id,))
            if _front_id(self._rows(conn)) != window_id:
                self._set_depth(conn, window_id, self._next_depth(conn))
                changed = True
            return changed

        return self._write("seat", window_id, write, expected_revision)

    def zoom(
        self,
        window_id: str,
        zoomed: bool,
        rect: Optional[Mapping[str, Any]] = None,
        *,
        expected_revision: Optional[int] = None,
    ) -> dict[str, Any]:
        """Zoom alternates between two remembered rects (C2): the normal rect
        stays untouched; the zoom rect is kept when given, and kept across an
        unzoom so the next zoom returns to it. A zoom raises the window."""
        zoomed = bool(zoomed)
        zoom_rect = validate_rect(rect) if rect is not None else None

        def write(conn: Any, row: Optional[dict[str, Any]]) -> bool:
            assert row is not None
            changed = False
            if bool(row["zoomed"]) != zoomed:
                conn.execute("UPDATE desk_windows SET zoomed = ? WHERE id = ?", (int(zoomed), window_id))
                changed = True
            if zoom_rect is not None and _loads(row["zoom_json"]) != zoom_rect:
                conn.execute("UPDATE desk_windows SET zoom_json = ? WHERE id = ?", (json.dumps(zoom_rect), window_id))
                changed = True
            if zoomed and _front_id(self._rows(conn)) != window_id:
                self._set_depth(conn, window_id, self._next_depth(conn))
                changed = True
            return changed

        return self._write("zoom", window_id, write, expected_revision)

    def arrange(
        self,
        rects: Mapping[str, Mapping[str, Any]],
        *,
        expected_revisions: Optional[Mapping[str, int]] = None,
    ) -> dict[str, Any]:
        """Many rects in ONE transaction and ONE ``desk_changed`` frame. Every
        id must be open; any stale revision refuses the whole arrangement."""
        if not isinstance(rects, Mapping) or not rects:
            raise ValidationError("arrange takes a map of window id to rect", code="geometry_invalid")
        validated = {}
        for window_id, rect in rects.items():
            window_app(window_id)
            validated[str(window_id)] = validate_rect(rect)
        expected = dict(expected_revisions or {})
        changed: list[str] = []
        with _WRITE_LOCK, self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for window_id, rect in validated.items():
                row = self._row(conn, window_id)
                if row is None:
                    raise NotFound("window", window_id)
                _check(window_id, row, expected.get(window_id))
                if _loads(row["geometry_json"]) == rect and row["arranged"]:
                    continue
                conn.execute(
                    "UPDATE desk_windows SET geometry_json = ?, arranged = 1, revision = revision + 1,"
                    " updated_at = datetime('now') WHERE id = ?",
                    (json.dumps(rect), window_id),
                )
                changed.append(window_id)
            rows = self._rows(conn)
        if changed:
            self._on_changed("arrange", changed)
        front = _front_id(rows)
        return {"windows": [_serialize(row, front) for row in rows if row["id"] in validated]}

    def set_stage_shelf(self, side: str, *, expected_revision: Optional[int] = None) -> dict[str, Any]:
        """Stage's shelf side for the desk (``left`` or ``right``)."""
        if side not in SHELF_SIDES:
            raise ValidationError(f"The shelf is left or right, not {side!r}", code="shelf_invalid")
        with _WRITE_LOCK, self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            desk = self._desk(conn)
            if expected_revision is not None and int(expected_revision) != desk["revision"]:
                raise WindowStale(DESK_ID, int(expected_revision), desk["revision"])
            changed = desk["stage_shelf"] != side
            if changed:
                conn.execute(
                    "UPDATE desk_window_desk SET stage_shelf = ?, revision = revision + 1,"
                    " updated_at = datetime('now') WHERE id = ?",
                    (side, DESK_ID),
                )
            desk = self._desk(conn)
        if changed:
            self._on_changed("stage_shelf", [DESK_ID])
        return {"stage_shelf": desk["stage_shelf"], "revision": desk["revision"]}

    # ---- the declared operations (desk_window_operations.py) -------------
    # The registry calls ``method(principal, **arguments)``; the principal is
    # the transport's and the service checks none (a window is the view).

    def list_windows(self, principal: Any) -> dict[str, Any]:
        return self.list()

    def open_window(self, principal: Any, window_id: str, object_ref: Optional[str] = None,
                    geometry: Optional[Mapping[str, Any]] = None, room: Optional[str] = None,
                    expected_revision: Optional[int] = None) -> dict[str, Any]:
        return self.open(window_id, None, object_ref, geometry, room, expected_revision=expected_revision)

    def close_window(self, principal: Any, window_id: str,
                     expected_revision: Optional[int] = None) -> dict[str, Any]:
        return self.close(window_id, expected_revision=expected_revision)

    def raise_window(self, principal: Any, window_id: str,
                     expected_revision: Optional[int] = None) -> dict[str, Any]:
        return self.raise_(window_id, expected_revision=expected_revision)

    def arrange_windows(self, principal: Any, rects: Mapping[str, Mapping[str, Any]],
                        expected_revisions: Optional[Mapping[str, int]] = None) -> dict[str, Any]:
        return self.arrange(rects, expected_revisions=expected_revisions)

    def seat_window(self, principal: Any, window_id: str, seated: bool,
                    expected_revision: Optional[int] = None) -> dict[str, Any]:
        return self.seat(window_id, seated, expected_revision=expected_revision)

    # ---- internals -----------------------------------------------------

    def _geometry(
        self, op: str, window_id: str, rect: dict[str, Any], expected_revision: Optional[int]
    ) -> dict[str, Any]:
        def write(conn: Any, row: Optional[dict[str, Any]]) -> bool:
            assert row is not None
            current = _loads(row["geometry_json"]) or {}
            merged = {**current, **rect}
            if merged == current and row["arranged"]:
                return False
            conn.execute(
                "UPDATE desk_windows SET geometry_json = ?, arranged = 1 WHERE id = ?",
                (json.dumps(merged), window_id),
            )
            return True

        return self._write(op, window_id, write, expected_revision)

    def _write(
        self,
        op: str,
        window_id: str,
        write: Callable[[Any, Optional[dict[str, Any]]], bool],
        expected_revision: Optional[int],
        *,
        create: bool = False,
    ) -> dict[str, Any]:
        window_app(window_id)
        with _WRITE_LOCK, self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row(conn, window_id)
            if row is None and not create:
                raise NotFound("window", window_id)
            if row is not None:
                _check(window_id, row, expected_revision)
            changed = write(conn, row)
            if changed:
                conn.execute(
                    "UPDATE desk_windows SET revision = revision + 1, updated_at = datetime('now')"
                    " WHERE id = ?",
                    (window_id,),
                )
            rows = self._rows(conn)
        if changed:
            self._on_changed(op, [window_id])
        front = _front_id(rows)
        return _serialize(next(r for r in rows if r["id"] == window_id), front)

    def _next_depth(self, conn: Any) -> int:
        """``++highest``: the desk's counter, never below a stored depth."""
        desk = self._desk(conn)
        top = conn.execute("SELECT COALESCE(MAX(depth), 0) FROM desk_windows").fetchone()[0]
        nxt = max(int(desk["highest_depth"]), int(top)) + 1
        conn.execute(
            "UPDATE desk_window_desk SET highest_depth = ?, updated_at = datetime('now') WHERE id = ?",
            (nxt, DESK_ID),
        )
        return nxt

    @staticmethod
    def _set_depth(conn: Any, window_id: str, depth: int) -> None:
        conn.execute("UPDATE desk_windows SET depth = ? WHERE id = ?", (depth, window_id))

    @staticmethod
    def _desk(conn: Any) -> dict[str, Any]:
        conn.execute("INSERT OR IGNORE INTO desk_window_desk (id) VALUES (?)", (DESK_ID,))
        row = conn.execute(
            "SELECT highest_depth, stage_shelf, revision FROM desk_window_desk WHERE id = ?", (DESK_ID,)
        ).fetchone()
        return {"highest_depth": row[0], "stage_shelf": row[1], "revision": row[2]}

    @staticmethod
    def _rows(conn: Any) -> list[dict[str, Any]]:
        return [dict(r) for r in conn.execute("SELECT * FROM desk_windows ORDER BY depth, id").fetchall()]

    @staticmethod
    def _row(conn: Any, window_id: str) -> Optional[dict[str, Any]]:
        row = conn.execute("SELECT * FROM desk_windows WHERE id = ?", (window_id,)).fetchone()
        return dict(row) if row is not None else None


def _check(window_id: str, row: Mapping[str, Any], expected: Optional[int]) -> None:
    if expected is None:
        return
    try:
        wanted = int(expected)
    except (TypeError, ValueError):
        raise ValidationError("expected_revision is a number", code="revision_invalid") from None
    if wanted != int(row["revision"]):
        raise WindowStale(window_id, wanted, int(row["revision"]))


def _front_id(rows: list[dict[str, Any]]) -> Optional[str]:
    """The shown window with the greatest depth (rows come back to front)."""
    shown = [r for r in rows if not r["minimized"]]
    return shown[-1]["id"] if shown else None


def _loads(raw: Any) -> Optional[dict[str, Any]]:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def _serialize(row: Mapping[str, Any], front: Optional[str]) -> dict[str, Any]:
    geometry = _loads(row["geometry_json"]) or {}
    return {
        "id": row["id"],
        "app": row["app"],
        "object_ref": row["object_ref"],
        "x": geometry.get("x"),
        "y": geometry.get("y"),
        "w": geometry.get("w"),
        "h": geometry.get("h"),
        "depth": int(row["depth"]),
        "minimized": bool(row["minimized"]),
        "zoomed": bool(row["zoomed"]),
        "zoom": _loads(row["zoom_json"]),
        "arranged": bool(row["arranged"]),
        "room": row["room"],
        "front": row["id"] == front,
        "revision": int(row["revision"]),
        "updated_at": row["updated_at"],
    }


#: The verbs on one window (the HTTP route's ``{verb}``; the MCP family's tools).
VERBS: tuple[str, ...] = (
    "open", "close", "move", "resize", "set_geometry", "raise", "send_back", "seat", "zoom",
)


def call_verb(svc: DeskWindowService, window_id: str, verb: str, args: Mapping[str, Any]) -> Any:
    """One verb on one window from a transport's arguments (HTTP body, MCP)."""
    rev = args.get("expected_revision")
    if verb == "open":
        return svc.open(window_id, args.get("app"), args.get("object_ref"), args.get("geometry"),
                        args.get("room"), expected_revision=rev)
    if verb == "close":
        return svc.close(window_id, expected_revision=rev)
    if verb == "move":
        return svc.move(window_id, args.get("x"), args.get("y"), expected_revision=rev)
    if verb == "resize":
        return svc.resize(window_id, args.get("w"), args.get("h"), expected_revision=rev)
    if verb == "set_geometry":
        return svc.set_geometry(window_id, args.get("rect"), expected_revision=rev)
    if verb == "raise":
        return svc.raise_(window_id, expected_revision=rev)
    if verb == "send_back":
        return svc.send_back(window_id, expected_revision=rev)
    if verb == "seat":
        return svc.seat(window_id, bool(args.get("seated", True)), expected_revision=rev)
    if verb == "zoom":
        return svc.zoom(window_id, bool(args.get("zoomed", True)), args.get("rect"), expected_revision=rev)
    raise NotFound("window verb", verb)


def default_desk_window_service() -> DeskWindowService:
    """The service over the hub's database (the one composition root)."""
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or

    return DeskWindowService(db_or(get_database))


__all__ = [
    "VERBS",
    "DeskWindowService",
    "call_verb",
    "STATIC_WINDOWS",
    "WINDOW_FAMILIES",
    "WindowStale",
    "default_desk_window_service",
    "parse_value",
    "registry",
    "validate_rect",
    "window_app",
]
