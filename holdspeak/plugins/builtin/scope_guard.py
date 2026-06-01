"""Real `scope_guard` plugin (HS-29-01).

Flips the `DeterministicPlugin` stub for `scope_guard` to a real LLM-backed
validator. Product/planning meetings drift; `scope_guard` flags what's in scope,
out of scope, and — most usefully — what looks like scope creep.

Mirrors the proven pattern: strict prompt → fenced ```json → parse/validate →
structured output.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.scope_guard")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_VALID_VERDICTS = ("in_scope", "out_of_scope", "scope_creep")
_VERDICT_SYNONYMS: dict[str, str] = {
    "in scope": "in_scope",
    "in_scope": "in_scope",
    "included": "in_scope",
    "committed": "in_scope",
    "out of scope": "out_of_scope",
    "out_of_scope": "out_of_scope",
    "excluded": "out_of_scope",
    "deferred": "out_of_scope",
    "scope creep": "scope_creep",
    "scope_creep": "scope_creep",
    "creep": "scope_creep",
    "new ask": "scope_creep",
    "stretch": "scope_creep",
}

_NULLISH = {"", "null", "none", "n/a", "na", "tbd", "?"}


_SYSTEM_PROMPT = (
    "You guard scope on a product/planning meeting transcript.\n"
    "For each item discussed, classify it as: in_scope (agreed part of this "
    "effort), out_of_scope (explicitly excluded or deferred), or scope_creep (a "
    "new ask that expands the agreed scope without a decision). Give a short "
    "rationale if stated.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"findings": [{"item": "...", "verdict": "in_scope|out_of_scope|scope_creep", '
    '"rationale": "or null"}]}\n'
    "Return an empty list if scope was not discussed. Output only the JSON block — "
    "no prose, no extra fences."
)


def _optional_field(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in _NULLISH:
        return None
    return text


def _normalize_verdict(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", " ")
    underscored = text.replace(" ", "_")
    if underscored in _VALID_VERDICTS:
        return underscored
    return _VERDICT_SYNONYMS.get(text) or _VERDICT_SYNONYMS.get(underscored, "in_scope")


def _extract_findings(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the response into a normalized scope-finding list (or None)."""
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
    raw_items = obj.get("findings")
    if not isinstance(raw_items, list):
        return None

    findings: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item = str(raw.get("item") or "").strip()
        if not item:
            continue
        findings.append(
            {
                "item": item,
                "verdict": _normalize_verdict(raw.get("verdict")),
                "rationale": _optional_field(raw.get("rationale")),
            }
        )
    return findings


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
    return f"{header}Transcript:\n{transcript}\n\nGuard the scope per the system prompt."


class ScopeGuardPlugin:
    """LLM-backed plugin classifying scope (in/out/creep) per window."""

    id: str = "scope_guard"
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
            return _failure("scope_guard: no transcript provided.")

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
            log.info("scope_guard: intel call failed: %s", exc)
            return _failure(f"scope_guard: intel call failed: {exc}")

        findings = _extract_findings(raw or "")
        if findings is None:
            return _failure("scope_guard: response did not contain a parseable findings list.")
        if not findings:
            return _failure("scope_guard: no scope findings.")

        creep = sum(1 for f in findings if f["verdict"] == "scope_creep")
        summary = (
            f"{len(findings)} scope finding(s); {creep} flagged as scope creep."
            if creep
            else f"{len(findings)} scope finding(s)."
        )
        return {
            "summary": summary,
            "findings": findings,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = ["ScopeGuardPlugin", "_extract_findings", "_normalize_verdict"]
