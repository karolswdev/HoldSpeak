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


def _object(name: str, arguments: Mapping[str, Any], value: Any) -> tuple[str, str]:
    """``(ref, title)`` of the one object a call touched; ``("", "")`` when none."""
    if name.startswith("desk."):
        return _desk_object(arguments, value)
    # Project update tools return the update inside an envelope, while the
    # operation's generic changed-for projection quite correctly names the
    # owning project.  The automation trace needs the object the model
    # actually edited so the Project Update face can cite it.
    if name in {"project.draft_update", "project.update_draft", "project.publish_update"}:
        update_id = str(arguments.get("update_id") or "")
        title = ""
        for record in _records(value):
            own = str(record.get("id") or record.get("update_id") or "")
            if not update_id and own:
                update_id = own
            if own == update_id and not title:
                title = _title_of(record)
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
        if effect == PREPARE:
            ref, title, detail = _prepared(args, value)
        else:
            ref, title = _object(name, args, value)
            if effect == WRITE:
                detail = {"op": name.rsplit(".", 1)[-1]}
        if db is None:
            from ..db import get_database

            db = get_database()
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO agent_run_calls (run_id, tool, effect, ref, title, detail_json, called_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(run_id), str(name), effect, ref, title, json.dumps(detail, sort_keys=True), utc_now_iso()),
            )
    except Exception as exc:  # never break the call for its record
        log.warning(f"agent run call not recorded: {exc}")


def _row(ref: str, title: str) -> dict[str, Any]:
    return {"ref": ref, "label": title or "Untitled", "kind": ref.split(":", 1)[0]}


def _fold(rows: Any, key_of: Any) -> dict[str, dict[str, list[dict[str, Any]]]]:
    used: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    for row in rows:
        lists = used.setdefault(str(key_of(row)), {"looked_at": {}, "wrote": {}, "prepared": {}})
        try:
            detail = json.loads(row["detail_json"] or "{}")
        except ValueError:
            detail = {}
        ref, title, effect = str(row["ref"]), str(row["title"] or ""), str(row["effect"])
        if effect == READ:
            entry = lists["looked_at"].setdefault(ref, _row(ref, title))
        elif effect == WRITE:
            entry = lists["wrote"].setdefault(ref, {**_row(ref, title), "undo": False})
            op = str(detail.get("op") or "")
            kind = ref.split(":", 1)[0]
            if (op == "create" and kind in _DESK_REF_KINDS.values()) or (kind, op) in _UNDO_OPS:
                entry["undo"] = True
            if op == "delete":
                entry["undo"] = False
        else:
            send_id = str(detail.get("send_id") or "")
            entry = lists["prepared"].setdefault(send_id or ref, {
                **_row(ref, title), "send_id": send_id, "destination": str(detail.get("destination") or ""),
            })
        if title:
            entry["label"] = title
    return {
        key: {name: list(values.values()) for name, values in lists.items()}
        for key, lists in used.items()
    }


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
