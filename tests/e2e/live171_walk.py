"""HS-171-05 PRE-WALK runner: the Heartbeat -- read-mostly walk of the owner's real hub.

Shoots five faces (Rhythm cadence, System shade, Dock badge, Cmd+K deck,
arrival) at 1440x900 and 393x852.  The ONE write: POST /api/settings/heartbeat/run-now
(a sweep of his real Rooms -- reads only, receipted).

THE LIVE LAWS (Article IV -- the walk arms nothing except one receipted sweep):
1. READ-ONLY except run-now.  Never clicks Delete, Import, Generate, or
   any mutating verb beyond the story's one allowed write.
2. NO HARDCODED TOKENS.  The --hub URL (with token) comes from the
   command line; the token never appears in any written file.
3. FACE-DRIVEN.  Opens surfaces via sessionStorage staging.
4. STANDALONE.  Not collected by pytest; run directly via
   `python tests/e2e/live171_walk.py --hub <url>`.

Usage:
  python tests/e2e/live171_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]
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
collect_ignore_glob = ["live171_walk.py"]

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-171-the-heartbeat/assets/story-05-shots"

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
    verdict: str  # MATCH | DATA | BOUNCE
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
    sweep_receipt: dict = field(default_factory=dict)


# ── Helpers ──

def _settle(page: Any) -> None:
    """Wait for CSS animations to finish."""
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
    """Settle, then screenshot the viewport or the surface window."""
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
    assert path.exists() and path.stat().st_size > 1_000, (
        f"Shot {fname} missing or too small"
    )
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
    """Check for raw <button> outside the library inside the active surface window."""
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
    """Build a FaceFact with auto-verdict."""
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


# ── Step 1: GET /api/settings/heartbeat ──

def _step_heartbeat_settings(page: Any, token: str, report: WalkReport) -> None:
    """Read the heartbeat settings via API."""
    face = "heartbeat-settings"
    result = _api(page, "GET", "/api/settings/heartbeat", None, token)
    if result["status"] >= 300:
        report.errors.append(f"GET /api/settings/heartbeat returned {result['status']}")
        report.facts.append(asdict(FaceFact(
            face=face, field="api_status", expected="200",
            observed=str(result["status"]), verdict="BOUNCE",
            why=f"HTTP {result['status']}",
        )))
        return
    payload = result["payload"]
    report.facts.append(asdict(FaceFact(
        face=face, field="api_status", expected="200",
        observed="200", verdict="MATCH", why="ok",
    )))
    # Record the settings fields we can see
    for key in ("sweep_interval_minutes", "quiet_hours_start", "quiet_hours_end",
                "notify_mode", "notify_content", "sweep_enabled"):
        val = payload.get(key, "---")
        report.facts.append(asdict(FaceFact(
            face=face, field=key, expected="(owner's setting)",
            observed=str(val), verdict="DATA", why="real desk content",
        )))


# ── Step 2: Settings -> Rhythm ──

def _step_rhythm(page: Any, out_dir: Path, w: int, token: str,
                 report: WalkReport) -> None:
    """Open Settings -> Rhythm module, shoot, record rows."""
    face = "rhythm"
    # Open the Rhythm window directly (configure-cadence, same as the glass test).
    _open_surface(page, token, "configure-cadence")
    _settle(page)
    page.wait_for_timeout(2000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-rhythm", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Headline: .surface-display[data-testid="rhythm-headline"]
    headline = page.evaluate("""() => {
        const el = document.querySelector('[data-testid="rhythm-headline"]');
        return el ? el.textContent.trim() : '---';
    }""")
    report.facts.append(asdict(_fact(
        face, "headline", "Every 15 min", headline,
    )))

    # SWEEP row: data-testid="rhythm-sweep-row" (SurfaceLedgerRow)
    #   CycleGadget inside .cycle-gadget (the interval picker)
    #   Trailing: "Run now" button data-testid="rhythm-run-now"
    # Sweep fact tokens: data-testid="rhythm-sweep-facts"
    #   QUIET HH:00-HH:00, NEXT HH:MM, LAST HH:MM, N ROOMS, NN MS
    sweep_data = page.evaluate("""() => {
        const row = document.querySelector('[data-testid="rhythm-sweep-row"]');
        const facts = document.querySelector('[data-testid="rhythm-sweep-facts"]');
        return {
            primary: row ? (row.querySelector('.surface-ledger-primary')?.textContent || '').trim() : '---',
            interval: row ? (row.querySelector('.cycle-gadget')?.textContent || '').trim() : '---',
            runNow: row ? (row.querySelector('[data-testid="rhythm-run-now"]')?.textContent || '').trim() : '---',
            facts: facts ? facts.textContent.trim() : '---',
        };
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="sweep_primary", expected="Sweep",
        observed=sweep_data["primary"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="sweep_interval", expected="EVERY 15 MIN",
        observed=sweep_data["interval"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="sweep_run_now", expected="Run now",
        observed=sweep_data["runNow"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="sweep_facts", expected="QUIET HH:00-HH:00 . NEXT HH:MM . LAST HH:MM",
        observed=sweep_data["facts"][:200], verdict="DATA", why="real desk content",
    )))

    # MONDAY BRIEF row: data-testid="rhythm-brief-row"
    #   cell: "DAILY HH:00" token
    #   trailing: "Generate now" data-testid="rhythm-generate-now"
    # Brief fact tokens: data-testid="rhythm-brief-facts"
    #   NEXT MON HH:00, LAST MON DD
    brief_data = page.evaluate("""() => {
        const row = document.querySelector('[data-testid="rhythm-brief-row"]');
        const facts = document.querySelector('[data-testid="rhythm-brief-facts"]');
        return {
            primary: row ? (row.querySelector('.surface-ledger-primary')?.textContent || '').trim() : '---',
            daily: row ? (row.querySelector('.surface-token[data-chip]')?.textContent || '').trim() : '---',
            generateNow: row ? (row.querySelector('[data-testid="rhythm-generate-now"]')?.textContent || '').trim() : '---',
            facts: facts ? facts.textContent.trim() : '---',
        };
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_primary", expected="Monday brief",
        observed=brief_data["primary"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_daily", expected="DAILY 08:00",
        observed=brief_data["daily"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_generate_now", expected="Generate now",
        observed=brief_data["generateNow"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="brief_facts", expected="NEXT MON HH:00 . LAST MON DD",
        observed=brief_data["facts"][:200], verdict="DATA", why="real desk content",
    )))

    # NOTIFY row: data-testid="rhythm-notify-row"
    #   Two CycleGadgets: mode (OFF/ON THE EDGE/EVERY SWEEP), content (COUNT ONLY/ROOM NAMES)
    #   Trailing: HELD token when in quiet hours
    notify_data = page.evaluate("""() => {
        const row = document.querySelector('[data-testid="rhythm-notify-row"]');
        if (!row) return { primary: '---', gadgets: '---', held: false };
        const primary = (row.querySelector('.surface-ledger-primary')?.textContent || '').trim();
        const cycles = row.querySelectorAll('.cycle-gadget');
        const gadgetTexts = [];
        for (const c of cycles) gadgetTexts.push(c.textContent.trim());
        const heldEl = row.querySelector('.surface-token[data-tone="warn"]');
        return {
            primary,
            gadgets: gadgetTexts.join(' | '),
            held: heldEl ? (heldEl.textContent || '').trim() : '',
        };
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="notify_primary", expected="Notify",
        observed=notify_data["primary"], verdict="DATA", why="real desk content",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="notify_gadgets", expected="ON THE EDGE | COUNT ONLY",
        observed=notify_data["gadgets"], verdict="DATA", why="real desk content",
    )))
    if notify_data["held"]:
        report.facts.append(asdict(FaceFact(
            face=face, field="notify_held", expected="HELD (quiet hours)",
            observed=notify_data["held"], verdict="DATA", why="quiet hours active",
        )))

    # Project mute toggles: data-testid="rhythm-mute-toggles"
    #   Each: CheckGadget variant="token" with the project name uppercase
    mute_data = page.evaluate("""() => {
        const container = document.querySelector('[data-testid="rhythm-mute-toggles"]');
        if (!container) return [];
        const gadgets = container.querySelectorAll('.check-gadget');
        const result = [];
        for (const g of gadgets) {
            const label = (g.textContent || '').trim();
            const input = g.querySelector('input[type="checkbox"]');
            const checked = input ? input.checked : null;
            result.push({ label, checked });
        }
        return result;
    }""")
    for i, toggle in enumerate(mute_data):
        status = "enabled" if toggle["checked"] else "muted"
        report.facts.append(asdict(FaceFact(
            face=face, field=f"mute_toggle:{i}",
            expected="(project name) enabled/muted",
            observed=f"{toggle['label']} {status}",
            verdict="DATA", why="real desk content",
        )))

    # Footer: EgressChip + WRITTEN HH:MM
    footer_text = page.evaluate("""() => {
        const footer = document.querySelector('.surface-footer');
        return footer ? footer.textContent.trim() : '---';
    }""")
    written_match = re.search(r'WRITTEN\s+\d{2}:\d{2}', footer_text.upper())
    report.facts.append(asdict(FaceFact(
        face=face, field="footer_written", expected="WRITTEN HH:MM",
        observed=written_match.group(0) if written_match else footer_text[:60],
        verdict="MATCH" if written_match else "DATA",
        why="timestamp found" if written_match else "no WRITTEN timestamp",
    )))

    # Overflow + raw-button checks
    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)
    btn_err = _check_raw_buttons(page, face)
    if btn_err:
        report.errors.append(btn_err)

    _close_surface(page)


# ── Step 3: POST /api/settings/heartbeat/run-now ──

def _step_run_now(page: Any, token: str, report: WalkReport) -> None:
    """The ONE write: trigger a sweep of his real Rooms (reads only, receipted)."""
    face = "sweep"
    result = _api(page, "POST", "/api/settings/heartbeat/run-now", None, token)
    if result["status"] >= 300:
        report.errors.append(f"POST heartbeat/run-now returned {result['status']}")
        report.facts.append(asdict(FaceFact(
            face=face, field="api_status", expected="200",
            observed=str(result["status"]), verdict="BOUNCE",
            why=f"HTTP {result['status']}",
        )))
        return
    receipt = result["payload"]
    report.sweep_receipt = receipt
    report.facts.append(asdict(FaceFact(
        face=face, field="api_status", expected="200",
        observed="200", verdict="MATCH", why="ok",
    )))
    # Record receipt fields
    for key in ("rooms", "watches", "duration_ms", "held", "errors",
                "needs_you_count", "sweep_id"):
        val = receipt.get(key, "---")
        report.facts.append(asdict(FaceFact(
            face=face, field=f"receipt:{key}", expected="(varies)",
            observed=str(val), verdict="DATA", why="real desk content",
        )))


# ── Step 4: System shade ──

def _step_shade(page: Any, out_dir: Path, w: int, token: str,
                report: WalkReport) -> None:
    """Open the system shade, shoot, record PROJECTS + brief rows."""
    face = "shade"
    # The shade opens via the AttentionBell (.desk-bell) in the chrome bar.
    # Its aria-label is "Desk memory: N need attention" or "Desk memory".
    shade_toggle = page.locator('.desk-bell').first
    if shade_toggle.count() > 0 and shade_toggle.is_visible():
        shade_toggle.click()
        page.wait_for_timeout(1500)
        _settle(page)
    else:
        report.surprises.append(f"SHADE: .desk-bell not found at {w}")

    shot = _shoot(page, out_dir, "walk-shade", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # PROJECTS section: aria-label="Projects", data-testid="shade-projects"
    # Project rows: data-testid="shade-project-row", .is-muted for muted
    # Brief row: data-testid="shade-brief-row"
    projects_data = page.evaluate("""() => {
        const section = document.querySelector('[data-testid="shade-projects"]');
        if (!section) return { caption: '---', rows: [], briefRow: '---' };

        // Caption: the <h4> inside the section ("Projects · N NEED YOU")
        const h4 = section.querySelector('h4');
        const caption = h4 ? h4.textContent.trim() : '---';

        // Project rows: data-testid="shade-project-row"
        const rowEls = section.querySelectorAll('[data-testid="shade-project-row"]');
        const rows = [];
        for (const row of rowEls) {
            const name = (row.querySelector('strong')?.textContent || '').trim();
            const token = (row.querySelector('.surface-token[data-chip]')?.textContent || '').trim();
            const why = (row.querySelector('.desk-shade-why')?.textContent || '').trim();
            const isMuted = row.classList.contains('is-muted');
            const verb = (row.querySelector('.btn')?.textContent || '').trim();
            rows.push({ name, token, why, muted: isMuted, verb });
        }

        // Brief row: data-testid="shade-brief-row"
        const briefEl = section.querySelector('[data-testid="shade-brief-row"]');
        let briefRow = '---';
        if (briefEl) {
            const bName = (briefEl.querySelector('strong')?.textContent || '').trim();
            const bToken = (briefEl.querySelector('.surface-token[data-chip]')?.textContent || '').trim();
            const bDate = (briefEl.querySelector('.desk-shade-why')?.textContent || '').trim();
            const bVerb = (briefEl.querySelector('.btn')?.textContent || '').trim();
            briefRow = [bName, bToken, bDate, bVerb].filter(Boolean).join(' ');
        }

        return { caption, rows, briefRow };
    }""")

    report.facts.append(asdict(FaceFact(
        face=face, field="projects_caption",
        expected="PROJECTS . N NEED YOU",
        observed=projects_data["caption"],
        verdict="DATA", why="real desk content",
    )))

    for i, row in enumerate(projects_data["rows"]):
        muted_tag = " [MUTED]" if row.get("muted") else ""
        observed = f"{row['name']} | {row['token']} | {row['why']} | {row['verb']}{muted_tag}"
        report.facts.append(asdict(FaceFact(
            face=face, field=f"project_row:{i}",
            expected="(name + count + WHY + Open)",
            observed=observed,
            verdict="DATA", why="real desk content",
        )))

    report.facts.append(asdict(FaceFact(
        face=face, field="brief_row",
        expected="Monday brief N THINGS SEP NN Open",
        observed=projects_data["briefRow"],
        verdict="DATA", why="real desk content",
    )))

    # Count muted rows separately for the report
    muted_rows = [r for r in projects_data["rows"] if r.get("muted")]
    if muted_rows:
        report.facts.append(asdict(FaceFact(
            face=face, field="muted_count",
            expected="(varies)",
            observed=str(len(muted_rows)),
            verdict="DATA", why="muted projects in shade",
        )))

    # Close shade
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    _settle(page)


# ── Step 5: Dock badge ──

def _step_dock_badge(page: Any, out_dir: Path, w: int,
                     report: WalkReport) -> None:
    """Read and shoot the dock badge count."""
    face = "dock"
    # Read the badge
    badge_data = page.evaluate("""() => {
        const badges = document.querySelectorAll('.desk-dock-badge');
        const result = [];
        for (const b of badges) {
            result.push({
                text: (b.textContent || '').trim(),
                tone: b.getAttribute('data-tone') || '',
            });
        }
        return result;
    }""")

    badge_text = ""
    if badge_data:
        badge_text = ", ".join(f"{b['text']}" + (f" (tone={b['tone']})" if b["tone"] else "")
                               for b in badge_data)
    report.facts.append(asdict(FaceFact(
        face=face, field="badge_count",
        expected="(aggregate needs-you count or absent)",
        observed=badge_text if badge_text else "absent",
        verdict="DATA", why="real desk content",
    )))

    # Shoot the dock area
    shot = _shoot(page, out_dir, "walk-dock", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})


# ── Step 6: Cmd+K command deck ──

def _step_command_deck(page: Any, out_dir: Path, w: int,
                       report: WalkReport) -> None:
    """Open Cmd+K, shoot with empty query, record PROJECTS group."""
    face = "command-deck"
    # Open the command deck via keyboard
    page.keyboard.press("Meta+k")
    page.wait_for_timeout(1000)
    _settle(page)

    shot = _shoot(page, out_dir, "walk-command-deck", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Read the deck's grouped rows.
    # Structure: #desk-palette-listbox > li > .desk-deck-band (group caption)
    #            #desk-palette-listbox > li > .desk-deck-row (entry)
    #   inside each .desk-deck-row: .desk-deck-label, .desk-deck-badge
    #   (needs-you count chip, HS-171-07), .desk-deck-kind
    deck_data = page.evaluate("""() => {
        const list = document.getElementById('desk-palette-listbox');
        if (!list) return { groups: {} };
        const groups = {};
        let currentGroup = '';
        for (const li of list.children) {
            const band = li.querySelector('.desk-deck-band');
            if (band) {
                currentGroup = band.textContent.trim();
                if (!groups[currentGroup]) groups[currentGroup] = [];
                continue;
            }
            const row = li.querySelector('.desk-deck-row');
            if (!row) continue;
            if (!groups[currentGroup]) groups[currentGroup] = [];
            const label = (row.querySelector('.desk-deck-label')?.textContent || '').trim();
            const badge = (row.querySelector('.desk-deck-badge')?.textContent || '').trim();
            const kind = (row.querySelector('.desk-deck-kind')?.textContent || '').trim();
            groups[currentGroup].push({ label, badge, kind });
        }
        return { groups };
    }""")

    groups = deck_data.get("groups", {})
    projects_group = groups.get("PROJECTS", groups.get("Projects", []))
    report.facts.append(asdict(FaceFact(
        face=face, field="projects_group_count",
        expected="(N project entries)",
        observed=str(len(projects_group)),
        verdict="DATA", why="real desk content",
    )))
    for i, entry in enumerate(projects_group):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"project:{i}",
            expected="Open <name> | N NEED(S) YOU | PROJECT",
            observed=f"{entry['label']} | {entry['badge']} | {entry['kind']}",
            verdict="DATA", why="real desk content",
        )))

    # Record all group names
    all_groups = list(groups.keys())
    report.facts.append(asdict(FaceFact(
        face=face, field="groups",
        expected="PROJECTS, VERBS, PROGRAMS, ...",
        observed=", ".join(all_groups) if all_groups else "---",
        verdict="DATA", why="real desk content",
    )))

    # Close the deck
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    _settle(page)


# ── Step 7: Notification receipts ──

def _step_notification_receipts(page: Any, token: str,
                                report: WalkReport) -> None:
    """Read heartbeat.notify receipts from the API if a route exists."""
    face = "notification"
    # Try pipeline_events for heartbeat.notify receipts
    result = _api(page, "GET", "/api/pipeline-events?kind=heartbeat.notify&limit=5",
                  None, token)
    if result["status"] == 200:
        payload = result["payload"]
        events = payload if isinstance(payload, list) else payload.get("events", payload.get("items", []))
        report.facts.append(asdict(FaceFact(
            face=face, field="receipt_count",
            expected="(varies)",
            observed=str(len(events)),
            verdict="DATA", why="real desk content",
        )))
        for i, ev in enumerate(events[:3]):
            summary = str(ev)[:150] if isinstance(ev, dict) else str(ev)[:150]
            report.facts.append(asdict(FaceFact(
                face=face, field=f"receipt:{i}",
                expected="(heartbeat.notify receipt)",
                observed=summary,
                verdict="DATA", why="real desk content",
            )))
    elif result["status"] == 404:
        report.facts.append(asdict(FaceFact(
            face=face, field="pipeline_events_route",
            expected="200",
            observed="404 -- seam not wired yet",
            verdict="DATA", why="route not found",
        )))
    else:
        report.facts.append(asdict(FaceFact(
            face=face, field="pipeline_events_route",
            expected="200",
            observed=f"HTTP {result['status']}",
            verdict="DATA", why=f"unexpected status",
        )))

    # Check if a banner should be expected
    # Read the aggregate count from the sweep receipt
    sweep_count = report.sweep_receipt.get("needs_you_count", 0)
    if isinstance(sweep_count, int) and sweep_count > 0:
        # Check quiet hours from settings
        settings_facts = [f for f in report.facts if f["face"] == "heartbeat-settings"]
        quiet_start = next((f["observed"] for f in settings_facts
                           if f["field"] == "quiet_hours_start"), "22:00")
        quiet_end = next((f["observed"] for f in settings_facts
                         if f["field"] == "quiet_hours_end"), "08:00")
        now_hour = datetime.now().hour
        # Simple quiet-hours check (assumes HH:MM format)
        try:
            qs = int(quiet_start.split(":")[0]) if ":" in str(quiet_start) else 22
            qe = int(quiet_end.split(":")[0]) if ":" in str(quiet_end) else 8
            in_quiet = (qs > qe and (now_hour >= qs or now_hour < qe)) or \
                       (qs <= qe and qs <= now_hour < qe)
        except (ValueError, TypeError):
            in_quiet = False

        if in_quiet:
            report.facts.append(asdict(FaceFact(
                face=face, field="banner_expectation",
                expected="HELD (quiet hours)",
                observed=f"quiet hours active ({quiet_start}-{quiet_end}), count={sweep_count}",
                verdict="DATA", why="notification held during quiet hours",
            )))
        else:
            report.facts.append(asdict(FaceFact(
                face=face, field="banner_expectation",
                expected="EXPECT A BANNER ON HIS SCREEN",
                observed=f"count={sweep_count}, outside quiet hours",
                verdict="DATA", why="EXPECT A BANNER ON HIS SCREEN",
            )))


# ── Defect detection ──

def _detect_defects(report: WalkReport) -> None:
    """Scan observed facts for real-desk defects."""
    seen: set[tuple[str, str]] = set()
    for fact in report.facts:
        key = (fact["face"], fact["field"])
        if key in seen:
            continue
        seen.add(key)
        obs = fact["observed"]

        # D1: a "0" counter anywhere (UX-CANON A.8)
        if re.search(r'\b0\s+(NEED|THINGS|RECORD|LOOP|ENGINE|GROUP|WATCH)', obs):
            report.defects.append(
                f"ZERO COUNTER on {fact['face']}/{fact['field']}: \"{obs}\" "
                f"-- UX-CANON A.8 forbids counters of zero"
            )

        # D2: a sentence in the shade (UX-CANON A.3)
        if fact["face"] == "shade" and "row" in fact["field"]:
            if len(obs) > 60 and obs.count(" ") > 8 and obs.endswith("."):
                report.defects.append(
                    f"PROSE in shade {fact['field']}: \"{obs[:60]}...\" "
                    f"-- UX-CANON A.3 forbids sentences"
                )

    # D3: caption count != badge count != notification count
    # Extract counts from facts
    shade_caption = next(
        (f["observed"] for f in report.facts
         if f["face"] == "shade" and f["field"] == "projects_caption"),
        "",
    )
    badge_obs = next(
        (f["observed"] for f in report.facts
         if f["face"] == "dock" and f["field"] == "badge_count"),
        "",
    )
    # Extract numbers
    shade_nums = re.findall(r'\d+', shade_caption)
    badge_nums = re.findall(r'\d+', badge_obs)
    shade_count = int(shade_nums[0]) if shade_nums else None
    badge_count = int(badge_nums[0]) if badge_nums else None
    if shade_count is not None and badge_count is not None and shade_count != badge_count:
        report.defects.append(
            f"COUNT MISMATCH: shade caption has {shade_count}, "
            f"dock badge has {badge_count} -- must be ONE count everywhere"
        )

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
        "# HS-171-05 walk facts",
        "",
        f"Generated: {report.generated_at}",
        f"Hub: {report.hub_host}",
        "",
    ]

    # Group facts by face
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

    if report.sweep_receipt:
        lines.append("## Sweep receipt")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(report.sweep_receipt, indent=2))
        lines.append("```")
        lines.append("")

    if report.shots:
        lines.append("## Shots")
        lines.append("")
        for s in report.shots:
            lines.append(f"- {s['face']} @ {s['width']}: `{Path(s['path']).name}`")
        lines.append("")

    if report.errors:
        lines.append("## Errors (BOUNCE)")
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
    parser = argparse.ArgumentParser(description="HS-171-05 pre-walk runner")
    parser.add_argument("--hub", required=True,
                        help="Hub URL with token")
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

        # Step 1: heartbeat settings (API only, no viewport needed)
        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={token}", wait_until="load")
        page0.wait_for_timeout(2000)
        print("  [1/7] Heartbeat settings (API)...")
        try:
            _step_heartbeat_settings(page0, token, report)
            print("        done.")
        except Exception as exc:
            msg = f"heartbeat-settings: {exc}"
            print(f"        FAILED: {msg}")
            report.errors.append(msg)

        # Step 3: run-now (API, before viewport loop so shade sees results)
        print("  [3/7] Run now (sweep)...")
        try:
            _step_run_now(page0, token, report)
            print("        done.")
        except Exception as exc:
            msg = f"run-now: {exc}"
            print(f"        FAILED: {msg}")
            report.errors.append(msg)
            errors_fatal.append(msg)

        page0.close()

        # Viewport loop for face steps
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

            # Step 2: Rhythm
            print(f"  [2/7] Rhythm...")
            try:
                _step_rhythm(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"rhythm@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Step 4: Shade
            print(f"  [4/7] Shade...")
            try:
                _step_shade(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"shade@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Step 5: Dock badge
            print(f"  [5/7] Dock badge...")
            try:
                _step_dock_badge(page, out_dir, w, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"dock@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Step 6: Cmd+K
            print(f"  [6/7] Command deck...")
            try:
                _step_command_deck(page, out_dir, w, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"command-deck@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # Collect page errors
            critical = [e for e in page_errors if "ResizeObserver" not in e]
            if critical:
                report.errors.extend([f"JS@{w}: {e}" for e in critical])

            page.close()

        # Step 7: Notification receipts (API only)
        print("\n  [7/7] Notification receipts...")
        page7 = browser.new_page(viewport={"width": 1440, "height": 900})
        page7.goto(f"{base_url}/?token={token}", wait_until="load")
        page7.wait_for_timeout(1000)
        try:
            _step_notification_receipts(page7, token, report)
            print("        done.")
        except Exception as exc:
            msg = f"notification-receipts: {exc}"
            print(f"        FAILED: {msg}")
            report.errors.append(msg)
        page7.close()

        browser.close()

    _detect_defects(report)

    json_path = _write_facts_json(report, out_dir)
    md_path = _write_facts_md(report, out_dir)

    print(f"\n=== WALK 171 COMPLETE ===")
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
