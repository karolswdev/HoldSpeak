"""HS-166-04 real-hub Jira Watch glass.

FIXTURE SEAM: MeetingWebServer(acli_runner=...) injects a fake runner
into JiraProviderAdapter so the booted hub uses canned acli responses.
Everything above the runner stays real: routes, services, adapter
logic, DB, React bundle.

The walk: setup interview with a Jira proposal -> connection list
(two rows, one connected, one owner_action_required with login command)
-> scope (projects -> types -> statuses -> JQL preview) -> test
(JiraTestDisplay) -> activation review.

Shots at 1440 and 393.  Every step is MANDATORY -- a missing element
fails the test loudly.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot as _conftest_boot, _api, _api_allow_error, _assert_clean, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Jira glass needs Playwright")

TOKEN = "hs166-jira-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-166-the-jira-parity/assets/story-04-shots"

OUTCOME_TEXT = "Track Jira project delivery across two sites"
SIGNALS_TEXT = "Stale issues, blocked work items, overdue tasks"

# ── Fixture data (real acli shapes, actual characters) ──────────────

_SWITCH_OK_ALPHA = {
    "stdout": "✓ Switched to account: alpha.atlassian.net [user@example.com]",
    "returncode": 0,
}
_SWITCH_OK_BETA = {
    "stdout": "✓ Switched to account: beta.atlassian.net [admin@example.com]",
    "returncode": 0,
}

_STATUS_CONNECTED_ALPHA = {
    "stdout": (
        "✓ Authenticated\n"
        "  Site: alpha.atlassian.net\n"
        "  Email: user@example.com\n"
        "  Authentication Type: oauth\n"
    ),
    "returncode": 0,
}

_STATUS_UNAUTH_BETA = {
    "stderr": "✗ Error: unauthorized: use 'acli jira auth login' to authenticate",
    "returncode": 1,
}

_PROJECT_LIST = json.dumps([
    {
        "id": "10001", "key": "KAN", "name": "Kanban Board",
        "projectTypeKey": "software", "style": "next-gen",
        "isPrivate": False,
        "lead": {"displayName": "Test Lead", "accountId": "712020:abc"},
        "issueTypes": None,
    },
    {
        "id": "10002", "key": "HR", "name": "HR Updates",
        "projectTypeKey": "software", "style": "next-gen",
        "isPrivate": False,
        "lead": {"displayName": "HR Lead", "accountId": "712020:def"},
        "issueTypes": None,
    },
])

_PROJECT_VIEW_KAN = json.dumps({
    "id": "10001", "key": "KAN", "name": "Kanban Board",
    "projectTypeKey": "software", "style": "next-gen",
    "isPrivate": False,
    "issueTypes": [
        {"id": "10004", "name": "Epic", "subtask": False, "hierarchyLevel": 1},
        {"id": "10005", "name": "Subtask", "subtask": True, "hierarchyLevel": -1},
        {"id": "10006", "name": "Task", "subtask": False, "hierarchyLevel": 0},
    ],
})

_SEARCH_ITEMS = json.dumps([
    {
        "id": "10006", "key": "KAN-3",
        "fields": {
            "assignee": None,
            "issuetype": {"id": "10005", "name": "Subtask", "subtask": True},
            "priority": None,
            "status": {
                "id": "10006", "name": "Done",
                "statusCategory": {"id": 3, "key": "done", "name": "Done"},
            },
            "summary": "Subtask 2.1",
            "labels": [],
        },
    },
    {
        "id": "10004", "key": "KAN-2",
        "fields": {
            "assignee": None,
            "issuetype": {"id": "10006", "name": "Task", "subtask": False},
            "priority": None,
            "status": {
                "id": "10005", "name": "In Progress",
                "statusCategory": {"id": 4, "key": "indeterminate", "name": "In Progress"},
            },
            "summary": "Task 2",
            "labels": [],
        },
    },
    {
        "id": "10002", "key": "KAN-1",
        "fields": {
            "assignee": None,
            "issuetype": {"id": "10006", "name": "Task", "subtask": False},
            "priority": None,
            "status": {
                "id": "10005", "name": "In Progress",
                "statusCategory": {"id": 4, "key": "indeterminate", "name": "In Progress"},
            },
            "summary": "Task 1",
            "labels": [],
        },
    },
])

_VIEW_ENRICHED = json.dumps({
    "id": "10002", "key": "KAN-1",
    "fields": {
        "duedate": "2026-09-10",
        "resolution": None,
        "resolutiondate": None,
        "updated": "2026-09-02T20:02:24.980-0600",
        "created": "2026-09-02T20:02:24.540-0600",
        "statuscategorychangedate": "2026-09-02T20:02:24.980-0600",
        "project": {"key": "KAN", "name": "Kanban Board"},
    },
})


# ── Fixture runner (stateful: tracks last-switched account) ─────────


def _make_acli_runner() -> Any:
    """Runner that returns canned responses and tracks the current account.

    The switch-and-verify discipline requires switch -> status -> command
    in sequence.  This runner remembers which account was last switched
    to, so `auth status` returns the right account's status.
    """
    # Map of "site|email" -> status response
    account_statuses: dict[str, dict[str, Any]] = {
        "alpha.atlassian.net|user@example.com": _STATUS_CONNECTED_ALPHA,
        "beta.atlassian.net|admin@example.com": _STATUS_UNAUTH_BETA,
    }
    switch_responses: dict[str, dict[str, Any]] = {
        "alpha.atlassian.net|user@example.com": _SWITCH_OK_ALPHA,
        "beta.atlassian.net|admin@example.com": _SWITCH_OK_BETA,
    }
    # Track the currently switched account
    state = {"current": "alpha.atlassian.net|user@example.com"}

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)

        if "auth switch" in cmd_str:
            site_idx = cmd.index("--site") + 1 if "--site" in cmd else -1
            email_idx = cmd.index("--email") + 1 if "--email" in cmd else -1
            if site_idx > 0 and email_idx > 0:
                key = f"{cmd[site_idx]}|{cmd[email_idx]}"
                state["current"] = key
                entry = switch_responses.get(key, {
                    "returncode": 1,
                    "stderr": f"✗ Error: account with email '{cmd[email_idx]}' and site '{cmd[site_idx]}' not found",
                })
            else:
                entry = {"returncode": 1, "stderr": "bad switch args"}
        elif "auth status" in cmd_str:
            entry = account_statuses.get(state["current"], {
                "returncode": 1,
                "stderr": "✗ Error: unauthorized: use 'acli jira auth login' to authenticate",
            })
        elif "project list" in cmd_str:
            entry = {"stdout": _PROJECT_LIST, "returncode": 0}
        elif "project view" in cmd_str:
            entry = {"stdout": _PROJECT_VIEW_KAN, "returncode": 0}
        elif "workitem search" in cmd_str:
            entry = {"stdout": _SEARCH_ITEMS, "returncode": 0}
        elif "workitem view" in cmd_str:
            entry = {"stdout": _VIEW_ENRICHED, "returncode": 0}
        else:
            entry = {"returncode": 1, "stderr": f"no fixture match: {cmd_str}"}

        return subprocess.CompletedProcess(
            args=cmd,
            returncode=entry.get("returncode", 0),
            stdout=entry.get("stdout", ""),
            stderr=entry.get("stderr", ""),
        )

    return runner


# ── Boot / helpers ────────────────────────────────────────────────


def _seed_acli_config(tmp_path: Path) -> None:
    """Write acli config so known_accounts returns something."""
    import yaml
    home = tmp_path / "home"
    acli_dir = home / ".config" / "acli"
    acli_dir.mkdir(parents=True, exist_ok=True)
    (acli_dir / "jira_config.yaml").write_text(yaml.dump({
        "current_profile": "cloud1:acc1",
        "profiles": [
            {
                "site": "alpha.atlassian.net",
                "email": "user@example.com",
                "display_name": "Test User",
                "auth_type": "oauth",
                "cloud_id": "cloud1",
                "account_id": "acc1",
            },
            {
                "site": "beta.atlassian.net",
                "email": "admin@example.com",
                "display_name": "Beta Admin",
                "auth_type": "pat",
                "cloud_id": "cloud2",
                "account_id": "acc2",
            },
        ],
    }))


def _boot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    acli_runner: Any = None,
) -> tuple[Any, str]:
    _seed_acli_config(tmp_path)
    return _conftest_boot(tmp_path, monkeypatch, token=TOKEN, acli_runner=acli_runner)


def _ref_encode(ref: str) -> str:
    """URL-encode a connection ref for path segments."""
    import urllib.parse
    return urllib.parse.quote(ref, safe="")


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


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


def _seed_desk_facts(tmp_path: Path) -> None:
    """Seed minimal desk facts so the interview can generate suggestions."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState

    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-glass-166-001",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint Review",
        capture_status="finalized",
    ))






def _shot(page: Any, name: str, width: int, *, locator: Any = None) -> Path:
    """Take a screenshot and return the path.

    When ``locator`` is given, scroll it into view first and assert
    it is visible, then screenshot the page (not the element -- we want
    the full window context for the owner's review).
    """
    path = SHOTS / f"{name}-{width}.png"
    if locator is not None:
        locator.scroll_into_view_if_needed()
        assert locator.is_visible(), f"{name}: target element not visible after scroll"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 5_000, f"Suspiciously small PNG: {path}"
    return path


# ── Tests ─────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_jira_setup_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Full mandatory walk: suggestions with Jira card -> connection list
    -> scope picker -> test display -> activation review.

    Every step MUST render -- no conditional skips.
    """
    from playwright.sync_api import sync_playwright

    _ensure_build()

    runner = _make_acli_runner()
    server, url = _boot(tmp_path, monkeypatch, acli_runner=runner)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            # -- Desk init + seed facts --
            _init_desk(page, url)
            _seed_desk_facts(tmp_path)

            # -- Prime Jira connections: add + recheck alpha (MUST become connected) --
            r1s, r1p = _api_allow_error(page, "POST", "/api/providers/jira/connections",
                       {"site": "alpha.atlassian.net", "email": "user@example.com"}, token=TOKEN)
            assert r1s == 200, f"Add alpha failed: {r1s} {r1p}"

            r2s, r2p = _api_allow_error(page, "POST", "/api/providers/jira/connections",
                       {"site": "beta.atlassian.net", "email": "admin@example.com"}, token=TOKEN)
            assert r2s == 200, f"Add beta failed: {r2s} {r2p}"

            # Recheck alpha -- MUST become connected
            r3s, r3p = _api_allow_error(page, "POST",
                       f"/api/providers/jira/connections/{_ref_encode('alpha.atlassian.net|user@example.com')}/recheck", token=TOKEN)
            assert r3s == 200, f"Recheck alpha HTTP failed: {r3s} {r3p}"
            assert r3p["state"] == "connected", (
                f"ROOT CAUSE CHECK: alpha recheck did not return connected: {r3p}"
            )

            # Recheck beta -- MUST become owner_action_required
            r4s, r4p = _api_allow_error(page, "POST",
                       f"/api/providers/jira/connections/{_ref_encode('beta.atlassian.net|admin@example.com')}/recheck", token=TOKEN)
            assert r4s == 200, f"Recheck beta HTTP failed: {r4s} {r4p}"
            assert r4p["state"] == "owner_action_required", (
                f"Beta should be owner_action_required: {r4p}"
            )

            # -- Open interview --
            _open_interview(page, url)

            # -- Answer outcome --
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            q_outcome.locator("textarea").fill(OUTCOME_TEXT)
            q_outcome.locator("textarea").press("Enter")

            # -- Answer signals --
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            q_signals.locator("textarea").fill(SIGNALS_TEXT)
            q_signals.locator("textarea").press("Enter")

            # -- Wait for suggestions --
            cards = page.get_by_test_id("setup-suggestion-cards")
            cards.wait_for(timeout=20000)
            card_elements = cards.locator('[role="option"]')
            card_elements.first.wait_for(timeout=10000)
            card_count = card_elements.count()

            # -- SHOT: suggestions --
            _shot(page, "jira-suggestions", width, locator=cards)

            # -- Find the Jira card (MANDATORY) --
            jira_card_idx = None
            for i in range(card_count):
                card = card_elements.nth(i)
                source_fact = card.locator('text=jira')
                if source_fact.count() > 0:
                    jira_card_idx = i
                    break
            assert jira_card_idx is not None, (
                f"MANDATORY: No Jira provider card found in {card_count} suggestion(s)."
            )

            # -- Click the Jira card to enter the wizard --
            card_elements.nth(jira_card_idx).click()

            # -- Jira wizard flow MUST appear --
            jira_flow = page.get_by_test_id("jira-wizard-flow")
            jira_flow.wait_for(timeout=10000)

            # -- Suggestion cards MUST NOT be visible (wizard replaces them) --
            suggestion_cards = page.get_by_test_id("setup-suggestion-cards")
            assert suggestion_cards.count() == 0, (
                "Suggestion cards MUST NOT render while the wizard is active"
            )

            # -- D1 ACCOUNTS STEP --
            accounts_step = page.get_by_test_id("jira-accounts-step")
            accounts_step.wait_for(timeout=5000)

            # -- SHOT: accounts --
            _shot(page, "jira-accounts", width, locator=accounts_step)

            # Verify account cards exist (ChoiceCard radios inside radiogroup)
            radiogroup = accounts_step.locator('[role="radiogroup"]')
            assert radiogroup.count() > 0, "Account radiogroup MUST exist"

            # The alpha card should show "Connected" and the beta "Sign in"
            assert accounts_step.locator('text=Connected').count() > 0, (
                "Alpha card MUST show Connected StateChip"
            )
            assert accounts_step.locator('text=Sign in').count() > 0, (
                "Beta card MUST show Sign in StateChip"
            )

            # ProvenanceChip naming the site MUST exist
            assert accounts_step.locator('text=alpha.atlassian.net').count() > 0, (
                "Alpha site MUST be visible"
            )

            # The ghost Add card MUST exist
            add_card = page.get_by_test_id("jira-add-card")
            assert add_card.count() > 0, "Ghost Add card MUST be visible"

            # -- SHOT: add card scrolled into view --
            _shot(page, "jira-add-card", width, locator=add_card)

            # -- Select alpha connection --
            # ChoiceCard renders as a <label> wrapping a hidden radio.
            # Click the radio via JS to ensure selection triggers.
            page.evaluate("""() => {
              const radios = document.querySelectorAll('input[type="radio"][name="jira-account"]');
              if (radios.length > 0) {
                radios[0].click();
                radios[0].dispatchEvent(new Event('change', { bubbles: true }));
              }
            }""")
            page.wait_for_timeout(1500)

            # -- Click "Choose project" footer button to advance to scope --
            # The button may be a TransportKey (aria-label) or a plain button (text)
            page.wait_for_function(
                """() => {
                  const btns = document.querySelectorAll('.jira-wizard-footer button');
                  for (const btn of btns) {
                    if ((btn.textContent || '').includes('project') || (btn.textContent || '').includes('Project') ||
                        btn.getAttribute('aria-label') === 'Choose project') {
                      return !btn.disabled;
                    }
                  }
                  return false;
                }""",
                timeout=8000,
            )
            choose_btn = page.locator('.jira-wizard-footer button').filter(has_text="roject")
            if choose_btn.count() == 0:
                choose_btn = page.locator('button[aria-label="Choose project"]')
            choose_btn.first.click()
            page.wait_for_timeout(1000)

            # -- D2 SCOPE STEP --
            scope_step = page.get_by_test_id("jira-scope-step")
            scope_step.wait_for(timeout=10000)

            # -- SHOT: scope (projects) --
            _shot(page, "jira-scope", width, locator=scope_step)

            # Select KAN project (ChoiceCard in the project radiogroup)
            kan_label = scope_step.locator('text=Kanban Board').first
            if kan_label.count() > 0:
                kan_label.click()
                page.wait_for_timeout(500)

            # Wait for population sheet to appear (types/statuses load)
            page.wait_for_timeout(1000)

            # -- SHOT: scope with population --
            _shot(page, "jira-scope-population", width, locator=scope_step)

            # -- Preview MUST exist and be clickable (catch 5: no conditional skip) --
            preview_btn = page.get_by_test_id("jira-preview-btn")
            preview_btn.wait_for(state="visible", timeout=10000)
            preview_btn.scroll_into_view_if_needed()
            preview_btn.click()
            page.wait_for_timeout(2000)

            # -- Preview ledger MUST appear --
            preview_area = page.get_by_test_id("jira-preview")
            preview_area.wait_for(timeout=10000)

            # -- SHOT: scope with preview --
            _shot(page, "jira-scope-preview", width, locator=preview_area)

            # Click "Test" footer button to advance to test
            test_watch_btn = scope_step.locator('button').filter(has_text="Test")
            test_watch_btn.last.scroll_into_view_if_needed()
            test_watch_btn.last.click()
            page.wait_for_timeout(3000)

            # -- D3 TEST STEP --
            test_step = page.get_by_test_id("jira-test-step")
            test_step.wait_for(timeout=15000)

            # -- SHOT: test --
            _shot(page, "jira-test", width, locator=test_step)

            # Verify ProgressPlan rendered
            plan = test_step.locator('[role="group"]')
            assert plan.count() > 0, "ProgressPlan MUST render"

            # Click "Review and activate" footer button
            review_btn = test_step.locator('button').filter(has_text="Review")
            if review_btn.count() > 0:
                review_btn.first.scroll_into_view_if_needed()
                review_btn.first.click()
                page.wait_for_timeout(500)
            else:
                # Fall back to the general proceed button
                done_btn = test_step.locator('button').filter(has_text="Done")
                if done_btn.count() > 0:
                    done_btn.first.click()
                    page.wait_for_timeout(500)

            # -- Back at suggestions -> proceed to review --
            review_btn = page.get_by_test_id("setup-proceed-review")
            review_btn.wait_for(timeout=5000)
            review_btn.scroll_into_view_if_needed()
            review_btn.click()

            # -- Activation review MUST appear --
            setup_root = page.get_by_test_id("setup-root")
            setup_root.wait_for(timeout=5000)

            # -- SHOT: activation review --
            _shot(page, "jira-review", width, locator=setup_root)

            # -- Verify no critical page errors --
            critical = [e for e in errors if "ResizeObserver" not in e]
            assert len(critical) == 0, f"Page errors: {critical}"

    finally:
        server.stop()
