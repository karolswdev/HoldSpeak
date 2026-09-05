"""HS-175-06 walk runner: Calendar and the Clock -- read-only walk of the owner's real hub.

Shoots five faces (arrival, Settings Meetings, Room SOURCES, and Rhythm)
at 1440x900 and 393x852.  ZERO WRITES.  This walk is entirely read-only
on the owner's desk.

THE LIVE LAWS (Article IV -- the walk arms nothing):
1. READ-ONLY.  Never connects a calendar.  Never changes Auto-record.
   Never arms or cancels a recording.  Never links an event to a Room.
   Never generates a brief.  Never presses Run now.
2. NO HARDCODED TOKENS.
3. FACE-DRIVEN.
4. STANDALONE.  Not collected by pytest.

Usage:
  python tests/e2e/live175_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

# -- pytest collection guard --
collect_ignore_glob = ["live175_walk.py"]


# ---------------------------------------------------------------------------
# Write guard (fail-closed: no writes permitted)
# ---------------------------------------------------------------------------

def _write_allowed(
    operation: str | None,
    context: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Decide whether a write operation is allowed in this walk.

    Returns (allowed: bool, reason: str).

    This walk is ENTIRELY READ-ONLY.  No write operation is permitted.
    The guard exists to make the prohibition explicit and fail-closed:
    any new step that calls it gets DENIED with a named reason.

    Decision table:
        _write_allowed("connect_calendar")   -> (False, "never connects a calendar")
        _write_allowed("change_auto_record") -> (False, "never changes Auto-record")
        _write_allowed("arm_recording")      -> (False, "never arms a recording")
        _write_allowed("cancel_recording")   -> (False, "never cancels a recording")
        _write_allowed("link_event_room")    -> (False, "never links an event to a Room")
        _write_allowed("generate_brief")     -> (False, "never generates a brief")
        _write_allowed("run_now")            -> (False, "never presses Run now")
        _write_allowed("run_intel")          -> (False, "never runs intelligence")
        _write_allowed("publish")            -> (False, "never publishes")
        _write_allowed("unknown")            -> (False, "unknown operation denied by default")
        _write_allowed("")                   -> (False, "empty operation denied")
        _write_allowed(None)                 -> (False, "null operation denied")
    """
    if not operation:
        return False, "empty operation denied" if operation == "" else "null operation denied"
    _DENIALS: dict[str, str] = {
        "connect_calendar": "never connects a calendar",
        "change_auto_record": "never changes Auto-record",
        "arm_recording": "never arms a recording",
        "cancel_recording": "never cancels a recording",
        "link_event_room": "never links an event to a Room",
        "generate_brief": "never generates a brief",
        "run_now": "never presses Run now",
        "run_intel": "never runs intelligence",
        "publish": "never publishes",
    }
    reason = _DENIALS.get(operation, "unknown operation denied by default")
    return False, reason


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/assets/story-06-shots"

VIEWPORTS = [
    {"width": 1440, "height": 900, "suffix": "1440"},
    {"width": 393, "height": 852, "suffix": "393"},
]


# -- Data model --

@dataclass
class FaceFact:
    face: str
    field: str
    expected: str
    observed: str
    verdict: str
    why: str


@dataclass
class WalkReport:
    generated_at: str = ""
    hub_host: str = ""
    viewports: list[dict] = field(default_factory=list)
    shots: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)


# -- Helpers --

def _settle(page: Any) -> None:
    page.evaluate("""() => {
        const anims = document.getAnimations();
        if (anims.length === 0) return;
        return Promise.race([
            Promise.all(anims.map(a => a.finished.catch(() => null))),
            new Promise(r => setTimeout(r, 2000)),
        ]);
    }""")
    page.wait_for_timeout(200)


def _shoot(page: Any, out_dir: Path, name: str, w: int,
           window: bool = False) -> Path:
    _settle(page)
    fname = f"{name}-{w}.png"
    path = out_dir / fname
    path.parent.mkdir(parents=True, exist_ok=True)
    if window:
        win_el = page.locator('.desk-surface-window').last
        if win_el.count() > 0 and win_el.is_visible():
            win_el.screenshot(path=str(path))
        else:
            page.screenshot(path=str(path), full_page=False)
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.exists() and path.stat().st_size > 1_000, f"Shot {fname} missing or too small"
    return path


def _check_overflow(page: Any, w: int, face_name: str) -> str | None:
    result = page.evaluate("""() => {
        const sw = document.documentElement.scrollWidth;
        const cw = document.documentElement.clientWidth;
        return { scrollWidth: sw, clientWidth: cw };
    }""")
    if result["scrollWidth"] > result["clientWidth"]:
        return (f"OVERFLOW on {face_name} at {w}: "
                f"scrollWidth={result['scrollWidth']} > clientWidth={result['clientWidth']}")
    return None


_FETCH_JS = """async ([method, path, body, token]) => {
  const response = await fetch(path, {
    method,
    headers: {
      authorization: `Bearer ${token}`,
      ...(body ? {"content-type": "application/json"} : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("json")
    ? await response.json()
    : await response.text();
  return {status: response.status, payload};
}"""


def _api(page: Any, method: str, path: str,
         body: dict[str, Any] | None, token: str) -> dict[str, Any]:
    return page.evaluate(_FETCH_JS, [method, path, body, token])


def _fact(face: str, fld: str, expected: str, observed: str) -> FaceFact:
    if not observed or observed == "---":
        return FaceFact(face=face, field=fld, expected=expected,
                        observed=observed, verdict="DATA", why="no data observed")
    exp_l = expected.lower().strip()
    obs_l = observed.lower().strip()
    if exp_l == obs_l:
        v, w = "MATCH", "exact"
    elif exp_l in obs_l or obs_l in exp_l:
        v, w = "MATCH", "substring"
    else:
        v, w = "DATA", f"board={expected}, real={observed}"
    return FaceFact(face=face, field=fld, expected=expected,
                    observed=observed, verdict=v, why=w)


def _open_surface(page: Any, token: str, action: str, scope: str | None = None) -> None:
    payload: dict[str, str] = {"key": action}
    if scope:
        payload["scope"] = scope
    page.evaluate(f"""() => {{
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({json.dumps(payload)})
        );
    }}""")
    page.reload(wait_until="load")
    page.wait_for_timeout(500)
    try:
        chair = page.locator(".chair")
        if chair.count() > 0:
            chair.wait_for(timeout=2000)
            if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                btn = page.get_by_role("button", name="Continue later", exact=True)
                if btn.count() > 0:
                    btn.click()
    except Exception:
        pass
    page.wait_for_timeout(1500)
    _settle(page)


def _close_surface(page: Any) -> None:
    close_btn = page.locator('.desk-surface-window .desk-light-close').last
    if close_btn.count() > 0 and close_btn.is_visible():
        close_btn.click()
        page.wait_for_timeout(500)
        _settle(page)


# -- Raw-button exclusion list (from live173_walk.py) --

_RAW_BTN_EXCLUDE_JS = """
    if (btn.classList.contains('btn') ||
        btn.classList.contains('signal-button') ||
        btn.classList.contains('surface-ledger-line') ||
        btn.classList.contains('surface-edit-in-place') ||
        btn.classList.contains('desk-mic') ||
        btn.classList.contains('surface-disclosure-trigger') ||
        btn.classList.contains('gadget-transport-key') ||
        btn.closest('.gadget-string') ||
        btn.closest('.mic-button') ||
        btn.closest('.cycle-gadget') ||
        btn.closest('.fold-gadget') ||
        btn.closest('.check-gadget') ||
        btn.closest('.stepper-gadget') ||
        btn.closest('.scroll-hint') ||
        btn.closest('.desk-traffic') ||
        btn.closest('.desk-wings') ||
        btn.closest('.surface-ledger-row') ||
        btn.closest('[role="tablist"]')) continue;
"""


# ---------------------------------------------------------------------------
# Step 1: read the door payload and meeting settings via the API
# ---------------------------------------------------------------------------

def _step_door_api(page: Any, token: str, report: WalkReport) -> dict:
    """Read GET /api/door for calendar_configured, upcoming (count,
    whether any carries a room, whether any is armed) and week when
    present.  Read GET /api/settings for auto_record.  Read
    GET /api/cadence for the brief kind.

    Returns a dict with:
      calendar_configured -- bool
      upcoming_count      -- int
      upcoming_has_room   -- bool: any event carries a room link
      upcoming_has_armed  -- bool: any event carries armed_schedule_id
      upcoming_ids        -- set of (source, id) tuples for dup detection
      week                -- list of day dicts (or None if absent)
      auto_record         -- str: off / with_url / all
      brief_kind          -- str: monday / weekly (or None)
      project_id          -- str: first project id (for Room step)
    """
    face = "door-api"
    out: dict[str, Any] = {}

    # GET /api/door
    door = _api(page, "GET", "/api/door", None, token)
    if door["status"] >= 300:
        report.errors.append(f"GET /api/door returned {door['status']}")
        out["calendar_configured"] = False
        return out

    dp = door["payload"]
    cal_conf = bool(dp.get("calendar_configured", False))
    upcoming = dp.get("upcoming", [])
    week = dp.get("week")
    out["calendar_configured"] = cal_conf
    out["upcoming_count"] = len(upcoming)

    report.facts.append(asdict(FaceFact(
        face=face, field="calendar_configured",
        expected="(true when at least one source connected)",
        observed=str(cal_conf),
        verdict="DATA", why="calendar adapter state",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="upcoming_count",
        expected="(varies)",
        observed=str(len(upcoming)),
        verdict="DATA", why="upcoming events + scheduled recordings",
    )))

    # Check whether any upcoming item carries a Room link or armed state.
    has_room = False
    has_armed = False
    seen_ids: set[tuple[str, str]] = set()
    duplicates: list[str] = []
    for item in upcoming:
        source = str(item.get("source", ""))
        item_id = str(item.get("id", ""))
        key = (source, item_id)
        if key in seen_ids:
            duplicates.append(f"{source}:{item_id[:12]}")
        seen_ids.add(key)
        if item.get("room_id") or item.get("project_id"):
            has_room = True
        if item.get("armed_schedule_id") or item.get("armed"):
            has_armed = True
    out["upcoming_has_room"] = has_room
    out["upcoming_has_armed"] = has_armed
    out["upcoming_ids"] = seen_ids

    report.facts.append(asdict(FaceFact(
        face=face, field="upcoming_has_room",
        expected="(true when an event links to a Room)",
        observed=str(has_room),
        verdict="DATA", why="event-to-Room link in upcoming",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="upcoming_has_armed",
        expected="(true when an event auto-created a recording)",
        observed=str(has_armed),
        verdict="DATA", why="armed schedule in upcoming",
    )))

    if duplicates:
        report.defects.append(
            f"DOOR API: duplicate upcoming entries -- A.7: {duplicates}"
        )

    # Week strip (D2 element -- may not exist yet).
    if week is not None:
        out["week"] = week
        week_count = len(week) if isinstance(week, list) else 0
        week_dots = sum(
            d.get("count", 0) if isinstance(d, dict) else 0
            for d in (week if isinstance(week, list) else [])
        )
        report.facts.append(asdict(FaceFact(
            face=face, field="week_days",
            expected="7 (Mon-Sun strip)",
            observed=str(week_count),
            verdict="MATCH" if week_count == 7 else "DATA",
            why="WEEK strip day count from door payload",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="week_total_dots",
            expected="(matches N MEETINGS THIS WEEK)",
            observed=str(week_dots),
            verdict="DATA", why="sum of dots across WEEK strip days",
        )))
    else:
        out["week"] = None
        report.facts.append(asdict(FaceFact(
            face=face, field="week",
            expected="(present when calendar configured)",
            observed="absent",
            verdict="DATA",
            why="WEEK strip not in door payload (face may not have landed)",
        )))

    # GET /api/settings for auto_record
    settings = _api(page, "GET", "/api/settings", None, token)
    if settings["status"] == 200:
        sp = settings["payload"]
        meeting_cfg = sp.get("meeting", {}) if isinstance(sp, dict) else {}
        auto_record = str(meeting_cfg.get("auto_record", "off"))
        out["auto_record"] = auto_record
        report.facts.append(asdict(FaceFact(
            face=face, field="auto_record",
            expected="(off / with_url / all)",
            observed=auto_record,
            verdict="DATA", why="meeting auto-record setting",
        )))
    else:
        out["auto_record"] = "unknown"
        report.facts.append(asdict(FaceFact(
            face=face, field="settings_status",
            expected="200", observed=str(settings["status"]),
            verdict="DATA", why=f"GET /api/settings returned HTTP {settings['status']}",
        )))

    # GET /api/cadence for brief kind
    cadence = _api(page, "GET", "/api/cadence", None, token)
    if cadence["status"] == 200:
        cp = cadence["payload"]
        brief_kind = None
        if isinstance(cp, dict):
            brief_kind = cp.get("brief_kind", cp.get("briefKind"))
        out["brief_kind"] = str(brief_kind) if brief_kind else None
        report.facts.append(asdict(FaceFact(
            face=face, field="brief_kind",
            expected="(monday or weekly)",
            observed=str(brief_kind) if brief_kind else "absent",
            verdict="DATA", why="brief kind from cadence API",
        )))
    else:
        out["brief_kind"] = None
        report.facts.append(asdict(FaceFact(
            face=face, field="cadence_status",
            expected="200", observed=str(cadence["status"]),
            verdict="DATA", why=f"GET /api/cadence returned HTTP {cadence['status']}",
        )))

    # First project id (for Room step).
    proj_result = _api(page, "GET", "/api/projects", None, token)
    if proj_result["status"] == 200:
        proj_list = proj_result["payload"]
        plist = proj_list.get("projects", []) if isinstance(proj_list, dict) else proj_list
        if plist:
            out["project_id"] = str(plist[0].get("id", ""))
            out["project_name"] = str(plist[0].get("name", plist[0].get("title", "---")))[:12]
        else:
            report.surprises.append("DOOR API: zero projects on owner's desk")
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="projects_status",
            expected="200", observed=str(proj_result["status"]),
            verdict="DATA", why=f"GET /api/projects returned HTTP {proj_result['status']}",
        )))

    return out


# ---------------------------------------------------------------------------
# Step 2: open the arrival, shoot, record NEXT / WEEK / events
# ---------------------------------------------------------------------------

def _step_arrival(page: Any, out_dir: Path, w: int, token: str,
                  report: WalkReport, door_state: dict) -> None:
    """Open the arrival at the given width, shoot walk-arrival-{w}.png.

    Records: the NEXT line text (12-char prefix), whether the WEEK strip
    is present and its dot total vs the N MEETINGS THIS WEEK total (they
    must agree -- DEFECT otherwise), whether any event row carries
    ROOM or ARMS, that the same recording is not shown twice (A.7).
    """
    face = "arrival"

    # The arrival is the default landing -- just settle.
    _settle(page)
    page.wait_for_timeout(1000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-arrival", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the arrival face.
    # Real selectors from ChairHome.tsx:
    #   data-testid="arrival-next"          -- the NEXT line
    #   data-testid="arrival-no-calendar"   -- NO CALENDAR state
    #   data-testid="arrival-arming"        -- ARMED countdown row
    #   data-testid="arrival-cancel-armed"  -- Cancel button on armed row
    #   data-testid="arrival-meetings"      -- meetings section container
    #   data-testid="arrival-meeting-row"   -- each meeting row
    #   data-testid="arrival-meeting-badge" -- badge on meeting row
    #   data-testid="arrival-run-intel"     -- Run intelligence verb
    # TODO selectors (D2 elements not yet built):
    #   data-testid="arrival-week-strip"    -- the WEEK strip container
    #   data-testid="arrival-week-dot"      -- each day dot in the strip
    #   data-testid="arrival-week-total"    -- N MEETINGS THIS WEEK token
    arrival_data = page.evaluate("""() => {
        const body = document.querySelector('.chair') || document.body;
        const bodyText = body.textContent || '';

        /* NEXT line: data-testid="arrival-next" */
        const nextEl = body.querySelector('[data-testid="arrival-next"]');
        const nextText = nextEl ? nextEl.textContent.trim() : '---';

        /* NO CALENDAR state: data-testid="arrival-no-calendar" */
        const noCalEl = body.querySelector('[data-testid="arrival-no-calendar"]');
        const noCalendar = Boolean(noCalEl);

        /* ARMED row: data-testid="arrival-arming" */
        const armingEl = body.querySelector('[data-testid="arrival-arming"]');
        const armingText = armingEl ? armingEl.textContent.trim() : null;

        /* WEEK strip: TODO data-testid="arrival-week-strip" */
        const weekStripEl = body.querySelector('[data-testid="arrival-week-strip"]');
        let weekStripPresent = Boolean(weekStripEl);
        let weekDotTotal = 0;
        let weekMeetingsLabel = null;
        if (weekStripEl) {
            const dots = weekStripEl.querySelectorAll('[data-testid="arrival-week-dot"]');
            weekDotTotal = dots.length;
            const totalEl = weekStripEl.querySelector('[data-testid="arrival-week-total"]');
            if (totalEl) weekMeetingsLabel = totalEl.textContent.trim();
        }

        /* Meetings section: data-testid="arrival-meetings" */
        const meetingsSection = body.querySelector('[data-testid="arrival-meetings"]');
        const meetingRows = meetingsSection
            ? meetingsSection.querySelectorAll('[data-testid="arrival-meeting-row"]')
            : [];
        const meetingCount = meetingRows.length;

        /* Check each meeting row for ROOM and ARMS tokens */
        let roomCount = 0;
        let armsCount = 0;
        const seenTitles = [];
        const duplicateTitles = [];
        for (const row of meetingRows) {
            const rowText = row.textContent || '';
            if (/ROOM/i.test(rowText)) roomCount++;
            if (/ARMS/i.test(rowText)) armsCount++;
            /* Check for duplicate armed rows (A.7) */
            const badge = row.querySelector('[data-testid="arrival-meeting-badge"]');
            const badgeText = badge ? badge.textContent.trim() : '';
            const titleEl = row.querySelector('.arrival-meeting-title, .surface-primary');
            const title = titleEl ? titleEl.textContent.trim().slice(0, 30) : rowText.slice(0, 30);
            const key = title + '|' + badgeText;
            if (seenTitles.includes(key)) {
                duplicateTitles.push(title.slice(0, 12));
            }
            seenTitles.push(key);
        }

        /* Defect scans */
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(MEETING|EVENT|CALENDAR|RECORDING)/gi;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const hasLocal = bodyText.includes('LOCAL');

        const clippedTexts = [];
        const primEls = body.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"], .arrival-next'
        );
        for (const el of primEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            nextText, noCalendar, armingText,
            weekStripPresent, weekDotTotal, weekMeetingsLabel,
            meetingCount, roomCount, armsCount,
            duplicateTitles,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""")

    # Record facts.
    next_text = arrival_data.get("nextText", "---")
    report.facts.append(asdict(FaceFact(
        face=face, field="next_line",
        expected="(NEXT <title> <time> -- from calendar or schedule)",
        observed=next_text[:12] if next_text != "---" else "---",
        verdict="DATA", why="NEXT line on arrival (12-char prefix)",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="no_calendar_state",
        expected="false (calendar should be configured)",
        observed=str(arrival_data.get("noCalendar", False)),
        verdict=(
            "MATCH"
            if not arrival_data.get("noCalendar")
            else "DATA"
        ),
        why="NO CALENDAR banner on arrival",
    )))

    # WEEK strip.
    week_present = arrival_data.get("weekStripPresent", False)
    report.facts.append(asdict(FaceFact(
        face=face, field="week_strip_present",
        expected="(true when calendar configured -- TODO face)",
        observed=str(week_present),
        verdict="DATA", why="WEEK strip on arrival face",
    )))
    if week_present:
        dot_total = arrival_data.get("weekDotTotal", 0)
        meetings_label = arrival_data.get("weekMeetingsLabel")
        report.facts.append(asdict(FaceFact(
            face=face, field="week_dot_total",
            expected="(matches N MEETINGS THIS WEEK)",
            observed=str(dot_total),
            verdict="DATA", why="sum of dots in WEEK strip",
        )))
        if meetings_label:
            # Extract the number from "N MEETINGS THIS WEEK".
            m = re.search(r'(\d+)\s+MEETING', meetings_label, re.I)
            label_count = int(m.group(1)) if m else -1
            if label_count >= 0 and label_count != dot_total:
                report.defects.append(
                    f"ARRIVAL: WEEK strip total ({dot_total}) != "
                    f"N MEETINGS THIS WEEK label ({label_count}) -- "
                    f"D2 consistency: the strip and the label must agree"
                )
            report.facts.append(asdict(FaceFact(
                face=face, field="week_meetings_label",
                expected=f"{dot_total} MEETINGS THIS WEEK",
                observed=meetings_label,
                verdict="MATCH" if label_count == dot_total else "DATA",
                why="WEEK strip total label",
            )))

    # ARMED row.
    arming_text = arrival_data.get("armingText")
    if arming_text:
        report.facts.append(asdict(FaceFact(
            face=face, field="arming_row",
            expected="(ARMED <title> IN M:SS)",
            observed=arming_text[:40],
            verdict="DATA", why="ARMED countdown row on arrival",
        )))

    # Meeting rows.
    report.facts.append(asdict(FaceFact(
        face=face, field="meeting_row_count",
        expected="(varies)",
        observed=str(arrival_data.get("meetingCount", 0)),
        verdict="DATA", why="meeting rows on arrival",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="meeting_rows_with_room",
        expected="(varies, >0 when events are linked to Rooms)",
        observed=str(arrival_data.get("roomCount", 0)),
        verdict="DATA", why="meeting rows carrying ROOM token",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="meeting_rows_with_arms",
        expected="(varies, >0 when auto-record is on)",
        observed=str(arrival_data.get("armsCount", 0)),
        verdict="DATA", why="meeting rows carrying ARMS token",
    )))

    # A.7: duplicate armed rows.
    dups = arrival_data.get("duplicateTitles", [])
    if dups:
        report.defects.append(
            f"ARRIVAL: duplicate meeting rows (A.7) -- "
            f"same title+badge seen twice: {dups}"
        )

    # Defects.
    for z in arrival_data.get("zeroCounters", []):
        report.defects.append(
            f"ARRIVAL: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if arrival_data.get("hasLocal"):
        report.defects.append(
            "ARRIVAL: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if arrival_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"ARRIVAL: {arrival_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in arrival_data.get("clippedTexts", []):
        report.defects.append(f"ARRIVAL: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)


# ---------------------------------------------------------------------------
# Step 3: open Settings -> Meetings, shoot the calendar section
# ---------------------------------------------------------------------------

def _step_settings_meetings(page: Any, out_dir: Path, w: int, token: str,
                            report: WalkReport, door_state: dict) -> None:
    """Open Settings -> Meetings at the given width, shoot
    walk-settings-calendar-{w}.png.

    Records the CALENDAR rows (count, types ICS/SNAPSHOT, whether a host
    chip names a host or THIS DEVICE), the Auto-record value.
    """
    face = "settings-calendar"

    _open_surface(page, token, "open-settings", "meetings")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-settings-calendar", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the Settings Meetings face.
    # Real selectors from SettingsCore.tsx:
    #   data-testid="meetings-auto-display"  -- auto-run intelligence display
    #   data-testid="settings-no-model"      -- NO MODEL warning
    #   data-testid="settings-choose-model"  -- Choose model button
    #   data-testid="settings-last-ran"      -- LAST RAN receipt
    # The calendar sources are rendered by a GadgetTable inside a
    # GadgetRow with label="Sources" -- no unique data-testid on each
    # source row; we read .prefs-calendar-sources and its children.
    # TODO selectors (D2 elements not yet built):
    #   data-testid="settings-auto-record"   -- Auto-record CycleGadget
    settings_data = page.evaluate("""() => {
        const body = document.querySelector('.desk-surface-body') ||
                     document.querySelector('[data-testid="room-body"]') ||
                     document.body;
        const bodyText = body.textContent || '';

        /* Calendar sources: .prefs-calendar-sources inside the GadgetTable */
        const sourcesEl = body.querySelector('.prefs-calendar-sources');
        let sourceCount = 0;
        let icsCount = 0;
        let snapshotCount = 0;
        const sourceUrls = [];
        if (sourcesEl) {
            /* Each source is a row in the GadgetTable -- look for
               StringGadget inputs with value */
            const inputs = sourcesEl.querySelectorAll('input[type="text"]');
            for (const inp of inputs) {
                const val = inp.value || '';
                const placeholder = inp.placeholder || '';
                if (placeholder.toLowerCase().includes('ics') ||
                    placeholder.toLowerCase().includes('url')) {
                    if (val) {
                        sourceCount++;
                        sourceUrls.push(val.slice(0, 30));
                        if (/\\.ics/i.test(val) || /^https?:\\/\\//i.test(val)) {
                            icsCount++;
                        } else if (/snapshot/i.test(val)) {
                            snapshotCount++;
                        }
                    }
                }
            }
            /* Fallback: count rows by the checkbox gadget (the ON column) */
            if (sourceCount === 0) {
                const checkboxes = sourcesEl.querySelectorAll('.check-gadget');
                sourceCount = checkboxes.length;
            }
        }

        /* Egress chips (host identity): .prefs-calendar-egress */
        const egressArea = body.querySelector('.prefs-calendar-egress');
        const egressChips = [];
        if (egressArea) {
            const chips = egressArea.querySelectorAll('.gadget-chip-egress');
            for (const chip of chips) {
                egressChips.push(chip.textContent.trim().slice(0, 60));
            }
        }

        /* Auto-record: TODO data-testid="settings-auto-record" */
        const autoRecordEl = body.querySelector('[data-testid="settings-auto-record"]');
        let autoRecordValue = '--- (face not landed)';
        if (autoRecordEl) {
            autoRecordValue = autoRecordEl.textContent.trim();
        } else {
            /* Fallback: look for "Auto-record" or "Auto record" text
               then the adjacent CycleGadget */
            const allText = bodyText;
            if (/Auto.record/i.test(allText)) {
                const match = allText.match(/Auto.record[\\s\\S]{0,40}?(OFF|WITH URL|ALL)/i);
                if (match) autoRecordValue = match[1] + ' (inferred)';
                else autoRecordValue = 'present (value not parsed)';
            }
        }

        /* Defect scans */
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(SOURCE|CALENDAR|RECORDING)/gi;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const hasLocal = bodyText.includes('LOCAL');

        const clippedTexts = [];
        const primEls = body.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"]'
        );
        for (const el of primEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            sourceCount, icsCount, snapshotCount, sourceUrls,
            egressChips, autoRecordValue,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""")

    # Record facts.
    report.facts.append(asdict(FaceFact(
        face=face, field="calendar_source_count",
        expected="(>= 1 when calendar configured)",
        observed=str(settings_data.get("sourceCount", 0)),
        verdict="DATA", why="calendar source rows in Settings Meetings",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="ics_source_count",
        expected="(varies)",
        observed=str(settings_data.get("icsCount", 0)),
        verdict="DATA", why="ICS/HTTPS sources",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="snapshot_source_count",
        expected="(varies)",
        observed=str(settings_data.get("snapshotCount", 0)),
        verdict="DATA", why="SNAPSHOT sources",
    )))

    egress_chips = settings_data.get("egressChips", [])
    for i, chip in enumerate(egress_chips):
        has_host = bool(re.search(r'THIS DEVICE|LAN|CLOUD|[.][a-z]', chip, re.I))
        report.facts.append(asdict(FaceFact(
            face=face, field=f"egress_chip:{i}",
            expected="(FETCHES <name> . <host> . N MIN)",
            observed=chip[:60],
            verdict="MATCH" if has_host else "DATA",
            why="calendar source egress chip",
        )))

    report.facts.append(asdict(FaceFact(
        face=face, field="auto_record_value",
        expected="(OFF / WITH URL / ALL -- from Settings face)",
        observed=settings_data.get("autoRecordValue", "---"),
        verdict="DATA", why="Auto-record CycleGadget value on face",
    )))

    # Defects.
    for z in settings_data.get("zeroCounters", []):
        report.defects.append(
            f"SETTINGS CALENDAR: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if settings_data.get("hasLocal"):
        report.defects.append(
            "SETTINGS CALENDAR: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if settings_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"SETTINGS CALENDAR: {settings_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in settings_data.get("clippedTexts", []):
        report.defects.append(f"SETTINGS CALENDAR: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 4: open the first Room, shoot SOURCES
# ---------------------------------------------------------------------------

def _step_room_sources(page: Any, out_dir: Path, w: int, token: str,
                       report: WalkReport, door_state: dict) -> None:
    """Open the owner's first Room, shoot walk-room-sources-{w}.png.

    Records whether a MEETINGS source row exists and its tokens.
    """
    face = "room-sources"
    project_id = door_state.get("project_id")
    if not project_id:
        report.surprises.append("ROOM SOURCES: no project_id from step 1")
        return

    _open_surface(page, token, "open-project-memory", f"project:{project_id}")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-room-sources", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the Room SOURCES section.
    # Real selectors from ProjectRoomCore.tsx:
    #   The SOURCES section header starts with "SOURCES" text
    #   data-testid="source-scope"         -- scope text on each source row
    #   data-testid="suggested-source-row" -- suggested source rows
    #   data-testid="steward-verb"         -- Steward verb button
    # The source rows are SurfaceLedgerRow inside the SOURCES section.
    # The emblem (lead) identifies the provider (github, jira, confluence,
    # meetings).  The scope primary text names the Watch reference.
    # Tokens sit after the scope as .surface-token spans.
    room_data = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="room-body"]') ||
                     document.querySelector('.desk-surface-body');
        if (!body) return {
            sourcesSectionPresent: false, sourceRows: [],
            meetingsSourcePresent: false, meetingsSourceTokens: '',
            zeroCounters: [], rawBtnCount: 0, hasLocal: false,
            clippedTexts: [],
        };

        /* Find the SOURCES section by its label */
        const sections = body.querySelectorAll('.surface-section-head, h3');
        let sourcesSectionPresent = false;
        for (const s of sections) {
            const t = (s.textContent || '').trim();
            if (t.startsWith('SOURCES')) {
                sourcesSectionPresent = true;
                break;
            }
        }

        /* Source rows: look for SurfaceLedgerRow elements inside SOURCES
           Each row has a lead emblem and a primary scope.
           The emblem's alt/text or class tells the provider. */
        const sourceRowEls = body.querySelectorAll('[data-testid="source-scope"]');
        const sourceRows = [];
        for (const scopeEl of sourceRowEls) {
            const scope = scopeEl.textContent.trim();
            /* Walk up to the SurfaceLedgerRow to read tokens */
            const row = scopeEl.closest('.surface-ledger-row') ||
                        scopeEl.parentElement?.closest('li') ||
                        scopeEl.parentElement;
            const tokens = [];
            if (row) {
                const tokenEls = row.querySelectorAll('.surface-token');
                for (const tok of tokenEls) {
                    tokens.push(tok.textContent.trim());
                }
            }
            /* Check the emblem to identify the provider */
            let provider = 'unknown';
            if (row) {
                const emblem = row.querySelector('.surface-ledger-lead img, .surface-ledger-lead svg');
                if (emblem) {
                    const alt = emblem.getAttribute('alt') || '';
                    const src = emblem.getAttribute('src') || '';
                    if (/github/i.test(alt) || /github/i.test(src)) provider = 'github';
                    else if (/jira/i.test(alt) || /jira/i.test(src)) provider = 'jira';
                    else if (/confluence/i.test(alt) || /confluence/i.test(src)) provider = 'confluence';
                    else if (/meeting/i.test(alt) || /meeting/i.test(src) || /calendar/i.test(alt)) provider = 'meetings';
                }
                /* Fallback: check emblem text content */
                const leadEl = row.querySelector('.surface-ledger-lead');
                if (leadEl && provider === 'unknown') {
                    const lt = leadEl.textContent.trim().toUpperCase();
                    if (lt === 'MTG' || lt.includes('MEETING') || lt.includes('CAL')) provider = 'meetings';
                    else if (lt.includes('GH') || lt.includes('GITHUB')) provider = 'github';
                }
            }
            sourceRows.push({scope, tokens: tokens.join(' . '), provider});
        }

        /* Find a meetings source row specifically */
        let meetingsSourcePresent = false;
        let meetingsSourceTokens = '';
        for (const sr of sourceRows) {
            if (sr.provider === 'meetings') {
                meetingsSourcePresent = true;
                meetingsSourceTokens = sr.tokens;
                break;
            }
        }

        /* Defect scans */
        const bodyText = body.textContent || '';
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(SOURCE|WATCH|MEETING|DECISION|COMMITMENT|THING)/gi;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }
        const hasLocal = bodyText.includes('LOCAL');

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const clippedTexts = [];
        const primEls = body.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"], .surface-primary'
        );
        for (const el of primEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            sourcesSectionPresent, sourceRows,
            meetingsSourcePresent, meetingsSourceTokens,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""")

    # Record facts.
    report.facts.append(asdict(FaceFact(
        face=face, field="sources_section_present",
        expected="true",
        observed=str(room_data.get("sourcesSectionPresent", False)),
        verdict="MATCH" if room_data.get("sourcesSectionPresent") else "DATA",
        why="SOURCES section on Room face",
    )))
    source_rows = room_data.get("sourceRows", [])
    report.facts.append(asdict(FaceFact(
        face=face, field="source_row_count",
        expected="(varies)",
        observed=str(len(source_rows)),
        verdict="DATA", why="source rows in SOURCES section",
    )))
    for i, sr in enumerate(source_rows[:5]):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"source_row:{i}",
            expected="(provider . scope . tokens)",
            observed=f"{sr.get('provider', '?')} . {sr.get('scope', '?')[:20]} . {sr.get('tokens', '')[:40]}",
            verdict="DATA", why="source row content",
        )))

    report.facts.append(asdict(FaceFact(
        face=face, field="meetings_source_present",
        expected="(true when meeting Watch adapter is registered)",
        observed=str(room_data.get("meetingsSourcePresent", False)),
        verdict="DATA", why="MEETINGS source row in Room SOURCES",
    )))
    if room_data.get("meetingsSourcePresent"):
        report.facts.append(asdict(FaceFact(
            face=face, field="meetings_source_tokens",
            expected="(N THIS WEEK . NEXT [day] [time])",
            observed=room_data.get("meetingsSourceTokens", "---")[:60],
            verdict="DATA", why="MEETINGS source row tokens",
        )))

    # Defects.
    for z in room_data.get("zeroCounters", []):
        report.defects.append(
            f"ROOM SOURCES: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if room_data.get("hasLocal"):
        report.defects.append(
            "ROOM SOURCES: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if room_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"ROOM SOURCES: {room_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in room_data.get("clippedTexts", []):
        report.defects.append(f"ROOM SOURCES: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 5: open Rhythm, shoot the brief row
# ---------------------------------------------------------------------------

def _step_rhythm(page: Any, out_dir: Path, w: int, token: str,
                 report: WalkReport, door_state: dict) -> None:
    """Open Rhythm, shoot walk-rhythm-brief-{w}.png.

    Records the brief row's label (Monday brief vs Weekly brief), its
    tokens, and that Generate now is present but never pressed.
    """
    face = "rhythm-brief"

    _open_surface(page, token, "configure-cadence")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-rhythm-brief", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the Rhythm face.
    # Real selectors from CadenceCore.tsx:
    #   data-testid="rhythm-brief-row"      -- the brief row
    #   data-testid="rhythm-generate-now"    -- Generate now verb
    #   data-testid="rhythm-brief-facts"     -- facts below the brief row
    #   data-testid="rhythm-sweep-row"       -- sweep row
    #   data-testid="rhythm-run-now"         -- Run now verb
    #   data-testid="rhythm-runs-on-row"     -- Runs on row
    rhythm_data = page.evaluate("""() => {
        const body = document.querySelector('.desk-surface-body') ||
                     document.querySelector('[data-testid="room-body"]') ||
                     document.body;
        const bodyText = body.textContent || '';

        /* Brief row: data-testid="rhythm-brief-row" */
        const briefRow = body.querySelector('[data-testid="rhythm-brief-row"]');
        let briefLabel = '---';
        let briefTokens = '---';
        if (briefRow) {
            /* The primary text is the label (Monday brief or Weekly brief) */
            const primary = briefRow.querySelector('.surface-ledger-primary, .surface-primary');
            briefLabel = primary ? primary.textContent.trim() : briefRow.textContent.trim().split(/\\n/)[0];
            /* Tokens sit in the cells slot */
            const tokens = briefRow.querySelectorAll('.surface-token');
            const tokenTexts = [];
            for (const tok of tokens) {
                tokenTexts.push(tok.textContent.trim());
            }
            briefTokens = tokenTexts.join(' . ') || '---';
        }

        /* Generate now: data-testid="rhythm-generate-now" */
        const generateBtn = body.querySelector('[data-testid="rhythm-generate-now"]');
        const generatePresent = Boolean(generateBtn);
        const generateText = generateBtn ? generateBtn.textContent.trim() : '---';

        /* Run now: data-testid="rhythm-run-now" (must not be pressed) */
        const runNowBtn = body.querySelector('[data-testid="rhythm-run-now"]');
        const runNowPresent = Boolean(runNowBtn);

        /* Brief facts: data-testid="rhythm-brief-facts" */
        const briefFacts = body.querySelector('[data-testid="rhythm-brief-facts"]');
        let briefFactsText = '---';
        if (briefFacts) {
            briefFactsText = briefFacts.textContent.trim().slice(0, 80);
        }

        /* Defect scans */
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(BRIEF|SWEEP|MEETING|EVENT)/gi;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-disclosure-trigger') ||
                btn.classList.contains('gadget-transport-key') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.scroll-hint') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const hasLocal = bodyText.includes('LOCAL');

        const clippedTexts = [];
        const primEls = body.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"]'
        );
        for (const el of primEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            briefLabel, briefTokens,
            generatePresent, generateText,
            runNowPresent, briefFactsText,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""")

    # Record facts.
    brief_label = rhythm_data.get("briefLabel", "---")
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_row_label",
        expected="(Monday brief or Weekly brief)",
        observed=brief_label,
        verdict="DATA", why="brief row primary label in Rhythm",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_row_tokens",
        expected="(DAILY HH:MM token)",
        observed=rhythm_data.get("briefTokens", "---"),
        verdict="DATA", why="brief row tokens (cadence + time)",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="generate_now_present",
        expected="true",
        observed=str(rhythm_data.get("generatePresent", False)),
        verdict="MATCH" if rhythm_data.get("generatePresent") else "DATA",
        why="Generate now verb on brief row (present but never pressed)",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="generate_now_text",
        expected="Generate now",
        observed=rhythm_data.get("generateText", "---"),
        verdict=(
            "MATCH"
            if rhythm_data.get("generateText", "").strip().lower() == "generate now"
            else "DATA"
        ),
        why="Generate now verb label",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_facts",
        expected="(varies)",
        observed=rhythm_data.get("briefFactsText", "---")[:80],
        verdict="DATA", why="brief facts section below the row",
    )))

    # Defects.
    for z in rhythm_data.get("zeroCounters", []):
        report.defects.append(
            f"RHYTHM BRIEF: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if rhythm_data.get("hasLocal"):
        report.defects.append(
            "RHYTHM BRIEF: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if rhythm_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"RHYTHM BRIEF: {rhythm_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in rhythm_data.get("clippedTexts", []):
        report.defects.append(f"RHYTHM BRIEF: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 6: cross-step defect detection
# ---------------------------------------------------------------------------

def _detect_defects(report: WalkReport) -> None:
    """Cross-step defect detection applied after all steps complete."""
    seen: set[tuple[str, str]] = set()
    for fact in report.facts:
        key = (fact["face"], fact["field"])
        if key in seen:
            continue
        seen.add(key)
        obs = fact["observed"]

        # D1: zero counter (UX-CANON A.8).
        if re.search(
            r'\b0\s+(MEETING|EVENT|CALENDAR|RECORDING|SOURCE|WATCH|'
            r'BRIEF|SWEEP|DECISION|COMMITMENT|THING)',
            obs,
        ):
            report.defects.append(
                f"ZERO COUNTER on {fact['face']}/{fact['field']}: "
                f'"{obs}" -- UX-CANON A.8 forbids counters of zero'
            )

        # D2: raw <button>.
        # already handled per-step

        # D3: LOCAL instead of THIS DEVICE.
        if "local" in fact["field"].lower() and obs.lower() == "true":
            pass  # already handled per-step

        # D4: clipped text.
        # already handled per-step

        # D5: strip total != dots (arrival WEEK strip).
        # already handled in step 2

        # D6: duplicate armed row (A.7).
        # already handled in step 2

        # D7: host chip without scope.
        if "egress_chip" in fact["field"] and obs and obs != "---":
            has_scope = re.search(
                r'THIS DEVICE|LAN|CLOUD|MESH|PAIRED|FETCHES', obs, re.I,
            )
            if not has_scope:
                report.defects.append(
                    f"HOST WITHOUT SCOPE on {fact['face']}/"
                    f"{fact['field']}: \"{obs}\" -- missing scope word"
                )

    report.defects = list(dict.fromkeys(report.defects))


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def _write_facts_json(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n")
    return path


def _write_facts_md(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# HS-175-06 walk facts",
        "",
        f"Generated: {report.generated_at}",
        f"Hub: {report.hub_host}",
        "",
    ]
    faces: dict[str, list[dict]] = {}
    for fact in report.facts:
        face_name = fact["face"]
        if face_name not in faces:
            faces[face_name] = []
        faces[face_name].append(fact)

    for face_name, facts in faces.items():
        lines.append(f"## {face_name}")
        lines.append("")
        lines.append("| Field | Expected | Observed | Verdict | Why |")
        lines.append("|-------|----------|----------|---------|-----|")
        for f in facts:
            exp = f["expected"].replace("|", "\\|")
            obs = f["observed"].replace("|", "\\|")
            why = f["why"].replace("|", "\\|")
            lines.append(
                f"| {f['field']} | {exp} | {obs} | {f['verdict']} | {why} |"
            )
        lines.append("")

    if report.shots:
        lines.append("## Shots")
        lines.append("")
        for s in report.shots:
            lines.append(
                f"- {s['face']} @ {s['width']}: `{Path(s['path']).name}`"
            )
        lines.append("")

    if report.errors:
        lines.append("## Errors")
        lines.append("")
        for e in report.errors:
            lines.append(f"- {e}")
        lines.append("")

    if report.surprises:
        lines.append("## Surprises")
        lines.append("")
        for s in report.surprises:
            lines.append(f"- {s}")
        lines.append("")

    if report.defects:
        lines.append("## Defects")
        lines.append("")
        for i, d in enumerate(report.defects, 1):
            lines.append(f"{i}. {d}")
        lines.append("")
    else:
        lines.append("## Defects")
        lines.append("")
        lines.append("None.")
        lines.append("")

    path.write_text("\n".join(lines) + "\n")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="HS-175-06 walk runner")
    parser.add_argument("--hub", required=True, help="Hub URL with token")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Output directory for shots and facts")
    args = parser.parse_args()

    parsed = urlparse(args.hub)
    qs = parse_qs(parsed.query)
    token = qs.get("token", [""])[0]
    if not token:
        print("ERROR: --hub URL must include ?token=...")
        return 1
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = WalkReport(
        generated_at=datetime.now().isoformat(),
        hub_host=parsed.netloc,
        viewports=[{"width": v["width"], "height": v["height"]}
                   for v in VIEWPORTS],
    )
    errors_fatal: list[str] = []

    # Print the write guard's decision table.
    print("=== WRITE GUARD DECISION TABLE ===")
    for op in ("connect_calendar", "change_auto_record", "arm_recording",
               "cancel_recording", "link_event_room", "generate_brief",
               "run_now", "run_intel", "publish", "unknown"):
        allowed, reason = _write_allowed(op)
        print(f"  {op:25s} -> allowed={allowed}, reason={reason}")
    print("  ALL WRITES DENIED.  This walk is read-only.\n")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # API-only step (no viewport needed).
        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={token}", wait_until="load")
        page0.wait_for_timeout(2000)

        print("  [1/5] Door + settings (API)...")
        try:
            door_state = _step_door_api(page0, token, report)
            print(
                f"        done. calendar={door_state.get('calendar_configured')}, "
                f"upcoming={door_state.get('upcoming_count', '?')}, "
                f"auto_record={door_state.get('auto_record', '?')}"
            )
        except Exception as exc:
            door_state = {"calendar_configured": False}
            print(f"        FAILED: {exc}")
            report.errors.append(f"door-api: {exc}")

        page0.close()

        # Viewport loop.
        for vp in VIEWPORTS:
            w = vp["width"]
            h = vp["height"]
            print(f"\n=== Viewport {w}x{h} ===")

            page = browser.new_page(viewport={"width": w, "height": h})
            page.emulate_media(reduced_motion="reduce")
            page_errors: list[str] = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto(f"{base_url}/?token={token}", wait_until="load")
            if "React Web build is missing" in page.content():
                raise RuntimeError(
                    "HUB SERVES NO BUNDLE: the web build is missing; "
                    "every face step would be hollow"
                )
            page.wait_for_timeout(2000)
            try:
                chair = page.locator(".chair")
                if chair.count() > 0:
                    chair.wait_for(timeout=3000)
                    if chair.evaluate(
                        "el => el.classList.contains('chair-first-value')"
                    ):
                        btn = page.get_by_role(
                            "button", name="Continue later", exact=True,
                        )
                        if btn.count() > 0:
                            btn.click()
                            page.wait_for_timeout(500)
            except Exception:
                pass
            _settle(page)

            # Step 2: Arrival.
            print(f"  [2/5] Arrival @ {w}...")
            try:
                _step_arrival(page, out_dir, w, token, report, door_state)
                print("        done.")
            except Exception as exc:
                msg = f"arrival@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Step 3: Settings -> Meetings.
            print(f"  [3/5] Settings Meetings @ {w}...")
            try:
                _step_settings_meetings(
                    page, out_dir, w, token, report, door_state,
                )
                print("        done.")
            except Exception as exc:
                msg = f"settings-meetings@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 4: Room SOURCES.
            print(f"  [4/5] Room SOURCES @ {w}...")
            try:
                _step_room_sources(
                    page, out_dir, w, token, report, door_state,
                )
                print("        done.")
            except Exception as exc:
                msg = f"room-sources@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 5: Rhythm.
            print(f"  [5/5] Rhythm @ {w}...")
            try:
                _step_rhythm(page, out_dir, w, token, report, door_state)
                print("        done.")
            except Exception as exc:
                msg = f"rhythm@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            critical = [e for e in page_errors if "ResizeObserver" not in e]
            if critical:
                report.errors.extend([f"JS@{w}: {e}" for e in critical])

            page.close()

        browser.close()

    _detect_defects(report)

    json_path = _write_facts_json(report, out_dir)
    md_path = _write_facts_md(report, out_dir)

    print(f"\n=== WALK 175 COMPLETE ===")
    print(f"  Facts JSON: {json_path}")
    print(f"  Facts MD:   {md_path}")
    print(f"  Shots:      {len(report.shots)}")
    print(f"  Errors:     {len(report.errors)}")
    print(f"  Surprises:  {len(report.surprises)}")
    print(f"  Defects:    {len(report.defects)}")
    if report.defects:
        for d in report.defects:
            print(f"    - {d}")

    if errors_fatal:
        print("\nFATAL ERRORS:")
        for e in errors_fatal:
            print(f"  - {e}")
        return 1

    bounces = [f for f in report.facts if f["verdict"] == "BOUNCE"]
    if bounces:
        print(f"\nBOUNCE verdicts ({len(bounces)}):")
        for b in bounces:
            print(f"  - {b['face']}/{b['field']}: {b['why']}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
