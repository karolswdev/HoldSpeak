"""Shared meeting export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from .meeting_session import MeetingState

MeetingExportFormat = Literal["json", "markdown", "txt"]

_EXPORT_EXTENSIONS: dict[MeetingExportFormat, str] = {
    "json": "json",
    "markdown": "md",
    "txt": "txt",
}


def _action_item_value(item: object, key: str, default: str = "") -> str:
    """Read action-item fields from dicts or dataclass-like objects."""
    if isinstance(item, dict):
        value = item.get(key, default)
    else:
        value = getattr(item, key, default)
    if value is None:
        return default
    return str(value)


def _render_markdown(meeting: MeetingState) -> str:
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
            status = _action_item_value(item, "status", "pending")
            check = "x" if status == "done" else " "
            task = _action_item_value(item, "task")
            owner = _action_item_value(item, "owner")
            owner_str = f" (@{owner})" if owner else ""
            lines.append(f"- [{check}] {task}{owner_str}")
        lines.append("")

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


def render_meeting_export(meeting: MeetingState, export_format: MeetingExportFormat) -> str:
    """Render a meeting into a supported export format."""
    if export_format == "json":
        return json.dumps(meeting.to_dict(), indent=2)
    if export_format == "markdown":
        return _render_markdown(meeting)
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
) -> Path:
    """Write an exported meeting file and return the path."""
    filepath = build_meeting_export_path(
        meeting,
        export_format,
        destination_dir=destination_dir,
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(render_meeting_export(meeting, export_format), encoding="utf-8")
    return filepath
