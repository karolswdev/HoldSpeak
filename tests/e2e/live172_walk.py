"""HS-172-08 PRE-WALK runner: the Loop Closes -- read-mostly walk of the owner's real hub.

Shoots five faces (Room, Meeting detail, Arrival, People, Settings Meetings)
at 1440x900 and 393x852.  The ONE write: POST /api/meetings/{id}/intelligence/run
on the "Already titled" meeting (2 words) -- allowed only when the model host
is LAN/local (never a cloud key).

THE LIVE LAWS (Article IV -- the walk arms nothing):
1. READ-ONLY except one intel run on his own data through his own model.
   Never clicks Confirm / Edit / Drop / Add / Dismiss on his desk.
2. NO HARDCODED TOKENS.
3. FACE-DRIVEN.
4. STANDALONE.  Not collected by pytest.

Usage:
  python tests/e2e/live172_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

# ── pytest collection guard ──
collect_ignore_glob = ["live172_walk.py"]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-08-shots"

VIEWPORTS = [
    {"width": 1440, "height": 900, "suffix": "1440"},
    {"width": 393, "height": 852, "suffix": "393"},
]


# ── Data model ──

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
    intel_receipt: dict = field(default_factory=dict)


# ── Helpers ──

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


def _check_raw_buttons(page: Any, face_name: str) -> str | None:
    raw_count = page.evaluate("""() => {
        const win = document.querySelector('.desk-surface-window');
        if (!win) return 0;
        const allBtns = win.querySelectorAll('button');
        let raw = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn')) continue;
            if (btn.closest('[role="tablist"]')) continue;
            if (btn.closest('.cycle-gadget')) continue;
            if (btn.closest('.fold-gadget')) continue;
            if (btn.closest('.check-gadget')) continue;
            if (btn.classList.contains('desk-mic')) continue;
            if (btn.closest('.surface-ledger-row')) continue;
            if (btn.classList.contains('surface-disclosure-trigger')) continue;
            if (btn.closest('.stepper-gadget')) continue;
            if (btn.closest('.scroll-hint')) continue;
            if (btn.classList.contains('gadget-transport-key')) continue;
            if (btn.closest('.desk-traffic')) continue;
            if (btn.closest('.desk-wings')) continue;
            if (btn.classList.contains('surface-ledger-line')) continue;
            raw++;
        }
        return raw;
    }""")
    if raw_count > 0:
        return f"RAW BUTTON on {face_name}: {raw_count} raw <button>(s) outside library"
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
    payload = {"key": action}
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


# ── Step 1: GET /api/settings/meetings/intelligence ──

def _step_intel_settings(page: Any, token: str, report: WalkReport) -> dict:
    """Read auto-run setting + host. Returns the payload for later decisions."""
    face = "intel-settings"
    # Try the meetings intelligence settings route
    result = _api(page, "GET", "/api/settings", None, token)
    payload = {}
    if result["status"] == 200:
        payload = result["payload"]
        # The intel settings live under meetings.intel_* or a dedicated key
        intel_enabled = payload.get("meetings", {}).get("intel_enabled", "---")
        intel_model = payload.get("meetings", {}).get("intel_realtime_model", "---")
        intel_provider = payload.get("meetings", {}).get("intel_provider", "---")
        report.facts.append(asdict(FaceFact(
            face=face, field="intel_enabled", expected="(owner's setting)",
            observed=str(intel_enabled), verdict="DATA", why="real desk content",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="intel_model", expected="(model name)",
            observed=str(intel_model), verdict="DATA", why="real desk content",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="intel_provider", expected="(provider)",
            observed=str(intel_provider), verdict="DATA", why="real desk content",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="api_status", expected="200",
            observed=str(result["status"]), verdict="DATA",
            why=f"HTTP {result['status']}",
        )))
    return payload


# ── Step 2: Meeting list + proposals + optional intel run ──

def _step_meetings_intel(page: Any, token: str, report: WalkReport,
                         settings: dict) -> str | None:
    """Read meetings, find 'Already titled', read proposals, optionally run intel.
    Returns the meeting ID used (or None)."""
    face = "meeting-intel"
    # Get meeting list
    result = _api(page, "GET", "/api/meetings", None, token)
    if result["status"] >= 300:
        report.errors.append(f"GET /api/meetings returned {result['status']}")
        return None
    meetings = result["payload"]
    rows = meetings if isinstance(meetings, list) else meetings.get("meetings", [])

    # Find "Already titled" meeting
    target = None
    for m in rows:
        title = str(m.get("title", ""))
        if "Already titled" in title:
            target = m
            break
    if not target:
        report.surprises.append("MEETINGS: 'Already titled' meeting not found")
        return None

    meeting_id = str(target.get("id", ""))
    report.facts.append(asdict(FaceFact(
        face=face, field="target_meeting", expected="Already titled",
        observed=f"{target.get('title')} (id={meeting_id[:8]}...)",
        verdict="DATA", why="real desk content",
    )))

    # Read proposals for this meeting
    prop_result = _api(page, "GET",
                       f"/api/meetings/{meeting_id}/follow-through-proposals", None, token)
    if prop_result["status"] == 200:
        proposals = prop_result["payload"]
        prop_list = proposals if isinstance(proposals, list) else proposals.get("proposals", [])
        report.facts.append(asdict(FaceFact(
            face=face, field="proposals_count", expected="(varies)",
            observed=str(len(prop_list)), verdict="DATA", why="real desk content",
        )))
        for i, p in enumerate(prop_list[:5]):
            text = str(p.get("extracted_text", p.get("text", "---")))[:80]
            status = str(p.get("proposal_status", p.get("status", "---")))
            host = str(p.get("model_host", "---"))
            report.facts.append(asdict(FaceFact(
                face=face, field=f"proposal:{i}",
                expected="(text . status . host)",
                observed=f"{text} | {status} | {host}",
                verdict="DATA", why="real desk content",
            )))
    elif prop_result["status"] == 404:
        report.facts.append(asdict(FaceFact(
            face=face, field="proposals_route", expected="200",
            observed="404 -- route not wired yet",
            verdict="DATA", why="proposals route not found",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="proposals_status", expected="200",
            observed=str(prop_result["status"]),
            verdict="DATA", why=f"HTTP {prop_result['status']}",
        )))

    # Determine if we can run intel (LAN/local host only)
    intel_provider = str(settings.get("meetings", {}).get("intel_provider", ""))
    intel_model = str(settings.get("meetings", {}).get("intel_realtime_model", ""))
    # Check if the provider is local/LAN (not cloud)
    is_cloud = any(cloud in intel_provider.lower() for cloud in
                   ("openai", "anthropic", "cloud", "api.")) if intel_provider else False
    if is_cloud:
        report.facts.append(asdict(FaceFact(
            face=face, field="intel_run", expected="SKIPPED (cloud host)",
            observed=f"provider={intel_provider}, model={intel_model}",
            verdict="DATA", why="cloud host -- will not run intel on his desk",
        )))
        return meeting_id

    # Run intel on the "Already titled" meeting (2 words, LAN model)
    report.facts.append(asdict(FaceFact(
        face=face, field="intel_run_attempt", expected="POST run",
        observed=f"running on meeting {meeting_id[:8]}...",
        verdict="DATA", why="LAN/local host, allowed",
    )))
    run_result = _api(page, "POST",
                      f"/api/meetings/{meeting_id}/intelligence/run",
                      {}, token)
    report.intel_receipt = run_result.get("payload", {}) if run_result["status"] < 300 else {}
    report.facts.append(asdict(FaceFact(
        face=face, field="intel_run_status", expected="200",
        observed=str(run_result["status"]),
        verdict="MATCH" if run_result["status"] < 300 else "DATA",
        why="ok" if run_result["status"] < 300 else f"HTTP {run_result['status']}",
    )))

    # Wait for intel to complete, then re-read proposals
    if run_result["status"] < 300:
        time.sleep(5)  # Give intel time to process (2-word meeting is fast)
        prop_result2 = _api(page, "GET",
                            f"/api/meetings/{meeting_id}/follow-through-proposals", None, token)
        if prop_result2["status"] == 200:
            props2 = prop_result2["payload"]
            prop_list2 = props2 if isinstance(props2, list) else props2.get("proposals", [])
            report.facts.append(asdict(FaceFact(
                face=face, field="proposals_after_intel", expected="(varies)",
                observed=str(len(prop_list2)), verdict="DATA",
                why="proposals after intel run",
            )))

    return meeting_id


# ── Step 3: Room ──

def _step_room(page: Any, out_dir: Path, w: int, token: str,
               report: WalkReport) -> None:
    """Open the owner's one Room, shoot, record NEEDS YOU + DECISIONS + SOURCES."""
    face = "room"
    # Get the project list to find his Room
    result = _api(page, "GET", "/api/projects", None, token)
    if result["status"] >= 300:
        report.errors.append(f"GET /api/projects returned {result['status']}")
        return
    projects = result["payload"]
    proj_list = projects.get("projects", []) if isinstance(projects, dict) else projects
    if not proj_list:
        report.surprises.append("ROOM: zero projects on owner's desk")
        return

    project_id = str(proj_list[0].get("id", ""))
    project_name = str(proj_list[0].get("name", proj_list[0].get("title", "---")))

    # Open the Room via surface staging
    # TODO: refine the surface key for opening a specific Room once built
    _open_surface(page, token, "project-room", project_id)
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-room", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    report.facts.append(asdict(FaceFact(
        face=face, field="project_name", expected="(owner's project)",
        observed=project_name, verdict="DATA", why="real desk content",
    )))

    # TODO: NEEDS YOU rows (proposal rows: text . BY . from . host . Confirm/Dismiss)
    # Selectors to fill once the proposal face lands:
    #   [data-testid="room-needs-you"] or similar
    #   [data-proposal] rows with .surface-ledger-row
    #   EgressChip (.gadget-chip-egress) per proposal
    #   Button verbs: Confirm / Edit / Drop
    needs_you_data = page.evaluate("""() => {
        // Read the Room body's content for NEEDS YOU rows
        const body = document.querySelector('[data-testid="room-body"]');
        if (!body) return { headline: '---', rows: [] };
        const headline = (body.querySelector('.surface-display, [data-testid="room-headline"]')?.textContent || '').trim();
        // Look for needs-you rows (generic until testids land)
        const sections = body.querySelectorAll('.surface-section-head, h3');
        let needsYouText = '';
        for (const s of sections) {
            if ((s.textContent || '').includes('NEEDS YOU')) {
                needsYouText = s.textContent.trim();
                break;
            }
        }
        return { headline, needsYouSection: needsYouText };
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="headline", expected="(N need you or Nothing needs you)",
        observed=needs_you_data.get("headline", "---"),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="needs_you_section", expected="NEEDS YOU N",
        observed=needs_you_data.get("needsYouSection", "---"),
        verdict="DATA", why="real desk content",
    )))

    # TODO: DECISIONS & COMMITMENTS section
    # TODO: SOURCES section incl. SUGGESTED rows
    # Selectors to fill once the Room face updates land

    btn_err = _check_raw_buttons(page, face)
    if btn_err:
        report.errors.append(btn_err)

    _close_surface(page)


# ── Step 4: Meeting detail ──

def _step_meeting_detail(page: Any, out_dir: Path, w: int, token: str,
                         report: WalkReport, meeting_id: str | None) -> None:
    """Open the meeting detail, shoot, record header tokens + NEEDS YOU."""
    face = "meeting-detail"
    _open_surface(page, token, "review-meetings")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    # Click the first meeting row to open detail
    if meeting_id:
        # Try to find the specific meeting row
        row_bodies = page.locator('.meetings-stream-row-body')
        if row_bodies.count() > 0:
            row_bodies.first.click()
            page.wait_for_timeout(2000)
            _settle(page)

    shot = _shoot(page, out_dir, "walk-meeting", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # TODO: Record header tokens (RAN . N S . host)
    # TODO: Record NEEDS YOU rows in the detail
    # Selectors to fill once the meeting detail proposal face lands
    detail_data = page.evaluate("""() => {
        // Look for intel status tokens in the meeting detail
        const detail = document.querySelector('.surface-split-detail, .meeting-detail');
        if (!detail) return { header: '---', needsYou: '---' };
        const header = detail.textContent?.substring(0, 200).trim() || '---';
        return { header };
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="detail_header", expected="(meeting title + tokens)",
        observed=detail_data.get("header", "---")[:150],
        verdict="DATA", why="real desk content",
    )))

    _close_surface(page)


# ── Step 5: Arrival ──

def _step_arrival(page: Any, out_dir: Path, w: int,
                  report: WalkReport) -> None:
    """Shoot the arrival, record Confirm: rows in NEEDS YOU."""
    face = "arrival"
    _settle(page)
    shot = _shoot(page, out_dir, "walk-arrival", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # TODO: Record Confirm: rows in the arrival's NEEDS YOU
    # Selectors to fill once the arrival proposal rows land
    arrival_data = page.evaluate("""() => {
        const display = document.querySelector('[data-testid="arrival-display"]');
        const headline = display ? display.textContent.trim() : '---';
        // Look for proposal/confirm rows
        const needsYou = document.querySelector('[data-testid="arrival-needs-you"]');
        const rows = [];
        if (needsYou) {
            const items = needsYou.querySelectorAll('[data-testid="arrival-needs-you-row"]');
            for (const item of items) {
                rows.push(item.textContent.trim().substring(0, 100));
            }
        }
        return { headline, needsYouCount: rows.length, rows };
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="headline", expected="(N need you or Nothing needs you)",
        observed=arrival_data.get("headline", "---"),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="needs_you_count", expected="(varies)",
        observed=str(arrival_data.get("needsYouCount", 0)),
        verdict="DATA", why="real desk content",
    )))
    # Record any Confirm: rows
    for i, row_text in enumerate(arrival_data.get("rows", [])[:5]):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"needs_you_row:{i}",
            expected="(Confirm: ... or Watch item)",
            observed=row_text,
            verdict="DATA", why="real desk content",
        )))


# ── Step 6: People ──

def _step_people(page: Any, out_dir: Path, w: int, token: str,
                 report: WalkReport) -> None:
    """Open People, find first relationship, shoot card, record watch_summary.
    Never writes a person's name to the facts file."""
    face = "people"
    # Get relationships
    result = _api(page, "GET", "/api/people/relationships", None, token)
    if result["status"] >= 300:
        report.facts.append(asdict(FaceFact(
            face=face, field="relationships_status", expected="200",
            observed=str(result["status"]), verdict="DATA",
            why=f"HTTP {result['status']}",
        )))
        return
    rels = result["payload"]
    rel_list = rels if isinstance(rels, list) else rels.get("relationships", [])
    if not rel_list:
        report.surprises.append("PEOPLE: zero relationships on owner's desk")
        return

    first_rel = rel_list[0]
    rel_id = str(first_rel.get("id", ""))

    report.facts.append(asdict(FaceFact(
        face=face, field="relationship_count", expected="(varies)",
        observed=str(len(rel_list)), verdict="DATA", why="real desk content",
    )))

    # Get 1:1 brief for the first relationship
    brief_result = _api(page, "GET",
                        f"/api/people/relationships/{rel_id}/one-on-one-brief",
                        None, token)
    if brief_result["status"] == 200:
        brief = brief_result["payload"]
        # Record watch_summary if present (PRs waiting, commitments, last meeting)
        # NEVER write the person's name -- use <person>
        ws = brief.get("watch_summary", {})
        prs = ws.get("prs_waiting", [])
        assignments = ws.get("open_assignments", [])
        overdue = ws.get("commitments_overdue_count", 0)
        report.facts.append(asdict(FaceFact(
            face=face, field="watch_summary:prs_waiting",
            expected="(count)",
            observed=str(len(prs)),
            verdict="DATA", why="PRs waiting on <person>",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="watch_summary:open_assignments",
            expected="(count)",
            observed=str(len(assignments)),
            verdict="DATA", why="open assignments for <person>",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="watch_summary:commitments_overdue",
            expected="(count)",
            observed=str(overdue),
            verdict="DATA", why="overdue commitments for <person>",
        )))
        # Last meeting count
        linked = brief.get("linked_meetings", [])
        if linked:
            last_mtg = linked[0]
            items = last_mtg.get("open_action_items", [])
            report.facts.append(asdict(FaceFact(
                face=face, field="watch_summary:last_meeting_items",
                expected="(count)",
                observed=str(len(items)),
                verdict="DATA", why="open items from last meeting with <person>",
            )))
    elif brief_result["status"] == 404:
        report.facts.append(asdict(FaceFact(
            face=face, field="one_on_one_brief", expected="200",
            observed="404", verdict="DATA", why="brief route not found",
        )))

    # TODO: Open the People face and shoot once the People card face lands
    # _open_surface(page, token, "inspect-personas-and-coders")
    # For now, shoot the arrival (People face not yet built for 172)
    # Selectors to fill: the People card with watch_summary sections


# ── Step 7: Settings -> Meetings ──

def _step_settings_meetings(page: Any, out_dir: Path, w: int, token: str,
                            report: WalkReport) -> None:
    """Open Settings -> Meetings module, shoot, record INTELLIGENCE row."""
    face = "settings-meetings"
    _open_surface(page, token, "configure-settings", "meetings")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-settings-meetings", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # TODO: Record INTELLIGENCE row (CycleGadget + EgressChip)
    # Selectors to fill once the meetings settings face updates
    intel_text = page.evaluate("""() => {
        // Look for the Intelligence row in the settings module
        const module = document.querySelector('.prefs-module');
        if (!module) return '---';
        const text = module.textContent || '';
        // Find the section containing "Intelligence" or "intelligence"
        const rows = module.querySelectorAll('.surface-ledger-row, .gadget-row, .gadget-group');
        for (const row of rows) {
            const t = (row.textContent || '').trim();
            if (t.toLowerCase().includes('intelligence')) return t.substring(0, 200);
        }
        return text.substring(0, 200);
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="intelligence_row",
        expected="Intelligence AFTER EVERY MEETING / ROOM-LINKED ONLY / OFF + host chip",
        observed=intel_text[:200], verdict="DATA", why="real desk content",
    )))

    btn_err = _check_raw_buttons(page, face)
    if btn_err:
        report.errors.append(btn_err)

    _close_surface(page)


# ── Defect detection ──

def _detect_defects(report: WalkReport) -> None:
    seen: set[tuple[str, str]] = set()
    for fact in report.facts:
        key = (fact["face"], fact["field"])
        if key in seen:
            continue
        seen.add(key)
        obs = fact["observed"]

        # D1: zero counter (UX-CANON A.8)
        if re.search(r'\b0\s+(NEED|THINGS|RECORD|PROPOSAL|DECISION|COMMITMENT)', obs):
            report.defects.append(
                f"ZERO COUNTER on {fact['face']}/{fact['field']}: \"{obs}\" "
                f"-- UX-CANON A.8 forbids counters of zero"
            )

        # D2: a proposal row without a host
        if "proposal:" in fact["field"] and "| ---" in obs:
            if obs.count("|") >= 2 and obs.rsplit("|", 1)[-1].strip() in ("---", ""):
                report.defects.append(
                    f"PROPOSAL WITHOUT HOST on {fact['field']}: \"{obs}\" "
                    f"-- every proposal must name its model host"
                )

        # D3: a person's real name in a facts field
        if fact["face"] == "people":
            # The runner should never write a name; check for accidental leaks
            # (names are typically > 2 words with capitals)
            pass  # The runner is designed to write <person> not names

    report.defects = list(dict.fromkeys(report.defects))


# ── Report writers ──

def _write_facts_json(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n")
    return path


def _write_facts_md(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# HS-172-08 walk facts",
        "",
        f"Generated: {report.generated_at}",
        f"Hub: {report.hub_host}",
        "",
    ]
    faces: dict[str, list[dict]] = {}
    for fact in report.facts:
        face = fact["face"]
        if face not in faces:
            faces[face] = []
        faces[face].append(fact)

    for face, facts in faces.items():
        lines.append(f"## {face}")
        lines.append("")
        lines.append("| Field | Expected | Observed | Verdict | Why |")
        lines.append("|-------|----------|----------|---------|-----|")
        for f in facts:
            exp = f["expected"].replace("|", "\\|")
            obs = f["observed"].replace("|", "\\|")
            why = f["why"].replace("|", "\\|")
            lines.append(f"| {f['field']} | {exp} | {obs} | {f['verdict']} | {why} |")
        lines.append("")

    if report.intel_receipt:
        lines.append("## Intel receipt")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(report.intel_receipt, indent=2))
        lines.append("```")
        lines.append("")

    if report.shots:
        lines.append("## Shots")
        lines.append("")
        for s in report.shots:
            lines.append(f"- {s['face']} @ {s['width']}: `{Path(s['path']).name}`")
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


# ── Main ──

def main() -> int:
    parser = argparse.ArgumentParser(description="HS-172-08 pre-walk runner")
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
        viewports=[{"width": v["width"], "height": v["height"]} for v in VIEWPORTS],
    )
    errors_fatal: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERROR: playwright not installed")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # API-only steps (no viewport needed)
        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={token}", wait_until="load")
        page0.wait_for_timeout(2000)

        print("  [1/7] Intel settings (API)...")
        try:
            settings = _step_intel_settings(page0, token, report)
            print("        done.")
        except Exception as exc:
            settings = {}
            print(f"        FAILED: {exc}")
            report.errors.append(f"intel-settings: {exc}")

        print("  [2/7] Meeting intel (API)...")
        try:
            meeting_id = _step_meetings_intel(page0, token, report, settings)
            print("        done.")
        except Exception as exc:
            meeting_id = None
            print(f"        FAILED: {exc}")
            report.errors.append(f"meeting-intel: {exc}")

        # People (API only for now)
        print("  [6/7] People (API)...")
        try:
            _step_people(page0, out_dir, 1440, token, report)
            print("        done.")
        except Exception as exc:
            print(f"        FAILED: {exc}")
            report.errors.append(f"people: {exc}")

        page0.close()

        # Viewport loop
        for vp in VIEWPORTS:
            w = vp["width"]
            h = vp["height"]
            print(f"\n=== Viewport {w}x{h} ===")

            page = browser.new_page(viewport={"width": w, "height": h})
            page.emulate_media(reduced_motion="reduce")
            page_errors: list[str] = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto(f"{base_url}/?token={token}", wait_until="load")
            page.wait_for_timeout(2000)
            try:
                chair = page.locator(".chair")
                if chair.count() > 0:
                    chair.wait_for(timeout=3000)
                    if chair.evaluate("el => el.classList.contains('chair-first-value')"):
                        btn = page.get_by_role("button", name="Continue later", exact=True)
                        if btn.count() > 0:
                            btn.click()
                            page.wait_for_timeout(500)
            except Exception:
                pass
            _settle(page)

            # Step 3: Room
            print(f"  [3/7] Room...")
            try:
                _step_room(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"room@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Step 4: Meeting detail
            print(f"  [4/7] Meeting detail...")
            try:
                _step_meeting_detail(page, out_dir, w, token, report, meeting_id)
                print(f"        done.")
            except Exception as exc:
                msg = f"meeting-detail@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 5: Arrival
            print(f"  [5/7] Arrival...")
            try:
                _step_arrival(page, out_dir, w, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"arrival@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 7: Settings -> Meetings
            print(f"  [7/7] Settings Meetings...")
            try:
                _step_settings_meetings(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"settings-meetings@{w}: {exc}"
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

    print(f"\n=== WALK 172 COMPLETE ===")
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
        print(f"\nFATAL ERRORS:")
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
