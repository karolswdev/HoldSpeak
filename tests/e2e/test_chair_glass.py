"""The Chair app, AS RENDERED: what only a real browser proves of the Chair.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation.

PHILO-14 A1c's legacy test ids remain for recovery evidence. DESIGN-windows
§4.5 (2026-10-13) parked the ready card: the bell now opens the exact stored
meeting inside Meetings, with Back returning to its list. These four cases
carry the original geometry proofs through that current owner journey:

  default   measure Capture's seat, close it, send the real ready signal;
            Capture stays closed, the bell owns its hit target, the exact
            summary opens, and Capture returns at its measured seat.
  moved     move Capture by its title bar; its rect and scroll survive the
            ready signal, reading the stored result, and the return.
  resized   size Capture by its grip; the same geometry and scroll proof.
  meetings  Meetings already open; the ready bell opens this exact result
            there without changing Capture's rect.

No inference POST may occur while opening the completed result. The summary
and Back must be whole and own their centres after scrolling into view.

The frame is the hub's own (``build_aftercare_ready_event`` over a seeded
meeting with open items, sent with ``MeetingWebServer.broadcast``).

Also kept here by lane e2e-high-1:

The Chair windows in a real browser: their exact places.

Kept by the test diet (push 2, 2026-10-12), one file for the Chair app:

* a Chair window zoomed, unzoomed, closed and opened again from
  Window > Chair comes back at its tile place (it came back 12 px low,
  clamped into the shell band; was the Chair leg of
  tests/e2e/test_finish_face_polish_glass.py).

Also here (lane e2e-high-1: the Chair as windows):

The Chair windows in a real browser.

Kept by the test diet (push 2, 2026-10-12), one file for the Chair app.

* THE CHAIR AS WINDOWS (PHILO-13-11, slice two; the canvas the owner ratified
  2026-10-02): four Chair windows tile without overlap at 1440, each body
  scrolls on its own; one blue window and the screen title names it (a
  press on each); Close closes and Window > Chair reopens in front; at 393
  one Chair window at a time with every target owning 44 x 44; the frame
  fences inside each window (hover, touch, exact geometry, elementFromPoint).
  Was tests/e2e/test_philo13_11_chair_glass.py (parked whole); its canvas
  week is tests/e2e/chair_rig.py.
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

from .chair_rig import _seed
from .frame_rig import FRAME_JS
from .chair_windows import chair_window, open_chair_window

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
        page.get_by_test_id("desk-bell").filter(
            has=page.locator(".desk-bell-ready")).wait_for()
        assert page.get_by_test_id("desk-bell").get_attribute("aria-label") == "Meeting ready: Vendor call"
        assert page.locator(".ambient-aftercare, .ambient-aftercare-fixed").count() == 0
        _settle(page)

    @staticmethod
    def _dismiss(page: Any) -> None:
        # DESIGN-windows §4.2: a ready meeting opens inside Meetings; Back
        # returns to its list before closing the window returns to the desk.
        meetings = page.locator('[id="surface-meetings"]')
        meetings.get_by_test_id("meeting-record-back").click()
        meetings.get_by_test_id(f"meeting-row-{CARD_MEETING}").wait_for()
        meetings.get_by_role("button", name="Close Meetings", exact=True).click()
        meetings.wait_for(state="detached")

    @staticmethod
    def _readable(page: Any, fails: list[str], name: str) -> dict[str, Any]:
        """The ready control and the exact stored result own their centres.

        DESIGN-attention parks the card; the ready bell is its real door.
        No inference request may run while opening this completed meeting.
        """
        bell = page.get_by_test_id("desk-bell")
        out = {"ready": bell.evaluate(WHOLE)}
        inference: list[str] = []
        page.on("request", lambda req: inference.append(req.url) if req.method == "POST"
                and req.url.endswith("/intelligence/run") else None)
        bell.click()
        meetings = page.locator('[id="surface-meetings"]')
        summary = meetings.get_by_test_id("meeting-summary-text")
        summary.wait_for()
        assert summary.inner_text() == "Contract draft by Friday."
        summary.scroll_into_view_if_needed()
        out["summary"] = summary.evaluate(WHOLE)
        back = meetings.get_by_test_id("meeting-record-back")
        back.scroll_into_view_if_needed()
        out["back"] = back.evaluate(WHOLE)
        rows = _api(page, "GET", "/api/desk/windows", token=TOKEN)["windows"]
        selected = [row for row in rows if row["id"] == "surface-meetings"]
        assert len(selected) == 1 and selected[0]["object_ref"] == f"meeting:{CARD_MEETING}", selected
        saved = _api(page, "GET", f"/api/meetings/{CARD_MEETING}", token=TOKEN)
        assert saved["id"] == CARD_MEETING, saved
        assert inference == [], inference
        out["meeting"] = selected[0]["object_ref"]
        for part in ("ready", "summary", "back"):
            if not (out[part]["full"] and out[part]["hit"]):
                fails.append(f"{name}: the ready journey's {part} is not whole {out[part]}")
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
                scroll = page.locator(f"{CAPTURE} .chair-window-body").evaluate("el => el.scrollTop")
                facts["before"] = before
                self._send_card(page)
                with_card = page.evaluate(GEOMETRY)
                facts["with_card"] = with_card
                page.screenshot(path=str(SHOTS / f"A1c-r2-{how}-1440-card.png"))
                if not _same(before["capture"], with_card["capture"]):
                    fails.append(f"{how}: Capture moved with the ready signal {before['capture']} -> {with_card['capture']}")
                assert page.locator(f"{CAPTURE} .chair-window-body").evaluate("el => el.scrollTop") == scroll
                facts["readable"] = self._readable(page, fails, how)
                page.screenshot(path=str(SHOTS / f"A1c-r2-{how}-1440-scrolled.png"))
                self._dismiss(page)
                self._open_chair(page, "Capture")
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                if not _same(before["capture"], after["capture"]):
                    fails.append(f"{how}: return did not keep Capture {before['capture']} -> {after['capture']}")
                assert page.locator(f"{CAPTURE} .chair-window-body").evaluate("el => el.scrollTop") == scroll
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
                page.locator(CAPTURE).wait_for(state="detached")
                # Closing the front frame animates the revealed Needs-you
                # plane. Measure its settled rect before sending the signal.
                _settle(page)
                if page.locator(f".desk-window-shell{CAPTURE}").count():
                    fails.append("Capture is open before the card")
                needs_before = page.evaluate(GEOMETRY)["needs"]
                self._send_card(page)
                g = page.evaluate(GEOMETRY)
                facts["with_card"] = g
                page.screenshot(path=str(SHOTS / "A1c-r2-default-1440-card.png"))
                # A completed meeting no longer opens or grows Capture. The
                # ready bell is visible without moving the work underneath.
                assert g["capture"] is None, g
                assert _same(needs_before, g["needs"]), (needs_before, g)
                facts["readable"] = self._readable(page, fails, "default")
                self._dismiss(page)
                self._open_chair(page, "Capture")
                after = page.evaluate(GEOMETRY)
                facts["after"] = after
                # Opening Capture after reading returns to its exact seat.
                if not _same(seat, after["capture"]):
                    fails.append(f"default: Capture did not return to its seat {seat} -> {after['capture']}")
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
                page.wait_for_timeout(600)
                before = page.evaluate(GEOMETRY)
                facts["before"] = before
                self._send_card(page)
                with_card = page.evaluate(GEOMETRY)
                facts["with_card"] = with_card
                page.screenshot(path=str(SHOTS / "A1c-r2-meetings-1440-card.png"))
                if not _same(before["capture"], with_card["capture"]):
                    fails.append(f"meetings: Capture moved {before['capture']} -> {with_card['capture']}")
                facts["readable"] = self._readable(page, fails, "meetings")
                self._dismiss(page)
                self._open_chair(page, "Capture")
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


# ══ lane e2e-high-1: the Chair as windows ════════════════════════════════════════

H1_TOKEN = "philo13-11-chair"

H1_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-build")

SIZES = {1440: 900, 393: 852}

CHAIR = ["Needs you", "Brief", "The week", "Capture"]

CHAIR_JS = r"""(width) => {
  const rgb = (s) => { const m = String(s).match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const blend = (top, under) => ({r: top.r * top.a + under.r * (1 - top.a), g: top.g * top.a + under.g * (1 - top.a),
    b: top.b * top.a + under.b * (1 - top.a), a: 1});
  const groundOf = (el) => { const chain = []; for (let e = el; e; e = e.parentElement) {
      const c = rgb(getComputedStyle(e).backgroundColor); if (c && c.a > 0) { chain.push(c); if (c.a >= 1) break; } }
    let g = {r: 0, g: 0, b: 0, a: 1}; for (let i = chain.length - 1; i >= 0; i--) g = blend(chain[i], g); return g; };
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05; };
  const label = (e) => (e.getAttribute('aria-label') || e.textContent || e.className || '').trim().slice(0, 50);
  const selector = width <= 720
    ? '.desk-window-shell.chair-window:not([data-departing]), [id="pullout:intelligence:desk"]:not([data-departing])'
    : '.desk-window-shell.chair-window:not([data-departing])';
  const wins = [...document.querySelectorAll(selector)].filter(visible);
  const chair = document.querySelector('.chair');
  const se = document.scrollingElement;
  const out = {width, windows: wins.map((w) => w.getAttribute('aria-label')),
    reopen: [...document.querySelectorAll('[data-testid^="chair-reopen-"] button')].filter(visible).map(label),
    page_scrolls: Boolean((chair && chair.scrollHeight > chair.clientHeight + 1) || (se && se.scrollHeight > se.clientHeight + 1)),
    bodies: {}, tiles_overlap: [], clipped: [], ellipsis: [], sideways: [], overlap: [], small_targets: [],
    low_contrast: [], small_text: []};
  if (width <= 720) {
    // A canonical program pane retains the Chair behind it. DOM presence
    // is not a second usable pane: sample the full work area, including
    // its corners and edges, and keep the actual compositor identities.
    out.phone_panes = wins.map((w) => {
      const r = w.getBoundingClientRect();
      const hits = [r.top + 2, r.top + r.height / 2, r.bottom - 2].flatMap((y) =>
        [r.left + 2, r.left + r.width / 2, r.right - 2].map((x) =>
          document.elementFromPoint(x, y)?.closest('.desk-window-shell')?.id ?? null));
      return {id: w.id, name: w.getAttribute('aria-label'), plane: w.dataset.plane,
        front: w.classList.contains('is-front'), z: getComputedStyle(w).zIndex,
        rect: [r.left, r.top, r.width, r.height], hits};
    });
    out.usable_windows = out.phone_panes.filter((w) => w.hits.includes(w.id)).map((w) => w.name);
  }
  const bodyOf = (w) => [...w.querySelectorAll('.chair-window-body, .intelligence-pullout')].find(visible);
  for (const w of wins) { const b = bodyOf(w); if (!b) continue;
    const cs = getComputedStyle(b);
    out.bodies[w.getAttribute('aria-label')] = {overflowY: cs.overflowY, scrolls: b.scrollHeight > b.clientHeight + 1,
      h: Math.round(b.getBoundingClientRect().height)}; }
  // the four tile: no two Chair windows overlap (1440)
  if (width > 720) for (let i = 0; i < wins.length; i++) for (let j = i + 1; j < wins.length; j++) {
    const a = wins[i].getBoundingClientRect(), b = wins[j].getBoundingClientRect();
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 1 && oy > 1) out.tiles_overlap.push([wins[i].getAttribute('aria-label'), wins[j].getAttribute('aria-label')]);
  }
  for (const w of wins) {
    const body = bodyOf(w); if (!body) continue;
    const br = body.getBoundingClientRect();
    // nothing clips: a text box past its clipping ancestor (single-line ellipsis recorded)
    const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const el = n.parentElement; const text = n.textContent.trim();
      if (!text || !visible(el)) continue;
      const range = document.createRange(); range.selectNodeContents(n); const tr = range.getBoundingClientRect();
      if (tr.width < 1 || tr.height < 1) continue;
      for (let a = el; a && a !== body.parentElement; a = a.parentElement) {
        const cs = getComputedStyle(a);
        if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
        const ar = a.getBoundingClientRect();
        if (tr.left < ar.left - 1 || tr.right > ar.right + 1) {
          const hs = getComputedStyle(el);
          if (hs.textOverflow === 'ellipsis' && hs.whiteSpace === 'nowrap') out.ellipsis.push(text.slice(0, 40));
          else out.clipped.push({text: text.slice(0, 40), in: label(a)});
        }
        break;
      }
      // only what is on screen in its window is read for contrast and size
      if (tr.bottom < br.top || tr.top > br.bottom) continue;
      const cs = getComputedStyle(el); const size = parseFloat(cs.fontSize);
      if (size < 1) continue;
      if (size < 12 - 0.01) out.small_text.push({text: text.slice(0, 30), size});
      const fg = rgb(cs.color); if (!fg) continue;
      const ground = groundOf(el); const shown = fg.a < 1 ? blend(fg, ground) : fg;
      const r = ratio(shown, ground); const large = size >= 24 || (size >= 18.66 && Number(cs.fontWeight) >= 700);
      if (r < (large ? 3 : 4.5) - 0.01) out.low_contrast.push({text: text.slice(0, 30), ratio: Math.round(r * 100) / 100});
    }
    // nothing scrolls sideways inside a Chair window
    for (const e of [body, ...body.querySelectorAll('*')]) { if (!visible(e)) continue; const cs = getComputedStyle(e);
      if (['auto', 'scroll'].includes(cs.overflowX) && e.scrollWidth > e.clientWidth + 1) out.sideways.push(label(e)); }
    // no two visible controls of one window overlap (on screen in the body)
    const ctrls = [...body.querySelectorAll('button, a[href], input, select, textarea, [role=button]')].filter(visible)
      .map((c) => [c, c.getBoundingClientRect()]).filter(([, r]) => r.bottom > br.top && r.top < br.bottom);
    for (let i = 0; i < ctrls.length; i++) for (let j = i + 1; j < ctrls.length; j++) {
      const [ca, a] = ctrls[i], [cb, b] = ctrls[j];
      if (ca.contains(cb) || cb.contains(ca)) continue;
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > 1 && oy > 1) out.overlap.push([label(ca), label(cb)]);
    }
    // 393: every target in the body owns 44 x 44 (on screen)
    if (width <= 720) for (const [c, r] of ctrls) {
      if (c.matches('input, textarea, select')) continue;
      if (r.width < 44 - 0.5 || r.height < 44 - 0.5) out.small_targets.push({control: label(c), w: Math.round(r.width), h: Math.round(r.height)});
    }
  }
  return out;
}"""

@pytest.mark.chair_windows_open
class TestTheChairAsWindows:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=H1_TOKEN)
        self.home = tmp_path / "home"
        _seed(self.home)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=2, has_touch=width < 720, is_mobile=False)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={H1_TOKEN}", wait_until="load")
        page.evaluate(
            """async (token) => fetch('/api/setup/onboarding', {method: 'PUT',
                headers: {authorization: `Bearer ${token}`, 'content-type': 'application/json'},
                body: JSON.stringify({disposition: 'completed'})})""",
            H1_TOKEN,
        )
        _api(page, "POST", "/api/channels/destinations",
             {"name": "Team updates", "channel": "file",
              "folder": str(self.home / "Documents" / "HoldSpeak" / "Team updates")}, token=H1_TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        try:
            page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=10_000)
        except Exception:  # noqa: BLE001 -- the fences below name what is missing (red on bbf7e9a4)
            pass
        page.wait_for_timeout(1500)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    @staticmethod
    def _measure(page: Any, width: int, board: str, facts: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        page.wait_for_timeout(400)
        _settle(page)
        frame = page.evaluate(FRAME_JS, width)
        chair = page.evaluate(CHAIR_JS, width)
        facts[board] = {"frame": frame, "chair": chair}
        return frame, chair

    @staticmethod
    def _fails(frame: dict[str, Any], chair: dict[str, Any], width: int) -> dict[str, Any]:
        fails: dict[str, Any] = {}
        if len(frame["blue"]) != 1 or frame["front"] != frame["blue"] or frame["screen"] != frame["blue"][0]:
            fails["C2 one blue window, named by the screen bar"] = {
                "blue": frame["blue"], "front": frame["front"], "screen": frame["screen"]}
        if frame["ownership"]:
            fails["C5 frame ownership"] = frame["ownership"]
        if frame["clipped"] or frame["sideways"]:
            fails["C5 frame clips"] = {"clipped": frame["clipped"], "sideways": frame["sideways"]}
        if frame["small_text"] or frame["low_contrast"]:
            fails["C5 frame text in place"] = {"small": frame["small_text"], "low": frame["low_contrast"]}
        if chair["clipped"] or chair["sideways"] or chair["overlap"]:
            fails["C5 Chair windows: nothing clips, nothing scrolls sideways, nothing overlaps"] = {
                "clipped": chair["clipped"], "sideways": chair["sideways"], "overlap": chair["overlap"]}
        if chair["low_contrast"]:
            fails["C5 Chair windows: contrast in place"] = chair["low_contrast"]
        if chair["page_scrolls"]:
            fails["C1 the Chair page does not scroll"] = True
        for name, body in chair["bodies"].items():
            if body["overflowY"] not in ("auto", "scroll"):
                fails.setdefault("C1 each window scrolls on its own", []).append({name: body})
        if width > 720 and chair["tiles_overlap"]:
            fails["C1 the four tile"] = chair["tiles_overlap"]
        if width <= 720:
            front = [pane for pane in chair["phone_panes"] if pane["front"]]
            if (len(front) != 1 or chair["usable_windows"] != frame["front"]
                    or any(owner != front[0]["id"] for owner in front[0]["hits"])):
                fails["C4 one usable front pane owns its full work area"] = chair["phone_panes"]
            if frame["content"] is None or frame["content"] < 700 or frame["small_targets"] or chair["small_targets"]:
                fails["C4 393 content and targets"] = {"content": frame["content"], "frame": frame["small_targets"],
                                                      "body": chair["small_targets"]}
        return fails

    @staticmethod
    def _verbs(page: Any) -> dict[str, Any]:
        """C6: the existing verbs, each in its window."""
        def inside(win: str, sel: str) -> int:
            return page.locator(f".desk-window-shell[aria-label='{win}'] {sel}").count()
        return {
            "needs.done": inside("Needs you", "[data-verb='done'], [data-verb='door-verb']"),
            "needs.name_owner": inside("Needs you", "[data-verb='name-owner']"),
            "needs.connect_calendar": inside("Needs you", "[data-verb='connect-calendar']"),
            "needs.choose_engine": inside("Needs you", "[data-verb='setup']"),
            "brief.ack_defer": inside("Brief", "[data-testid='arrival-brief-row'] button"),
            "brief.generate": inside("Brief", "button:has-text('Generate')"),
            "brief.send_well": inside("Brief", ":text('Team updates')"),
            "week.open": inside("The week", "[data-testid='arrival-meeting-row'] button:has-text('Open')"),
            "week.stored": page.evaluate("""() => [...document.querySelectorAll(
                '.desk-window-shell[aria-label="The week"] [data-testid="arrival-meeting-row"]')]
                .filter((r) => (r.querySelector('[data-testid="arrival-meeting-badge"]') || {}).textContent === 'SUMMARY STORED')
                .map((r) => ({run: Boolean(r.querySelector('[data-testid="arrival-run-intel"]')),
                              open: Boolean(r.querySelector('[data-testid="arrival-meeting-open"]'))}))"""),
            "capture": inside("Capture", "[data-testid='arrival-develop-thought'], [data-testid='arrival-record-meeting'], [data-testid='arrival-schedule']"),
        }

    @staticmethod
    def _stop(facts: dict[str, Any], failures: dict[str, Any], tag: str) -> None:
        """No Chair windows to walk: record what the first board measured and fail."""
        failures = {k: v for k, v in failures.items() if v}
        facts["failures"] = failures
        (H1_SHOTS / f"chair-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
        raise AssertionError(json.dumps(failures, indent=2))

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_chair_as_windows(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        facts: dict[str, Any] = {}
        failures: dict[str, Any] = {}
        tag = f"{width}"
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                shell = lambda name: chair_window(page, name)  # noqa: E731
                if width > 720:
                    # C1-4a: the four windows
                    frame, chair = self._measure(page, width, "chair-windows", facts)
                    failures["chair-windows"] = self._fails(frame, chair, width)
                    if sorted(chair["windows"]) != sorted(CHAIR):
                        failures["chair-windows"]["C1 four Chair windows"] = chair["windows"]
                        self._stop(facts, failures, tag)
                    verbs = self._verbs(page)
                    facts["verbs"] = verbs
                    missing = [k for k, v in verbs.items() if k not in ("week.stored",) and not v]
                    stored = verbs["week.stored"]
                    if missing or not stored or any(r["run"] or not r["open"] for r in stored):
                        failures["chair-windows"]["C6 the verbs keep their windows"] = {"missing": missing, "stored": stored}
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4a-chair-windows-{tag}.png"))

                    # C2b: the screen title names the front Chair window after a
                    # press on each one (Astra, #730: it read the Dock-only list).
                    named = {}
                    for name in CHAIR:
                        shell(name).locator(".desk-pullout-title").click()
                        page.wait_for_timeout(250)
                        named[name] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    facts["screen-title-after-press"] = named
                    if any(named[n] != n for n in CHAIR):
                        failures["chair-windows"]["C2 the screen title names each front Chair window"] = named
                    shell("Needs you").locator(".desk-pullout-title").click()

                    # C1-4c: Close closes. PHILO-14 A1 (board A-1): the Chair is
                    # the screen of objects, so no reopen Button stands in its place.
                    shell("Brief").get_by_role("button", name="Close Brief").click()
                    shell("Brief").wait_for(state="detached")
                    frame, chair = self._measure(page, width, "chair-window-closed", facts)
                    failures["chair-window-closed"] = self._fails(frame, chair, width)
                    if "Brief" in chair["windows"] or chair["reopen"]:
                        failures["chair-window-closed"]["C3 close closes; the screen stands"] = {
                            "windows": chair["windows"], "reopen": chair["reopen"]}
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4c-chair-window-closed-{tag}.png"))

                    # C1-4d: Window ▸ Chair, a check on each open one
                    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Desk')").hover()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()
                    # PHILO-16: the Window menu's verbs (Stage carries a check)
                    # sit above; the Chair's windows are their own list, the
                    # Window ▸ Chair submenu. Read that list only.
                    rows = page.evaluate("""() => {
                        // The innermost list holding the Chair rows (a submenu
                        // nests inside the Window list).
                        const list = [...document.querySelectorAll('.desk-menu-list')]
                          .filter((l) => [...l.querySelectorAll('[role="menuitemcheckbox"]')]
                            .some((e) => e.textContent.includes('Needs you'))).pop();
                        return [...(list ? list.querySelectorAll('[role="menuitemcheckbox"]') : [])]
                          .map((e) => [e.textContent.trim(), e.getAttribute('aria-checked')]); }""")
                    facts["window-menu-chair"] = rows
                    want = [["Needs you", "true"], ["Brief", "false"], ["The week", "true"], ["Capture", "true"]]
                    frame, chair = self._measure(page, width, "window-menu-chair", facts)
                    failures["window-menu-chair"] = self._fails(frame, chair, width)
                    if [[t.replace("✓", "").strip(), c] for t, c in rows] != want:
                        failures["window-menu-chair"]["C3 Window ▸ Chair checks the open ones"] = rows
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4d-window-menu-chair-{tag}.png"))
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Brief')").click()
                    shell("Brief").wait_for()
                    frame, chair = self._measure(page, width, "chair-window-reopened", facts)
                    failures["chair-window-reopened"] = self._fails(frame, chair, width)
                    if frame["screen"] != "Brief" or chair["reopen"]:
                        failures["chair-window-reopened"]["C3 reopened in front"] = {
                            "screen": frame["screen"], "reopen": chair["reopen"]}
                    # PHILO-14 A1: the screen's Needs you drawer reopens its window
                    shell("Needs you").get_by_role("button", name="Close Needs you").click()
                    shell("Needs you").wait_for(state="detached")
                    page.locator(".desk-screen [data-object-id='drawer:needs']").press("Enter")
                    shell("Needs you").wait_for()
                    # a press on a window brings it to the front (one blue)
                    shell("Needs you").locator(".desk-pullout-title").click()
                    frame, chair = self._measure(page, width, "needs-front", facts)
                    failures["needs-front"] = self._fails(frame, chair, width)
                    if frame["blue"] != ["Needs you"]:
                        failures["needs-front"]["C2 the pressed window is the blue one"] = frame["blue"]
                else:
                    # C1-6a: one window at a time, Needs you first
                    frame, chair = self._measure(page, width, "phone-desk", facts)
                    failures["phone-desk"] = self._fails(frame, chair, width)
                    if chair["windows"] != ["Needs you"]:
                        failures["phone-desk"]["C4 one window, Needs you first"] = chair["windows"]
                        self._stop(facts, failures, tag)
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-6a-phone-desk-{tag}.png"))

                    # C2b (393): the screen title names the one Chair window
                    named = {"Needs you": page.get_by_test_id("desk-screen-title").inner_text().strip()}

                    # C1-4a (393): Go ▸ Brief (PHILO-14 A1 #939: the Chair's
                    # windows are Go's first rows, two taps)
                    self._press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
                    page.locator(".desk-verbbar-menu").wait_for()
                    page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").wait_for()
                    # PHILO-16: the Window menu's verbs (Stage carries a check)
                    # sit above; the Chair's windows are their own list, the
                    # Window ▸ Chair submenu. Read that list only.
                    rows = page.locator(".desk-verbbar-menu .desk-menu-label").all_inner_texts()
                    rows = [name for name in rows if name in CHAIR]
                    facts["go-chair"] = rows
                    # Brief is a command into Today rather than a checked
                    # Chair-window row; the four owner-facing doors stay.
                    if rows != CHAIR:
                        failures["phone-desk"]["C4 Go has the four Chair rows"] = rows
                    page.keyboard.press("Escape")
                    brief = open_chair_window(page, "Brief")
                    brief_name = brief.get_attribute("aria-label")
                    frame, chair = self._measure(page, width, "chair-windows", facts)
                    failures["chair-windows"] = self._fails(frame, chair, width)
                    if chair["usable_windows"] != [brief_name]:
                        failures["chair-windows"]["C4 one window at a time"] = chair["phone_panes"]
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4a-chair-windows-{tag}.png"))
                    named["Brief"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    open_chair_window(page, "The week")
                    page.wait_for_timeout(250)
                    named["The week"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    open_chair_window(page, "Brief")

                    # C1-4c (393): close gives the work area to the next Chair window
                    # A restored pullout flies back from its Dock chip. Measure
                    # the settled control before sending the original touch.
                    _settle(page)
                    back = shell("Brief").get_by_role("button", name=f"Back from {brief_name}", exact=True)
                    facts["brief-back-target"] = back.evaluate(WHOLE)
                    assert facts["brief-back-target"]["full"] and facts["brief-back-target"]["hit"], facts["brief-back-target"]
                    back.evaluate("""el => el.addEventListener('click', event => {
                        window.__chairBackTap = {trusted: event.isTrusted,
                            label: event.currentTarget.getAttribute('aria-label')};
                    }, {once: true})""")
                    self._press(page, back, width)
                    facts["brief-back-event"] = page.evaluate("window.__chairBackTap")
                    assert facts["brief-back-event"] == {"trusted": True, "label": f"Back from {brief_name}"}
                    shell("Brief").wait_for(state="detached")
                    frame, chair = self._measure(page, width, "chair-window-closed", facts)
                    failures["chair-window-closed"] = self._fails(frame, chair, width)
                    if len(chair["windows"]) != 1 or brief_name in chair["windows"]:
                        failures["chair-window-closed"]["C4 the next Chair window takes the work area"] = chair["windows"]
                    page.screenshot(path=str(H1_SHOTS / f"build-C1-4c-chair-window-closed-{tag}.png"))

                    # Capture on demand from the Speak AppIcon
                    self._press(page, page.locator(".desk-dock").get_by_role("button", name="Capture", exact=True), width)
                    shell("Capture").wait_for()
                    frame, chair = self._measure(page, width, "capture-from-speak", facts)
                    failures["capture-from-speak"] = self._fails(frame, chair, width)
                    verbs = self._verbs(page)
                    facts["capture-verbs"] = verbs["capture"]
                    page.wait_for_timeout(250)
                    named["Capture"] = page.get_by_test_id("desk-screen-title").inner_text().strip()
                    facts["screen-title-per-window"] = named
                    if any(named[n] != (brief_name if n == "Brief" else n) for n in CHAIR):
                        failures["capture-from-speak"]["C2 the screen title names the shown Chair window"] = named
                    if chair["windows"] != ["Capture"] or verbs["capture"] != 3:
                        failures["capture-from-speak"]["C4 Speak opens Capture"] = {
                            "windows": chair["windows"], "capture": verbs["capture"]}

                    # C4b (Muad'Dib's ruling): ONLY the Dock's Speak AppIcon opens
                    # Capture; Go ▸ Speak (the verb, the menu, ⌘1) keeps opening the
                    # Speak (dictation) window, so it stays reachable from the Chair.
                    # PHILO-15 11 (B21, owner ruling 2026-10-07): Speak is not in the
                    # phone Go; at 393 the Speak verb is one Search away.
                    self._press(page, page.locator("button[aria-controls=desk-tool-shelf]"), width)
                    page.locator("input[aria-controls=desk-palette-listbox]").fill("Speak")
                    go_speak = page.locator("[id='desk-palette-option-go.dictate']")
                    go_speak.first.wait_for()
                    self._press(page, go_speak.first, width)
                    try:
                        page.locator(".desk-window-shell[aria-label='Speak']").wait_for(timeout=8_000)
                    except Exception:  # noqa: BLE001 -- the fence below names what opened instead
                        pass
                    page.wait_for_timeout(400)
                    go = {"speak_window": page.locator(".desk-window-shell[aria-label='Speak']").count(),
                          "screen": page.get_by_test_id("desk-screen-title").inner_text().strip()}
                    facts["go-speak"] = go
                    if go["speak_window"] != 1 or go["screen"] != "Speak":
                        failures["capture-from-speak"]["C4b the Speak verb opens the Speak window"] = go
                facts["errors"] = [e for e in errors if "ResizeObserver" not in e]
                failures = {k: v for k, v in failures.items() if v}
                facts["failures"] = failures
                (H1_SHOTS / f"chair-facts-{tag}.json").write_text(json.dumps(facts, indent=2) + "\n")
                assert not facts["errors"], facts["errors"]
                assert not failures, json.dumps(failures, indent=2)
            finally:
                browser.close()
