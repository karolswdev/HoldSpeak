"""PHILO-15 lane 19 -- the Brief carries the day, as rendered (1440 and 393).

Rehearsal 2 (docs/internal/philo/phase-15/rehearsal-2/BOUNCES-C.md):
  B58  the morning Brief missed the decision, the agent, its PR, the merge and
       the sent update.
  B59  the open Brief window kept yesterday's Brief until a page reload.
  B73  rows carried JSON details and UTC ISO stamps.

The rig opens the Brief window on YESTERDAY's Brief, makes the day through
the real producers (a meeting decision confirmed, an action done, an update
published and sent to the HoldSpeak folder), then runs the REAL cadence tick
(the scheduled path: regenerate=False, key-free) while the window is open.
Today's Brief replaces yesterday's on the glass with no reload; its first three
rows are the merge, the sent update and the PR (the order ruling), and the
key-free Brief says NOT READ · People (the People store exists, its key is
not asked for with nobody at the desk).
The agent launch is the one record written as the follow-through leaves it
(the launch, its PR and the merge are fenced through the real producers in
tests/unit/test_philo15_19_brief_carries_the_day.py).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the brief glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

TOKEN = "philo15-19-brief-day"
SHOTS = evidence_dir("docs/internal/philo/phase-15/19-shots")
SIZES = {1440: 900, 393: 852}
_RAW = re.compile(r"[{}]|\d{4}-\d{2}-\d{2}T|sha256|launch-|prop-")


def _iso(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).replace(microsecond=0).isoformat()


def _the_day(page: Any, ledger_path: Path) -> None:
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

    pid = _api(page, "POST", "/api/projects", {"name": "Rehearsal repo hygiene"}, token=TOKEN)["project"]["id"]
    update = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {}, token=TOKEN)["update"]["id"]
    _api(page, "POST", f"/api/updates/{update}/publish", {}, token=TOKEN)
    ref = f"project_update:{update}"
    digest = _api(page, "POST", "/api/channels/preview",
                  {"document_ref": ref, "destination_id": "holdspeak-folder"}, token=TOKEN)["payload_digest"]
    _api(page, "POST", "/api/channels/send", {"document_ref": ref, "destination_id": "holdspeak-folder",
                                              "preview_digest": digest, "command_id": "glass-19"}, token=TOKEN)

    # The launch as the K4 follow-through leaves it after the merge.
    url = "https://github.com/karolswdev/holdspeak-dayone-rehearsal/pull/4"
    LaunchLedger(ledger_path).record({
        "launch_id": "launch-glass-19", "state": "launched", "profile_id": "codex",
        "origin_ref": {"kind": "action", "id": "m-hygiene-a1"}, "launched_at": _iso(30),
        "follow_through": {
            "pr": {"number": 4, "title": "Add CODEOWNERS naming the owner", "url": url, "state": "merged"},
            "pr_opened_at": _iso(18), "pr_state": "pr_merged", "close": "closed", "done": True,
            "evidence": {"pr_url": url, "pr_number": "4", "merged_at": _iso(10)},
        },
    })


def _yesterdays_brief() -> None:
    """Yesterday's Brief is the one on the desk this morning."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.timestamps import local_wall

    MondayBriefService(get_database()).generate(
        Principal(PrincipalKind.OWNER, "karol"), now=local_wall() - timedelta(days=1))


def _cadence_tick() -> None:
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


class TestTheBriefCarriesTheDay:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        self.ledger = tmp_path / "agent_launches.json"
        monkeypatch.setattr("holdspeak.delivery.factory_launch.DEFAULT_LAUNCHES_PATH", self.ledger)
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_open_brief_shows_the_day_when_the_scheduled_write_lands(self, width: int) -> None:
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
                from holdspeak.people import production_people_store

                production_people_store().initialize()
                _yesterdays_brief()
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()
                # Yesterday's Brief is on the desk at load; the window opens on it.
                _menu_pick(page, width, "Brief")
                brief = _shell(page, "Brief")
                brief.get_by_test_id("arrival-brief").first.wait_for()
                yesterday = _api(page, "GET", "/api/brief/latest", token=TOKEN)
                title = brief.locator(".desk-window-title").first
                page.wait_for_function(
                    "([el, want]) => el.innerText.trim() === want",
                    arg=[title.element_handle(), yesterday["title"]], timeout=15_000)

                _the_day(page, self.ledger)
                _cadence_tick()

                # B59: no reload. The window re-reads on the hub's frame.
                latest = _api(page, "GET", "/api/brief/latest", token=TOKEN)
                assert latest["id"] != yesterday["id"], "the tick made today's Brief"
                page.wait_for_function(
                    "([el, want]) => el.innerText.trim() === want",
                    arg=[title.element_handle(), latest["title"]], timeout=15_000)
                brief.locator("[data-testid=arrival-brief-row]", has_text="PR merged").wait_for()
                # ORDER RULING: the three rows on the face.
                shown = [r.split("\n")[0].strip() for r in
                         brief.get_by_test_id("arrival-brief-row").all_inner_texts()]
                assert [t.split(": ", 1)[0] for t in shown] == ["PR merged", "Update sent", "PR opened"], shown
                rows = {i["text"]: i for items in latest["sections"].values() for i in items}
                for wanted in (
                    "Decision confirmed: Squash merges only on the rehearsal repository",
                    "Action done: Add a CODEOWNERS file",
                    "Agent launched: Add a CODEOWNERS file",
                    "PR opened: Add CODEOWNERS naming the owner (PR #4)",
                    "PR merged: Add CODEOWNERS naming the owner (PR #4)",
                    "Update sent: Rehearsal repo hygiene",
                    "Meeting recorded: Repo hygiene sync",
                    "Project added: Rehearsal repo hygiene",
                ):
                    assert wanted in rows, (wanted, sorted(rows))
                    assert re.search(r"\d{2}:\d{2}$", rows[wanted]["detail"] or ""), rows[wanted]
                # B73: no JSON, no id, no UTC stamp in any row.
                for text, item in rows.items():
                    assert not _RAW.search(text) and not _RAW.search(item.get("detail") or ""), item
                # One honest NOT READ row: the key-free Brief did not read People.
                assert any(t.startswith("NOT READ · People") for t in rows), sorted(rows)
                row = brief.locator("[data-testid=arrival-brief-row]", has_text="Update sent")
                detail = row.get_by_test_id("arrival-brief-row-detail")
                assert re.fullmatch(r"HoldSpeak folder · \d{2}:\d{2}", detail.inner_text().strip()), \
                    detail.inner_text()
                assert not _RAW.search(brief.inner_text()), brief.inner_text()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"brief-window-after-write-{width}.png"))

                # The whole day, in the Brief's full view (its "N more").
                _press(page, brief.get_by_test_id("arrival-brief-more"), width)
                full = page.get_by_text("PR merged", exact=False).first
                full.wait_for()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"brief-full-{width}.png"))
                intel = page.locator(".desk-window[aria-label='Intelligence']")
                unread = intel.get_by_text("NOT READ · People", exact=False).first
                unread.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"brief-full-not-read-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
