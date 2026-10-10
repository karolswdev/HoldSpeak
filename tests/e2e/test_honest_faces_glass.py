"""Faces that contradicted themselves (inventory A, defects 10 and 11; UX-CANON A.10).

One fact shows once, truthfully. Each case below was a face that said two
opposite things on the walked product (2026-10-03):

  - Meetings: "All summaries done" over "NO SUMMARY ROUTE".
  - Room: "Clear here / Nothing open" while its meeting had an action with
    no owner.
  - Settings: "SUMMARY SET ON" and "Voice LIVE" with no engine.
  - Trust: "Enabled destinations None" with a saved destination.
  - Desk memory: "NO SOURCE" beside "SOURCE MTG ... Open source".
  - Intelligence: "3 NOWS", a raw decision id that cut the decision's words.

A real hub on a cold HOME (no engine), seeded through the real producers.
Every face is read at 1440 and at 393.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="glass needs Playwright")

TOKEN = "glass-test"
SHOTS = evidence_dir("pm/evidence/honest-faces")
SHOTS.mkdir(parents=True, exist_ok=True)
WIDTHS = ((1440, 900), (393, 852))


def _seed() -> None:
    """The inventory's seed, cut to what these faces read (real producers)."""
    from holdspeak.db import get_database
    from holdspeak.db.decisions import backfill_decisions
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.decision_record_service import DecisionRecordService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "karol")
    db.projects.create_project(
        project_id="p-ledger", name="Payments ledger cutover",
        description="Move settlement to the new ledger by Nov 5.",
        keywords=["payments", "ledger", "cutover"],
    )
    now = datetime.now()
    for mid, title, hours_ago, action, decisions in (
        ("m-standup", "Ledger cutover sync", 2, "Write the rollback runbook",
         ["Freeze the old ledger on Nov 5"]),
        ("m-arch", "Architecture review: tracing", 26, "Pilot OTel in billing", []),
    ):
        start = (now - timedelta(hours=hours_ago)).replace(microsecond=0)
        summary = "Dual-write is stable. The team agreed to freeze the old ledger on Nov 5."
        db.meetings.save_meeting(MeetingState(
            id=mid, started_at=start, ended_at=start + timedelta(minutes=30), title=title,
            segments=[TranscriptSegment(text="Dual-write is stable.", speaker="Me",
                                        start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["cutover"], summary=summary, action_items=[{
                "id": f"{mid}-a1", "task": action, "owner": None, "due": None,
                "status": "pending", "review_state": "accepted",
                "source_timestamp": None, "created_at": start.isoformat()}]),
            intel_status="completed",
        ))
        db.projects.associate_meeting_project(
            meeting_id=mid, project_id="p-ledger", source="manual", confidence=1.0)
        if decisions:
            db.plugins.record_artifact(
                artifact_id=f"{mid}-decisions", meeting_id=mid, artifact_type="decisions",
                title="Meeting decisions", plugin_id="honest-faces",
                structured_json={"decisions": [
                    {"decision": d, "rationale": "Agreed in the meeting."} for d in decisions]},
            )
    with db._connection() as conn:
        backfill_decisions(conn)
    lifecycle = db.decisions.list(meeting_id="m-standup")[0]
    DecisionRecordService(db).create_from_meeting(owner, lifecycle.id)


@pytest.fixture(scope="module")
def _build():
    _ensure_build()


@pytest.fixture()
def desk(tmp_path, monkeypatch, _build):
    server, base_url = _boot(tmp_path, monkeypatch, token=TOKEN)
    _seed()
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch()

        def open_page(width: int, height: int, surface: str | None = None,
                      scope: str | None = None) -> Any:
            page = browser.new_context(viewport={"width": width, "height": height}).new_page()
            page.goto(f"{base_url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            if surface:
                page.evaluate(
                    """([key, scope]) => sessionStorage.setItem(
                         "hs.desk.staged-surface-open",
                         JSON.stringify(scope ? {key, scope} : {key}))""",
                    [surface, scope],
                )
                page.reload(wait_until="load")
                _normal_chair(page)
            return page

        yield open_page, tmp_path
        browser.close()
        pw.stop()
    finally:
        server.stop()


def _shot(page: Any, name: str, width: int) -> None:
    _settle(page)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))


def _text(page: Any) -> str:
    return page.locator("body").inner_text()


def test_meetings_gives_no_all_clear_without_an_engine(desk):
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height, "review-meetings")
        page.get_by_text("NO SUMMARY ROUTE").first.wait_for(timeout=15000)
        _shot(page, "meetings", width)
        window = page.locator(".desk-surface-window").first
        text = window.inner_text()
        assert "No engine for summaries" in text
        assert "All summaries done" not in text


def test_room_shows_its_meeting_action_as_open(desk):
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height, "open-project-memory", "project:p-ledger")
        headline = page.get_by_test_id("room-headline")
        headline.wait_for(timeout=15000)
        assert headline.text_content() == "2 open here"
        rows = page.get_by_test_id("needs-you-row")
        assert rows.count() == 2
        listed = " | ".join(rows.all_text_contents())
        assert "Write the rollback runbook" in listed and "Pilot OTel in billing" in listed
        assert listed.count("OWNER · UNKNOWN") == 2
        assert page.get_by_test_id("needs-you-empty").count() == 0
        _shot(page, "room", width)
        # Each row has a way to act: Open lands on the action's card in
        # Follow-through, where an owner is named.
        opens = page.get_by_test_id("needs-you-open-action")
        assert opens.count() == 2
        target = rows.first.locator(".surface-primary").first.inner_text().strip()
        opens.first.evaluate("el => el.click()")
        intel = page.locator(".desk-window[aria-label='Intelligence']")
        intel.wait_for(timeout=15000)
        intel.locator(".intelligence-segment.is-active", has_text=re.compile("follow-through", re.I)).wait_for(timeout=15000)
        intel.get_by_text(target).first.wait_for(timeout=15000)
        _shot(page, "room-open-action", width)


def test_room_actions_are_not_counted_twice_on_the_desk(desk):
    """The Desk reads a meeting's action through the follow-through board; the
    Room's new row must not add a second one to the Desk aggregate.

    Since #788 the hub's answer holds the Door cards too (`items`), so an
    action is in the answer one time, as its Door card. The Room rows
    (`roomItems`) still carry no action row.
    """
    open_page, _ = desk
    page = open_page(1440, 900)
    _api(page, "POST", "/api/settings/heartbeat/run-now")
    aggregate = _api(page, "GET", "/api/desk/needs-you")
    assert not [row for row in aggregate["roomItems"] if row.get("kind") == "action_item"]
    actions = [row for row in aggregate["items"] if row.get("kind") == "action_item"]
    assert actions, aggregate["items"]
    assert all(row.get("_isDoor") for row in actions), actions
    refs = [row["ref"] for row in actions]
    assert len(refs) == len(set(refs)), refs
    titles = [row["title"] for row in aggregate["items"]]
    assert len(titles) == len(set(titles)), titles


def test_settings_names_the_missing_engine(desk):
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height, "configure-settings")
        page.get_by_text("SUMMARY · NO ENGINE").first.wait_for(timeout=15000)
        text = _text(page)
        assert "SUMMARY SET ON" not in text
        voice = page.locator(".surface-ledger-row", has_text="Voice").first
        voice_text = voice.inner_text()
        assert "NO ENGINE" in voice_text
        assert "LIVE" not in voice_text
        _shot(page, "settings", width)


def test_trust_counts_the_saved_destination(desk):
    open_page, tmp_path = desk
    folder = tmp_path / "home" / "Documents" / "HoldSpeak" / "Team updates"
    folder.mkdir(parents=True, exist_ok=True)
    for index, (width, height) in enumerate(WIDTHS):
        page = open_page(width, height)
        if index == 0:
            _api(page, "POST", "/api/channels/destinations",
                 {"name": "Team updates", "channel": "file", "folder": str(folder)})
        page.evaluate("() => document.querySelector('.egress-badge-button')?.click()")
        window = page.locator(".desk-trust-window")
        window.wait_for(timeout=15000)
        page.wait_for_timeout(1500)
        _shot(page, "trust", width)
        window.get_by_text("Team updates").first.wait_for(timeout=15000)
        count_row = window.locator(".surface-setting-row", has_text="Enabled destinations").first
        # Two saved destinations: the built-in HoldSpeak folder (owner ruling 2026-10-05) and Team updates.
        window.get_by_text("HoldSpeak folder").first.wait_for(timeout=15000)
        assert re.search(r"Enabled destinations\s*2$", count_row.inner_text().strip())
        text = window.inner_text()
        # A folder on this device is in use and sends nothing out.
        assert "All data stays on this device" in text
        assert "THIS DEVICE" in text
        assert "/private/" not in text and str(tmp_path) not in text
        _shot(page, "trust", width)


def test_desk_memory_does_not_say_no_source_beside_a_source(desk):
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height, "open-project-memory")
        page.get_by_text("Freeze the old ledger on Nov 5").first.wait_for(timeout=15000)
        page.get_by_text("Open source").first.wait_for(timeout=15000)
        text = _text(page)
        assert "LINKED" in text
        assert "NO SOURCE" not in text
        _shot(page, "desk-memory", width)


def test_intelligence_lane_names_and_decision_rows(desk):
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height)
        # A DOM click: at 393 the Dock pages its seats.
        page.locator(".desk-dock-launch[aria-label^='Intelligence']").first.evaluate("el => el.click()")
        intel = page.locator(".desk-window[aria-label='Intelligence']")
        intel.wait_for(timeout=15000)
        intel.locator(".intelligence-segment", has_text=re.compile("follow-through", re.I)).first.click()
        page.get_by_text("2 TO REVIEW").first.wait_for(timeout=15000)
        assert not re.search(r"\b\d+ (NOWS|TO REVIEWS|UNASSIGNEDS|WAITINGS|OVERDUES)\b", _text(page))
        _shot(page, "intelligence-follow-through", width)
        intel.locator(".intelligence-segment", has_text=re.compile("decisions", re.I)).first.click()
        row = page.locator(".receipts-results .surface-ledger-row").first
        row.wait_for(timeout=15000)
        row_text = row.inner_text()
        assert "Freeze the old ledger on Nov 5" in row_text
        assert not re.search(r"D-[0-9a-f]{6,}", row_text)
        # PHILO-17: a row names its meeting (and its date), never
        # "UNASSIGNED GOVERNING"; the filter is a plain word.
        assert "Ledger cutover sync" in row_text, row_text
        assert "UNASSIGNED" not in row_text and "GOVERNING" not in row_text, row_text
        view = intel.locator(".receipts-view").inner_text()
        assert "WHY" not in view, view
        intel.get_by_role("button", name="Current only").wait_for(timeout=5000)
        _shot(page, "intelligence-decisions", width)


def test_an_open_meeting_shows_its_decisions_above_commitments(desk):
    """PHILO-17 ("what did we decide yesterday?"): the meeting's recorded
    decision is on its record, above Commitments."""
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height, "review-meetings")
        row = page.locator("[data-testid='meeting-row-m-standup'] .meetings-stream-row-body").first
        row.wait_for(timeout=15000)
        row.evaluate("el => el.click()")
        decisions = page.locator("[data-testid='meeting-decisions']").first
        decisions.wait_for(timeout=15000)
        assert "Freeze the old ledger on Nov 5" in decisions.inner_text()
        commitments = page.locator("[data-testid='meeting-commitments']").first
        commitments.wait_for(timeout=15000)
        assert decisions.bounding_box()["y"] < commitments.bounding_box()["y"]
        decisions.scroll_into_view_if_needed()
        _shot(page, "meeting-decisions", width)


def test_a_decision_search_hit_opens_the_decision_and_adds_no_floor_icon(desk):
    """PHILO-17: ⌘K → a DECISION hit opens the decision itself (in
    Intelligence → Decisions), not the meeting, and drops no "New decision"
    icon on the Floor."""
    open_page, _ = desk
    for width, height in WIDTHS:
        page = open_page(width, height)
        page.wait_for_timeout(1500)
        _settle(page)
        icons_before = page.locator(".desk-icon").count()
        page.locator("[aria-controls=desk-tool-shelf]").first.evaluate("el => el.click()")
        page.locator("[aria-controls=desk-palette-listbox]").fill("Freeze the old ledger")
        hit = page.locator("[id^='desk-palette-option-memory:decision:']").first
        hit.wait_for(timeout=15000)
        hit.evaluate("el => el.click()")
        intel = page.locator(".desk-window[aria-label='Intelligence']")
        intel.wait_for(timeout=15000)
        head = intel.locator(".receipt-detail h3").first
        head.wait_for(timeout=15000)
        assert (head.text_content() or "").strip() == "Freeze the old ledger on Nov 5"
        page.wait_for_timeout(1500)
        _settle(page)
        assert page.locator(".desk-icon").count() == icons_before
        assert page.locator(".desk-icon-name", has_text="New decision").count() == 0
        _shot(page, "decision-search-hit", width)


def test_trust_scope_names_a_saved_external_destination(desk):
    """A synced folder sends data out: the lede and the scope say the same."""
    open_page, tmp_path = desk
    folder = tmp_path / "home" / "Dropbox" / "Team updates"
    folder.mkdir(parents=True, exist_ok=True)
    for index, (width, height) in enumerate(WIDTHS):
        page = open_page(width, height)
        if index == 0:
            saved = _api(page, "POST", "/api/channels/destinations",
                         {"name": "Synced updates", "channel": "file",
                          "folder": str(folder), "synced": True})
            assert saved["destination"]["badge"] == "cloud", saved
        page.evaluate("() => document.querySelector('.egress-badge-button')?.click()")
        window = page.locator(".desk-trust-window")
        window.get_by_text("Synced updates").first.wait_for(timeout=15000)
        text = window.inner_text()
        assert "External destinations configured" in text
        assert "All data stays on this device" not in text
        scope = window.locator(".surface-setting-row", has_text="Current scope").first.inner_text()
        assert "this device + external" in scope, scope
        assert "SENDS OUT" in text
        _shot(page, "trust-external", width)
