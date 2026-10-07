"""PHILO-13-08 (B3) -- Decide where the meeting is, fenced AS RENDERED through
the real hub on an isolated HOME, at 1440 (mouse) and 393 (touch).

Every state comes from a real producer:

* the meeting: the real meeting repository (``db.meetings.save_meeting``)
  with transcript segments and an intel snapshot (summary);
* the project and its meeting: the real routes (``POST /api/projects``,
  ``POST /api/projects/{id}/meetings/{mid}``).

Each case: the record open -> ``Decide`` (gesture 1) -> type the title and
confirm (gesture 2: Enter at 1440, a tap on Save at 393) -> the receipt in
the meeting -> the decision read back from the hub and from its DB (title,
the meeting, the project) -> the receipt row opens the decision's own window.
Then the abandoned tries (the meeting's Cancel, ⌘K New Decision closed
unnamed): no ``New decision`` row exists anywhere in the DB.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the decide glass needs Playwright")

TOKEN = "philo13-08-decide"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-08-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
MEETING = "p13-checkout"
MEETING_TITLE = "Checkout latency review"
MEETING_B = "p13-hiring"
MEETING_B_TITLE = "Hiring debrief"
RECEIPT = re.compile(r"^✓ DECIDED \d\d:\d\d$")


def _seed_meeting(db: Any) -> None:
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db.meetings.save_meeting(MeetingState(
        id=MEETING, started_at=datetime(2026, 10, 1, 9, 0, 0), ended_at=datetime(2026, 10, 1, 9, 30, 0),
        title=MEETING_TITLE,
        segments=[
            TranscriptSegment(text="p99 doubled after the cache change.", speaker="Avery", start_time=0.0, end_time=3.0),
            TranscriptSegment(text="We roll it back today.", speaker="Priya", start_time=4.0, end_time=8.0),
        ],
        intel=IntelSnapshot(timestamp=8.0, topics=["Latency"], summary="p99 doubled after the cache change.",
                            action_items=[{"id": "p13-08-a1", "task": "Roll back the cache", "owner": "Priya"}])))


def _seed_second_meeting(db: Any) -> None:
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db.meetings.save_meeting(MeetingState(
        id=MEETING_B, started_at=datetime(2026, 9, 30, 14, 0, 0), ended_at=datetime(2026, 9, 30, 14, 20, 0),
        title=MEETING_B_TITLE,
        segments=[TranscriptSegment(text="We hire for the platform team.", speaker="Sam", start_time=0.0, end_time=3.0)],
        intel=IntelSnapshot(timestamp=3.0, topics=["Hiring"], summary="Run a second ops interview.",
                            action_items=[])))


def _decision_rows(db: Any) -> list[dict[str, Any]]:
    """Every desk decision in the hub's own DB (deleted ones too)."""
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT id, title, context_markdown, tags_json, deleted FROM desk_decisions ORDER BY created_at"
        ).fetchall()
    return [{"id": r[0], "title": r[1], "context": r[2], "tags": json.loads(r[3] or "[]"), "deleted": r[4]}
            for r in rows]


def _project_edges(db: Any, decision_id: str) -> list[str]:
    """The Project edges of a desk decision, under its one ref name.

    Since #770 a desk decision is `desk_decision:<id>` in project_resources
    (the name memory, Send and grounding read). A row under the old name
    `decision:<id>` is a defect: the query reads both and the name is asserted.
    """
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT project_id, resource_ref FROM project_resources "
            "WHERE resource_ref IN (?, ?) AND deleted = 0",
            (f"desk_decision:{decision_id}", f"decision:{decision_id}"),
        ).fetchall()
    assert all(r[1] == f"desk_decision:{decision_id}" for r in rows), [tuple(r) for r in rows]
    return [r[0] for r in rows]


class TestDecideGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        touch = width <= 720
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=touch, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        self.touch = touch
        return browser, page, errors

    def _press(self, loc: Any) -> None:
        """His press: a tap at 393 (touch), a click at 1440 (mouse)."""
        loc.scroll_into_view_if_needed()
        if self.touch:
            loc.tap()
        else:
            loc.click()

    def _project(self, page: Any) -> str:
        created = _api(page, "POST", "/api/projects", {
            "name": "Checkout", "description": "The checkout path.", "command_id": "p13-08-project",
        }, token=TOKEN)
        project_id = created["project"]["id"]
        _api(page, "POST", f"/api/projects/{project_id}/meetings/{MEETING}", {}, token=TOKEN)
        return project_id

    @staticmethod
    def _shot(page: Any, name: str, width: int) -> None:
        _settle(page)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))

    def _meetings_record(self, page: Any) -> Any:
        """The Meetings window with the meeting's record open."""
        page.evaluate("""() => { localStorage.removeItem('hs.desk.workspace.v1');
            sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'review-meetings'})); }""")
        page.reload(wait_until="load")
        _normal_chair(page)
        page.get_by_test_id("meetings-headline").wait_for(timeout=T)
        page.wait_for_timeout(600)
        self._press(page.get_by_test_id(f"meeting-row-{MEETING}").locator(".meetings-stream-row-body"))
        well = page.get_by_test_id("meeting-decide-well").first
        well.wait_for(timeout=T)
        return well

    def _box44(self, loc: Any) -> None:
        """At 393 every target owns a 44 x 44 box (workbench-look §5)."""
        if not self.touch:
            return
        box = loc.bounding_box()
        assert box and box["width"] >= 44 and box["height"] >= 44, box

    def _decide(self, page: Any, well: Any, title: str) -> int:
        """Decide -> type -> confirm. Returns the gestures he made."""
        gestures = 0
        decide = well.get_by_role("button", name="Decide", exact=True)
        decide.scroll_into_view_if_needed()
        self._box44(decide)
        self._press(decide)
        gestures += 1
        box = well.get_by_role("textbox", name="Decision title")
        box.wait_for(timeout=T)
        page.wait_for_timeout(120)  # the well's autofocus
        assert page.evaluate("() => document.activeElement?.getAttribute('aria-label')") == "Decision title", \
            "the title well is not focused: typing would need another tap"
        self._shot(page, "02-decide-title-well", page.viewport_size["width"])
        for verb in ("Save", "Cancel"):
            self._box44(well.get_by_role("button", name=verb, exact=True))
        self._box44(box)
        page.keyboard.type(title)
        if self.touch:
            self._press(well.get_by_role("button", name="Save", exact=True))
        else:
            page.keyboard.press("Enter")
        gestures += 1  # type + confirm
        return gestures

    def _switch_to(self, page: Any, meeting_id: str) -> None:
        """Select another meeting in the SAME Meetings record."""
        if not self.touch:
            # A Meetings reload draws the list's loading line in place of the
            # rows (SurfaceState, Surface.tsx:232), so a row can detach under
            # the press right after a decision lands. He presses the row once
            # it is drawn again.
            row = page.get_by_test_id(f"meeting-row-{meeting_id}").locator(".meetings-stream-row-body")
            for attempt in range(3):
                try:
                    row.wait_for(timeout=T)
                    self._press(row)
                    return
                except Exception as error:  # noqa: BLE001 - only a detach is retried
                    if "not attached" not in str(error) or attempt == 2:
                        raise
                    page.wait_for_timeout(300)
            return
        # 393: one window at a time, and the record folds its list. He sends
        # Meetings to the back (it stays open, the same record), steps to the
        # Chair's week and presses Open on the other meeting: the Meetings
        # window comes back with that meeting selected (HistoryCore's scope).
        title = MEETING_B_TITLE if meeting_id == MEETING_B else MEETING_TITLE
        self._press(page.get_by_role("button", name="To back Meetings", exact=True))
        page.wait_for_timeout(400)
        # PHILO-14 A1 (#939): the Chair's windows start closed; he opens The
        # week from Go (a no-op when it is already shown).
        open_chair_window(page, "The week")
        opener = page.locator("li, .surface-row", has_text=title).get_by_test_id("arrival-meeting-open").first
        for _ in range(6):
            if opener.count() and opener.is_visible():
                break
            front = page.evaluate("""() => [...document.querySelectorAll('.desk-window-shell')]
                .filter((w) => w.checkVisibility() && w.getBoundingClientRect().width > 0 && w.getAttribute('aria-label') !== 'Meetings')
                .map((w) => w.getAttribute('aria-label'))[0] || null""")
            assert front, "no Chair window to step past"
            self._press(page.get_by_role("button", name=f"To back {front}", exact=True))
            page.wait_for_timeout(400)
        self._press(opener)
        page.locator(".desk-window-shell[aria-label='Meetings']").wait_for(timeout=T)

    def _read_back(self, page: Any, decision_id: str, project_id: str) -> dict[str, Any]:
        hub = _api(page, "GET", f"/api/decisions/{decision_id}", token=TOKEN)["decision"]
        rel = _api(page, "GET", f"/api/desk/relationships/decision:{decision_id}", token=TOKEN)
        projects = [str(p.get("project_id") or p.get("id") or "") for p in rel.get("projects", [])]
        return {"hub": hub, "projects": projects, "edges": _project_edges(self.db, decision_id)}

    # ── the cases ────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_decide_in_the_meetings_record(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        _seed_meeting(self.db)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                project_id = self._project(page)
                well = self._meetings_record(page)
                self._shot(page, "01-meetings-record-decide", width)
                title = f"Roll back the cache change {width}"
                gestures = self._decide(page, well, title)
                receipt = page.get_by_test_id("decide-receipt")
                receipt.wait_for(timeout=T)
                assert RECEIPT.match(receipt.inner_text().strip()), receipt.inner_text()
                assert gestures == 2, gestures
                self._shot(page, "03-decide-receipt-in-record", width)

                rows = [r for r in _decision_rows(self.db) if r["title"] == title]
                assert len(rows) == 1, _decision_rows(self.db)
                row = rows[0]
                assert row["tags"] == [f"meeting:{MEETING}", f"project:{project_id}"], row
                assert row["context"].startswith(f"Meeting: {MEETING_TITLE} · 2026-10-01"), row
                back = self._read_back(page, row["id"], project_id)
                assert back["hub"]["title"] == title
                assert f"meeting:{MEETING}" in back["hub"]["tags"], back
                assert back["edges"] == [project_id], back
                assert project_id in back["projects"], back

                # The receipt row opens the decision in its own window (B1).
                self._press(well.locator(".surface-row", has_text=title).first.locator("button, [role=button]").first)
                win = page.locator(f".desk-pullout[aria-label*='{title[:20]}']").first
                win.wait_for(timeout=T)
                self._shot(page, "04-decision-own-window", width)
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_decide_in_the_meeting_window_and_abandoned_tries(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        _seed_meeting(self.db)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                project_id = self._project(page)
                page.goto(f"{self.base}/?token={TOKEN}&open=meeting:{MEETING}", wait_until="load")
                _normal_chair(page)
                well = page.locator(".desk-pullout [data-testid=meeting-decide-well]").first
                well.wait_for(timeout=T)
                self._shot(page, "05-meeting-window-decide", width)

                # Abandoned try 1: Decide -> type -> Cancel.
                self._press(well.get_by_role("button", name="Decide", exact=True))
                well.get_by_role("textbox", name="Decision title").fill("Half a thought")
                self._press(well.get_by_role("button", name="Cancel", exact=True))
                # Abandoned try 2: ⌘K -> New Decision -> close unnamed.
                page.keyboard.press("Meta+k") if not self.touch else self._press(
                    page.get_by_role("button", name=re.compile(r"^Search")).first)
                deck = page.locator("#desk-tool-shelf")
                deck.wait_for(timeout=T)
                page.keyboard.type("New Decision")
                self._press(page.locator("[id='desk-palette-option-desk.new-decision']"))
                name = page.get_by_test_id("palette-name")
                name.wait_for(timeout=T)
                self._shot(page, "06-palette-asks-the-title", width)
                page.keyboard.press("Escape")
                deck.wait_for(state="detached", timeout=T)
                page.wait_for_timeout(400)
                assert _decision_rows(self.db) == [], _decision_rows(self.db)

                # The meeting window decides in two gestures.
                title = f"Keep the canary {width}"
                assert self._decide(page, well, title) == 2
                page.get_by_test_id("decide-receipt").wait_for(timeout=T)
                self._shot(page, "07-meeting-window-receipt", width)
                rows = _decision_rows(self.db)
                assert [r["title"] for r in rows] == [title], rows
                assert rows[0]["tags"] == [f"meeting:{MEETING}", f"project:{project_id}"], rows
                assert _project_edges(self.db, rows[0]["id"]) == [project_id]

                # ⌘K New Decision named: one row with his title.
                page.keyboard.press("Meta+k") if not self.touch else self._press(
                    page.get_by_role("button", name=re.compile(r"^Search")).first)
                deck.wait_for(timeout=T)
                page.keyboard.type("New Decision")
                self._press(page.locator("[id='desk-palette-option-desk.new-decision']"))
                page.get_by_test_id("palette-name").wait_for(timeout=T)
                self._box44(page.get_by_test_id("palette-name-save"))
                page.keyboard.type(f"Adopt feature flags {width}")
                if self.touch:
                    self._press(page.get_by_test_id("palette-name-save"))
                else:
                    page.keyboard.press("Enter")
                page.locator(f".desk-pullout[aria-label*='Adopt feature flags']").first.wait_for(timeout=T)
                self._shot(page, "08-palette-named-decision", width)
                titles = [r["title"] for r in _decision_rows(self.db)]
                assert titles == [title, f"Adopt feature flags {width}"], titles
                assert "New decision" not in titles
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_draft_never_moves_to_another_meeting(self, width: int) -> None:
        """Astra's single pass: a title typed under A, then B selected, then
        Save -- A's title filed under B. Now the draft stays with A."""
        from playwright.sync_api import sync_playwright

        _seed_meeting(self.db)
        _seed_second_meeting(self.db)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                project_id = self._project(page)
                well = self._meetings_record(page)  # meeting A selected
                self._press(well.get_by_role("button", name="Decide", exact=True))
                well.get_by_role("textbox", name="Decision title").fill("Typed under A")
                self._shot(page, "09-draft-under-a", width)
                # He opens meeting B in the same record: the list row at 1440;
                # at 393 the list folds behind the record, so the Chair's Open.
                self._switch_to(page, MEETING_B)
                page.get_by_text(MEETING_B_TITLE, exact=True).last.wait_for(timeout=T)
                well_b = page.get_by_test_id("meeting-decide-well").first
                well_b.wait_for(timeout=T)
                assert well_b.get_by_role("textbox", name="Decision title").count() == 0, \
                    "A's unfinished title is in B's well"
                save = well_b.get_by_role("button", name="Save", exact=True)
                if save.count():
                    self._press(save)
                    page.wait_for_timeout(600)
                assert _decision_rows(self.db) == [], _decision_rows(self.db)
                self._shot(page, "10-meeting-b-no-draft", width)
                # B's own decision files under B only.
                assert self._decide(page, well_b, "Typed under B") == 2
                page.get_by_test_id("decide-receipt").wait_for(timeout=T)
                rows = _decision_rows(self.db)
                assert [(r["title"], r["tags"]) for r in rows] == [("Typed under B", [f"meeting:{MEETING_B}"])], rows
                assert rows[0]["context"].startswith(f"Meeting: {MEETING_B_TITLE}"), rows
                # Back on A: A's own draft returns and files under A.
                self._switch_to(page, MEETING)
                box = page.get_by_test_id("meeting-decide-well").first.get_by_role("textbox", name="Decision title")
                box.wait_for(timeout=T)
                assert box.input_value() == "Typed under A"
                self._shot(page, "11-back-on-a-own-draft", width)
                self._press(page.get_by_test_id("meeting-decide-well").first.get_by_role("button", name="Save", exact=True))
                page.wait_for_function("() => !document.querySelector('[data-testid=decide-naming]')", timeout=T)
                rows = _decision_rows(self.db)
                by_title = {r["title"]: r["tags"] for r in rows}
                assert by_title == {
                    "Typed under B": [f"meeting:{MEETING_B}"],
                    "Typed under A": [f"meeting:{MEETING}", f"project:{project_id}"],
                }, rows
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()
