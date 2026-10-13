"""The Door rig: gh and acli fixture runners and the Door opener.

Lifted from the parked tests/e2e/_parked/test_hs169_door_glass.py so the
live walks and recorders keep one copy. Not a test file.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .glass_infra import _normal_chair


def _open_door(page: Any, url: str) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["project-setup"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


# ── GH fixture runner ─────────────────────────────────────────────

_GH_AUTH_CONNECTED = {
    "stdout": "github.com\n  Logged in to github.com account karolswdev (keyring)\n",
    "returncode": 0,
}
_GH_AUTH_COLD = {
    "stderr": "You are not logged into any GitHub hosts. Run gh auth login to authenticate.\n",
    "returncode": 1,
}
_GH_REPO_LIST = json.dumps([
    {"name": "HoldSpeak", "owner": {"login": "karolswdev"}, "visibility": "public"},
    {"name": "reusable-processes", "owner": {"login": "karolswdev"}, "visibility": "private"},
    {"name": "warpdrv", "owner": {"login": "karolswdev"}, "visibility": "public"},
    {"name": "HoldSpeak-docs", "owner": {"login": "karolswdev"}, "visibility": "public"},
])
_GH_PR_SNAPSHOT = json.dumps([
    {
        "number": 612, "title": "Rig settles animations before every shot",
        "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [], "reviewDecision": "",
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "headRefOid": "abc123", "updatedAt": "2026-09-01T13:26:00Z",
    },
    {
        "number": 610, "title": "Add surface library ScrollHint",
        "url": "https://github.com/karolswdev/HoldSpeak/pull/610",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [], "reviewDecision": "",
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "headRefOid": "def456", "updatedAt": "2026-09-01T12:30:00Z",
    },
    {
        "number": 608, "title": "Fix CI pipeline timeout",
        "url": "https://github.com/karolswdev/HoldSpeak/pull/608",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [], "reviewDecision": "",
        "statusCheckRollup": [{"conclusion": "FAILURE"}],
        "headRefOid": "ghi789", "updatedAt": "2026-09-01T11:00:00Z",
    },
])
_GH_RUN_LIST = json.dumps([
    {
        "conclusion": "success", "status": "completed",
        "name": "CI", "url": "https://github.com/karolswdev/HoldSpeak/actions/runs/1",
        "updatedAt": "2026-09-01T13:00:00Z", "headBranch": "main",
    },
])


def _make_gh_runner(fixture_path: Path) -> Any:
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)
        with open(fixture_path) as f:
            fixture = json.load(f)
        if "auth status" in cmd_str:
            entry = fixture.get("auth_status", {})
        elif "repo list" in cmd_str:
            entry = fixture.get("repo_list", {})
        elif "run list" in cmd_str:
            entry = fixture.get("run_list", {})
        elif "pr list" in cmd_str:
            entry = fixture.get("pr_list", {})
        else:
            entry = {"returncode": 1, "stderr": f"no fixture: {cmd_str}"}
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=entry.get("returncode", 0),
            stdout=entry.get("stdout", ""),
            stderr=entry.get("stderr", ""),
        )
    return runner


def _write_gh_fixture(path: Path, *, auth: dict[str, Any], **kw: Any) -> None:
    fixture: dict[str, Any] = {"auth_status": auth}
    fixture.update(kw)
    path.write_text(json.dumps(fixture, indent=2))


# ── Jira fixture runner ───────────────────────────────────────────

_JIRA_STATUS_CONNECTED = {
    "stdout": "Site: alpha.atlassian.net\nEmail: user@example.com\nAuth type: PAT\nStatus: Authenticated\n",
    "returncode": 0,
}
_JIRA_SWITCH_OK = {
    "stdout": "Switched to alpha.atlassian.net (user@example.com)\n",
    "returncode": 0,
}
_JIRA_PROJECT_LIST = json.dumps([
    {"key": "KAN", "name": "Kanban Board", "id": "10001", "projectTypeKey": "software", "style": "next-gen"},
    {"key": "WRONG", "name": "Wrong Board", "id": "10002", "projectTypeKey": "software", "style": "next-gen"},
])
_JIRA_SEARCH = json.dumps({
    "issues": [
        {"key": "KAN-1", "fields": {
            "summary": "Sprint planning", "issuetype": {"name": "Task"},
            "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate"}},
            "assignee": None, "priority": {"name": "Medium"}, "labels": [],
            "duedate": "2026-08-20", "resolution": None,
        }},
        {"key": "KAN-2", "fields": {
            "summary": "Review backlog", "issuetype": {"name": "Task"},
            "status": {"name": "To Do", "statusCategory": {"key": "new"}},
            "assignee": None, "priority": {"name": "High"}, "labels": [],
            "duedate": "2026-09-07", "resolution": None,
        }},
    ],
    "total": 2,
})
_JIRA_ISSUE_VIEW = json.dumps({
    "key": "KAN-1", "fields": {
        "summary": "Sprint planning", "issuetype": {"name": "Task"},
        "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate", "name": "In Progress"}},
        "assignee": None, "priority": {"name": "Medium"}, "labels": [],
        "duedate": "2026-08-20", "resolution": None,
    },
})


def _make_jira_runner() -> Any:
    statuses = {"alpha.atlassian.net|user@example.com": _JIRA_STATUS_CONNECTED}
    switches = {"alpha.atlassian.net|user@example.com": _JIRA_SWITCH_OK}
    state = {"current": "alpha.atlassian.net|user@example.com"}

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)
        if "auth switch" in cmd_str:
            si = cmd.index("--site") + 1 if "--site" in cmd else -1
            ei = cmd.index("--email") + 1 if "--email" in cmd else -1
            if si > 0 and ei > 0:
                key = f"{cmd[si]}|{cmd[ei]}"
                state["current"] = key
                entry = switches.get(key, {"returncode": 1, "stderr": "not found"})
            else:
                entry = {"returncode": 1, "stderr": "bad args"}
        elif "auth status" in cmd_str:
            entry = statuses.get(state["current"], {"returncode": 1, "stderr": "unauthorized"})
        elif "project list" in cmd_str:
            entry = {"stdout": _JIRA_PROJECT_LIST, "returncode": 0}
        elif "project view" in cmd_str:
            entry = {"stdout": json.dumps({"key": "KAN", "name": "Kanban Board", "projectTypeKey": "software", "style": "next-gen", "issueTypes": [{"id": "10001", "name": "Task", "subtask": False}]}), "returncode": 0}
        elif "workitem search" in cmd_str:
            entry = {"stdout": _JIRA_SEARCH, "returncode": 0}
        elif "workitem view" in cmd_str:
            entry = {"stdout": _JIRA_ISSUE_VIEW, "returncode": 0}
        else:
            entry = {"returncode": 1, "stderr": f"no fixture: {cmd_str}"}
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=entry.get("returncode", 0),
            stdout=entry.get("stdout", ""),
            stderr=entry.get("stderr", ""),
        )
    return runner
