"""The desk's clocks in the owner's zone (inventory A, defect 3; 2026-10-03).

The owner is in America/Denver. Three faces printed a time wrong by the UTC
offset:

  - Chair: a recording set for 21:32 read "NEXT · ... · 15:32" (the schedule's
    cron is wall-clock time in its zone; the service computed it in UTC, so
    the recording also FIRED six hours early).
  - Bell: an artifact made a minute ago read "6h ago" (a bare local ISO stamp
    was labelled UTC).
  - Rhythm: "LAST 03:06" at 21:06 local (the face cut HH:MM out of a UTC
    string).

Hub and browser both run in America/Denver. Every record is made through the
real producer or the real route.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="glass needs Playwright")

ZONE = "America/Denver"
TOKEN = "glass-test"
SHOTS = evidence_dir("pm/evidence/times-local-zone")
SHOTS.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="module")
def _build():
    _ensure_build()


@pytest.fixture()
def denver(tmp_path, monkeypatch, _build):
    """A real hub and a browser, both in America/Denver."""
    monkeypatch.setenv("TZ", ZONE)
    time.tzset()
    server, base_url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch()

        def open_page(width: int = 1440, height: int = 900) -> Any:
            context = browser.new_context(
                viewport={"width": width, "height": height}, timezone_id=ZONE,
            )
            page = context.new_page()
            page.goto(f"{base_url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            return page

        yield open_page
        browser.close()
        pw.stop()
    finally:
        server.stop()
        monkeypatch.undo()
        time.tzset()


def _local_now() -> datetime:
    return datetime.now(ZoneInfo(ZONE))


def _open_surface(page: Any, key: str) -> None:
    page.evaluate(
        """([key]) => sessionStorage.setItem(
             "hs.desk.staged-surface-open", JSON.stringify({key}))""",
        [key],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _near(clock: str, moment: datetime, minutes: int = 2) -> bool:
    """`clock` (HH:MM) is within `minutes` of `moment`'s local wall clock."""
    return any(
        (moment + timedelta(minutes=delta)).strftime("%H:%M") == clock
        for delta in range(-minutes, minutes + 1)
    )


def test_chair_next_shows_the_scheduled_local_time(denver):
    page = denver()
    when = (_local_now() + timedelta(hours=2)).replace(second=0, microsecond=0)
    created = _api(page, "POST", "/api/scheduled-recordings", {
        "title": "Cutover dry run",
        "cron_expr": f"{when.minute} {when.hour} {when.day} {when.month} *",
        "tz": ZONE,
        "one_shot": True,
        "duration_minutes": 30,
        "enabled": True,
    })
    # The source: the hub will fire at the wall-clock time in the schedule's zone.
    fire = datetime.fromisoformat(created["schedule"]["next_fire_at"].replace("Z", "+00:00"))
    assert fire.astimezone(ZoneInfo(ZONE)) == when

    for width, height in ((1440, 900), (393, 852)):
        face = denver(width, height)
        # PHILO-14 A1 (#939): the Chair's windows start closed; he opens Needs
        # you (Window > Chair at 1440, Go at 393). PHILO-14 A5 (#935): its
        # body is the drawer, whose quiet footer line reads
        # `NEXT · <HH:MM> · <title>` (needsFace.ts nextWord).
        open_chair_window(face, "Needs you")
        line = face.get_by_test_id("needs-next")
        line.wait_for(timeout=15000)
        text = line.text_content() or ""
        assert text == f"NEXT · {when.strftime('%H:%M')} · Cutover dry run", text
        _settle(face)
        face.screenshot(path=str(SHOTS / f"chair-next-{width}.png"))


def test_bell_reads_a_new_artifact_as_new(denver):
    from holdspeak.db import get_database
    from holdspeak.meeting_session import MeetingState

    db = get_database()
    start = datetime.now().replace(microsecond=0) - timedelta(minutes=40)
    db.meetings.save_meeting(MeetingState(
        id="m-zone", started_at=start, ended_at=start + timedelta(minutes=30),
        title="Ledger cutover sync", segments=[], intel_status="completed",
    ))
    db.plugins.record_artifact(
        artifact_id="m-zone-notes", meeting_id="m-zone", artifact_type="notes",
        title="Ledger cutover sync: notes", body_markdown="Dual-write is stable.",
        plugin_id="zone-test", status="draft",
    )

    for width, height in ((1440, 900), (393, 852)):
        page = denver(width, height)
        # PHILO-17 (needsyou): the bell opens Needs you; the shade has its own event.
        page.locator(".desk-bell").first.wait_for(timeout=15000)
        page.evaluate("window.dispatchEvent(new CustomEvent('hs-open-system-shade'))")
        row = page.locator(".desk-shade-item", has_text="Ledger cutover sync: notes").first
        row.wait_for(timeout=15000)
        text = row.locator("small").first.text_content() or ""
        assert re.search(r"· (just now|[0-5]m ago)$", text), text
        _settle(page)
        page.screenshot(path=str(SHOTS / f"bell-{width}.png"))


def test_rhythm_prints_the_local_clock(denver):
    page = denver()
    ran = _local_now()
    _api(page, "POST", "/api/settings/heartbeat/run-now")

    for width, height in ((1440, 900), (393, 852)):
        face = denver(width, height)
        _open_surface(face, "configure-cadence")
        facts = face.get_by_test_id("rhythm-sweep-facts")
        facts.wait_for(timeout=15000)
        face.wait_for_function(
            """() => /LAST \\d{2}:\\d{2}/.test(
                 document.querySelector('[data-testid="rhythm-sweep-facts"]')?.textContent || '')""",
            timeout=15000,
        )
        text = facts.text_content() or ""
        last = re.search(r"LAST (\d{2}:\d{2})", text)
        nxt = re.search(r"NEXT (\d{2}:\d{2})", text)
        assert last and _near(last.group(1), ran), text
        assert nxt and _near(nxt.group(1), ran + timedelta(minutes=15)), text
        _settle(face)
        face.screenshot(path=str(SHOTS / f"rhythm-{width}.png"))
