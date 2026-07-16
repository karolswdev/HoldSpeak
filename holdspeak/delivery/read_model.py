"""The coherent `delivery_schema: 1` read model (HS-94-02).

PLATFORM-CONTRACT §4.4 and §11: one snapshot carries one revision
covering every collection it contains, one replayable cursor
composed from the per-source dw cursors, and per-source freshness
as data (`live` / `stale` / `offline` / `incompatible` /
`unavailable`). §12/§13: nothing in the wire shapes is a repo root,
credentialed URL, or raw asset path — sources project through the
registry's `to_wire()` and the event allow-list below, never through
a blocklist walk over arbitrary payloads.

The read model is a projection, not a new source of rail truth; it
may be discarded and rebuilt from the providers (§11).
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from typing import Any, Optional

DELIVERY_SCHEMA = 1

SOURCE_STATUSES = (
    "live",
    "stale",
    "offline",
    "incompatible",
    "unauthorized",
    "unavailable",
)

# The rail-event fields allowed onto the wire (dw events_schema 2 —
# the counterpart's own privacy allow-list, §5.2). Anything else a
# future dw adds stays server-side until named here.
EVENT_WIRE_FIELDS = ("event_id", "ts", "event", "project", "story", "detail", "tree")

_CURSOR_PREFIX = "cur_"


def sanitize_event(event: dict[str, Any], source_id: str) -> dict[str, Any]:
    """One rail event, allow-listed field by field and stamped with
    its opaque source."""
    out: dict[str, Any] = {"source_id": source_id}
    for key in EVENT_WIRE_FIELDS:
        if key in event:
            out[key] = event[key]
    return out


def compose_cursor(per_source: dict[str, str]) -> str:
    """One opaque replayable cursor over all sources: the per-source
    dw cursors, canonically encoded. Clients compare cursors for
    equality and hand them back; they never parse them."""
    packed = json.dumps(per_source, sort_keys=True, separators=(",", ":"))
    encoded = base64.urlsafe_b64encode(packed.encode("utf-8")).decode("ascii")
    return _CURSOR_PREFIX + encoded.rstrip("=")


def parse_cursor(text: Optional[str]) -> dict[str, str]:
    """Tolerant decode: anything unrecognizable replays from the
    beginning of the retained buffer (§2 rule 12 — reconnect never
    depends on a witnessed frame)."""
    raw = str(text or "")
    if not raw.startswith(_CURSOR_PREFIX):
        return {}
    body = raw[len(_CURSOR_PREFIX):]
    body += "=" * (-len(body) % 4)
    try:
        decoded = json.loads(base64.urlsafe_b64decode(body.encode("ascii")))
    except (ValueError, binascii.Error):
        return {}
    if not isinstance(decoded, dict):
        return {}
    return {str(k): str(v) for k, v in decoded.items()}


def snapshot_revision(source_rows: list[dict[str, Any]], cursor: str) -> str:
    """One revision over every collection in the snapshot. Timestamps
    are excluded so an unchanged payload keeps its revision (the
    ETag/304 economy); any data or cursor motion changes it."""
    hashable = [
        {k: v for k, v in row.items() if k != "observed_at"}
        for row in source_rows
    ]
    digest = hashlib.sha256(
        json.dumps([hashable, cursor], sort_keys=True).encode("utf-8")
    ).hexdigest()
    return "rev_" + digest[:16]


def build_snapshot(
    source_rows: list[dict[str, Any]],
    per_source_cursors: dict[str, str],
    generated_at: str,
) -> dict[str, Any]:
    """Assemble the wire snapshot: internally consistent by
    construction — the rows and cursors come from ONE collection
    pass, and the revision is computed over exactly what ships."""
    cursor = compose_cursor(per_source_cursors)
    return {
        "delivery_schema": DELIVERY_SCHEMA,
        "revision": snapshot_revision(source_rows, cursor),
        "cursor": cursor,
        "generated_at": generated_at,
        "sources": source_rows,
    }
