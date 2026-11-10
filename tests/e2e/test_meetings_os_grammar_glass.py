"""Records selection, menus, bounded wells and shots over an isolated real hub."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows_http

TOKEN = "meetings-os-grammar"


@pytest.mark.e2e
@pytest.mark.timeout(240)
def test_records_selection_and_shots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import expect, sync_playwright
    from holdspeak.db import get_database
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    shots = Path(__file__).resolve().parents[2] / ".tmp/evidence-shots/os-grammar"
    shots.mkdir(parents=True, exist_ok=True)
    try:
        db = get_database()
        for i, (mid, title, status, summary) in enumerate((
            ("platform", "Platform review", "completed", "The team agreed to move the release to Friday."),
            ("dana", "1:1 with Dana", "completed", "Dana wants the on-call rota changed before December. You agreed to raise it with the leads on Friday."),
            ("guild", "Architecture guild", "completed", "The guild reviewed the migration plan."),
            ("vendor", "Vendor call, Woodward", "error", ""),
            ("sprint", "Sprint planning", "disabled", ""),
            ("incident", "Incident review", "queued", ""),
            ("hiring", "Hiring sync", "completed", "The hiring panel will meet on Monday."),
        )):
            start = datetime.now().astimezone() - timedelta(hours=i + 1)
            db.meetings.save_meeting(MeetingState(id=mid, title=title, started_at=start, ended_at=start + timedelta(minutes=27 + i),
                segments=[TranscriptSegment(text="We move the release to Friday.", speaker="Me", start_time=1.0, end_time=4.0)],
                intel=IntelSnapshot(timestamp=1.0, topics=[], summary=summary, action_items=[]) if summary else None,
                intel_status=status))
        db.plugins.record_artifact(artifact_id="dana-decision", meeting_id="dana", artifact_type="decisions", title="Decisions",
            structured_json={"decisions": [{"decision": "Raise the rota change with the leads on Friday."}]}, plugin_id="decision_capture")
        for task in ("Write the migration plan", "Review the rollback plan", "Confirm the release date"):
            db.proposals.create_proposal(meeting_id="guild", project_id=None, kind="action", text=task, source_plugin="summary")
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.evaluate("sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key: 'review-meetings'}))")
                page.reload(wait_until="load")
                _normal_chair(page)
                window = page.locator("#surface-meetings")
                window.get_by_test_id("meeting-row-platform").wait_for()
                if width == 1440:
                    _api(page, "POST", "/api/desk/windows/surface-meetings/set_geometry", {"rect": {"x": "-1/2 + 100", "y": "-1/2 + 80", "w": "900px", "h": "600px"}}, token=TOKEN)
                _settle(page)

                def shot(state: str) -> None:
                    _settle(page)
                    assert window.evaluate("""el => {
                      const body = el.querySelector('.desk-surface-body');
                      return body.scrollHeight <= body.clientHeight + 1 && body.scrollWidth <= body.clientWidth + 1;
                    }"""), state
                    page.screenshot(path=str(shots / f"meetings-{state}-{'900x600' if width == 1440 else '393'}-after.png"))

                assert window.locator('[role="row"] button').count() == 0
                assert window.locator('.surface-spine, .mt-rail, .mt-plate').count() == 0
                rows = window.locator('[role="row"][data-object-id]')
                assert all(abs(row.bounding_box()["height"] - (26 if width == 1440 else 44)) < 1 for row in rows.all())
                expect(window.get_by_test_id("meeting-row-platform").locator('[data-col="state"]')).to_have_text("")
                shot("records")
                for mid, state in (("dana", "summary"), ("guild", "confirm"), ("vendor", "failed"), ("sprint", "no-summary"), ("incident", "queued")):
                    row = window.get_by_test_id(f"meeting-row-{mid}")
                    row.click()
                    expect(row).to_have_attribute("aria-selected", "true")
                    expect(window.get_by_test_id("meeting-list-preview")).to_contain_text(row.locator('[data-col="name"]').inner_text())
                    expect(window.get_by_test_id("meeting-list-preview")).not_to_contain_text("Reading summary…")
                    assert window.get_by_test_id("meeting-mast").count() == 0
                    if mid == "dana":
                        expect(window.get_by_test_id("meeting-list-preview")).to_contain_text("Raise the rota change with the leads on Friday.")
                    shot(state)
                # Keyboard moves the selection, and Home/End keep the list in its well.
                window.get_by_test_id("meeting-row-incident").focus()
                page.keyboard.press("Home")
                expect(window.get_by_test_id("meeting-row-platform")).to_have_attribute("aria-selected", "true")
                page.keyboard.press("ArrowDown")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_attribute("aria-selected", "true")
                row = window.get_by_test_id("meeting-row-dana")
                row.click(button="right")
                menu = page.get_by_role("menu", name="Meetings actions", exact=True)
                expect(menu.get_by_role("menuitem", name="Open", exact=False)).to_be_visible()
                expect(menu.get_by_role("menuitem", name="Delete", exact=False)).to_be_visible()
                shot("context-menu")
                page.keyboard.press("Escape")
                # The app menu uses the same selection declaration.
                switcher = page.get_by_test_id("desk-screen-switcher")
                if switcher.is_visible():
                    switcher.click()
                    page.get_by_role("menuitem", name="Meetings", exact=True).click()
                    app_menu = page.get_by_role("menu").last
                else:
                    page.get_by_test_id("desk-screen-title").get_by_role("button", name="Meetings", exact=True).click()
                    app_menu = page.get_by_role("menu", name="Meetings menu", exact=True)
                expect(app_menu.get_by_role("menuitem", name="Delete", exact=False)).to_be_visible()
                shot("app-menu")
                page.keyboard.press("Escape")
                # Backspace is reversible; the list stays in the window.
                row.focus()
                page.keyboard.press("Backspace")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_count(0)
                expect(window.get_by_test_id("meetings-park-receipt")).to_be_visible()
                if width == 393:
                    restore = window.get_by_test_id("meetings-park-receipt").get_by_role("button", name="Restore", exact=True)
                    assert restore.evaluate("""el => {
                      const r = el.getBoundingClientRect(); const x = (r.left+r.right)/2; const y = (r.top+r.bottom)/2;
                      return [-20,0,20].every(dx => [-20,0,20].every(dy => document.elementFromPoint(x+dx,y+dy)?.closest('button') === el));
                    }"""), "Restore must own its 44px hit area in the status bar"
                shot("deleted")
                window.get_by_test_id("meetings-park-receipt").get_by_role("button", name="Restore", exact=True).click()
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                # Deleted records use the same selection list and restore action.
                window.get_by_test_id("meeting-row-dana").focus()
                page.keyboard.press("Delete")
                expect(window.get_by_test_id("meeting-row-dana")).to_have_count(0)
                if width == 1440:
                    window.get_by_role("button", name="Deleted…", exact=True).click()
                else:
                    window.get_by_role("button", name="Actions ▾", exact=True).click()
                    page.get_by_role("menuitem", name="Deleted…", exact=True).click()
                window.get_by_test_id("meeting-row-dana").click()
                shot("deleted-list")
                window.get_by_role("button", name="Restore", exact=True).click()
                expect(window.get_by_test_id("meeting-row-platform")).to_be_visible()
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                find = window.get_by_role("textbox", name="Find a meeting", exact=True)
                find.fill("zzzzzz")
                expect(rows).to_have_count(0)
                shot("find-empty")
                find.fill("no-match-for-this-meeting")
                expect(window.get_by_role("alert")).to_have_text("Meetings not read")
                shot("find-error")
                find.fill("")
                expect(window.get_by_test_id("meeting-row-dana")).to_be_visible()
                window.get_by_test_id("meeting-row-dana").focus()
                page.keyboard.press("Enter")
                expect(window.get_by_test_id("meeting-mast")).to_be_visible()
                assert errors == [], errors
                page.close()
            browser.close()
    finally:
        server.stop()
