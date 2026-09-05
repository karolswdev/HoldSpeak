"""HS-175-03 -- Settings Meetings CALENDAR section glass rig.

Seeds two calendar sources through the real seam (one file-based ICS in
the isolated HOME, one HTTPS-labelled source whose projection is seeded
directly), sets auto_record=room_linked with one linked event INSIDE
the current ISO week, navigates to Settings -> Meetings, and asserts
the artboard.

Shots to story-03-shots/:
  settings-calendar-1440.png, settings-calendar-393.png,
  settings-calendar-well-1440.png
"""
from __future__ import annotations

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
    _ensure_build,
    _settle,
    REPO,
)

pytest.importorskip("playwright.sync_api", reason="Calendar glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-03-shots"
TOKEN = "hs175-settings-calendar"


def _this_week_event_time() -> tuple[str, str]:
    """Return (starts_at, ends_at) for an event inside the current ISO week."""
    now = datetime.now(timezone.utc)
    # Move to the next weekday within this week (or today if still room).
    monday = now - timedelta(days=now.weekday())
    # Pick Wednesday of this week (always within the ISO week).
    wed = monday + timedelta(days=2)
    starts = wed.replace(hour=10, minute=0, second=0, microsecond=0)
    # If Wednesday is already past, use tomorrow (still within the week for most days).
    if starts < now:
        starts = now + timedelta(hours=1)
        starts = starts.replace(minute=0, second=0, microsecond=0)
    ends = starts + timedelta(hours=1)
    fmt = lambda dt: dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    return fmt(starts), fmt(ends)


def _seed_calendar_sources(tmp_path: Path) -> dict[str, str]:
    """Seed two calendar sources and their events via the real DB seam.

    Returns dict with source_id_file and source_id_https keys.
    """
    from holdspeak.config import Config
    from holdspeak.config.integrations import CalendarSource, CalendarConfig
    from holdspeak.db import get_database

    db = get_database()
    config = Config.load()

    sid_file = str(uuid.uuid4())
    sid_https = str(uuid.uuid4())

    # Create a minimal ICS file in the isolated HOME.
    ics_path = tmp_path / "home" / "work.ics"
    ics_path.parent.mkdir(parents=True, exist_ok=True)
    ics_path.write_text(
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "BEGIN:VEVENT\n"
        "UID:uid-standup-001\n"
        "SUMMARY:Standup\n"
        "DTSTART:20260908T100000Z\n"
        "DTEND:20260908T110000Z\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )

    sources = [
        CalendarSource(
            id=sid_file,
            label="WORK",
            url=str(ics_path),
            enabled=True,
        ),
        CalendarSource(
            id=sid_https,
            label="PERSONAL",
            url="https://calendar.google.com/ics/personal.ics",
            enabled=True,
        ),
    ]
    config.calendar = CalendarConfig(sources=sources)
    config.meeting.auto_record = "room_linked"
    config.meeting.auto_record_lead_minutes = 5
    config.save()

    # Seed events directly via the repository (no parser, no network).
    now = time.time()

    class _Evt:
        def __init__(self, **kw: Any):
            for k, v in kw.items():
                setattr(self, k, v)

    # File source: one event.
    file_event_id = str(uuid.uuid4())
    db.calendar_events.replace_projection(
        "rev-file",
        [
            _Evt(
                id=file_event_id,
                uid="uid-standup-001",
                title="Standup",
                starts_at="2026-09-08T10:00:00Z",
                ends_at="2026-09-08T11:00:00Z",
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=now,
        source_id=sid_file,
        source_label="WORK",
    )

    # HTTPS source: one event with meeting_url INSIDE this ISO week.
    starts_at, ends_at = _this_week_event_time()
    https_event_id = str(uuid.uuid4())
    db.calendar_events.replace_projection(
        "rev-https",
        [
            _Evt(
                id=https_event_id,
                uid="uid-review-001",
                title="Architecture Review",
                starts_at=starts_at,
                ends_at=ends_at,
                location=None,
                meeting_url="https://meet.google.com/abc-def",
            ),
        ],
        seen_at=now,
        source_id=sid_https,
        source_label="PERSONAL",
    )

    # Create a project and link the HTTPS event to it for matched_this_week.
    pid = str(uuid.uuid4())
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO projects (id, name) VALUES (?, ?)",
            (pid, "Q4 Platform"),
        )
    db.calendar_event_projects.link(https_event_id, pid, "title")

    return {
        "source_id_file": sid_file,
        "source_id_https": sid_https,
        "project_id": pid,
        "https_event_id": https_event_id,
    }


def _navigate_to_settings_hub(page: Any, url: str) -> None:
    """Navigate to the Settings hub (same as test_hs172)."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "configure-settings"})
        );
    }""")
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    page.locator(".prefs-hub-headline").wait_for(timeout=10_000)


def _open_meetings_module(page: Any) -> None:
    """Open the Meetings module from the Settings hub (same as test_hs172)."""
    meetings_row = page.locator(
        ".surface-ledger-row",
        has=page.locator(".surface-ledger-primary", has_text="Meetings"),
    )
    meetings_row.locator(".btn", has_text="Open").click()
    page.locator("[data-testid='meetings-auto-display']").wait_for(timeout=8_000)


class TestSettingsCalendarSection:
    """HS-175-03: the Settings Meetings CALENDAR section at both widths."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.tmp_path = tmp_path
        self.ids = _seed_calendar_sources(tmp_path)

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.parametrize("width", [1440, 393])
    def test_calendar_section(self, width: int) -> None:
        """Calendar section: source rows, connect row, auto-record."""
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_meetings_module(page)
            _settle(page)

            body_text = page.locator(".desk-surface-body").text_content() or ""

            # -- CALENDAR caption below CAPTURE + EXPORT --
            calendar_section = page.locator(".prefs-calendar-section")
            assert calendar_section.count() >= 1, (
                f"Calendar section (.prefs-calendar-section) not found at {width}"
            )
            assert "CALENDAR" in body_text, (
                f"CALENDAR caption not found at {width}"
            )

            # Capture + export is above CALENDAR.
            assert "Mic device" in body_text, f"Mic device missing at {width}"
            assert "Auto export" in body_text, f"Auto export missing at {width}"

            # -- Source rows with correct chips --
            sources_container = page.locator(".prefs-calendar-sources")
            assert sources_container.count() >= 1, (
                f"Sources container not found at {width}"
            )
            sources_text = sources_container.text_content() or ""
            assert "ICS" in sources_text, f"ICS type token missing at {width}"

            # StateChip dots present.
            state_chips = sources_container.locator(".surface-state-chip")
            assert state_chips.count() >= 2, (
                f"Expected 2 StateChips on source rows at {width}, got {state_chips.count()}"
            )

            # EgressChip on the HTTPS source.
            assert "calendar.google.com" in sources_text, (
                f"Egress host missing at {width}: {sources_text[:200]}"
            )

            # THIS DEVICE on the file source.
            assert "THIS DEVICE" in sources_text, (
                f"THIS DEVICE chip missing for file source at {width}"
            )

            # N CALENDARS present (both sources have events).
            assert "CALENDAR" in sources_text, (
                f"CALENDAR count token missing at {width}"
            )

            # LAST READ present.
            assert "LAST READ" in sources_text, (
                f"LAST READ token missing at {width}"
            )

            # -- Connect calendar row --
            connect_row = page.locator("[data-testid='calendar-connect-row']")
            assert connect_row.count() >= 1, (
                f"Connect calendar row not found at {width}"
            )
            add_btn = page.locator("[data-testid='calendar-add-btn']")
            assert add_btn.count() >= 1, (
                f"Add button missing at {width}"
            )

            # -- Auto-record row --
            auto_record = page.locator("[data-testid='settings-auto-record']")
            assert auto_record.count() >= 1, (
                f"Auto-record row not found at {width}"
            )
            ar_text = auto_record.text_content() or ""
            assert "Auto-record" in ar_text, (
                f"Auto-record label missing at {width}"
            )

            # CycleGadget present.
            cycle = auto_record.locator("select")
            assert cycle.count() >= 1, (
                f"CycleGadget on Auto-record row missing at {width}"
            )

            # 5 MIN BEFORE (auto_record=room_linked).
            assert "MIN BEFORE" in ar_text, (
                f"5 MIN BEFORE token missing at {width}: {ar_text}"
            )

            # N MATCHED THIS WEEK must be present (event seeded inside this week).
            matched_chip = page.locator("[data-testid='matched-this-week']")
            assert matched_chip.count() >= 1, (
                f"MATCHED THIS WEEK chip not found at {width}"
            )
            matched_text = matched_chip.text_content() or ""
            assert "MATCHED THIS WEEK" in matched_text, (
                f"MATCHED THIS WEEK text wrong: {matched_text}"
            )

            # -- The verbs on every source row (Edit / Disable / Remove), both widths --
            for sid in (self.ids["source_id_file"], self.ids["source_id_https"]):
                row = page.locator(f"[data-testid='calendar-source-{sid}']")
                assert row.count() == 1, f"source row {sid} missing at {width}"
                for verb in ("Edit", "Disable", "Remove"):
                    verb_btn = row.locator(".btn", has_text=verb)
                    assert verb_btn.count() == 1, f"{verb} verb missing on {sid} at {width}"
                    assert verb_btn.is_visible(), f"{verb} verb hidden on {sid} at {width}"

            # -- Labels are single-line at 1440 --
            if width == 1440:
                single_line = page.evaluate("""() => {
                    const section = document.querySelector('.prefs-calendar-section');
                    if (!section) return { ok: false, reason: 'no section' };
                    const primaries = section.querySelectorAll('.surface-ledger-primary');
                    const bad = [];
                    for (const el of primaries) {
                        const style = getComputedStyle(el);
                        const lineH = parseFloat(style.lineHeight) || parseFloat(style.fontSize) * 1.2;
                        const boxH = el.getBoundingClientRect().height;
                        if (boxH > lineH * 1.5) {
                            bad.push((el.textContent || '').trim().slice(0, 30) + ': ' + boxH.toFixed(1) + '/' + lineH.toFixed(1));
                        }
                    }
                    return { ok: bad.length === 0, bad };
                }""")
                assert single_line["ok"], (
                    f"Labels wrap at 1440 (box > 1.5x line-height): {single_line['bad']}"
                )

            # -- No intersecting children, both widths: rows never overlap
            #    each other, and inside every row line the lead / primary /
            #    cells / verbs never overprint one another (the 1440 verbs-
            #    over-LAST-READ scar). --
            intersections = page.evaluate("""() => {
                const section = document.querySelector('.prefs-calendar-section');
                if (!section) return ['no section'];
                const box = (el) => el.getBoundingClientRect();
                const overlap = (a, b) => {
                    const x = Math.min(a.right, b.right) - Math.max(a.left, b.left);
                    const y = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
                    return x > 2 && y > 2 ? x.toFixed(0) + 'x' + y.toFixed(0) : null;
                };
                const out = [];
                const rows = Array.from(section.querySelectorAll('.surface-ledger-row'));
                for (let i = 0; i < rows.length; i++) {
                    for (let j = i + 1; j < rows.length; j++) {
                        const o = overlap(box(rows[i]), box(rows[j]));
                        if (o) out.push('row ' + i + ' x row ' + j + ': ' + o);
                    }
                }
                for (const line of section.querySelectorAll('.surface-ledger-line')) {
                    const kids = Array.from(line.children).filter(k => box(k).width > 0 && box(k).height > 0);
                    for (let i = 0; i < kids.length; i++) {
                        for (let j = i + 1; j < kids.length; j++) {
                            const o = overlap(box(kids[i]), box(kids[j]));
                            if (o) out.push((line.textContent || '').trim().slice(0, 24) + ': '
                                + kids[i].className + ' x ' + kids[j].className + ' ' + o);
                        }
                    }
                }
                return out;
            }""")
            assert len(intersections) == 0, (
                f"CALENDAR children intersect at {width}: {intersections}"
            )

            # -- No raw <button> outside library --
            raw_buttons = page.evaluate("""() => {
                const body = document.querySelector('.desk-surface-body') || document.body;
                const allowed = ['btn', 'desk-mic', 'gadget-cycle',
                    'gadget-stepper-btn', 'gadget-table-add',
                    'gadget-table-delete', 'surface-ledger-line',
                    'surface-edit-in-place', 'surface-disclosure-trigger',
                    'gadget-transport-key'];
                return Array.from(body.querySelectorAll('button'))
                    .filter(b => !allowed.some(c => b.classList.contains(c))
                        && !b.closest('.gadget-stepper')
                        && !b.closest('.gadget-table')
                        && !b.closest('.gadget-string')
                        && !b.closest('.mic-button')
                        && !b.closest('.cycle-gadget')
                        && !b.closest('.fold-gadget')
                        && !b.closest('.check-gadget')
                        && !b.closest('.stepper-gadget')
                        && !b.closest('.scroll-hint')
                        && !b.closest('.desk-traffic')
                        && !b.closest('.desk-wings')
                        && !b.closest('.surface-ledger-row')
                        && !b.closest('[role="tablist"]'))
                    .map(b => (b.textContent || '').trim().slice(0, 40));
            }""")
            assert len(raw_buttons) == 0, f"Raw buttons at {width}: {raw_buttons}"

            # -- No zero counters --
            zero_counters = page.evaluate("""() => {
                const el = document.querySelector('.prefs-calendar-section');
                if (!el) return [];
                const text = el.textContent || '';
                const re = /\\b0\\s+(SOURCE|CALENDAR|RECORDING|MATCHED)/gi;
                const matches = [];
                let m;
                while ((m = re.exec(text)) !== null) matches.push(m[0]);
                return matches;
            }""")
            assert len(zero_counters) == 0, (
                f"Zero counters at {width}: {zero_counters}"
            )

            # Scroll to CALENDAR and shoot.
            calendar_section.scroll_into_view_if_needed()
            SHOTS.mkdir(parents=True, exist_ok=True)
            _settle(page)
            page.screenshot(
                path=str(SHOTS / f"settings-calendar-{width}.png"),
                full_page=True,
            )

            if width == 393:
                no_overflow = page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert no_overflow, f"Calendar section overflows at {width}"

            # -- Remove: one in-world confirm step under the row, then Cancel --
            file_row = page.locator(f"[data-testid='calendar-source-{self.ids['source_id_file']}']")
            file_row.locator(".btn", has_text="Remove").click()
            confirm = page.locator("[data-testid='calendar-remove-confirm']")
            confirm.wait_for(timeout=3_000)
            assert page.locator("[role='dialog']").count() == 0, f"Remove opened a modal at {width}"
            assert confirm.locator(".btn", has_text="Remove").count() == 1
            assert confirm.locator(".btn", has_text="Cancel").count() == 1
            confirm.locator(".btn", has_text="Cancel").click()
            assert page.locator("[data-testid='calendar-remove-confirm']").count() == 0, (
                f"Remove confirm did not fold on Cancel at {width}"
            )

            # -- Edit: the SAME well unfolds under the row, pre-filled --
            file_row.locator(".btn", has_text="Edit").click()
            edit_well = page.locator("[data-testid='calendar-well']")
            edit_well.wait_for(timeout=3_000)
            prefilled = edit_well.locator("input[type='text']").input_value()
            assert prefilled.endswith("work.ics"), f"Edit well not pre-filled at {width}: {prefilled!r}"
            assert edit_well.locator(".desk-mic").count() >= 1, f"Edit well has no mic at {width}"
            edit_well.locator(".btn", has_text="Cancel").click()
            assert page.locator("[data-testid='calendar-well']").count() == 0, (
                f"Edit well did not fold on Cancel at {width}"
            )

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_calendar_well_unfold(self) -> None:
        """Add button unfolds the connect well with StringGadget + mic."""
        from playwright.sync_api import sync_playwright

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_meetings_module(page)
            _settle(page)

            # Scroll to the Add button and click.
            add_btn = page.locator("[data-testid='calendar-add-btn']")
            add_btn.scroll_into_view_if_needed()
            add_btn.click()
            page.wait_for_timeout(500)

            # Well should be visible.
            well = page.locator("[data-testid='calendar-well']")
            assert well.count() >= 1, "Calendar well did not unfold"

            well_text = well.text_content() or ""

            # StringGadget with placeholder.
            gadget_input = well.locator("input[type='text']")
            assert gadget_input.count() >= 1, "StringGadget input missing in well"
            placeholder = gadget_input.get_attribute("placeholder") or ""
            assert "ICS" in placeholder or "file" in placeholder, (
                f"Placeholder should mention ICS/file: {placeholder}"
            )

            # MicButton present.
            mic = well.locator(".desk-mic")
            assert mic.count() >= 1, "MicButton missing in connect well"

            # Cancel and Save buttons.
            assert "Cancel" in well_text, "Cancel button missing in well"
            assert "Save" in well_text, "Save button missing in well"

            # Screenshot of the well open state.
            well.scroll_into_view_if_needed()
            SHOTS.mkdir(parents=True, exist_ok=True)
            _settle(page)
            page.screenshot(
                path=str(SHOTS / "settings-calendar-well-1440.png"),
                full_page=True,
            )

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_matched_absent_when_zero(self) -> None:
        """When auto_record is off, MATCHED THIS WEEK is absent (A.8)."""
        from playwright.sync_api import sync_playwright
        from holdspeak.config import Config

        # Set auto_record to off.
        config = Config.load()
        config.meeting.auto_record = "off"
        config.save()

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _navigate_to_settings_hub(page, self.base)
            _open_meetings_module(page)
            _settle(page)

            auto_record = page.locator("[data-testid='settings-auto-record']")
            ar_text = auto_record.text_content() or ""

            # MATCHED THIS WEEK should not be present when OFF.
            assert "MATCHED THIS WEEK" not in ar_text, (
                f"MATCHED THIS WEEK should be absent when OFF: {ar_text}"
            )
            # 5 MIN BEFORE should not be present when OFF.
            assert "MIN BEFORE" not in ar_text, (
                f"MIN BEFORE should be absent when OFF: {ar_text}"
            )

            _assert_clean(page, errors)
            page.close()
            errors.clear()
            browser.close()
