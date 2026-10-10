"""PHILO-17 (needsyou): sources of one cause are ONE Needs-you row.

The walker saw 34 rows: 31 GitHub/Jira sources that could not be checked,
each its own row with a raw runner error, above the three rows that needed
him. The hub now counts the sources of one cause once (``source_group_key``),
names a plain cause when it has one, and keeps the raw line in ``reason``.
"""
from __future__ import annotations

from datetime import datetime

from holdspeak.services.needs_you_aggregate import _watch_coverage
from holdspeak.services.needs_you_membership import source_group_key, unread_source_groups
from holdspeak.services.project_service import ProjectService

RAW = "To get started with GitHub CLI, please run:  gh auth login"


def _gap(n: int, *, provider: str = "github", token: str = "CANT CHECK", state: str = "failed",
         cause: str | None = None) -> dict:
    return {
        "source_id": f"watch:w{n}", "kind": "watch", "state": state, "provider": provider,
        "label": f"GitHub · acme/r{n}", "project_id": f"p{n}", "reason": f"{RAW} r{n}",
        "cause": cause, "repair": {"token": token, "verb": "Reconnect", "href": "/settings"},
    }


def test_thirty_sources_of_one_cause_are_one_group() -> None:
    coverage = [_gap(n) for n in range(30)]
    groups = unread_source_groups(coverage)
    assert len(groups) == 1
    assert len(groups[0]) == 30


def test_a_different_provider_token_or_cause_is_its_own_group() -> None:
    coverage = [
        _gap(1), _gap(2),
        _gap(3, provider="jira"),
        _gap(4, token="STALE", state="stale"),
        _gap(5, cause="Not signed in"),
        {"source_id": "x", "kind": "watch", "state": "available", "provider": "github"},
        {**_gap(6, state="quiet", token="QUIET UNTIL 08:00")},
    ]
    groups = unread_source_groups(coverage)
    # The available and the quiet sources are never counted.
    assert [len(g) for g in groups] == [2, 1, 1, 1]
    assert source_group_key(coverage[0]) == source_group_key(coverage[1])


def test_a_signed_out_cli_reads_not_signed_in() -> None:
    assert ProjectService._plain_reason(RAW) == "Not signed in"
    assert "Not signed in" in ProjectService.PLAIN_REASONS


def test_watch_coverage_names_the_provider_and_a_plain_cause_only() -> None:
    now = datetime(2026, 10, 10, 9, 0)
    room = {"sources": {"state": "ok", "items": [
        {"watchId": "w1", "provider": "gh", "scope": "acme/r1", "state": "cant_check",
         "plainReason": "fatal: some raw runner line 0x7f"},
        {"watchId": "w2", "provider": "jira", "scope": "KAN", "state": "cant_check",
         "plainReason": "Jira rejected the query"},
        {"watchId": "w3", "provider": "github", "scope": "acme/r3", "state": "live",
         "checkedAt": "2026-10-09T01:00:00"},
    ]}}
    rows = {row["source_id"]: row for row in _watch_coverage(room, "p1", "Payments", now, 3600.0)}
    raw = rows["watch:w1"]
    assert raw["provider"] == "github" and raw["cause"] is None
    assert raw["reason"] == "fatal: some raw runner line 0x7f"
    assert rows["watch:w2"]["cause"] == "Jira rejected the query"
    stale = rows["watch:w3"]
    assert stale["state"] == "stale" and stale["cause"] == "not checked recently"
