"""Rolling-window intent timeline helpers for MIR routing."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .plugins.contracts import IntentWindow


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _normalize_segments(segments: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for segment in segments:
        start = max(0.0, _to_float(segment.get("start_time"), 0.0))
        end = max(start, _to_float(segment.get("end_time"), start))
        text = str(segment.get("text") or "").strip()
        if not text:
            continue
        normalized.append(
            {
                "start_time": start,
                "end_time": end,
                "speaker": str(segment.get("speaker") or "").strip() or "Unknown",
                "text": text,
            }
        )
    normalized.sort(key=lambda seg: (seg["start_time"], seg["end_time"]))
    return normalized


def build_intent_windows(
    segments: list[Mapping[str, Any]],
    *,
    meeting_id: str,
    window_seconds: float = 90.0,
    step_seconds: float = 30.0,
    min_text_chars: int = 1,
) -> list[IntentWindow]:
    """Build overlapping rolling transcript windows for multi-intent routing."""
    normalized_segments = _normalize_segments(segments)
    if not normalized_segments:
        return []

    safe_window = max(1.0, float(window_seconds))
    safe_step = max(1.0, float(step_seconds))
    min_chars = max(0, int(min_text_chars))

    timeline_start = normalized_segments[0]["start_time"]
    timeline_end = max(seg["end_time"] for seg in normalized_segments)

    windows: list[IntentWindow] = []
    window_start = timeline_start
    index = 0

    while window_start <= timeline_end:
        window_end = window_start + safe_window
        covered = [
            seg
            for seg in normalized_segments
            if seg["start_time"] < window_end and seg["end_time"] > window_start
        ]
        transcript = " ".join(seg["text"] for seg in covered).strip()
        if len(transcript) >= min_chars and transcript:
            windows.append(
                IntentWindow(
                    window_id=f"{meeting_id}:w{index:04d}",
                    meeting_id=meeting_id,
                    start_seconds=round(window_start, 3),
                    end_seconds=round(window_end, 3),
                    transcript=transcript,
                    tags=[],
                    metadata={
                        "segment_count": len(covered),
                    },
                )
            )
        index += 1
        window_start += safe_step

    return windows


def detect_intent_transitions(
    ordered_window_intents: list[tuple[str, list[str]]],
) -> list[dict[str, Any]]:
    """Return transition events when dominant active intent sets change."""
    transitions: list[dict[str, Any]] = []
    previous: set[str] = set()

    for window_id, intents in ordered_window_intents:
        current = {str(intent).strip().lower() for intent in intents if str(intent).strip()}
        added = sorted(current - previous)
        removed = sorted(previous - current)
        if added or removed:
            transitions.append(
                {
                    "window_id": window_id,
                    "active_intents": sorted(current),
                    "added": added,
                    "removed": removed,
                }
            )
        previous = current

    return transitions
