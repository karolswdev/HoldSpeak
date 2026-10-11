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

from .glass_infra import open_project_drawer, _api, _boot, _ensure_build, _normal_chair, _settle
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
    @pytest.mark.parametrize("save", ["pending", "failed"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_proposal_request_never_saves_the_update_draft(self, width: int, save: str) -> None:
        """A5b (Muad'Dib's ruling on Astra r2): a proposal request never
        writes. He saves text A (the save is held, or it fails), types B,
        then opens a proposal from Needs you: no request carries B; when the
        held save of A lands, the reopened editor still reads B (the hub holds
        A, his explicit save, never A over a saved B); a failed save keeps its
        failure (at 1440, where the Room window stays mounted) and his text."""
        import re

        from playwright.sync_api import sync_playwright

        self.db.proposals.create_proposal(meeting_id="m-sync", project_id=PROJECT, kind="action", text=PROPOSAL,
                                          source_plugin="a2b-glass")
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                needs_icon = page.locator(".desk-screen [data-object-id='drawer:needs']")

                def raise_needs() -> Any:
                    if width < 720 and not needs_icon.is_visible():
                        page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                        page.locator(".desk-verbbar-menu").wait_for(timeout=T)
                        page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").first.click()
                    else:
                        needs_icon.wait_for(timeout=T)
                        needs_icon.focus()
                        page.keyboard.press("Enter")
                    needs = page.locator(".desk-window-shell.chair-window[aria-label='Needs you']")
                    row = needs.locator("li.needs-row[data-opens=true]").filter(has_text=PROPOSAL).first
                    row.wait_for(timeout=T)
                    _settle(page)
                    return row

                selected = page.locator(".surface-ledger-row[data-selected]:has([data-testid=proposal-row])")
                self._press(page, raise_needs().locator(".needs-row-name").first, width)
                selected.wait_for(timeout=T)

                # The Update editor on a fresh draft.
                self._press(page, page.get_by_test_id("updates-verb").first, width)
                self._press(page, page.get_by_test_id("update-verb-draft-deterministic").first, width)
                editor = page.get_by_test_id("update-body-editor").locator("[contenteditable=true]").first
                editor.wait_for(timeout=T)
                _settle(page)

                puts: list[str] = []
                held: list[Any] = []

                def handle(route: Any) -> None:
                    if route.request.method != "PUT":
                        route.continue_()
                        return
                    puts.append(route.request.post_data or "")
                    if save == "failed":
                        route.fulfill(status=500, body='{"detail":"injected failure"}',
                                      content_type="application/json")
                    else:
                        held.append(route)  # answered later: the save of A is in flight

                page.route(re.compile(r".*/api/updates/[^/]+$"), handle)
                self._press(page, editor, width)
                page.keyboard.press("Control+End")
                page.keyboard.type(" AAA-saved-words")
                self._press(page, page.get_by_test_id("update-verb-save").first, width)
                if save == "failed":
                    page.get_by_text("NOT SAVED").first.wait_for(timeout=T)
                else:
                    for _ in range(50):
                        if held:
                            break
                        page.wait_for_timeout(100)
                    assert held, "the save of A never left"
                self._press(page, editor, width)
                page.keyboard.press("Control+End")
                page.keyboard.type(" BBB-newer-words")
                page.wait_for_timeout(300)
                assert len(puts) == 1, puts

                # The proposal again, from Needs you: the Room shows it.
                self._press(page, raise_needs().locator(".needs-row-name").first, width)
                selected.wait_for(state="visible", timeout=T)
                page.wait_for_timeout(500)
                assert len(puts) == 1, f"a proposal request wrote: {puts}"
                assert "BBB" not in puts[0], puts
                if held:
                    held.pop().continue_()
                    page.wait_for_timeout(800)

                # Back in Update: his newest words, unsaved; a failure still named.
                self._press(page, page.get_by_test_id("updates-verb").first, width)
                listed = page.get_by_test_id("update-list-item")
                if not editor.is_visible():
                    listed.first.wait_for(timeout=T)
                    self._press(page, listed.first, width)
                editor.wait_for(timeout=T)
                _settle(page)
                text = editor.inner_text()
                assert "BBB-newer-words" in text and "AAA-saved-words" in text, text
                assert "UNSAVED" in (page.get_by_test_id("update-footer-receipt").first.text_content() or "")
                if save == "failed" and width >= 720:
                    assert page.get_by_text("NOT SAVED").first.is_visible()
                assert len(puts) == 1, puts
                stored = _api(page, "GET", f"/api/projects/{PROJECT}/updates", None, token=TOKEN)
                bodies = json.dumps(stored)
                assert "BBB-newer-words" not in bodies, "the hub holds B: a proposal request saved"
                if save == "pending":
                    assert "AAA-saved-words" in bodies, "his explicit save of A did not land"
                page.screenshot(path=str(SHOTS / f"glass-proposal-keeps-draft-{save}-{width}.png"))
                assert not [e for e in errors if "injected" not in e], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("away", ["history", "update"])
    @pytest.mark.parametrize("via", ["row", "room-verb"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_proposal_reopened_over_history_is_revealed(self, width: int, via: str, away: str) -> None:
        """A5b (Astra r1 on #965): the proposal's Room is already open on its
        History wing (or in its Update posture); the same proposal pressed
        again in Needs you (its row body, or its Room verb) brings the Room
        back to its ROOM wing with THAT proposal selected and on screen."""
        from playwright.sync_api import sync_playwright

        self.db.proposals.create_proposal(meeting_id="m-sync", project_id=PROJECT, kind="action", text=PROPOSAL,
                                          source_plugin="a2b-glass")
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                needs_icon = page.locator(".desk-screen [data-object-id='drawer:needs']")

                def raise_needs() -> Any:
                    if width < 720 and not needs_icon.is_visible():
                        # At 393 the Room covers the screen: Go ▸ Needs you.
                        page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                        page.locator(".desk-verbbar-menu").wait_for(timeout=T)
                        page.locator(".desk-menu-list [role='menuitemcheckbox']:has-text('Needs you')").first.click()
                    else:
                        needs_icon.wait_for(timeout=T)
                        needs_icon.focus()
                        page.keyboard.press("Enter")
                    needs = page.locator(".desk-window-shell.chair-window[aria-label='Needs you']")
                    row = needs.locator("li.needs-row[data-opens=true]").filter(has_text=PROPOSAL).first
                    row.wait_for(timeout=T)
                    _settle(page)
                    return row

                def press_proposal(row: Any) -> None:
                    target = (row.locator(".needs-row-name").first if via == "row"
                              else row.get_by_role("button", name=f"Room: {PROPOSAL}"))
                    self._press(page, target, width)

                selected = page.locator(".surface-ledger-row[data-selected]:has([data-testid=proposal-row])")
                press_proposal(raise_needs())
                selected.wait_for(timeout=T)
                # The Room goes to History (or Update): the proposal is not drawn there.
                if away == "history":
                    self._press(page, page.get_by_role("tab", name="History").first, width)
                else:
                    self._press(page, page.get_by_role("button", name="Draft update").first, width)
                    page.locator("[data-testid=update-posture]").first.wait_for(timeout=T)
                selected.wait_for(state="detached", timeout=T)
                _settle(page)
                # Needs you again, the same proposal again.
                press_proposal(raise_needs())
                selected.wait_for(state="visible", timeout=T)
                page.wait_for_timeout(400)
                assert PROPOSAL in selected.inner_text()
                assert page.get_by_role("tab", name="Room").first.get_attribute("aria-selected") == "true"
                box = selected.bounding_box()
                assert box and 0 <= box["y"] and box["y"] + box["height"] <= SIZES[width], box
                assert page.locator(".drawer-window").count() == 0
                page.screenshot(path=str(SHOTS / f"glass-proposal-over-{away}-{via}-{width}.png"))
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
                open_project_drawer(page, self.base, PROJECT, TOKEN)  # PHILO-17 U30: the parked drawer, by its key
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
                open_project_drawer(page, self.base, PROJECT, TOKEN)  # PHILO-17 U30: the parked drawer, by its key
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
