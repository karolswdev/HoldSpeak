"""HS-168-04 -- Sources step glass rig.

COLD leg: TOOLS row with Connect verbs, zero provider suggestion cards,
connect round trip (session survives), answered-row shots.

CONNECTED leg: Sources with Connected chips, GitHub wizard (repo step
with known-scope, tested state with SUBJECT/BASE/QUERY + MATCHES),
Jira wizard (account skipped, project cards, Test enabled by pick).

Shots at 1440 AND 393 into assets/story-04-shots/.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
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
    / "pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "glass-test"


# ── Helpers ────────────────────────────────────────────────────────


def _seed_desk(page: Any) -> None:
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState
    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-168-001",
        started_at=datetime(2026, 9, 1, 10, 0),
        title="Sprint Review",
        capture_status="finalized",
    ))


def _open_interview(page: Any, url: str) -> None:
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


def _answer_both_questions(page: Any) -> None:
    textarea = page.locator(".setup-well-textarea")
    textarea.wait_for(timeout=10000)
    textarea.fill("Ship Q4 Payments Platform on time with zero incidents")
    page.get_by_test_id("setup-next").click()
    textarea2 = page.locator(".setup-well-textarea")
    textarea2.wait_for(timeout=10000)
    textarea2.fill("Missed sprint commitments, overdue action items, stale decisions")
    page.get_by_test_id("setup-next").click()
    page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=15000)


def _shot(page: Any, name: str, width: int, *, locator: Any = None) -> Path:
    """Settle animations, then take the shot."""
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    if locator:
        locator.screenshot(path=str(path))
    else:
        panel = page.locator(".desk-surface-window").filter(
            has=page.locator('[data-testid="setup-root"]')
        )
        if panel.count() > 0:
            panel.first.screenshot(path=str(path))
        else:
            setup = page.get_by_test_id("setup-root")
            if setup.count() > 0:
                setup.screenshot(path=str(path))
            else:
                page.screenshot(path=str(path), full_page=False)
    min_size = 2_000 if locator else 5_000
    assert path.stat().st_size > min_size, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _shots_differ(a: Path, b: Path) -> bool:
    ha = hashlib.sha256(a.read_bytes()).hexdigest()
    hb = hashlib.sha256(b.read_bytes()).hexdigest()
    return ha != hb


def _assert_luminance_parity(page: Any) -> None:
    """Assert TOOLS label and brief label have similar luminance (not dimmed)."""
    result = page.evaluate("""() => {
        function lum(el) {
            if (!el) return -1;
            const cs = getComputedStyle(el);
            const m = cs.color.match(/\\d+/g);
            if (!m || m.length < 3) return -1;
            return 0.299 * +m[0] + 0.587 * +m[1] + 0.114 * +m[2];
        }
        const tools = document.querySelector('[data-testid="setup-tools-row"] h3');
        const brief = document.querySelector('[data-testid="setup-brief"] h3');
        return { tools: lum(tools), brief: lum(brief) };
    }""")
    tl = result.get("tools", -1)
    bl = result.get("brief", -1)
    if tl > 0 and bl > 0:
        ratio = min(tl, bl) / max(tl, bl)
        assert ratio > 0.85, (
            f"TOOLS label luminance ({tl:.0f}) vs brief label ({bl:.0f}) "
            f"ratio {ratio:.2f} < 0.85 -- one column is dimmed"
        )


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
])
_GH_PR_VALIDATE_OK = json.dumps([{"number": 1}])
_GH_PR_SNAPSHOT = json.dumps([
    {
        "number": 412, "title": "Fix steward observation loop",
        "url": "https://github.com/karolswdev/HoldSpeak/pull/412",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [], "reviewDecision": "",
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "headRefOid": "abc123", "updatedAt": "2026-09-01T13:26:00Z",
    },
    {
        "number": 410, "title": "Add surface library ScrollHint",
        "url": "https://github.com/karolswdev/HoldSpeak/pull/410",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [], "reviewDecision": "",
        "statusCheckRollup": [{"conclusion": "SUCCESS"}],
        "headRefOid": "def456", "updatedAt": "2026-09-01T12:30:00Z",
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
        elif "pr list" in cmd_str and "-R" in cmd_str and "--limit" in cmd_str and "1" in cmd_str:
            entry = fixture.get("pr_validate", {})
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
])
_JIRA_PROJECT_VIEW = json.dumps({
    "key": "KAN", "name": "Kanban Board",
    "projectTypeKey": "software", "style": "next-gen",
    "issueTypes": [
        {"id": "10001", "name": "Epic", "subtask": False},
        {"id": "10003", "name": "Task", "subtask": False},
    ],
})
_JIRA_SEARCH = json.dumps({
    "issues": [
        {"key": "KAN-1", "fields": {"summary": "Sprint planning", "issuetype": {"name": "Task"}, "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate"}}, "assignee": None, "priority": {"name": "Medium"}, "labels": []}},
    ],
    "total": 1,
})
_JIRA_ISSUE_VIEW = json.dumps({
    "key": "KAN-1", "fields": {
        "summary": "Sprint planning", "issuetype": {"name": "Task"},
        "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate", "name": "In Progress"}},
        "assignee": None, "priority": {"name": "Medium"}, "labels": [],
        "duedate": None, "resolution": None,
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
            entry = {"stdout": _JIRA_PROJECT_VIEW, "returncode": 0}
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


@pytest.mark.skip(reason="HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig")
@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_sources_cold(tmp_path, monkeypatch, width):
    """COLD: TOOLS with Connect verbs, zero provider cards, connect
    round trip preserves session, answered-row shot."""
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
            _seed_desk(page)
            _open_interview(page, url)
            _answer_both_questions(page)

            # TOOLS row visible
            tools = page.get_by_test_id("setup-tools-row")
            tools.wait_for(timeout=10000)
            gh_tool = page.get_by_test_id("setup-tool-github")
            gh_tool.wait_for(timeout=5000)
            assert "SIGN IN" in gh_tool.inner_text().upper() or \
                   "CONNECT" in gh_tool.inner_text().upper()

            # Luminance parity (not dimmed)
            _assert_luminance_parity(page)

            # -- SHOT: sources-cold --
            _shot(page, "sources-cold", width)

            # Zero GH cards
            card_els = page.get_by_test_id("setup-suggestion-cards").locator('[role="option"]')
            for i in range(card_els.count()):
                assert card_els.nth(i).locator(
                    ".surface-provenance-source", has_text="gh"
                ).count() == 0, f"Card {i} has GH provenance cold"

            # -- Answered-row shot (bounce 7: lead + primary on one line) --
            answered = page.locator('[data-testid^="setup-answer-"]').first
            answered.wait_for(timeout=5000)
            _settle(page)
            _shot(page, "answered-row", width, locator=answered)

            # -- Connect round trip --
            page.get_by_test_id("setup-connect-github").click()
            page.wait_for_timeout(2000)
            session_id = page.evaluate(
                "() => sessionStorage.getItem('hs.project-setup.session-id')")
            assert session_id, "Session must survive connect round trip"

            _shot(page, "connect-roundtrip", width)

            session_data = _api(page, "GET",
                                f"/api/project-setups/{session_id}", token=TOKEN)
            assert session_data.get("stage") == "proposals"
            assert "outcome" in session_data.get("answers", {})
            assert "signals" in session_data.get("answers", {})

            # Return to setup
            page.evaluate("""() => {
                sessionStorage.setItem("hs.desk.staged-surface-open",
                    JSON.stringify({key: "project-setup"}));
            }""")
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("setup-tools-row").wait_for(timeout=10000)
            _shot(page, "sources-after-roundtrip", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.skip(reason="HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig")
@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_sources_connected(tmp_path, monkeypatch, width):
    """CONNECTED: GitHub + Jira. GitHub wizard with known-scope, tested
    state. Jira wizard with account skipped, project pick enables Test."""
    _ensure_build()
    gh_fixture = tmp_path / "gh_fixture.json"
    _write_gh_fixture(
        gh_fixture, auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT, "returncode": 0},
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
            _seed_desk(page)

            # Prime Jira connection: add + recheck to connected
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

            _open_interview(page, url)
            _answer_both_questions(page)

            # TOOLS Connected
            tools = page.get_by_test_id("setup-tools-row")
            tools.wait_for(timeout=10000)
            gh_tool = page.get_by_test_id("setup-tool-github")
            gh_tool.wait_for(timeout=5000)
            assert "CONNECTED" in gh_tool.inner_text().upper()

            _assert_luminance_parity(page)
            _shot(page, "sources-connected", width)

            # ── GitHub wizard ──
            cards = page.get_by_test_id("setup-suggestion-cards")
            card_els = cards.locator('[role="option"]')
            card_els.first.wait_for(timeout=10000)

            gh_idx = None
            gh_card_id = None
            for i in range(card_els.count()):
                card = card_els.nth(i)
                if card.locator(
                    ".surface-provenance-source", has_text="gh"
                ).count() > 0:
                    gh_idx = i
                    gh_card_id = card.get_attribute("data-testid")
                    break
            assert gh_idx is not None, "Must find a GH card"
            assert gh_card_id is not None

            # HS-168-05: enter via the "Set up" verb button (primary path)
            prop_id = gh_card_id.replace("setup-card-", "")
            setup_btn = page.get_by_test_id(f"setup-card-setup-{prop_id}")
            setup_btn.wait_for(timeout=5000)
            setup_btn.click()
            wizard = page.get_by_test_id("provider-wizard-flow")
            wizard.wait_for(timeout=10000)

            # HS-168-05: wizard owns the body -- TOOLS, cards unmounted
            assert page.get_by_test_id("setup-tools-row").count() == 0, \
                "TOOLS row must unmount while wizard is open"
            assert page.get_by_test_id("setup-suggestion-cards").count() == 0, \
                "Suggestion cards must unmount while wizard is open"

            # Wizard flow top within 120px of setup-root top
            wiz_box = wizard.bounding_box()
            root_box = page.get_by_test_id("setup-root").bounding_box()
            assert wiz_box is not None and root_box is not None
            assert abs(wiz_box["y"] - root_box["y"]) < 120, (
                f"Wizard top ({wiz_box['y']:.0f}) must be within 120px of "
                f"setup-root top ({root_box['y']:.0f})"
            )

            _shot(page, "github-wizard-owns-body", width)

            # Heading has the Watch name
            heading = page.get_by_test_id("wizard-heading-name")
            heading.wait_for(timeout=5000)
            assert heading.inner_text().strip(), "Wizard heading must show Watch name"

            # Test this Watch DISABLED before scope
            test_btn = page.get_by_test_id("provider-test-btn")
            test_btn.wait_for(timeout=5000)
            assert test_btn.is_disabled(), "Test this Watch must be disabled before scope"

            # Discovery
            disc = page.get_by_test_id("provider-discovery-list")
            disc.wait_for(timeout=10000)
            disc_items = disc.locator('[role="option"]')
            disc_items.first.wait_for(timeout=10000)

            # SHOT before repo pick (Test disabled)
            _shot(page, "github-wizard-repo", width)

            # Pick a repo
            disc_items.first.click()
            page.wait_for_timeout(500)
            _settle(page)

            # Test this Watch now enabled
            assert not test_btn.is_disabled(), "Test enabled after scope"
            test_btn.click()

            # Wait for passed
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="provider-test-display"][data-test-state="passed"]'
                    );
                    return el !== null;
                }""",
                timeout=15000,
            )
            td = page.get_by_test_id("provider-test-display")
            td_text = td.inner_text()
            assert "SUBJECT" in td_text, "SUBJECT expected"
            assert "MATCHES" in td_text, "MATCHES expected"

            _shot(page, "github-wizard-test", width)

            # Use this Watch
            page.get_by_test_id("provider-wizard-done").click()
            page.wait_for_timeout(500)

            # ── Second GH card for known-scope (body click = alternate path) ──
            cards2 = page.get_by_test_id("setup-suggestion-cards")
            cards2.wait_for(timeout=10000)
            c2 = cards2.locator('[role="option"]')
            c2.first.wait_for(timeout=10000)

            gh2_idx = None
            gh2_card_id = None
            for i in range(c2.count()):
                card = c2.nth(i)
                if card.locator(".surface-provenance-source", has_text="gh").count() > 0:
                    if card.get_attribute("aria-selected") != "true":
                        gh2_idx = i
                        gh2_card_id = card.get_attribute("data-testid")
                        break
            if gh2_idx is not None:
                # HS-168-05: body click also enters wizard for connected provider
                c2.nth(gh2_idx).click()
                page.get_by_test_id("provider-wizard-flow").wait_for(timeout=10000)
                _settle(page)

                known = page.get_by_test_id("known-scope-card")
                if known.count() > 0:
                    known.scroll_into_view_if_needed()
                    _settle(page)
                    known_text = known.inner_text()
                    assert "chosen for" in known_text.lower(), (
                        f"Known-scope card must say 'chosen for'; got: {known_text}"
                    )
                _shot(page, "github-wizard-known-scope", width)

                page.get_by_test_id("provider-wizard-back").click()
                page.wait_for_timeout(500)

            # ── Jira wizard ──
            cards3 = page.get_by_test_id("setup-suggestion-cards")
            cards3.wait_for(timeout=10000)
            c3 = cards3.locator('[role="option"]')
            c3.first.wait_for(timeout=10000)

            jira_idx = None
            jira_card_id = None
            for i in range(c3.count()):
                card = c3.nth(i)
                if card.locator(
                    ".surface-provenance-source", has_text="acli"
                ).count() > 0:
                    jira_idx = i
                    jira_card_id = card.get_attribute("data-testid")
                    break
            assert jira_idx is not None, (
                "Must find a Jira card (acli connected + fixture yields candidates)"
            )

            # HS-168-05: enter via the "Set up" verb button
            jira_prop_id = jira_card_id.replace("setup-card-", "")
            jira_setup_btn = page.get_by_test_id(f"setup-card-setup-{jira_prop_id}")
            jira_setup_btn.wait_for(timeout=5000)
            jira_setup_btn.click()
            jira = page.get_by_test_id("jira-wizard-flow")
            jira.wait_for(timeout=10000)

            # 1 connection -> accounts skipped -> scope
            scope = page.get_by_test_id("jira-scope-step")
            scope.wait_for(timeout=10000)

            # Test disabled before project pick
            jira_test = page.get_by_test_id("jira-test-btn")
            jira_test.wait_for(timeout=5000)
            assert jira_test.is_disabled(), "Test disabled before project"

            _shot(page, "jira-wizard-project", width)

            # Wait for project cards to load (discover is async)
            page.wait_for_timeout(2000)
            _settle(page)

            # Wait for project discovery to complete
            page.wait_for_timeout(2000)
            _settle(page)
            # Pick KAN project
            kan = scope.locator("text=Kanban Board").first
            kan.wait_for(timeout=10000)
            kan.click()
            page.wait_for_timeout(1000)
            _settle(page)

            assert not jira_test.is_disabled(), "Test enabled after project"
            _shot(page, "jira-wizard-scoped", width)

            page.get_by_test_id("jira-wizard-back").click()
            page.wait_for_timeout(500)

            # Footer step count
            step = page.get_by_test_id("setup-step-count")
            if step.count() > 0:
                assert "3" in step.inner_text() and "4" in step.inner_text()

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
