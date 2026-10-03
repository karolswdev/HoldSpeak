"""PHILO-13-13 C3-W -- the live Dock, fenced AS RENDERED.

Through the real hub on an isolated HOME, at 1440x900 (mouse) and 393x852
(touch), to the ratified C1 boards (C1-1, C1-8a-c):

* The shelf fits: no page scroll sideways; at 1440 the first AppIcon's name
  is whole (it was clipped off the left edge); at 393 the daily seats
  (Intelligence, Meetings, People, Speak) come first, whole, and More
  AppIcons moves the shelf one page.
* READY: a meeting saved with aftercare by the real producer
  (``MeetingSession.save`` -> the durable unseen row -> ``aftercare_ready``
  on the hub's bus) shows ``READY 1`` on Meetings; opening the meeting
  (the Meetings window row -> ``POST /ready/read``) clears it.
* SENT: a published update sent to a FILE destination in the HOME through
  the real routes shows ``SENT hh:mm`` on Intelligence, the time of the
  durable row's ``settled_at``.
* REC: a refused start (the real route's 501) shows no REC; a start the hub
  confirms (the route answers and broadcasts ``meeting_started``) shows
  ``REC hh:mm``. The capture device is the one stand-in: ``on_start``
  answers in place of a microphone (no physical recording here).
* OFFLINE: the hub stops; the Dock stays, one ``OFFLINE · AS OF hh:mm`` tag
  and no fresh tag or count; the Desk is never replaced by the error face.
* Every state read by the on-glass reader: zero clipped text, zero overlap.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Dock glass needs Playwright")

TOKEN = "philo13-13-dock"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-13-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
DOCK = ".desk-dock"


def _hhmm(iso: str) -> str:
    value = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if value.tzinfo is not None:
        value = value.astimezone()
    return value.strftime("%H:%M")


class _Capture:
    """The capture boundary: the first start is refused (no microphone),
    the second is confirmed by the hub. Stop answers stopped."""

    def __init__(self) -> None:
        self.calls = 0

    def start(self) -> Any:
        from holdspeak.services.errors import ValidationError

        self.calls += 1
        if self.calls == 1:
            raise ValidationError("No microphone is available")
        return {"id": "c3w-live", "title": "Live", "started_at": datetime.now().astimezone().isoformat()}

    def stop(self) -> Any:
        return {"status": "stopped"}


class TestLiveDock:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.capture = _Capture()
        # Resolved, so a destination under the HOME reads `~/…` on the face
        # (macOS's /var is /private/var; a scratch path is never drawn).
        root = tmp_path.resolve()
        server, base = _boot(root, monkeypatch, token=TOKEN,
                             on_start=self.capture.start, on_stop=self.capture.stop)
        self.server, self.base, self.home = server, base, root / "home"
        self.stopped = False
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            if not self.stopped:
                server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str], list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720,
                                  reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        posts: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.on("request", lambda r: posts.append(r.url.split("?")[0]) if r.method == "POST" else None)
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.locator(DOCK).wait_for()
        page.wait_for_timeout(1200)
        _settle(page)
        return browser, page, errors, posts

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
    def _shelf_home(page: Any) -> None:
        page.evaluate("() => { const d = document.querySelector('.desk-dock'); if (d) d.scrollLeft = 0; }")
        page.wait_for_timeout(150)

    def _read(self, page: Any, name: str, width: int, proof: dict[str, Any]) -> None:
        """The Dock, read on the glass: no clip, no overlap (the one ratified
        waiver: an AppIcon partly scrolled under More at 393), no page scroll."""
        _settle(page)
        page.screenshot(path=str(SHOTS / f"dock-{name}-{width}.png"))
        faults = _rendered_text_faults(page, DOCK, on_glass=True)
        more = [o for o in faults["overlaps"] if "More AppIcons" in (o[0], o[1])]
        other = [o for o in faults["overlaps"] if o not in more]
        if width >= 720:
            assert not more, more
        # The shelf is the one strip allowed to scroll sideways (design §6, §10;
        # canvas README: "The Dock is outside this rule by name"). The reader
        # flags every text of a sideways container; a text there is only
        # REACHED by the shelf's scroll, never cut: it is recorded, not failed.
        shelf = [c for c in faults["clipped"] if c.get("sideways") and c.get("in") == "desk-dock"]
        cut = [c for c in faults["clipped"] if c not in shelf]
        scroll = page.evaluate("() => { const d = document.querySelector('.desk-dock'); return [d.scrollWidth, d.clientWidth]; }")
        proof[name] = {"clipped": cut, "overlaps": other, "under_more": more, "shelf_scrolls": scroll,
                       "reached_by_shelf_scroll": [c["text"] for c in shelf],
                       "ellipsis": faults.get("ellipsis", [])}
        assert faults["scopes"], f"{name}: no visible Dock"
        assert not cut, f"{name}: {cut}"
        if name == "01-rest" and width >= 720:
            assert scroll[0] <= scroll[1], f"the 1440 shelf at rest scrolls: {scroll}"
        assert not other, f"{name}: {other}"
        page_x = page.evaluate("() => document.scrollingElement.scrollWidth - window.innerWidth")
        assert page_x <= 0, f"{name}: the page scrolls sideways by {page_x}px"
        box = page.locator(DOCK).bounding_box()
        assert box and box["x"] >= 0 and box["x"] + box["width"] <= width + 0.5, box

    def _refresh_from_hub(self, page: Any, width: int) -> None:
        """His "Refresh from hub" (desk.refresh), from the palette: the
        search shelf opens it at both widths."""
        field = page.locator("[aria-controls=desk-palette-listbox]")
        if not field.is_visible():
            self._press(page, page.locator("[aria-controls=desk-tool-shelf]"), width)
        field.fill("Refresh from hub")
        self._press(page, page.locator("[id='desk-palette-option-desk.refresh']"), width)

    def _outage_receipt(self, page: Any) -> dict[str, Any]:
        """The named failure, on the glass and usable: its exact words, and
        Retry and OK each own the point at their centre (nothing over them)."""
        words = "READ MEETINGS FAILED · HUB UNREACHABLE"
        label = page.locator(".write-receipt", has_text=words).first
        label.wait_for(timeout=T)
        _settle(page)  # the phone window yields to the receipt row in a layout pass; measure after it
        text = " ".join(label.locator(".write-receipt-label").inner_text().split())
        assert text == words, text
        owned: dict[str, Any] = {}
        for name in ("Retry", "OK"):
            button = label.get_by_role("button", name=name, exact=True)
            assert button.count() == 1, f"{name} is missing from the outage receipt"
            owned[name] = page.evaluate(
                """(el) => { const r = el.getBoundingClientRect();
                    const x = r.left + r.width / 2, y = r.top + r.height / 2;
                    const hit = document.elementFromPoint(x, y);
                    return { owned: !!hit && (hit === el || el.contains(hit)),
                             hit: hit ? (hit.className || hit.tagName) + '' : null,
                             in_viewport: x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight }; }""",
                button.element_handle())
            assert owned[name]["in_viewport"] and owned[name]["owned"], f"{name}: {owned[name]}"
        return {"text": text, "controls": owned}

    def _tag(self, page: Any, testid: str, pattern: str) -> str:
        page.wait_for_function(
            "([id, p]) => new RegExp(p).test(document.querySelector(`[data-testid=${id}]`)?.textContent || '')",
            arg=[testid, pattern], timeout=T,
        )
        return page.get_by_test_id(testid).text_content() or ""

    # ── the producers ────────────────────────────────────────────────────

    def _meeting_ready(self) -> str:
        from holdspeak.meeting_session import IntelSnapshot, MeetingSession, MeetingState

        session = MeetingSession(transcriber=None, on_broadcast=self.server.broadcast)
        session._state = MeetingState(
            id="c3w-ready", title="Ledger cutover sync",
            started_at=datetime(2026, 10, 2, 10, 0), ended_at=datetime(2026, 10, 2, 10, 30),
            intel=IntelSnapshot(timestamp=1.0, summary="Dual-write is stable.",
                                action_items=[{"id": "a1", "task": "Draft the rollback plan", "owner": "Me"}]),
        )
        assert session.save(self.home / "meetings-json").database_saved is True
        return "c3w-ready"

    def _send_to_file(self, page: Any) -> dict[str, Any]:
        project = _api(page, "POST", "/api/projects", {"name": "Payments ledger cutover"}, token=TOKEN)["project"]["id"]
        update = _api(page, "POST", f"/api/projects/{project}/updates/draft", {}, token=TOKEN)["update"]["id"]
        _api(page, "POST", f"/api/updates/{update}/publish", {}, token=TOKEN)
        folder = self.home / "Documents" / "HoldSpeak" / "Team updates"
        folder.mkdir(parents=True, exist_ok=True)
        dest = _api(page, "POST", "/api/channels/destinations",
                    {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)["destination"]["id"]
        send = _api(page, "POST", "/api/channels/sends",
                    {"document_ref": f"project_update:{update}", "destination_id": dest}, token=TOKEN)["send"]["id"]
        body = _api(page, "POST", "/api/channels/send", {"send_id": send}, token=TOKEN)
        assert body["outcome"] == "sent", body
        with self.db._connection() as conn:
            row = dict(conn.execute("SELECT state, settled_at FROM channel_sends WHERE id = ?", (send,)).fetchone())
        assert row["state"] == "sent" and row["settled_at"], row
        assert any(folder.iterdir()), "the FILE destination wrote nothing"
        return row

    # ── the fence ────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_dock_shows_his_day_live_and_stays_through_an_outage(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, posts = self._page(pw, width)
            proof: dict[str, Any] = {"width": width}
            try:
                dock = page.locator(DOCK)
                self._read(page, "01-rest", width, proof)
                first = dock.locator(".desk-dock-launch").first
                if width >= 720:
                    # The first AppIcon's name is whole and inside the shelf (it was clipped).
                    label = first.locator(".desk-dock-label")
                    lb, db = label.bounding_box(), dock.bounding_box()
                    assert lb and db and lb["x"] >= db["x"], (lb, db)
                    assert label.inner_text() == "Intelligence"
                else:
                    seats = page.evaluate("""() => {
                        const d = document.querySelector('.desk-dock');
                        const more = d.querySelector('.desk-dock-more').getBoundingClientRect();
                        return [...d.querySelectorAll('.desk-dock-launch')]
                          .map((b) => ({ app: b.dataset.app || b.getAttribute('aria-label'), r: b.getBoundingClientRect() }))
                          .filter((x) => x.r.right <= more.left + 0.5 && x.r.left >= 0)
                          .sort((a, b) => a.r.left - b.r.left).map((x) => x.app);
                    }""")
                    assert seats == ["intelligence:desk", "surface-meetings", "surface-people", "surface-dictation"], seats
                    before = page.evaluate("() => document.querySelector('.desk-dock').scrollLeft")
                    self._press(page, page.get_by_role("button", name="More AppIcons"), width)
                    page.wait_for_timeout(700)
                    after = page.evaluate("() => document.querySelector('.desk-dock').scrollLeft")
                    assert after > before, (before, after)
                    page.screenshot(path=str(SHOTS / f"dock-02-more-{width}.png"))
                    self._shelf_home(page)

                # READY after a meeting becomes ready; clears on open.
                meeting = self._meeting_ready()
                ready = self._tag(page, "desk-dock-meetings-state", r"^READY 1$")
                proof["ready"] = ready
                self._shelf_home(page)
                self._read(page, "03-ready", width, proof)
                self._press(page, dock.locator("[data-app='surface-meetings']"), width)
                row = page.get_by_test_id(f"meeting-row-{meeting}").locator(".meetings-stream-row-body")
                row.wait_for(timeout=T)
                self._press(page, row, width)
                page.get_by_test_id("desk-dock-meetings-state").wait_for(state="detached", timeout=T)
                assert any(p.endswith(f"/api/meetings/{meeting}/ready/read") for p in posts), posts
                assert self.db.meetings.list_unread_ready() == []
                self._shelf_home(page)
                self._read(page, "04-ready-cleared", width, proof)

                # SENT with its time.
                row = self._send_to_file(page)
                sent = self._tag(page, "desk-dock-send-state", r"^SENT \d\d:\d\d$")
                assert sent == f"SENT {_hhmm(row['settled_at'])}", (sent, row)
                proof["sent"] = sent
                self._shelf_home(page)
                self._read(page, "05-sent", width, proof)

                # REC only on the hub's confirmation.
                orb = dock.locator(".desk-orb").first
                self._press(page, orb, width)
                page.wait_for_timeout(1500)
                assert self.capture.calls == 1
                assert page.get_by_test_id("desk-dock-meetings-state").count() == 0, "REC after a refused start"
                self._shelf_home(page)
                self._read(page, "06-rec-refused", width, proof)
                self._press(page, orb, width)
                rec = self._tag(page, "desk-dock-meetings-state", r"^REC \d\d:\d\d$")
                assert self.capture.calls == 2
                assert page.get_by_test_id("desk-dock-meetings-state").get_attribute("data-tone") == "rec"
                proof["rec"] = rec
                self._shelf_home(page)
                self._read(page, "07-rec-confirmed", width, proof)

                # OFFLINE · AS OF; the Dock and the Desk stay.
                self.server.stop()
                self.stopped = True
                offline = page.get_by_test_id("desk-dock-offline")
                offline.wait_for(timeout=T)
                assert re.fullmatch(r"OFFLINE · AS OF \d\d:\d\d", offline.inner_text()), offline.inner_text()
                for tag in ("desk-dock-meetings-state", "desk-dock-send-state", "desk-dock-people-state"):
                    assert page.get_by_test_id(tag).count() == 0, f"{tag} claims freshness offline"
                assert dock.locator(".desk-dock-badge:visible").count() == 0, "a count claims freshness offline"
                # An actual failed Desk refresh: his "Refresh from hub", from the palette.
                self._refresh_from_hub(page, width)
                receipt = self._outage_receipt(page)
                proof["outage_receipt"] = receipt
                assert page.get_by_label("Preparing HoldSpeak").count() == 0, "the error face replaced the Desk"
                assert dock.is_visible() and offline.is_visible()
                page.screenshot(path=str(SHOTS / f"dock-08b-outage-receipt-{width}.png"))
                proof["offline"] = offline.inner_text()
                proof["receipt"] = page.evaluate(
                    "() => [...document.querySelectorAll('[role=status]')].map((n) => n.innerText).filter(Boolean)")
                # The tag heads the shelf at both widths: on the glass with the shelf at home.
                self._shelf_home(page)
                ob, dbx = offline.bounding_box(), dock.bounding_box()
                assert ob and dbx and ob["x"] >= dbx["x"] and ob["x"] + ob["width"] <= dbx["x"] + dbx["width"], (ob, dbx)
                self._read(page, "08-offline", width, proof)
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                (SHOTS / f"dock-proof-{width}.txt").write_text(repr(proof) + "\n")
                browser.close()
