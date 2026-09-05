"""HS-175-02 -- arrival face glass rig for the WEEK strip and calendar event rows.

Seed calendar events via direct DB inserts (the real seam through
calendar_events + calendar_event_projects + scheduled_recordings),
configure a calendar source via the config file, open the arrival,
and assert the artboard.

Tests:
  1. test_arrival_week_strip: strip present, dots sum == total,
     today accented, MEETINGS count == rows, ARMS chip on armed row,
     Cancel button present; at 1440 + 393.
  2. test_arrival_orphan: orphan armed recording below MEETINGS,
     not counted in MEETINGS or the strip; at 1440.
  3. test_arrival_no_calendar: strip absent, NO CALENDAR shown; at 1440.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Arrival glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-02-shots"
TOKEN = "hs175-arrival"


# ── Seed helpers ───────────────────────────────────────────────


def _seed_project(conn: Any, project_id: str, name: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, revision, "
        "target_at, created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
        "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
        (project_id, name),
    )


def _seed_calendar_event(
    conn: Any,
    event_id: str,
    title: str,
    starts_at: str,
    ends_at: str,
    source_id: str = "src-work",
    source_label: str = "WORK",
    meeting_url: str | None = None,
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO calendar_events "
        "(id, uid, title, starts_at, ends_at, location, meeting_url, "
        "last_seen_at, subscription_revision, source_id, source_label) "
        "VALUES (?, ?, ?, ?, ?, NULL, ?, ?, 'rev1', ?, ?)",
        (
            event_id,
            f"uid-{event_id}",
            title,
            starts_at,
            ends_at,
            meeting_url,
            time.time(),
            source_id,
            source_label,
        ),
    )


def _seed_event_project_link(
    conn: Any,
    event_id: str,
    project_id: str,
    match_source: str = "title",
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO calendar_event_projects "
        "(calendar_event_id, project_id, match_source) "
        "VALUES (?, ?, ?)",
        (event_id, project_id, match_source),
    )


def _seed_armed_recording(
    conn: Any,
    recording_id: str,
    title: str,
    fire_at: float,
    calendar_event_id: str = "",
    born_from: str = "",
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO scheduled_recordings "
        "(id, title, cron_expr, tz, one_shot, duration_minutes, "
        "enabled, revision, created_at, next_fire_at, state, "
        "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
        "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
        "?, ?, ?, ?)",
        (
            recording_id,
            title,
            time.time(),
            fire_at,
            calendar_event_id,
            f"uid-{calendar_event_id}" if calendar_event_id else "",
            "src-work" if calendar_event_id else "",
            born_from,
        ),
    )


def _write_calendar_config(home: Path, source_url: str) -> None:
    """Write a config.json with one calendar source so calendar_configured=True."""
    config_dir = home / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "calendar": {
            "sources": [
                {
                    "id": "src-work",
                    "label": "WORK",
                    "url": source_url,
                    "enabled": True,
                }
            ]
        }
    }
    (config_dir / "config.json").write_text(json.dumps(config))


def _create_ics_file(home: Path, events: list[dict[str, str]]) -> str:
    """Create a minimal .ics file and return its path."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//hs175-test//EN",
    ]
    for ev in events:
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{ev.get('uid', uuid.uuid4().hex)}",
            f"DTSTART:{ev['starts_at'].replace('-', '').replace(':', '').replace('T', 'T')}",
            f"DTEND:{ev['ends_at'].replace('-', '').replace(':', '').replace('T', 'T')}",
            f"SUMMARY:{ev['title']}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    ics_path = home / "work.ics"
    ics_path.write_text("\n".join(lines))
    return str(ics_path)


# ── Seed scenarios ─────────────────────────────────────────────


def _seed_week_strip(home: Path) -> None:
    """Seed the main week strip scenario: 3 events (2 today, 1 later this week),
    one project link, one armed recording on the first event."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now(tz=timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Create ICS file and configure it
    ics_path = _create_ics_file(home, [])
    _write_calendar_config(home, ics_path)

    with db._connection() as conn:
        # Project for Room link
        _seed_project(conn, "proj-q4", "Q4 Platform")

        # Watch connection (required for needs-you to render projects)
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', 'karolswdev', 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
        )

        # All events must be in the FUTURE so list_upcoming finds them.
        # Anchor to tomorrow 08:00 UTC: always future, always within
        # the same Mon-Sun week (unless today is Sunday -- handled by
        # softening the today-accent assertion below).
        anchor = (today + timedelta(days=1)).replace(hour=8)

        # Event 1: Standup, armed, linked to Q4 Platform
        ev1_start = anchor
        ev1_end = anchor + timedelta(minutes=30)
        _seed_calendar_event(
            conn, "ev-standup", "Standup",
            ev1_start.isoformat(), ev1_end.isoformat(),
            meeting_url="https://teams.example.com/standup",
        )
        _seed_event_project_link(conn, "ev-standup", "proj-q4")
        # Armed recording for the standup (5 min before)
        arms_at = (ev1_start - timedelta(minutes=5)).timestamp()
        _seed_armed_recording(
            conn, "rec-standup", "Standup", arms_at,
            calendar_event_id="ev-standup",
            born_from="calendar_event",
        )

        # Event 2: Design review, no armed, no room link
        ev2_start = anchor + timedelta(hours=2)
        ev2_end = ev2_start + timedelta(hours=1)
        _seed_calendar_event(
            conn, "ev-design", "Design review",
            ev2_start.isoformat(), ev2_end.isoformat(),
        )

        # Event 3: 1:1 Ania, same day
        ev3_start = anchor + timedelta(hours=4)
        ev3_end = ev3_start + timedelta(minutes=30)
        _seed_calendar_event(
            conn, "ev-ania", "1:1 Ania",
            ev3_start.isoformat(), ev3_end.isoformat(),
        )

        conn.commit()


def _seed_orphan(home: Path) -> None:
    """Seed the orphan scenario: 2 events today + 1 orphan recording
    whose event is NOT in the upcoming list (event in the past)."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now(tz=timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    ics_path = _create_ics_file(home, [])
    _write_calendar_config(home, ics_path)

    with db._connection() as conn:
        _seed_project(conn, "proj-q4", "Q4 Platform")

        # Anchor to tomorrow 08:00 UTC (always future).
        anchor = (today + timedelta(days=1)).replace(hour=8)

        # Event 1: Standup, armed, linked
        ev1_start = anchor
        ev1_end = anchor + timedelta(minutes=30)
        _seed_calendar_event(
            conn, "ev-standup2", "Standup",
            ev1_start.isoformat(), ev1_end.isoformat(),
            meeting_url="https://teams.example.com/standup",
        )
        _seed_event_project_link(conn, "ev-standup2", "proj-q4")
        arms_at = (ev1_start - timedelta(minutes=5)).timestamp()
        _seed_armed_recording(
            conn, "rec-standup2", "Standup", arms_at,
            calendar_event_id="ev-standup2",
            born_from="calendar_event",
        )

        # Event 2: Design review
        ev2_start = anchor + timedelta(hours=2)
        ev2_end = ev2_start + timedelta(hours=1)
        _seed_calendar_event(
            conn, "ev-design2", "Design review",
            ev2_start.isoformat(), ev2_end.isoformat(),
        )

        # Orphan: armed recording for "Retro" whose event is BEFORE this
        # week's Monday (not in the upcoming projection AND not in count_per_day).
        days_since_monday = now.weekday()  # 0=Mon
        past_event_start = today - timedelta(days=days_since_monday + 1)
        _seed_calendar_event(
            conn, "ev-retro-past", "Retro",
            past_event_start.isoformat(),
            (past_event_start + timedelta(hours=1)).isoformat(),
            meeting_url="https://teams.example.com/retro",
        )
        # The orphan recording fires in the future even though its event
        # is in the past (a rescheduled scenario).
        orphan_fire_at = (now + timedelta(hours=3)).timestamp()
        _seed_armed_recording(
            conn, "rec-retro-orphan", "Retro", orphan_fire_at,
            calendar_event_id="ev-retro-past",
            born_from="calendar_event",
        )

        conn.commit()


def _seed_past_future_mix(home: Path) -> None:
    """Seed 1 past event + 2 future events today for the strip-vs-MEETINGS
    ruling test: dots == total (3), MEETINGS shows only 2 (future)."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now(tz=timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    ics_path = _create_ics_file(home, [])
    _write_calendar_config(home, ics_path)

    with db._connection() as conn:
        # All 3 events on tomorrow's UTC date so count_per_day groups
        # them on one day regardless of when the test runs.
        anchor = (today + timedelta(days=1)).replace(hour=0)

        # Past event: 01:00 tomorrow (seeded as past by lying about the
        # date; list_upcoming uses starts_at >= now, so this event at
        # anchor + 1h is "past" only if now > anchor + 1h.  Instead,
        # put it on today's date so it is genuinely past.)
        past_start = today.replace(hour=2)  # 02:00 today UTC (past)
        past_end = past_start + timedelta(minutes=30)
        _seed_calendar_event(
            conn, "ev-past-today", "Morning standup",
            past_start.isoformat(), past_end.isoformat(),
        )

        # Future events on tomorrow 08:00+ (always future)
        future_anchor = anchor.replace(hour=8)
        _seed_calendar_event(
            conn, "ev-future1", "Design review",
            future_anchor.isoformat(),
            (future_anchor + timedelta(hours=1)).isoformat(),
        )

        ev3_start = future_anchor + timedelta(hours=3)
        _seed_calendar_event(
            conn, "ev-future2", "Retro",
            ev3_start.isoformat(),
            (ev3_start + timedelta(hours=1)).isoformat(),
        )

        conn.commit()


def _seed_no_calendar(home: Path) -> None:
    """No calendar source configured; strip should be absent."""
    # Do NOT write calendar config -- calendar_configured will be False.
    pass


# ── The rig ────────────────────────────────────────────────────


class TestArrivalWeekStrip:
    """HS-175-02 -- the WEEK strip and calendar event rows."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.home = tmp_path / "home"
        self.tmp_path = tmp_path

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_arrival_week_strip(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        _seed_week_strip(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            headline = page.locator("[data-testid='arrival-display']")
            headline.wait_for(timeout=10_000)
            _settle(page)

            # ── NEXT line carries Room token ──
            next_el = page.locator("[data-testid='arrival-next']")
            if next_el.count() >= 1:
                next_text = next_el.first.text_content() or ""
                assert "Q4 PLATFORM" in next_text.upper(), (
                    f"NEXT line missing Room token at {width}: {next_text}"
                )

            # ── WEEK strip present ──
            strip = page.locator("[data-testid='arrival-week-strip']")
            assert strip.count() == 1, (
                f"WEEK strip missing at {width}"
            )

            # ── Dots sum == total text ──
            dots = page.locator("[data-testid='arrival-week-dot']")
            dot_count = dots.count()
            total_el = page.locator("[data-testid='arrival-week-total']")
            total_text = total_el.text_content() or ""
            # Extract N from "N MEETING(S) THIS WEEK"
            import re
            m = re.match(r"(\d+)\s+MEETING", total_text)
            total_n = int(m.group(1)) if m else -1
            assert dot_count == total_n, (
                f"Dot count ({dot_count}) != total text ({total_n}) at {width}: '{total_text}'"
            )
            assert total_n == 3, (
                f"Expected 3 meetings, got {total_n} at {width}"
            )

            # ── Today accented ──
            # MON-FRI always show in the strip, so today is accented when
            # it is a weekday.  SAT/SUN only appear when they carry events;
            # the anchor seeds events on tomorrow, so today's weekend day
            # may be absent.  The assertion is soft on weekends.
            today_days = page.locator("[data-today]")
            is_weekday = datetime.now(tz=timezone.utc).weekday() < 5
            if is_weekday:
                assert today_days.count() >= 1, (
                    f"No today-accented day at {width} (weekday)"
                )

            # ── MEETINGS section count == rows ──
            meetings_section = page.locator("[data-testid='arrival-meetings']")
            assert meetings_section.count() >= 1, (
                f"MEETINGS section missing at {width}"
            )
            meeting_rows = page.locator("[data-testid='arrival-meeting-row']")
            row_count = meeting_rows.count()
            assert row_count == 3, (
                f"Expected 3 meeting rows, got {row_count} at {width}"
            )

            # ── Room token on linked event ──
            body_text = meetings_section.first.text_content() or ""
            assert "Q4 PLATFORM" in body_text.upper(), (
                f"Room token missing at {width}: {body_text[:200]}"
            )

            # ── ARMS chip on armed row ──
            arms_chips = page.locator(".surface-state-chip:has-text('ARMS')")
            if arms_chips.count() == 0:
                # Fallback: check for text "ARMS" in the meetings section
                assert "ARMS" in body_text, (
                    f"ARMS chip missing at {width}: {body_text[:200]}"
                )

            # ── Cancel button on armed row ──
            cancel_btns = page.locator("[data-testid='arrival-cancel-armed']")
            assert cancel_btns.count() >= 1, (
                f"No Cancel button at {width}"
            )

            # ── No orphan row (all events are listed) ──
            orphans = page.locator("[data-testid='arrival-orphan-row']")
            assert orphans.count() == 0, (
                f"Unexpected orphan row at {width}: {orphans.count()}"
            )

            # ── No raw <button> ──
            raw_buttons = page.evaluate("""() => {
                const body = document.querySelector('.chair');
                if (!body) return [];
                const allowed = ['btn', 'desk-mic', 'surface-ledger-line',
                    'gadget-cycle', 'gadget-stepper-btn'];
                return Array.from(body.querySelectorAll('button'))
                    .filter(b => !allowed.some(c => b.classList.contains(c)))
                    .map(b => (b.textContent || '').trim().slice(0, 40));
            }""")
            assert len(raw_buttons) == 0, f"Raw buttons at {width}: {raw_buttons}"

            # ── No zero counter ──
            chair_text = page.locator(".chair").text_content() or ""
            assert "0 MEETING" not in chair_text, f"Zero counter at {width}"

            # ── Screenshot ──
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            suffix = "1440" if width == 1440 else "393"
            page.screenshot(
                path=str(SHOTS / f"arrival-week-{suffix}.png"),
                full_page=True,
            )

            # ── 393: no overflow ──
            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Arrival overflows at {width}"

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_orphan(self) -> None:
        """Orphan armed recording below MEETINGS, not counted."""
        from playwright.sync_api import sync_playwright

        _seed_orphan(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            headline = page.locator("[data-testid='arrival-display']")
            headline.wait_for(timeout=10_000)
            _settle(page)

            # MEETINGS section: 2 events (not counting orphan)
            meeting_rows = page.locator("[data-testid='arrival-meeting-row']")
            row_count = meeting_rows.count()
            assert row_count == 2, (
                f"Expected 2 meeting rows (orphan excluded), got {row_count}"
            )

            # Orphan row present
            orphans = page.locator("[data-testid='arrival-orphan-row']")
            assert orphans.count() >= 1, (
                f"Orphan row missing, got {orphans.count()}"
            )

            # Orphan carries ARMED chip
            orphan_text = orphans.first.text_content() or ""
            assert "ARMED" in orphan_text, (
                f"ARMED chip missing in orphan: {orphan_text[:120]}"
            )

            # Orphan carries FROM token with source_label (not empty parens)
            assert "FROM" in orphan_text, (
                f"FROM token missing in orphan: {orphan_text[:120]}"
            )
            assert "(WORK)" in orphan_text, (
                f"FROM token missing source_label in orphan: {orphan_text[:120]}"
            )
            assert "()" not in orphan_text, (
                f"Empty parentheses in orphan FROM token: {orphan_text[:120]}"
            )

            # Orphan has Cancel button
            orphan_cancel = orphans.first.locator("[data-testid='arrival-cancel-armed']")
            assert orphan_cancel.count() >= 1, (
                "Cancel button missing on orphan row"
            )

            # Week strip total matches event count, not event+orphan
            total_el = page.locator("[data-testid='arrival-week-total']")
            total_text = total_el.text_content() or ""
            import re
            m = re.match(r"(\d+)\s+MEETING", total_text)
            total_n = int(m.group(1)) if m else -1
            assert total_n == 2, (
                f"Week strip total should be 2, got {total_n}: '{total_text}'"
            )

            # Screenshot
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SHOTS / "arrival-armed-orphan-1440.png"),
                full_page=True,
            )

            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_past_future_mix(self) -> None:
        """Ruling: strip dots == total (the week's shape, including past events);
        MEETINGS rows == future-only count. A mismatch between the two on a
        Thursday is not a defect -- they are two honest facts.
        (Coordinator ruling, 2026-09-05.)"""
        from playwright.sync_api import sync_playwright

        _seed_past_future_mix(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            headline = page.locator("[data-testid='arrival-display']")
            headline.wait_for(timeout=10_000)
            _settle(page)

            # Strip total = 3 (all events in the week, including past)
            import re
            total_el = page.locator("[data-testid='arrival-week-total']")
            total_text = total_el.text_content() or ""
            m = re.match(r"(\d+)\s+MEETING", total_text)
            total_n = int(m.group(1)) if m else -1
            assert total_n == 3, (
                f"Strip total should be 3 (past + future), got {total_n}: '{total_text}'"
            )

            # Dots == total
            dots = page.locator("[data-testid='arrival-week-dot']")
            dot_count = dots.count()
            assert dot_count == total_n, (
                f"Dots ({dot_count}) != total ({total_n})"
            )

            # MEETINGS rows = 2 (future only)
            meeting_rows = page.locator("[data-testid='arrival-meeting-row']")
            row_count = meeting_rows.count()
            assert row_count == 2, (
                f"MEETINGS rows should be 2 (future only), got {row_count}"
            )

            # The mismatch (3 dots, 2 rows) is intentional per ruling.

            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_no_calendar(self) -> None:
        """No calendar configured: strip absent, NO CALENDAR shown."""
        from playwright.sync_api import sync_playwright

        _seed_no_calendar(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            headline = page.locator("[data-testid='arrival-display']")
            headline.wait_for(timeout=10_000)
            _settle(page)

            # WEEK strip absent
            strip = page.locator("[data-testid='arrival-week-strip']")
            assert strip.count() == 0, (
                f"WEEK strip should be absent without calendar, count={strip.count()}"
            )

            # NO CALENDAR state
            no_cal = page.locator("[data-testid='arrival-no-calendar']")
            assert no_cal.count() >= 1, (
                "NO CALENDAR state missing"
            )
            no_cal_text = no_cal.first.text_content() or ""
            assert "NO CALENDAR" in no_cal_text, (
                f"NO CALENDAR text missing: {no_cal_text}"
            )

            # Connect calendar verb
            connect_btn = page.locator("[data-testid='arrival-connect-calendar']")
            assert connect_btn.count() >= 1, (
                "Connect calendar button missing"
            )

            # Screenshot
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(
                path=str(SHOTS / "arrival-no-calendar-1440.png"),
                full_page=True,
            )

            _assert_clean(page, errors)
            page.close()
            browser.close()
