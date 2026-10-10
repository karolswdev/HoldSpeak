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


def _gh_signed_in(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
    """gh signed in as acme with one repository; every list read is empty."""
    args = list(argv)
    if args[:3] == ["gh", "auth", "status"]:
        return subprocess.CompletedProcess(
            argv, 0, stdout="", stderr="github.com\n  Logged in to github.com account acme (keyring)\n")
    if args[:3] == ["gh", "repo", "list"]:
        return subprocess.CompletedProcess(
            argv, 0, stdout='[{"name":"app","owner":{"login":"acme"},"visibility":"PUBLIC"}]', stderr="")
    return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")


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


def _add_walk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Astra r1 on #1068: the job done: pick a repository, Add, reload, it is under SOURCES;
    the same repository again says Already watched."""
    _ensure_build()
    _server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_gh_signed_in)
    errors: list[str] = []
    from playwright.sync_api import sync_playwright

    def pick_and_add(room: Any) -> Any:
        well = room.get_by_test_id("room-add-sources")
        well.wait_for(timeout=T)
        well.get_by_test_id("door-trigger-github").click()
        well.get_by_test_id("door-pick-acme/app").click()
        add = well.get_by_test_id("room-add-sources-add")
        page.wait_for_function(
            "() => !document.querySelector('[data-testid=room-add-sources-add]')?.disabled", timeout=T)
        add.click()
        return well

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            clear_hub_windows(page, token=TOKEN)
            pid = _api(page, "POST", "/api/projects/door", {"outcome": "Ledger cutover"}, token=TOKEN)["projectId"]
            _api(page, "POST", "/api/connections/github/recheck", {}, token=TOKEN)

            room = _open_room(page, pid)
            well = pick_and_add(room)
            well.wait_for(state="detached", timeout=T)  # added: the well closes

            # Reload: the source is the project's, under SOURCES.
            room = _open_room(page, pid)
            scope = room.locator("[data-testid=source-scope]", has_text="acme/app")
            scope.first.wait_for(timeout=T)
            assert room.locator("[data-testid=source-scope]", has_text="acme/app").count() == 1
            _settle(page)
            room.screenshot(path=str(SHOTS / f"room-source-added-{width}.png"))

            # The same repository again: refused, Already watched, nothing doubled.
            def watch_ids() -> list[str]:
                items = _api(page, "GET", f"/api/projects/{pid}/room", token=TOKEN)["sources"]["items"]
                return sorted(i for item in items if item.get("scope") == "acme/app" for i in item.get("watchIds", []))

            before = watch_ids()
            assert before, "the added repository arms its watches"
            room.get_by_test_id("room-add-source").click()
            well = pick_and_add(room)
            well.get_by_text("Already watched").wait_for(timeout=T)
            assert watch_ids() == before
            _assert_clean(page, errors)
        finally:
            browser.close()


@pytest.mark.parametrize("width", [1440, 393])
def test_add_a_repository_and_it_stays_after_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    _add_walk(tmp_path, monkeypatch, width)


@pytest.mark.parametrize("width", [1440, 393])
def test_room_add_source_and_sign_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _walk(tmp_path, monkeypatch, width)


# ── Astra r2 on #1068: what the parked drawer did, the Room does ──────────


def _seed_lone_meeting() -> None:
    """A project with one filed meeting (the hub's own producers)."""
    from datetime import datetime, timedelta

    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db = get_database()
    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    db.projects.create_project(project_id="p-lone", name="Vendor review", description="One meeting.",
                               keywords=["vendor"])
    db.meetings.save_meeting(MeetingState(
        id="m-lone", started_at=start, ended_at=start + timedelta(minutes=30), title="Vendor call",
        segments=[TranscriptSegment(text="We pick the vendor.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["vendor"], summary="Pick it.", action_items=[]),
        intel_status="completed"))
    db.projects.associate_meeting_project(meeting_id="m-lone", project_id="p-lone", source="manual", confidence=1.0)


@pytest.mark.parametrize("width", [1440, 393])
def test_park_from_files_leaves_its_receipt_and_restore_in_the_room(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """FILES → Get Info → Park: the Room keeps `PARKED · Vendor call` with
    Restore, also when FILES is left empty; Restore brings the meeting back."""
    _ensure_build()
    _server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_gh_not_signed_in)
    _seed_lone_meeting()
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
            room = _open_room(page, "p-lone")
            files = room.get_by_test_id("room-files")
            files.wait_for(timeout=T)
            files.locator(".object-list-open[aria-label^='Vendor call,']").click()
            files.get_by_test_id("room-files-info").click()
            info = page.locator(".drawer-info-window")
            info.wait_for(timeout=T)
            info.get_by_role("button", name="Park", exact=True).click()
            receipt = room.get_by_test_id("room-files-park-receipt")
            receipt.wait_for(timeout=T)
            page.wait_for_function(
                "() => !document.querySelector(\"#surface-project-memory [data-object-id='meeting:m-lone']\")",
                timeout=T)
            assert receipt.locator("[role=status]").text_content() == "PARKED · Vendor call"
            _settle(page)
            room.screenshot(path=str(SHOTS / f"room-park-receipt-{width}.png"))
            receipt.get_by_role("button", name="Restore", exact=True).click()
            room.locator("[data-object-id='meeting:m-lone']").wait_for(timeout=T)
            page.wait_for_function(
                "() => /RESTORED/.test(document.querySelector("
                "'#surface-project-memory [data-testid=room-files-park-receipt] [role=status]')?.textContent || '')",
                timeout=T)
            _assert_clean(page, errors)
        finally:
            browser.close()


@pytest.mark.parametrize("width", [1440, 393])
def test_an_older_project_registers_its_repository_in_the_room(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """A project that watches acme/app with no registration (made before the
    Door registered, or by the API): Register in the Room registers it."""
    _ensure_build()
    _server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_gh_signed_in)
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
            pid = _api(page, "POST", "/api/projects/door", {
                "outcome": "Ledger cutover",
                "sources": [{"provider": "github", "scope": "acme/app", "watches": ["open_prs"]}],
            }, token=TOKEN)["projectId"]
            before = _api(page, "GET", f"/api/projects/{pid}/repository", token=TOKEN)
            assert (before["registered"], before["watched"]) == (False, ["acme/app"]), before
            room = _open_room(page, pid)
            register = room.get_by_test_id("room-register")
            register.wait_for(timeout=T)
            register.click()
            register.wait_for(state="detached", timeout=T)  # registered: the verb leaves
            after = _api(page, "GET", f"/api/projects/{pid}/repository", token=TOKEN)
            assert (after["repository"], after["registered"], after["cloned"]) == ("acme/app", True, False), after
            _assert_clean(page, errors)
        finally:
            browser.close()
