"""PHILO-15 08 (B02): the summary's decisions and action items as one artifact.

Carved out of ``meeting_plugin_projection`` (the broker density guard): the
bound analysis projection calls these inside its own publication transaction.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any


def summary_action_id(projection: dict[str, Any], ordinal: int, item: dict[str, Any]) -> str:
    """The persistence id of one summary action item.

    The closed semantic result omits persistence IDs. Derive one from the
    immutable job descriptor and ordinal, so replay writes the same action item
    without putting transcript/prompt material in queue evidence.
    """
    return str(item.get("id") or "").strip() or "action_" + hashlib.sha256(
        f"{projection['job_id']}:{ordinal}".encode()
    ).hexdigest()[:24]


#: PHILO-15 08 (B02): the summary's own extractor id. Its decisions and
#: action items are one artifact the proposal bridge reads, so a meeting
#: yields proposals from the summary run alone (no plugin chain needed).
SUMMARY_ITEMS_PLUGIN = "meeting_summary"
SUMMARY_ITEMS_TYPE = "summary_items"


def write_summary_items(
    conn: Any, projection: dict[str, Any], meeting_id: str, action_items: list[Any],
) -> None:
    """Write the summary's decisions and action items as one artifact.

    One row per meeting (a re-run replaces it). The type is not
    ``decisions``: a summary decision is a PROPOSAL until the owner confirms
    it; nothing here writes a decision record.
    """
    actions = [
        {"task": str(item.get("task") or ""), "owner": item.get("owner"),
         "due": item.get("due"), "action_item_id": summary_action_id(projection, ordinal, item)}
        for ordinal, item in enumerate(action_items, 1)
        if isinstance(item, dict) and str(item.get("task") or "").strip()
    ]
    decisions = [
        {"decision": str(item.get("decision") or "").strip(),
         "rationale": item.get("rationale")}
        for item in list(projection.get("decisions") or [])
        if isinstance(item, dict) and str(item.get("decision") or "").strip()
    ]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # The artifact lands on the desk beside others: it names its meeting.
    row = conn.execute("SELECT title FROM meetings WHERE id=?", (meeting_id,)).fetchone()
    meeting_title = str((row["title"] if row is not None else "") or "").strip()
    title = f"{meeting_title}: decisions and actions" if meeting_title else "Decisions and action items"
    lines = [f"- Decision: {d['decision']}" for d in decisions] + [
        f"- Action: {a['task']}" for a in actions
    ]
    conn.execute(
        """INSERT INTO artifacts (id,meeting_id,origin,artifact_type,title,body_markdown,
           structured_json,confidence,status,plugin_id,plugin_version,created_at,updated_at)
           VALUES (?,?,'meeting',?,?,?,?,1.0,'draft',?,'1',?,?) ON CONFLICT(id) DO UPDATE SET
           title=excluded.title,body_markdown=excluded.body_markdown,
           structured_json=excluded.structured_json,updated_at=excluded.updated_at""",
        (f"summary-items-{meeting_id}", meeting_id, SUMMARY_ITEMS_TYPE,
         title[:200], "\n".join(lines),
         json.dumps({"decisions": decisions, "action_items": actions,
                     "job_id": str(projection.get("job_id") or "")},
                    separators=(",", ":"), sort_keys=True),
         SUMMARY_ITEMS_PLUGIN, now, now),
    )
