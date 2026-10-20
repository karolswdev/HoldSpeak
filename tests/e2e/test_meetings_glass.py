"""The Meetings app, AS RENDERED: what only a real browser proves of a meeting.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

* PHILO-15 lane 12, B22: the meeting record uses the window body's whole
  width (no rail column beside it), at 1440 (also zoomed) and 393.
* PHILO-17 ("A meeting opens in one window"): one meeting, five doors (the
  Needs-you row, the desk icon on Enter, the ⌘K hit or the Search tap, the
  Meetings list row, the Room's FILES row), ONE window on the glass and on the
  hub, in front; Record -> Stop keeps the same window; a saved Meetings
  window scoped to a meeting migrates on the hub, in three views; a meeting
  with a summary holds still while its Send preview lands (held 2 s).

The rest of the PHILO-17 meeting-window glass has cheaper successors: a person
icon opens the person in web/src/desk/__tests__/people.app.test.tsx; a summary
that finishes keeps the open meeting in front in
web/src/desk/chair/__tests__/aftercarePhone.philo1317.test.tsx:146.
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .fit_rig import BOX_JS, T, WIDTHS, FitRig, TITLE
from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from .meetings_rig import _save_meeting
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Meetings glass needs Playwright")

pytestmark = [pytest.mark.e2e]


class TestTheMeetingRecord(FitRig):
    """replaces: tests/e2e/test_philo15_12_ugly_glass.py::TestPhilo15Lane12Ugly::test_the_record_uses_the_window_width (moved whole)."""

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_record_uses_the_window_width(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._seed_meeting()
                # PHILO-17 ("A meeting opens in one window"): the record is the
                # meeting's own window; it takes the window body's whole width.
                self._stage(page, "review-meetings", "meeting:p15-12-m")
                win = page.locator("#surface-meetings")
                detail = win.locator(".desk-surface-body > .surface-section").first
                detail.locator(".kit-disp").first.wait_for(timeout=T)
                page.wait_for_timeout(800)
                _settle(page)

                def measure(tag: str) -> dict[str, Any]:
                    body = win.locator(".desk-surface-body").first.evaluate(
                        "(e) => { const st = getComputedStyle(e); const b = e.getBoundingClientRect();"
                        " return {x: b.left, w: e.clientWidth - parseFloat(st.paddingLeft) - parseFloat(st.paddingRight)}; }")
                    d = detail.evaluate(BOX_JS)
                    facts = {"body": body, "detail": d}
                    self.facts[f"B22_{tag}"] = facts
                    # The record takes the window body's whole width; no rail
                    # column beside it (the list is its own window now).
                    assert d["w"] >= body["w"] - 2, facts
                    assert win.locator(".surface-split-main").count() == 0, facts
                    return facts

                measure("normal")
                self._shot(page, "B22-record", width, win)
                if width > 720:
                    win.get_by_role("button", name=f"Zoom {TITLE}").click()
                    page.wait_for_timeout(700)
                    _settle(page)
                    page.mouse.wheel(0, 600)
                    page.wait_for_timeout(400)
                    measure("zoomed")
                    self._shot(page, "B22-record-zoomed", width)
                self._write("record", width)
                assert not errors, errors
            finally:
                browser.close()


SIZES = {1440: 900, 393: 852}
MW_TOKEN = "meetings-glass-window"
MW_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-17/assets/meeting-window-shots")
ONE = "m-one"
LIVE = "m-live"
PROJECT = "p-room"


def _http(base: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"authorization": f"Bearer {MW_TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}




class _Capture:
    """The capture boundary and the runtime's state, told truthfully: start
    answers the live meeting and the state says it is live (the producer's
    words, ``meeting_active``); stop saves the meeting through the real
    producer (as the recorder does) and the state goes back to the runtime's
    idle words (``meeting_active: False``, holdspeak/runtime/activity.py)."""

    def __init__(self) -> None:
        self.live = False

    def start(self) -> Any:
        self.live = True
        return {"id": LIVE, "title": "Live sync", "started_at": datetime.now().astimezone().isoformat()}

    def stop(self) -> Any:
        self.live = False
        _save_meeting(LIVE, "Live sync", 0.1, "disabled")
        return {"status": "stopped"}

    def state(self) -> Any:
        if self.live:
            return {"id": LIVE, "meeting_id": LIVE, "meeting_active": True, "title": "Live sync",
                    "formatted_duration": "00:01", "segments": []}
        return {"id": "web-runtime", "meeting_active": False, "meeting_id": None, "segments": []}


class TestOneMeetingOneWindow:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        capture = _Capture()
        server, base = _boot(tmp_path, monkeypatch, token=MW_TOKEN, on_start=capture.start, on_stop=capture.stop,
                             get_state=capture.state)
        self.base, self.server = base, server
        from holdspeak.db import get_database
        from holdspeak.people import production_people_store
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.people_service import PeopleService

        db = get_database()
        # ONE: a meeting whose summary failed (a Needs-you member), loose on the desk.
        _save_meeting(ONE, "Platform sync", 2, "error")
        # A Project: ONE is filed in it during the walk (its fifth door is the
        # Room's FILES; a filed meeting leaves the loose desk).
        db.projects.create_project(project_id=PROJECT, name="Payments ledger cutover",
                                   description="Move settlement.", keywords=["ledger"])
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
        page.goto(f"{self.base}/?token={MW_TOKEN}", wait_until="load")
        if staged:
            page.evaluate("""(key) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}))""", staged)
            page.reload(wait_until="load")
        _normal_chair(page)
        page.locator("[data-testid=desk-screen]").wait_for(state="attached", timeout=T)
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

    def _open_icon(self, key: str) -> None:
        """A desk icon opens on Enter (a press only selects it)."""
        icon = self.page.locator(f"[data-testid=desk-screen] [data-object-id='{key}']").first
        icon.wait_for(state="attached", timeout=T)
        icon.focus()
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(600)

    def _hub_rows(self) -> list[dict[str, Any]]:
        return list(_http(self.base, "GET", "/api/desk/windows").get("windows") or [])

    def _hub_ids(self) -> list[str]:
        return [w["id"] for w in self._hub_rows()]

    def _one_front(self, meeting_id: str, door: str) -> None:
        """Exactly one window for the meeting, on the glass and on the hub, in front."""
        wid = "surface-meetings"
        page = self.page
        page.wait_for_function(
            "(id) => { const w = document.getElementById(id); return !!w && w.classList.contains('is-front'); }",
            arg=wid, timeout=T)
        on_glass = page.evaluate(
            "() => [...document.querySelectorAll('#surface-meetings')].map((w) => w.id)")
        assert on_glass.count(wid) == 1, f"{door}-{self.width}: {on_glass}"
        # Never a second form of the same meeting's window (a bare id).
        assert page.locator(f"[id='pullout:{meeting_id}']").count() == 0, door
        for _ in range(40):
            rows = self._hub_rows()
            mine = [r for r in rows if r["id"] == wid]
            if len(mine) == 1 and mine[0]["front"]:
                break
            page.wait_for_timeout(250)
        assert len(mine) == 1, f"{door}-{self.width}: hub {[r['id'] for r in rows]}"
        # The hub holds it as the FRONT window, as this view shows it.
        assert mine[0]["front"], f"{door}-{self.width}: hub front {[(r['id'], r['front']) for r in rows]}"
        assert f"pullout:{meeting_id}" not in [r["id"] for r in rows], rows
        assert mine[0]["object_ref"] == f"meeting:{meeting_id}", mine
        assert page.locator("[id^='pullout:meeting:']").count() == 0, door
        assert page.locator("#surface-meetings .meetings-detail-body").count() == 1, door

    def _shot(self, board: str) -> None:
        _settle(self.page)
        self.page.screenshot(path=str(MW_SHOTS / f"{board}-{self.width}.png"))

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
        """replaces: tests/e2e/test_philo17_meeting_window_glass.py::TestOneMeetingOneWindow::test_one_meeting_opens_in_one_window_from_every_door
        (moved whole: Enter on a desk icon, ⌘K at 1440, taps at 393)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # 1. The Needs-you row (the failed summary): Summarize opens the meeting.
                self._press(page.get_by_test_id("desk-bell"))
                # P5 may also offer this meeting as a project source. Select
                # its failed-summary member rather than whichever title is first.
                row = page.get_by_test_id("needs-row").filter(
                    has_text="Platform sync", has=page.locator("[data-verb=summarize]"),
                )
                row.wait_for(timeout=T)
                assert row.count() == 1
                self._press(row.locator("[data-verb=summarize]"))
                self._one_front(ONE, "needs")
                win = page.locator("#surface-meetings")
                self._press(win.get_by_role("button", name="More actions", exact=True))
                for verb in ("Open transcript", "Export MD", "Export SRT", "Park"):
                    assert page.get_by_role("menuitem", name=verb, exact=True).count() == 1, verb
                page.keyboard.press("Escape")
                assert win.get_by_role("tab", name="Outcomes").count() + win.locator(".desk-wing", has_text="Outcomes").count() >= 1
                assert "Platform sync" in (win.get_attribute("aria-label") or win.inner_text())
                self._shot("meeting-window-needs")

                # 2. The saved meeting's desk icon opens its current host.
                # Phone Back returns to the list, then the desk before the icon.
                if self.phone:
                    self._press(win.get_by_role("button", name=re.compile(r"^Back from ")))
                    win.get_by_test_id(f"meeting-row-{ONE}").wait_for(timeout=T)
                    self._press(win.get_by_role("button", name="Back from Meetings", exact=True))
                    self._press(page.get_by_role("button", name="Go", exact=True))
                    self._press(page.locator(".desk-menu-list").get_by_role("menuitem", name="Meetings", exact=True))
                    self._press(win.locator(f"[data-testid='meeting-row-{ONE}'] .meetings-stream-row-body"))
                else:
                    self._open_icon(f"meeting:{ONE}")
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

                # 5. (Betterment P3) The Room's FILES fold left the Now wing
                # (parked in web/src/features/project-room/_parked/nowWingFolds.tsx);
                # the hub half of "park from Files" stays in
                # tests/integration/test_desk_project_room.py.
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("stop", ["window", "orb"])
    @pytest.mark.parametrize("width", [1440])
    def test_record_then_stop_keeps_the_same_window(self, width: int, stop: str) -> None:
        """replaces: tests/e2e/test_philo17_meeting_window_glass.py::TestOneMeetingOneWindow::test_record_then_stop_keeps_the_same_window
        (1440; the 393 run differed only in taps). T2 owed: the live room turning
        into the record in one window wants the desk rendered over a recorded
        start/stop pair."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._press(page.get_by_role("button", name="Record a meeting"))
                wid = "surface-meetings"
                win = page.locator(f"[id='{wid}']")
                win.wait_for(timeout=T)
                # The live room in the meeting's own window (the hub says live).
                win.get_by_role("button", name="Stop meeting").wait_for(timeout=T)
                self._shot(f"meeting-window-live-{stop}")
                if stop == "window":
                    self._press(win.get_by_role("button", name="Stop meeting"))
                else:
                    self._press(page.get_by_role("button", name="Stop recording"))
                # The SAME window shows the saved record, its final transcript,
                # and stays the record (a late live reply never brings the room back).
                win.get_by_role("button", name="More actions", exact=True).wait_for(timeout=T)
                win.get_by_text("We move the cutover to Friday.").first.wait_for(timeout=T)
                page.wait_for_timeout(2500)
                assert win.get_by_role("button", name="Stop meeting").count() == 0
                ids = page.evaluate("() => [...document.querySelectorAll('#surface-meetings, [id^=\"pullout:meeting:\"]')].map((w) => w.id)")
                assert ids == [wid], ids
                assert page.locator("#surface-live").count() == 0
                rows = [r for r in self._hub_rows() if r["id"] == wid or r["id"].startswith("pullout:meeting:")]
                assert [r["id"] for r in rows] == [wid] and rows[0]["front"], rows
                assert rows[0]["object_ref"] == f"meeting:{LIVE}", rows
                # A reload keeps the record (the hub is idle; nothing reads live).
                page.reload(wait_until="load")
                _normal_chair(page)
                win.get_by_role("button", name="More actions", exact=True).wait_for(timeout=T)
                assert win.get_by_role("button", name="Stop meeting").count() == 0
                self._shot(f"meeting-window-stopped-{stop}")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440])
    def test_a_saved_meetings_window_migrates_on_the_hub(self, width: int) -> None:
        """replaces: tests/e2e/test_philo17_meeting_window_glass.py::TestOneMeetingOneWindow::test_a_saved_meetings_window_migrates_on_the_hub
        (1440; three views of one hub).

        Astra r1: the hub's row of a Meetings window scoped to a meeting (and
        a bare `pullout:<id>` row) migrates to the meeting's one window, once;
        closed, it does not come back; two views agree."""
        from playwright.sync_api import sync_playwright

        _http(self.base, "POST", "/api/desk/windows/surface-meetings/open", {"object_ref": f"meeting:{ONE}"})
        _http(self.base, "POST", f"/api/desk/windows/pullout:{ONE}/open", {})
        wid = "surface-meetings"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.locator(f"[id='{wid}']").wait_for(timeout=T)
                for _ in range(40):
                    ids = self._hub_ids()
                    if wid in ids and f"pullout:meeting:{ONE}" not in ids and f"pullout:{ONE}" not in ids:
                        break
                    page.wait_for_timeout(250)
                assert ids.count(wid) == 1 and f"pullout:meeting:{ONE}" not in ids and f"pullout:{ONE}" not in ids, ids
                assert next(row for row in self._hub_rows() if row["id"] == wid)["object_ref"] == f"meeting:{ONE}"
                assert page.locator("[id^='pullout:meeting:']").count() == 0
                assert page.locator(f"[id='pullout:{ONE}']").count() == 0
                # A second view (no cache) shows the same desk.
                other = browser.new_context(viewport={"width": width, "height": SIZES[width]}).new_page()
                other.goto(f"{self.base}/?token={MW_TOKEN}", wait_until="load")
                _normal_chair(other)
                other.locator(f"[id='{wid}']").wait_for(state="attached", timeout=T)
                assert other.locator("[id^='pullout:meeting:']").count() == 0
                # Closed, it stays closed after a reload, in both views.
                self._press(page.locator("#surface-meetings").get_by_role("button", name=re.compile(r"^Close (Platform sync|Meetings)$")))
                for _ in range(40):
                    if wid not in self._hub_ids():
                        break
                    page.wait_for_timeout(250)
                assert wid not in self._hub_ids(), self._hub_ids()
                for view in (page, other):
                    view.reload(wait_until="load")
                    _normal_chair(view)
                    view.wait_for_timeout(1500)
                    assert view.locator(f"[id='{wid}']").count() == 0
                    assert view.locator("#surface-meetings").count() == 0
                assert not [i for i in self._hub_ids() if "meeting" in i or i == f"pullout:{ONE}"], self._hub_ids()
                # Astra r2: a THIRD view boots with the OLD cache (the scoped
                # Meetings window it had before the migration). The hub holds no
                # window for the meeting: the cached window closes, and no new
                # hub row is written.
                old = json.dumps({
                    "version": 1,
                    "windowsById": {"surface-meetings": {
                        "id": "surface-meetings", "kind": "surface", "applicationKey": "review-meetings",
                        "scope": f"meeting:{ONE}", "persistence": "workspace"}},
                    "panel": {"rects": {}, "order": ["surface-meetings"], "max": []},
                    "zoneWindows": [], "zoneViewPrefs": {},
                })
                third_ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]})
                third_ctx.add_init_script(
                    "if (!sessionStorage.getItem('p17-old-cache')) { sessionStorage.setItem('p17-old-cache', '1');"
                    f" localStorage.setItem('hs.desk.workspace.v1', {json.dumps(old)}); }}")
                third = third_ctx.new_page()
                third.goto(f"{self.base}/?token={MW_TOKEN}", wait_until="load")
                _normal_chair(third)
                third.wait_for_timeout(2500)
                assert third.locator(f"[id='{wid}']").count() == 0
                assert third.locator("#surface-meetings").count() == 0
                assert not [i for i in self._hub_ids() if "meeting" in i], self._hub_ids()
                assert not errors, errors
            finally:
                browser.close()

    # Daily work repair: the saved record is drawn without Send. Its footer
    # opens Send on request; the built-in folder then reads a real preview
    # (released after the pending assertion). The well receives focus after
    # that real read completes.
    _HOLD_PREVIEW_JS = """(() => {
      window.__preview = {asked: 0, done: null};
      const gate = new Promise((resolve) => { window.__releasePreview = resolve; });
      const f = window.fetch.bind(window);
      window.fetch = (input, init) => {
        const u = typeof input === 'string' ? input : (input && input.url) || '';
        if (!u.includes('/api/channels/preview')) return f(input, init);
        window.__preview.asked += 1;
        return gate.then(() => f(input, init))
          .finally(() => { window.__preview.done = performance.now(); });
      };
    })()"""
    _WATCH_JS = """([id, ms]) => new Promise((resolve) => {
      const t0 = performance.now(); let shownAt = null; const first = new Map(); let worst = [];
      const tick = () => {
        const w = document.getElementById(id);
        const decide = w && w.querySelector('[data-testid=meeting-decide]');
        if (w && decide && !w.querySelector('[data-settling]')) {
          if (shownAt === null) shownAt = performance.now();
          const limit = decide.getBoundingClientRect().bottom;
          for (const el of w.querySelectorAll('button, [role=button], [data-testid], input, textarea')) {
            const r = el.getBoundingClientRect();
            if (!r.width || !r.height || r.top > limit) continue;
            if (!first.has(el)) { first.set(el, [r.left, r.top]); continue; }
            const [x, y] = first.get(el); const d = Math.max(Math.abs(r.left - x), Math.abs(r.top - y));
            if (d > 2) worst.push((el.getAttribute('data-testid') || el.textContent || '').trim().slice(0, 30) + ' ' + Math.round(d));
          }
        }
        if (performance.now() - t0 < ms) requestAnimationFrame(tick);
        else resolve({shownAt, previewDone: window.__preview.done, asked: window.__preview.asked, moved: [...new Set(worst)]});
      };
      requestAnimationFrame(tick);
    })"""

    @pytest.mark.e2e
    @pytest.mark.timeout(300)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_meeting_with_a_summary_holds_still_while_its_send_preview_lands(self, width: int) -> None:
        """replaces: tests/e2e/test_philo17_meeting_window_glass.py::TestOneMeetingOneWindow::test_a_meeting_with_a_summary_holds_still_while_its_send_preview_lands
        Updated for requested Send: absent on first open, no send before the
        held preview, focus inside its existing well when ready."""
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

        mid = "m-sum"
        start = (datetime.now() - timedelta(hours=1)).replace(microsecond=0)
        get_database().meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger sync",
            segments=[TranscriptSegment(text="We move the cutover to Friday.", speaker="Me", start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["cutover"], summary="The cutover moves to Friday.", action_items=[]),
            intel_status="completed"))
        wid = "surface-meetings"
        _http(self.base, "POST", f"/api/desk/windows/{urllib.request.quote(wid, safe='')}/open", {"object_ref": f"meeting:{mid}"})
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                          has_touch=width < 720, reduced_motion="reduce")
                page = ctx.new_page()
                page.add_init_script(self._HOLD_PREVIEW_JS)
                page.goto(f"{self.base}/?token={MW_TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator(f"[id='{wid}']").wait_for(timeout=T)
                win = page.locator(f"[id='{wid}']")
                page.wait_for_function("id => { const w=document.getElementById(id); return w && !w.querySelector('[data-settling]'); }", arg=wid, timeout=T)
                assert win.get_by_test_id("meeting-send-well").count() == 0
                assert page.evaluate("window.__preview.asked") == 0
                page.screenshot(path=str(MW_SHOTS / f"summary-meeting-closed-{width}.png"))
                win.get_by_test_id("meeting-send").click()
                win.get_by_test_id("meeting-send-well").wait_for(timeout=T)
                page.wait_for_function("() => window.__preview.asked >= 1", timeout=T)
                assert win.get_by_test_id("send-verb").count() == 0
                page.screenshot(path=str(MW_SHOTS / f"summary-meeting-preview-pending-{width}.png"))
                page.evaluate("window.__releasePreview()")
                page.wait_for_function("() => window.__preview.done !== null", timeout=T)
                win.get_by_test_id("send-preview").wait_for(timeout=T)
                page.wait_for_function("() => { const well=document.querySelector('[data-testid=meeting-send-well]'); return well && well.contains(document.activeElement); }", timeout=T)
                page.screenshot(path=str(MW_SHOTS / f"summary-meeting-preview-held-{width}.png"))
                seen = page.evaluate("window.__preview")
            finally:
                browser.close()
        assert seen["asked"] >= 1, f"requested Send read no preview: {seen}"
        assert seen["done"] is not None, f"requested preview did not finish: {seen}"
