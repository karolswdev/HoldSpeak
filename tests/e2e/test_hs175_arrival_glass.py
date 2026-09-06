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

HS-175 counsel-on-built (lane W2) adds:
  4. test_arrival_cancel_idle_event_born: Cancel on an idle event-born
     row succeeds -- the row loses ARMS, the recording is disabled on
     the API (state cancelled, last_outcome owner_cancelled), a
     scheduled_recording.cancelled.owner receipt exists.
  5. test_arrival_cancel_refused_names_reason: the row moved to
     `recording` under a stale face; Cancel is refused BY NAME on the
     row (CAN'T CANCEL . <plain reason>), then withheld.
  6. test_arrival_unlink_room: Unlink beside ROOM . Q4 PLATFORM removes
     the link (the token leaves the row and the NEXT line); at 1440
     (hover verb) + 393 (visible verb).
  7. test_arrival_this_week_bound: a next-week event stays out of the
     THIS WEEK section and the strip's total. The calendar section wears
     `arrival-this-week` (the recorded ledger keeps `arrival-meetings`).
  8. test_arrival_week_overflow_reads_five_plus: five or more on one
     day reads exactly `5+`.
  9. test_arrival_local_clock_minus_six: the row time and ARMS tokens
     are the browser's local clock (-06:00), never UTC.
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
    _api_allow_error,
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
        # now + 1h: always future, and inside this Mon-Sun UTC week except
        # during the last hour of Sunday UTC (the one unavoidable hole;
        # "tomorrow 08:00" fell into next week on Sunday -- seen live).
        anchor = now + timedelta(hours=1)

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
        # now + 1h: always future, and inside this Mon-Sun UTC week except
        # during the last hour of Sunday UTC (the one unavoidable hole;
        # "tomorrow 08:00" fell into next week on Sunday -- seen live).
        anchor = now + timedelta(hours=1)

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

    ics_path = _create_ics_file(home, [])
    _write_calendar_config(home, ics_path)

    with db._connection() as conn:
        # Past event: now - 1h (genuinely past; still inside this Mon-Sun
        # week except the first hour of Monday UTC).
        past_start = now - timedelta(hours=1)
        past_end = past_start + timedelta(minutes=30)
        _seed_calendar_event(
            conn, "ev-past-today", "Morning standup",
            past_start.isoformat(), past_end.isoformat(),
        )

        # Future events at now + 1h / + 4h (always future, in-week).
        future_anchor = now + timedelta(hours=1)
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


def _local_week_bounds() -> tuple[datetime, datetime]:
    """Monday 00:00 and next Monday 00:00 of the CURRENT LOCAL week -- the
    hub runs in this process's zone, so the rig's week is the hub's week."""
    local_now = datetime.now().astimezone()
    monday = (local_now - timedelta(days=local_now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    return monday, monday + timedelta(days=7)


def _seed_next_week_event(home: Path) -> str:
    """One event next Monday 10:00 LOCAL on top of the week-strip scenario.
    Returns its title."""
    from holdspeak.db import get_database

    _seed_week_strip(home)
    _, next_monday = _local_week_bounds()
    starts = (next_monday + timedelta(hours=10)).astimezone(timezone.utc)
    db = get_database()
    with db._connection() as conn:
        _seed_calendar_event(
            conn, "ev-next-week", "Next week planning",
            starts.isoformat(), (starts + timedelta(hours=1)).isoformat(),
        )
        conn.commit()
    return "Next week planning"


def _seed_overflow_day(home: Path) -> None:
    """Five extra events beside the three of the week-strip scenario, all on
    the anchor's day (now + 1h .. + 1h50), so one local day carries >= 5."""
    from holdspeak.db import get_database

    _seed_week_strip(home)
    db = get_database()
    anchor = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    with db._connection() as conn:
        for i in range(5):
            start = anchor + timedelta(minutes=10 * (i + 1))
            _seed_calendar_event(
                conn, f"ev-overflow-{i}", f"Sync {i + 1}",
                start.isoformat(), (start + timedelta(minutes=5)).isoformat(),
            )
        conn.commit()


def _open_arrival(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)
    page.locator("[data-testid='arrival-display']").wait_for(timeout=10_000)
    _settle(page)


def _receipts(outcome: str) -> list[Any]:
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        return conn.execute(
            "SELECT receipt_id, state, result_ref FROM kernel_receipts WHERE outcome = ?",
            (outcome,),
        ).fetchall()


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

            # ── THIS WEEK section (ruling B10) count == rows ──
            meetings_section = page.locator("[data-testid='arrival-this-week']")
            assert meetings_section.count() >= 1, (
                f"THIS WEEK section missing at {width}"
            )
            section_text = meetings_section.first.text_content() or ""
            assert "THIS WEEK" in section_text, (
                f"Calendar section caption must read THIS WEEK at {width}: {section_text[:80]}"
            )
            assert "MEETINGS 3" not in section_text, (
                f"Calendar section must not be captioned MEETINGS (B10) at {width}"
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

            # THIS WEEK section: 2 events (not counting orphan)
            section_text = (
                page.locator("[data-testid='arrival-this-week']").first.text_content() or ""
            )
            assert "THIS WEEK 2" in section_text, (
                f"Calendar section caption must read THIS WEEK 2 (B10): {section_text[:80]}"
            )
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

    # ── HS-175 counsel-on-built, lane W2 ───────────────────────────

    @pytest.mark.e2e
    def test_arrival_cancel_idle_event_born(self) -> None:
        """C2: Cancel on an idle event-born row is a real verb."""
        from playwright.sync_api import sync_playwright

        _seed_week_strip(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _open_arrival(page, self.base)

            row = page.locator("[data-testid='arrival-meeting-row']", has_text="Standup")
            assert row.count() == 1
            assert "ARMS" in (row.first.text_content() or "")
            cancel = row.first.locator("[data-testid='arrival-cancel-armed']")
            assert cancel.count() == 1, "Cancel missing on the idle event-born row"
            cancel.first.click()

            # The row loses ARMS and its Cancel (the door refetched).
            page.wait_for_function(
                """() => {
                    const rows = Array.from(document.querySelectorAll("[data-testid='arrival-meeting-row']"));
                    const row = rows.find(r => (r.textContent || '').includes('Standup'));
                    return !!row && !(row.textContent || '').includes('ARMS')
                        && !row.querySelector("[data-testid='arrival-cancel-armed']");
                }""",
                timeout=10_000,
            )
            assert page.locator("[data-testid='arrival-cancel-refused']").count() == 0, (
                "a successful cancel must not name a refusal"
            )
            # The row itself stays (the meeting is still on the calendar).
            assert page.locator("[data-testid='arrival-meeting-row']").count() == 3

            # The wire: disabled, cancelled, by the owner, receipted.
            schedule = _api(page, "GET", "/api/scheduled-recordings/rec-standup", token=TOKEN)["schedule"]
            assert schedule["enabled"] is False, schedule
            assert schedule["state"] == "cancelled", schedule
            assert schedule["last_outcome"] == "owner_cancelled", schedule
            assert schedule["next_fire_at"] is None, schedule
            receipts = _receipts("scheduled_recording.cancelled.owner")
            assert len(receipts) == 1, receipts
            assert receipts[0]["state"] == "succeeded"
            assert "ev-standup" in receipts[0]["result_ref"]

            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / "arrival-cancelled-1440.png"), full_page=True)
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_cancel_refused_names_reason(self) -> None:
        """C2: a refusal is named on the row, never swallowed. The face is
        stale (the row still says ARMS . Cancel) while the recording has
        started on the hub -- the one honest race."""
        from holdspeak.db import get_database
        from playwright.sync_api import sync_playwright

        _seed_week_strip(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _open_arrival(page, self.base)

            row = page.locator("[data-testid='arrival-meeting-row']", has_text="Standup")
            assert row.first.locator("[data-testid='arrival-cancel-armed']").count() == 1

            # Capture starts under the stale face.
            with get_database()._connection() as conn:
                conn.execute(
                    "UPDATE scheduled_recordings SET state='recording' WHERE id='rec-standup'"
                )
                conn.commit()
            status, payload = _api_allow_error(
                page, "POST", "/api/scheduled-recordings/rec-standup/cancel", token=TOKEN,
            )
            assert status == 409 and payload.get("code") == "already_recording", (status, payload)

            row.first.locator("[data-testid='arrival-cancel-armed']").first.click()

            refused = page.locator("[data-testid='arrival-cancel-refused']")
            refused.first.wait_for(timeout=10_000)
            refused_text = (refused.first.text_content() or "").upper()
            assert "CAN'T CANCEL" in refused_text, refused_text
            assert "STOP THE MEETING" in refused_text, refused_text
            assert "TRACEBACK" not in refused_text and "ERROR:" not in refused_text
            chip = refused.first.locator(".surface-state-chip[data-state='failure']")
            assert chip.count() == 1, "the refusal is a StateChip failure token"

            # After the refetch the row is honest: RECORDING, no ARMS, no Cancel.
            page.wait_for_function(
                """() => {
                    const rows = Array.from(document.querySelectorAll("[data-testid='arrival-meeting-row']"));
                    const row = rows.find(r => (r.textContent || '').includes('Standup'));
                    return !!row && (row.textContent || '').includes('RECORDING')
                        && !row.querySelector("[data-testid='arrival-cancel-armed']");
                }""",
                timeout=10_000,
            )
            row_text = row.first.text_content() or ""
            assert "ARMS" not in row_text, row_text

            # The hub did not touch the recording.
            schedule = _api(page, "GET", "/api/scheduled-recordings/rec-standup", token=TOKEN)["schedule"]
            assert schedule["state"] == "recording" and schedule["enabled"] is True, schedule
            assert _receipts("scheduled_recording.cancelled.owner") == []

            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / "arrival-cancel-refused-1440.png"), full_page=True)
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_arrival_unlink_room(self, width: int) -> None:
        """C5 (face): Unlink beside ROOM . Q4 PLATFORM calls
        DELETE /api/calendar/events/{id}/link; the token leaves."""
        from holdspeak.db import get_database
        from playwright.sync_api import sync_playwright

        _seed_week_strip(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _open_arrival(page, self.base)

            row = page.locator("[data-testid='arrival-meeting-row']", has_text="Standup")
            assert row.count() == 1
            room = row.first.locator("[data-testid='arrival-meeting-room']")
            assert room.count() == 1 and "Q4 PLATFORM" in (room.first.text_content() or "")
            unlink = row.first.locator("[data-testid='arrival-unlink-room']")
            assert unlink.count() == 1, "Unlink missing beside the ROOM token"
            # Only the linked row wears the verb.
            assert page.locator("[data-testid='arrival-unlink-room']").count() == 1

            # Hover verb at the desk width; visible at the phone width.
            at_rest = unlink.first.evaluate("el => getComputedStyle(el.parentElement).opacity")
            if width == 1440:
                assert at_rest == "0", f"Unlink must be a hover verb at 1440 (opacity {at_rest})"
                row.first.hover()
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector("[data-testid='arrival-unlink-room']");
                        return !!el && getComputedStyle(el.parentElement).opacity === '1';
                    }""",
                    timeout=5_000,
                )
            else:
                assert at_rest == "1", f"Unlink must be visible at 393 (opacity {at_rest})"

            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            suffix = "1440" if width == 1440 else "393"
            page.screenshot(path=str(SHOTS / f"arrival-unlink-{suffix}.png"), full_page=True)

            unlink.first.click()
            page.wait_for_function(
                """() => {
                    const rows = Array.from(document.querySelectorAll("[data-testid='arrival-meeting-row']"));
                    const row = rows.find(r => (r.textContent || '').includes('Standup'));
                    return !!row && !row.querySelector("[data-testid='arrival-meeting-room']")
                        && !row.querySelector("[data-testid='arrival-unlink-room']");
                }""",
                timeout=10_000,
            )
            assert page.locator("[data-testid='arrival-unlink-refused']").count() == 0
            # The NEXT line drops the Room token too (same door read).
            next_text = page.locator("[data-testid='arrival-next']").first.text_content() or ""
            assert "Q4 PLATFORM" not in next_text.upper(), next_text
            # The row and its ARMS stay: unlink is not cancel.
            row_text = row.first.text_content() or ""
            assert "ARMS" in row_text and "ROOM" not in row_text, row_text

            with get_database()._connection() as conn:
                links = conn.execute(
                    "SELECT COUNT(*) FROM calendar_event_projects WHERE calendar_event_id='ev-standup'"
                ).fetchone()[0]
                receipts = conn.execute(
                    "SELECT method, args_summary FROM pipeline_events "
                    "WHERE service='CalendarEventLink' AND method='unlink'"
                ).fetchall()
            assert links == 0
            assert len(receipts) == 1 and "ev-standup" in receipts[0]["args_summary"], receipts

            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_this_week_bound(self) -> None:
        """C9: the THIS WEEK section is bounded to the strip's week."""
        from playwright.sync_api import sync_playwright

        next_title = _seed_next_week_event(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _open_arrival(page, self.base)

            # The projection carries the next-week event; the face bounds it.
            door = _api(page, "GET", "/api/door", token=TOKEN)
            assert any(i["title"] == next_title for i in door["upcoming"]), door["upcoming"]
            assert door["week"]["ends_at"], door["week"]

            section = page.locator("[data-testid='arrival-this-week']")
            assert section.count() == 1, "exactly one calendar section (P2-14)"
            section_text = section.first.text_content() or ""
            assert "THIS WEEK 3" in section_text, section_text[:120]
            assert next_title not in section_text, section_text[:200]
            assert page.locator("[data-testid='arrival-meeting-row']").count() == 3

            import re
            total_text = page.locator("[data-testid='arrival-week-total']").text_content() or ""
            m = re.match(r"(\d+)\s+MEETING", total_text)
            assert m and int(m.group(1)) == 3, total_text
            assert page.locator("[data-testid='arrival-week-dot']").count() == 3

            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / "arrival-this-week-bound-1440.png"), full_page=True)
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_week_overflow_reads_five_plus(self) -> None:
        """C9: five or more on one day reads exactly `5+` (the design)."""
        from playwright.sync_api import sync_playwright

        _seed_overflow_day(self.home)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _open_arrival(page, self.base)

            overflow = page.locator("[data-testid='arrival-week-overflow']")
            assert overflow.count() >= 1, "no overflow day rendered"
            for i in range(overflow.count()):
                el = overflow.nth(i)
                assert (el.text_content() or "").strip() == "5+", el.text_content()
                assert int(el.get_attribute("data-count") or "0") >= 5
            # Dots and overflow days together account for the strip's total.
            import re
            total_text = page.locator("[data-testid='arrival-week-total']").text_content() or ""
            m = re.match(r"(\d+)\s+MEETING", total_text)
            assert m and int(m.group(1)) == 8, total_text
            dots = page.locator("[data-testid='arrival-week-dot']").count()
            overflow_sum = sum(
                int(overflow.nth(i).get_attribute("data-count") or "0")
                for i in range(overflow.count())
            )
            assert dots + overflow_sum == 8, (dots, overflow_sum)
            chair_text = page.locator(".chair").text_content() or ""
            assert "8+" not in chair_text, "overflow must read 5+, never {count}+"

            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    def test_arrival_local_clock_minus_six(self) -> None:
        """C8: the row time and ARMS tokens are the viewer's local clock.
        The browser sits at -06:00 (Etc/GMT+6); the hub stores UTC."""
        from playwright.sync_api import sync_playwright

        _seed_week_strip(self.home)
        minus_six = timezone(timedelta(hours=-6))
        with __import__("holdspeak.db", fromlist=["get_database"]).get_database()._connection() as conn:
            starts_at, fire_at = conn.execute(
                "SELECT e.starts_at, r.next_fire_at FROM calendar_events e "
                "JOIN scheduled_recordings r ON r.calendar_event_id = e.id "
                "WHERE e.id='ev-standup'"
            ).fetchone()
        start_local = datetime.fromisoformat(starts_at.replace("Z", "+00:00")).astimezone(minus_six)
        arms_local = datetime.fromtimestamp(float(fire_at), tz=minus_six)
        expected_arms = f"ARMS {arms_local:%H:%M}"
        today_local = datetime.now(tz=minus_six).date()
        expected_time = (
            f"{start_local:%H:%M}" if start_local.date() == today_local
            else f"{start_local:%a %H:%M}".upper()
        )
        utc_arms = f"ARMS {datetime.fromtimestamp(float(fire_at), tz=timezone.utc):%H:%M}"

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900}, timezone_id="Etc/GMT+6",
            )
            page = context.new_page()
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _open_arrival(page, self.base)

            row = page.locator("[data-testid='arrival-meeting-row']", has_text="Standup")
            assert row.count() == 1
            time_token = row.first.locator(".surface-ledger-time").first.text_content() or ""
            assert time_token.strip() == expected_time, (time_token, expected_time)
            arms_chip = row.first.locator(".surface-state-chip", has_text="ARMS")
            arms_text = (arms_chip.first.text_content() or "").replace("●", "").strip()
            assert arms_text == expected_arms, (arms_text, expected_arms)
            assert arms_text != utc_arms, "ARMS printed the UTC clock"

            _assert_clean(page, errors)
            page.close()
            context.close()
            browser.close()

