from __future__ import annotations

import json
import subprocess

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from holdspeak.services.watch_sources import GitHubWatchSource


OWNER = Principal(PrincipalKind.OWNER, "watch-owner")


def test_github_watch_source_owns_query_and_normalization() -> None:
    captured = {}

    def runner(command, **kwargs):  # noqa: ANN001
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, json.dumps([{
            "number": 17, "title": "Review me", "url": "https://github.com/acme/app/pull/17",
            "state": "OPEN", "isDraft": False,
            "reviewRequests": [{"login": "karol"}], "reviewDecision": "REVIEW_REQUIRED",
            "statusCheckRollup": [{"conclusion": "FAILURE"}],
            "headRefOid": "abc", "updatedAt": "2026-08-16T20:00:00Z",
        }]), "")

    rows = GitHubWatchSource(runner=runner).snapshot(
        OWNER, query_kind="pull_requests",
        query={"repository": "acme/app", "search": "review-requested:@me"},
    )
    assert captured["command"][:6] == ["gh", "pr", "list", "--repo", "acme/app", "--state"]
    assert captured["command"][-2:] == ["--search", "review-requested:@me"]
    assert rows[0]["reviewRequests"] == ["karol"]
    assert rows[0]["checks"] == "failing"


def test_github_watch_requires_a_scoped_repository() -> None:
    with pytest.raises(ValidationError, match="owner/name"):
        GitHubWatchSource(runner=lambda *_args, **_kwargs: None).snapshot(
            OWNER, query_kind="pull_requests", query={"repository": "everything"},
        )
