"""PHILO-13-04 (A3) -- faces that do not lie, fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch: every press a tap). The engine is off; this hub has no recorder.

  * Record on a hub with no recorder: the hub answers its real 501 (no mocked
    fetch). The face says ``NOT RECORDING`` + the reason; no ``is-recording``,
    no timer. Red on main 27b91553 (the orb showed recording, a timer ran).
  * The populated week with the engine off: Settings names the CONFIGURED
    switch (``SUMMARY SET ON``), Trust names whether data leaves
    (``SENDS NOTHING``, the lamp unlit), the Chair and the Meetings record name
    a STORED summary (never ``OFF`` above it), the Chair names the AVAILABLE
    fact (``No engine for summaries``).
  * Failure faces in plain words with a verb: the Intelligence BRIEF on a 500;
    People on a 503 keeps Priya and the unsent note, the failure one row with
    Try again.

Every record comes from a real producer: routes for decisions, people, notes
and the brief; meetings through the real repository (``save_meeting``, as the
Phase 11 rigs mint them: no route records a summarized meeting with the
engine off).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the faces glass needs Playwright")

TOKEN = "philo13-04-faces"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-04-shots")
SIZES = {1440: 900, 393: 852}
NOTE = "Priya asked for a backup on the EU shard work."


class TestFacesDoNotLie:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _seed_week(self, page: Any) -> None:
        from holdspeak.db import get_database
        from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

        db = get_database()
        now = datetime.now()
        started = (now - timedelta(hours=3)).replace(minute=0, second=0, microsecond=0)
        summary = "Latency came from a cold cache after deploy. Add a warm-up step."
        db.meetings.save_meeting(MeetingState(
            id="p13a3-incident", started_at=started, ended_at=started + timedelta(minutes=45),
            title="Checkout latency review",
            segments=[TranscriptSegment(text=summary, speaker="Karol", start_time=1.0, end_time=9.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["Incident"], summary=summary, action_items=[]),
        ))
        db.meetings.save_meeting(MeetingState(
            id="p13a3-vendor", started_at=started - timedelta(hours=1),
            ended_at=started - timedelta(minutes=30), title="Vendor call: card network",
            segments=[TranscriptSegment(text="We discussed the card network SLA.", speaker="Karol",
                                        start_time=1.0, end_time=5.0)],
        ))
        _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
        rid = _api(page, "POST", "/api/people/relationships",
                   {"display_name": "Priya Nair", "relationship_kind": "direct_report"}, token=TOKEN)["relationship"]["id"]
        _api(page, "POST", f"/api/people/relationships/{rid}/notes",
             {"topic": "Growth", "body": "Wants to lead the EU shard work."}, token=TOKEN)
        _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)

    def _page(self, pw: Any, width: int, *, seed: bool = True) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        if seed:
            self._seed_week(page)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1500)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _shot(page: Any, name: str, width: int) -> None:
        _settle(page)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))

    def _close_windows(self, page: Any, width: int) -> None:
        for _ in range(6):
            gadgets = page.locator(".desk-window .desk-light-close:visible")
            if not gadgets.count():
                return
            self._press(page, gadgets.last, width)
            page.wait_for_timeout(500)

    # ── the fences ───────────────────────────────────────────────────────

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_refused_start_says_not_recording(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width, seed=False)
            try:
                starts: list[int] = []
                page.on("response", lambda r: starts.append(r.status)
                        if r.url.endswith("/api/meeting/start") else None)
                self._press(page, page.get_by_test_id("arrival-record-meeting"), width)
                receipt = page.locator(".write-receipt").filter(has_text="NOT RECORDING")
                receipt.wait_for()
                page.wait_for_timeout(2500)  # a timer would have ticked twice
                self._shot(page, "record-refused", width)
                assert starts == [501], starts  # the real hub's refusal, no mock
                assert "NOT RECORDING · NO RECORDER ON THIS HUB" in receipt.inner_text()
                assert page.locator(".desk-orb.is-recording").count() == 0
                assert page.locator(".desk-orb-elapsed").count() == 0
                # A Retry cannot add a recorder (A.11): OK is the verb.
                assert receipt.get_by_role("button", name="OK").count() == 1
                assert receipt.get_by_role("button", name="Retry").count() == 0
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_each_face_names_its_fact(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # The Chair: the AVAILABLE fact, and a STORED summary per meeting.
                chair = page.locator(".chair")
                assert "No engine for summaries" in chair.inner_text()
                badges = page.get_by_test_id("arrival-meeting-badge").all_inner_texts()
                assert "SUMMARY STORED" in badges and "OFF" in badges, badges
                self._shot(page, "chair-facts", width)

                # Settings: the CONFIGURED switch.
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Settings']"), width)
                settings = page.locator(".desk-window[aria-label='Settings']")
                settings.get_by_text(re.compile(r"SUMMARY SET (ON|OFF)")).first.wait_for()
                assert not settings.get_by_text(re.compile(r"SUMMARY (ON|OFF)")).count()
                self._shot(page, "settings-configured", width)
                self._close_windows(page, width)

                # Trust: whether data leaves; no lit dot on a route that sends nothing.
                self._press(page, page.locator("button.egress-badge-button").first, width)
                trust = page.locator(".desk-trust-window")
                trust.get_by_text("SENDS NOTHING").first.wait_for()
                lit = trust.locator(".gadget-lamp[data-on='true']").all_inner_texts()
                assert all("SENDS OUT" in t for t in lit), lit
                assert not trust.get_by_text(re.compile(r"^OFF$")).count()
                self._shot(page, "trust-sends", width)
                self._close_windows(page, width)

                # Meetings: the record of a summarized meeting says STORED.
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Meetings']"), width)
                meetings = page.locator(".desk-window[aria-label='Meetings']")
                row = meetings.get_by_text("Checkout latency review").first
                row.wait_for()
                self._press(page, row, width)
                meetings.get_by_text("SUMMARY STORED").first.wait_for()
                assert not meetings.locator(".meetings-detail-head").get_by_text("SUMMARY OFF").count()
                self._shot(page, "meetings-stored", width)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_failures_are_plain_words_with_a_verb(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # Intelligence BRIEF on a 500: plain words + Try again, never `detail`.
                page.route("**/api/brief/latest*", lambda r: r.fulfill(
                    status=500, body='{"detail":"injected detail text"}', content_type="application/json"))
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Intelligence']"), width)
                intel = page.locator(".desk-window[aria-label='Intelligence']")
                intel.get_by_text("BRIEF DID NOT LOAD · HUB FAILED").wait_for()
                assert intel.get_by_role("button", name="Try again").count() >= 1
                assert "injected detail text" not in intel.inner_text()
                self._shot(page, "brief-failed", width)
                page.unroute("**/api/brief/latest*")
                self._close_windows(page, width)

                # People on a 503: Priya and the unsent note stay; one row + Try again.
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").fill("people")
                option = page.locator("[id='desk-palette-option-desk.open-people']")
                option.wait_for()
                self._press(page, option, width)
                people = page.locator("#surface-people")
                person = people.locator("button").filter(has_text="Priya Nair").first
                person.wait_for()
                self._press(page, person, width)
                self._press(page, people.get_by_role("tab", name="Context"), width)
                field = people.get_by_role("textbox", name="Grounding note")
                field.fill(NOTE)
                notes = re.compile(r".*/api/people/relationships/[^/]+/notes$")
                page.route(notes, lambda r: r.fulfill(
                    status=503, body='{"detail":"people_store_unavailable"}', content_type="application/json")
                    if r.request.method == "POST" else r.continue_())
                self._press(page, people.get_by_role("button", name="Add note"), width)
                people.get_by_text("PEOPLE STORE · NOT AVAILABLE NOW").wait_for()
                self._shot(page, "people-store-failed", width)
                # The row is ON SCREEN beside the note he is writing, not above
                # the scroll: its Try again owns its own centre point.
                again = people.get_by_test_id("people-failure").get_by_role("button", name="Try again")
                box = again.bounding_box()
                assert box and 0 <= box["y"] and box["y"] + box["height"] <= SIZES[width], box
                assert page.evaluate(
                    "([x, y]) => document.elementFromPoint(x, y)?.closest('[data-testid]')?.dataset.testid",
                    [box["x"] + box["width"] / 2, box["y"] + box["height"] / 2]) == "people-failure"
                assert field.is_visible()
                assert people.get_by_test_id("people-joy-state").count() == 0
                assert field.input_value() == NOTE
                assert "people_store_unavailable" not in people.inner_text()
                page.unroute(notes)
                self._press(page, again, width)
                people.get_by_text("PEOPLE STORE · NOT AVAILABLE NOW").wait_for(state="detached")
                assert field.input_value() == NOTE
                self._press(page, people.get_by_role("button", name="Add note"), width)
                people.get_by_text(NOTE).first.wait_for()
                self._shot(page, "people-note-kept-and-saved", width)
                assert not errors, errors
            finally:
                browser.close()
