"""PHILO-13-09 (B4-W) -- THE 1:1 FINDS ITS PERSON, walked on glass.

A real hub on an isolated HOME, at 1440x900 (mouse) and 393x852 (touch).
Every record comes from a real producer, through Astra's H-B4 fixture
(``scripts/philo13_b4_fixture.py``): the ICS calendar ingest conductor,
``save_meeting`` with an action owned by Priya's alias, the encrypted People
store with a FILE key in this HOME, the People routes and ProjectService. The
hub's own Config then names the same ICS source (PUT /api/settings), and the
real conductor re-ingests it with the 1:1 inside this week.

The walk, per width (the browser in America/Denver):
  0. The brief route fails once (503): the Now side names it
     (`NEXT 1:1 DID NOT LOAD · NOT AVAILABLE NOW`) with Try again, never
     "No 1:1 planned"; Try again shows the suggestion.
  1. People on Priya, Prep: the calendar suggestion; nothing is linked yet
     (the custody rule). His press on `Link this 1:1` links it; then
     `NEXT 1:1 · <formatted time>` shows.
  2. Now: the Next 1:1 side section reads as the header does; no ISO time.
  3. A fresh Chair: the 1:1 row alone -> Priya on Prep (1 gesture).
  4. Prep: the agenda, `Waiting on Priya` with the owed action, her project;
     nothing clipped or overlapping.
  5. The owed action row -> its meeting, the front window.

Shots go to pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-09-shots/
under HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _assert_clean, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the B4 Prep glass needs Playwright")

TOKEN = "philo13-09-prep"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-09-shots")
SIZES = {1440: 900, 393: 852}
ISO = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
OWED = "Send the dry-run report"
DUE = "2026-10-06"  # a Tuesday; the desk below runs in America/Denver
DESK_ZONE = "America/Denver"


def _http(base: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"authorization": f"Bearer {TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}


def _seed(root: Path, base: str) -> dict[str, Any]:
    """Astra's B4 fixture on the hub's own database, then the hub's Config
    and a re-ingest inside this week.

    ``root`` is the run's tmp directory: the hub's database
    (``root/holdspeak.db``, glass_infra._boot) and the FILE People key
    (``root/people.key``) both live under it, so the fixture's isolation
    guard (the database below its HOME) holds with HOME = ``root``.
    """
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
    from scripts import philo13_b4_fixture as b4

    seeded = b4.seed_people_prep(root / "holdspeak.db", home=root)
    _http(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    ics = root / "philo13-b4-calendar.ics"
    b4._ics(ics, datetime.now(timezone.utc).replace(second=0, microsecond=0) + timedelta(minutes=50))
    _http(base, "PUT", "/api/settings", {"calendar": {"sources": [
        {"id": b4.EVENT_SOURCE_ID, "label": "B4 calendar", "url": str(ics), "enabled": True}]}})
    assert CalendarIngestConductor().refresh() is True
    rid = seeded["ids"]["relationship_id"]
    rel = _http(base, "GET", f"/api/people/relationships/{rid}")["relationship"]
    assert not rel.get("calendar_links"), "the fixture links nothing: a suggestion is his to confirm"
    brief = _http(base, "GET", f"/api/people/relationships/{rid}/brief")["brief"]
    assert [s["title"] for s in brief["calendar_link_suggestions"]] == [b4.EVENT_TITLE]
    assert [a["task"] for a in brief["open_meeting_actions"]] == [OWED]
    # Astra's B4-W condition 2: the fixture's owned action carries no deadline
    # (due=None). The real `Set a date` producer (follow_through_service,
    # verb "due") gives it a calendar day, stored as `YYYY-MM-DD`.
    _http(base, "POST", "/api/follow-through/complete",
          {"card_id": b4.ACTION_ID, "verb": "due", "payload": {"due": DUE}})
    brief = _http(base, "GET", f"/api/people/relationships/{rid}/brief")["brief"]
    assert [a["due"] for a in brief["open_meeting_actions"]] == [DUE]
    return {"rid": rid, "title": b4.EVENT_TITLE, "project": "B4 Dry-run project", "meeting_id": b4.MEETING_ID}


WINDOWS_JS = r"""() => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
  .filter((w) => { const r = w.getBoundingClientRect(); const cs = getComputedStyle(w);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.05; })
  .map((w) => ({title: (w.getAttribute('aria-label') || '').trim(), front: w.classList.contains('is-front'),
    text: (w.innerText || '').replace(/\s+/g, ' ').slice(0, 600)}))
  .filter((w, i, all) => w.title && all.findIndex((x) => x.title === w.title) === i)"""


class TestOneOnOneFindsItsPerson:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.ids = _seed(tmp_path, base)
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720, is_mobile=False,
                                  timezone_id=DESK_ZONE)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
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

    def _palette(self, page: Any, query: str, option: str, width: int) -> None:
        self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
        page.locator("[aria-controls=desk-palette-listbox]").fill(query)
        opt = page.locator(f"[id='desk-palette-option-{option}']")
        opt.wait_for(timeout=8_000)
        self._press(page, opt, width)

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

    @staticmethod
    def _lens(page: Any) -> str | None:
        return page.evaluate("""() => { const t = document.querySelector('.people-lenses [role=tab][aria-selected=true]');
            return t ? t.textContent.trim() : null; }""")

    @staticmethod
    def _front(page: Any) -> list[dict[str, Any]]:
        return [w for w in page.evaluate(WINDOWS_JS) if w["front"]]

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_one_on_one_finds_its_person(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        walk: dict[str, Any] = {"width": width, "touch": width < 720, "frame_taps": 0}
        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # 1. People on Priya, Prep: the suggestion; Link this 1:1 on his press.
                self._palette(page, "people", "desk.open-people", width)
                people = page.locator("#surface-people")
                # Astra's B4-W condition 1: the brief route fails once (503);
                # the Now side names the failure; Try again shows the suggestion.
                fail_once = {"left": 1}

                def _brief_503(route: Any) -> None:
                    if fail_once["left"] > 0:
                        fail_once["left"] -= 1
                        route.fulfill(status=503, body='{"detail":"people_plaintext_unavailable"}',
                                      content_type="application/json")
                    else:
                        route.continue_()

                page.route(re.compile(r".*/api/people/relationships/[^/]+/brief$"), _brief_503)
                self._press(page, people.locator("button").filter(has_text="Priya Sharma").first, width)
                side = people.get_by_test_id("people-next-side")
                failure = side.get_by_test_id("people-next-failure")
                failure.wait_for()
                _settle(page)
                walk["brief_failure"] = failure.inner_text()
                walk["brief_failure_side"] = side.inner_text()
                page.screenshot(path=str(SHOTS / f"B4-00-brief-failed-{width}.png"))
                self._press(page, failure.get_by_role("button", name="Try again"), width)
                side.get_by_role("button", name="Link this 1:1").wait_for()
                walk["after_retry_side"] = side.inner_text()
                page.unroute(re.compile(r".*/api/people/relationships/[^/]+/brief$"))
                self._press(page, people.get_by_role("tab", name="Prep"), width)
                suggestion = people.get_by_test_id("prep-link-suggestion")
                suggestion.wait_for()
                _settle(page)
                walk["suggestion"] = suggestion.inner_text()
                walk["header_before_link"] = people.get_by_test_id("people-next-1on1").count()
                walk["links_before_press"] = len(_http(self.base, "GET", f"/api/people/relationships/{self.ids['rid']}")
                                                 ["relationship"].get("calendar_links") or [])
                page.screenshot(path=str(SHOTS / f"B4-01-suggestion-{width}.png"))
                self._press(page, suggestion.get_by_role("button", name="Link this 1:1"), width)
                header = people.get_by_test_id("people-next-1on1")
                header.wait_for()
                suggestion.wait_for(state="detached")
                _settle(page)
                walk["header_after_link"] = header.inner_text()
                page.screenshot(path=str(SHOTS / f"B4-02-linked-next-{width}.png"))

                # 2. Now: the side section reads as the header does.
                self._press(page, people.get_by_role("tab", name="Now"), width)
                side = people.get_by_test_id("people-next-side")
                side.wait_for()
                _settle(page)
                walk["now_side"] = side.inner_text()
                walk["people_iso"] = ISO.findall(people.inner_text())
                page.screenshot(path=str(SHOTS / f"B4-03-now-next-{width}.png"))
            finally:
                browser.close()

            # 3. A fresh Chair: the 1:1 row alone -> Priya on Prep.
            browser, page, fresh_errors = self._page(pw, width)
            errors.extend(fresh_errors)
            try:
                self._chair_window(page, width, "The week", walk)
                row = page.locator("[data-testid='arrival-meeting-row']", has_text=self.ids["title"]).first
                row.wait_for()
                self._press(page, row, width)
                walk["row_taps"] = 1
                people = page.locator("#surface-people")
                people.get_by_test_id("people-prep-lens").wait_for()
                people.get_by_test_id("prep-owed").wait_for()
                page.wait_for_timeout(400)
                _settle(page)
                front = self._front(page)
                walk["front_after_row"] = [w["title"] for w in front]
                walk["lens_after_row"] = self._lens(page)

                # 4. Prep: agenda, what Priya owes, her project; readable.
                walk["agenda"] = people.get_by_test_id("prep-agenda").inner_text()
                walk["owed"] = people.get_by_test_id("prep-owed").inner_text()
                walk["projects"] = people.get_by_test_id("prep-projects").inner_text()
                walk["prep_iso"] = ISO.findall(people.inner_text())
                walk["prep_header"] = people.get_by_test_id("people-next-1on1").inner_text()
                walk["readable"] = _rendered_text_faults(page, "#surface-people")
                page.screenshot(path=str(SHOTS / f"B4-04-chair-row-prep-{width}.png"))
                # the whole Prep, scrolled, for the owner
                people.get_by_test_id("prep-projects").scroll_into_view_if_needed()
                _settle(page)
                walk["readable_scrolled"] = _rendered_text_faults(page, "#surface-people")
                page.screenshot(path=str(SHOTS / f"B4-05-prep-owed-projects-{width}.png"))

                # 5. The owed action -> its meeting, the front window.
                owed_row = people.get_by_test_id("prep-owed").get_by_role("button", name=re.compile(OWED))
                self._press(page, owed_row, width)
                try:
                    page.wait_for_function(
                        """(title) => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
                            .some((w) => w.classList.contains('is-front') && !(w.getAttribute('aria-label') || '').startsWith('People')
                              && (w.innerText || '').includes(title))""",
                        arg=self.ids["title"], timeout=10_000)
                except Exception:  # noqa: BLE001 -- recorded below
                    pass
                page.wait_for_timeout(500)
                _settle(page)
                walk["front_after_owed"] = [{"title": w["title"], "text": w["text"][:160]} for w in self._front(page)]
                page.screenshot(path=str(SHOTS / f"B4-06-owed-opens-meeting-{width}.png"))
                _assert_clean(page, errors)
            finally:
                facts = {**walk, "errors": errors}
                (SHOTS / f"B4-walk-{width}.json").write_text(json.dumps(facts, indent=1))
                browser.close()

        print(json.dumps(walk, indent=1))
        time_token = re.compile(r"^NEXT 1:1 · (TODAY|TOMORROW|[A-Z]{3}) \S")
        if self.ids["title"] not in walk.get("suggestion", "") or "Link this 1:1" not in walk.get("suggestion", ""):
            fails["the suggestion shows with Link this 1:1"] = walk.get("suggestion")
        if walk.get("header_before_link") or walk.get("links_before_press"):
            fails["a suggestion never links by itself"] = [walk.get("header_before_link"), walk.get("links_before_press")]
        if not time_token.match(walk.get("header_after_link", "")):
            fails["NEXT 1:1 · <formatted time> after Link"] = walk.get("header_after_link")
        label = time_token.sub("", walk.get("header_after_link", "")).strip()
        head = walk.get("header_after_link", "").replace("NEXT 1:1 · ", "")
        if not head or head not in walk.get("now_side", "") or "No 1:1 planned" in walk.get("now_side", ""):
            fails["Now side reads as the header"] = [walk.get("now_side"), head, label]
        if walk.get("people_iso") or walk.get("prep_iso"):
            fails["no ISO time on People"] = [walk.get("people_iso"), walk.get("prep_iso")]
        if walk.get("row_taps") != 1 or walk.get("lens_after_row") != "Prep" or \
                not any(t.startswith("People") for t in walk.get("front_after_row", [])):
            fails["Chair 1:1 row -> Priya on Prep in 1 gesture"] = [walk.get("front_after_row"), walk.get("lens_after_row")]
        if "Review the dry-run report" not in walk.get("agenda", ""):
            fails["Prep shows the agenda"] = walk.get("agenda")
        if OWED not in walk.get("owed", "") or "WAITING ON PRIYA" not in walk.get("owed", "").upper():
            fails["Prep shows what Priya owes"] = walk.get("owed")
        if "BY TUE" not in walk.get("owed", "").upper() or "BY MON" in walk.get("owed", "").upper():
            fails["the date-only deadline stays Tuesday in America/Denver"] = walk.get("owed")
        if "NEXT 1:1 DID NOT LOAD · NOT AVAILABLE NOW" not in walk.get("brief_failure", "") or \
                "No 1:1 planned" in walk.get("brief_failure_side", ""):
            fails["a failed brief read is named, never 'No 1:1 planned'"] = walk.get("brief_failure_side")
        if "Link this 1:1" not in walk.get("after_retry_side", ""):
            fails["Try again brings the suggestion"] = walk.get("after_retry_side")
        if self.ids["project"] not in walk.get("projects", ""):
            fails["Prep shows her project"] = walk.get("projects")
        for key in ("readable", "readable_scrolled"):
            faults = walk.get(key) or {}
            if not faults.get("scopes") or faults.get("clipped") or faults.get("overlaps"):
                fails[f"nothing clipped or overlapping ({key})"] = faults
        owed_front = walk.get("front_after_owed") or []
        if not any(not w["title"].startswith("People") and self.ids["title"] in w["text"] for w in owed_front):
            fails["the owed action opens its meeting"] = owed_front
        assert not fails, json.dumps(fails, indent=1)
