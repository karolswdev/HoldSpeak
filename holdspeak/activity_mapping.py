"""Deterministic project mapping rules for local activity records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional


VALID_ACTIVITY_PROJECT_MATCH_TYPES = frozenset(
    {
        "domain",
        "url_contains",
        "title_contains",
        "entity_type",
        "entity_id_prefix",
        "github_repo",
        "source_browser",
    }
)


@dataclass(frozen=True)
class ActivityMappingRecord:
    """Small record shape used before an activity row has been persisted."""

    source_browser: str
    normalized_url: str
    title: Optional[str]
    domain: str
    entity_type: Optional[str]
    entity_id: Optional[str]


def normalize_match_type(value: object) -> str:
    """Normalize and validate an activity project rule match type."""
    normalized = str(value or "").strip().lower()
    if normalized not in VALID_ACTIVITY_PROJECT_MATCH_TYPES:
        raise ValueError(
            "activity project rule match_type must be one of "
            f"{sorted(VALID_ACTIVITY_PROJECT_MATCH_TYPES)}"
        )
    return normalized


def rule_matches_record(rule: Any, record: Any) -> bool:
    """Return true when one deterministic rule matches one activity record."""
    match_type = normalize_match_type(getattr(rule, "match_type", ""))
    pattern = _clean_pattern(getattr(rule, "pattern", ""))
    if not pattern and match_type not in {"entity_type"}:
        return False

    if match_type == "domain":
        domain = str(getattr(record, "domain", "") or "").strip().lower()
        return bool(domain) and (domain == pattern or domain.endswith(f".{pattern}"))

    if match_type == "url_contains":
        return pattern in str(getattr(record, "normalized_url", "") or "").lower()

    if match_type == "title_contains":
        return pattern in str(getattr(record, "title", "") or "").lower()

    if match_type == "entity_type":
        entity_type = str(getattr(record, "entity_type", "") or "").strip().lower()
        return entity_type == pattern

    if match_type == "entity_id_prefix":
        if not _entity_type_allowed(rule, record):
            return False
        entity_id = str(getattr(record, "entity_id", "") or "")
        return entity_id.lower().startswith(pattern)

    if match_type == "github_repo":
        entity_type = str(getattr(record, "entity_type", "") or "").strip().lower()
        if entity_type not in {"github_pull_request", "github_issue"}:
            return False
        entity_id = str(getattr(record, "entity_id", "") or "").lower()
        return entity_id.startswith(f"{pattern}#")

    if match_type == "source_browser":
        source_browser = str(getattr(record, "source_browser", "") or "").strip().lower()
        return source_browser == pattern

    return False


def first_matching_rule(record: Any, rules: Iterable[Any]) -> Optional[Any]:
    """Return the first enabled rule that matches in caller-provided order."""
    for rule in rules:
        if not bool(getattr(rule, "enabled", True)):
            continue
        if rule_matches_record(rule, record):
            return rule
    return None


def project_id_for_record(record: Any, rules: Iterable[Any]) -> Optional[str]:
    """Return the matching project ID for a record, if any."""
    rule = first_matching_rule(record, rules)
    if rule is None:
        return None
    project_id = str(getattr(rule, "project_id", "") or "").strip()
    return project_id or None


def _clean_pattern(value: object) -> str:
    return str(value or "").strip().lower()


def _entity_type_allowed(rule: Any, record: Any) -> bool:
    rule_entity_type = str(getattr(rule, "entity_type", "") or "").strip().lower()
    if not rule_entity_type:
        return True
    record_entity_type = str(getattr(record, "entity_type", "") or "").strip().lower()
    return record_entity_type == rule_entity_type
