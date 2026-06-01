"""Real `dependency_mapper` plugin (HS-29-01).

Flips the `DeterministicPlugin` stub for `dependency_mapper` to a real LLM-backed
synthesizer. Planning meetings surface inter-team / inter-component dependencies
("billing can't start until the API freezes"). A real run captures each as a
directed edge: from → to, with an optional note.

Mirrors the proven pattern: strict prompt → single fenced ```json block →
parse/validate → structured output.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.dependency_mapper")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You map dependencies discussed in a meeting transcript.\n"
    "A dependency is a directed relationship: one thing (team, component, task, "
    "milestone) must happen or exist before another. Capture the dependent (from) "
    "and what it depends on (to), plus a short note if the reason was stated.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"dependencies": [{"from": "...", "to": "...", "note": "or null"}]}\n'
    "Use null for an unstated note. Return an empty list if there are no "
    "dependencies. Output only the JSON block — no prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _extract_dependencies(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the response into a normalized dependency-edge list (or None)."""
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
    raw_items = obj.get("dependencies")
    if not isinstance(raw_items, list):
        return None

    deps: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        src = str(raw.get("from") or "").strip()
        dst = str(raw.get("to") or "").strip()
        if not src or not dst:
            continue
        deps.append({"from": src, "to": dst, "note": _optional_field(raw.get("note"))})
    return deps


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
    return (
        f"{header}Transcript:\n{transcript}\n\n"
        "Map the dependencies per the system prompt."
    )


class DependencyMapperPlugin:
    """LLM-backed plugin mapping inter-team/component dependencies per window."""

    id: str = "dependency_mapper"
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
            return _failure("dependency_mapper: no transcript provided.")

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
            log.info("dependency_mapper: intel call failed: %s", exc)
            return _failure(f"dependency_mapper: intel call failed: {exc}")

        deps = _extract_dependencies(raw or "")
        if deps is None:
            return _failure("dependency_mapper: response did not contain a parseable dependency list.")
        if not deps:
            return _failure("dependency_mapper: no dependencies found.")

        return {
            "summary": f"{len(deps)} dependency edge(s) mapped.",
            "dependencies": deps,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = ["DependencyMapperPlugin", "_extract_dependencies"]
