"""Real `milestone_planner` plugin (HS-28-03).

Flips the `DeterministicPlugin` stub for `milestone_planner` to a real LLM-backed
synthesizer. The delivery counterpart to `action_owner_enforcer`: planning and
roadmap meetings produce milestones with target dates, deliverables, and
dependencies. A real run turns "let's aim to ship the beta by Q3, after the API
freezes" into a structured plan.

Mirrors the Phase-16 / Phase-27 pattern: strict prompt → single fenced ```json
block → parse/validate → structured output. Returns the success shape (`summary`,
`milestones`, `confidence_hint=1.0`, `active_intents`) when at least one milestone
is found, else the failure shape.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.milestone_planner")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You extract a milestone plan from a meeting transcript.\n"
    "A milestone is a meaningful delivery checkpoint. For each, capture: a short "
    "name, the target (a date or timeframe, if stated), the deliverables it "
    "includes, and any dependencies (what must happen first).\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"milestones": [{"name": "...", "target": "date/timeframe or null", '
    '"deliverables": ["..."], "dependencies": ["..."]}]}\n'
    "Use null for an unstated target, and empty lists when there are no "
    "deliverables or dependencies. Output only the JSON block — no prose, no "
    "extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for raw in value:
        text = str(raw or "").strip()
        if text:
            out.append(text)
    return out


def _extract_milestones(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the LLM response into a normalized milestone list.

    Returns the list (possibly empty) on a structurally valid response, or
    `None` when no parseable `{"milestones": [...]}` object is found.
    """
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
    raw_items = obj.get("milestones")
    if not isinstance(raw_items, list):
        return None

    milestones: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip()
        if not name:
            continue
        milestones.append(
            {
                "name": name,
                "target": _optional_field(raw.get("target")),
                "deliverables": _string_list(raw.get("deliverables")),
                "dependencies": _string_list(raw.get("dependencies")),
            }
        )
    return milestones


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
        "Extract the milestone plan per the system prompt."
    )


class MilestonePlannerPlugin:
    """LLM-backed plugin extracting a delivery milestone plan per window."""

    id: str = "milestone_planner"
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
        return self._cached_provider._chat_completion_text(
            messages,
            temperature=0.2,
            max_tokens=1000,
        )

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
            return _failure("milestone_planner: no transcript provided.")

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(
                    transcript=transcript,
                    active_intents=active_intents,
                    tags=tags,
                    project_name=project_name,
                ),
            },
        ]

        try:
            raw = self._call_intel(messages)
        except Exception as exc:
            log.info("milestone_planner: intel call failed: %s", exc)
            return _failure(f"milestone_planner: intel call failed: {exc}")

        milestones = _extract_milestones(raw or "")
        if milestones is None:
            return _failure(
                "milestone_planner: response did not contain a parseable milestone list."
            )
        if not milestones:
            return _failure("milestone_planner: no milestones found.")

        dated = sum(1 for m in milestones if m["target"])
        summary = (
            f"{len(milestones)} milestone(s); {dated} with a target date."
            if dated
            else f"{len(milestones)} milestone(s)."
        )

        return {
            "summary": summary,
            "milestones": milestones,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "MilestonePlannerPlugin",
    "_extract_milestones",
]
