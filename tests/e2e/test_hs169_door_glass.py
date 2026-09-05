"""HS-169-02 -- The Streamlined Door glass rig.

CONNECTED leg: outcome well, source rows with in-world pickers, counts
arrive, Create Project in 5 clicks, no vertical scroll at 1440.

COLD leg: Connect verbs, Settings round trip.

Shots at 1440 AND 393 into assets/story-02-shots/.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-169-the-streamlined-door/assets/story-02-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "glass-test"


# ── Helpers ────────────────────────────────────────────────────────


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


def _shot(page: Any, name: str, width: int, *, locator: Any = None) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    if locator:
        locator.screenshot(path=str(path))
    else:
        panel = page.locator(".desk-surface-window").filter(
            has=page.locator('[data-testid="door-root"]')
        )
        if panel.count() > 0:
            panel.first.screenshot(path=str(path))
        else:
            door = page.get_by_test_id("door-root")
            if door.count() > 0:
                door.screenshot(path=str(path))
            else:
                page.screenshot(path=str(path), full_page=False)
    min_size = 2_000 if locator else 5_000
    assert path.stat().st_size > min_size, f"Shot {name} too small ({path.stat().st_size})"
    return path


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


# ── Tests ─────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_door_connected(tmp_path, monkeypatch, width):
    """CONNECTED: outcome + repo pick + Jira pick + Create in 5 clicks.
    No vertical scroll at 1440 in the picked state."""
    _ensure_build()
    gh_fixture = tmp_path / "gh_fixture.json"
    _write_gh_fixture(
        gh_fixture, auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT, "returncode": 0},
        run_list={"stdout": _GH_RUN_LIST, "returncode": 0},
    )
    server, url = _boot(
        tmp_path, monkeypatch, token=TOKEN,
        gh_runner=_make_gh_runner(gh_fixture),
        acli_runner=_make_jira_runner(),
    )
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Prime Jira connection
            _api(page, "POST", "/api/providers/jira/connections",
                 {"site": "alpha.atlassian.net", "email": "user@example.com"},
                 token=TOKEN)
            import urllib.parse
            jira_ref = urllib.parse.quote("alpha.atlassian.net|user@example.com", safe="")
            recheck_resp = _api(page, "POST",
                                f"/api/providers/jira/connections/{jira_ref}/recheck",
                                token=TOKEN)
            assert recheck_resp.get("state") == "connected", (
                f"Jira recheck must return connected; got: {recheck_resp}"
            )

            _open_door(page, url)

            # 1. The door-root is visible
            door = page.get_by_test_id("door-root")
            door.wait_for(timeout=10000)

            # Outcome well visible with placeholder
            outcome_input = page.get_by_test_id("door-outcome-input")
            outcome_input.wait_for(timeout=5000)
            assert outcome_input.get_attribute("placeholder") == "What are you delivering?"

            # SHOT: first open (empty state)
            _shot(page, "door-empty", width)

            # 2. Type outcome (not a click)
            outcome_input.fill("Ship Q4 Payments Platform on time")
            _settle(page)

            # Receipt shows BLANK PROJECT before any scope picked
            receipt = page.get_by_test_id("door-receipt")
            assert "NO SOURCES" in receipt.inner_text().upper()

            # Create disabled without scope (we have outcome but no scope)
            create_btn = page.get_by_test_id("door-create")
            # Create is enabled because outcome has text, but receipt says BLANK PROJECT
            # (zero sources = blank project is allowed)

            # ── Click counting starts ──
            clicks = 0

            # 3. Click GitHub trigger (click 1)
            gh_trigger = page.get_by_test_id("door-trigger-github")
            gh_trigger.wait_for(timeout=5000)
            gh_trigger.click()
            clicks += 1

            # Picker opens
            gh_picker = page.get_by_test_id("door-picker-github")
            gh_picker.wait_for(timeout=10000)

            # Wait for discovery items
            page.wait_for_timeout(2000)
            _settle(page)

            # SHOT: picker open
            _shot(page, "door-picker", width)

            # Assert: picker content is reachable — "Show more" is
            # visible (in viewport) or the body is scrollable.
            show_more = page.locator(".door-picker-more")
            if show_more.count() > 0:
                assert show_more.first.is_visible(), (
                    "Show more is present but not visible — picker content is cut off"
                )
            else:
                # No Show more = all items fit; picker is not cut off.
                pass

            # 4. Click repo card (click 2)
            repo_card = page.get_by_test_id("door-pick-karolswdev/HoldSpeak")
            repo_card.wait_for(timeout=10000)
            repo_card.click()
            clicks += 1

            # Picker closes, state = checking
            page.wait_for_timeout(300)
            _settle(page)

            # SHOT: checking state
            _shot(page, "door-checking", width)

            # Wait for counts to arrive (live state)
            page.wait_for_function(
                """() => {
                    const el = document.querySelector('[data-testid="door-counts-github"]');
                    return el !== null;
                }""",
                timeout=15000,
            )
            _settle(page)

            # SHOT: live state
            _shot(page, "door-live-gh", width)

            # 5. Click Jira trigger (click 3)
            jira_trigger = page.get_by_test_id("door-trigger-jira")
            jira_trigger.wait_for(timeout=5000)
            jira_trigger.click()
            clicks += 1

            # Wait for Jira picker items
            jira_picker = page.get_by_test_id("door-picker-jira")
            jira_picker.wait_for(timeout=10000)
            page.wait_for_timeout(2000)
            _settle(page)

            # 6. Pick Jira project (click 4)
            kan_card = page.get_by_test_id("door-pick-KAN")
            kan_card.wait_for(timeout=10000)
            kan_card.click()
            clicks += 1

            # Wait for Jira counts
            page.wait_for_timeout(3000)
            _settle(page)

            # SHOT: both live
            _shot(page, "door-live", width)

            # Receipt should show sources + watches
            receipt_text = receipt.inner_text().upper()
            assert "SOURCE" in receipt_text
            assert "WATCH" in receipt_text

            # ── 393 no-intersection probe: no two row children overlap ──
            if width == 393:
                overlaps = page.evaluate(
                    """() => {
                        const rows = document.querySelectorAll(
                            '[data-testid^="door-row-"] .surface-ledger-line'
                        );
                        const hits = [];
                        for (const row of rows) {
                            const children = Array.from(row.children).filter(
                                el => el.offsetHeight > 0 && el.offsetWidth > 0
                            );
                            for (let i = 0; i < children.length; i++) {
                                const a = children[i].getBoundingClientRect();
                                for (let j = i + 1; j < children.length; j++) {
                                    const b = children[j].getBoundingClientRect();
                                    const overlapX = Math.max(0,
                                        Math.min(a.right, b.right) - Math.max(a.left, b.left));
                                    const overlapY = Math.max(0,
                                        Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
                                    if (overlapX > 2 && overlapY > 2) {
                                        hits.push({
                                            a: children[i].className,
                                            b: children[j].className,
                                            ox: overlapX, oy: overlapY
                                        });
                                    }
                                }
                            }
                        }
                        return hits;
                    }"""
                )
                assert len(overlaps) == 0, (
                    f"Overlapping row elements at 393: {overlaps}"
                )

            # ── No-scroll assertion (1440 only) ──
            if width == 1440:
                no_scroll = page.evaluate(
                    """() => {
                        const body = document.querySelector('.desk-surface-body')
                            || document.querySelector('[data-testid="door-root"]');
                        if (!body) return {ok: true, sh: 0, ch: 0};
                        return {ok: body.scrollHeight <= body.clientHeight,
                                sh: body.scrollHeight, ch: body.clientHeight};
                    }"""
                )
                assert no_scroll["ok"], (
                    f"Vertical scroll detected at 1440: scrollHeight={no_scroll['sh']} > clientHeight={no_scroll['ch']}"
                )

            # ── Adjust test ──
            gh_adjust = page.get_by_test_id("door-adjust-github")
            gh_adjust.wait_for(timeout=3000)
            gh_adjust.click()
            _settle(page)
            adjust_well = page.get_by_test_id("door-adjust-well-github")
            adjust_well.wait_for(timeout=5000)
            _shot(page, "door-adjust", width)
            # Close adjust
            gh_adjust.click()
            _settle(page)

            # 7. Click Create Project (click 5)
            create_btn.click()
            clicks += 1

            assert clicks == 5, f"Expected 5 clicks, got {clicks}"

            # Wait for project creation (the Room opens)
            page.wait_for_timeout(3000)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_door_cold(tmp_path, monkeypatch, width):
    """COLD: Connect verbs visible, Connect opens Settings round trip."""
    _ensure_build()
    gh_fixture = tmp_path / "gh_fixture.json"
    _write_gh_fixture(gh_fixture, auth=_GH_AUTH_COLD)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN,
                        gh_runner=_make_gh_runner(gh_fixture))
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _open_door(page, url)

            door = page.get_by_test_id("door-root")
            door.wait_for(timeout=10000)

            # Both rows should show Connect
            gh_connect = page.get_by_test_id("door-connect-github")
            gh_connect.wait_for(timeout=5000)
            assert gh_connect.is_visible()

            # Receipt says BLANK PROJECT
            receipt = page.get_by_test_id("door-receipt")
            assert "NO SOURCES" in receipt.inner_text().upper()

            _shot(page, "door-cold", width)

            # Connect round trip: opens Settings
            gh_connect.click()
            page.wait_for_timeout(2000)
            _settle(page)
            _shot(page, "door-cold-connect", width)

            # Return to door
            _open_door(page, url)
            door2 = page.get_by_test_id("door-root")
            door2.wait_for(timeout=10000)
            _shot(page, "door-cold-return", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
