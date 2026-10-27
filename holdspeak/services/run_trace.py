"""What an agent CLI run used and did, in words (Betterment MCP slice M2).

Each tool call an agent CLI run makes with its run credential
(``agent:run:<run_id>``, ``intel/cli_engine.py``) reaches the hub through
``POST /api/mcp`` (``web/routes/mcp_http.py``). That route hands each answered
call to :func:`record_call`, which adds one ``agent_run_calls`` row: the tool,
what it did (``read``, ``write`` or ``prepare``), the object it touched as a
qualified ref with its title, and when. A refused call touched nothing and
adds no row; a list or a search names no one object and keeps ``ref`` empty.

An automation result reads the rows of the runs made for its item
(``cli_engine_runs.item_id``) as three lists (:func:`use_by_item`):

- ``looked_at``: the objects it read, by name;
- ``wrote``: the desk objects it changed; ``undo`` is true for an object the
  run made (the desk's own delete, with its Undo, takes it back);
- ``prepared``: the sends it prepared (``send_id``); he presses Send.

Betterment Q7 (Ask my whole desk) records the same rows for an Ask: a CLI
engine's runs are linked by the Ask's trace key (:func:`ask_trace`, set with
:func:`for_item` around the engine call), and the hub's own tool loop
(``thread_service``) records each call it serves with :func:`record_value`
under that key as the run id. :func:`use_by_trace` reads both.

MCP M5: an automation item on an HTTP engine whose server takes tool calls
runs the hub's tool loop (``services/engine_tool_loop``), which records each
call under the item's trace key (:func:`item_trace`); :func:`use_by_item`
reads those rows beside the CLI runs' rows.

A write here never breaks a call: a failed write is logged.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Mapping, Optional

from ..logging_config import get_logger
from ..timestamps import utc_now_iso

log = get_logger("services.run_trace")

READ = "read"
WRITE = "write"
PREPARE = "prepare"

#: ``desk.*`` kinds (plural, as the tools take them) to the ref kind.
_DESK_REF_KINDS = {
    "notes": "note",
    "decisions": "decision",
    "kbs": "knowledge",
    "directories": "zone",
    "workflows": "workflow",
    "chains": "sequence",
}
#: The ``desk.*`` kind's own id field (``note_id``, ...) in a record.
_DESK_ID_FIELDS = {
    "notes": "note_id",
    "decisions": "decision_id",
    "kbs": "kb_id",
    "directories": "directory_id",
    "workflows": "workflow_id",
    "chains": "chain_id",
}


#: The automation item the current engine call runs for ('' = none). The
#: workbench runner sets it around its engine call (:func:`for_item`); a CLI
#: run's ``cli_engine_runs`` row records it, so a result finds its runs. Kept
#: here, not in ``holdspeak.intel`` (that package costs ~0.3 s to import, and
#: the runner sets this inside a timed item).
_ITEM: ContextVar[str] = ContextVar("agent_run_item", default="")

# A window call is recorded after the dispatcher returns, while its useful
# undo state is the desk immediately before the call.  The MCP dispatcher
# captures that small read into this context slot; ``record_value`` consumes it
# when it writes the existing agent_run_calls row.  This keeps window history
# in the existing trace without a second ledger or a geometry cache.
_WINDOW_BEFORE: ContextVar[Optional[dict[str, Any]]] = ContextVar("agent_run_window_before", default=None)
_WINDOW_TOOLS = frozenset({
    "desk_window.open", "desk_window.close", "desk_window.raise",
    "desk_window.arrange", "desk_window.seat",
})


def _window_state(row: Mapping[str, Any]) -> dict[str, Any]:
    geometry = {
        key: row.get(key)
        for key in ("x", "y", "w", "h")
        if row.get(key) is not None
    }
    return {
        "id": str(row.get("id") or ""),
        "app": str(row.get("app") or ""),
        "object_ref": row.get("object_ref"),
        "geometry": geometry or None,
        "minimized": bool(row.get("minimized")),
        "room": row.get("room"),
        "revision": int(row.get("revision") or 0),
    }


def capture_window_before(name: str, arguments: Any, *, db: Any = None) -> None:
    """Capture the affected window rows before one admitted MCP write.

    This is deliberately a best-effort read.  A refusal or a broken database
    must still be handled by the normal dispatcher, and trace recording must
    never make the product call fail.
    """
    if name not in _WINDOW_TOOLS:
        return
    args = arguments if isinstance(arguments, Mapping) else {}
    if name.endswith(".arrange"):
        raw_ids = args.get("rects") if isinstance(args.get("rects"), Mapping) else {}
        ids = [str(value) for value in raw_ids]
    else:
        ids = [str(args.get("window_id") or "")]
    ids = [value for value in ids if value]
    try:
        if db is None:
            from ..db import get_database
            from ..runtime.composition import db_or

            db = db_or(get_database)
        from .desk_window_service import DeskWindowService

        rows = DeskWindowService(db).list().get("windows") or []
        by_id = {str(row.get("id")): _window_state(row) for row in rows if row.get("id")}
        _WINDOW_BEFORE.set({
            "tool": name,
            "ids": ids,
            "before": {window_id: by_id.get(window_id) for window_id in ids},
        })
    except Exception:
        _WINDOW_BEFORE.set({"tool": name, "ids": ids, "before": {window_id: None for window_id in ids}})


def _take_window_before() -> Optional[dict[str, Any]]:
    value = _WINDOW_BEFORE.get()
    _WINDOW_BEFORE.set(None)
    return value


@contextmanager
def for_item(item_id: str) -> Iterator[None]:
    """Name the automation item of the engine calls made inside this block."""
    token = _ITEM.set(str(item_id or ""))
    try:
        yield
    finally:
        _ITEM.reset(token)


def current_item() -> str:
    return _ITEM.get()


#: Tools whose object is not their family's name: ``door.add_item`` makes a
#: task (an action item, which opens in Follow-through).
_TOOL_REF_KINDS = {"door.add_item": "action_item"}
#: Writes the face can take back: a task it added is dismissed (Q7, Wrote).
_UNDO_OPS = {("action_item", "add_item")}

ASK_TRACE_PREFIX = "ask:"
ITEM_TRACE_PREFIX = "item:"


def ask_trace(invocation_id: str) -> str:
    """The trace key of one Ask (its invocation id), for its tool calls."""
    return ASK_TRACE_PREFIX + str(invocation_id or "")


def item_trace(item_id: str) -> str:
    """The trace key of one automation item run on an HTTP engine (MCP M5):
    the hub's tool loop (``services/engine_tool_loop``) records its calls
    under it, and :func:`use_by_item` reads them with the CLI runs' calls."""
    return ITEM_TRACE_PREFIX + str(item_id or "")


def _effect(name: str) -> str:
    from ..mcp.tools import is_read_tool

    if name == "channel.prepare":
        return PREPARE
    return READ if is_read_tool(name) else WRITE


def _answer_value(response: Any) -> Any:
    """The tool's value inside a JSON-RPC answer; None for an error or a refusal."""
    if not isinstance(response, Mapping) or "error" in response:
        return None
    result = response.get("result")
    if not isinstance(result, Mapping) or result.get("isError"):
        return None
    parts = [p for p in result.get("content") or [] if isinstance(p, Mapping) and p.get("type") == "text"]
    if not parts:
        return None
    try:
        return json.loads(str(parts[0].get("text") or ""))
    except ValueError:
        return None


def _records(value: Any) -> list[Mapping[str, Any]]:
    """The answer and the records one level inside it (``{"note": {...}}``)."""
    if not isinstance(value, Mapping):
        return []
    found = [value]
    for inner in value.values():
        if isinstance(inner, Mapping):
            found.append(inner)
    return found


def _title_of(record: Mapping[str, Any]) -> str:
    for key in ("title", "name", "display_name", "task"):
        text = " ".join(str(record.get(key) or "").split())
        if text:
            return text
    return ""


def _desk_object(arguments: Mapping[str, Any], value: Any) -> tuple[str, str]:
    kind = str(arguments.get("kind") or "")
    ref_kind = _DESK_REF_KINDS.get(kind)
    if ref_kind is None:
        return "", ""
    obj_id = str(arguments.get("id") or "")
    title = ""
    for record in _records(value):
        own = str(record.get("id") or record.get(_DESK_ID_FIELDS.get(kind, "")) or "")
        if not obj_id and own:
            obj_id = own
        if own and own == obj_id and not title:
            title = _title_of(record)
    if not title:
        data = arguments.get("data")
        if isinstance(data, Mapping):
            title = _title_of(data)
    return (f"{ref_kind}:{obj_id}" if obj_id else ""), title


#: The read kinds with no desk record behind them: their facts are the tool's.
_NO_LOCAL_RECORD = {"pr", "jira"}
_STATE_KEYS = ("state", "status", "lifecycle")
_AT_KEYS = ("updated_at", "updated", "updatedAt", "modified_at", "started_at", "created_at", "created")


def _read_facts(ref: str, value: Any) -> dict[str, str]:
    """The state and the time of the one record a read returned ("" when
    the tool said nothing about them). Only short words are kept."""
    obj_id = ref.split(":", 1)[1] if ":" in ref else ""
    records = _records(value)
    own = [r for r in records if str(r.get("id") or r.get("key") or r.get("number") or "") == obj_id]
    facts: dict[str, str] = {}
    for record in own or records[:1]:
        for key in _STATE_KEYS:
            word = record.get(key)
            if isinstance(word, Mapping):
                word = word.get("name") or word.get("value")
            if isinstance(word, str) and word.strip() and len(word) <= 40 and "state" not in facts:
                facts["state"] = word.strip()
        for key in _AT_KEYS:
            at = record.get(key)
            if isinstance(at, str) and at.strip() and len(at) <= 40 and "at" not in facts:
                facts["at"] = at.strip()
        if facts:
            break
    return facts


def _object(name: str, arguments: Mapping[str, Any], value: Any) -> tuple[str, str]:
    """``(ref, title)`` of the one object a call touched; ``("", "")`` when none."""
    if name.startswith("desk."):
        return _desk_object(arguments, value)
    # Project update tools return the update inside an envelope, while the
    # operation's generic changed-for projection quite correctly names the
    # owning project.  The automation trace needs the object the model
    # actually edited so the Project Update face can cite it.
    if name == "provider.github_pr_get" and isinstance(value, Mapping):
        # Ask hub gap 2: a pull request the tool read is named as the desk
        # names one (``pr:owner/repo#12``); it has no local record.
        repo = str(value.get("repository") or arguments.get("owner_repo") or "")
        number = value.get("number") or arguments.get("number")
        return (f"pr:{repo}#{number}" if repo and number else ""), _title_of(value)
    if name in {"project.draft_update", "project.update_draft", "project.publish_update"}:
        update_id = ""
        title = ""
        for record in _records(value):
            own = str(record.get("id") or record.get("update_id") or "")
            if not update_id and own:
                update_id = own
            if own == update_id and not title:
                title = _title_of(record)
        update_id = update_id or str(arguments.get("update_id") or "")
        return (f"project_update:{update_id}" if update_id else ""), title
    from .. import operations

    kind, obj_id, _op = operations.changed_for(name, arguments, value)
    if name in _TOOL_REF_KINDS:
        kind = _TOOL_REF_KINDS[name]
        record = value if isinstance(value, Mapping) else {}
        obj_id = str(record.get("id") or obj_id or "")
    if not obj_id:
        return "", ""
    title = ""
    for record in _records(value):
        own = str(record.get("id") or record.get(f"{kind}_id") or "")
        if own == obj_id:
            title = _title_of(record)
            if title:
                break
    return f"{kind}:{obj_id}", title


def _prepared(arguments: Mapping[str, Any], value: Any) -> tuple[str, str, dict[str, Any]]:
    send = value.get("send") if isinstance(value, Mapping) else None
    if not isinstance(send, Mapping) or not send.get("id"):
        return "", "", {}
    document = send.get("document_json") if isinstance(send.get("document_json"), Mapping) else {}
    title = _title_of(document) or str(send.get("document_ref") or arguments.get("document_ref") or "")
    return (
        str(send.get("document_ref") or arguments.get("document_ref") or ""),
        title,
        {"send_id": str(send["id"]), "destination": str(send.get("destination_name") or "")},
    )


def _window_title(window_id: str, row: Mapping[str, Any] | None = None) -> str:
    """A short face word for a window row, without exposing a raw id."""
    item = row or {}
    scope = str(item.get("object_ref") or "")
    if scope:
        scope = scope.split("?", 1)[0]
        if ":" in scope:
            scope = scope.split(":", 1)[1]
        words = " ".join(scope.replace(":", " ").replace("_", " ").replace("-", " ").split())
        if words:
            return words.title()
    app = str(item.get("app") or "")
    names = {
        "open-people": "People", "review-meetings": "Meetings", "chair": "Today",
        "chair-capture": "Capture", "open-conductor": "Agents",
    }
    if app in names:
        return names[app]
    return "Window" if not window_id else "Window"


def _window_result_rows(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        return {}
    rows: list[Any] = []
    if isinstance(value.get("windows"), list):
        rows.extend(value["windows"])
    if value.get("id"):
        rows.append(value)
    return {
        str(row.get("id")): _window_state(row)
        for row in rows
        if isinstance(row, Mapping) and row.get("id")
    }


def _window_event(
    name: str, run_id: str, arguments: Mapping[str, Any], value: Any,
) -> tuple[list[tuple[str, str, dict[str, Any]]], dict[str, Any]]:
    """Return one trace row per affected window and its event summary."""
    before = _take_window_before() or {}
    ids = list(before.get("ids") or [])
    if not ids:
        if name.endswith(".arrange") and isinstance(arguments.get("rects"), Mapping):
            ids = [str(value) for value in arguments["rects"]]
        elif arguments.get("window_id"):
            ids = [str(arguments["window_id"])]
    previous = before.get("before") if isinstance(before.get("before"), Mapping) else {}
    previous = {str(key): row for key, row in previous.items()}
    after_rows = _window_result_rows(value)
    op = name.rsplit(".", 1)[-1]
    after_revision = int(value.get("revision") or 0) if isinstance(value, Mapping) else 0
    if op == "close":
        after_rows = {}
    event_windows: list[dict[str, Any]] = []
    rows: list[tuple[str, str, dict[str, Any]]] = []
    for window_id in ids:
        old = previous.get(window_id)
        new = after_rows.get(window_id)
        event_windows.append({
            "id": window_id,
            "before": old,
            "after": new,
            "after_revision": after_revision if new is None else int(new.get("revision") or 0),
        })
        row = new or old or {"id": window_id}
        ref = f"window:{window_id}"
        title = _window_title(window_id, row)
        rows.append((ref, title, {"op": op}))
    for index, (ref, title, detail) in enumerate(rows):
        rows[index] = (ref, title, {
            **detail,
            "window_undo": {
                "group": str(run_id),
                "operation": op,
                "windows": event_windows,
            },
        })
    return rows, {"operation": op, "windows": event_windows, "count": len(event_windows)}


def record_call(run_id: str, name: str, arguments: Any, response: Any, *, db: Any = None) -> None:
    """Add one row for an answered tool call of the run ``run_id``."""
    if not run_id or not name:
        return
    value = _answer_value(response)
    if value is None:
        return
    record_value(run_id, name, arguments, value, db=db)


def record_value(run_id: str, name: str, arguments: Any, value: Any, *, db: Any = None) -> None:
    """Add one row for a tool call that answered ``value`` (the tool's own
    value, not a JSON-RPC answer): the hub's tool loop records its calls so."""
    if not run_id or not name or value is None:
        return
    args = arguments if isinstance(arguments, Mapping) else {}
    try:
        effect = _effect(name)
        detail: dict[str, Any] = {}
        rows: list[tuple[str, str, dict[str, Any]]] = []
        window_summary: dict[str, Any] | None = None
        if effect == PREPARE:
            ref, title, detail = _prepared(args, value)
            rows = [(ref, title, detail)] if ref else []
        elif name in _WINDOW_TOOLS:
            rows, window_summary = _window_event(name, str(run_id), args, value)
        else:
            ref, title = _object(name, args, value)
            if effect == WRITE:
                detail = {"op": name.rsplit(".", 1)[-1]}
            elif effect == READ and ref.split(":", 1)[0] in _NO_LOCAL_RECORD:
                # Ask hub gap 2: a read keeps the facts the tool returned
                # (a PR's or a Jira item's state and updated time), so its
                # reference row can say them with no local record.
                detail = _read_facts(ref, value)
            rows = [(ref, title, detail)] if ref else []
        if db is None:
            from ..db import get_database

            db = get_database()
        with db._connection() as conn:
            called_at = utc_now_iso()
            for ref, title, row_detail in rows:
                if window_summary is not None:
                    event = row_detail.get("window_undo")
                    if isinstance(event, Mapping):
                        row_detail = {"op": row_detail.get("op") or "", "window_undo": event}
                conn.execute(
                    "INSERT INTO agent_run_calls (run_id, tool, effect, ref, title, detail_json, called_at)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (str(run_id), str(name), effect, ref, title, json.dumps(row_detail, sort_keys=True), called_at),
                )
    except Exception as exc:  # never break the call for its record
        log.warning(f"agent run call not recorded: {exc}")


def _row(ref: str, title: str) -> dict[str, Any]:
    return {"ref": ref, "label": title or "Untitled", "kind": ref.split(":", 1)[0]}


def _fold(rows: Any, key_of: Any) -> dict[str, dict[str, list[dict[str, Any]]]]:
    used: dict[str, dict[str, Any]] = {}
    for row in rows:
        lists = used.setdefault(str(key_of(row)), {"looked_at": {}, "wrote": {}, "prepared": {}})
        try:
            detail = json.loads(row["detail_json"] or "{}")
        except ValueError:
            detail = {}
        ref, title, effect = str(row["ref"]), str(row["title"] or ""), str(row["effect"])
        if effect == READ:
            entry = lists["looked_at"].setdefault(ref, _row(ref, title))
            for fact in ("state", "at"):
                if isinstance(detail.get(fact), str) and detail[fact]:
                    entry[fact] = detail[fact]
        elif effect == WRITE:
            entry = lists["wrote"].setdefault(ref, {**_row(ref, title), "undo": False})
            op = str(detail.get("op") or "")
            kind = ref.split(":", 1)[0]
            if (op == "create" and kind in _DESK_REF_KINDS.values()) or (kind, op) in _UNDO_OPS:
                entry["undo"] = True
            if op == "delete":
                entry["undo"] = False
            event = detail.get("window_undo")
            if kind == "window" and isinstance(event, Mapping):
                entries = lists.setdefault("_window_events", [])
                entries.append((ref, title, dict(event), op))
        else:
            send_id = str(detail.get("send_id") or "")
            entry = lists["prepared"].setdefault(send_id or ref, {
                **_row(ref, title), "send_id": send_id, "destination": str(detail.get("destination") or ""),
            })
        if title:
            entry["label"] = title
    folded: dict[str, dict[str, Any]] = {}
    for key, lists in used.items():
        events = lists.pop("_window_events", [])
        if events:
            aggregate: dict[str, dict[str, Any]] = {}
            operations: list[tuple[str, int, int, int]] = []
            first_ref = ""
            for ref, title, event, op in events:
                if not first_ref:
                    first_ref = ref
                windows = event.get("windows") if isinstance(event.get("windows"), list) else []
                opened_now = sum(1 for item in windows if isinstance(item, Mapping) and item.get("before") is None and item.get("after") is not None)
                closed_now = sum(1 for item in windows if isinstance(item, Mapping) and item.get("before") is not None and item.get("after") is None)
                operations.append((op, len(windows), opened_now, closed_now))
                for item in windows:
                    if not isinstance(item, Mapping) or not item.get("id"):
                        continue
                    window_id = str(item["id"])
                    if window_id not in aggregate:
                        aggregate[window_id] = {
                            "id": window_id, "before": item.get("before"),
                        }
                    aggregate[window_id]["after"] = item.get("after")
                    aggregate[window_id]["after_revision"] = item.get("after_revision")
            undo_windows = list(aggregate.values())
            undoable = any(op in {"open", "close", "arrange"} for op, *_rest in operations)
            for ref, entry in lists["wrote"].items():
                if ref.startswith("window:"):
                    entry["window_undo"] = {"group": key, "windows": undo_windows, "primary": ref == first_ref}
                    entry["undo"] = undoable and ref == first_ref
            opened = sum(created for op, _count, created, _closed in operations if op == "open")
            closed = sum(removed for op, _count, _created, removed in operations if op == "close")
            summary: list[str] = []
            if opened:
                summary.append(f"Opened {opened} window{'s' if opened != 1 else ''}")
            if closed:
                summary.append(f"Closed {closed} window{'s' if closed != 1 else ''}")
            if any(op == "arrange" for op, _count, _created, _closed in operations):
                summary.append("Tiled" if any(count > 1 for op, count, _created, _closed in operations if op == "arrange") else "Moved")
            if summary:
                lists["wrote_summary"] = " · ".join(summary)
        output: dict[str, Any] = {
            name: list(values.values())
            for name, values in lists.items()
            if name in {"looked_at", "wrote", "prepared"}
        }
        if lists.get("wrote_summary"):
            output["wrote_summary"] = lists["wrote_summary"]
        folded[key] = output
    return folded


def use_by_item(db: Any, item_ids: list[str]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Looked at, Wrote and Prepared for each item whose runs touched an object.

    An item none of whose calls named an object is absent (the card then
    draws nothing). One object is listed once per list, by its newest title.
    """
    ids = [str(i) for i in item_ids if str(i or "").strip()]
    if not ids or db is None:
        return {}
    traces = [item_trace(i) for i in ids]
    try:
        with db._connection() as conn:
            rows = conn.execute(
                """SELECT COALESCE(r.item_id, substr(c.run_id, ?)) AS item_id,
                          c.effect, c.ref, c.title, c.detail_json
                   FROM agent_run_calls c LEFT JOIN cli_engine_runs r ON r.run_id = c.run_id
                   WHERE c.ref != '' AND (
                     r.item_id IN (SELECT value FROM json_each(?))
                     OR c.run_id IN (SELECT value FROM json_each(?)))
                   ORDER BY c.id""",
                (len(ITEM_TRACE_PREFIX) + 1, json.dumps(ids), json.dumps(traces)),
            ).fetchall()
    except Exception as exc:
        log.info(f"agent run calls not read: {exc}")
        return {}
    return _fold(rows, lambda row: row["item_id"])


def use_by_trace(db: Any, keys: list[str]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Looked at, Wrote and Prepared for each trace key (Q7: an Ask), from the
    calls recorded under the key itself (the hub's tool loop) and from the
    CLI runs linked to it (``cli_engine_runs.item_id``)."""
    ids = [str(k) for k in keys if str(k or "").strip()]
    if not ids or db is None:
        return {}
    try:
        with db._connection() as conn:
            rows = conn.execute(
                """SELECT COALESCE(r.item_id, c.run_id) AS trace, c.effect, c.ref, c.title, c.detail_json
                   FROM agent_run_calls c LEFT JOIN cli_engine_runs r ON r.run_id = c.run_id
                   WHERE c.ref != '' AND (
                     c.run_id IN (SELECT value FROM json_each(?))
                     OR r.item_id IN (SELECT value FROM json_each(?)))
                   ORDER BY c.id""",
                (json.dumps(ids), json.dumps(ids)),
            ).fetchall()
    except Exception as exc:
        log.info(f"agent run calls not read: {exc}")
        return {}
    return _fold(rows, lambda row: row["trace"])


def run_id_of(identity: Optional[str]) -> str:
    """The run id of an ``agent:run:<run_id>`` identity ('' for any other)."""
    from .conductor_launch import RUN_IDENTITY_PREFIX

    text = str(identity or "")
    return text[len(RUN_IDENTITY_PREFIX):] if text.startswith(RUN_IDENTITY_PREFIX) else ""


def launch_key_of(identity: Optional[str]) -> str:
    """Betterment AG10: ``launch:<id>`` for an ``agent:launch:<id>`` identity
    (a launched agent's credential); '' for any other. Its calls are kept
    under that key (``use_by_trace``)."""
    from .conductor_launch import LAUNCH_IDENTITY_PREFIX

    text = str(identity or "")
    return f"launch:{text[len(LAUNCH_IDENTITY_PREFIX):]}" if text.startswith(LAUNCH_IDENTITY_PREFIX) else ""


__all__ = [
    "PREPARE", "READ", "WRITE", "ask_trace", "launch_key_of", "current_item", "for_item", "item_trace", "record_call", "record_value",
    "run_id_of", "use_by_item", "use_by_trace",
]
