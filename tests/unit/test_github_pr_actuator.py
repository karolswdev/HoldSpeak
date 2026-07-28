"""HS-106-08: approved GitHub PR writes stay narrow and payload-bound."""
from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from holdspeak.plugins.builtin.github_pr_actuator import build_github_pr_connector


def test_comment_connector_runs_only_gh_pr_comment() -> None:
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "https://github.com/o/r/pull/393#issuecomment-1\n", "")

    connector = build_github_pr_connector("comment", runner=runner)
    result = connector(
        SimpleNamespace(payload={"repo": "o/r", "number": 393, "body": "Full review text"})
    )
    assert calls == [[
        "gh", "pr", "comment", "393", "--repo", "o/r", "--body", "Full review text"
    ]]
    assert "issuecomment" in result["output"]


def test_status_connector_cannot_smuggle_another_command() -> None:
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "{}", "")

    connector = build_github_pr_connector("status", runner=runner)
    connector(
        SimpleNamespace(
            payload={
                "repo": "o/r",
                "sha": "a" * 40,
                "state": "pending",
                "context": "HoldSpeak",
                "description": "Review in progress",
            }
        )
    )
    assert calls[0][:5] == ["gh", "api", "--method", "POST", f"repos/o/r/statuses/{'a' * 40}"]
    assert "merge" not in calls[0]
    assert "close" not in calls[0]


def test_comment_connector_refuses_invalid_repo_before_runner() -> None:
    connector = build_github_pr_connector(
        "comment", runner=lambda *args, **kwargs: pytest.fail("runner must stay silent")
    )
    with pytest.raises(ValueError, match="github_pr_comment_payload_invalid"):
        connector(SimpleNamespace(payload={"repo": "o/r;evil", "number": 1, "body": "x"}))
