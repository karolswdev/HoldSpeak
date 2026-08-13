"""Receipt-gated Rails journal and artifact projections."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from .model import KernelRefused
from .projection_stager import _PublicationPermit


def _artifact(conn: Any, *, artifact_id: str, meeting_id: str, artifact_type: str,
              title: str, body: str, plugin_id: str, sources: list[dict[str, str]]) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute(
        """INSERT INTO artifacts (id,meeting_id,origin,artifact_type,title,body_markdown,
           structured_json,confidence,status,plugin_id,plugin_version,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
           meeting_id=excluded.meeting_id,origin=excluded.origin,artifact_type=excluded.artifact_type,
           title=excluded.title,body_markdown=excluded.body_markdown,structured_json=excluded.structured_json,
           confidence=excluded.confidence,status=excluded.status,plugin_id=excluded.plugin_id,
           plugin_version=excluded.plugin_version,updated_at=excluded.updated_at""",
        (artifact_id, meeting_id or None, "meeting" if meeting_id else "run", artifact_type,
         title, body, "{}", 1.0, "draft", plugin_id, "1", now, now),
    )
    conn.execute("DELETE FROM artifact_sources WHERE artifact_id=?", (artifact_id,))
    for source in sources:
        conn.execute("INSERT INTO artifact_sources (artifact_id,source_type,source_ref,created_at) VALUES (?,?,?,?)",
                     (artifact_id, source["source_type"], source["source_ref"], now))


def _decision(conn: Any, stage: Any) -> dict[str, Any]:
    projection = dict(stage.projection)
    decision_id = str(projection["decision_id"])
    artifact_type = str(projection["artifact_type"])
    row = conn.execute("SELECT * FROM decisions WHERE id=? AND lifecycle='accepted'", (decision_id,)).fetchone()
    if row is None:
        raise KernelRefused("decision_promotion_not_promotable")
    from ..db.decisions import derive_promoted_artifact_id
    from ..plugins.synthesis import render_promoted_decision
    title, _, structured = render_promoted_decision(
        artifact_type, text=str(row["text"]), rationale=str(row["rationale"] or ""),
        decided_at=str(row["decided_at"]), meeting_id=str(row["source_meeting_id"]),
    )
    structured["promotion"] = {"decision_id": decision_id, "meeting_id": str(row["source_meeting_id"]), "model_assisted": True}
    artifact_id = derive_promoted_artifact_id(decision_id, artifact_type)
    # Decision artifacts retain their structured causal body, unlike run outputs.
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    conn.execute("""INSERT INTO artifacts (id,meeting_id,origin,artifact_type,title,body_markdown,structured_json,confidence,status,plugin_id,plugin_version,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET body_markdown=excluded.body_markdown,structured_json=excluded.structured_json,status=excluded.status,updated_at=excluded.updated_at""",
        (artifact_id, row["source_meeting_id"], "meeting", artifact_type, title, str(projection["output"]).strip(), json.dumps(structured, sort_keys=True, separators=(",", ":")), 1.0, "draft", "decision_promotion", "1", now, now))
    conn.execute("DELETE FROM artifact_sources WHERE artifact_id=?", (artifact_id,))
    for source_type, source_ref in (("decision", decision_id), ("meeting", str(row["source_meeting_id"]))):
        conn.execute("INSERT INTO artifact_sources (artifact_id,source_type,source_ref,created_at) VALUES (?,?,?,?)", (artifact_id, source_type, source_ref, now))
    return {**projection, "artifact_id": artifact_id}


def _delivery(conn: Any, stage: Any) -> dict[str, Any]:
    projection = dict(stage.projection)
    artifact_id = "artifact_" + uuid.uuid4().hex[:12]
    number = int(projection["number"])
    source_id = str(projection["source_id"])
    _artifact(conn, artifact_id=artifact_id, meeting_id="", artifact_type="run_output",
              title=f"PR #{number} review: PR #{number}", body=str(projection["output"]),
              plugin_id="delivery_pr_review_run", sources=[
                  {"source_type": "input", "source_ref": f"pr:{source_id}:{number}"},
                  {"source_type": "invocation", "source_ref": f"operation:{stage.operation_id}"},
              ])
    return {**projection, "artifact_id": artifact_id}


def materialize(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    if not isinstance(permit, _PublicationPermit):
        raise KernelRefused("projection_publication_permit_invalid")
    permit.use(conn)
    if stage.kind == "decision-promotion-draft":
        return _decision(conn, stage)
    if stage.kind == "delivery-pr-review":
        return _delivery(conn, stage)
    return dict(stage.projection)


def register(stager: Any) -> None:
    # The parented service kinds have no checkpoint CAS; the parent election is
    # their only publication fence.  Rails is a root invocation.  The three
    # meeting kinds and the cadence draft are passthrough: their staged projection
    # carries the authorized output the caller applies after the winning receipt.
    for kind in ("rails-journal", "voice-resolver-attempt", "delivery-pr-review", "decision-promotion-draft",
                 "cadence-next-action",
                 "meeting-live-window", "meeting-bookmark-label", "meeting-auto-title"):
        try:
            stager.register(kind, materialize, discard_on_parent_cancel=kind != "rails-journal")
        except ValueError:
            pass
