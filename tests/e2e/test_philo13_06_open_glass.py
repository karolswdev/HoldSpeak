"""PHILO-13-06 (B1) -- ONE OPEN GRAMMAR, walked on glass.

The owner's fork 2 (2026-10-01): "Opens its own window". Every named row
opens its object in its own window. Through the real hub on an isolated
HOME, at 1440x900 (mouse) and 393x852 (touch), seeded with the canvas week
(Avery, Sam, Jordan, Priya; meetings; decisions; the brief) and a calendar,
all minted through the real producers: the Chair glass seed
(test_philo13_11_chair_glass._seed), the People routes (Priya's request,
accepted; the 1:1 series linked to Priya, people.py:193-204), an ICS file in
this HOME through PUT /api/settings and the real ingest conductor, the
calendar link route (the sync event to its Room), and POST
/api/brief/generate after the week exists.

J1 (the morning) walked end to end, one gesture per press or tap:
  1. Brief window: the brief row `Review decision: ...` -> that decision's window.
  2. Needs you window: Priya's commitment row -> People on Priya.
  3. The week window: `1:1 Priya / Karol` -> People on Priya, on Prep.
A dead tap is a press after which the object it names is not the front
window. J3 prep: from a fresh Chair, the 1:1 row alone -> Priya on Prep.

At 393 one Chair window shows at a time (PHILO-13-11, C1-6a): reaching the
Brief and The week windows takes Go > Chair > <window>. Those frame taps are
counted apart from the row taps and reported as they are; the open grammar
is fenced on the row taps (0 dead, one tap per open).

Shots go to pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-06-shots/
under HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_chair_glass import _seed as _canvas_seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the open-grammar glass needs Playwright")

TOKEN = "philo13-06-open"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-06-shots")
SIZES = {1440: 900, 393: 852}
COMMITMENT = "Review the rollout plan before Friday"
ONE_ON_ONE = "1:1 Priya / Karol"


def _http(base: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"authorization": f"Bearer {TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}


def _seed(home: Path, base: str) -> dict[str, Any]:
    """The canvas week, then the calendar and Priya's request (real producers)."""
    _canvas_seed(home)
    _http(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    people = {r["display_name"]: r["id"] for r in _http(base, "GET", "/api/people/relationships")["relationships"]}
    priya = people["Priya Nair"]
    req = _http(base, "POST", f"/api/people/relationships/{priya}/requests", {"body": COMMITMENT})["request"]
    _http(base, "POST", f"/api/people/requests/{req['id']}/accept", {})

    utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//PHILO13-06//EN"]
    for uid, starts, mins, title in (
        ("p13-06-1on1", utc + timedelta(minutes=50), 30, ONE_ON_ONE),
        ("p13-06-sync", utc + timedelta(minutes=110), 45, "Ledger cutover sync"),
    ):
        lines += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}",
                  f"DTEND:{(starts + timedelta(minutes=mins)).strftime('%Y%m%dT%H%M%SZ')}",
                  f"SUMMARY:{title}", "END:VEVENT"]
    lines += ["END:VCALENDAR", ""]
    ics = home / "week.ics"
    ics.write_text("\r\n".join(lines), encoding="utf-8")
    _http(base, "PUT", "/api/settings",
          {"calendar": {"sources": [{"id": "p13-06-week", "label": "Work", "url": str(ics), "enabled": True}]}})
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
    assert CalendarIngestConductor().refresh() is True
    events = {e["title"]: e for e in _http(base, "GET", "/api/calendar/events")["events"]}
    _http(base, "POST", f"/api/calendar/events/{events['Ledger cutover sync']['id']}/link", {"project_id": "p-ledger"})
    _http(base, "POST", f"/api/people/relationships/{priya}/calendar-links",
          {"uid": "p13-06-1on1", "source_id": "p13-06-week", "label": ONE_ON_ONE})
    brief = _http(base, "POST", "/api/brief/generate", {})
    decisions = [i for i in (brief.get("sections") or {}).get("decisions", []) if i["text"].startswith("Review decision:")]
    assert decisions, "the brief carries a decision to review"
    return {"priya": priya, "decision_row": decisions[0]["text"],
            "decision_title": decisions[0]["text"].split(": ", 1)[1]}


WINDOWS_JS = r"""() => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
  .filter((w) => { const r = w.getBoundingClientRect(); const cs = getComputedStyle(w);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; })
  .map((w) => ({title: (w.getAttribute('aria-label') || '').trim(), front: w.classList.contains('is-front'),
    text: (w.innerText || '').replace(/\s+/g, ' ').slice(0, 400)}))
  .filter((w, i, all) => w.title && all.findIndex((x) => x.title === w.title) === i)"""


class TestOneOpenGrammar:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.home = tmp_path / "home"
        self.base = base
        self.ids = _seed(self.home, base)
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=15_000)
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
            loc.click(timeout=8_000)

    def _chair_window(self, page: Any, width: int, name: str, walk: dict[str, Any]) -> None:
        """At 393, Go > Chair > <name> (three frame taps); at 1440 the window stands."""
        shell = page.locator(f".desk-window-shell[aria-label='{name}']")
        if width > 720 or (shell.count() and shell.first.is_visible() and
                           shell.first.evaluate("e => e.classList.contains('is-front')")):
            return
        for loc in (
            page.locator(".desk-verbbar-item[data-menu-id='go'] button"),
            page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')"),
            page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"),
        ):
            loc.first.wait_for()
            self._press(page, loc.first, width)
            page.wait_for_timeout(250)
            walk["frame_taps"] += 1
        shell.wait_for()
        _settle(page)

    def _open(self, page: Any, width: int, row: Any, expect_title: str, expect_text: str,
              what: str, walk: dict[str, Any]) -> dict[str, Any]:
        """One row gesture; dead unless the named object is the front window."""
        before = page.evaluate(WINDOWS_JS)
        self._press(page, row, width)
        try:
            page.wait_for_function(
                """([title, text]) => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
                    .some((w) => w.classList.contains('is-front') && (w.getAttribute('aria-label') || '').includes(title)
                      && (w.innerText || '').includes(text))""",
                arg=[expect_title, expect_text], timeout=8_000)
        except Exception:  # noqa: BLE001 -- recorded as a dead tap below
            pass
        page.wait_for_timeout(500)
        _settle(page)
        after = page.evaluate(WINDOWS_JS)
        front = [w for w in after if w["front"]]
        ok = any(expect_title in w["title"] and expect_text in w["text"] for w in front)
        step = {"what": what, "dead": not ok, "front": [w["title"] for w in front],
                "opened": [w["title"] for w in after if w["title"] not in {b["title"] for b in before}]}
        walk["row_taps"] += 1
        walk["dead"] += 0 if ok else 1
        walk["steps"].append(step)
        return step

    @staticmethod
    def _lens(page: Any) -> str | None:
        return page.evaluate("""() => { const t = document.querySelector('.people-lenses [role=tab][aria-selected=true]');
            return t ? t.textContent.trim() : null; }""")

    @pytest.mark.parametrize("width", [1440, 393])
    def test_j1_and_j3_open_in_their_own_windows(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        walk: dict[str, Any] = {"width": width, "touch": width < 720, "row_taps": 0, "frame_taps": 0,
                                "dead": 0, "steps": []}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.screenshot(path=str(SHOTS / f"B1-00-chair-{width}.png"))
                # 1. the brief row -> its decision
                self._chair_window(page, width, "Brief", walk)
                brief_row = page.locator("[data-testid='arrival-brief-row']", has_text=self.ids["decision_title"]).first
                assert brief_row.get_attribute("role") == "button", "the brief row offers its open"
                self._open(page, width, brief_row, self.ids["decision_title"], self.ids["decision_title"],
                           "brief row -> the decision", walk)
                page.screenshot(path=str(SHOTS / f"B1-01-brief-row-decision-{width}.png"))

                # 2. Priya's commitment row -> People on Priya
                self._chair_window(page, width, "Needs you", walk)
                commitment = page.locator(".desk-window-shell[aria-label='Needs you'] .surface-ledger-line",
                                          has_text=COMMITMENT).first
                self._open(page, width, commitment, "People", "Priya Nair", "commitment row -> its person", walk)
                page.screenshot(path=str(SHOTS / f"B1-02-commitment-person-{width}.png"))

                # 3. the 1:1 row -> Priya on Prep
                self._chair_window(page, width, "The week", walk)
                one = page.locator("[data-testid='arrival-meeting-row']", has_text=ONE_ON_ONE).first
                self._open(page, width, one, "People", "Priya Nair", "1:1 row -> Priya on Prep", walk)
                walk["lens_after_1on1"] = self._lens(page)
                walk["j1_gestures"] = walk["row_taps"] + walk["frame_taps"]
                page.screenshot(path=str(SHOTS / f"B1-03-one-on-one-prep-{width}.png"))

                # The sync row's Room: the event linked to its project opens the Room.
                self._chair_window(page, width, "The week", walk)
                sync = page.locator("[data-testid='arrival-meeting-row']", has_text="Ledger cutover sync").first
                # (at 393 the Room's head carries its wings, not its name: the title is the proof)
                room = self._open(page, width, sync, "Payments ledger cutover", "",
                                  "calendar row -> its Room", walk)
                walk["room_step"] = room
                page.screenshot(path=str(SHOTS / f"B1-04-calendar-room-{width}.png"))

                # J3 prep: a fresh browser (no remembered windows), the 1:1 row alone
                fresh_browser, fresh, fresh_errors = self._page(pw, width)
                try:
                    j3: dict[str, Any] = {"row_taps": 0, "frame_taps": 0, "dead": 0, "steps": [],
                                          "windows_before": [w["title"] for w in fresh.evaluate(WINDOWS_JS)]}
                    self._chair_window(fresh, width, "The week", j3)
                    one = fresh.locator("[data-testid='arrival-meeting-row']", has_text=ONE_ON_ONE).first
                    self._open(fresh, width, one, "People", "Priya Nair", "J3: 1:1 row -> Priya on Prep", j3)
                    j3["lens"] = self._lens(fresh)
                    walk["j3"] = j3
                    fresh.screenshot(path=str(SHOTS / f"B1-05-j3-prep-{width}.png"))
                    errors.extend(fresh_errors)
                finally:
                    fresh_browser.close()

                # Intelligence BRIEF: the row opens; Open person opens People on Priya
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                intel = page.locator(".desk-dock-launch[aria-label^='Intelligence']")
                if intel.count():
                    self._press(page, intel.first, width)
                else:  # the Dock names it differently on this frame: the palette verb
                    page.keyboard.press("Meta+K")
                    page.keyboard.type("Intelligence")
                    page.keyboard.press("Enter")
                page.locator("[data-testid='brief-lookback-rows'], [data-testid='person-sections']").first.wait_for()
                walk["intel_people"] = page.locator("[data-testid='person-sections']").count()
                sf = page.locator("[data-testid='brief-sf-row'] .intelligence-brief-sf-primary",
                                  has_text=self.ids["decision_title"]).first
                ib: dict[str, Any] = {"row_taps": 0, "frame_taps": 0, "dead": 0, "steps": []}
                self._open(page, width, sf, self.ids["decision_title"], self.ids["decision_title"],
                           "Intelligence BRIEF row -> the decision", ib)
                walk["intelligence"] = ib
                walk["intel_footer"] = page.evaluate("""() => { const f = [...document.querySelectorAll('.desk-pullout')]
                    .find((w) => (w.getAttribute('aria-label') || '').includes('Intelligence'));
                    const r = f && f.querySelector('.surface-footer-receipt, [data-testid=surface-footer-receipt]');
                    return r ? r.textContent.trim() : (f ? (f.innerText.match(/SELECTED[^\\n]*/) || [null])[0] : null); }""")
                page.screenshot(path=str(SHOTS / f"B1-06-intelligence-brief-row-{width}.png"))

                # Brief -> People: select a person, Open person -> People on that relationship
                if width < 720:  # one window at a time: close the decision to see Intelligence again
                    close = page.locator(f".desk-pullout[aria-label*='{self.ids['decision_title'][:20]}'] "
                                         "[aria-label^='Close ']").first
                    self._press(page, close, width)
                    walk["frame_taps"] += 1
                    page.wait_for_timeout(600)
                person = page.locator("[data-testid^='person-row-']", has_text="Avery Chen").first
                self._press(page, person, width)
                page.locator("[data-testid='verb-open-person']").wait_for()
                bp: dict[str, Any] = {"row_taps": 0, "frame_taps": 0, "dead": 0, "steps": []}
                self._open(page, width, page.locator("[data-testid='verb-open-person']").first,
                           "People", "Avery Chen", "Brief -> Open person", bp)
                walk["brief_people"] = bp
                page.screenshot(path=str(SHOTS / f"B1-07-brief-open-person-{width}.png"))
            finally:
                facts = {**walk, "errors": errors}
                (SHOTS / f"B1-walk-{width}.json").write_text(json.dumps(facts, indent=1))
                browser.close()

        print(json.dumps(walk, indent=1))
        fails: dict[str, Any] = {}
        if walk["dead"]:
            fails["J1 dead taps 0"] = [s for s in walk["steps"] if s["dead"]]
        j1_rows = [s for s in walk["steps"] if s["what"] != "calendar row -> its Room"]
        if len(j1_rows) != 3:
            fails["J1 three row gestures"] = j1_rows
        if width > 720 and walk.get("j1_gestures", 99) > 3:
            fails["J1 <= 3 gestures at 1440"] = walk.get("j1_gestures")
        if walk.get("lens_after_1on1") != "Prep":
            fails["the 1:1 opens Prep"] = walk.get("lens_after_1on1")
        j3 = walk.get("j3") or {}
        if j3.get("dead") or j3.get("row_taps") != 1 or j3.get("lens") != "Prep":
            fails["J3 prep 1 gesture"] = j3
        if (walk.get("brief_people") or {}).get("dead", 1):
            fails["Brief -> Open person opens People on that relationship"] = walk.get("brief_people")
        if (walk.get("intelligence") or {}).get("dead", 1):
            fails["Intelligence BRIEF row opens"] = walk.get("intelligence")
        assert not fails, json.dumps(fails, indent=1)
