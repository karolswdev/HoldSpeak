"""Receipt-gated meeting plugin-run and artifact materialization (HS-131-08).

A routed plugin's durable output — its ``plugin_runs`` record and the artifacts
synthesized from the meeting's runs — is written ONLY here, inside the
finalization transaction that the winning child receipt permits. A cancelled,
expired, or revoked deferred job parent therefore leaves no plugin run and no
artifact row behind: the stage is discarded instead.

The base deferred analysis (``meeting-deferred-analysis``) stays a passthrough
projection: the queue applies its earned snapshot to the Meeting after the
receipt, exactly as the live session does with its window.

The work ``stop()`` displaces onto the deferred job has no live session left to
apply it, so its two kinds ARE materialized here: the earned auto title
(``meeting-deferred-auto-title``) and each earned bookmark label
(``meeting-deferred-bookmark-label``) are written to the meeting and bookmark
rows inside the permitted transaction, and nowhere else.
"""
from __future__ import annotations

import json
import time
from typing import Any

from .model import KernelRefused
from .projection_stager import _PublicationPermit



def _record_run(conn: Any, projection: dict[str, Any]) -> None:
    """Mirror ``PluginRepository.record_plugin_run`` on the permitted connection."""
    meeting_id = str(projection["meeting_id"]).strip()
    window_id = str(projection["window_id"]).strip()
    plugin_id = str(projection["plugin_id"]).strip()
    status = str(projection["status"]).strip().lower()
    version = str(projection.get("plugin_version") or "unknown").strip() or "unknown"
    key = str(projection.get("idempotency_key") or "").strip() or None
    if not meeting_id or not window_id or not plugin_id or not status:
        raise KernelRefused("meeting_plugin_projection_incomplete")
    output = projection.get("output")
    output_json = (
        json.dumps(output, separators=(",", ":"), sort_keys=True)
        if isinstance(output, dict)
        else None
    )
    error = str(projection.get("error") or "") or None
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    columns = """meeting_id, window_id, plugin_id, plugin_version, status,
                 idempotency_key, duration_ms, output_json, error, deduped, created_at, updated_at"""
    values = (meeting_id, window_id, plugin_id, version, status, key,
              float(projection.get("duration_ms") or 0.0), output_json, error,
              int(bool(projection.get("deduped"))), now, now)
    if key:
        conn.execute(
            f"""INSERT INTO plugin_runs ({columns}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    meeting_id=excluded.meeting_id, window_id=excluded.window_id,
                    plugin_id=excluded.plugin_id, plugin_version=excluded.plugin_version,
                    status=excluded.status, duration_ms=excluded.duration_ms,
                    output_json=excluded.output_json, error=excluded.error,
                    deduped=excluded.deduped, updated_at=excluded.updated_at""",
            values,
        )
    else:
        conn.execute(
            f"INSERT INTO plugin_runs ({columns}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", values
        )


def _runs_for(conn: Any, meeting_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM plugin_runs WHERE meeting_id=? ORDER BY created_at DESC, id DESC LIMIT 5000",
        (meeting_id,),
    ).fetchall()
    runs: list[dict[str, Any]] = []
    for row in rows:
        raw = row["output_json"]
        try:
            output = json.loads(raw) if isinstance(raw, str) and raw else None
        except ValueError:
            output = None
        runs.append({
            "id": str(row["id"]),
            "meeting_id": str(row["meeting_id"] or ""),
            "window_id": str(row["window_id"] or ""),
            "plugin_id": str(row["plugin_id"] or ""),
            "plugin_version": str(row["plugin_version"] or ""),
            "status": str(row["status"] or ""),
            "output": output if isinstance(output, dict) else None,
            "created_at": str(row["created_at"] or ""),
        })
    return runs


def _write_artifact(conn: Any, artifact: Any) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    origin = "meeting" if str(artifact.meeting_id or "").strip() else "run"
    conn.execute(
        """INSERT INTO artifacts (id,meeting_id,origin,artifact_type,title,body_markdown,
           structured_json,confidence,status,plugin_id,plugin_version,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
           meeting_id=excluded.meeting_id,origin=excluded.origin,artifact_type=excluded.artifact_type,
           title=excluded.title,body_markdown=excluded.body_markdown,
           structured_json=excluded.structured_json,confidence=excluded.confidence,
           status=excluded.status,plugin_id=excluded.plugin_id,
           plugin_version=excluded.plugin_version,updated_at=excluded.updated_at""",
        (str(artifact.artifact_id), str(artifact.meeting_id or "") or None, origin,
         str(artifact.artifact_type or "plugin_output").lower(), str(artifact.title or "Artifact"),
         str(artifact.body_markdown or ""),
         json.dumps(artifact.structured_json or {}, separators=(",", ":"), sort_keys=True),
         max(0.0, min(1.0, float(artifact.confidence or 0.0))),
         str(artifact.status or "draft").lower(), str(artifact.plugin_id or "unknown"),
         str(artifact.plugin_version or "unknown"), now, now),
    )
    from ..db.plugins import VALID_ARTIFACT_SOURCE_TYPES

    conn.execute("DELETE FROM artifact_sources WHERE artifact_id=?", (str(artifact.artifact_id),))
    seen: set[tuple[str, str]] = set()
    for source in artifact.sources or []:
        entry = source.to_dict() if hasattr(source, "to_dict") else dict(source)
        source_type = str(entry.get("source_type") or "").strip().lower()
        source_ref = str(entry.get("source_ref") or "").strip()
        if not source_type or not source_ref or source_type not in VALID_ARTIFACT_SOURCE_TYPES:
            continue
        if (source_type, source_ref) in seen:
            continue
        seen.add((source_type, source_ref))
        conn.execute(
            "INSERT INTO artifact_sources (artifact_id,source_type,source_ref,created_at) VALUES (?,?,?,?)",
            (str(artifact.artifact_id), source_type, source_ref, now),
        )
    if str(artifact.artifact_type or "").lower() == "decisions":
        # The one reconciliation call site stays reachable: a receipt-gated
        # decisions artifact still projects into decision records in the SAME
        # transaction, exactly as the direct repository write does.
        from ..db.decisions import _project_artifact_row

        row = conn.execute("SELECT * FROM artifacts WHERE id=?", (str(artifact.artifact_id),)).fetchone()
        if row is not None:
            _project_artifact_row(conn, row)


def _write_title(conn: Any, projection: dict[str, Any]) -> dict[str, Any]:
    """Write one earned auto title onto the meeting (HS-131-08 D3).

    The live session applied its own title; a post-close job has no session, so
    the write happens HERE, inside the transaction this child's winning receipt
    permits. An owner-set title is never overwritten.
    """
    meeting_id = str(projection.get("meeting_id") or "").strip()
    title = str(projection.get("title") or "").strip()
    if not meeting_id:
        raise KernelRefused("meeting_title_projection_incomplete")
    if not title:
        # The provider had no title to offer: an honest zero-write, not a refusal.
        return {**projection, "title_written": 0}
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    cursor = conn.execute(
        """UPDATE meetings SET title=?, sync_modified_at=?, updated_at=datetime('now')
           WHERE id=? AND (title IS NULL OR title='')""",
        (title, now, meeting_id),
    )
    return {**projection, "title_written": int(cursor.rowcount or 0)}


def _write_bookmark_label(conn: Any, projection: dict[str, Any]) -> dict[str, Any]:
    """Write one earned bookmark label onto its bookmark row (HS-131-08 D3)."""
    meeting_id = str(projection.get("meeting_id") or "").strip()
    label = str(projection.get("label") or "").strip()
    if not meeting_id or projection.get("bookmark_timestamp") is None:
        raise KernelRefused("meeting_bookmark_projection_incomplete")
    if not label:
        # No better label was produced: keep the owner's existing one untouched.
        return {**projection, "labels_written": 0}
    timestamp = float(projection["bookmark_timestamp"])
    cursor = conn.execute(
        "UPDATE bookmarks SET label=? WHERE meeting_id=? AND timestamp=?",
        (label, meeting_id, timestamp),
    )
    conn.execute(
        "UPDATE meetings SET sync_modified_at=?, updated_at=datetime('now') WHERE id=?",
        (time.strftime("%Y-%m-%dT%H:%M:%S"), meeting_id),
    )
    return {**projection, "labels_written": int(cursor.rowcount or 0)}


def materialize(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    """Write the earned plugin run, then re-synthesize the meeting's artifacts."""
    if not isinstance(permit, _PublicationPermit):
        raise KernelRefused("projection_publication_permit_invalid")
    permit.use(conn)
    projection = dict(stage.projection)
    if stage.kind == "meeting-deferred-auto-title":
        return _write_title(conn, projection)
    if stage.kind == "meeting-deferred-bookmark-label":
        return _write_bookmark_label(conn, projection)
    if stage.kind != "meeting-plugin-result":
        return projection
    from ..plugins.synthesis import synthesize_meeting_artifacts

    _record_run(conn, projection)
    meeting_id = str(projection["meeting_id"]).strip()
    artifacts = synthesize_meeting_artifacts(
        meeting_id=meeting_id, plugin_runs=_runs_for(conn, meeting_id), max_artifacts=500
    )
    for artifact in artifacts:
        _write_artifact(conn, artifact)
    return {**projection, "artifacts_saved": len(artifacts)}


def register(stager: Any) -> None:
    # Every deferred kind is fenced by the job parent's election alone: they have
    # no checkpoint CAS, so a cancelled job discards their staged output — no
    # plugin run, no artifact, no title, no bookmark label.
    for kind in (
        "meeting-deferred-analysis",
        "meeting-plugin-result",
        "meeting-deferred-bookmark-label",
        "meeting-deferred-auto-title",
    ):
        try:
            stager.register(kind, materialize, discard_on_parent_cancel=True)
        except ValueError:
            pass


__all__ = ["materialize", "register"]
