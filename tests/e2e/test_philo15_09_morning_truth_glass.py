"""PHILO-15-09 -- the Morning tells the truth, as rendered (1440 and 393).

Rehearsal 1a (docs/internal/philo/phase-15/rehearsal-1a/BOUNCES.md):
  B04  after a full day the Brief said "No changes" and Generate returned the
       morning's brief; "Monday Brief" on a Wednesday; two date ranges.
  B07  The week with no calendar was an empty window.
  B11  the Needs-you head number was not the number of rows.

This rig makes the rehearsal's day on a fresh HOME (a meeting, a decision he
made, a person, a Project), generates the morning brief BEFORE it, presses
Generate in the Brief window after it, and shoots the three faces.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the morning glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

TOKEN = "philo15-09-morning"
SHOTS = evidence_dir("docs/internal/philo/phase-15/shots/09-morning-truth")
SIZES = {1440: 900, 393: 852}


def _the_rehearsal_day() -> None:
    """What the owner did in rehearsal 1a, through the real producers."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.people import production_people_store
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.primitive_service import PrimitiveService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    start = (datetime.now() - timedelta(minutes=20)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-day-one", started_at=start, ended_at=start + timedelta(seconds=35),
        title="Architect sync",
        segments=[TranscriptSegment(text="We adopt SQLite for the local meeting ledger.",
                                    speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="Three decisions.", action_items=[{
            "id": "m-day-one-a1", "task": "Write the migration plan", "owner": None, "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))
    PrimitiveService(db).create_decision(
        owner, decision_id="d-sqlite", title="Use SQLite for the local meeting ledger", status="accepted")
    db.projects.create_project(project_id="p-ledger", name="Local meeting ledger")
    store = production_people_store()
    store.initialize()
    PeopleService(store).create_relationship(owner, {"display_name": "Priya Shah", "relationship_kind": "direct_report"})


def _shell(page: Any, name: str) -> Any:
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


def _press(page: Any, loc: Any, width: int) -> None:
    loc.first.wait_for()
    if width < 720:
        loc.first.tap()
    else:
        loc.first.click()
    page.wait_for_timeout(300)


def _menu_pick(page: Any, width: int, name: str) -> None:
    if width < 720:
        _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
    else:
        _press(page, page.locator(".desk-verbbar-item[data-menu-id='window'] button"), width)
        page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')").hover()
    _press(page, page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"), width)


class TestTheMorningTellsTheTruth:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_brief_the_week_and_needs_you_after_a_full_day(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()
                # The morning: the day's brief before any work.
                morning = _api(page, "POST", "/api/brief/generate", token=TOKEN)
                _the_rehearsal_day()

                # B04: Generate in the Brief window makes the brief again.
                _menu_pick(page, width, "Brief")
                brief = _shell(page, "Brief")
                brief.wait_for()
                _press(page, brief.get_by_test_id("arrival-brief-generate"), width)
                receipt = brief.get_by_test_id("arrival-brief-receipt")
                receipt.wait_for()
                assert receipt.inner_text().startswith("GENERATED · "), receipt.inner_text()
                latest = _api(page, "GET", "/api/brief/latest", token=TOKEN)
                assert latest["id"] == morning["id"]
                assert latest["generated_at"] > morning["generated_at"]
                texts = [i["text"] for items in latest["sections"].values() for i in items]
                for wanted in ("Meeting recorded: Architect sync",
                               "Decision made: Use SQLite for the local meeting ledger",
                               "Project added: Local meeting ledger", "Person added"):
                    assert wanted in texts, (wanted, texts)
                assert latest["headline"] != "No changes"
                assert latest["title"].startswith("Brief · ") and "Monday Brief" not in latest["title"]
                assert latest["period_label"] in brief.get_by_test_id("arrival-brief-date").inner_text()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"after-brief-{width}.png"))

                # B07: The week with no calendar is never empty.
                _menu_pick(page, width, "The week")
                week = _shell(page, "The week")
                week.wait_for()
                week.get_by_test_id("week-no-calendar").wait_for()
                week.get_by_test_id("week-decision-row").first.wait_for()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"after-the-week-{width}.png"))

                # B11 + B12: the head is the row count; each row says its kind.
                _menu_pick(page, width, "Needs you")
                needs = _shell(page, "Needs you")
                needs.wait_for()
                needs.get_by_test_id("needs-drawer").wait_for()
                _settle(page)
                head = needs.get_by_test_id("arrival-display").inner_text().strip()
                rows = needs.locator("[data-testid='needs-list'] li.needs-row")
                count = rows.count()
                if count:
                    assert head.startswith(f"{count} "), (head, count)
                    for i in range(count):
                        assert rows.nth(i).get_by_test_id("needs-row-kind").count() == 1 or \
                            rows.nth(i).get_attribute("data-object-id", timeout=1000).startswith("blocker:")
                assert "Use SQLite for the local meeting ledger" not in needs.inner_text()
                page.screenshot(path=str(SHOTS / f"after-needs-you-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
