"""Real `requirements_extractor` plugin (HS-27-04).

Flips the `DeterministicPlugin` stub for `requirements_extractor` to a real
LLM-backed synthesizer. Common on eng/product/planning meetings — it pulls the
requirements expressed in a transcript and classifies each as functional, a
non-functional quality, a constraint, or an acceptance criterion.

Mirrors the Phase-16 / HS-27-03 pattern: strict prompt → single fenced ```json
block → parse/validate → structured output. Returns the success shape
(`summary`, `requirements`, `confidence_hint=1.0`, `active_intents`) when at
least one requirement is found, else the failure shape.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.requirements_extractor")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Canonical requirement types and the synonyms we coerce into them.
_VALID_TYPES = ("functional", "non_functional", "constraint", "acceptance")
_TYPE_SYNONYMS: dict[str, str] = {
    "functional": "functional",
    "function": "functional",
    "feature": "functional",
    "non_functional": "non_functional",
    "non-functional": "non_functional",
    "nonfunctional": "non_functional",
    "non functional": "non_functional",
    "nfr": "non_functional",
    "quality": "non_functional",
    "constraint": "constraint",
    "constraints": "constraint",
    "limitation": "constraint",
    "acceptance": "acceptance",
    "acceptance_criteria": "acceptance",
    "acceptance criteria": "acceptance",
    "acceptance_criterion": "acceptance",
    "criteria": "acceptance",
}


_SYSTEM_PROMPT = (
    "You extract requirements from a meeting transcript.\n"
    "A *requirement* is something the product/system must do or satisfy. "
    "Classify each as one of:\n"
    "- functional: a behavior or capability the system must provide.\n"
    "- non_functional: a quality attribute (performance, security, scalability, "
    "usability, reliability).\n"
    "- constraint: a fixed limitation (budget, deadline, technology, regulation).\n"
    "- acceptance: a concrete acceptance criterion / definition of done.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"requirements": [{"text": "...", "type": "functional|non_functional|'
    'constraint|acceptance"}]}\n'
    "Use an empty list when there are no requirements. Output only the JSON "
    "block — no prose, no extra fences."
)


def _normalize_type(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    if text in _VALID_TYPES:
        return text
    # Try both the underscored and spaced forms against the synonym table.
    return _TYPE_SYNONYMS.get(text) or _TYPE_SYNONYMS.get(text.replace("_", " "), "functional")


def _extract_requirements(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the LLM response into a normalized requirement list.

    Returns the list (possibly empty) on a structurally valid response, or
    `None` when no parseable `{"requirements": [...]}` object is found.
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
    raw_items = obj.get("requirements")
    if not isinstance(raw_items, list):
        return None

    items: list[dict[str, Any]] = []
    for raw in raw_items:
        if isinstance(raw, dict):
            req_text = str(raw.get("text") or "").strip()
            req_type = _normalize_type(raw.get("type"))
        elif isinstance(raw, str):
            req_text = raw.strip()
            req_type = "functional"
        else:
            continue
        if req_text:
            items.append({"text": req_text, "type": req_type})
    return items


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
        "Extract the requirements per the system prompt."
    )


class RequirementsExtractorPlugin:
    """LLM-backed plugin extracting + classifying requirements per window."""

    id: str = "requirements_extractor"
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
            return _failure("requirements_extractor: no transcript provided.")

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
            log.info("requirements_extractor: intel call failed: %s", exc)
            return _failure(f"requirements_extractor: intel call failed: {exc}")

        items = _extract_requirements(raw or "")
        if items is None:
            return _failure(
                "requirements_extractor: response did not contain a parseable requirements list."
            )
        if not items:
            return _failure("requirements_extractor: no requirements found.")

        by_type: dict[str, int] = {}
        for item in items:
            by_type[item["type"]] = by_type.get(item["type"], 0) + 1
        breakdown = ", ".join(
            f"{by_type[t]} {t.replace('_', '-')}" for t in _VALID_TYPES if by_type.get(t)
        )
        summary = f"{len(items)} requirement(s)" + (f" ({breakdown})." if breakdown else ".")

        return {
            "summary": summary,
            "requirements": items,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "RequirementsExtractorPlugin",
    "_extract_requirements",
]
