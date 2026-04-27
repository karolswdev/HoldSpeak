"""Shared meeting export helpers."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Literal

from .meeting_session import MeetingState

MeetingExportFormat = Literal["json", "markdown", "txt"]

_EXPORT_EXTENSIONS: dict[MeetingExportFormat, str] = {
    "json": "json",
    "markdown": "md",
    "txt": "txt",
}


def _object_value(item: object, key: str, default: Any = None) -> Any:
    """Read fields from dicts or dataclass-like objects."""
    if isinstance(item, dict):
        value = item.get(key, default)
    else:
        value = getattr(item, key, default)
    return default if value is None else value


def _action_item_value(item: object, key: str, default: str = "") -> str:
    """Read action-item fields as strings."""
    value = _object_value(item, key, default)
    if value is None:
        return default
    return str(value)


def _format_timestamp(seconds: object) -> str:
    try:
        total = max(0, int(float(seconds)))
    except (TypeError, ValueError):
        return ""
    minutes, remainder = divmod(total, 60)
    return f"{minutes:02d}:{remainder:02d}"


def _format_action_item_line(item: object) -> str:
    status = _action_item_value(item, "status", "pending")
    check = "x" if status == "done" else " "
    task = _action_item_value(item, "task")
    owner = _action_item_value(item, "owner")
    due = _action_item_value(item, "due")
    review_state = _action_item_value(item, "review_state", "pending")
    source_timestamp = _format_timestamp(_object_value(item, "source_timestamp"))

    owner_str = f" (@{owner})" if owner else ""
    details: list[str] = []
    if due:
        details.append(f"due {due}")
    if review_state:
        details.append(f"review {review_state}")
    if source_timestamp:
        details.append(f"source {source_timestamp}")
    detail_str = f" - {'; '.join(details)}" if details else ""
    return f"- [{check}] {task}{owner_str}{detail_str}"


def _artifact_to_dict(artifact: object) -> dict[str, Any]:
    created_at = _object_value(artifact, "created_at")
    updated_at = _object_value(artifact, "updated_at")
    return {
        "id": _object_value(artifact, "id", ""),
        "meeting_id": _object_value(artifact, "meeting_id", ""),
        "artifact_type": _object_value(artifact, "artifact_type", ""),
        "title": _object_value(artifact, "title", ""),
        "body_markdown": _object_value(artifact, "body_markdown", ""),
        "structured_json": _object_value(artifact, "structured_json", {}),
        "confidence": _object_value(artifact, "confidence", None),
        "status": _object_value(artifact, "status", ""),
        "plugin_id": _object_value(artifact, "plugin_id", ""),
        "plugin_version": _object_value(artifact, "plugin_version", ""),
        "sources": _object_value(artifact, "sources", []),
        "created_at": created_at.isoformat() if isinstance(created_at, datetime) else created_at,
        "updated_at": updated_at.isoformat() if isinstance(updated_at, datetime) else updated_at,
    }


def _render_artifacts_markdown(artifacts: Iterable[object]) -> list[str]:
    lines: list[str] = []
    artifact_payloads = [_artifact_to_dict(artifact) for artifact in artifacts]
    if not artifact_payloads:
        return lines

    lines.extend(["## Artifacts", ""])
    for artifact in artifact_payloads:
        title = str(artifact.get("title") or artifact.get("id") or "Untitled artifact")
        artifact_type = str(artifact.get("artifact_type") or "artifact")
        status = str(artifact.get("status") or "draft")
        confidence = artifact.get("confidence")
        sources = artifact.get("sources") or []
        meta = [artifact_type, status]
        if isinstance(confidence, (int, float)):
            meta.append(f"{confidence * 100:.0f}% confidence")
        if sources:
            meta.append(f"{len(sources)} sources")

        lines.append(f"### {title}")
        lines.append("")
        lines.append(f"*{'; '.join(meta)}*")
        body = str(artifact.get("body_markdown") or "").strip()
        if body:
            lines.extend(["", body])
        lines.append("")
    return lines


def _render_markdown(
    meeting: MeetingState,
    *,
    artifacts: Iterable[object] | None = None,
) -> str:
    lines = [
        f"# {meeting.title or 'Meeting Transcript'}",
        "",
        f"**Date:** {meeting.started_at.strftime('%Y-%m-%d %H:%M')}",
        f"**Duration:** {meeting.format_duration()}",
        "",
    ]

    if meeting.intel and meeting.intel.summary:
        lines.extend(["## Summary", "", meeting.intel.summary, ""])

    if meeting.intel and meeting.intel.topics:
        lines.extend(["## Topics", ""])
        for topic in meeting.intel.topics:
            lines.append(f"- {topic}")
        lines.append("")

    if meeting.intel and meeting.intel.action_items:
        lines.extend(["## Action Items", ""])
        for item in meeting.intel.action_items:
            lines.append(_format_action_item_line(item))
        lines.append("")

    if artifacts is not None:
        lines.extend(_render_artifacts_markdown(artifacts))

    if meeting.tags:
        lines.extend(["## Tags", "", ", ".join(meeting.tags), ""])

    if meeting.bookmarks:
        lines.extend(["## Bookmarks", ""])
        for bookmark in meeting.bookmarks:
            label = f" - {bookmark.label}" if bookmark.label else ""
            lines.append(f"- [{bookmark.timestamp:.0f}s]{label}")
        lines.append("")

    lines.extend(["## Transcript", ""])
    for segment in meeting.segments:
        bookmark = " **[BOOKMARK]**" if segment.is_bookmarked else ""
        lines.append(
            f"**{segment.speaker}** [{segment.start_time:.0f}s]: {segment.text}{bookmark}"
        )
        lines.append("")

    return "\n".join(lines)


def _render_text(meeting: MeetingState) -> str:
    lines = [
        f"Meeting: {meeting.title or meeting.id}",
        f"Date: {meeting.started_at.strftime('%Y-%m-%d %H:%M')}",
        f"Duration: {meeting.format_duration()}",
    ]

    if meeting.tags:
        lines.append(f"Tags: {', '.join(meeting.tags)}")

    if meeting.intel and meeting.intel.summary:
        lines.extend(["", "Summary:", meeting.intel.summary])

    lines.extend(["", "Transcript:", "-" * 40])
    for segment in meeting.segments:
        bookmark = " *" if segment.is_bookmarked else ""
        lines.append(
            f"[{segment.start_time:.0f}s] {segment.speaker}: {segment.text}{bookmark}"
        )

    return "\n".join(lines)


def render_meeting_export(
    meeting: MeetingState,
    export_format: MeetingExportFormat,
    *,
    artifacts: Iterable[object] | None = None,
) -> str:
    """Render a meeting into a supported export format."""
    if export_format == "json":
        payload = meeting.to_dict()
        if artifacts is not None:
            payload["artifacts"] = [_artifact_to_dict(artifact) for artifact in artifacts]
        return json.dumps(payload, indent=2)
    if export_format == "markdown":
        return _render_markdown(meeting, artifacts=artifacts)
    if export_format == "txt":
        return _render_text(meeting)
    raise ValueError(f"Unsupported export format: {export_format}")


def build_meeting_export_path(
    meeting: MeetingState,
    export_format: MeetingExportFormat,
    destination_dir: Path | None = None,
) -> Path:
    """Build the output path for an exported meeting."""
    extension = _EXPORT_EXTENSIONS.get(export_format)
    if extension is None:
        raise ValueError(f"Unsupported export format: {export_format}")

    target_dir = destination_dir or (Path.home() / "Documents")
    timestamp = meeting.started_at.strftime("%Y%m%d_%H%M%S")
    filename = f"meeting_{meeting.id[:8]}_{timestamp}.{extension}"
    return target_dir / filename


def write_meeting_export(
    meeting: MeetingState,
    export_format: MeetingExportFormat,
    destination_dir: Path | None = None,
    *,
    artifacts: Iterable[object] | None = None,
) -> Path:
    """Write an exported meeting file and return the path."""
    filepath = build_meeting_export_path(
        meeting,
        export_format,
        destination_dir=destination_dir,
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(
        render_meeting_export(meeting, export_format, artifacts=artifacts),
        encoding="utf-8",
    )
    return filepath
