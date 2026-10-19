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
        # Betterment shell S0 (#1257): the Window menu holds "No windows
        # open" on an empty desk; Go lists the Chair's windows (the shared door).
        open_chair_window(page, name)
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
        # Betterment shell S0 (#1257): an empty desk's Window menu holds one
        # line; Go is the Chair windows' door (the shared helper).
        open_chair_window(page, name)
        return
    _brief_press(page, page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"), width)


# ══ lane e2e-high-1 (the finish-polish and Dock-tap fences) ═══════════

class TestChairWindowPlaces(FinishRig):
    @pytest.mark.e2e
    def test_a_chair_window_reopens_at_its_tile_place_after_a_zoom(self) -> None:
        from playwright.sync_api import sync_playwright

        rect = """() => { const b = document.querySelector(".desk-window-shell.chair-window[aria-label='Needs you']").getBoundingClientRect();
                          return [Math.round(b.left), Math.round(b.top), Math.round(b.width), Math.round(b.height)]; }"""
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                shell = page.locator(".desk-window-shell.chair-window[aria-label='Needs you']")

                def open_brief() -> None:
                    # Betterment shell S0 (#1257): an empty desk's Window
                    # menu holds one line; Go is the Chair window's door.
                    # Daily D5: the Brief retired into Today; Needs you is
                    # the Chair window with a tile place.
                    open_chair_window(page, "Needs you")
                    shell.wait_for()
                    page.wait_for_timeout(600)
                    _settle(page)

                # Phase 14 A1: Chair windows start closed. Open Needs you at
                # its tile place first; that place is what a zoom must return to.
                if not shell.count():
                    open_brief()
                home = page.evaluate(rect)
                shell.get_by_role("button", name="Zoom Needs you").click()
                page.wait_for_timeout(500)
                shell.get_by_role("button", name="Zoom Needs you").click()
                page.wait_for_timeout(500)
                assert page.evaluate(rect) == home
                shell.get_by_role("button", name="Close Needs you").click()
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
