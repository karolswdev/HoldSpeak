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

# -- pytest collection guard --
collect_ignore_glob = ["live172_walk.py"]


# -- Intel run guard --

_LAN_RE = re.compile(
    r"^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)"
)


def _run_allowed(host: str | None) -> tuple[bool, str]:
    """Decide whether POST /api/meetings/{id}/intelligence/run is allowed.

    Returns (allowed: bool, reason: str).

    ALLOWED only when *host* is a private-network IP or the literal
    ``local`` / ``this_device`` / ``THIS DEVICE``.  Every other value
    -- empty, None, a cloud provider name, a profile label, an unknown
    string -- is DENIED.

    Cases:
        _run_allowed(None)                   -> (False, "no host")
        _run_allowed("")                     -> (False, "empty host")
        _run_allowed("192.168.1.43")         -> (True,  "LAN")
        _run_allowed("10.0.0.5")             -> (True,  "LAN")
        _run_allowed("172.16.0.1")           -> (True,  "LAN")
        _run_allowed("172.32.0.1")           -> (False, "not LAN: 172.32.0.1")
        _run_allowed("local")               -> (True,  "local")
        _run_allowed("this_device")          -> (True,  "local")
        _run_allowed("THIS DEVICE")          -> (True,  "local")
        _run_allowed("Migrated intel endpoint") -> (False, "not LAN: Migrated intel endpoint")
        _run_allowed("openai")              -> (False, "not LAN: openai")
        _run_allowed("api.openai.com")      -> (False, "not LAN: api.openai.com")
        _run_allowed("anthropic")           -> (False, "not LAN: anthropic")
        _run_allowed("external_service")    -> (False, "not LAN: external_service")
    """
    if not host:
        return False, "no host" if host is None else "empty host"
    h = host.strip()
    if not h:
        return False, "empty host"
    if h.lower() in ("local", "this_device", "this device"):
        return True, "local"
    if _LAN_RE.match(h):
        return True, "LAN"
    return False, f"not LAN: {h}"

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-08-shots"

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
    intel_receipt: dict = field(default_factory=dict)


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


# -- Step 1: read intel settings from GET /api/settings/hub + GET /api/settings --

def _step_intel_settings(page: Any, token: str, report: WalkReport) -> dict:
    """Read auto-run setting + host from the hub wire and raw settings.

    Returns a dict with keys the later steps need:
      hub_meetings_host  -- the resolved model host from /api/settings/hub
      intelligence_auto   -- "room_linked" | "every" | "off"
      intel_profile_id    -- the raw profile id from /api/settings
    """
    face = "intel-settings"
    out: dict[str, Any] = {}

    # 1a. GET /api/settings/hub -- the seven-module summary
    hub_result = _api(page, "GET", "/api/settings/hub", None, token)
    if hub_result["status"] == 200:
        hub = hub_result["payload"]
        meetings_hub = hub.get("meetings", {}) if isinstance(hub, dict) else {}
        host = meetings_hub.get("host") or None
        auto = meetings_hub.get("auto", "---")
        intelligence = meetings_hub.get("intelligence", "---")
        out["hub_meetings_host"] = host
        out["intelligence_auto"] = auto

        report.facts.append(asdict(FaceFact(
            face=face, field="hub_meetings_host", expected="(resolved model host or null)",
            observed=str(host) if host else "(null)",
            verdict="DATA", why="from GET /api/settings/hub",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="hub_meetings_auto", expected="room_linked / every / off",
            observed=str(auto), verdict="DATA", why="from GET /api/settings/hub",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="hub_meetings_intelligence", expected="true / false",
            observed=str(intelligence), verdict="DATA", why="from GET /api/settings/hub",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="hub_api_status", expected="200",
            observed=str(hub_result["status"]), verdict="DATA",
            why=f"GET /api/settings/hub returned HTTP {hub_result['status']}",
        )))

    # 1b. GET /api/settings -- the raw settings (for the profile id)
    settings_result = _api(page, "GET", "/api/settings", None, token)
    if settings_result["status"] == 200:
        settings = settings_result["payload"]
        meeting_block = settings.get("meeting", {}) if isinstance(settings, dict) else {}
        profile_id = meeting_block.get("intel_profile_id", "---")
        auto_raw = meeting_block.get("intelligence_auto", "---")
        out["intel_profile_id"] = profile_id

        report.facts.append(asdict(FaceFact(
            face=face, field="raw_intel_profile_id", expected="(profile id or empty)",
            observed=str(profile_id) if profile_id else "(empty)",
            verdict="DATA", why="from GET /api/settings -> meeting.intel_profile_id",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="raw_intelligence_auto", expected="room_linked / every / off",
            observed=str(auto_raw), verdict="DATA",
            why="from GET /api/settings -> meeting.intelligence_auto",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="settings_api_status", expected="200",
            observed=str(settings_result["status"]), verdict="DATA",
            why=f"GET /api/settings returned HTTP {settings_result['status']}",
        )))

    return out


# -- Step 2: Meeting list + proposals + optional intel run --

def _step_meetings_intel(page: Any, token: str, report: WalkReport,
                         settings: dict) -> str | None:
    """Read meetings, find 'Already titled', read proposals, optionally run intel.

    The intel run is guarded by THREE conditions -- ALL must be true:
      1. hub_meetings_host passes _run_allowed (private LAN or local)
      2. The target meeting's intel_status is NOT already complete/running/queued
      3. _run_allowed returned True

    Returns the meeting ID used (or None)."""
    face = "meeting-intel"
    result = _api(page, "GET", "/api/meetings", None, token)
    if result["status"] >= 300:
        report.errors.append(f"GET /api/meetings returned {result['status']}")
        return None
    meetings = result["payload"]
    rows = meetings if isinstance(meetings, list) else meetings.get("meetings", [])

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

    # ---- Intel run guard (three conditions) ----

    # Condition 1: host must be private LAN or local
    hub_host = settings.get("hub_meetings_host")
    allowed, reason = _run_allowed(hub_host)

    if not allowed:
        report.facts.append(asdict(FaceFact(
            face=face, field="intel_run", expected="SKIPPED",
            observed=f"SKIPPED: {reason} (host={hub_host})",
            verdict="DATA", why=f"host guard denied: {reason}",
        )))
        return meeting_id

    # Condition 2: meeting must not already have intel complete/running/queued
    intel_status = str(target.get("intel_status", "disabled")).lower().strip()
    if intel_status in ("complete", "running", "queued", "importing"):
        report.facts.append(asdict(FaceFact(
            face=face, field="intel_run", expected="SKIPPED",
            observed=f"SKIPPED: meeting already {intel_status}",
            verdict="DATA", why=f"intel_status={intel_status}, no re-run needed",
        )))
        return meeting_id

    # All guards passed -- fire the one allowed write
    report.facts.append(asdict(FaceFact(
        face=face, field="intel_run_attempt", expected="POST run",
        observed=f"running on meeting {meeting_id[:8]}... (host={hub_host}, guard={reason})",
        verdict="DATA", why=f"LAN/local host ({reason}), intel_status={intel_status}",
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

    if run_result["status"] < 300:
        time.sleep(5)
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


# -- Step 3: Room --

def _step_room(page: Any, out_dir: Path, w: int, token: str,
               report: WalkReport) -> None:
    """Open the owner's one Room, shoot, record NEEDS YOU + DECISIONS + SOURCES + PEOPLE."""
    face = "room"
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

    _open_surface(page, token, "open-project-memory", f"project:{project_id}")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-room", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    report.facts.append(asdict(FaceFact(
        face=face, field="project_name", expected="(owner's project)",
        observed=project_name, verdict="DATA", why="real desk content",
    )))

    # Read face via real selectors from ProjectRoomCore.tsx
    room_data = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="room-body"]');
        if (!body) return { headline: '---', proposalRows: 0, decisionRows: 0,
            suggestedRows: 0, peopleRows: 0, sourceRows: 0, needsYouRows: 0 };

        // Headline: data-testid="room-headline"
        const hl = body.querySelector('[data-testid="room-headline"]');
        const headline = hl ? hl.textContent.trim() : '---';

        // Proposal rows: data-testid="proposal-row"
        const propRows = body.querySelectorAll('[data-testid="proposal-row"]');
        // Check each proposal row for MTG emblem and clipped primary
        const proposalDefects = [];
        for (const row of propRows) {
            const lead = row.querySelector('.surface-ledger-lead');
            const leadText = lead ? lead.textContent.trim() : '';
            if (leadText !== 'MTG') {
                proposalDefects.push('PROPOSAL WITHOUT MTG EMBLEM: lead=' + leadText);
            }
            const primary = row.querySelector('[data-testid="proposal-primary"]');
            if (primary && primary.scrollWidth > primary.clientWidth + 2) {
                proposalDefects.push('CLIPPED PROPOSAL: ' + (primary.textContent || '').slice(0, 40));
            }
        }

        // Decision rows: data-testid="decision-row"
        const decRows = body.querySelectorAll('[data-testid="decision-row"]');

        // Suggested source rows: data-testid="suggested-source-row"
        const sugRows = body.querySelectorAll('[data-testid="suggested-source-row"]');
        const sugRefs = [];
        for (const row of sugRows) {
            const ref = row.querySelector('[data-testid="suggested-ref"]');
            sugRefs.push(ref ? ref.textContent.trim() : '---');
        }

        // Needs-you rows (non-proposal): data-testid="needs-you-row"
        const nyRows = body.querySelectorAll('[data-testid="needs-you-row"]');

        // Source scope rows: data-testid="source-scope"
        const srcRows = body.querySelectorAll('[data-testid="source-scope"]');

        // PEOPLE section: look for rows with monogram lead slots
        // RoomPeopleSection renders SurfaceLedgerRows with data-testid not set
        // but the section has PEOPLE N label
        const sections = body.querySelectorAll('.surface-section-head, h3');
        let peopleSectionText = '';
        for (const s of sections) {
            const t = (s.textContent || '').trim();
            if (t.startsWith('PEOPLE')) {
                peopleSectionText = t;
                break;
            }
        }

        // Host chip check: EgressChip (.gadget-chip-egress) without scope word
        // Exclude chips that validly lack a scope: "MODEL . NOT SET", empty default,
        // and cloud host chips (github.com etc. -- the scope IS the host name itself).
        const egressChips = body.querySelectorAll('.gadget-chip-egress');
        const hostDefects = [];
        for (const chip of egressChips) {
            const chipText = chip.textContent.trim();
            if (!chipText) continue;
            // Known valid patterns without an explicit scope word:
            if (/NOT SET/i.test(chipText)) continue;
            if (/MODEL/i.test(chipText)) continue;
            // Cloud hosts (github.com, jira.example.com) are their own scope label
            if (/[.][a-z]+$/i.test(chipText) && chipText.indexOf(' ') < 0) continue;
            const hasScope = /THIS DEVICE|LAN|CLOUD|MESH|PAIRED/i.test(chipText);
            if (!hasScope) {
                hostDefects.push('HOST WITHOUT SCOPE: ' + chipText);
            }
        }

        // Check for LOCAL anywhere in room body
        const bodyText = body.textContent || '';
        const hasLocal = bodyText.includes('LOCAL');

        // Check for zero counters
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(NEEDS|SOURCES|DECISIONS|THINGS|RECORD|PROPOSAL|COMMITMENT|PEOPLE)/g;
        let zcMatch;
        while ((zcMatch = zcRe.exec(bodyText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }

        // Check for raw <button>
        const allBtns = body.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('signal-button') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.closest('.gadget-string') ||
                btn.closest('.mic-button') ||
                btn.classList.contains('desk-mic')) continue;
            rawBtnCount++;
        }

        return {
            headline,
            proposalRows: propRows.length,
            decisionRows: decRows.length,
            suggestedRows: sugRows.length,
            suggestedRefs: sugRefs,
            needsYouRows: nyRows.length,
            sourceRows: srcRows.length,
            peopleSectionText,
            proposalDefects,
            hostDefects,
            hasLocal,
            zeroCounters,
            rawBtnCount,
        };
    }""")

    report.facts.append(asdict(_fact(
        face, "headline", "(N need you or Nothing needs you)",
        room_data.get("headline", "---"),
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="proposal_rows", expected="(varies)",
        observed=str(room_data.get("proposalRows", 0)),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="decision_rows", expected="(varies)",
        observed=str(room_data.get("decisionRows", 0)),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="suggested_source_rows", expected="(varies)",
        observed=str(room_data.get("suggestedRows", 0)),
        verdict="DATA", why="real desk content",
    )))
    for i, ref in enumerate(room_data.get("suggestedRefs", [])):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"suggested_ref:{i}", expected="(repo ref)",
            observed=ref[:12], verdict="DATA", why="suggested source reference",
        )))
    report.facts.append(asdict(FaceFact(
        face=face, field="source_rows", expected="(varies)",
        observed=str(room_data.get("sourceRows", 0)),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="people_section", expected="PEOPLE N",
        observed=room_data.get("peopleSectionText", "---"),
        verdict="DATA", why="real desk content",
    )))

    # Record defects from the face evaluation
    for d in room_data.get("proposalDefects", []):
        report.defects.append(f"ROOM/{face}: {d}")
    for d in room_data.get("hostDefects", []):
        report.defects.append(f"ROOM/{face}: {d}")
    if room_data.get("hasLocal"):
        report.defects.append(f"ROOM: LOCAL found (should be THIS DEVICE or LAN)")
    for z in room_data.get("zeroCounters", []):
        report.defects.append(f"ROOM: ZERO COUNTER '{z}' -- UX-CANON A.8 forbids counters of zero")
    if room_data.get("rawBtnCount", 0) > 0:
        report.defects.append(f"ROOM: {room_data['rawBtnCount']} raw <button>(s) outside library")

    # Overflow check at 393
    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# -- Step 4: Meeting detail --

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
        row_bodies = page.locator('.meetings-stream-row-body')
        if row_bodies.count() > 0:
            row_bodies.first.click()
            page.wait_for_timeout(2000)
            _settle(page)

    shot = _shoot(page, out_dir, "walk-meeting", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read detail face using real selectors from MeetingHeader.tsx + NeedsYouTable.tsx
    detail_data = page.evaluate("""() => {
        // MeetingHeader.tsx: .meetings-detail-head > .surface-display (title)
        //   .meetings-detail-facts > token spans + StateChip + EgressChip
        const head = document.querySelector('.meetings-detail-head');
        const facts = document.querySelector('.meetings-detail-facts');

        let title = '---';
        let factTokens = '---';
        if (head) {
            const display = head.querySelector('.surface-display');
            title = display ? display.textContent.trim() : '---';
        }
        if (facts) {
            factTokens = facts.textContent.trim();
        }

        // Check for RAN chip (StateChip with state="success" label="RAN")
        const ranChip = facts ? facts.querySelector('.surface-state-chip') : null;
        const hasRanChip = ranChip ? ranChip.textContent.trim().includes('RAN') : false;

        // EgressChip in detail facts
        const egressChip = facts ? facts.querySelector('.gadget-chip-egress') : null;
        const egressText = egressChip ? egressChip.textContent.trim() : '---';

        // NeedsYouTable.tsx: data-testid="meeting-needs-you"
        const needsYou = document.querySelector('[data-testid="meeting-needs-you"]');
        let needsCaption = '---';
        let needsRowCount = 0;
        if (needsYou) {
            const caption = needsYou.querySelector('.surface-caption');
            needsCaption = caption ? caption.textContent.trim() : '---';
            const outcomes = needsYou.querySelectorAll('.meetings-detail-outcome-row');
            needsRowCount = outcomes.length;
        }

        // Defect checks on the detail face
        const detailBody = document.querySelector('.surface-split-detail') ||
                           document.querySelector('.desk-surface-body');
        let hasLocal = false;
        let rawBtns = 0;
        let zeroCounters = [];
        if (detailBody) {
            const text = detailBody.textContent || '';
            hasLocal = text.includes('LOCAL');
            const zcRe = /\\b0\\s+(NEEDS|PROPOSAL|THING)/g;
            let m;
            while ((m = zcRe.exec(text)) !== null) zeroCounters.push(m[0]);

            const btns = detailBody.querySelectorAll('button');
            for (const b of btns) {
                if (b.classList.contains('btn') || b.classList.contains('desk-mic') ||
                    b.closest('.desk-traffic') || b.closest('.desk-wings')) continue;
                rawBtns++;
            }
        }

        // Check for clipped outcome text
        const outcomeTexts = document.querySelectorAll('.meetings-detail-outcome-text');
        const clipped = [];
        for (const t of outcomeTexts) {
            if (t.scrollWidth > t.clientWidth + 2) {
                clipped.push(t.textContent?.trim().slice(0, 40));
            }
        }

        return {
            title: title.slice(0, 12),
            factTokens: factTokens.slice(0, 200),
            hasRanChip,
            egressText,
            needsCaption,
            needsRowCount,
            hasLocal,
            rawBtns,
            zeroCounters,
            clippedOutcomes: clipped,
        };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="detail_title", expected="(meeting title[:12])",
        observed=detail_data.get("title", "---"),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="detail_facts", expected="DATE . N MIN . RAN . N S . host . LAN",
        observed=detail_data.get("factTokens", "---")[:200],
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="ran_chip", expected="true",
        observed=str(detail_data.get("hasRanChip", False)),
        verdict="MATCH" if detail_data.get("hasRanChip") else "DATA",
        why="RAN chip present" if detail_data.get("hasRanChip") else "no RAN chip",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="egress_chip", expected="(host . LAN or THIS DEVICE)",
        observed=detail_data.get("egressText", "---"),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="needs_you_caption", expected="NEEDS YOU N",
        observed=detail_data.get("needsCaption", "---"),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="needs_you_rows", expected="(varies)",
        observed=str(detail_data.get("needsRowCount", 0)),
        verdict="DATA", why="real desk content",
    )))

    # Record defects
    if detail_data.get("hasLocal"):
        report.defects.append("MEETING DETAIL: LOCAL found (should be THIS DEVICE or LAN)")
    if detail_data.get("rawBtns", 0) > 0:
        report.defects.append(f"MEETING DETAIL: {detail_data['rawBtns']} raw <button>(s)")
    for z in detail_data.get("zeroCounters", []):
        report.defects.append(f"MEETING DETAIL: ZERO COUNTER '{z}'")
    for c in detail_data.get("clippedOutcomes", []):
        report.defects.append(f"MEETING DETAIL: clipped outcome text: {c}")

    _close_surface(page)


# -- Step 5: Arrival --

def _step_arrival(page: Any, out_dir: Path, w: int,
                  report: WalkReport) -> None:
    """Shoot the arrival, record proposal rows + meetings."""
    face = "arrival"
    _settle(page)
    shot = _shoot(page, out_dir, "walk-arrival", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the arrival face using real selectors from ChairHome.tsx
    arrival_data = page.evaluate("""() => {
        // Headline: data-testid="arrival-display"
        const display = document.querySelector('[data-testid="arrival-display"]');
        const headline = display ? display.textContent.trim() : '---';

        // NEEDS YOU section: data-testid="arrival-needs-you"
        const needsYou = document.querySelector('[data-testid="arrival-needs-you"]');

        // Proposal rows: data-testid="arrival-proposal-row"
        const propRows = document.querySelectorAll('[data-testid="arrival-proposal-row"]');
        const proposals = [];
        for (const row of propRows) {
            // MTG emblem: data-testid="arrival-source-emblem"
            const emblem = row.querySelector('[data-testid="arrival-source-emblem"]');
            const emblemText = emblem ? emblem.textContent.trim() : '---';
            // Prefix: data-testid="arrival-proposal-prefix"
            const prefix = row.querySelector('[data-testid="arrival-proposal-prefix"]');
            const prefixText = prefix ? prefix.textContent.trim() : '---';
            // Text: data-testid="arrival-proposal-text"
            const textEl = row.querySelector('[data-testid="arrival-proposal-text"]');
            const proposalText = textEl ? textEl.textContent.trim().slice(0, 80) : '---';
            // Confirm verb: data-testid="arrival-proposal-confirm"
            const confirmBtn = row.querySelector('[data-testid="arrival-proposal-confirm"]');
            const hasConfirm = Boolean(confirmBtn);
            // Open verb: data-testid="arrival-proposal-open"
            const openBtn = row.querySelector('[data-testid="arrival-proposal-open"]');
            const hasOpen = Boolean(openBtn);
            proposals.push({ emblem: emblemText, prefix: prefixText,
                text: proposalText, hasConfirm, hasOpen });
        }

        // Other needs-you rows: data-testid="arrival-needs-you-row"
        const otherRows = document.querySelectorAll('[data-testid="arrival-needs-you-row"]');

        // MEETINGS section: data-testid="arrival-meeting-row"
        const meetingRows = document.querySelectorAll('[data-testid="arrival-meeting-row"]');
        let meetingsText = '';
        for (const mr of meetingRows) {
            meetingsText += (mr.textContent || '') + ' ';
        }
        const hasRAN = meetingsText.includes('RAN');

        // Sections present
        const sections = [];
        if (document.querySelector('[data-testid="arrival-needs-you"]')) sections.push('needs_you');
        if (document.querySelector('[data-testid="arrival-thoughts"]')) sections.push('thoughts');
        if (document.querySelector('[data-testid="arrival-brief"]')) sections.push('brief');
        if (document.querySelector('[data-testid="arrival-meetings"]')) sections.push('meetings');

        // Capture bar: data-testid="arrival-capture-bar"
        const captureBar = document.querySelector('[data-testid="arrival-capture-bar"]');
        const captureText = captureBar ? captureBar.textContent.trim() : '---';

        // Defect checks on the arrival face
        const chair = document.querySelector('.chair');
        const bodyText = chair ? chair.textContent : '';
        const hasLocal = bodyText.includes('LOCAL');
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(NEED|THINGS|MEETING|THOUGHT|AGENT)/g;
        let m;
        while ((m = zcRe.exec(bodyText)) !== null) zeroCounters.push(m[0]);

        // Check proposal rows without MTG emblem
        const missingEmblems = proposals.filter(p => p.emblem !== 'MTG').length;

        // Check for raw login / pronouns in people-like rows
        const pronounHits = [];
        const pronounRe = /\\b(her|him|she|he)\\b/gi;
        if (bodyText) {
            let pm;
            while ((pm = pronounRe.exec(bodyText)) !== null) pronounHits.push(pm[0]);
        }

        return {
            headline,
            proposalCount: propRows.length,
            proposals,
            otherNeedsYouRows: otherRows.length,
            meetingRowCount: meetingRows.length,
            hasRAN,
            sections,
            captureText: captureText.slice(0, 100),
            hasLocal,
            zeroCounters,
            missingEmblems,
            pronounHits,
        };
    }""")

    report.facts.append(asdict(_fact(
        face, "headline", "(N need you or Nothing needs you)",
        arrival_data.get("headline", "---"),
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="proposal_rows", expected="(varies)",
        observed=str(arrival_data.get("proposalCount", 0)),
        verdict="DATA", why="real desk content",
    )))
    for i, p in enumerate(arrival_data.get("proposals", [])[:5]):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"proposal:{i}",
            expected="MTG . Confirm:/Decide: . text . Confirm + Open",
            observed=f"{p['emblem']} . {p['prefix']} . {p['text'][:40]} . confirm={p['hasConfirm']} open={p['hasOpen']}",
            verdict="DATA", why="arrival proposal row",
        )))
    report.facts.append(asdict(FaceFact(
        face=face, field="meeting_rows", expected="(varies)",
        observed=str(arrival_data.get("meetingRowCount", 0)),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="meetings_has_RAN", expected="true",
        observed=str(arrival_data.get("hasRAN", False)),
        verdict="MATCH" if arrival_data.get("hasRAN") else "DATA",
        why="RAN chip in meetings" if arrival_data.get("hasRAN") else "no RAN chip",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="sections_present", expected="(varies by desk state)",
        observed=", ".join(arrival_data.get("sections", [])) or "none",
        verdict="DATA", why="real desk state",
    )))

    # Record defects
    if arrival_data.get("hasLocal"):
        report.defects.append("ARRIVAL: LOCAL found (should be THIS DEVICE or LAN)")
    for z in arrival_data.get("zeroCounters", []):
        report.defects.append(f"ARRIVAL: ZERO COUNTER '{z}' -- UX-CANON A.8")
    if arrival_data.get("missingEmblems", 0) > 0:
        report.defects.append(f"ARRIVAL: {arrival_data['missingEmblems']} proposal row(s) without MTG emblem")
    if arrival_data.get("pronounHits"):
        # Filter to unique
        hits = list(set(arrival_data["pronounHits"]))
        report.defects.append(f"ARRIVAL: pronoun tokens found: {hits}")


# -- Step 6: People --

def _step_people(page: Any, out_dir: Path, w: int, token: str,
                 report: WalkReport) -> None:
    """Open People, find first relationship, shoot card, record watch_summary.
    Never writes a person's name to the facts file."""
    face = "people"
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
                        f"/api/people/relationships/{rel_id}/brief",
                        None, token)
    if brief_result["status"] == 200:
        brief = brief_result["payload"]
        brief_data = brief.get("brief", brief) if isinstance(brief, dict) else {}
        ws = brief_data.get("watch_summary", {})
        prs = ws.get("prs_waiting", [])
        assignments = ws.get("open_assignments", [])

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

        # Overdue commitments from open_commitments
        open_commitments = brief_data.get("open_commitments", [])
        overdue = [c for c in open_commitments if c.get("due")]
        report.facts.append(asdict(FaceFact(
            face=face, field="watch_summary:open_commitments",
            expected="(count)",
            observed=str(len(open_commitments)),
            verdict="DATA", why="open commitments for <person>",
        )))

        # Last meeting
        lm = brief_data.get("last_meeting")
        if lm:
            report.facts.append(asdict(FaceFact(
                face=face, field="watch_summary:last_meeting_items",
                expected="(count)",
                observed=str(lm.get("item_count", 0)),
                verdict="DATA", why="items from last meeting with <person>",
            )))

        # Defect checks: raw login in watch summary
        for pr in prs[:3]:
            pr_title = str(pr.get("title", ""))
            if re.search(r'\b[a-z]+-[a-z]+\b', pr_title) and not re.search(r'[A-Z]', pr_title):
                report.defects.append(f"PEOPLE: raw login in PR title: {pr_title[:20]}")

    elif brief_result["status"] == 404:
        report.facts.append(asdict(FaceFact(
            face=face, field="one_on_one_brief", expected="200",
            observed="404", verdict="DATA", why="brief route not found",
        )))

    # Open the People face and shoot the Prep lens
    _open_surface(page, token, "open-people", f"people:{rel_id}:prep")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    # Check if prep lens rendered
    prep_lens = page.locator('[data-testid="people-prep-lens"]')
    if prep_lens.count() > 0:
        shot = _shoot(page, out_dir, "walk-people-prep", w, window=True)
        report.shots.append({"face": f"{face}-prep", "width": w, "path": str(shot)})

        # Read Prep lens data using real selectors from PeopleCore.tsx
        prep_data = page.evaluate("""() => {
            const lens = document.querySelector('[data-testid="people-prep-lens"]');
            if (!lens) return { display: '---', prsRow: false, assignRow: false,
                commitRow: false, meetingRow: false };

            // Display step: data-testid="prep-display-name"
            const display = lens.querySelector('[data-testid="prep-display-name"]');
            const displayText = display ? display.textContent.trim() : '---';

            // PRS WAITING row: data-testid="prep-prs-row"
            const prsRow = lens.querySelector('[data-testid="prep-prs-row"]');
            // ASSIGNMENTS row: data-testid="prep-assignments-row"
            const assignRow = lens.querySelector('[data-testid="prep-assignments-row"]');
            // COMMITMENTS row: data-testid="prep-commitments-row"
            const commitRow = lens.querySelector('[data-testid="prep-commitments-row"]');
            // MEETING row: data-testid="prep-meeting-row"
            const meetingRow = lens.querySelector('[data-testid="prep-meeting-row"]');

            // Footer: data-testid="prep-receipt"
            const receipt = lens.querySelector('[data-testid="prep-receipt"]');
            const receiptText = receipt ? receipt.textContent.trim() : '---';

            // Defect: raw login or pronouns in summary rows
            const summaryRows = lens.querySelector('[data-testid="prep-summary-rows"]');
            const summaryText = summaryRows ? summaryRows.textContent : '';
            const pronounRe = /\\b(her|him|she|he)\\b/gi;
            const pronouns = [];
            let pm;
            while ((pm = pronounRe.exec(summaryText)) !== null) pronouns.push(pm[0]);

            // Zero counter check
            const zcRe = /\\b0\\s+(PRS?|ASSIGNMENTS?|COMMITMENTS?|ITEMS?)/g;
            const zc = [];
            let zm;
            while ((zm = zcRe.exec(summaryText)) !== null) zc.push(zm[0]);

            return {
                display: displayText.slice(0, 2) + '***',
                prsRow: Boolean(prsRow),
                assignRow: Boolean(assignRow),
                commitRow: Boolean(commitRow),
                meetingRow: Boolean(meetingRow),
                receipt: receiptText,
                pronouns,
                zeroCounters: zc,
            };
        }""")

        report.facts.append(asdict(FaceFact(
            face=face, field="prep_display", expected="(person name[:2]***)",
            observed=prep_data.get("display", "---"),
            verdict="DATA", why="prep display (truncated for privacy)",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="prep_prs_row", expected="(present if prs > 0)",
            observed=str(prep_data.get("prsRow", False)),
            verdict="DATA", why="PRS WAITING row",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="prep_assignments_row", expected="(present if assigns > 0)",
            observed=str(prep_data.get("assignRow", False)),
            verdict="DATA", why="ASSIGNMENTS OPEN row",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="prep_receipt", expected="PREPARED HH:MM",
            observed=prep_data.get("receipt", "---"),
            verdict="DATA", why="prep footer",
        )))

        # Defects
        if prep_data.get("pronouns"):
            report.defects.append(f"PEOPLE PREP: pronoun tokens: {prep_data['pronouns']}")
        for z in prep_data.get("zeroCounters", []):
            report.defects.append(f"PEOPLE PREP: ZERO COUNTER '{z}'")
    else:
        report.surprises.append("PEOPLE: Prep lens did not render")

    _close_surface(page)


# -- Step 7: Settings -> Meetings --

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

    # Read the Meetings module face using real selectors from SettingsCore.tsx
    settings_data = page.evaluate("""() => {
        // Display headline: data-testid="meetings-auto-display"
        const display = document.querySelector('[data-testid="meetings-auto-display"]');
        const displayText = display ? display.textContent.trim() : '---';

        // Intelligence row: CycleGadget (.gadget-cycle select)
        const cycle = document.querySelector('.gadget-cycle select');
        let cycleValue = '---';
        if (cycle && cycle.selectedOptions && cycle.selectedOptions.length) {
            cycleValue = cycle.selectedOptions[0].text.trim();
        }

        // EgressChip in the intelligence row (.gadget-chip-egress)
        const egressChips = document.querySelectorAll('.gadget-chip-egress');
        let intelEgress = '---';
        for (const chip of egressChips) {
            const t = chip.textContent.trim();
            if (t && !t.includes('FETCHES')) {
                intelEgress = t;
                break;
            }
        }

        // NO MODEL chip: data-testid="settings-no-model"
        const noModel = document.querySelector('[data-testid="settings-no-model"]');
        const hasNoModel = Boolean(noModel);

        // Choose model button: data-testid="settings-choose-model"
        const chooseModel = document.querySelector('[data-testid="settings-choose-model"]');
        const hasChooseModel = Boolean(chooseModel);

        // Defect checks on the settings body
        const body = document.querySelector('.desk-surface-body');
        const bodyText = body ? body.textContent : '';
        const hasLocal = bodyText.includes('LOCAL');
        const zc = [];
        const zcRe = /\\b0\\s+(NEEDS|SOURCE|ENGINE)/g;
        let m;
        while ((m = zcRe.exec(bodyText)) !== null) zc.push(m[0]);

        // Raw <button> check
        let rawBtns = 0;
        if (body) {
            const btns = body.querySelectorAll('button');
            for (const b of btns) {
                if (b.classList.contains('btn') || b.classList.contains('desk-mic') ||
                    b.closest('.gadget-stepper') || b.closest('.gadget-table') ||
                    b.closest('.gadget-cycle') || b.closest('.fold-gadget') ||
                    b.closest('.check-gadget') || b.closest('.desk-traffic') ||
                    b.closest('.desk-wings') || b.closest('.surface-ledger-row') ||
                    b.classList.contains('surface-ledger-line')) continue;
                rawBtns++;
            }
        }

        return {
            displayText,
            cycleValue,
            intelEgress,
            hasNoModel,
            hasChooseModel,
            hasLocal,
            zeroCounters: zc,
            rawBtns,
        };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="display_headline",
        expected="After every meeting / After room meetings / Off",
        observed=settings_data.get("displayText", "---"),
        verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="intelligence_cycle",
        expected="AFTER EVERY MEETING / ROOM-LINKED ONLY / OFF",
        observed=settings_data.get("cycleValue", "---"),
        verdict="DATA", why="real desk content",
    )))

    if settings_data.get("hasNoModel"):
        report.facts.append(asdict(FaceFact(
            face=face, field="intelligence_model",
            expected="(model host chip or NO MODEL + Choose)",
            observed=f"NO MODEL (Choose={settings_data.get('hasChooseModel', False)})",
            verdict="DATA", why="no model assigned",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="intelligence_egress",
            expected="(host . LAN or THIS DEVICE)",
            observed=settings_data.get("intelEgress", "---"),
            verdict="DATA", why="intel model host chip",
        )))

    # Defects
    if settings_data.get("hasLocal"):
        report.defects.append("SETTINGS MEETINGS: LOCAL found (should be THIS DEVICE or LAN)")
    for z in settings_data.get("zeroCounters", []):
        report.defects.append(f"SETTINGS MEETINGS: ZERO COUNTER '{z}'")
    if settings_data.get("rawBtns", 0) > 0:
        report.defects.append(f"SETTINGS MEETINGS: {settings_data['rawBtns']} raw <button>(s)")

    # Overflow at 393
    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# -- Defect detection --

def _detect_defects(report: WalkReport) -> None:
    seen: set[tuple[str, str]] = set()
    for fact in report.facts:
        key = (fact["face"], fact["field"])
        if key in seen:
            continue
        seen.add(key)
        obs = fact["observed"]

        # D1: zero counter (UX-CANON A.8)
        if re.search(r'\b0\s+(NEED|THINGS|RECORD|PROPOSAL|DECISION|COMMITMENT|PEOPLE)', obs):
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

    report.defects = list(dict.fromkeys(report.defects))


# -- Report writers --

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


# -- Main --

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
