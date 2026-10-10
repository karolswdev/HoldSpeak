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
         cause: str | None = "Not signed in", reason: str | None = None, verb: str = "Reconnect",
         href: str = "/settings", host: str = "github.com") -> dict:
    return {
        "source_id": f"watch:w{n}", "kind": "watch", "state": state, "provider": provider,
        "label": f"GitHub · acme/r{n}", "project_id": f"p{n}", "host": host,
        "reason": reason if reason is not None else (cause or RAW), "cause": cause,
        "repair": {"token": token, "verb": verb, "href": href},
    }


def test_thirty_sources_of_one_cause_and_one_repair_are_one_group() -> None:
    # Thirty Rooms; Reconnect goes to Settings for every one of them.
    coverage = [_gap(n) for n in range(30)]
    groups = unread_source_groups(coverage)
    assert len(groups) == 1
    assert len(groups[0]) == 30


def test_a_different_provider_token_or_cause_is_its_own_group() -> None:
    coverage = [
        _gap(1), _gap(2),
        _gap(3, provider="jira"),
        _gap(4, token="STALE", state="stale", cause="not checked recently"),
        _gap(5, cause="Tool not installed"),
        {"source_id": "x", "kind": "watch", "state": "available", "provider": "github"},
        _gap(6, state="quiet", token="QUIET UNTIL 08:00", cause="quiet until 08:00"),
    ]
    groups = unread_source_groups(coverage)
    # The available and the quiet sources are never counted.
    assert [len(g) for g in groups] == [2, 1, 1, 1]
    assert source_group_key(coverage[0]) == source_group_key(coverage[1])


def test_a_different_repair_destination_is_its_own_group() -> None:
    # Astra r1 (1): two paused Watches in two Rooms each open their own Room.
    a = _gap(1, state="unavailable", token="PAUSED", cause="paused", verb="Open source", href="/projects/pA")
    b = _gap(2, state="unavailable", token="PAUSED", cause="paused", verb="Open source", href="/projects/pB")
    assert len(unread_source_groups([a, b])) == 2


def test_a_different_egress_host_is_its_own_group() -> None:
    # Astra r1 (3): Retry on two Jira sites names two hosts.
    a = _gap(1, provider="jira", state="stale", token="STALE", cause="not checked recently",
             verb="Retry", href="/projects/p1", host="a.atlassian.net")
    b = {**a, "source_id": "watch:w2", "host": "b.atlassian.net"}
    assert len(unread_source_groups([a, b])) == 2


def test_unknown_causes_group_only_on_the_same_first_line() -> None:
    # Astra r1 (2): a 404 and a 429 are two problems, never one row.
    e404 = _gap(1, cause=None, reason="HTTP 404: Not Found (repos/acme/r1)")
    e429 = _gap(2, cause=None, reason="HTTP 429: rate limit exceeded")
    e429b = _gap(3, cause=None, reason="HTTP 429:  rate limit exceeded\nretry-after: 60")
    groups = unread_source_groups([e404, e429, e429b])
    assert [len(g) for g in groups] == [1, 2]


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
