"""Real `decision_capture` plugin: decisions + open questions (HS-27-03).

The single most ubiquitous meeting output — nearly every meeting makes
decisions and leaves questions unresolved. A net-new `synthesizer` (not one of
the original stub IDs), wired into the default profile's base chain so it fires
broadly.

Mirrors the Phase-16 pattern: strict prompt → single fenced ```json block →
parse/validate → structured output. Returns the success shape (`summary`,
`decisions`, `open_questions`, `confidence_hint=1.0`, `active_intents`) when at
least one decision or open question is found, else the failure shape.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.decision_capture")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


_SYSTEM_PROMPT = (
    "You capture the decisions and open questions from a meeting transcript.\n"
    "A *decision* is something the participants settled on or agreed to do. An "
    "*open question* is something raised but left unresolved (no answer, a "
    "deferral, or an explicit 'we'll decide later').\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"decisions": [{"decision": "...", "rationale": "why, or null"}], '
    '"open_questions": ["..."]}\n'
    "Use null for a missing rationale. Use empty lists when there are none. "
    "Output only the JSON block — no prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none", "n/a"}:
        return None
    return text


def _extract_decisions(text: str) -> Optional[dict[str, Any]]:
    """Parse the response into `{"decisions": [...], "open_questions": [...]}`.

    Returns the normalized dict (lists possibly empty) on a structurally valid
    response, or `None` when no parseable object is found.
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

    decisions: list[dict[str, Any]] = []
    for raw in obj.get("decisions") or []:
        if isinstance(raw, dict):
            decision = str(raw.get("decision") or "").strip()
            if decision:
                decisions.append({"decision": decision, "rationale": _optional_field(raw.get("rationale"))})
        elif isinstance(raw, str) and raw.strip():
            decisions.append({"decision": raw.strip(), "rationale": None})

    open_questions: list[str] = []
    for raw in obj.get("open_questions") or []:
        question = str(raw or "").strip()
        if question:
            open_questions.append(question)

    # A dict that had neither key in a recognizable form is not a valid parse.
    if "decisions" not in obj and "open_questions" not in obj:
        return None
    return {"decisions": decisions, "open_questions": open_questions}


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
        "Capture the decisions and open questions per the system prompt."
    )


class DecisionCapturePlugin:
    """LLM-backed plugin capturing decisions + open questions per window."""

    id: str = "decision_capture"
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
            max_tokens=800,
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
            return _failure("decision_capture: no transcript provided.")

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
            log.info("decision_capture: intel call failed: %s", exc)
            return _failure(f"decision_capture: intel call failed: {exc}")

        parsed = _extract_decisions(raw or "")
        if parsed is None:
            return _failure("decision_capture: response did not contain a parseable decisions object.")
        decisions = parsed["decisions"]
        open_questions = parsed["open_questions"]
        if not decisions and not open_questions:
            return _failure("decision_capture: no decisions or open questions found.")

        summary = (
            f"{len(decisions)} decision(s); {len(open_questions)} open question(s)."
        )
        return {
            "summary": summary,
            "decisions": decisions,
            "open_questions": open_questions,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "DecisionCapturePlugin",
    "_extract_decisions",
]
