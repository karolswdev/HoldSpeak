"""PHILO-13-02 (A1-F) -- Park, never delete, fenced AS RENDERED through the
real hub on an isolated HOME, at 1440 (mouse) and 393 (touch).

Built to the owner-ratified C1 artboard "Parked and Restore" (story 11,
boards C1-5a–j; ratified 2026-10-02: Park is ONE press with no confirm,
because Restore undoes it).

Every state comes from a real producer:

* the meetings: the real meeting repository (``db.meetings.save_meeting``)
  with transcript segments, an intel snapshot (summary + action item) and an
  artifact recorded through ``db.plugins.record_artifact``;
* the Workbench and its items: the real routes (``POST /api/workbenches``,
  ``POST .../items``, ``PUT .../items/{id}`` for the done states); the
  item's artifact through ``db.plugins.record_artifact`` with a
  ``workbench_item:`` source;
* the run's claim: the runner's own claim statement
  (``holdspeak/services/workbench_runner.py:257``), run after the face read
  the item, so the claim lands between the read and the press.

Each case runs producer -> park -> the row read back from the DB (kept,
parked) -> the Parked filter -> Restore -> the row read back (kept, active)
-> a reload of the page.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_readable, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the park glass needs Playwright")

TOKEN = "philo13-02-park"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-02-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
CLOCK = re.compile(r"^PARKED \d\d:\d\d$")
WINDOW_WAIT_MS = 9_000  # past the old 8 s Undo window


def _seed_meetings(db: Any) -> None:
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    def segs(text: str) -> list[TranscriptSegment]:
        return [
            TranscriptSegment(text=f"{text} one.", speaker="Avery", start_time=0.0, end_time=3.0),
            TranscriptSegment(text=f"{text} two.", speaker="Priya", start_time=4.0, end_time=8.0),
        ]

    db.meetings.save_meeting(MeetingState(
        id="p13-sync", started_at=datetime(2026, 10, 1, 9, 0, 0), ended_at=datetime(2026, 10, 1, 9, 30, 0),
        title="Ledger cutover sync", segments=segs("We freeze the ledger"),
        intel=IntelSnapshot(timestamp=8.0, topics=["Cutover"], summary="Freeze the old ledger on Nov 5.",
                            action_items=[{"id": "p13-a1", "task": "Draft the rollback plan", "owner": "Jordan"}])))
    db.meetings.save_meeting(MeetingState(
        id="p13-hiring", started_at=datetime(2026, 9, 28, 14, 0, 0), ended_at=datetime(2026, 9, 28, 14, 45, 0),
        title="Hiring debrief: staff engineer", segments=segs("We hire for the platform team"),
        intel=IntelSnapshot(timestamp=8.0, topics=["Hiring"], summary="Run a second ops interview.",
                            action_items=[{"id": "p13-a2", "task": "Book the second interview", "owner": "Sam"}])))
    db.plugins.record_artifact(
        artifact_id="p13-hiring-artifact", meeting_id="p13-hiring", artifact_type="handoff",
        title="Hiring handoff", body_markdown="The body stays while parked.")


def _meeting_rows(db: Any, meeting_id: str) -> dict[str, Any]:
    """The meeting row and its retained work, read from the hub's own DB."""
    with db._connection() as conn:
        row = conn.execute("SELECT parked FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        count = lambda sql: conn.execute(sql, (meeting_id,)).fetchone()[0]  # noqa: E731
        return {
            "present": row is not None,
            "parked": None if row is None else int(row[0]),
            "segments": count("SELECT COUNT(*) FROM segments WHERE meeting_id = ?"),
            "intel": count("SELECT COUNT(*) FROM intel_snapshots WHERE meeting_id = ?"),
            "actions": count("SELECT COUNT(*) FROM action_items WHERE meeting_id = ?"),
            "artifacts": count("SELECT COUNT(*) FROM artifacts WHERE meeting_id = ?"),
        }


def _item_row(db: Any, item_id: str) -> dict[str, Any]:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT parked, status, title FROM workbench_items WHERE id = ?", (item_id,)
        ).fetchone()
        links = conn.execute(
            "SELECT COUNT(*) FROM artifact_sources WHERE source_ref = ?", (f"workbench_item:{item_id}",)
        ).fetchone()[0]
    return {"present": row is not None, "parked": None if row is None else int(row[0]),
            "status": None if row is None else row[1], "links": links}


class TestParkGlass:
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
                                  device_scale_factor=1, has_touch=touch,
                                  # The Floor's still mode (one_delete glass, STILL_FLOOR).
                                  reduced_motion="reduce")
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

    @staticmethod
    def _meetings(page: Any) -> None:
        # PHILO-16 (16b): the hub remembers the windows; clear them there too.
        from .glass_infra import clear_hub_windows

        clear_hub_windows(page, TOKEN)
        page.evaluate("""() => { localStorage.removeItem('hs.desk.workspace.v1');
            sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'review-meetings'})); }""")
        page.reload(wait_until="load")
        _normal_chair(page)
        page.get_by_test_id("meetings-headline").wait_for(timeout=T)
        # PHILO-16 (16b): the hub restores the Chair's windows beside the
        # staged Meetings; which one lands in front depends on which page
        # wrote first. The owner brings Meetings forward from its Dock door.
        page.locator(".desk-dock").get_by_role("button", name="Meetings", exact=True).click()
        page.wait_for_timeout(300)
        page.wait_for_timeout(600)

    @staticmethod
    def _receipt(page: Any, testid: str, pattern: str) -> str:
        page.wait_for_function(
            "([id, p]) => new RegExp(p).test(document.querySelector(`[data-testid=${id}] [role=status]`)?.innerText || '')",
            arg=[testid, pattern], timeout=T,
        )
        return page.locator(f"[data-testid={testid}] [role=status]").inner_text()

    @staticmethod
    def _shot(page: Any, name: str, width: int) -> None:
        """Every state's footer is read AS RENDERED before its shot: the
        receipt, the egress warning and the verbs are whole and apart."""
        _settle(page)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))
        _assert_readable(page, ".surface-footer-layout", f"{name}-{width}")

    def _clean(self, page: Any, errors: list[str]) -> None:
        real = [e for e in errors if "ResizeObserver" not in e]
        assert not real, real
        words = page.evaluate("() => document.body.innerText")
        assert "DELETED" not in words, "a DELETED receipt is on the glass"

    def _workbench(self, page: Any, wb: str) -> Any:
        """The Workbench window, opened by its desk link (``?open=``)."""
        page.goto(f"{self.base}/?token={TOKEN}&open=workbench:{wb}", wait_until="load")
        _normal_chair(page)
        window = page.locator(".desk-workbench-window")
        window.wait_for(timeout=T)
        page.wait_for_timeout(600)
        return window

    # ── Meetings (C1-5a–e) ───────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_meeting_park_parked_filter_restore_and_reload(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        _seed_meetings(self.db)
        before = _meeting_rows(self.db, "p13-hiring")
        assert before == {"present": True, "parked": 0, "segments": 2, "intel": 1, "actions": 1, "artifacts": 1}, before
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                self._meetings(page)
                assert page.get_by_text(re.compile(r"^PARKED \d+$")).count() == 0, "a PARKED token at zero"
                deletes: list[str] = []
                page.on("request", lambda r: deletes.append(r.url) if r.method == "DELETE" else None)
                # C1-5a: the selected record's footer verb is Park; no Delete.
                self._press(page.get_by_test_id("meeting-row-p13-hiring").locator(".meetings-stream-row-body"))
                park = page.get_by_role("button", name="Park", exact=True)
                park.wait_for(timeout=T)
                assert page.get_by_role("button", name=re.compile("^Delete")).count() == 0
                self._shot(page, "01-meeting-selected-park", width)
                # One press, no confirm.
                self._press(park)
                text = self._receipt(page, "meetings-park-receipt", r"^PARKED \d\d:\d\d$")
                assert CLOCK.match(text), text
                assert len(deletes) == 1 and deletes[0].endswith("/api/meetings/p13-hiring"), deletes
                page.get_by_test_id("meeting-row-p13-hiring").wait_for(state="detached", timeout=T)
                self._shot(page, "02-meeting-parked-receipt", width)
                # The row is in the DB, parked, with all its work.
                parked = _meeting_rows(self.db, "p13-hiring")
                assert parked == {**before, "parked": 1}, parked
                # C1-5c: the PARKED token; on, the parked rows with Restore.
                token = page.get_by_text("PARKED 1", exact=True)
                self._press(token)
                prow = page.get_by_test_id("parked-row")
                prow.wait_for(timeout=T)
                assert "Hiring debrief: staff engineer" in prow.inner_text()
                self._shot(page, "03-meetings-parked-filter", width)
                # Reload: still parked (the hub, not the client, holds it).
                self._meetings(page)
                assert _meeting_rows(self.db, "p13-hiring")["parked"] == 1
                assert page.get_by_test_id("meeting-row-p13-hiring").count() == 0
                self._press(page.get_by_text("PARKED 1", exact=True))
                prow = page.get_by_test_id("parked-row")
                prow.wait_for(timeout=T)
                # C1-5d: Restore -> the row comes back, in view, marked; RESTORED hh:mm.
                self._press(page.locator("li.surface-ledger-row", has=prow).get_by_role("button", name="Restore", exact=True))
                self._receipt(page, "meetings-park-receipt", r"^RESTORED \d\d:\d\d$")
                back = page.get_by_test_id("meeting-row-p13-hiring")
                back.wait_for(timeout=T)
                page.wait_for_function(
                    "() => document.querySelector('[data-testid=meeting-row-p13-hiring]')?.dataset.restored === 'true'",
                    timeout=T,
                )
                assert back.is_visible()
                assert page.get_by_text(re.compile(r"^PARKED \d+$")).count() == 0, "the token stays at zero"
                self._shot(page, "04-meeting-restored", width)
                assert _meeting_rows(self.db, "p13-hiring") == before
                # Reload: active, with the same rows.
                self._meetings(page)
                page.get_by_test_id("meeting-row-p13-hiring").wait_for(timeout=T)
                assert _meeting_rows(self.db, "p13-hiring") == before
                # C1-5e: a refused Restore names it with Retry; Retry restores.
                self._press(page.get_by_test_id("meeting-row-p13-hiring").locator(".meetings-stream-row-body"))
                self._press(page.get_by_role("button", name="Park", exact=True))
                self._receipt(page, "meetings-park-receipt", r"^PARKED ")
                refuse = lambda route: route.fulfill(status=500, content_type="application/json", body='{"error":"no"}')  # noqa: E731
                page.route("**/api/meetings/p13-hiring/restore", refuse)
                self._press(page.get_by_test_id("meetings-park-receipt").get_by_role("button", name="Restore", exact=True))
                failed = self._receipt(page, "meetings-park-receipt", "^NOT RESTORED")
                assert failed == "NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE", failed
                assert page.locator("[data-testid=meetings-park-receipt] [role=status]").get_attribute("data-tone") == "danger"
                assert _meeting_rows(self.db, "p13-hiring")["parked"] == 1
                self._shot(page, "05-meeting-restore-refused", width)
                page.unroute("**/api/meetings/p13-hiring/restore", refuse)
                self._press(page.get_by_test_id("meetings-park-receipt").get_by_role("button", name="Retry"))
                self._receipt(page, "meetings-park-receipt", r"^RESTORED ")
                assert _meeting_rows(self.db, "p13-hiring") == before
                print(f"meetings {width}: before {before}; parked {parked}; DELETE {deletes}")
                self._clean(page, errors)
            finally:
                browser.close()

    # ── the Workbench window (C1-5f–j) ───────────────────────────────────

    def _seed_workbench(self, page: Any) -> tuple[str, dict[str, str]]:
        wb = _api(page, "POST", "/api/workbenches", {"name": "Ledger cutover bench"}, token=TOKEN)["workbench"]["id"]
        ids: dict[str, str] = {}
        for title in ["Draft rollback runbook", "Old sampling spike", "Rerun shard benchmark", "Close the audit ticket"]:
            ids[title] = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": title}, token=TOKEN)["item"]["id"]
        for title in ["Rerun shard benchmark", "Close the audit ticket"]:
            _api(page, "PUT", f"/api/workbenches/{wb}/items/{ids[title]}", {"status": "done"}, token=TOKEN)
        self.db.plugins.record_artifact(
            artifact_id="p13-wb-artifact", meeting_id="", artifact_type="workbench_output",
            title="Spike result", body_markdown="Sampling at 1 in 10.",
            sources=[{"source_type": "input", "source_ref": f"workbench_item:{ids['Old sampling spike']}"}])
        return wb, ids

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_workbench_item_park_single_bulk_restore_and_reload(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                wb, ids = self._seed_workbench(page)
                spike = ids["Old sampling spike"]
                before = _item_row(self.db, spike)
                assert before == {"present": True, "parked": 0, "status": "pending", "links": 1}, before
                window = self._workbench(page, wb)
                assert window.get_by_role("button", name="Remove", exact=True).count() == 0
                # C1-5f: Park on the item (one press).
                self._press(window.get_by_text("Old sampling spike", exact=True))
                self._press(window.get_by_role("button", name="Park", exact=True))
                text = self._receipt(page, "wb-park-receipt", r"^PARKED \d\d:\d\d$")
                assert CLOCK.match(text), text
                window.get_by_text("Old sampling spike", exact=True).wait_for(state="detached", timeout=T)
                self._shot(page, "06-workbench-item-parked", width)
                assert _item_row(self.db, spike) == {**before, "parked": 1}
                # Past the old 8 s window: still present and parked.
                page.wait_for_timeout(WINDOW_WAIT_MS)
                assert _item_row(self.db, spike) == {**before, "parked": 1}
                normal = [i["id"] for i in _api(page, "GET", f"/api/workbenches/{wb}", token=TOKEN)["workbench"]["items"]]
                assert spike not in normal, normal
                # Reload: the PARKED token; on, the parked row with Restore (C1-5g).
                window = self._workbench(page, wb)
                self._press(window.get_by_text("PARKED 1", exact=True))
                prow = window.get_by_test_id("parked-row")
                prow.wait_for(timeout=T)
                assert "Old sampling spike" in prow.inner_text()
                self._shot(page, "07-workbench-parked-filter", width)
                # C1-5h: Restore brings it back with its links, marked.
                self._press(window.locator("li.surface-ledger-row", has=page.get_by_test_id("parked-row")).first.get_by_role("button", name="Restore", exact=True))
                self._receipt(page, "wb-park-receipt", r"^RESTORED \d\d:\d\d$")
                window.get_by_text("Old sampling spike", exact=True).wait_for(timeout=T)
                page.wait_for_function(
                    "() => [...document.querySelectorAll('.desk-workbench-window .wb-card[data-restored]')].length === 1",
                    timeout=T,
                )
                self._shot(page, "08-workbench-item-restored", width)
                assert _item_row(self.db, spike) == before
                # C1-5j: bulk "Clear done" parks both done items: PARKED 2 · hh:mm.
                done = [ids["Rerun shard benchmark"], ids["Close the audit ticket"]]
                self._press(window.get_by_role("button", name="Clear done", exact=True))
                bulk = self._receipt(page, "wb-park-receipt", r"^PARKED 2 · \d\d:\d\d$")
                assert re.match(r"^PARKED 2 · \d\d:\d\d$", bulk), bulk
                self._shot(page, "09-workbench-clear-done-parked", width)
                assert [_item_row(self.db, i)["parked"] for i in done] == [1, 1]
                page.wait_for_timeout(WINDOW_WAIT_MS)
                window = self._workbench(page, wb)
                assert [_item_row(self.db, i)["parked"] for i in done] == [1, 1]
                window.get_by_text("PARKED 2", exact=True).wait_for(timeout=T)
                # Restore each from the filter (the receipt's bulk Restore,
                # one request for all, is fenced in workbenchPark.test.tsx).
                for left in range(len(done), 0, -1):
                    token = window.get_by_text(f"PARKED {left}", exact=True)
                    token.wait_for(timeout=T)
                    page.wait_for_timeout(300)
                    self._press(token)
                    window.get_by_test_id("parked-row").first.wait_for(timeout=T)
                    self._press(window.locator("li.surface-ledger-row", has=page.get_by_test_id("parked-row")).first
                                .get_by_role("button", name="Restore", exact=True))
                    self._receipt(page, "wb-park-receipt", r"^RESTORED ")
                    window.get_by_text(f"PARKED {left}", exact=True).wait_for(state="detached", timeout=T)
                assert [_item_row(self.db, i) for i in done] == [
                    {"present": True, "parked": 0, "status": "done", "links": 0}
                ] * 2
                print(f"workbench {width}: before {before}; done {done}")
                self._clean(page, errors)
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_claimed_item_is_refused_in_place(self, width: int) -> None:
        """C1-5i: a run claims the item between the read and the press."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                wb, ids = self._seed_workbench(page)
                item = ids["Draft rollback runbook"]
                window = self._workbench(page, wb)
                self._press(window.get_by_text("Draft rollback runbook", exact=True))
                park = window.get_by_role("button", name="Park", exact=True)
                park.wait_for(timeout=T)
                # The runner's own claim statement (workbench_runner.py:257).
                with self.db._connection() as conn:
                    conn.execute(
                        "UPDATE workbench_items SET status='claimed', claimed_at=? WHERE id=? AND status='pending' AND parked=0",
                        (datetime.now().isoformat(), item),
                    )
                self._press(park)
                text = self._receipt(page, "wb-park-receipt", "^NOT PARKED")
                assert text == "NOT PARKED · CLAIMED BY A RUN", text
                receipt = page.get_by_test_id("wb-park-receipt")
                assert receipt.locator("[role=status]").get_attribute("data-tone") == "danger"
                assert receipt.get_by_role("button", name="Restore").count() == 0
                self._shot(page, "10-workbench-claimed-refused", width)
                row = _item_row(self.db, item)
                assert row["parked"] == 0 and row["status"] == "claimed", row
                print(f"claimed {width}: {text!r}; row {row}")
                self._clean(page, errors)
            finally:
                browser.close()
