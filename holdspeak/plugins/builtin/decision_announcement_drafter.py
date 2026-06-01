"""Real `decision_announcement_drafter` plugin (HS-29-03).

Flips the last `DeterministicPlugin` stub to a real LLM-backed artifact generator
— after this, every registered MIR plugin has a real `run()`. Turns the decisions
made in a meeting into shareable announcements: a title, an audience, and a
ready-to-send message.

Mirrors the proven pattern: strict prompt → fenced ```json → parse/validate →
structured output.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.decision_announcement_drafter")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You draft decision announcements from a meeting transcript.\n"
    "For each significant decision worth communicating, draft a short title, the "
    "intended audience (if clear), and a ready-to-send message announcing it.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"announcements": [{"title": "...", "audience": "or null", "message": "..."}]}\n'
    "Return an empty list if there are no decisions worth announcing. Output only "
    "the JSON block — no prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _extract_announcements(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the response into a normalized announcement list (or None)."""
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
    raw_items = obj.get("announcements")
    if not isinstance(raw_items, list):
        return None

    announcements: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()
        message = str(raw.get("message") or "").strip()
        # An announcement needs at least a title and a message.
        if not title or not message:
            continue
        announcements.append(
            {"title": title, "audience": _optional_field(raw.get("audience")), "message": message}
        )
    return announcements


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
    return f"{header}Transcript:\n{transcript}\n\nDraft the decision announcements per the system prompt."


class DecisionAnnouncementDrafterPlugin:
    """LLM-backed plugin drafting decision announcements per window."""

    id: str = "decision_announcement_drafter"
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
        return self._cached_provider._chat_completion_text(messages, temperature=0.3, max_tokens=1200)

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
            return _failure("decision_announcement_drafter: no transcript provided.")

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
            log.info("decision_announcement_drafter: intel call failed: %s", exc)
            return _failure(f"decision_announcement_drafter: intel call failed: {exc}")

        announcements = _extract_announcements(raw or "")
        if announcements is None:
            return _failure(
                "decision_announcement_drafter: response did not contain a parseable announcement list."
            )
        if not announcements:
            return _failure("decision_announcement_drafter: no decisions worth announcing.")

        return {
            "summary": f"{len(announcements)} decision announcement(s) drafted.",
            "announcements": announcements,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = ["DecisionAnnouncementDrafterPlugin", "_extract_announcements"]
