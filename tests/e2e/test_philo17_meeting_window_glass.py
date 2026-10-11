"""PHILO-17 (owner 2026-10-10, "A meeting opens in one window") -- on glass.

Through the real hub on an isolated HOME, at 1440x900 and 393x852:

* One meeting, five doors: the Needs-you row, the desk icon, the ⌘K hit
  (the Search tap at 393), the Meetings list row, and a Project Room's FILES
  row (a second meeting, filed in the Project). Each meeting opens in its own
  window, ``pullout:meeting:<id>``: after every door there is exactly ONE
  such window on the glass and on the hub, and it is the front window (the
  second door brings it to the front; it never opens twice). The Meetings
  window is the list: it holds no record.
* Record -> Stop keeps the same window: the Record orb opens the new
  meeting's window on the live room; Stop turns the SAME window
  (``pullout:meeting:<id>``) into the saved record. The capture device is
  the one stand-in: ``on_start`` / ``on_stop`` answer in place of a
  microphone, and the stop saves the meeting through the real producer.
* A person icon opens THAT person (``pullout:people:<id>``, the
  RelationshipPane with the person's name), not the People application.

Shots go to ``.tmp/evidence-shots/`` (``tests/_evidence.py``).
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the meeting window glass needs Playwright")

TOKEN = "philo17-meeting-window"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-17/assets/meeting-window-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
ONE = "m-one"
TWO = "m-two"
LIVE = "m-live"
PROJECT = "p-room"


def _http(base: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"authorization": f"Bearer {TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}


def _save_meeting(meeting_id: str, title: str, hours_ago: float, intel_status: str) -> None:
    """A meeting saved by the real producer (MeetingState -> save_meeting)."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState, TranscriptSegment

    start = (datetime.now() - timedelta(hours=hours_ago)).replace(microsecond=0)
    get_database().meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
        segments=[TranscriptSegment(text="We move the cutover to Friday.", speaker="Me", start_time=1.0, end_time=4.0),
                  TranscriptSegment(text="Agreed.", speaker="Avery", start_time=4.0, end_time=5.0)],
        intel_status=intel_status))


class _Capture:
    """The capture boundary: start answers the live meeting; stop saves it
    through the real producer (as the recorder does) and answers stopped."""

    def start(self) -> Any:
        return {"id": LIVE, "title": "Live sync", "started_at": datetime.now().astimezone().isoformat()}

    def stop(self) -> Any:
        _save_meeting(LIVE, "Live sync", 0.1, "disabled")
        return {"status": "stopped"}


class TestOneMeetingOneWindow:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        capture = _Capture()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN, on_start=capture.start, on_stop=capture.stop)
        self.base = base
        from holdspeak.db import get_database
        from holdspeak.people import production_people_store
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.people_service import PeopleService

        db = get_database()
        # ONE: a meeting whose summary failed (a Needs-you member), loose on the desk.
        _save_meeting(ONE, "Platform sync", 2, "error")
        # TWO: a meeting filed in a Project (its door is the Room's FILES).
        db.projects.create_project(project_id=PROJECT, name="Payments ledger cutover",
                                   description="Move settlement.", keywords=["ledger"])
        _save_meeting(TWO, "Vendor review", 5, "disabled")
        db.projects.associate_meeting_project(meeting_id=TWO, project_id=PROJECT, source="manual", confidence=1.0)
        # A person on the desk (loose: in no Project).
        store = production_people_store()
        store.initialize()
        owner = Principal(PrincipalKind.OWNER, "karol")
        self.person = PeopleService(store).create_relationship(
            owner, {"display_name": "Avery Chen", "relationship_kind": "direct_report"})["id"]
        _http(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        self.page, self.phone, self.width = page, width < 720, width
        self._home()
        return browser, page, errors

    def _home(self, staged: str | None = None) -> None:
        page = self.page
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        if staged:
            page.evaluate("""(key) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}))""", staged)
            page.reload(wait_until="load")
        _normal_chair(page)
        page.locator("[data-testid=desk-screen]").wait_for(timeout=T)
        page.wait_for_timeout(1200)

    def _press(self, loc: Any) -> None:
        loc = loc.first
        loc.scroll_into_view_if_needed()
        if self.phone:
            b = loc.bounding_box()
            assert b, "nothing to tap"
            self.page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        else:
            loc.click()
        self.page.wait_for_timeout(600)

    def _hub_ids(self) -> list[str]:
        return [w["id"] for w in _http(self.base, "GET", "/api/desk/windows").get("windows") or []]

    def _one_front(self, meeting_id: str, door: str) -> None:
        """Exactly one window for the meeting, on the glass and on the hub, in front."""
        wid = f"pullout:meeting:{meeting_id}"
        page = self.page
        page.wait_for_function(
            "(id) => { const w = document.getElementById(id); return !!w && w.classList.contains('is-front'); }",
            arg=wid, timeout=T)
        on_glass = page.evaluate(
            "() => [...document.querySelectorAll('[id^=\"pullout:meeting:\"]')].map((w) => w.id)")
        assert on_glass.count(wid) == 1, f"{door}-{self.width}: {on_glass}"
        for _ in range(40):
            hub = [i for i in self._hub_ids() if i.startswith("pullout:meeting:")]
            if hub.count(wid) == 1:
                break
            page.wait_for_timeout(250)
        assert hub.count(wid) == 1, f"{door}-{self.width}: hub {hub}"
        # Never a second form of the same meeting's window (a bare id).
        assert meeting_id not in [i.removeprefix("pullout:") for i in hub], hub
        # The Meetings window is the list: it holds no record.
        assert page.locator("#surface-meetings [data-testid=meeting-open-transcript]").count() == 0, door

    def _shot(self, board: str) -> None:
        _settle(self.page)
        self.page.screenshot(path=str(SHOTS / f"{board}-{self.width}.png"))

    def _palette(self, query: str) -> None:
        page = self.page
        if page.locator("#desk-tool-shelf").count() == 0:
            if self.phone:
                self._press(page.locator("button[aria-controls=desk-tool-shelf]"))
            else:
                page.keyboard.press("Meta+k")
                page.wait_for_timeout(400)
        box = page.locator("input[aria-controls=desk-palette-listbox]")
        box.wait_for(timeout=T)
        box.fill(query)
        page.wait_for_timeout(900)

    # ── the cases ────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_one_meeting_opens_in_one_window_from_every_door(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # 1. The Needs-you row (the failed summary): Summarize opens the meeting.
                self._press(page.locator("[data-object-id='drawer:needs']"))
                row = page.locator("[data-testid='needs-row']", has_text="Platform sync").first
                row.wait_for(timeout=T)
                self._press(row.locator("[data-verb=summarize]"))
                self._one_front(ONE, "needs")
                win = page.locator(f"[id='pullout:meeting:{ONE}']")
                # The whole record: the wings, the transcript, the foot verbs.
                for verb in ("Open transcript", "MD", "SRT", "Park"):
                    assert win.get_by_role("button", name=verb, exact=True).count() >= 1, verb
                assert win.get_by_role("tab", name="Review").count() + win.locator(".desk-wing", has_text="Review").count() >= 1
                assert "Platform sync" in (win.get_attribute("aria-label") or win.inner_text())
                self._shot("meeting-window-needs")

                # 2. The desk icon: the open window comes to the front, never twice.
                icon = page.locator(f".desk-screen [data-object-id='meeting:{ONE}']").first
                icon.focus()
                page.keyboard.press("Enter")
                page.wait_for_timeout(600)
                self._one_front(ONE, "icon")

                # 3. The ⌘K hit (the Search tap at 393).
                self._palette("Platform sync")
                option = page.locator("#desk-palette-listbox [role=option]", has_text="Platform sync").first
                self._press(option)
                self._one_front(ONE, "palette")

                # 4. The Meetings list row (the Meetings window is the list).
                self._home(staged="review-meetings")
                page.locator("#surface-meetings [data-testid='meetings-headline']").wait_for(timeout=T)
                self._shot("meetings-list")
                self._press(page.locator(f"#surface-meetings [data-testid='meeting-row-{ONE}'] .meetings-stream-row-body"))
                self._one_front(ONE, "list")

                # 5. The Project Room's FILES row: the filed meeting opens its own window.
                self._palette("Payments ledger cutover")
                self._press(page.locator("#desk-palette-listbox [role=option]", has_text="Payments ledger cutover"))
                files = page.locator("#surface-project-memory [data-testid=room-files]")
                files.wait_for(timeout=T)
                self._press(files.get_by_text("Vendor review").first)
                self._press(files.locator("[data-testid=room-files-open]"))
                self._one_front(TWO, "room")
                # The list row of the same meeting fronts it, never a second window.
                self._home(staged="review-meetings")
                self._press(page.locator(f"#surface-meetings [data-testid='meeting-row-{TWO}'] .meetings-stream-row-body"))
                self._one_front(TWO, "room-then-list")
                self._shot("meeting-window-two")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_record_then_stop_keeps_the_same_window(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                orb = page.get_by_role("button", name="Record a meeting")
                self._press(orb)
                wid = f"pullout:meeting:{LIVE}"
                win = page.locator(f"[id='{wid}']")
                win.wait_for(timeout=T)
                # The live room in the meeting's own window.
                win.get_by_role("button", name="Stop meeting").wait_for(timeout=T)
                self._shot("meeting-window-live")
                self._press(page.get_by_role("button", name="Stop recording"))
                # The SAME window shows the saved record; no new window opened.
                win.get_by_role("button", name="Open transcript").wait_for(timeout=T)
                ids = page.evaluate("() => [...document.querySelectorAll('[id^=\"pullout:meeting:\"]')].map((w) => w.id)")
                assert ids == [wid], ids
                assert page.locator("#surface-live").count() == 0
                self._shot("meeting-window-stopped")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_person_icon_opens_the_person(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                icon = page.locator(f".desk-screen [data-object-id='people:{self.person}']").first
                icon.wait_for(timeout=T)
                icon.focus()
                page.keyboard.press("Enter")
                wid = f"pullout:people:{self.person}"
                win = page.locator(f"[id='{wid}']")
                win.locator("[data-testid=person-window]").wait_for(timeout=T)
                assert "Avery Chen" in win.inner_text()
                assert win.locator(".people-lenses [role=tab]").count() == 6
                # The person, not the People application (the roster).
                assert page.locator("#surface-people").count() == 0
                assert not re.search(r"\bBack\b", win.locator(".people-detail-head").inner_text())
                self._shot("person-window")
                assert not errors, errors
            finally:
                browser.close()
