"""PHILO-17 lane sources (U10, U29, U30) -- the Room's Add source, glass.

A bare project made through the Door, GitHub not signed in (the injected gh
runner answers ``gh auth status`` as the real gh does with no login). The
Room shows SOURCES with Add source open (the project has none): the same rows
as New Project. GitHub says NOT SIGNED IN; Connect opens the sign-in well in
the row with the exact command and Copy, and no Settings window opens. At
1440 the Dock opens the project's Room, never the drawer (one home).
1440 and 393.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="sources glass needs Playwright")

SHOTS = evidence_dir("pm/roadmap/holdspeak/philo-17/sources-shots")
SHOTS.mkdir(parents=True, exist_ok=True)
TOKEN = "philo17-sources"
T = 30_000


def _gh_not_signed_in(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
    """gh with no login: what the real ``gh auth status`` prints."""
    if list(argv[:3]) == ["gh", "auth", "status"]:
        return subprocess.CompletedProcess(
            argv, 1, stdout="",
            stderr="You are not logged into any GitHub hosts. To log in, run: gh auth login\n")
    return subprocess.CompletedProcess(argv, 1, stdout="", stderr="not logged in")


def _open_room(page: Any, project_id: str) -> Any:
    page.evaluate(
        """([key, scope]) => sessionStorage.setItem(
             "hs.desk.staged-surface-open", JSON.stringify({key, scope}))""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    room = page.locator("#surface-project-memory")
    room.wait_for(timeout=T)
    return room


def _walk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    _server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_gh_not_signed_in)
    errors: list[str] = []
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            clear_hub_windows(page, token=TOKEN)
            pid = _api(page, "POST", "/api/projects/door", {"outcome": "Ledger cutover"}, token=TOKEN)["projectId"]
            # The stored check: gh answers "not logged in".
            _api(page, "POST", "/api/connections/github/recheck", {}, token=TOKEN)

            room = _open_room(page, pid)
            # U10: the Room has the New Project rows under SOURCES (open: no sources yet).
            well = room.get_by_test_id("room-add-sources")
            well.wait_for(timeout=T)
            gh_row = well.get_by_test_id("door-row-github")
            gh_row.wait_for(timeout=T)
            assert well.get_by_test_id("door-row-jira").count() == 1
            # U29: the cause in plain words, never UNREACHABLE.
            text = gh_row.inner_text().upper()
            assert "NOT SIGNED IN" in text and "UNREACHABLE" not in text, text
            gh_row.get_by_test_id("door-connect-github").click()
            sign_in = well.get_by_test_id("signin-well-github")  # the open well is the line's sibling
            sign_in.wait_for(timeout=T)
            assert "gh auth login" in sign_in.inner_text()
            assert sign_in.get_by_role("button", name="Copy").count() == 1
            # Connect signs in where the row is: no Settings window over the work.
            page.wait_for_timeout(400)
            assert page.locator("#surface-settings").count() == 0
            _settle(page)
            room.screenshot(path=str(SHOTS / f"room-add-source-{width}.png"))

            if width >= 1000:
                # U30: the Dock opens the project's Room (one home), not the drawer.
                clear_hub_windows(page, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                dock = page.locator(".desk-dock-project", has_text="Ledger cutover").first
                dock.wait_for(timeout=T)
                dock.click()
                page.locator("#surface-project-memory").wait_for(timeout=T)
                page.wait_for_timeout(400)
                assert page.locator(".drawer-window").count() == 0
            _assert_clean(page, errors)
        finally:
            browser.close()


@pytest.mark.parametrize("width", [1440, 393])
def test_room_add_source_and_sign_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _walk(tmp_path, monkeypatch, width)
