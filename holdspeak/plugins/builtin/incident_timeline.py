"""Real `incident_timeline` plugin (HS-29-02).

Flips the `DeterministicPlugin` stub to a real LLM-backed synthesizer. Incident
retros need an ordered timeline of what happened. A real run extracts the events
in the order the model returns them (chronological), each with an optional
timestamp/marker.

Mirrors the proven pattern: strict prompt → fenced ```json → parse/validate →
structured output.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.incident_timeline")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You build an incident timeline from a meeting transcript.\n"
    "List the events in chronological order — what happened, in sequence. For each "
    "event, include a time/marker if one was mentioned (a clock time, a relative "
    "marker like 'T+10m', or a phase like 'detection').\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"events": [{"time": "or null", "event": "..."}]}\n'
    "Keep the list in chronological order. Use null for an unstated time. Return "
    "an empty list if this is not an incident. Output only the JSON block — no "
    "prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _extract_events(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the response into a normalized event list (or None)."""
    if not text:
        return None
    candidate: Optional[str] = None
    fence = _JSON_FENCE_RE.search(text)
    if fence is not None:
        candidate = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            candidate = text[start : end + 1]
    if not candidate:
        return None
    try:
        obj = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(obj, dict):
        return None
    raw_items = obj.get("events")
    if not isinstance(raw_items, list):
        return None

    events: list[dict[str, Any]] = []
    for raw in raw_items:
        if isinstance(raw, dict):
            event = str(raw.get("event") or "").strip()
            time = _optional_field(raw.get("time"))
        elif isinstance(raw, str):
            event = raw.strip()
            time = None
        else:
            continue
        if event:
            events.append({"time": time, "event": event})
    return events


def _build_user_prompt(
    *, transcript: str, active_intents: list[str], tags: list[str], project_name: str
) -> str:
    header_lines: list[str] = []
    if project_name:
        header_lines.append(f"Project: {project_name}")
    if active_intents:
        header_lines.append(f"Active intents: {', '.join(active_intents)}")
    if tags:
        header_lines.append(f"Tags: {', '.join(tags)}")
    header = ("\n".join(header_lines) + "\n\n") if header_lines else ""
    return f"{header}Transcript:\n{transcript}\n\nBuild the incident timeline per the system prompt."


class IncidentTimelinePlugin:
    """LLM-backed plugin building an ordered incident timeline per window."""

    id: str = "incident_timeline"
    version: str = "0.1.0"
    kind: str = "synthesizer"
    execution_mode: str = "deferred"
    required_capabilities: list[str] = ["llm"]

    def __init__(self, *, intel_call: Optional[IntelChat] = None) -> None:
        self._intel_call_override = intel_call
        self._cached_provider: Any = None

    def _call_intel(self, messages: list[dict[str, str]]) -> str:
        if self._intel_call_override is not None:
            return self._intel_call_override(messages)
        if self._cached_provider is None:
            from ...intel import build_configured_meeting_intel  # lazy import: optional deps

            self._cached_provider = build_configured_meeting_intel()
        return self._cached_provider._chat_completion_text(messages, temperature=0.2, max_tokens=1200)

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        transcript = str(context.get("transcript") or "").strip()
        active_intents = [
            str(intent).strip().lower()
            for intent in (context.get("active_intents") or [])
            if str(intent).strip()
        ]
        tags = [str(tag).strip() for tag in (context.get("tags") or []) if str(tag).strip()]
        project_name = str(context.get("project_name") or context.get("project") or "").strip()

        def _failure(reason: str) -> dict[str, Any]:
            return {"summary": reason, "confidence_hint": 0.0, "active_intents": active_intents}

        if not transcript:
            return _failure("incident_timeline: no transcript provided.")

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    transcript=transcript, active_intents=active_intents, tags=tags, project_name=project_name
                ),
            },
        ]

        try:
            raw = self._call_intel(messages)
        except Exception as exc:
            log.info("incident_timeline: intel call failed: %s", exc)
            return _failure(f"incident_timeline: intel call failed: {exc}")

        events = _extract_events(raw or "")
        if events is None:
            return _failure("incident_timeline: response did not contain a parseable event list.")
        if not events:
            return _failure("incident_timeline: no incident events found.")

        return {
            "summary": f"{len(events)} timeline event(s).",
            "events": events,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = ["IncidentTimelinePlugin", "_extract_events"]
