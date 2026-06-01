"""Real `runbook_delta` plugin (HS-29-02).

Flips the `DeterministicPlugin` stub to a real LLM-backed artifact generator.
Incident retros and ops meetings imply runbook changes ("add a step to flush the
cache", "the old rollback step is wrong"). A real run captures each as a typed
delta: added / modified / removed.

Mirrors the proven pattern: strict prompt → fenced ```json → parse/validate →
structured output.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.runbook_delta")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_VALID_TYPES = ("added", "modified", "removed")
_TYPE_SYNONYMS: dict[str, str] = {
    "added": "added",
    "add": "added",
    "new": "added",
    "modified": "modified",
    "modify": "modified",
    "changed": "modified",
    "updated": "modified",
    "removed": "removed",
    "remove": "removed",
    "deleted": "removed",
    "obsolete": "removed",
}

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You extract runbook changes implied by a meeting transcript.\n"
    "A runbook delta is a change to operational procedure. Classify each as: added "
    "(a new step/procedure), modified (an existing step changes), or removed (a "
    "step is dropped). Add a short detail if stated.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"changes": [{"change": "...", "type": "added|modified|removed", "detail": '
    '"or null"}]}\n'
    "Return an empty list if no runbook changes were implied. Output only the JSON "
    "block — no prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _normalize_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in _VALID_TYPES:
        return text
    return _TYPE_SYNONYMS.get(text, "modified")


def _extract_changes(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the response into a normalized runbook-change list (or None)."""
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
    raw_items = obj.get("changes")
    if not isinstance(raw_items, list):
        return None

    changes: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        change = str(raw.get("change") or "").strip()
        if not change:
            continue
        changes.append(
            {
                "change": change,
                "type": _normalize_type(raw.get("type")),
                "detail": _optional_field(raw.get("detail")),
            }
        )
    return changes


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
    return f"{header}Transcript:\n{transcript}\n\nExtract the runbook deltas per the system prompt."


class RunbookDeltaPlugin:
    """LLM-backed plugin extracting runbook changes (added/modified/removed)."""

    id: str = "runbook_delta"
    version: str = "0.1.0"
    kind: str = "artifact_generator"
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
        return self._cached_provider._chat_completion_text(messages, temperature=0.2, max_tokens=1000)

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
            return _failure("runbook_delta: no transcript provided.")

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
            log.info("runbook_delta: intel call failed: %s", exc)
            return _failure(f"runbook_delta: intel call failed: {exc}")

        changes = _extract_changes(raw or "")
        if changes is None:
            return _failure("runbook_delta: response did not contain a parseable change list.")
        if not changes:
            return _failure("runbook_delta: no runbook changes found.")

        return {
            "summary": f"{len(changes)} runbook change(s).",
            "changes": changes,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = ["RunbookDeltaPlugin", "_extract_changes", "_normalize_type"]
