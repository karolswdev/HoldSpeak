"""PHILO-13-04 (A3) -- faces that do not lie, fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch: every press a tap). The engine is off; this hub has no recorder.

  * Record on a hub with no recorder: the hub answers its real 501 (no mocked
    fetch). The face says ``NOT RECORDING`` + the reason; no ``is-recording``,
    no timer. Red on main 27b91553 (the orb showed recording, a timer ran).
  * The populated week with the engine off: Settings names the CONFIGURED
    switch (``SUMMARY SET ON``; with no engine, ``SUMMARY · NO ENGINE``), Trust names whether data leaves
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
from .chair_windows import open_chair_window
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

    def _page(self, pw: Any, width: int, *, seed: bool = True,
              fake_media: bool = False) -> tuple[Any, Any, list[str]]:
        args = ["--disable-smooth-scrolling"]
        if fake_media:
            # Chromium's synthetic tone device: never a real microphone.
            args += ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"]
        browser = pw.chromium.launch(headless=True, args=args)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720,
                                  permissions=["microphone"] if fake_media else [])
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
            gadgets = page.locator(".desk-window .desk-gadget-close:visible")
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
                # PHILO-13-11 (slice two, R2): at 393 Capture opens from the Speak AppIcon.
                if width <= 720:
                    open_chair_window(page, "Capture")
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
                # PHILO-13-11 (slice two, R2): at 393 the meetings are in The week.
                if width <= 720:
                    open_chair_window(page, "The week")
                badges = page.get_by_test_id("arrival-meeting-badge").all_inner_texts()
                assert "SUMMARY STORED" in badges and "OFF" in badges, badges
                self._shot(page, "chair-facts", width)

                # Settings: the CONFIGURED switch.
                self._press(page, page.locator(".desk-dock-launch[aria-label^='Settings']"), width)
                settings = page.locator(".desk-window[aria-label='Settings']")
                # 2026-10-03 (inventory A defect 10): with the switch on and no
                # engine the row names the missing engine, not SET ON.
                settings.get_by_text(re.compile(r"SUMMARY (SET (ON|OFF)|· NO ENGINE)")).first.wait_for()
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
                # A3-W: the rail now says SUMMARY STORED too (its hidden compact
                # line at 393), so the record's own head is the locator.
                head = meetings.locator(".meetings-detail-head")
                head.get_by_text("SUMMARY STORED").first.wait_for()
                assert not head.get_by_text("SUMMARY OFF").count()
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

    # ── PHILO-13-04 fix round: the recovery walks (Astra counsel 1-4, 6) ──

    @staticmethod
    def _palette(page: Any, query: str, option: str, width: int) -> None:
        TestFacesDoNotLie._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
        page.locator("[aria-controls=desk-palette-listbox]").fill(query)
        opt = page.locator(f"[id='desk-palette-option-{option}']")
        try:
            opt.wait_for(timeout=8_000)
        except Exception:
            ids = page.evaluate("() => [...document.querySelectorAll('[id^=desk-palette-option-]')].map(o => o.id)")
            raise AssertionError(f"no palette option {option!r}; options: {ids}")
        TestFacesDoNotLie._press(page, opt, width)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_room_retry_sends_the_newer_words(self, width: int) -> None:
        """Save fails, he types more, Try again: the request carries the newer
        text and the editor keeps it. Then Publish fails and Try again
        publishes. Red on HEAD 07aa76e3 (the retry resent the old text)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width, seed=False)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": "Ledger cutover"}, token=TOKEN)["project"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                self._palette(page, "Ledger", f"project.open.{pid}", width)
                room = page.locator("#surface-project-memory")
                self._press(page, room.get_by_test_id("updates-verb"), width)
                self._press(page, room.get_by_test_id("update-verb-draft-deterministic"), width)
                editor = room.locator("[contenteditable=true]").first
                editor.wait_for()
                puts: list[str] = []
                saves = re.compile(r".*/api/updates/[^/]+$")
                fail_next = {"on": True}

                def handle(route: Any) -> None:
                    if route.request.method != "PUT":
                        route.continue_()
                        return
                    puts.append(route.request.post_data or "")
                    if fail_next["on"]:
                        route.fulfill(status=500, body='{"detail":"injected failure"}',
                                      content_type="application/json")
                    else:
                        route.continue_()

                page.route(saves, handle)
                self._press(page, editor, width)
                page.keyboard.press("Control+End")
                page.keyboard.type(" first edit")
                self._press(page, room.get_by_test_id("update-verb-save"), width)
                room.get_by_text("NOT SAVED · HUB FAILED").wait_for()
                self._press(page, editor, width)
                page.keyboard.press("Control+End")
                page.keyboard.type(" and newer words")
                self._shot(page, "room-save-failed-then-typed", width)
                fail_next["on"] = False
                self._press(page, room.get_by_role("button", name="Try again"), width)
                room.get_by_text("NOT SAVED · HUB FAILED").wait_for(state="detached")
                assert len(puts) == 2, puts
                # The failed save carried only the first words; the retry
                # carries the newer ones too, and the editor still holds them.
                # (At 393 a tap seats the caret where it lands, so the two
                # fragments are checked, not their order.)
                assert "first edit" in puts[0] and "newer words" not in puts[0], puts[0]
                assert "first edit" in puts[1] and "and newer words" in puts[1], puts[1]
                text = editor.inner_text()
                assert "first edit" in text and "and newer words" in text, text
                self._shot(page, "room-retry-kept-newer-words", width)
                page.unroute(saves)

                # Publish fails, then Try again publishes (the publish recovery walk).
                pubs = re.compile(r".*/api/updates/[^/]+/publish$")
                page.route(pubs, lambda r: r.fulfill(status=500, body='{"detail":"injected failure"}',
                                                     content_type="application/json"))
                self._press(page, room.get_by_test_id("update-verb-publish"), width)
                room.get_by_text("NOT PUBLISHED · HUB FAILED").wait_for()
                assert "injected failure" not in room.inner_text()
                self._shot(page, "room-publish-failed", width)
                page.unroute(pubs)
                self._press(page, room.get_by_role("button", name="Try again"), width)
                room.get_by_text("NOT PUBLISHED · HUB FAILED").wait_for(state="detached")
                updates = _api(page, "GET", f"/api/projects/{pid}/updates", token=TOKEN)
                assert any(u.get("lifecycle") == "published" for u in updates.get("updates", [])), updates
                self._shot(page, "room-publish-recovered", width)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_ask_with_no_model_names_the_fact(self, width: int) -> None:
        """The real hub with no engine: Ask says NOT ANSWERED in plain words,
        no hub text on the face or in any title; its verb is Choose default."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width, seed=False)
            try:
                answers: list[str] = []
                page.on("response", lambda r: answers.append(r.text()) if r.url.endswith("/api/ask") else None)
                self._palette(page, "Ask", "go.ask", width)
                ask = page.locator(".desk-ask")
                ask.locator("textarea").first.fill("Summarize the week.")
                self._press(page, ask.get_by_role("button", name="ASK", exact=True), width)
                failure = ask.get_by_test_id("ask-failure")
                failure.wait_for()
                assert failure.inner_text().startswith("NOT ANSWERED · "), failure.inner_text()
                self._shot(page, "ask-not-answered", width)
                titles = page.evaluate("() => [...document.querySelectorAll('.desk-ask [title]')].map(e => e.title)")
                html = ask.inner_html()
                for raw in answers:
                    for word in re.findall(r'"error"\s*:\s*"([^"]+)"', raw):
                        assert word not in html, word
                        assert all(word not in t for t in titles), (word, titles)
                verb = ask.get_by_role("button", name="Choose default")
                if failure.inner_text().endswith("NO MODEL TO RUN IT"):
                    assert ask.get_by_role("button", name="Ask again").count() == 0
                    assert verb.count() == 1
                    self._press(page, verb, width)
                    page.wait_for_timeout(800)
                    self._shot(page, "ask-choose-default", width)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_voice_open_setup_opens_setup(self, width: int) -> None:
        """The voice failure's Open Setup opens the Setup application
        (configure-setup), never New Project. Red on HEAD (project-setup)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width, seed=False, fake_media=True)
            try:
                if width <= 720:   # PHILO-13-11 (slice two, R2): Capture from Speak
                    open_chair_window(page, "Capture")
                self._press(page, page.get_by_test_id("arrival-develop-thought"), width)
                thought = page.locator(".desk-window[aria-label='Thought']")
                mic = thought.locator("[aria-label='Speak the note']")
                mic.wait_for()
                self._press(page, mic, width)
                face = thought.locator(".desk-mic-failure")
                face.wait_for(timeout=20_000)
                self._shot(page, "voice-failed", width)
                no_prose = face.get_attribute("title") is None and \
                    "Your draft remains editable" not in thought.inner_html()
                setup = face.get_by_role("button", name=re.compile("^(Open Setup|Check the microphone)$"))
                self._press(page, setup, width)
                page.wait_for_timeout(1500)
                opened = page.evaluate(
                    "() => [...document.querySelectorAll('[id^=surface-]')].map(e => e.id)")
                self._shot(page, "voice-open-setup-destination", width)
                assert "surface-setup" in opened and "surface-project-setup" not in opened, opened
                assert no_prose, "the voice failure carries a sentence or a title"
                assert not errors, errors
            finally:
                browser.close()


    @pytest.mark.parametrize("width", list(SIZES))
    def test_people_try_again_rereads_the_person(self, width: int) -> None:
        """The person's detail read fails; Try again re-runs THAT read (counted)
        and the row leaves only when the person is back, notes and all. Red on
        HEAD 07aa76e3 (Try again read only /api/people/readiness)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                detail = re.compile(r".*/api/people/relationships/[^/?]+$")
                reads: list[int] = []
                state = {"down": True}

                def handle(route: Any) -> None:
                    if route.request.method != "GET":
                        route.continue_()
                        return
                    reads.append(1)
                    if state["down"]:
                        route.fulfill(status=503, body='{"detail":"people_store_unavailable"}',
                                      content_type="application/json")
                    else:
                        route.continue_()

                page.route(detail, handle)
                self._palette(page, "people", "desk.open-people", width)
                people = page.locator("#surface-people")
                person = people.locator("button").filter(has_text="Priya Nair").first
                person.wait_for()
                self._press(page, person, width)
                row = people.get_by_test_id("people-failure")
                row.wait_for()
                assert "people_store_unavailable" not in people.inner_text()
                before = len(reads)
                assert before >= 1
                self._shot(page, "people-detail-failed", width)

                state["down"] = False
                self._press(page, row.get_by_role("button", name="Try again"), width)
                row.wait_for(state="detached")
                assert len(reads) == before + 1, (before, len(reads))
                self._press(page, people.get_by_role("tab", name="Context"), width)
                people.get_by_text("Wants to lead the EU shard work.").first.wait_for()
                self._shot(page, "people-detail-recovered", width)
                page.unroute(detail)
                assert not errors, errors
            finally:
                browser.close()


# ── PHILO-13-04 A3-W: the Meetings list rail names the STORED fact ────────


def _mint_through_the_real_producers(tmp_path: Path) -> None:
    """One summarized and one unsummarized meeting, as H-A3's fences mint them.

    ``import_meeting`` -> ``_admit`` -> ``process_next_intel_job`` over the
    deferred-queue rig (only the engine and plugin host are doubles), into a
    database of its own; the hub boots on a copy of it. The patches live in a
    private ``MonkeyPatch`` context and leave before the hub boots. Then the
    stored meeting's run status is set to ``disabled``, as the H-A3 fence does
    (``tests/unit/test_philo13_a3h_meeting_summary.py``): the case that drew
    ``OFF`` beside a stored summary.
    """
    import shutil
    import sqlite3

    from holdspeak.intel_queue import process_next_intel_job
    from tests.unit.test_phase200_meeting_outcomes import _rig as _outcomes_rig
    from types import SimpleNamespace

    from holdspeak.meeting_import import import_meeting
    from tests.unit.test_philo13_a3h_meeting_summary import PRODUCED_SUMMARY, SOURCE
    from tests.unit.test_philo3_summary_detail import _admit

    def _import(db: Any, source: Path, meeting_id: str, title: str, transcript: str) -> Any:
        class _Transcriber:  # the one double: the words the import hears
            def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
                return transcript

        return import_meeting(
            source, db=db, transcriber=_Transcriber(),
            config=SimpleNamespace(meeting=SimpleNamespace(
                intel_enabled=True, intel_deferred_enabled=True)),
            title=title, meeting_id=meeting_id,
        ).state

    rig = tmp_path / "producer"
    rig.mkdir()
    with pytest.MonkeyPatch.context() as mp:
        # The HS-200-12 rig: `_queue_rig` with the REAL plugin host and the
        # REAL decision/action plugins put back; the one double is the
        # provider's completion text.
        db, engine = _outcomes_rig(rig, mp)
        source = rig / "meeting.wav"
        shutil.copyfile(SOURCE, source)
        stored = _import(db, source, A3W_STORED, "Checkout latency review",
                         "Latency came from a cold cache after deploy.")
        none = _import(db, source, A3W_NONE, "Vendor call: card network",
                       "We discussed the card network SLA.")
        _admit(db, stored.id)
        assert process_next_intel_job() is True
        assert db.meetings.get_meeting(stored.id).intel.summary == PRODUCED_SUMMARY
        assert db.meetings.get_meeting(none.id).intel is None
        with db._connection() as conn:
            conn.execute("UPDATE meetings SET intel_status = 'disabled' WHERE id = ?", (stored.id,))

        # Astra's #730 finding 3: a stored summary WITH proposed outcomes.
        # Each meeting is saved and enqueued by the stop-handoff producer, and
        # the real drainer runs the summary, the plugins and the proposal
        # bridge. Then two get a re-run: the first fails for real (the
        # provider errors), the second stays queued (this hub has no drainer).
        for meeting_id, title in OUTCOME_MEETINGS.items():
            _outcome_meeting(db, meeting_id, title)
        drained = 0
        while process_next_intel_job():
            drained += 1
        assert drained >= len(OUTCOME_MEETINGS)
        for meeting_id in (A3W_FAILED, A3W_QUEUED):
            db.intel.enqueue_intel_job(
                meeting_id, transcript_hash=db.meetings.get_meeting(meeting_id).transcript_hash(),
                reason="re-run")
        engine.error = "provider failed"
        assert process_next_intel_job(retry_max_attempts=1) is True
        rows = {m.id: m for m in db.meetings.list_meetings(limit=50)}
        assert {i: rows[i].intel_status for i in OUTCOME_MEETINGS} == {
            A3W_OUTCOMES: "ready", A3W_FAILED: "error", A3W_QUEUED: "queued"}
        assert all(rows[i].has_summary and rows[i].needs_you_count > 0 for i in OUTCOME_MEETINGS)
    src = sqlite3.connect(rig / "queue.db")
    dst = sqlite3.connect(tmp_path / "holdspeak.db")  # _boot's DEFAULT_DB_PATH
    src.backup(dst)
    src.close()
    dst.close()


A3W_STORED = "a3w-stored"
A3W_NONE = "a3w-none"
A3W_OUTCOMES = "a3w-outcomes"
A3W_FAILED = "a3w-rerun-failed"
A3W_QUEUED = "a3w-rerun-queued"
OUTCOME_MEETINGS = {
    A3W_OUTCOMES: "Payments cut-over review",
    A3W_FAILED: "Payments cut-over: re-run failed",
    A3W_QUEUED: "Payments cut-over: re-run queued",
}


def _outcome_meeting(db: Any, meeting_id: str, title: str) -> None:
    """The HS-200-12 meeting (`test_phase200_meeting_outcomes._meeting`) with
    its own title: saved, linked to a Project, enqueued at stop handoff."""
    from holdspeak.meeting_session import MeetingState, TranscriptSegment
    from tests.unit.test_hs172_loop_wire import _link_meeting_project, _seed_project
    from tests.unit.test_phase200_meeting_outcomes import SEGMENTS

    state = MeetingState(
        id=meeting_id, started_at=datetime.now() - timedelta(hours=2),
        ended_at=datetime.now() - timedelta(hours=1), title=title,
        segments=[TranscriptSegment(text=text, speaker=speaker, start_time=start, end_time=end)
                  for start, end, speaker, text in SEGMENTS],
    )
    db.meetings.save_meeting(state)
    _seed_project(db, "prj-cutover")
    _link_meeting_project(db, meeting_id, "prj-cutover")
    db.intel.enqueue_intel_job(meeting_id, transcript_hash=state.transcript_hash(),
                               reason="stop handoff")


class TestMeetingsRailNamesStored:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        _mint_through_the_real_producers(tmp_path)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_rail_says_summary_stored(self, width: int) -> None:
        """The list rail says SUMMARY STORED beside the stored summary, and
        OFF only beside the meeting that stores none. Red on main 02ce9e8c
        (the rail said OFF for both)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                rows = {r["id"]: r for r in _api(page, "GET", "/api/meetings?limit=20", token=TOKEN)["meetings"]}
                assert rows[A3W_STORED]["has_summary"] is True
                assert rows[A3W_STORED]["intel_status"] == "disabled"
                assert rows[A3W_NONE]["has_summary"] is False
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                _settle(page)
                TestFacesDoNotLie._press(
                    page, page.locator(".desk-dock-launch[aria-label^='Meetings']"), width)
                meetings = page.locator(".desk-window[aria-label='Meetings']")
                stored = meetings.get_by_test_id(f"meeting-row-{A3W_STORED}")
                none = meetings.get_by_test_id(f"meeting-row-{A3W_NONE}")
                stored.wait_for()
                none.wait_for()
                stored.scroll_into_view_if_needed()  # at 393 the rail scrolls
                TestFacesDoNotLie._shot(page, "meetings-rail-stored", width)
                assert stored.get_by_test_id("state-token").inner_text() == "SUMMARY STORED"
                assert not stored.get_by_text(re.compile(r"\bOFF\b")).count()
                assert none.get_by_test_id("state-token").inner_text() == "OFF"
                assert not none.get_by_text("STORED").count()
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_needs_you_count_never_covers_the_run(self, width: int) -> None:
        """Muad'Dib's ruling on Astra's #730 finding 3: capture → FAILED (Retry)
        → RUNNING / QUEUED → NEEDS YOU → SUMMARY STORED → the rest. Three
        meetings store a summary AND proposed outcomes (real producers); the
        rail names the failed and the queued re-run, and the count only where
        no run is live. Red on a139ad13 (all three said `5 NEED YOU`)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                rows = {r["id"]: r for r in _api(page, "GET", "/api/meetings?limit=20", token=TOKEN)["meetings"]}
                for meeting_id in OUTCOME_MEETINGS:
                    assert rows[meeting_id]["has_summary"] is True
                    assert rows[meeting_id]["needs_you_count"] == 5
                assert rows[A3W_FAILED]["intel_status"] == "error"
                assert rows[A3W_QUEUED]["intel_status"] == "queued"
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                _settle(page)
                TestFacesDoNotLie._press(
                    page, page.locator(".desk-dock-launch[aria-label^='Meetings']"), width)
                meetings = page.locator(".desk-window[aria-label='Meetings']")

                def token(meeting_id: str) -> str:
                    row = meetings.get_by_test_id(f"meeting-row-{meeting_id}")
                    row.wait_for()
                    return row.get_by_test_id("state-token").inner_text()

                assert token(A3W_FAILED) == "FAILED"
                # This hub has no drainer, so the queued run says so (HS-200-42).
                assert token(A3W_QUEUED) in {"QUEUED", "NOT DRAINING"}
                # PHILO-13-03: a meeting's proposals are TO REVIEW.
                assert token(A3W_OUTCOMES) == "5 TO REVIEW"
                assert token(A3W_STORED) == "SUMMARY STORED"
                meetings.get_by_test_id(f"meeting-row-{A3W_FAILED}").scroll_into_view_if_needed()
                TestFacesDoNotLie._shot(page, "meetings-rail-precedence", width)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_running_rerun_is_named_over_its_outcomes(self, width: int) -> None:
        """Astra's counsel r2 on #730: RUNNING beside a real nonzero
        needs_you_count, through the real rail producer. The stored summary and
        its 5 proposals came from the real plugins and bridge (setup), and setup
        left its re-run queued. Here the REAL executor claims that re-run on
        the hub's own database and broker; the one double, the provider,
        BLOCKS until the browser has read the rail. Red with the
        PROCESS_LEADS skip removed (the rail said `5 NEED YOU`)."""
        import threading

        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.intel_queue import process_next_intel_job
        from tests.unit.test_meeting_deferred_admission import _Route
        from tests.unit.test_phase200_meeting_outcomes import ACT, DEC, ScriptedIntel

        db = get_database()  # the hub's database
        engine = ScriptedIntel()
        entered, release = threading.Event(), threading.Event()
        real_analyze = engine.analyze

        def held_analyze(transcript: str, **kwargs: Any) -> Any:
            entered.set()
            release.wait(120.0)  # the provider answers only when released
            return real_analyze(transcript, **kwargs)

        engine.analyze = held_analyze  # type: ignore[method-assign]
        outcome: dict[str, Any] = {}
        with pytest.MonkeyPatch.context() as mp, sync_playwright() as pw:
            mp.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
            mp.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
            mp.setattr("holdspeak.plugins.router.preview_route_from_transcript",
                       lambda **kwargs: _Route((DEC, ACT)))
            worker = threading.Thread(
                target=lambda: outcome.setdefault("ran", process_next_intel_job()), daemon=True)
            worker.start()
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                assert entered.wait(60.0), "the executor never reached the provider"
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                rows = {r["id"]: r for r in _api(page, "GET", "/api/meetings?limit=20", token=TOKEN)["meetings"]}
                assert rows[A3W_QUEUED]["intel_status"] == "running", rows[A3W_QUEUED]
                assert rows[A3W_QUEUED]["needs_you_count"] > 0
                assert rows[A3W_QUEUED]["has_summary"] is True
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1500)
                _settle(page)
                TestFacesDoNotLie._press(
                    page, page.locator(".desk-dock-launch[aria-label^='Meetings']"), width)
                meetings = page.locator(".desk-window[aria-label='Meetings']")
                row = meetings.get_by_test_id(f"meeting-row-{A3W_QUEUED}")
                row.wait_for()
                row.scroll_into_view_if_needed()
                assert entered.is_set() and not release.is_set()
                TestFacesDoNotLie._shot(page, "meetings-rail-running", width)
                assert row.get_by_test_id("state-token").inner_text() == "RUNNING"
                assert not row.get_by_text("TO REVIEW").count()
                assert not errors, errors
            finally:
                release.set()
                worker.join(120.0)
                browser.close()
        assert not worker.is_alive() and outcome.get("ran") is True, outcome
        after = db.meetings.get_meeting(A3W_QUEUED)
        assert after.intel_status == "ready", after.intel_status

