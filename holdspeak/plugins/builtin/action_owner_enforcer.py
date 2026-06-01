"""Real `action_owner_enforcer` plugin: LLM-backed action-item ownership check.

Phase 27 / HS-27-01. Replaces the `DeterministicPlugin` stub for
`action_owner_enforcer` — the most ubiquitous of the stubs (almost every working
meeting produces action items, and the common failure mode is items with no
clear owner or due date).

The plugin mirrors the `mermaid_architecture` pattern:
  1. Build a strict prompt asking the LLM for the meeting's action items as a
     single fenced ```json block: a list of {task, owner|null, due|null}.
  2. Call the configured intel provider via `MeetingIntel._chat_completion_text`.
  3. Parse + validate the JSON (`_extract_action_items`); per item, compute the
     ownership/scheduling `gap`.
  4. Return the success shape (`summary`, `action_items`, `confidence_hint=1.0`,
     `active_intents`) or the failure shape (`summary`, `confidence_hint=0.0`,
     `active_intents` — `action_items` key absent).

This is a `validator`: it emits an ownership-gap *artifact*; it does not mutate
HoldSpeak's existing action-item review system.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.action_owner_enforcer")


IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Owner strings that actually mean "no owner".
_UNASSIGNED = {"", "null", "none", "n/a", "na", "unassigned", "unknown", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You extract action items from meeting transcripts.\n"
    "Identify every concrete action/task the participants committed to. For each, "
    "capture who owns it and when it is due, if stated.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"action_items": [{"task": "...", "owner": "name or null", "due": "date/'
    'timeframe or null"}]}\n'
    "Use null (not a guess) when the owner or due date was not stated. If there "
    "are no action items, return an empty list. Output only the JSON block — no "
    "prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _UNASSIGNED:
        return None
    return text


def _gap_for(owner: Optional[str], due: Optional[str]) -> Optional[str]:
    if owner is None and due is None:
        return "missing_both"
    if owner is None:
        return "missing_owner"
    if due is None:
        return "missing_due"
    return None


def _extract_action_items(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the LLM response into a normalized action-item list.

    Returns the list (possibly empty) on a structurally valid response, or
    `None` when no parseable `{"action_items": [...]}` object is found.
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
    raw_items = obj.get("action_items")
    if not isinstance(raw_items, list):
        return None

    items: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        task = str(raw.get("task") or "").strip()
        if not task:
            continue
        owner = _optional_field(raw.get("owner"))
        due = _optional_field(raw.get("due"))
        items.append(
            {"task": task, "owner": owner, "due": due, "gap": _gap_for(owner, due)}
        )
    return items


def _build_user_prompt(
    *,
    transcript: str,
    active_intents: list[str],
    tags: list[str],
    project_name: str,
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
        "Extract the action items per the system prompt."
    )


class ActionOwnerEnforcerPlugin:
    """LLM-backed plugin flagging action items with missing owner/due date."""

    id: str = "action_owner_enforcer"
    version: str = "0.1.0"
    kind: str = "validator"
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
            max_tokens=800,
        )

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        transcript = str(context.get("transcript") or "").strip()
        active_intents = [
            str(intent).strip().lower()
            for intent in (context.get("active_intents") or [])
            if str(intent).strip()
        ]
        tags = [
            str(tag).strip()
            for tag in (context.get("tags") or [])
            if str(tag).strip()
        ]
        project_name = str(
            context.get("project_name") or context.get("project") or ""
        ).strip()

        def _failure(reason: str) -> dict[str, Any]:
            return {
                "summary": reason,
                "confidence_hint": 0.0,
                "active_intents": active_intents,
            }

        if not transcript:
            return _failure("action_owner_enforcer: no transcript provided.")

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
            log.info("action_owner_enforcer: intel call failed: %s", exc)
            return _failure(f"action_owner_enforcer: intel call failed: {exc}")

        items = _extract_action_items(raw or "")
        if items is None:
            return _failure(
                "action_owner_enforcer: response did not contain a parseable action-item list."
            )
        if not items:
            return _failure("action_owner_enforcer: no action items found.")

        gaps = sum(1 for item in items if item["gap"])
        summary = (
            f"{len(items)} action item(s); {gaps} missing an owner or due date."
            if gaps
            else f"{len(items)} action item(s); all have an owner and due date."
        )

        return {
            "summary": summary,
            "action_items": items,
            "gap_count": gaps,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "ActionOwnerEnforcerPlugin",
    "_extract_action_items",
]
