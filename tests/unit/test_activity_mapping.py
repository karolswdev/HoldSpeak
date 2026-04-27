"""Unit tests for deterministic activity project mapping."""

from __future__ import annotations

from dataclasses import dataclass

from holdspeak.activity_mapping import (
    ActivityMappingRecord,
    first_matching_rule,
    project_id_for_record,
    rule_matches_record,
)


@dataclass(frozen=True)
class Rule:
    project_id: str
    match_type: str
    pattern: str
    entity_type: str | None = None
    enabled: bool = True
    priority: int = 100


def record(**overrides):
    values = {
        "source_browser": "safari",
        "normalized_url": "https://example.atlassian.net/browse/HS-123",
        "title": "HS-123 customer escalation",
        "domain": "example.atlassian.net",
        "entity_type": "jira_ticket",
        "entity_id": "HS-123",
    }
    values.update(overrides)
    return ActivityMappingRecord(**values)


def test_domain_rules_match_exact_and_subdomains() -> None:
    rule = Rule("holdspeak", "domain", "atlassian.net")

    assert rule_matches_record(rule, record()) is True
    assert rule_matches_record(rule, record(domain="other.com")) is False


def test_url_and_title_contains_are_case_insensitive() -> None:
    assert rule_matches_record(Rule("holdspeak", "url_contains", "/BROWSE/hs-"), record()) is True
    assert rule_matches_record(Rule("holdspeak", "title_contains", "CUSTOMER"), record()) is True


def test_entity_type_and_prefix_rules_match_entities() -> None:
    assert rule_matches_record(Rule("holdspeak", "entity_type", "jira_ticket"), record()) is True
    assert rule_matches_record(Rule("holdspeak", "entity_id_prefix", "HS-", "jira_ticket"), record()) is True
    assert rule_matches_record(Rule("other", "entity_id_prefix", "HS-", "github_issue"), record()) is False


def test_github_repo_rules_match_prs_and_issues() -> None:
    github = record(
        domain="github.com",
        normalized_url="https://github.com/openai/codex/pull/99",
        entity_type="github_pull_request",
        entity_id="openai/codex#99",
    )

    assert rule_matches_record(Rule("codex", "github_repo", "OpenAI/Codex"), github) is True
    assert rule_matches_record(Rule("other", "github_repo", "openai/other"), github) is False


def test_source_browser_rules_match_source() -> None:
    assert rule_matches_record(Rule("holdspeak", "source_browser", "Safari"), record()) is True
    assert rule_matches_record(Rule("other", "source_browser", "firefox"), record()) is False


def test_first_matching_rule_ignores_disabled_and_uses_caller_order() -> None:
    disabled = Rule("disabled", "domain", "atlassian.net", enabled=False)
    first = Rule("first", "domain", "atlassian.net", priority=200)
    second = Rule("second", "domain", "atlassian.net", priority=100)

    assert first_matching_rule(record(), [disabled, first, second]) == first
    assert project_id_for_record(record(), [disabled, first, second]) == "first"
