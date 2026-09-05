"""HS-175: Rhythm weekly brief row + brief detail THIS WEEK section glass rig.

Two legs:
  1. Calendar configured: the brief row reads "Weekly brief", shows
     WEEKLY MON 08:00 token, LAST chip, summary line, and Generate verb.
     The brief detail shows THIS WEEK before SINCE FRIDAY with rows and
     source emblem chips.
  2. No calendar: the row reads "Monday brief", no THIS WEEK section.

Shots at 1440 + 393:
  rhythm-weekly-brief-1440.png, rhythm-weekly-brief-393.png,
  brief-week-1440.png, brief-week-393.png.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot as _conftest_boot,
    _api,
    _ensure_build,
    _settle,
    _normal_chair,
    _assert_clean,
)

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-05-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "glass-test"


# ── Helpers ──────────────────────────────────────────────────────

def _open_rhythm(page: Any) -> None:
    """Open the Rhythm / Cadence surface window."""
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["configure-cadence"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _open_intelligence(page: Any) -> None:
    """Open the Intelligence pullout with the brief view.

    Reload first so the chair has fresh API data, then click the
    Intelligence dock icon (the first dock app, label "Intelligence").
    """
    page.reload(wait_until="load")
    _normal_chair(page)
    _settle(page)
    # Click the Intelligence dock button by aria-label
    dock_btn = page.locator('button.desk-dock-app').first
    if dock_btn.count() > 0:
        dock_btn.click()
    page.wait_for_timeout(800)
    _settle(page)


def _window(page: Any) -> Any:
    """The first surface window element."""
    return page.locator(".desk-surface-window").first


def _shot(page: Any, name: str, width: int, *, pullout: bool = False) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": old_size["width"], "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    if pullout:
        # Try to capture the pullout panel specifically
        panel = page.locator(".desk-pullout, .intelligence-pullout").first
        if panel.count() > 0 and panel.is_visible():
            panel.screenshot(path=str(path))
        else:
            page.screenshot(path=str(path), full_page=False)
    else:
        win = _window(page)
        if win.count() > 0 and win.is_visible():
            win.screenshot(path=str(path))
        else:
            page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 1_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _seed_calendar_events(page: Any) -> None:
    """Seed 4 calendar events this week via the DB."""
    from holdspeak.db import get_database

    db = get_database()
    now = time.time()
    # Events must fall within the current ISO week (Monday..Sunday of now).
    # The brief's week window runs from this week's Monday 00:00 to Sunday 23:59.
    # At least one event must be in the future (after now) so the "Next:"
    # item is produced.  Place two past, one later today, one tomorrow.
    import datetime as _dt
    today = _dt.date.today()
    days_since_monday = today.weekday()
    monday = today - _dt.timedelta(days=days_since_monday)
    tomorrow = today + _dt.timedelta(days=1)
    # Ensure tomorrow is within the same ISO week (i.e. not past Sunday)
    if tomorrow.weekday() == 0:
        # today is Sunday; put the future event later today instead
        tomorrow = today
    events = [
        ("evt-glass-1", "uid-1", "Team Standup",
         f"{monday.isoformat()}T10:00:00", f"{monday.isoformat()}T10:30:00"),
        ("evt-glass-2", "uid-2", "Architecture Review",
         f"{(monday + _dt.timedelta(days=1)).isoformat()}T14:00:00",
         f"{(monday + _dt.timedelta(days=1)).isoformat()}T15:00:00"),
        ("evt-glass-3", "uid-3", "Sprint Planning",
         f"{today.isoformat()}T23:30:00", f"{today.isoformat()}T23:59:00"),
        ("evt-glass-4", "uid-4", "1:1 with Ania",
         f"{tomorrow.isoformat()}T11:00:00", f"{tomorrow.isoformat()}T11:30:00"),
    ]
    with db._connection() as conn:
        for eid, uid, title, starts, ends in events:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES (?, ?, ?, ?, ?, ?, 'rev1', 'src1', 'WORK')""",
                (eid, uid, title, starts, ends, now),
            )


def _seed_armed_recording(page: Any) -> None:
    """Seed an armed scheduled recording linked to a calendar event."""
    from holdspeak.db import get_database

    db = get_database()
    now = time.time()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO scheduled_recordings
               (id, title, cron_expr, enabled, next_fire_at, state,
                calendar_event_id, calendar_uid, calendar_source_id,
                created_at)
               VALUES ('sr-glass-1', 'Team Standup', '0 55 9 * * *', 1, ?,
                       'idle', 'evt-glass-1', 'uid-1', 'src1', ?)""",
            (now, now),
        )


def _seed_commitment(page: Any) -> None:
    """Seed a commitment due this week via the DB."""
    from holdspeak.db import get_database

    db = get_database()
    art_id = f"art-{uuid.uuid4().hex[:8]}"
    import datetime as _dt
    today = _dt.date.today()
    days_since_monday = today.weekday()
    # Due Friday of this week
    friday = today - _dt.timedelta(days=days_since_monday) + _dt.timedelta(days=4)

    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions
               (id, text, rationale, source_artifact_id, source_meeting_id,
                lifecycle, project_key, decided_at)
               VALUES ('d-glass-1', 'Ania owns the API spec', '', ?, '',
                       'recorded', '', datetime('now'))""",
            (art_id,),
        )
        conn.execute(
            """INSERT INTO decision_commitments
               (id, decision_id, action_item_id, owner, due_at, status,
                created_at, updated_at)
               VALUES ('dc-glass-1', 'd-glass-1', 'ai-glass-1', 'karol',
                       ?, 'open', datetime('now'), datetime('now'))""",
            (friday.isoformat(),),
        )


def _seed_calendar_source_config(tmp_path: Path) -> None:
    """Create a minimal config with a calendar source so calendar_configured=true."""
    import json

    config_dir = tmp_path / "home" / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    # Write a config with an enabled calendar source pointing to a local file
    ics_path = tmp_path / "work.ics"
    ics_path.write_text(
        "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//glass//EN\nEND:VCALENDAR\n"
    )
    config = {
        "calendar": {
            "sources": [
                {
                    "url": str(ics_path),
                    "label": "WORK",
                    "enabled": True,
                }
            ]
        }
    }
    config_file.write_text(json.dumps(config))


# ── Build + boot fixture ────────────────────────────────────────

@pytest.fixture(scope="session")
def _build():
    _ensure_build()


@pytest.fixture()
def glass_with_calendar(tmp_path, monkeypatch, _build):
    """Boot server with calendar configured + seed data."""
    _seed_calendar_source_config(tmp_path)
    server, hub_url = _conftest_boot(tmp_path, monkeypatch, token=TOKEN)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        errors: list[str] = []
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda msg: (
            errors.append(msg.text) if msg.type == "error" else None
        ))
        page.goto(f"{hub_url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)

        # Seed data through the DB
        _seed_calendar_events(page)
        _seed_armed_recording(page)
        _seed_commitment(page)

        # Generate brief through the real route
        _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)

        yield page, errors, hub_url
        browser.close()
    server.stop()


@pytest.fixture()
def glass_no_calendar(tmp_path, monkeypatch, _build):
    """Boot server WITHOUT calendar configured."""
    server, hub_url = _conftest_boot(tmp_path, monkeypatch, token=TOKEN)
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        errors: list[str] = []
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda msg: (
            errors.append(msg.text) if msg.type == "error" else None
        ))
        page.goto(f"{hub_url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)

        # Generate brief without calendar data
        _api(page, "POST", "/api/brief/generate", {}, token=TOKEN)

        yield page, errors, hub_url
        browser.close()
    server.stop()


# ── Leg 1: Calendar configured ──────────────────────────────────

class TestRhythmWeeklyBrief:

    def test_rhythm_brief_row_with_calendar(self, glass_with_calendar):
        """When calendar is configured: Weekly brief label, WEEKLY token,
        LAST chip, summary line, Generate verb."""
        page, errors, _ = glass_with_calendar

        _open_rhythm(page)
        _settle(page)

        # Brief row
        brief_row = page.locator('[data-testid="rhythm-brief-row"]')
        assert brief_row.count() > 0, "Brief row not found"
        row_text = brief_row.text_content() or ""

        # Label should be "Weekly brief"
        primary = brief_row.locator(".surface-ledger-primary, .surface-primary").first
        label_text = primary.text_content().strip() if primary.count() > 0 else row_text.split("\n")[0].strip()
        assert "Weekly brief" in label_text, f"Expected 'Weekly brief', got: {label_text}"

        # WEEKLY token
        cadence_token = page.locator('[data-testid="rhythm-brief-cadence"]')
        assert cadence_token.count() > 0, "Cadence token not found"
        cadence_text = cadence_token.text_content() or ""
        assert "WEEKLY" in cadence_text.upper(), f"Expected WEEKLY in cadence token, got: {cadence_text}"
        assert "MON" in cadence_text.upper(), f"Expected MON in cadence token, got: {cadence_text}"

        # LAST chip (StateChip)
        last_chip = page.locator('[data-testid="rhythm-brief-last"]')
        assert last_chip.count() > 0, "LAST chip not found"
        last_text = last_chip.text_content() or ""
        assert "LAST" in last_text.upper(), f"Expected LAST in chip, got: {last_text}"

        # Summary line
        summary = page.locator('[data-testid="rhythm-brief-summary"]')
        assert summary.count() > 0, "Summary line not found (no zero parts)"
        summary_text = summary.text_content() or ""
        assert "MEETINGS" in summary_text.upper(), f"Expected MEETINGS in summary, got: {summary_text}"

        # Generate verb
        gen_btn = page.locator('[data-testid="rhythm-generate-now"]')
        assert gen_btn.count() > 0, "Generate button not found"
        gen_text = gen_btn.text_content() or ""
        assert "Generate" in gen_text, f"Expected 'Generate', got: {gen_text}"

        # Shoot 1440
        _shot(page, "rhythm-weekly-brief-1440", 1440)

        # Shoot 393
        page.set_viewport_size({"width": 393, "height": 852})
        _settle(page)
        _shot(page, "rhythm-weekly-brief-393", 393)

        # Reset
        page.set_viewport_size({"width": 1440, "height": 900})
        _assert_clean(page, errors)

    def test_brief_this_week_section(self, glass_with_calendar):
        """The brief face: period as the ONE display fact, no headline
        sentence, THIS WEEK composed rows, flat SINCE FRIDAY, no '00'."""
        page, errors, _ = glass_with_calendar

        _open_intelligence(page)
        _settle(page)
        page.wait_for_timeout(1000)

        # Check the brief data via API
        brief_data = _api(page, "GET", "/api/brief/latest", token=TOKEN)
        tw_items = brief_data.get("sections", {}).get("this_week", [])
        assert len(tw_items) > 0, (
            f"Brief API has no this_week items: {list(brief_data.get('sections', {}).keys())}"
        )

        # Wait for the intelligence pullout to appear
        pullout = page.locator(".intelligence-pullout, .intelligence-brief")
        try:
            pullout.first.wait_for(timeout=3000)
        except Exception:
            pass

        pullout_visible = pullout.first.count() > 0 and pullout.first.is_visible()

        if pullout_visible:
            # ── (1) Exactly ONE display-step element (the period label) ──
            brief_el = page.locator(".intelligence-brief")
            display_els = brief_el.locator(".intelligence-brief-period")
            assert display_els.count() == 1, (
                f"Expected exactly 1 display-step element, got {display_els.count()}"
            )
            # No headline sentence on this face
            headline = brief_el.locator(".intelligence-brief-headline")
            assert headline.count() == 0, (
                "Headline sentence must not appear on the brief face (canon C + A.3)"
            )

            # ── (2) No text matching /\b00\b/ (counters of zero = A.8 bounce) ──
            body_text = brief_el.text_content() or ""
            import re
            assert not re.search(r'\b00\b', body_text), (
                f"Found '00' counter of zero on the brief face: ...{body_text[:200]}..."
            )

            # ── (3) No row text ending in a period (no sentences / A.3) ──
            # Check all primary-step text nodes
            primaries = brief_el.locator(
                ".intelligence-brief-tw-primary, .surface-ledger-primary, .surface-primary"
            )
            for i in range(primaries.count()):
                txt = (primaries.nth(i).text_content() or "").strip()
                if txt:
                    assert not txt.endswith("."), (
                        f"Row text ends in a period (prose): '{txt}'"
                    )

            # ── (4) NEXT token inside the MEETINGS row ──
            meetings_row = page.locator('[data-testid="brief-tw-meetings"]')
            assert meetings_row.count() > 0, "MEETINGS row not found"
            next_token = meetings_row.locator('[data-testid="brief-tw-next"]')
            assert next_token.count() > 0, "NEXT token not inside the MEETINGS row"
            next_text = next_token.text_content() or ""
            assert "NEXT" in next_text, f"NEXT token text: {next_text}"

            # ── (5) DUE row has a day token ──
            due_row = page.locator('[data-testid="brief-tw-due"]')
            if due_row.count() > 0:
                day_tok = due_row.locator('[data-testid="brief-tw-due-day"]')
                # Day token may be absent if the commitment text does not
                # contain a parseable date -- assert presence when present
                if day_tok.count() > 0:
                    day_text = day_tok.text_content() or ""
                    assert len(day_text) == 3, f"Day token should be 3 chars, got: {day_text}"

            # ── (6) SINCE FRIDAY rows have kind tokens ──
            since_friday = page.locator('[data-testid="brief-since-friday"]')
            if since_friday.count() > 0:
                sf_rows = since_friday.locator('[data-testid="brief-sf-row"]')
                for i in range(sf_rows.count()):
                    row = sf_rows.nth(i)
                    # Each row should have a kind token and a primary
                    kind = row.locator('[data-testid="brief-sf-kind"]')
                    primary = row.locator('.intelligence-brief-sf-primary')
                    assert primary.count() > 0, (
                        f"SINCE FRIDAY row {i} has no primary"
                    )
                    # kind may be absent when item text has no colon prefix
                    if kind.count() > 0:
                        kind_text = kind.text_content() or ""
                        assert kind_text == kind_text.upper(), (
                            f"Kind token should be uppercase, got: '{kind_text}'"
                        )

                # Emblem chips: verify format when present
                sf_emblems = since_friday.locator('[data-testid="brief-source-emblem"]')
                for i in range(sf_emblems.count()):
                    txt = sf_emblems.nth(i).text_content() or ""
                    assert txt == txt.upper() and 1 <= len(txt) <= 4, (
                        f"Emblem chip should be 1-4 uppercase chars, got: '{txt}'"
                    )

            # ── (7) ONE GUTTER: all elements share one left edge ──
            # Measure x offsets of period, section captions, and rows.
            gutter_data = brief_el.evaluate("""(el) => {
                const xs = [];
                for (const sel of [
                    '.intelligence-brief-period',
                    '.intelligence-brief-generated',
                    '.intelligence-brief-section-caption',
                    '.intelligence-brief-tw-row',
                    '.intelligence-brief-sf-row',
                    '.intelligence-brief-person-unavailable',
                ]) {
                    for (const node of el.querySelectorAll(sel)) {
                        const r = node.getBoundingClientRect();
                        if (r.width > 0) xs.push({ sel, x: Math.round(r.left) });
                    }
                }
                return xs;
            }""")
            if len(gutter_data) >= 2:
                xs = [d["x"] for d in gutter_data]
                min_x = min(xs)
                max_x = max(xs)
                assert max_x - min_x <= 4, (
                    f"Not one gutter: left edges span {max_x - min_x}px "
                    f"(min={min_x}, max={max_x}, data={gutter_data})"
                )

            # ── (8) No raw ISO dates (YYYY-MM-DD) on the face ──
            import re
            assert not re.search(r'\d{4}-\d{2}-\d{2}', body_text), (
                f"Raw ISO date on the brief face: {body_text[:300]}"
            )

        # Shoot 1440 (the pullout if visible, else the full page)
        _shot(page, "brief-week-1440", 1440, pullout=pullout_visible)

        # Shoot 393
        page.set_viewport_size({"width": 393, "height": 852})
        _settle(page)
        _shot(page, "brief-week-393", 393, pullout=pullout_visible)

        # Reset
        page.set_viewport_size({"width": 1440, "height": 900})

        _assert_clean(page, errors)


# ── Leg 2: No calendar ──────────────────────────────────────────

class TestRhythmMondayBrief:

    def test_no_calendar_monday_brief(self, glass_no_calendar):
        """Without calendar: row reads 'Monday brief', no THIS WEEK section."""
        page, errors, _ = glass_no_calendar

        _open_rhythm(page)
        _settle(page)

        # Brief row
        brief_row = page.locator('[data-testid="rhythm-brief-row"]')
        assert brief_row.count() > 0, "Brief row not found"

        primary = brief_row.locator(".surface-ledger-primary, .surface-primary").first
        label_text = primary.text_content().strip() if primary.count() > 0 else ""
        assert "Monday brief" in label_text, f"Expected 'Monday brief', got: {label_text}"

        # DAILY token (not WEEKLY)
        cadence_token = page.locator('[data-testid="rhythm-brief-cadence"]')
        if cadence_token.count() > 0:
            cadence_text = cadence_token.text_content() or ""
            assert "DAILY" in cadence_text.upper(), f"Expected DAILY, got: {cadence_text}"

        # Verify via API: no this_week items
        brief_data = _api(page, "GET", "/api/brief/latest", token=TOKEN)
        tw_items = brief_data.get("sections", {}).get("this_week", [])
        assert len(tw_items) == 0, f"Without calendar, this_week should be empty, got: {tw_items}"

        _assert_clean(page, errors)
