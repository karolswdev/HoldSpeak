"""PHILO-17 (owner 2026-10-10, "A meeting opens in one window") -- on glass.

Through the real hub on an isolated HOME, at 1440x900 and 393x852:

* One meeting, five doors: the Needs-you row, the desk icon, the ⌘K hit
  (the Search tap at 393), the Meetings list row, and (once it is filed in
  a Project) the Room's FILES row. Each meeting opens in its own
  window, ``pullout:meeting:<id>``: after every door there is exactly ONE
  such window on the glass and on the hub, and it is the front window (the
  second door brings it to the front; it never opens twice). The Meetings
  window is the list: it holds no record. The hub holds the window as the
  FRONT window; no bare `pullout:<id>` form exists.
* A saved Meetings window scoped to a meeting (and a bare `pullout:<id>`
  row) migrates on the hub to the meeting's one window; closed, it stays
  closed after a reload, in two views.
* Record -> Stop (the window's own Stop and the orb) keeps the same window: the Record orb opens the new
  meeting's window on the live room; Stop turns the SAME window
  (``pullout:meeting:<id>``) into the saved record. The capture device is
  the one stand-in: ``on_start`` / ``on_stop`` answer in place of a
  microphone, and the stop saves the meeting through the real producer.
* A summary that finishes while its meeting is open (the hub's
  ``aftercare_ready``) lands in that meeting's window: at 393 the meeting
  sheet stays the visible front; Capture never takes it (the owner's bug:
  after Import the meeting he opened hid behind Capture).
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
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN, on_start=capture.start, on_stop=capture.stop,
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
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
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
        wid = f"pullout:meeting:{meeting_id}"
        page = self.page
        page.wait_for_function(
            "(id) => { const w = document.getElementById(id); return !!w && w.classList.contains('is-front'); }",
            arg=wid, timeout=T)
        on_glass = page.evaluate(
            "() => [...document.querySelectorAll('[id^=\"pullout:meeting:\"]')].map((w) => w.id)")
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
                self._open_icon("drawer:needs")
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

                # 5. The SAME meeting, filed in a Project now: the Room's FILES
                # row fronts its one window.
                _http(self.base, "POST", f"/api/projects/{PROJECT}/meetings/{ONE}", {})
                self._palette("Payments ledger cutover")
                self._press(page.locator("#desk-palette-listbox [role=option]", has_text="Payments ledger cutover"))
                files = page.locator("#surface-project-memory [data-testid=room-files]")
                files.wait_for(timeout=T)
                self._press(files.get_by_text("Platform sync").first)
                self._press(files.locator("[data-testid=room-files-open]"))
                self._one_front(ONE, "room")
                self._shot("meeting-window-room")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("stop", ["window", "orb"])
    @pytest.mark.parametrize("width", list(SIZES))
    def test_record_then_stop_keeps_the_same_window(self, width: int, stop: str) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._press(page.get_by_role("button", name="Record a meeting"))
                wid = f"pullout:meeting:{LIVE}"
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
                win.get_by_role("button", name="Open transcript").wait_for(timeout=T)
                win.get_by_text("We move the cutover to Friday.").first.wait_for(timeout=T)
                page.wait_for_timeout(2500)
                assert win.get_by_role("button", name="Stop meeting").count() == 0
                ids = page.evaluate("() => [...document.querySelectorAll('[id^=\"pullout:meeting:\"]')].map((w) => w.id)")
                assert ids == [wid], ids
                assert page.locator("#surface-live").count() == 0
                rows = [r for r in self._hub_rows() if r["id"].startswith("pullout:meeting:")]
                assert [r["id"] for r in rows] == [wid] and rows[0]["front"], rows
                # A reload keeps the record (the hub is idle; nothing reads live).
                page.reload(wait_until="load")
                _normal_chair(page)
                win.get_by_role("button", name="Open transcript").wait_for(timeout=T)
                assert win.get_by_role("button", name="Stop meeting").count() == 0
                self._shot(f"meeting-window-stopped-{stop}")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_saved_meetings_window_migrates_on_the_hub(self, width: int) -> None:
        """Astra r1: the hub's row of a Meetings window scoped to a meeting (and
        a bare `pullout:<id>` row) migrates to the meeting's one window, once;
        closed, it does not come back; two views agree."""
        from playwright.sync_api import sync_playwright

        _http(self.base, "POST", "/api/desk/windows/surface-meetings/open", {"object_ref": f"meeting:{ONE}"})
        _http(self.base, "POST", f"/api/desk/windows/pullout:{ONE}/open", {})
        wid = f"pullout:meeting:{ONE}"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.locator(f"[id='{wid}']").wait_for(timeout=T)
                for _ in range(40):
                    ids = self._hub_ids()
                    if wid in ids and "surface-meetings" not in ids and f"pullout:{ONE}" not in ids:
                        break
                    page.wait_for_timeout(250)
                assert wid in ids and "surface-meetings" not in ids and f"pullout:{ONE}" not in ids, ids
                assert page.locator("#surface-meetings").count() == 0
                assert page.locator(f"[id='pullout:{ONE}']").count() == 0
                # A second view (no cache) shows the same desk.
                other = browser.new_context(viewport={"width": width, "height": SIZES[width]}).new_page()
                other.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(other)
                other.locator(f"[id='{wid}']").wait_for(state="attached", timeout=T)
                assert other.locator("#surface-meetings").count() == 0
                # Closed, it stays closed after a reload, in both views.
                self._press(page.get_by_role("button", name=re.compile(r"^Close Platform sync")))
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
                third.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(third)
                third.wait_for_timeout(2500)
                assert third.locator(f"[id='{wid}']").count() == 0
                assert third.locator("#surface-meetings").count() == 0
                assert not [i for i in self._hub_ids() if "meeting" in i], self._hub_ids()
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
                self._open_icon(f"people:{self.person}")
                wid = f"pullout:people:{self.person}"
                win = page.locator(f"[id='{wid}']")
                win.locator("[data-testid=person-window]").wait_for(timeout=T)
                assert "Avery Chen" in win.inner_text()
                # PHILO-17 refit: Prep leads; Context, History and Info are the folded tabs.
                assert win.locator(".people-lenses [role=tab]").count() == 4
                # The person, not the People application (the roster).
                assert page.locator("#surface-people").count() == 0
                assert not re.search(r"\bBack\b", win.locator(".people-detail-head").inner_text())
                self._shot("person-window")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_finished_summary_keeps_the_open_meeting_in_front(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                self._open_icon(f"meeting:{ONE}")
                wid = f"pullout:meeting:{ONE}"
                self._one_front(ONE, "icon")
                # The summary finishes: the hub announces the meeting's aftercare
                # on its one bus (the queue's own frame; the run is the stand-in).
                self.server.broadcast("aftercare_ready", {
                    # The hub's own counts (this meeting has no proposals; a card
                    # that came with proposals leaves when the hub reads none).
                    "meeting_id": ONE, "title": "Platform sync", "open_total": 1, "proposal_total": 0,
                })
                page.wait_for_timeout(1500)
                state = page.evaluate("""(id) => {
                    const w = document.getElementById(id);
                    const cap = document.getElementById('chair:capture');
                    return {front: !!w && w.classList.contains('is-front'),
                            shown: !!w && getComputedStyle(w).display !== 'none' && w.checkVisibility(),
                            captureFront: !!cap && cap.classList.contains('is-front')};
                }""", wid)
                assert state == {"front": True, "shown": True, "captureFront": False}, f"{width}: {state}"
                # The card itself landed in the meeting window's own seat.
                seat = page.locator(f"[id='{wid}'] [data-aftercare-window-slot='top']")
                page.wait_for_function(
                    "(id) => (document.getElementById(id)?.querySelector('[data-aftercare-window-slot=\"top\"]')?.innerText || '').includes('Platform sync')",
                    arg=wid, timeout=T)
                assert "Platform sync" in seat.inner_text()
                self._shot("meeting-window-aftercare")
                assert not errors, errors
            finally:
                browser.close()

    # PHILO-17 (the desk sweep; Astra r1 on #1108): a recorded meeting WITH a
    # summary draws its Send well, and the well picks the built-in folder on
    # its own and reads its preview. The record's body is drawn only once that
    # preview has landed (held 2 s here): nothing above Decide moves after.
    _HOLD_PREVIEW_JS = """(() => {
      window.__preview = {asked: 0, done: null};
      const f = window.fetch.bind(window);
      window.fetch = (input, init) => {
        const u = typeof input === 'string' ? input : (input && input.url) || '';
        if (!u.includes('/api/channels/preview')) return f(input, init);
        window.__preview.asked += 1;
        return new Promise((r) => setTimeout(r, 2000)).then(() => f(input, init))
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
        wid = f"pullout:meeting:{mid}"
        _http(self.base, "POST", f"/api/desk/windows/{urllib.request.quote(wid, safe='')}/open", {})
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                          has_touch=width < 720, reduced_motion="reduce")
                page = ctx.new_page()
                page.add_init_script(self._HOLD_PREVIEW_JS)
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator(f"[id='{wid}']").wait_for(timeout=T)
                seen = page.evaluate(self._WATCH_JS, [wid, 6000])
                page.screenshot(path=str(SHOTS / f"summary-meeting-preview-held-{width}.png"))
            finally:
                browser.close()
        assert seen["asked"] >= 1, f"the well picked no destination on its own: {seen}"
        assert seen["shownAt"] is not None, f"the record body was never drawn: {seen}"
        assert seen["previewDone"] is not None and seen["shownAt"] >= seen["previewDone"] - 50, (
            f"the body was drawn before its Send preview landed: {seen}")
        assert not seen["moved"], f"rows above Decide moved after the body was drawn: {seen}"
