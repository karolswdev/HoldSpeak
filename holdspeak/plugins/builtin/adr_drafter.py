"""Real `adr_drafter` plugin (HS-28-02).

Flips the `DeterministicPlugin` stub for `adr_drafter` to a real LLM-backed
artifact generator. The natural companion to `mermaid_architecture` on
architecture meetings: when a team settles an architectural question, the durable
output is an Architecture Decision Record — context, the decision, its status, and
the consequences.

Mirrors the Phase-16 / Phase-27 pattern: strict prompt → single fenced ```json
block → parse/validate → structured output. Returns the success shape (`summary`,
`adrs`, `confidence_hint=1.0`, `active_intents`) when at least one well-formed ADR
is found, else the failure shape.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from ...logging_config import get_logger

log = get_logger("plugins.adr_drafter")

IntelChat = Callable[[list[dict[str, str]]], str]

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# Canonical ADR statuses and the synonyms we coerce into them.
_VALID_STATUSES = ("proposed", "accepted", "rejected", "superseded", "deprecated")
_STATUS_SYNONYMS: dict[str, str] = {
    "proposed": "proposed",
    "proposal": "proposed",
    "draft": "proposed",
    "open": "proposed",
    "accepted": "accepted",
    "approved": "accepted",
    "agreed": "accepted",
    "decided": "accepted",
    "adopted": "accepted",
    "rejected": "rejected",
    "declined": "rejected",
    "superseded": "superseded",
    "replaced": "superseded",
    "deprecated": "deprecated",
    "obsolete": "deprecated",
}


_SYSTEM_PROMPT = (
    "You draft Architecture Decision Records (ADRs) from a meeting transcript.\n"
    "An ADR captures one architectural decision the participants made or proposed. "
    "For each, capture: a short title, the status, the context (the forces/problem "
    "that prompted it), the decision itself, and the consequences (trade-offs, "
    "follow-ups).\n"
    "status is one of: proposed (discussed, not finalized), accepted (agreed), "
    "rejected (considered and declined), superseded, deprecated. Use proposed when "
    "unsure.\n\n"
    "Output format — strictly: a single fenced code block tagged ```json "
    "containing an object of the form:\n"
    '{"adrs": [{"title": "...", "status": "proposed|accepted|rejected|superseded|'
    'deprecated", "context": "...", "decision": "...", "consequences": "..."}]}\n'
    "Return an empty list if no architectural decisions were discussed. Output "
    "only the JSON block — no prose, no extra fences."
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_status(value: Any) -> str:
    text = _clean(value).lower().replace("-", " ").replace("_", " ").strip()
    if text in _VALID_STATUSES:
        return text
    return _STATUS_SYNONYMS.get(text, "proposed")


def _extract_adrs(text: str) -> Optional[list[dict[str, Any]]]:
    """Parse the LLM response into a normalized ADR list.

    Returns the list (possibly empty) on a structurally valid response, or
    `None` when no parseable `{"adrs": [...]}` object is found.
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
    raw_items = obj.get("adrs")
    if not isinstance(raw_items, list):
        return None

    adrs: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        title = _clean(raw.get("title"))
        decision = _clean(raw.get("decision"))
        # An ADR needs at minimum a title and a decision to be meaningful.
        if not title or not decision:
            continue
        adrs.append(
            {
                "title": title,
                "status": _normalize_status(raw.get("status")),
                "context": _clean(raw.get("context")),
                "decision": decision,
                "consequences": _clean(raw.get("consequences")),
            }
        )
    return adrs


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
        "Draft the ADRs per the system prompt."
    )


class AdrDrafterPlugin:
    """LLM-backed plugin drafting Architecture Decision Records per window."""

    id: str = "adr_drafter"
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
        return self._cached_provider._chat_completion_text(
            messages,
            temperature=0.2,
            max_tokens=1200,
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
            return _failure("adr_drafter: no transcript provided.")

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
            log.info("adr_drafter: intel call failed: %s", exc)
            return _failure(f"adr_drafter: intel call failed: {exc}")

        adrs = _extract_adrs(raw or "")
        if adrs is None:
            return _failure("adr_drafter: response did not contain a parseable ADR list.")
        if not adrs:
            return _failure("adr_drafter: no architectural decisions found.")

        accepted = sum(1 for adr in adrs if adr["status"] == "accepted")
        summary = (
            f"{len(adrs)} ADR(s); {accepted} accepted."
            if accepted
            else f"{len(adrs)} ADR(s) drafted."
        )

        return {
            "summary": summary,
            "adrs": adrs,
            "confidence_hint": 1.0,
            "active_intents": active_intents,
        }


__all__ = [
    "AdrDrafterPlugin",
    "_extract_adrs",
]
