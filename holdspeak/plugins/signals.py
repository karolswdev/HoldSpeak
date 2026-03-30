"""Deterministic lexical signal extraction for MIR routing."""

from __future__ import annotations

import re

SUPPORTED_INTENTS: tuple[str, ...] = (
    "architecture",
    "delivery",
    "product",
    "incident",
    "comms",
)

_INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "architecture": ("architecture", "design", "adr", "api", "schema", "latency", "service", "interface"),
    "delivery": ("sprint", "deliver", "milestone", "estimate", "deadline", "owner", "dependency", "roadmap"),
    "product": ("customer", "persona", "feature", "scope", "outcome", "kpi", "feedback", "value"),
    "incident": ("incident", "outage", "sev", "severity", "rollback", "mitigation", "postmortem", "blast radius"),
    "comms": ("announce", "announcement", "stakeholder", "update", "email", "slack", "recap", "message"),
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _match_count(haystack: str, keywords: tuple[str, ...]) -> int:
    count = 0
    for keyword in keywords:
        term = keyword.strip().lower()
        if not term:
            continue
        # Deterministic substring matching keeps this lightweight.
        if term in haystack:
            count += 1
    return count


def extract_intent_signals(
    transcript: str | None,
    *,
    tags: list[str] | None = None,
) -> dict[str, float]:
    """Extract normalized multi-intent lexical scores from transcript + tags."""
    raw_tags = [str(tag).strip().lower() for tag in (tags or []) if str(tag).strip()]
    haystack = _normalize_text(f"{transcript or ''} {' '.join(raw_tags)}")

    scores = {intent: 0.0 for intent in SUPPORTED_INTENTS}
    if not haystack:
        return scores

    for intent in SUPPORTED_INTENTS:
        keywords = _INTENT_KEYWORDS.get(intent, ())
        if not keywords:
            continue

        keyword_hits = _match_count(haystack, keywords)
        tag_boost = 1 if intent in raw_tags else 0
        # Saturating hit-based score keeps previews useful on short transcripts.
        score = min(1.0, (0.22 * keyword_hits) + (0.2 * tag_boost))
        scores[intent] = round(score, 4)

    return scores
