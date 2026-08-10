"""Serialized journal record allocation and persistence helpers."""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Mapping

from .model import KernelRefused, forbidden_content

_HEAD_LIMIT = 120
_EVENT_FIELDS = (
    "stream", "stream_sequence", "event_id", "operation_id", "process_id",
    "correlation_id", "causation_id", "event_type", "event_version", "refs",
    "privacy_class", "head", "timestamp", "previous_sha256",
)


def json_encode(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def record_hash(record: Mapping[str, Any]) -> str:
    material = {field: record[field] for field in _EVENT_FIELDS}
    return "sha256:" + hashlib.sha256(json_encode(material).encode()).hexdigest()


def append_record(
    connection: Any, append_lock: Any, clock: Any, event_type: str, operation_id: str,
    *, refs: tuple[str, ...] = (), head: str = "", privacy_class: str = "private",
    stream: str = "operations", process_id: str = "", correlation_id: str = "",
    causation_id: str = "",
) -> dict[str, Any]:
    metadata = {"refs": refs, "head": head}
    if forbidden_content(metadata):
        raise KernelRefused("journal_content_forbidden")
    append_lock.acquire()
    with connection() as conn:
        if not correlation_id or not causation_id:
            operation = conn.execute(
                "SELECT correlation_id,parent_operation_id FROM kernel_operations WHERE operation_id=?",
                (operation_id,),
            ).fetchone()
            if operation is not None:
                correlation_id = correlation_id or str(operation["correlation_id"] or "")
                causation_id = causation_id or str(operation["parent_operation_id"] or "")
        previous = conn.execute(
            "SELECT stream_sequence, record_sha256 FROM kernel_journal WHERE stream=? ORDER BY stream_sequence DESC LIMIT 1",
            (stream,),
        ).fetchone()
        sequence = int(previous[0]) + 1 if previous is not None else 1
        record = {
            "stream": stream,
            "stream_sequence": sequence,
            "event_id": "evt_" + uuid.uuid4().hex,
            "operation_id": operation_id,
            "process_id": process_id,
            "correlation_id": correlation_id,
            "causation_id": causation_id,
            "event_type": event_type,
            "event_version": 1,
            "refs": list(refs),
            "privacy_class": privacy_class,
            "head": str(head)[:_HEAD_LIMIT],
            "timestamp": clock(),
            "previous_sha256": str(previous[1]) if previous is not None else "sha256:genesis",
        }
        hash_value = record_hash(record)
        cursor = conn.execute(
            """INSERT INTO kernel_journal(
                stream,stream_sequence,event_id,operation_id,process_id,correlation_id,
                causation_id,event_type,event_version,refs_json,privacy_class,head,
                timestamp,previous_sha256,record_sha256
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record["stream"], sequence, record["event_id"], operation_id,
                process_id, correlation_id, causation_id, event_type, 1,
                json_encode(record["refs"]), privacy_class, record["head"],
                record["timestamp"], record["previous_sha256"], hash_value,
            ),
        )
        record["cursor"] = int(cursor.lastrowid)
        record["record_sha256"] = hash_value
    append_lock.release()
    return record
