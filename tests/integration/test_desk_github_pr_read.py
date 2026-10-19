"""The review starter reads the PR it is about (Betterment MCP M6), against a real hub.

A real MeetingWebServer (``_boot``: isolated HOME and DB) whose gh runner
replays ONE REAL ``gh pr view --json`` answer
(``tests/fixtures/automations/gh_pr_view.json``, recorded by
``scripts/record_gh_pr_view.py``). The fake ``claude`` on PATH
(``tests/fixtures/fake_agent_cli.py``) is the automation's agent: it calls
``provider.github_pr_get`` over the hub's MCP route with its run credential,
and its answer is the tools' results. No test calls GitHub.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.glass_infra import _boot
from tests.fixtures.fake_agent_cli import calls, install_fake_agent_clis, mcp_runs, path_with, set_tool_plan
from tests.integration.test_desk_engines_tools import TOKEN, _connect, _ok

pytestmark = pytest.mark.timeout(180, method="thread")

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "automations"
PR = json.loads((FIXTURES / "gh_pr_view.json").read_text())
EVENT = json.loads((FIXTURES / "gh_pr_review_requested.json").read_text())


class _Gh:
    """The hub's gh: ``gh pr view`` answers the recorded PR; nothing else runs."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def __call__(self, command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.commands.append(list(command))
        if command[:3] == ["gh", "pr", "view"]:
            if command[3] == str(PR["number"]) and command[4:6] == ["-R", PR["repository"]]:
                return subprocess.CompletedProcess(command, 0, json.dumps(PR["stdout"]), "")
            return subprocess.CompletedProcess(
                command, 1, "", "GraphQL: Could not resolve to a PullRequest with the number of 9.")
        return subprocess.CompletedProcess(command, 1, "", "not in this rig")


@pytest.fixture()
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    gh = _Gh()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=gh)
    bin_dir = install_fake_agent_clis(tmp_path / "home" / "bin")
    monkeypatch.setenv("PATH", path_with(bin_dir))
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    try:
        yield base, gh, bin_dir
    finally:
        server.stop()


def _pr_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The A2 review-request rows (gh pr list shape), about the recorded PR."""
    pr = PR["stdout"]
    return [{**row, "number": pr["number"], "title": pr["title"], "url": pr["url"]} for row in rows]


def test_when_github_asks_me_to_review_the_summary_names_the_changed_files(rig) -> None:
    """Done when (M6): "When GitHub asks me to review" produces a summary that
    names the changed files. The review request is a recorded watch event; the
    agent reads the PR with provider.github_pr_get (one gh pr view on the
    hub, under his gh sign-in); a refused number is a plain error."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.reaction_service import ReactionService
    from holdspeak.services.watch_sources import GitHubWatchSource

    base, gh, bin_dir = rig
    bench = _ok(base, "POST", "/api/workbenches", {"name": "Review starter"})["workbench"]["id"]
    _ok(base, "PUT", f"/api/workbenches/{bench}",
        {"instruction": "When GitHub asks me to review, summarize the PR and name the changed files."})
    _connect(base, "claude")
    _ok(base, "PUT", f"/api/workbenches/{bench}/engine", {"profile_id": "agent-claude"})
    set_tool_plan(bin_dir, "claude", [
        {"name": "provider.github_pr_get", "arguments": {"url": PR["stdout"]["url"]}},
        {"name": "provider.github_pr_get", "arguments": {"owner_repo": PR["repository"], "number": 9}},
    ], once=True)

    def snapshot(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def replay(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
            assert command[:3] == ["gh", "pr", "list"]
            return subprocess.CompletedProcess(command, 0, json.dumps(rows), "")
        return GitHubWatchSource(runner=replay).snapshot(
            owner, query_kind="pull_requests", query={"repository": PR["repository"]})

    owner = Principal(PrincipalKind.OWNER, "desk-github-pr-read")
    reactions = ReactionService(get_database())
    watch = reactions.create_watch(owner, connector_id="gh", query_kind="pull_requests",
                                   query={"repository": PR["repository"]}, watch_id="watch-m6")
    reactions.create_reaction(owner, watch_id=watch["id"], event_pattern="github.pr.review_requested",
                              workbench_id=bench, reaction_id="reaction-m6", enabled=True, auto_run=True)
    asyncio.run(reactions.refresh_watch(owner, watch["id"], snapshot(_pr_rows(EVENT["before"]))))
    asyncio.run(reactions.refresh_watch(owner, watch["id"], snapshot(_pr_rows(EVENT["after"]))))

    (event_run,) = calls(bin_dir, "claude")[:1]
    assert PR["stdout"]["url"] in event_run["prompt"], event_run["prompt"]
    (run,) = mcp_runs(bin_dir, "claude")
    read, refused = run["calls"]
    assert read["status"] == 200 and "result" in read["reply"] and not read["reply"]["result"].get("isError"), read
    pr = json.loads(read["reply"]["result"]["content"][0]["text"])
    files = [f["path"] for f in PR["stdout"]["files"]]
    assert pr["repository"] == PR["repository"] and pr["number"] == PR["number"], pr
    assert [f["path"] for f in pr["files"]] == files and pr["changed_files"] == len(files), pr
    assert pr["title"] == PR["stdout"]["title"] and pr["additions"] == PR["stdout"]["additions"], pr
    assert "Could not resolve to a PullRequest" in json.dumps(refused["reply"]), refused

    newest = _ok(base, "GET", f"/api/workbenches/{bench}")["workbench"]["results"][0]
    assert newest["status"] == "done" and newest["title"] == PR["stdout"]["title"], newest
    assert all(path in newest["text"] for path in files), newest["text"]
    views = [c for c in gh.commands if c[:3] == ["gh", "pr", "view"]]
    assert views[0] == ["gh", "pr", "view", str(PR["number"]), "-R", PR["repository"],
                        "--json", PR["command"][-1]], views


def test_a_pr_read_says_who_is_asked_and_refuses_a_bad_name() -> None:
    """The answer names each review request (a person by login, a team by its
    slug), cuts a long body, and refuses a call that names no PR."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError, ValidationError
    from holdspeak.services.github_provider import PR_BODY_LIMIT, GitHubProviderAdapter, pr_from_gh

    row = {**PR["stdout"], "body": "x" * (PR_BODY_LIMIT + 5), "reviewRequests": [
        {"__typename": "User", "login": "karolswdev"},
        {"__typename": "Team", "name": "Ledger reviewers", "slug": "ledger-reviewers"}]}
    answer = pr_from_gh(row, PR["repository"])
    assert answer["review_requests"] == ["karolswdev", "ledger-reviewers"]
    assert len(answer["body"]) == PR_BODY_LIMIT and answer["body_cut"] is True
    assert answer["state"] == PR["stdout"]["state"].lower() and answer["author"] == PR["stdout"]["author"]["login"]

    agent = Principal(PrincipalKind.AGENT, "agent:run:run_m6")
    adapter = GitHubProviderAdapter(runner=_Gh())
    for bad in ({}, {"owner_repo": "not-a-repo", "number": 1}, {"owner_repo": "a/b", "number": 0}):
        with pytest.raises(ValidationError):
            adapter.pr_get(agent, **bad)
    with pytest.raises(ServiceError) as missing:
        adapter.pr_get(agent, owner_repo=PR["repository"], number=9)
    assert missing.value.code == "scope_denied", missing.value.code
    assert adapter.pr_get(agent, url=PR["stdout"]["url"])["number"] == PR["number"]
