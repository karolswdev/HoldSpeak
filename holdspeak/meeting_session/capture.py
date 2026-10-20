"""Assemble recorder ownership for one Meeting's capture journal."""
from __future__ import annotations

from typing import Any


def recorder_options(
    journal: Any, meeting_id: str, recorder_type: Any, *,
    mic_device: Any, system_device: Any, on_mic_level: Any, on_system_level: Any,
) -> dict[str, Any]:
    """Native capture owns its journal; other recorders receive its callback."""
    options: dict[str, Any] = {
        "mic_device": mic_device,
        "system_device": system_device,
        "on_mic_level": on_mic_level,
        "on_system_level": on_system_level,
        "on_audio_chunk": lambda chunk: journal.append(chunk.source, chunk.audio)
        if journal is not None else None,
    }
    directory = getattr(journal, "directory", None)
    if directory is not None and bool(getattr(recorder_type, "capture_process_supported", False)):
        options.update(
            capture_directory=directory.parent,
            meeting_id=meeting_id,
            on_audio_chunk=None,
        )
    return options
