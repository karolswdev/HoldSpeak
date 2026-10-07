"""PHILO-14 A2b — Astra r1 on #945, on a real hub with the hub's own producers.

- A proposal row in Needs you opens the destination that CONTAINS it: the
  Room with that proposal selected (its Confirm on the row), never a drawer
  that lists no proposals (1440 and 393).
- A Room answer whose decisions section is `degraded` is a failed read in the
  drawer: `DECISIONS · NOT READ`, PARTIAL, no ON TRACK, one decision (no
  second copy), and Retry reads the Room again (1440 and 393).
- Prepare's DEC citation (`decision_record:<record id>`) opens the decision
  the record was made from: its meeting; it never reads
  `/api/decisions/record-…` (1440).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo14_a2_drawer_glass import MEETING, PROJECT, _seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="A2b glass needs Playwright")

TOKEN = "philo14-a2b-paths"
SHOTS = evidence_dir("p14-a2b")
SIZES = {1440: 900, 393: 852}
T = 20_000
PROPOSAL = "Run the dry run on Nov 3"


class TestA2bPathsGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database

        self.db = get_database()
        self.ids = _seed(self.db)
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    def _press(self, page: Any, locator: Any, width: int) -> None:
        if width < 720:
            locator.tap()
        else:
            locator.click()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_proposal_row_opens_the_room_with_the_proposal_selected(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

        # Two Projects need him (every row names its Project); each has a
        # pending proposal, the Room's own row with Confirm.
        start = datetime.now().replace(microsecond=0) - timedelta(hours=1)
        self.db.projects.create_project(project_id="p-infra", name="Infra budget", description="Q4.",
                                        keywords=["infra"])
        self.db.meetings.save_meeting(MeetingState(
            id="m-infra", started_at=start, ended_at=start + timedelta(minutes=20), title="Budget sync",
            segments=[TranscriptSegment(text="Cut the budget.", speaker="Me", start_time=1.0, end_time=3.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["budget"], summary="Cut it.", action_items=[]),
            intel_status="completed"))
        self.db.projects.associate_meeting_project(meeting_id="m-infra", project_id="p-infra", source="manual",
                                                   confidence=1.0)
        for mid, pid, text in (("m-sync", PROJECT, PROPOSAL), ("m-infra", "p-infra", "Cut the budget")):
            self.db.proposals.create_proposal(meeting_id=mid, project_id=pid, kind="action", text=text,
                                              source_plugin="a2b-glass")
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                needs_icon = page.locator(".desk-screen [data-object-id='drawer:needs']")
                needs_icon.wait_for(timeout=T)
                needs_icon.focus()
                page.keyboard.press("Enter")
                needs = page.locator(".desk-window-shell.chair-window[aria-label='Needs you']")
                # PHILO-14 A5b: the Needs-you window is the smart drawer; the
                # proposal is its object row and the row body is its open.
                row = needs.locator("li.needs-row[data-opens=true]").filter(has_text=PROPOSAL).first
                row.wait_for(timeout=T)
                _settle(page)
                self._press(page, row.locator(".needs-row-name").first, width)
                selected = page.locator(".surface-ledger-row[data-selected]:has([data-testid=proposal-row])")
                selected.wait_for(timeout=T)
                page.wait_for_timeout(500)
                page.screenshot(path=str(SHOTS / f"glass-proposal-room-{width}.png"))
                assert PROPOSAL in selected.inner_text()
                assert selected.locator("[data-testid=proposal-confirm]").count() == 1
                assert page.locator(".drawer-window").count() == 0  # never a drawer without it
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_degraded_decisions_read_is_named_and_retried(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.services.project_service import ProjectService

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # The real Room answer, its decisions section faulted the way
                # the producer reports a failed section.
                real = _api(page, "GET", f"/api/projects/{PROJECT}/room", None, token=TOKEN)

                def fail() -> Any:
                    raise RuntimeError("glass: decisions read failed")

                faulted = {**real, "decisions": ProjectService._room_section("decisions", fail)}
                assert faulted["decisions"]["state"] == "degraded", faulted["decisions"]
                served = {"faulted": 0}

                def fault(route: Any) -> None:
                    served["faulted"] += 1
                    route.fulfill(status=200, content_type="application/json", body=json.dumps(faulted))

                pattern = f"**/api/projects/{PROJECT}/room*"
                page.route(pattern, fault)
                page.goto(f"{self.base}/?token={TOKEN}&open=project:{PROJECT}", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                facts = drawer.locator("[data-testid=drawer-facts]")
                facts.wait_for(timeout=T)
                page.wait_for_function(
                    "() => /DECISIONS · NOT READ/.test(document.querySelector('.drawer-window [data-testid=drawer-facts]')?.textContent || '')",
                    timeout=T)
                page.wait_for_timeout(600)
                page.screenshot(path=str(SHOTS / f"glass-decisions-not-read-{width}.png"))
                text = facts.inner_text()
                assert "PARTIAL" in text and "ON TRACK" not in text, text
                refs = drawer.locator("[data-object-id]").evaluate_all("els => els.map(e => e.dataset.objectId)")
                decisions = [r for r in refs if r.startswith("decision")]
                assert decisions == [f"decision:{self.ids['decision']}"], refs  # one decision, no second copy
                # Retry reads the Room again; the hub answers whole now.
                page.unroute(pattern)
                before = served["faulted"]
                drawer.get_by_role("button", name="Retry", exact=True).click()
                page.wait_for_function(
                    "() => !/NOT READ/.test(document.querySelector('.drawer-window [data-testid=drawer-facts]')?.textContent || '')",
                    timeout=T)
                assert served["faulted"] == before
                assert drawer.locator("[data-testid=drawer-partial]").count() == 0
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_prepare_opens_a_decision_record_through_its_source(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            asked: list[str] = []
            page.on("request", lambda r: asked.append(r.url))
            try:
                prepared = _api(page, "POST", f"/api/projects/{PROJECT}/briefs/prepare",
                                {"purpose": "Ledger decision review", "generator": "deterministic"}, token=TOKEN)
                brief = prepared["brief"]
                assert any(d["ref"].startswith("decision_record:record-") for d in brief["manifest"]["decisions"]), brief
                _api(page, "POST", f"/api/briefs/{brief['id']}/keep", {}, token=TOKEN)
                page.goto(f"{self.base}/?token={TOKEN}&open=project:{PROJECT}", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.locator("[data-testid=drawer-facts]").wait_for(timeout=T)
                drawer.get_by_role("button", name="Room", exact=True).click()
                page.locator("[data-testid=room-brief-open]").first.click()
                claim = page.locator("[data-testid=prepare-claim-row]:has([data-testid=prepare-claim-ref]:has-text('DEC'))")
                claim.first.wait_for(timeout=T)
                _settle(page)
                claim.first.locator("[data-testid=prepare-claim-open]").click()
                page.wait_for_function(
                    """(name) => [...document.querySelectorAll('.desk-window-shell.is-front, .desk-window.is-front')]
                      .some((w) => (w.innerText || '').includes(name))""",
                    arg=MEETING, timeout=T)
                page.screenshot(path=str(SHOTS / "glass-prepare-record-open-1440.png"))
                assert any("/api/decision-records/record-" in u for u in asked), asked
                assert not any("/api/decisions/record-" in u for u in asked), [u for u in asked if "record-" in u]
                assert not errors, errors
            finally:
                browser.close()
