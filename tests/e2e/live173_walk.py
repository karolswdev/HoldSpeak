"""HS-173-06 PRE-WALK runner: the Steward's Hand and Voice -- read-only walk of the owner's real hub.

Shoots five faces (Room HEALTH, Update editor, Steward policy posture,
and the steward's NEEDS YOU bottleneck rows) at 1440x900 and 393x852.
ZERO WRITES.  This walk is entirely read-only on the owner's desk.

THE LIVE LAWS (Article IV -- the walk arms nothing):
1. READ-ONLY.  Never presses Send / Publish / Run now / Enable.
   Never fires a nudge.  Never runs the steward.  Never enables
   an effect kind.
2. NO HARDCODED TOKENS.
3. FACE-DRIVEN.
4. STANDALONE.  Not collected by pytest.

Usage:
  python tests/e2e/live173_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]
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
collect_ignore_glob = ["live173_walk.py"]


# -- Write guard (fail-closed: no writes permitted) --

def _write_allowed(operation: str | None, context: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Decide whether a write operation is allowed in this walk.

    Returns (allowed: bool, reason: str).

    This walk is ENTIRELY READ-ONLY.  No write operation is permitted.
    D5 names four write beats (steward run, publish, nudge send, enable
    effect kind); ALL FOUR are excluded by the walk law.  The guard
    exists to make the prohibition explicit and fail-closed: any new
    step that calls it gets DENIED with a named reason.

    Cases:
        _write_allowed("steward_run")        -> (False, "steward run excluded by walk law")
        _write_allowed("publish_update")     -> (False, "publish excluded by walk law")
        _write_allowed("send_nudge")         -> (False, "nudge send excluded by walk law")
        _write_allowed("enable_effect_kind") -> (False, "enable effect kind excluded by walk law")
        _write_allowed("save_draft")         -> (False, "save draft not named in D5")
        _write_allowed("unknown")            -> (False, "unknown operation denied by default")
        _write_allowed("")                   -> (False, "empty operation denied")
        _write_allowed(None)                 -> (False, "null operation denied")
    """
    if not operation:
        return False, "empty operation denied" if operation == "" else "null operation denied"
    _REASONS: dict[str, str] = {
        "steward_run": "steward run excluded by walk law",
        "publish_update": "publish excluded by walk law",
        "send_nudge": "nudge send excluded by walk law",
        "enable_effect_kind": "enable effect kind excluded by walk law",
        "save_draft": "save draft not named in D5",
    }
    reason = _REASONS.get(operation, "unknown operation denied by default")
    return False, reason


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-173-the-stewards-hand-and-voice/assets/story-06-shots"

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


# ---------------------------------------------------------------------------
# Step 1: read the steward policy for the owner's first Room via the API
# ---------------------------------------------------------------------------

def _step_steward_policy(page: Any, token: str, report: WalkReport) -> dict:
    """Read the steward policy for the first project.

    Returns a dict with:
      project_id              -- the first project's id
      project_name            -- its name (truncated to 12 chars)
      eligible_effect_kinds   -- list of enabled effect kind strings
      github_comment_enabled  -- bool: is github_comment in the list?
    """
    face = "steward-policy-api"
    out: dict[str, Any] = {}

    # Find the first project
    proj_result = _api(page, "GET", "/api/projects", None, token)
    if proj_result["status"] >= 300:
        report.errors.append(f"GET /api/projects returned {proj_result['status']}")
        return out
    projects = proj_result["payload"]
    proj_list = projects.get("projects", []) if isinstance(projects, dict) else projects
    if not proj_list:
        report.surprises.append("STEWARD POLICY: zero projects on owner's desk")
        return out

    project = proj_list[0]
    project_id = str(project.get("id", ""))
    project_name = str(project.get("name", project.get("title", "---")))
    out["project_id"] = project_id
    out["project_name"] = project_name[:12]

    report.facts.append(asdict(FaceFact(
        face=face, field="project_name", expected="(owner's project)",
        observed=project_name[:12], verdict="DATA", why="real desk content",
    )))

    # Read the steward policy -- try dedicated route first, fall back to
    # the project detail payload.
    # TODO(D3-steward-policy): confirm exact route once wire lands
    steward_result = _api(page, "GET",
                          f"/api/projects/{project_id}/steward", None, token)
    if steward_result["status"] == 200:
        steward = steward_result["payload"]
        policy = steward.get("policy", steward) if isinstance(steward, dict) else {}
        eligible = policy.get("eligible_effect_kinds",
                              policy.get("eligible_effect_kinds_json", []))
        if isinstance(eligible, str):
            try:
                eligible = json.loads(eligible)
            except (json.JSONDecodeError, TypeError):
                eligible = []
        out["eligible_effect_kinds"] = eligible
        out["github_comment_enabled"] = "github_comment" in eligible

        report.facts.append(asdict(FaceFact(
            face=face, field="eligible_effect_kinds",
            expected="(list, github_comment expected absent)",
            observed=json.dumps(eligible), verdict="DATA",
            why="from steward policy",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="github_comment_enabled", expected="false",
            observed=str("github_comment" in eligible),
            verdict="MATCH" if "github_comment" not in eligible else "DATA",
            why=("github_comment absent as expected"
                 if "github_comment" not in eligible
                 else "github_comment in eligible_effect_kinds"),
        )))
    elif steward_result["status"] == 404:
        # Fall back to the project detail payload
        proj_detail = _api(page, "GET",
                           f"/api/projects/{project_id}", None, token)
        if proj_detail["status"] == 200:
            proj_data = proj_detail["payload"]
            policy = (proj_data.get("steward_policy", {})
                      if isinstance(proj_data, dict) else {})
            eligible = policy.get("eligible_effect_kinds",
                                  policy.get("eligible_effect_kinds_json", []))
            if isinstance(eligible, str):
                try:
                    eligible = json.loads(eligible)
                except (json.JSONDecodeError, TypeError):
                    eligible = []
            out["eligible_effect_kinds"] = eligible
            out["github_comment_enabled"] = "github_comment" in eligible

            report.facts.append(asdict(FaceFact(
                face=face, field="eligible_effect_kinds", expected="(list)",
                observed=json.dumps(eligible), verdict="DATA",
                why="from project detail payload (steward route 404)",
            )))
            report.facts.append(asdict(FaceFact(
                face=face, field="github_comment_enabled", expected="false",
                observed=str("github_comment" in eligible),
                verdict="MATCH" if "github_comment" not in eligible else "DATA",
                why="from project detail",
            )))
        else:
            report.facts.append(asdict(FaceFact(
                face=face, field="steward_route", expected="200",
                observed=f"steward=404, project={proj_detail['status']}",
                verdict="DATA",
                why="steward route not found, project fallback failed",
            )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="steward_api_status", expected="200",
            observed=str(steward_result["status"]),
            verdict="DATA",
            why=f"GET steward returned HTTP {steward_result['status']}",
        )))

    return out


# ---------------------------------------------------------------------------
# Step 2: read the Room's health payload via the API
# ---------------------------------------------------------------------------

def _step_room_health_api(page: Any, token: str, report: WalkReport,
                          policy: dict) -> dict:
    """Read the Room's health payload from the API.

    Returns a dict with the health signal data (or empty if the route
    does not exist yet).
    """
    face = "room-health-api"
    out: dict[str, Any] = {}
    project_id = policy.get("project_id")
    if not project_id:
        report.surprises.append("ROOM HEALTH API: no project_id from step 1")
        return out

    # TODO(D3-room-health): GET /api/projects/{id}/room should return a
    # health object with per-signal data once the wire lands
    room_result = _api(page, "GET",
                       f"/api/projects/{project_id}/room", None, token)
    if room_result["status"] == 200:
        room = room_result["payload"]
        health = room.get("health", {}) if isinstance(room, dict) else {}
        out["health"] = health

        # Record each signal if present
        for signal_key in ("review_latency", "issue_aging", "ci", "release"):
            signal = health.get(signal_key)
            if signal:
                tone = signal.get("tone", signal.get("state", "---"))
                summary = signal.get("summary", signal.get("label", "---"))
                report.facts.append(asdict(FaceFact(
                    face=face, field=f"health:{signal_key}:tone",
                    expected="(green/amber/red or absent)",
                    observed=str(tone), verdict="DATA",
                    why="from Room health payload",
                )))
                report.facts.append(asdict(FaceFact(
                    face=face, field=f"health:{signal_key}:summary",
                    expected="(signal summary)",
                    observed=str(summary)[:80], verdict="DATA",
                    why="from Room health payload",
                )))
            else:
                report.facts.append(asdict(FaceFact(
                    face=face, field=f"health:{signal_key}",
                    expected="(absent when no data)",
                    observed="absent", verdict="DATA",
                    why="signal not present in health payload",
                )))

        # Scorecard composite
        scorecard = health.get("scorecard", health.get("composite"))
        if scorecard:
            report.facts.append(asdict(FaceFact(
                face=face, field="health:scorecard",
                expected="(green/amber/red composite)",
                observed=str(scorecard)[:80], verdict="DATA",
                why="release-readiness composite",
            )))

        # Reviewer-latency per-person breakdown (for NEEDS YOU rows)
        reviewers = health.get(
            "reviewers",
            health.get("review_latency", {}).get("per_person", []),
        )
        if isinstance(reviewers, list):
            report.facts.append(asdict(FaceFact(
                face=face, field="health:reviewer_count",
                expected="(count of reviewers with pending PRs)",
                observed=str(len(reviewers)), verdict="DATA",
                why="from Room health payload",
            )))
            for i, rev in enumerate(reviewers[:5]):
                name = str(rev.get("name", rev.get("login", "---")))[:12]
                median = rev.get("median_hours", rev.get("median", "---"))
                waiting = rev.get("waiting_count", rev.get("count", "---"))
                report.facts.append(asdict(FaceFact(
                    face=face, field=f"health:reviewer:{i}",
                    expected="(name . median . waiting)",
                    observed=f"{name} . {median} H . {waiting} waiting",
                    verdict="DATA", why="per-person reviewer latency",
                )))
    elif room_result["status"] == 404:
        report.facts.append(asdict(FaceFact(
            face=face, field="room_health_route", expected="200",
            observed="404 -- route not wired yet",
            verdict="DATA",
            why="Room health route not found (TODO from D3)",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="room_health_status", expected="200",
            observed=str(room_result["status"]),
            verdict="DATA",
            why=f"HTTP {room_result['status']}",
        )))

    return out


# ---------------------------------------------------------------------------
# Step 3: open the Room, shoot HEALTH rows + NEEDS YOU bottleneck
# ---------------------------------------------------------------------------

def _step_room_health_face(page: Any, out_dir: Path, w: int, token: str,
                           report: WalkReport, policy: dict) -> None:
    """Open the Room, shoot walk-room-health-{w}.png, record HEALTH and
    NEEDS YOU rows.  Check whether the Nudge verb is correctly withheld
    when github_comment is not in eligible_effect_kinds."""
    face = "room-health"
    project_id = policy.get("project_id")
    if not project_id:
        report.surprises.append("ROOM HEALTH FACE: no project_id from step 1")
        return

    _open_surface(page, token, "open-project-memory", f"project:{project_id}")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-room-health", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    github_comment_enabled = policy.get("github_comment_enabled", False)

    # Read HEALTH section and NEEDS YOU from the Room face.
    # TODO(D2b-health-section): selector for the HEALTH section caption
    # TODO(D2b-health-review-latency): selector for REVIEW LATENCY row
    # TODO(D2b-health-issue-aging): selector for ISSUE AGING row
    # TODO(D2b-health-ci): selector for CI row
    # TODO(D2b-health-release): selector for RELEASE row
    # TODO(D2c-nudge-verb): selector for the Nudge verb on reviewer NEEDS YOU rows
    room_data = page.evaluate("""([githubCommentEnabled]) => {
        const body = document.querySelector('[data-testid="room-body"]');
        if (!body) return {
            healthSectionPresent: false, healthRows: [],
            needsYouRows: 0, nudgeVerbPresent: false,
            nudgeVerbCount: 0, nudgeWhileIneligible: false,
            zeroCounters: [], rawBtnCount: 0, hasLocal: false,
            hostDefects: [], clippedTexts: [],
        };

        /* --- HEALTH section --- */
        const sections = body.querySelectorAll(
            '.surface-section-head, h3, [data-testid]'
        );
        let healthSectionPresent = false;
        for (const s of sections) {
            const t = (s.textContent || '').trim();
            if (t.startsWith('HEALTH') ||
                s.dataset.testid === 'room-health-section') {
                healthSectionPresent = true;
                break;
            }
        }

        /* --- HEALTH rows --- */
        const healthRowIds = [
            'room-health-review-latency',
            'room-health-issue-aging',
            'room-health-ci',
            'room-health-release',
        ];
        const healthRows = [];
        for (const rid of healthRowIds) {
            const row = body.querySelector('[data-testid="' + rid + '"]');
            if (row) {
                const sc = row.querySelector('.surface-state-chip');
                const tone = sc
                    ? (sc.dataset.tone ||
                       (sc.className.match(/state--(\\w+)/) || [])[1] ||
                       '---')
                    : '---';
                const primary = row.querySelector(
                    '.surface-ledger-primary, [data-testid$="-primary"]'
                );
                const primaryText = primary
                    ? primary.textContent.trim() : '---';
                const cells = row.querySelector(
                    '.surface-ledger-cells, [data-testid$="-cells"]'
                );
                const cellsText = cells
                    ? cells.textContent.trim() : '---';
                const hasDataTokens = Boolean(
                    cellsText && cellsText !== '---' && cellsText.length > 0
                );
                healthRows.push({
                    id: rid, present: true, tone,
                    primary: primaryText, cells: cellsText,
                    hasDataTokens,
                });
            } else {
                healthRows.push({ id: rid, present: false });
            }
        }

        /* --- NEEDS YOU rows --- */
        const needsYouRows = body.querySelectorAll(
            '[data-testid="needs-you-row"], [data-testid="room-needs-you-row"]'
        );
        let nudgeVerbPresent = false;
        let nudgeVerbCount = 0;
        for (const row of needsYouRows) {
            const nudgeBtn = row.querySelector(
                '[data-testid="nudge-verb"], .btn[data-verb="nudge"]'
            );
            if (nudgeBtn) {
                nudgeVerbPresent = true;
                nudgeVerbCount++;
            }
        }
        const nudgeWhileIneligible = !githubCommentEnabled && nudgeVerbPresent;

        /* --- defect scans --- */
        const bodyText = body.textContent || '';
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(NEED|HEALTH|REVIEW|ISSUE|CI|RELEASE|SOURCES|DECISIONS|THINGS|RECORD|PROPOSAL|COMMITMENT|PEOPLE)/g;
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

        const egressChips = body.querySelectorAll('.gadget-chip-egress');
        const hostDefects = [];
        for (const chip of egressChips) {
            const ct = chip.textContent.trim();
            if (!ct) continue;
            if (/NOT SET/i.test(ct)) continue;
            if (/MODEL/i.test(ct)) continue;
            if (/[.][a-z]+$/i.test(ct) && ct.indexOf(' ') < 0) continue;
            if (!/THIS DEVICE|LAN|CLOUD|MESH|PAIRED/i.test(ct)) {
                hostDefects.push('HOST WITHOUT SCOPE: ' + ct);
            }
        }

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
            healthSectionPresent, healthRows,
            needsYouRows: needsYouRows.length,
            nudgeVerbPresent, nudgeVerbCount, nudgeWhileIneligible,
            zeroCounters, hasLocal, rawBtnCount,
            hostDefects, clippedTexts,
        };
    }""", [github_comment_enabled])

    # ---- record facts ----

    report.facts.append(asdict(FaceFact(
        face=face, field="health_section_present",
        expected="(true when signals have data, false when no data)",
        observed=str(room_data.get("healthSectionPresent", False)),
        verdict="DATA", why="HEALTH section on Room face",
    )))

    for hr in room_data.get("healthRows", []):
        rid = hr.get("id", "unknown")
        short_name = rid.replace("room-health-", "")
        if hr.get("present"):
            report.facts.append(asdict(FaceFact(
                face=face, field=f"health_row:{short_name}",
                expected="(tone . primary . cells with data tokens)",
                observed=(f"tone={hr.get('tone', '---')} . "
                          f"{hr.get('primary', '---')} . "
                          f"{hr.get('cells', '---')}"),
                verdict="DATA", why="HEALTH row on Room face",
            )))
            if not hr.get("hasDataTokens"):
                report.defects.append(
                    f"ROOM HEALTH: row {short_name} present but has "
                    f"no data tokens (cells empty)"
                )
        else:
            report.facts.append(asdict(FaceFact(
                face=face, field=f"health_row:{short_name}",
                expected="(absent when no data for this signal)",
                observed="absent", verdict="DATA",
                why="HEALTH row not rendered",
            )))

    report.facts.append(asdict(FaceFact(
        face=face, field="needs_you_rows",
        expected="(varies)",
        observed=str(room_data.get("needsYouRows", 0)),
        verdict="DATA", why="NEEDS YOU rows in Room",
    )))

    report.facts.append(asdict(FaceFact(
        face=face, field="nudge_verb_present",
        expected=("true if github_comment eligible"
                  if github_comment_enabled
                  else "false (github_comment not eligible)"),
        observed=(f"present={room_data.get('nudgeVerbPresent', False)} "
                  f"(count={room_data.get('nudgeVerbCount', 0)})"),
        verdict="DATA",
        why="Nudge verb on reviewer-bottleneck NEEDS YOU rows",
    )))

    # H1 defect: Nudge shown while github_comment is not eligible
    if room_data.get("nudgeWhileIneligible"):
        report.defects.append(
            "H1 DEFECT: Nudge verb shown on NEEDS YOU row while "
            "github_comment is NOT in eligible_effect_kinds -- "
            "the verb is a lie (UX-CANON A.11)"
        )

    # other defects
    for z in room_data.get("zeroCounters", []):
        report.defects.append(
            f"ROOM HEALTH: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if room_data.get("hasLocal"):
        report.defects.append(
            "ROOM HEALTH: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if room_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"ROOM HEALTH: {room_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for d in room_data.get("hostDefects", []):
        report.defects.append(f"ROOM HEALTH: {d}")
    for c in room_data.get("clippedTexts", []):
        report.defects.append(f"ROOM HEALTH: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 4: open the update editor (read-only)
# ---------------------------------------------------------------------------

def _step_update_editor(page: Any, out_dir: Path, w: int, token: str,
                        report: WalkReport, policy: dict) -> None:
    """Open the latest draft update (read-only), shoot walk-update-{w}.png,
    record generator token, claim chip count, UNVERIFIED count, host chip."""
    face = "update-editor"
    project_id = policy.get("project_id")
    if not project_id:
        report.surprises.append("UPDATE EDITOR: no project_id from step 1")
        return

    # Check if any updates exist via the API
    updates_result = _api(page, "GET",
                          f"/api/projects/{project_id}/updates", None, token)
    if updates_result["status"] >= 300:
        report.facts.append(asdict(FaceFact(
            face=face, field="updates_api_status", expected="200",
            observed=str(updates_result["status"]),
            verdict="DATA",
            why=f"HTTP {updates_result['status']}",
        )))
        return

    updates = updates_result["payload"]
    update_list = (updates.get("updates", [])
                   if isinstance(updates, dict) else updates)
    if not update_list:
        report.surprises.append("UPDATE EDITOR: no updates on owner's desk")
        return

    latest = update_list[0]
    status = str(latest.get("status", latest.get("state", "---")))
    generator = str(latest.get("generator", "---"))

    report.facts.append(asdict(FaceFact(
        face=face, field="latest_update_status",
        expected="(draft or published)",
        observed=status, verdict="DATA", why="latest update state",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="latest_update_generator",
        expected="(deterministic or model label)",
        observed=generator, verdict="DATA",
        why="who generated the update",
    )))

    # Open the Room (the update editor lives inside the project Room)
    # TODO(D2a-update-posture): exact navigation to UpdatePosture
    _open_surface(page, token, "open-project-memory", f"project:{project_id}")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-update", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read update editor face data.
    # TODO(D2a-update-posture): selector for UpdatePosture area
    # TODO(D2a-claim-chip): selector for inline claim chips
    # TODO(D2a-unverified-chip): selector for UNVERIFIED StateChip markers
    # TODO(D2a-host-chip): selector for the model host EgressChip
    update_data = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="room-body"]') ||
                     document.querySelector('.desk-surface-body');
        if (!body) return {
            generatorToken: '---', claimChipCount: 0,
            unverifiedCount: 0, hostChipText: '---',
            hasHostChip: false, zeroCounters: [],
            rawBtnCount: 0, hasLocal: false, clippedTexts: [],
        };

        const area = body.querySelector('[data-testid="update-posture"]') ||
                     body.querySelector('[data-testid="update-editor"]') ||
                     body;

        /* generator token */
        const genEl = area.querySelector('[data-testid="update-generator"]');
        const generatorToken = genEl ? genEl.textContent.trim() : '---';

        /* claim chips */
        const claimChips = area.querySelectorAll(
            '[data-testid="claim-chip"], .surface-token[data-chip]'
        );
        const claimChipCount = claimChips.length;

        /* UNVERIFIED markers */
        const stateChips = area.querySelectorAll(
            '[data-testid="unverified-marker"], .surface-state-chip'
        );
        let unverifiedCount = 0;
        for (const chip of stateChips) {
            if ((chip.textContent || '').trim().includes('UNVERIFIED')) {
                unverifiedCount++;
            }
        }

        /* host EgressChip */
        const hostChip = area.querySelector('.gadget-chip-egress');
        const hostChipText = hostChip ? hostChip.textContent.trim() : '---';
        const hasHostChip = Boolean(hostChip);

        /* defect scans */
        const areaText = area.textContent || '';
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(CLAIM|REF|UNVERIFIED|SOURCE)/g;
        let zcMatch;
        while ((zcMatch = zcRe.exec(areaText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }
        const hasLocal = areaText.includes('LOCAL');

        const allBtns = area.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.classList.contains('surface-edit-in-place') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.gadget-string') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        const clippedTexts = [];
        const textEls = area.querySelectorAll(
            '.surface-ledger-primary, [data-testid$="-primary"], .surface-token'
        );
        for (const el of textEls) {
            if (el.scrollWidth > el.clientWidth + 2) {
                clippedTexts.push(
                    'CLIPPED: ' + (el.textContent || '').slice(0, 40)
                );
            }
        }

        return {
            generatorToken, claimChipCount, unverifiedCount,
            hostChipText, hasHostChip,
            zeroCounters, rawBtnCount, hasLocal, clippedTexts,
        };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="generator_token",
        expected="(deterministic or model label)",
        observed=update_data.get("generatorToken", "---"),
        verdict="DATA", why="generator token on update face",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="claim_chip_count", expected="(varies)",
        observed=str(update_data.get("claimChipCount", 0)),
        verdict="DATA", why="claim chips in update body",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="unverified_count",
        expected="(varies, 0 for deterministic)",
        observed=str(update_data.get("unverifiedCount", 0)),
        verdict="DATA", why="UNVERIFIED markers in update body",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="host_chip",
        expected="(model host or absent for deterministic)",
        observed=update_data.get("hostChipText", "---"),
        verdict="DATA", why="EgressChip on update card",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="host_chip_present",
        expected="(true when model, false when deterministic)",
        observed=str(update_data.get("hasHostChip", False)),
        verdict="DATA", why="EgressChip presence",
    )))

    # Defect: UNVERIFIED smoothed when generator is a model
    if (generator not in ("deterministic", "---")
            and update_data.get("claimChipCount", 0) > 0
            and update_data.get("unverifiedCount", 0) == 0):
        report.surprises.append(
            "UPDATE EDITOR: model-generated update has claim chips but "
            "ZERO UNVERIFIED markers -- all claims may be grounded, or "
            "markers may be missing (needs manual verification)"
        )

    # Defect: host chip without scope
    host_text = update_data.get("hostChipText", "---")
    if host_text and host_text != "---":
        has_cloud_host = re.search(r'[.][a-z]+$', host_text, re.I) and ' ' not in host_text
        has_scope = re.search(r'THIS DEVICE|LAN|CLOUD|MESH|PAIRED', host_text, re.I)
        if not has_scope and not has_cloud_host:
            report.defects.append(
                f"UPDATE EDITOR: HOST WITHOUT SCOPE: {host_text}"
            )

    for z in update_data.get("zeroCounters", []):
        report.defects.append(
            f"UPDATE EDITOR: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if update_data.get("hasLocal"):
        report.defects.append(
            "UPDATE EDITOR: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if update_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"UPDATE EDITOR: {update_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )
    for c in update_data.get("clippedTexts", []):
        report.defects.append(f"UPDATE EDITOR: {c}")

    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)

    _close_surface(page)


# ---------------------------------------------------------------------------
# Step 5: open the steward posture, shoot the policy face
# ---------------------------------------------------------------------------

def _step_steward_posture(page: Any, out_dir: Path, w: int, token: str,
                          report: WalkReport, policy: dict) -> None:
    """Open the steward posture, shoot walk-steward-policy-{w}.png,
    record the Effects rows, the Reviewer nudge row's checked state,
    and its GITHUB.COM chip."""
    face = "steward-posture"
    project_id = policy.get("project_id")
    if not project_id:
        report.surprises.append("STEWARD POSTURE: no project_id from step 1")
        return

    # TODO(D2d-steward-posture): exact surface-open key for the steward
    # posture (may be a tab inside the project Room)
    _open_surface(page, token, "open-project-memory", f"project:{project_id}")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    # TODO(D2d-steward-tab): navigate to the steward / policy tab
    # within the Room once the face lands

    shot = _shoot(page, out_dir, "walk-steward-policy", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the steward posture face.
    # TODO(D2d-effects-rows): selector for Effects CheckGadget rows
    # TODO(D2d-reviewer-nudge-row): selector for github_comment row
    # TODO(D2d-reviewer-nudge-egress): selector for GITHUB.COM EgressChip
    posture_data = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="room-body"]') ||
                     document.querySelector('.desk-surface-body');
        if (!body) return {
            effectsRows: [], reviewerNudgeRow: null,
            zeroCounters: [], rawBtnCount: 0, hasLocal: false,
        };

        const area = body.querySelector('[data-testid="steward-posture"]') ||
                     body.querySelector('[data-testid="steward-policy"]') ||
                     body;

        /* Effects CheckGadget rows */
        const checkRows = area.querySelectorAll(
            '[data-testid="effect-kind-row"], .check-gadget'
        );
        const effectsRows = [];
        for (const row of checkRows) {
            const lbl = row.querySelector('.check-gadget-label, label');
            const labelText = lbl ? lbl.textContent.trim() : '---';
            const inp = row.querySelector('input[type="checkbox"]');
            const checked = inp ? inp.checked : false;
            const egress = row.querySelector('.gadget-chip-egress');
            const egressText = egress ? egress.textContent.trim() : null;
            effectsRows.push({
                label: labelText, checked, egressChip: egressText,
            });
        }

        /* find the Reviewer nudge / github_comment row */
        let reviewerNudgeRow = null;
        for (const er of effectsRows) {
            if (/reviewer.*nudge|github.comment/i.test(er.label)) {
                reviewerNudgeRow = er;
                break;
            }
        }

        /* defect scans */
        const areaText = area.textContent || '';
        const zeroCounters = [];
        const zcRe = /\\b0\\s+(EFFECT|KIND|RUN|STEP)/g;
        let zcMatch;
        while ((zcMatch = zcRe.exec(areaText)) !== null) {
            zeroCounters.push(zcMatch[0]);
        }
        const hasLocal = areaText.includes('LOCAL');

        const allBtns = area.querySelectorAll('button');
        let rawBtnCount = 0;
        for (const btn of allBtns) {
            if (btn.classList.contains('btn') ||
                btn.classList.contains('desk-mic') ||
                btn.classList.contains('surface-ledger-line') ||
                btn.closest('.desk-traffic') ||
                btn.closest('.desk-wings') ||
                btn.closest('.gadget-string') ||
                btn.closest('.fold-gadget') ||
                btn.closest('.check-gadget') ||
                btn.closest('.cycle-gadget') ||
                btn.closest('.stepper-gadget') ||
                btn.closest('.surface-ledger-row') ||
                btn.closest('[role="tablist"]')) continue;
            rawBtnCount++;
        }

        return {
            effectsRows, reviewerNudgeRow,
            zeroCounters, rawBtnCount, hasLocal,
        };
    }""")

    # ---- record facts ----

    effects = posture_data.get("effectsRows", [])
    report.facts.append(asdict(FaceFact(
        face=face, field="effects_row_count",
        expected="(6 kinds including github_comment)",
        observed=str(len(effects)),
        verdict="DATA",
        why="Effects CheckGadget rows in steward posture",
    )))
    for i, er in enumerate(effects):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"effect_row:{i}",
            expected="(label . checked . egress chip if external)",
            observed=(f"{er.get('label', '---')} . "
                      f"checked={er.get('checked', '---')} . "
                      f"egress={er.get('egressChip', 'none')}"),
            verdict="DATA", why="effect kind row",
        )))

    nudge_row = posture_data.get("reviewerNudgeRow")
    if nudge_row:
        report.facts.append(asdict(FaceFact(
            face=face, field="reviewer_nudge_checked",
            expected="false (github_comment not enabled by default)",
            observed=str(nudge_row.get("checked", "---")),
            verdict="MATCH" if not nudge_row.get("checked") else "DATA",
            why="Reviewer nudge CheckGadget state",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field="reviewer_nudge_egress_chip",
            expected="GITHUB.COM",
            observed=str(nudge_row.get("egressChip", "---")),
            verdict=(
                "MATCH"
                if str(nudge_row.get("egressChip", "")).upper() == "GITHUB.COM"
                else "DATA"
            ),
            why=("EgressChip on Reviewer nudge row "
                 "(Article III: egress where egress happens)"),
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="reviewer_nudge_row",
            expected="(present with GITHUB.COM chip)",
            observed="not found (face may not have landed yet)",
            verdict="DATA", why="Reviewer nudge row not rendered",
        )))

    # defects
    for z in posture_data.get("zeroCounters", []):
        report.defects.append(
            f"STEWARD POSTURE: ZERO COUNTER '{z}' -- UX-CANON A.8"
        )
    if posture_data.get("hasLocal"):
        report.defects.append(
            "STEWARD POSTURE: LOCAL found (should be THIS DEVICE or LAN)"
        )
    if posture_data.get("rawBtnCount", 0) > 0:
        report.defects.append(
            f"STEWARD POSTURE: {posture_data['rawBtnCount']} "
            f"raw <button>(s) outside library"
        )

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

        # D1: zero counter (UX-CANON A.8)
        if re.search(
            r'\b0\s+(NEED|HEALTH|REVIEW|ISSUE|CI|RELEASE|CLAIM|'
            r'EFFECT|THINGS|RECORD|PROPOSAL|DECISION|COMMITMENT|PEOPLE)',
            obs,
        ):
            report.defects.append(
                f"ZERO COUNTER on {fact['face']}/{fact['field']}: "
                f'"{obs}" -- UX-CANON A.8 forbids counters of zero'
            )

        # D2: host chip without scope
        if "host_chip" in fact["field"] and obs and obs != "---":
            has_cloud = (re.search(r'[.][a-z]+$', obs, re.I)
                         and ' ' not in obs)
            has_scope = re.search(
                r'THIS DEVICE|LAN|CLOUD|MESH|PAIRED|GITHUB\.COM', obs, re.I,
            )
            if not has_scope and not has_cloud:
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
        "# HS-173-06 walk facts",
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
    parser = argparse.ArgumentParser(description="HS-173-06 walk runner")
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

    # Print the write guard's decision table
    print("=== WRITE GUARD DECISION TABLE ===")
    for op in ("steward_run", "publish_update", "send_nudge",
               "enable_effect_kind", "save_draft", "unknown"):
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

        # API-only steps (no viewport needed)
        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={token}", wait_until="load")
        page0.wait_for_timeout(2000)

        print("  [1/5] Steward policy (API)...")
        try:
            policy = _step_steward_policy(page0, token, report)
            print(
                f"        done. project={policy.get('project_name', '?')}, "
                f"github_comment={policy.get('github_comment_enabled', '?')}"
            )
        except Exception as exc:
            policy = {}
            print(f"        FAILED: {exc}")
            report.errors.append(f"steward-policy: {exc}")

        print("  [2/5] Room health (API)...")
        try:
            _step_room_health_api(page0, token, report, policy)
            print("        done.")
        except Exception as exc:
            print(f"        FAILED: {exc}")
            report.errors.append(f"room-health-api: {exc}")

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

            # Step 3: Room HEALTH face
            print("  [3/5] Room HEALTH face...")
            try:
                _step_room_health_face(
                    page, out_dir, w, token, report, policy,
                )
                print("        done.")
            except Exception as exc:
                msg = f"room-health-face@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Step 4: Update editor (read-only)
            print("  [4/5] Update editor...")
            try:
                _step_update_editor(
                    page, out_dir, w, token, report, policy,
                )
                print("        done.")
            except Exception as exc:
                msg = f"update-editor@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 5: Steward posture
            print("  [5/5] Steward posture...")
            try:
                _step_steward_posture(
                    page, out_dir, w, token, report, policy,
                )
                print("        done.")
            except Exception as exc:
                msg = f"steward-posture@{w}: {exc}"
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

    print(f"\n=== WALK 173 COMPLETE ===")
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
