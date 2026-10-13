"""The Chair app, AS RENDERED: what only a real browser proves of the Chair.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

PHILO-14 A1c -- the MEETING READY card in Capture's slot at 1440 (exact
rects; Capture moved and sized by the mouse).

Muad'Dib's ruling 2026-10-07: a card that lands opens a closed Capture and
sits in Capture's slot; nothing floats over another window. Astra r1 (#954)
asked for rendered geometry, not presence:

  default   Capture's seat is measured (open from the menu, close), then the
            card opens the closed Capture; it grows up from the seat's foot;
            the eyebrow, the title and Dismiss are whole in its body; it does
            not cover Needs you; Dismiss -> the exact seat rect.
  moved     Capture moved by its title bar (arranged) -> its rect does not
            change through card -> Dismiss; the eyebrow is whole at
            scrollTop 0; the title and Dismiss are whole once scrolled to.
  resized   Capture sized by its grip (arranged) -> the same.
  meetings  Capture open, Meetings in front -> the card lands in Meetings;
            Capture's rect does not change through card -> Dismiss.

The frame is the hub's own (``build_aftercare_ready_event`` over a seeded
meeting with open items, sent with ``MeetingWebServer.broadcast``).

Also kept here by lane e2e-high-1:

The Chair windows in a real browser: their exact places.

Kept by the test diet (push 2, 2026-10-12), one file for the Chair app:

* a Chair window zoomed, unzoomed, closed and opened again from
  Window > Chair comes back at its tile place (it came back 12 px low,
  clamped into the shell band; was the Chair leg of
  tests/e2e/test_finish_face_polish_glass.py).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

from .finish_rig import SHOTS as FINISH_SHOTS, FinishRig

pytest.importorskip("playwright.sync_api", reason="the Chair glass needs Playwright")

TOKEN = "chair-glass"
CARD_MEETING = "m-c7-vendor"
SHOTS = evidence_dir("docs/internal/philo/phase-14/a1c-shots")
CAPTURE = "[id='chair:capture']"

GEOMETRY = r"""() => {
  const rect = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; };
  const capture = document.getElementById('chair:capture');
  const needs = document.getElementById('chair:needs');
  const card = document.querySelector('.ambient-aftercare');
  const host = card ? card.closest('.desk-window-shell') : null;
  return { capture: rect(capture), needs: rect(needs), card: rect(card),
           host: host ? host.getAttribute('aria-label') : null,
           fixed: !!document.querySelector('.ambient-aftercare-fixed') };
}"""

# Whole = the element's box lies inside every clipping ancestor and the
# viewport, and the point at its centre hits it (nothing covers it).
WHOLE = r"""(el) => {
  const r = el.getBoundingClientRect();
  let t = r.top, l = r.left, b = r.bottom, ri = r.right;
  for (let a = el.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (/(auto|scroll|hidden|clip)/.test(cs.overflowX + cs.overflowY)) {
      const ar = a.getBoundingClientRect();
      t = Math.max(t, ar.top); l = Math.max(l, ar.left); b = Math.min(b, ar.bottom); ri = Math.min(ri, ar.right);
    }
  }
  t = Math.max(t, 0); l = Math.max(l, 0); b = Math.min(b, innerHeight); ri = Math.min(ri, innerWidth);
  const full = Math.abs(ri - l - r.width) < 1.5 && Math.abs(b - t - r.height) < 1.5;
  const h = document.elementFromPoint((r.left + r.right) / 2, (r.top + r.bottom) / 2);
  return { full, hit: !!h && (h === el || el.contains(h)), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}"""


def _seed_card_meeting() -> None:
    """A finished meeting with open items, so the hub's own aftercare event is not quiet."""
    from holdspeak.db import get_database
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    start = (datetime.now() - timedelta(minutes=40)).replace(microsecond=0)
    get_database().meetings.save_meeting(MeetingState(
        id=CARD_MEETING, started_at=start, ended_at=start + timedelta(minutes=30), title="Vendor call",
        segments=[TranscriptSegment(text="Avery sends the contract draft.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["vendor"], summary="Contract draft by Friday.",
                            action_items=[ActionItem(task="Send the contract draft", owner="Avery Chen"),
                                          ActionItem(task="Book the legal review", owner="Me")]),
        intel_status="completed"))


def _same(a: dict | None, b: dict | None) -> bool:
    return bool(a and b) and all(abs(a[k] - b[k]) <= 1 for k in ("x", "y", "w", "h"))


class TestTheCardInCapture1440:
    """replaces: tests/e2e/test_philo14_a1c_aftercare_capture_glass.py::TestTheCardInCapture1440 (every test, moved whole)."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed_card_meeting()
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the hands ────────────────────────────────────────────────────────

    def _page(self, pw: Any) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1).new_page()
        page.set_default_timeout(20_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(800)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _open_chair(page: Any, name: str) -> None:
        page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
        page.locator(".desk-verbbar-menu [role='menuitem']").filter(has_text="Desk").click()
        page.locator(".desk-menu-list [role='menuitemcheckbox']").filter(has_text=name).click()
        page.locator(f".desk-window-shell.chair-window[aria-label='{name}']").wait_for()
        page.wait_for_timeout(400)

    def _send_card(self, page: Any) -> None:
        from holdspeak.db import get_database
        from holdspeak.meeting_aftercare import build_aftercare_ready_event

        event = build_aftercare_ready_event(get_database(), CARD_MEETING)
        assert event, "the seeded meeting has no aftercare (the event is quiet)"
        self.server.broadcast("aftercare_ready", event)
        page.locator(".ambient-aftercare").wait_for()
        page.wait_for_timeout(700)
        _settle(page)

    @staticmethod
    def _dismiss(page: Any) -> None:
        button = page.locator(".ambient-aftercare").get_by_role("button", name="Dismiss")
        button.scroll_into_view_if_needed()
        button.click()
        page.locator(".ambient-aftercare").wait_for(state="detached")
        page.wait_for_timeout(500)

    @staticmethod
    def _readable(page: Any, fails: list[str], name: str) -> dict[str, Any]:
        """The receipt is reachable by scrolling Capture's body: at scrollTop 0
        the eyebrow is whole; scrolled to them, the title and Dismiss are whole."""
        body = page.locator(f"{CAPTURE} .chair-window-body")
        body.evaluate("(el) => { el.scrollTop = 0; }")
        page.wait_for_timeout(150)
        card = page.locator(f"{CAPTURE} [data-aftercare-slot] .ambient-aftercare")
        # At scrollTop 0 the card's first line is whole: nothing is stranded
        # above the scroll origin. Each later part is whole once scrolled to.
        out = {"eyebrow": card.locator(".signal-eyebrow").evaluate(WHOLE)}
        for part, loc in (("title", card.locator("strong")),
                          ("dismiss", card.get_by_role("button", name="Dismiss"))):
            loc.evaluate("(el) => el.scrollIntoView({ block: 'nearest' })")
            page.wait_for_timeout(150)
            out[part] = loc.evaluate(WHOLE)
        out["scroll"] = body.evaluate("(el) => ({ top: el.scrollTop, height: el.scrollHeight, client: el.clientHeight })")
        for part in ("eyebrow", "title", "dismiss"):
            if not (out[part]["full"] and out[part]["hit"]):
                fails.append(f"{name}: the card's {part} is not whole {out[part]}")
        return out

    def _arranged(self, how: str) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._open_chair(page, "Needs you")
                self._open_chair(page, "Capture")
                if how == "moved":
                    head = page.locator(f"{CAPTURE} .desk-pullout-head").bounding_box()
                    x, y = head["x"] + 180, head["y"] + head["height"] / 2
                    page.mouse.move(x, y)
                    page.mouse.down()
                    page.mouse.move(x + 20, y - 30, steps=10)
                    page.mouse.up()
                else:
                    grip = page.locator(f"{CAPTURE} .desk-window-grip").bounding_box()
                    x, y = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                    page.mouse.move(x, y)
                    page.mouse.down()
                    page.mouse.move(x - 218, y + 32, steps=12)
                    page.mouse.up()
                page.wait_for_timeout(500)
                before = page.evaluate(GEOMETRY)
                facts["before"] = before
                self._send_card(page)
                with_card = page.evaluate(GEOMETRY)
                facts["with_card"] = with_card
                page.screenshot(path=str(SHOTS / f"A1c-r2-{how}-1440-card.png"))
                if with_card["host"] != "Capture":
                    fails.append(f"{how}: the card is in {with_card['host']}, not Capture")
                if with_card["fixed"]:
                    fails.append(f"{how}: a fixed card floats")
                if not _same(before["capture"], with_card["capture"]):
                    fails.append(f"{how}: Capture moved with the card {before['capture']} -> {with_card['capture']}")
                facts["readable"] = self._readable(page, fails, how)
                page.screenshot(path=str(SHOTS / f"A1c-r2-{how}-1440-scrolled.png"))
                self._dismiss(page)
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                if not _same(before["capture"], after["capture"]):
                    fails.append(f"{how}: Dismiss did not keep Capture {before['capture']} -> {after['capture']}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / f"A1c-r2-{how}-facts.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1))
                browser.close()
        assert not fails, fails

    # ── the fences ───────────────────────────────────────────────────────

    def test_closed_capture_opens_and_holds_the_whole_card(self) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._open_chair(page, "Needs you")
                # Capture's seat (C1-1): opened once from Window > Chair with
                # no card, measured, then closed with its own close gadget.
                self._open_chair(page, "Capture")
                seat = page.evaluate(GEOMETRY)["capture"]
                facts["seat"] = seat
                page.get_by_role("button", name="Close Capture", exact=True).click()
                page.wait_for_timeout(400)
                if page.locator(f".desk-window-shell{CAPTURE}").count():
                    fails.append("Capture is open before the card")
                self._send_card(page)
                g = page.evaluate(GEOMETRY)
                facts["with_card"] = g
                page.screenshot(path=str(SHOTS / "A1c-r2-default-1440-card.png"))
                if g["host"] != "Capture":
                    fails.append(f"default: the card is in {g['host']}, not Capture")
                if g["fixed"]:
                    fails.append("default: a fixed card floats")
                cap, needs = g["capture"], g["needs"]
                if cap and needs and cap["y"] < needs["y"] + needs["h"] - 1 and cap["x"] < needs["x"] + needs["w"]:
                    fails.append(f"default: Capture {cap} covers Needs you {needs}")
                facts["readable"] = self._readable(page, fails, "default")
                scroll = facts["readable"]["scroll"]
                if scroll["height"] > scroll["client"] + 1:
                    fails.append(f"default: the grown Capture still scrolls {scroll}")
                self._dismiss(page)
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                # Astra r2: Dismiss returns Capture to the EXACT seat rect.
                if not _same(seat, after["capture"]):
                    fails.append(f"default: Capture did not return to its seat {seat} -> {after['capture']}")
                if cap and seat and abs(cap["y"] + cap["h"] - seat["y"] - seat["h"]) > 1:
                    fails.append(f"default: the grown Capture's foot left the seat's {seat} -> {cap}")
                if cap and seat and cap["h"] <= seat["h"]:
                    fails.append(f"default: Capture did not grow for the card {seat} -> {cap}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / "A1c-r2-default-facts.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1))
                browser.close()
        assert not fails, fails

    def test_moved_capture_keeps_its_rect_and_the_card_scrolls_whole(self) -> None:
        self._arranged("moved")

    def test_resized_capture_keeps_its_rect_and_the_card_scrolls_whole(self) -> None:
        self._arranged("resized")

    def test_card_in_meetings_does_not_move_capture(self) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        fails: list[str] = []
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw)
            try:
                self._open_chair(page, "Needs you")
                self._open_chair(page, "Capture")
                page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                page.locator(".desk-verbbar-menu").get_by_role("menuitem", name=re.compile(r"^Meetings")).click()
                meetings = page.locator(".desk-window-shell[aria-label='Meetings']")
                meetings.wait_for()
                meetings.locator("[data-aftercare-window-slot]").first.wait_for(state="attached")
                page.wait_for_timeout(600)
                before = page.evaluate(GEOMETRY)
                facts["before"] = before
                self._send_card(page)
                with_card = page.evaluate(GEOMETRY)
                facts["with_card"] = with_card
                page.screenshot(path=str(SHOTS / "A1c-r2-meetings-1440-card.png"))
                if with_card["host"] != "Meetings":
                    fails.append(f"meetings: the card is in {with_card['host']}, not Meetings")
                if not _same(before["capture"], with_card["capture"]):
                    fails.append(f"meetings: Capture moved {before['capture']} -> {with_card['capture']}")
                self._dismiss(page)
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                if not _same(before["capture"], after["capture"]):
                    fails.append(f"meetings: Capture moved after Dismiss {before['capture']} -> {after['capture']}")
                real = [e for e in errors if "ResizeObserver" not in e]
                if real:
                    fails.append(f"page errors {real}")
            finally:
                (SHOTS / "A1c-r2-meetings-facts.json").write_text(json.dumps({"facts": facts, "fails": fails}, indent=1))
                browser.close()
        assert not fails, fails


# ── PHILO-15 lane 19: the Brief carries the day (rehearsal 2: B58, B59, B73) ──
# The rig opens the Brief window on YESTERDAY's Brief, makes the day through
# the real producers, then runs the REAL cadence tick (the scheduled path)
# while the window is open. Today's Brief replaces yesterday's on the glass
# with no reload; its first three rows are the merge, the sent update and the
# PR. The rows' words are the hub's (tests/unit/test_monday_brief_service.py
# B58, B59, B73 fence them); this browser case is the live re-read.
BRIEF_TOKEN = "chair-glass-brief"
BRIEF_SHOTS = evidence_dir("docs/internal/philo/phase-15/19-shots")
_BRIEF_RAW = re.compile(r"[{}]|\d{4}-\d{2}-\d{2}T|sha256|launch-|prop-")


def _brief_iso(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).replace(microsecond=0).isoformat()


def _brief_the_day(page: Any, ledger_path: Path) -> None:
    """The rehearsal's day through the real producers."""
    from holdspeak.db import get_database
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    start = (datetime.now() - timedelta(minutes=40)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-hygiene", started_at=start, ended_at=start + timedelta(seconds=21),
        title="Repo hygiene sync",
        segments=[TranscriptSegment(text="We squash merge only. Karol adds a CODEOWNERS file by Friday.",
                                    speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["hygiene"], summary="One decision.", action_items=[{
            "id": "m-hygiene-a1", "task": "Add a CODEOWNERS file", "owner": "me", "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))
    proposal = db.proposals.create_proposal(
        meeting_id="m-hygiene", project_id=None, kind="decision",
        text="Squash merges only on the rehearsal repository", source_plugin="rehearsal")
    ProposalBridgeService(db).confirm_proposal(owner, proposal.id)
    FollowThroughService(db).complete(owner, "m-hygiene-a1", "done", {})

    pid = _api(page, "POST", "/api/projects", {"name": "Rehearsal repo hygiene"}, token=BRIEF_TOKEN)["project"]["id"]
    update = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {}, token=BRIEF_TOKEN)["update"]["id"]
    # PHILO-15 B64 (Astra r1): an update with no verified claim is refused
    # NOTHING VERIFIED; a fresh Project's draft has none. The owner's own saved
    # words are reviewed, so the update carries one line (tests/unit/_philo10_send.py).
    _api(page, "PUT", f"/api/updates/{update}",
         {"body_md": "## Progress\n\nCODEOWNERS landed; merges are squash only.\n"}, token=BRIEF_TOKEN)
    _api(page, "POST", f"/api/updates/{update}/publish", {}, token=BRIEF_TOKEN)
    ref = f"project_update:{update}"
    digest = _api(page, "POST", "/api/channels/preview",
                  {"document_ref": ref, "destination_id": "holdspeak-folder"}, token=BRIEF_TOKEN)["payload_digest"]
    _api(page, "POST", "/api/channels/send", {"document_ref": ref, "destination_id": "holdspeak-folder",
                                              "preview_digest": digest, "command_id": "glass-19"}, token=BRIEF_TOKEN)

    # The launch as the K4 follow-through leaves it after the merge.
    url = "https://github.com/karolswdev/holdspeak-dayone-rehearsal/pull/4"
    LaunchLedger(ledger_path).record({
        "launch_id": "launch-glass-19", "state": "launched", "profile_id": "codex",
        "origin_ref": {"kind": "action", "id": "m-hygiene-a1"}, "launched_at": _brief_iso(30),
        "follow_through": {
            "pr": {"number": 4, "title": "Add CODEOWNERS naming the owner", "url": url, "state": "merged"},
            "pr_opened_at": _brief_iso(18), "pr_state": "pr_merged", "close": "closed", "done": True,
            "evidence": {"pr_url": url, "pr_number": "4", "merged_at": _brief_iso(10)},
        },
    })


def _brief_yesterdays() -> None:
    """Yesterday's Brief is the one on the desk this morning."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.timestamps import local_wall

    MondayBriefService(get_database()).generate(
        Principal(PrincipalKind.OWNER, "karol"), now=local_wall() - timedelta(days=1))


def _brief_cadence_tick() -> None:
    """The hub's own scheduled tick, unchanged (regenerate=False, key-free,
    announced as one desk_changed frame). Only its hour is set to 00:00 so
    the rig runs at any time of day."""
    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    class _Hub(CadenceMixin):
        def __init__(self) -> None:
            self.config = Config()
            self.config.cadence.brief_hour = 0

    _Hub()._cadence_tick_once()


def _brief_shell(page: Any, name: str) -> Any:
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


def _brief_press(page: Any, loc: Any, width: int) -> None:
    loc.first.wait_for()
    if width < 720:
        loc.first.tap()
    else:
        loc.first.click()
    page.wait_for_timeout(300)


def _brief_menu_pick(page: Any, width: int, name: str) -> None:
    if width < 720:
        _brief_press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
    else:
        _brief_press(page, page.locator(".desk-verbbar-item[data-menu-id='window'] button"), width)
        page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").hover()
    _brief_press(page, page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"), width)


class TestTheBriefCarriesTheDay:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        self.ledger = tmp_path / "agent_launches.json"
        monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", self.ledger)
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=BRIEF_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.timeout(600, method="thread")
    def test_the_open_brief_shows_the_day_when_the_scheduled_write_lands(self) -> None:
        """replaces: tests/e2e/test_philo15_19_brief_day_glass.py::TestTheBriefCarriesTheDay::test_the_open_brief_shows_the_day_when_the_scheduled_write_lands
        (1440; the 393 run differed only in Go as the door: phoneRing.test.tsx:191-206).
        T2 owed: the open Brief re-reading on the hub's desk_changed frame wants a
        ChairHome render over a recorded Brief pair and a delivered frame."""
        width = 1440
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": {1440: 900, 393: 852}[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                from holdspeak.people import production_people_store

                production_people_store().initialize()
                _brief_yesterdays()
                page.goto(f"{self.base}/?token={BRIEF_TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()
                # Yesterday's Brief is on the desk at load; the window opens on it.
                _brief_menu_pick(page, width, "Brief")
                brief = _brief_shell(page, "Brief")
                brief.get_by_test_id("arrival-brief").first.wait_for()
                yesterday = _api(page, "GET", "/api/brief/latest", token=BRIEF_TOKEN)
                title = brief.locator(".desk-window-title").first
                page.wait_for_function(
                    "([el, want]) => el.innerText.trim() === want",
                    arg=[title.element_handle(), yesterday["title"]], timeout=15_000)

                _brief_the_day(page, self.ledger)
                _brief_cadence_tick()

                # B59: no reload. The window re-reads on the hub's frame.
                latest = _api(page, "GET", "/api/brief/latest", token=BRIEF_TOKEN)
                assert latest["id"] != yesterday["id"], "the tick made today's Brief"
                page.wait_for_function(
                    "([el, want]) => el.innerText.trim() === want",
                    arg=[title.element_handle(), latest["title"]], timeout=15_000)
                brief.locator("[data-testid=arrival-brief-row]", has_text="PR merged").wait_for()
                # ORDER RULING: the three rows on the face.
                shown = [r.split("\n")[0].strip() for r in
                         brief.get_by_test_id("arrival-brief-row").all_inner_texts()]
                assert [t.split(": ", 1)[0] for t in shown] == ["PR merged", "Update sent", "PR opened"], shown
                rows = {i["text"]: i for items in latest["sections"].values() for i in items}
                for wanted in (
                    "Decision confirmed: Squash merges only on the rehearsal repository",
                    "Action done: Add a CODEOWNERS file",
                    "Agent launched: Add a CODEOWNERS file",
                    "PR opened: Add CODEOWNERS naming the owner (PR #4)",
                    "PR merged: Add CODEOWNERS naming the owner (PR #4)",
                    "Update sent: Rehearsal repo hygiene",
                    "Meeting recorded: Repo hygiene sync",
                    "Project added: Rehearsal repo hygiene",
                ):
                    assert wanted in rows, (wanted, sorted(rows))
                    assert re.search(r"\d{2}:\d{2}$", rows[wanted]["detail"] or ""), rows[wanted]
                # B73: no JSON, no id, no UTC stamp in any row.
                for text, item in rows.items():
                    assert not _BRIEF_RAW.search(text) and not _BRIEF_RAW.search(item.get("detail") or ""), item
                # One honest NOT READ row: the key-free Brief did not read People.
                assert any(t.startswith("NOT READ · People") for t in rows), sorted(rows)
                row = brief.locator("[data-testid=arrival-brief-row]", has_text="Update sent")
                detail = row.get_by_test_id("arrival-brief-row-detail")
                assert re.fullmatch(r"HoldSpeak folder · \d{2}:\d{2}", detail.inner_text().strip()), \
                    detail.inner_text()
                assert not _BRIEF_RAW.search(brief.inner_text()), brief.inner_text()
                _settle(page)
                page.screenshot(path=str(BRIEF_SHOTS / f"brief-window-after-write-{width}.png"))

                # The whole day, in the Brief's full view (its "N more").
                _brief_press(page, brief.get_by_test_id("arrival-brief-more"), width)
                full = page.get_by_text("PR merged", exact=False).first
                full.wait_for()
                _settle(page)
                page.screenshot(path=str(BRIEF_SHOTS / f"brief-full-{width}.png"))
                intel = page.locator(".desk-window[aria-label='Today']")
                unread = intel.get_by_text("NOT READ · People", exact=False).first
                unread.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(BRIEF_SHOTS / f"brief-full-not-read-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()


# ══ lane e2e-high-1 (the finish-polish and Dock-tap fences) ═══════════

class TestChairWindowPlaces(FinishRig):
    @pytest.mark.e2e
    def test_a_chair_window_reopens_at_its_tile_place_after_a_zoom(self) -> None:
        from playwright.sync_api import sync_playwright

        rect = """() => { const b = document.querySelector(".desk-window-shell.chair-window[aria-label='Brief']").getBoundingClientRect();
                          return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; }"""
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                shell = page.locator(".desk-window-shell.chair-window[aria-label='Brief']")

                def open_brief() -> None:
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").hover()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                    shell.wait_for()
                    page.wait_for_timeout(600)
                    _settle(page)

                # Phase 14 A1: Chair windows start closed. Open the Brief at
                # its tile place first; that place is what a zoom must return to.
                if not shell.count():
                    open_brief()
                home = page.evaluate(rect)
                shell.get_by_role("button", name="Zoom Brief").click()
                page.wait_for_timeout(500)
                shell.get_by_role("button", name="Zoom Brief").click()
                page.wait_for_timeout(500)
                assert page.evaluate(rect) == home
                shell.get_by_role("button", name="Close Brief").click()
                shell.wait_for(state="detached")
                open_brief()
                page.screenshot(path=str(FINISH_SHOTS / "chair-reopened-1440.png"))
                assert page.evaluate(rect) == home, (page.evaluate(rect), home)
                assert not errors, errors
            finally:
                browser.close()
