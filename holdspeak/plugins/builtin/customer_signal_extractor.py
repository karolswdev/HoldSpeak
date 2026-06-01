"""Real `customer_signal_extractor` plugin (HS-29-01).

Flips the `DeterministicPlugin` stub for `customer_signal_extractor` to a real
LLM-backed signals plugin. Product/customer meetings carry signals — feature
requests, pain points, praise, churn risk. A real run captures each with its type
and a supporting quote if present.

Mirrors the proven pattern: strict prompt → fenced ```json → parse/validate →
structured output.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.customer_signal_extractor")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_VALID_TYPES = ("request", "pain", "praise", "churn_risk")
_TYPE_SYNONYMS: dict[str, str] = {
    "request": "request",
    "feature request": "request",
    "feature_request": "request",
    "ask": "request",
    "pain": "pain",
    "pain point": "pain",
    "pain_point": "pain",
    "complaint": "pain",
    "frustration": "pain",
    "issue": "pain",
    "praise": "praise",
    "positive": "praise",
    "compliment": "praise",
    "churn_risk": "churn_risk",
    "churn risk": "churn_risk",
    "churn": "churn_risk",
    "cancellation": "churn_risk",
}

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You extract customer signals from a meeting transcript.\n"
    "A signal is something a customer expressed. Classify each as: request (a "
    "feature/capability ask), pain (a frustration or problem), praise (positive "
    "feedback), or churn_risk (a sign they might leave). Include a short "
    "supporting quote if one is present.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"signals": [{"signal": "...", "type": "request|pain|praise|churn_risk", '
    '"quote": "or null"}]}\n'
    "Return an empty list if there are no customer signals. Output only the JSON "
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
    text = str(value or "").strip().lower().replace("-", " ")
    underscored = text.replace(" ", "_")
    if underscored in _VALID_TYPES:
        return underscored
    return _TYPE_SYNONYMS.get(text) or _TYPE_SYNONYMS.get(underscored, "request")


def _extract_signals(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the response into a normalized customer-signal list (or None)."""
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
    raw_items = obj.get("signals")
    if not isinstance(raw_items, list):
        return None

    signals: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        signal = str(raw.get("signal") or "").strip()
        if not signal:
            continue
        signals.append(
            {
                "signal": signal,
                "type": _normalize_type(raw.get("type")),
                "quote": _optional_field(raw.get("quote")),
            }
        )
    return signals


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
    return f"{header}Transcript:\n{transcript}\n\nExtract the customer signals per the system prompt."


class CustomerSignalExtractorPlugin:
    """LLM-backed plugin extracting + classifying customer signals per window."""

    id: str = "customer_signal_extractor"
    version: str = "0.1.0"
    kind: str = "signals"
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
            return _failure("customer_signal_extractor: no transcript provided.")

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
            log.info("customer_signal_extractor: intel call failed: %s", exc)
            return _failure(f"customer_signal_extractor: intel call failed: {exc}")

        signals = _extract_signals(raw or "")
        if signals is None:
            return _failure("customer_signal_extractor: response did not contain a parseable signals list.")
        if not signals:
            return _failure("customer_signal_extractor: no customer signals found.")

        by_type: dict[str, int] = {}
        for s in signals:
            by_type[s["type"]] = by_type.get(s["type"], 0) + 1
        breakdown = ", ".join(f"{by_type[t]} {t.replace('_', ' ')}" for t in _VALID_TYPES if by_type.get(t))
        summary = f"{len(signals)} customer signal(s)" + (f" ({breakdown})." if breakdown else ".")
        return {
            "summary": summary,
            "signals": signals,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = ["CustomerSignalExtractorPlugin", "_extract_signals", "_normalize_type"]
