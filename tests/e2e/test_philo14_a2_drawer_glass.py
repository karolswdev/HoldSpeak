"""PHILO-14 A2 — a Project opens as a drawer, on a real hub (Astra r1 on #937).

Every member is made by the hub's own producers (a meeting with its action
item, the meeting's recorded decision and its decision record, an artifact,
a note filed in the Project), and every Open is followed to its real window:

- each member kind opens the window its identity names (the decision opens
  through the `decisions` row its record names, never the record's id; the
  action item opens its Follow-through card);
- a generic Project open (`?open=project:<id>`, the Project primitive) lands
  in the drawer, never in the Room; the drawer's Room verb opens the Room;
- the drawer, its view and its place come back after a reload (B2);
- Park on a meeting leaves `PARKED · <name>` with Restore on the drawer, also
  when the drawer is left empty; Restore brings the member back;
- A2b: the Needs you row's Project button opens the drawer, never the Room.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="drawer glass needs Playwright")

TOKEN = "philo14-a2-drawer"
SHOTS = evidence_dir("p14-a2")
SIZES = {1440: 900, 393: 852}
T = 20_000

PROJECT, LONE = "p-ledger", "p-lone"
MEETING, LONE_MEETING = "Ledger cutover sync", "Vendor call"
ACTION = "Write the rollback runbook"
DECISION = "Freeze the old ledger on Nov 5"
ARTIFACT = "Cutover requirements"
NOTE = "Ledger cutover risks"

FRONT_JS = r"""(name) => [...document.querySelectorAll('.desk-window-shell.is-front, .desk-window.is-front')]
  .filter((w) => !w.classList.contains('drawer-window'))
  .some((w) => (w.innerText || '').includes(name))"""


def _seed(db: Any) -> dict[str, str]:
    """The hub's own producers, as the canvas seed makes them."""
    from holdspeak.db.decisions import backfill_decisions
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.decision_record_service import DecisionRecordService
    from holdspeak.services.primitive_service import PrimitiveService

    owner = Principal(PrincipalKind.OWNER, "karol")
    now = datetime.now().replace(microsecond=0)
    db.projects.create_project(project_id=PROJECT, name="Payments ledger cutover", description="Nov 5.",
                               keywords=["ledger"])
    db.projects.create_project(project_id=LONE, name="Vendor review", description="One meeting.",
                               keywords=["vendor"])
    for mid, title, pid, action in (("m-sync", MEETING, PROJECT, ACTION), ("m-lone", LONE_MEETING, LONE, None)):
        start = now - timedelta(hours=2)
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
            segments=[TranscriptSegment(text="We freeze the old ledger.", speaker="Me", start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["cutover"], summary="Freeze on Nov 5.", action_items=[{
                "id": f"{mid}-a1", "task": action, "owner": None, "due": None, "status": "pending",
                "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}] if action else []),
            intel_status="completed"))
        db.projects.associate_meeting_project(meeting_id=mid, project_id=pid, source="manual", confidence=1.0)
    db.plugins.record_artifact(artifact_id="m-sync-decisions", meeting_id="m-sync", artifact_type="decisions",
                               title="Meeting decisions",
                               structured_json={"decisions": [{"decision": DECISION, "rationale": "Agreed."}]},
                               plugin_id="a2-glass")
    db.plugins.record_artifact(artifact_id="art-reqs", meeting_id="m-sync", artifact_type="requirements",
                               title=ARTIFACT, body_markdown="### Cutover requirements\n\n- Freeze on Nov 5.\n",
                               status="accepted", plugin_id="requirements_extractor", confidence=0.9)
    with db._connection() as conn:
        backfill_decisions(conn)
    decision = db.decisions.list(meeting_id="m-sync")[0]
    DecisionRecordService(db).create_from_meeting(owner, decision.id)
    PrimitiveService(db).create_note(owner, note_id="n-risks", title=NOTE, body_markdown="- slow recon", tags=[])
    return {"decision": decision.id}


class TestDrawerGlass:
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
        # A note filed in the Project: the drawer's resources read.
        _api(page, "PUT", f"/api/projects/{PROJECT}/resources/note:n-risks", {}, token=TOKEN)
        return browser, page, errors

    def _drawer(self, page: Any, project: str = PROJECT) -> Any:
        """A generic open of the Project (the arrival path → the Project primitive)."""
        page.goto(f"{self.base}/?token={TOKEN}&open=project:{project}", wait_until="load")
        _normal_chair(page)
        drawer = page.locator(".drawer-window")
        drawer.wait_for(timeout=T)
        drawer.locator("[data-testid=drawer-facts]").wait_for(timeout=T)
        page.wait_for_function("() => document.querySelectorAll('.drawer-window [data-object-id]').length > 0",
                               timeout=T)
        _settle(page)
        return drawer

    @staticmethod
    def _member(drawer: Any, ref: str) -> Any:
        return drawer.locator(f"[data-object-id='{ref}']").first

    @pytest.mark.e2e
    def test_every_member_opens_its_own_window(self) -> None:
        """1440: each member kind's Open lands on the window its identity names."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                drawer = self._drawer(page)
                refs = drawer.locator(".desk-icon").evaluate_all("els => els.map(e => e.dataset.objectId)")
                decision_ref = f"decision:{self.ids['decision']}"
                for ref in ("meeting:m-sync", decision_ref, "action:m-sync-a1", "artifact:art-reqs", "note:n-risks"):
                    assert ref in refs, (ref, refs)
                assert not any(r.startswith("decision:record") for r in refs), refs  # never the record's id
                # The Room is not a generic destination: no Room window opened.
                assert page.locator(".desk-window-shell[aria-label='Payments ledger cutover'] .room-head").count() == 0
                cases = [
                    ("meeting:m-sync", MEETING),
                    (decision_ref, MEETING),  # a meeting's decision opens where it was made
                    ("action:m-sync-a1", ACTION),  # its Follow-through card
                    ("artifact:art-reqs", ARTIFACT),
                    ("note:n-risks", NOTE),
                ]
                arrived: dict[str, bool] = {}
                for ref, words in cases:
                    drawer.locator(".drawer-head").click(position={"x": 4, "y": 4})  # the drawer in front
                    self._member(drawer, ref).dblclick()
                    try:
                        page.wait_for_function(FRONT_JS, arg=words, timeout=T)
                        arrived[ref] = True
                    except Exception:  # noqa: BLE001 -- recorded, asserted below
                        arrived[ref] = False
                    page.screenshot(path=str(SHOTS / f"glass-open-{ref.split(':')[0]}-1440.png"))
                assert all(arrived.values()), arrived
                # The drawer's own Room verb opens the Room.
                drawer.locator(".drawer-head").click(position={"x": 4, "y": 4})
                drawer.get_by_role("button", name="Room", exact=True).click()
                page.locator(".room-head").first.wait_for(timeout=T)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_needs_you_project_button_opens_the_drawer(self, width: int) -> None:
        """A2b: a Needs you row names its Project (two Projects need him); its
        Project button is a generic open, so it lands on the drawer."""
        from playwright.sync_api import sync_playwright

        from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

        # A second Project; a pending proposal in each Project is a Room row
        # that names its Project, so every row draws its Project button.
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
        for mid, pid, text in (("m-sync", PROJECT, "Run the dry run on Nov 3"), ("m-infra", "p-infra", "Cut the budget")):
            self.db.proposals.create_proposal(meeting_id=mid, project_id=pid, kind="action", text=text,
                                              source_plugin="a2b-glass")
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                screen = page.locator(".desk-screen [data-object-id='drawer:needs']")
                screen.wait_for(timeout=T)
                screen.focus()
                page.keyboard.press("Enter")
                needs = page.locator(".desk-window-shell.chair-window[aria-label='Needs you']")
                button = needs.get_by_role("button", name="Open the Project: Payments ledger cutover").first
                button.wait_for(timeout=T)
                _settle(page)
                button.scroll_into_view_if_needed()
                page.screenshot(path=str(SHOTS / f"glass-needs-project-row-{width}.png"))
                if width < 720:
                    button.tap()
                else:
                    button.click()
                drawer = page.locator(".drawer-window")
                drawer.wait_for(timeout=T)
                drawer.locator("[data-testid=drawer-facts]").wait_for(timeout=T)
                page.wait_for_timeout(600)
                page.screenshot(path=str(SHOTS / f"glass-needs-project-drawer-{width}.png"))
                assert "Payments ledger cutover" in (drawer.first.get_attribute("aria-label") or drawer.first.inner_text())
                # The Room is not a generic destination: no Room window opened.
                assert page.locator(".room-head").count() == 0
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_drawer_comes_back_after_a_reload(self, width: int) -> None:
        """B2: the open drawer, its view and its place return after a reload."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                drawer = self._drawer(page)
                view = "Icons" if width < 720 else "List"  # the one the drawer does NOT default to
                drawer.get_by_role("group", name="Drawer view").get_by_role("button", name=view).click()
                page.wait_for_timeout(400)
                if width >= 720:
                    head = page.locator(".drawer-window .desk-window-handle").first
                    hb = head.bounding_box()
                    # Grab the head clear of its title text and gadgets.
                    page.mouse.move(hb["x"] + hb["width"] * 0.6, hb["y"] + hb["height"] / 2)
                    page.mouse.down()
                    page.mouse.move(hb["x"] + hb["width"] * 0.6 - 120, hb["y"] + hb["height"] / 2 + 60, steps=8)
                    page.mouse.up()
                    page.wait_for_timeout(500)
                before = page.locator(".drawer-window").bounding_box()
                if width >= 720:
                    assert before["x"] < 1440 - before["width"] - 10 or before["y"] > 40, before  # it moved
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".drawer-window [data-testid=drawer-facts]").wait_for(timeout=T)
                page.wait_for_timeout(1200)
                after = page.locator(".drawer-window").bounding_box()
                listed = page.locator(".drawer-window .object-list").count() > 0
                page.screenshot(path=str(SHOTS / f"glass-reload-{width}.png"))
                assert listed is (view == "List"), (view, listed)
                assert after and before and abs(after["x"] - before["x"]) <= 2 and abs(after["y"] - before["y"]) <= 2, (before, after)
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_park_leaves_its_receipt_on_the_drawer(self, width: int) -> None:
        """Park (one press) from Get Info: the drawer keeps `PARKED · <name>`
        with Restore, also when it is left empty; Restore brings it back."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                drawer = self._drawer(page, LONE)
                drawer.get_by_role("group", name="Drawer view").get_by_role("button", name="List").click()
                row = drawer.locator(".object-list-open[aria-label^='Vendor call,']")
                row.click()
                drawer.get_by_role("button", name="Get Info", exact=True).click()
                info = page.locator(".drawer-info-window")
                info.wait_for(timeout=T)
                info.get_by_role("button", name="Park", exact=True).click()
                receipt = page.locator(".drawer-window [data-testid=drawer-park-receipt]")
                receipt.wait_for(timeout=T)
                page.wait_for_function(
                    "() => !document.querySelector(\".drawer-window [data-object-id='meeting:m-lone']\")", timeout=T)
                assert receipt.locator("[role=status]").text_content() == f"PARKED · {LONE_MEETING}"
                assert page.locator(".drawer-window").get_by_text("Nothing filed here").count() == 1  # left empty
                with self.db._connection() as conn:
                    parked = conn.execute("SELECT parked FROM meetings WHERE id = 'm-lone'").fetchone()[0]
                    segments = conn.execute("SELECT COUNT(*) FROM segments WHERE meeting_id = 'm-lone'").fetchone()[0]
                assert int(parked) == 1 and segments == 1
                page.screenshot(path=str(SHOTS / f"glass-park-receipt-{width}.png"))
                receipt.get_by_role("button", name="Restore", exact=True).click()
                page.locator(".drawer-window [data-object-id='meeting:m-lone']").wait_for(timeout=T)
                page.wait_for_function(
                    "() => /RESTORED/.test(document.querySelector('.drawer-window [data-testid=drawer-park-receipt] [role=status]')?.textContent || '')",
                    timeout=T)
                assert not errors, errors
            finally:
                browser.close()
