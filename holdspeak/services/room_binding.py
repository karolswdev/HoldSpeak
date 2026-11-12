"""Saved-content bindings for the Room's answers and removals.

Like Program answer bindings, these are returned by the read and checked
under the write transaction. A content revision covers legacy rows without
adding a second revision counter or relying on second-resolution timestamps.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .errors import ConflictError

BINDING_SCHEMA = {
    "type": "object",
    "properties": {"id": {"type": "string"}, "revision": {"type": "string"}},
    "required": ["id", "revision"], "additionalProperties": False,
    "description": "Required saved binding from the object's last read. Missing or stale: nothing changes.",
}


def room_binding(row: Mapping[str, Any], *related: Any) -> dict[str, str]:
    saved = dict(row)
    saved.pop("binding", None)
    revision = hashlib.sha256(json.dumps(
        [saved, *related], sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()
    return {"id": str(saved["id"]), "revision": revision}


def check_room_binding(binding: Any, current: Mapping[str, Any]) -> None:
    if not isinstance(binding, dict) or binding != dict(current):
        raise ConflictError(
            "This item changed or its saved version is missing. Nothing changed. Read again.",
            code="answer_stale", context={"status": 409},
        )


def watch_binding(row: Mapping[str, Any], source_words: Any = None) -> dict[str, str]:
    # Bind the saved specification and observation content shown beside Remove.
    # A timestamp-only refresh does not change what the source said.
    row = dict(row)
    row["enabled"] = bool(row.get("enabled"))
    for key in ("query", "trigger", "snapshot"):
        value = row.get(key + "_json")
        row[key + "_json"] = json.loads(value or "{}") if isinstance(value, str) else (row.get(key) or {})
    return room_binding({key: row.get(key) for key in (
        "id", "revision", "name", "intent", "query_json", "trigger_json",
        "state", "enabled", "project_id", "evaluation_cadence_minutes",
        "subject_kind", "trigger_kind", "mode", "provider_connection_id",
        "connector_id", "query_kind", "snapshot_json", "last_error",
    )}, source_words)
