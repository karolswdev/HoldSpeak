"""Real `risk_heatmap` plugin (HS-28-04).

Flips the `DeterministicPlugin` stub for `risk_heatmap` to a real LLM-backed
synthesizer. Risk surfacing is cross-cutting — eng, delivery, and incident
meetings all raise risks ("if the vendor slips we can't launch", "the migration
could lose data"). A real run captures each as a register row: impact, likelihood,
mitigation, owner.

Note the ID/artifact mismatch is intentional and pre-existing: the plugin ID is
`risk_heatmap` but the artifact type is `risk_register` (see
`synthesis._ARTIFACT_TYPE_BY_PLUGIN`). v1 renders a structured table, not a
literal 2D heatmap.

Mirrors the Phase-16 / Phase-27 pattern: strict prompt → single fenced ```json
block → parse/validate → structured output. Returns the success shape (`summary`,
`risks`, `confidence_hint=1.0`, `active_intents`) when at least one risk is found,
else the failure shape.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.risk_heatmap")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Canonical severity levels and the synonyms we coerce into them.
_LEVELS = ("low", "medium", "high")
_LEVEL_SYNONYMS: dict[str, str] = {
    "low": "low",
    "minor": "low",
    "small": "low",
    "unlikely": "low",
    "rare": "low",
    "medium": "medium",
    "moderate": "medium",
    "med": "medium",
    "possible": "medium",
    "high": "high",
    "major": "high",
    "severe": "high",
    "critical": "high",
    "likely": "high",
    "almost certain": "high",
}

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?", "unassigned", "unknown"}


_SYSTEM_PROMPT = (
    "You build a risk register from a meeting transcript.\n"
    "A risk is something that could go wrong and threaten the goal. For each, "
    "capture: the risk, its impact (low/medium/high), its likelihood "
    "(low/medium/high), a mitigation if discussed, and an owner if named.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"risks": [{"risk": "...", "impact": "low|medium|high", "likelihood": '
    '"low|medium|high", "mitigation": "or null", "owner": "name or null"}]}\n'
    "Use null for an unstated mitigation or owner. Output only the JSON block — "
    "no prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _normalize_level(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in _LEVELS:
        return text
    return _LEVEL_SYNONYMS.get(text, "medium")


def _extract_risks(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the LLM response into a normalized risk list.

    Returns the list (possibly empty) on a structurally valid response, or
    `None` when no parseable `{"risks": [...]}` object is found.
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
    raw_items = obj.get("risks")
    if not isinstance(raw_items, list):
        return None

    risks: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        risk = str(raw.get("risk") or "").strip()
        if not risk:
            continue
        risks.append(
            {
                "risk": risk,
                "impact": _normalize_level(raw.get("impact")),
                "likelihood": _normalize_level(raw.get("likelihood")),
                "mitigation": _optional_field(raw.get("mitigation")),
                "owner": _optional_field(raw.get("owner")),
            }
        )
    return risks


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
        "Build the risk register per the system prompt."
    )


class RiskHeatmapPlugin:
    """LLM-backed plugin building a risk register per window."""

    id: str = "risk_heatmap"
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
            return _failure("risk_heatmap: no transcript provided.")

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
            log.info("risk_heatmap: intel call failed: %s", exc)
            return _failure(f"risk_heatmap: intel call failed: {exc}")

        risks = _extract_risks(raw or "")
        if risks is None:
            return _failure("risk_heatmap: response did not contain a parseable risk list.")
        if not risks:
            return _failure("risk_heatmap: no risks found.")

        high = sum(1 for r in risks if r["impact"] == "high")
        summary = (
            f"{len(risks)} risk(s); {high} high-impact."
            if high
            else f"{len(risks)} risk(s) registered."
        )

        return {
            "summary": summary,
            "risks": risks,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "RiskHeatmapPlugin",
    "_extract_risks",
]
