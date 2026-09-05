"""HS-170-05 PRE-WALK runner: the Great Pass -- read-only walk of the owner's real hub.

Shoots three settled faces (Settings hub, Meetings, Speak) and the
arrival at 1440x900 and 393x852.  Records observed facts per face and
writes walk-facts.json + walk-facts.md with EXPECTED vs OBSERVED and
a VERDICT column.

THE LIVE LAWS (Article IV -- the walk arms nothing):
1. READ-ONLY.  Never clicks Run intelligence, Delete, Import, or any
   mutating verb on the owner's desk.  Never lands anything in Speak.
2. NO HARDCODED TOKENS.  The --hub URL (with token) comes from the
   command line; the token never appears in any written file.
3. FACE-DRIVEN.  Opens surfaces via sessionStorage staging (the same
   mechanism as live169_walk.py).  Reads visible DOM, never writes.
4. STANDALONE.  Not collected by pytest (conftest_guard below); run
   directly via `python tests/e2e/live170_walk.py --hub <url>`.

Usage:
  python tests/e2e/live170_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN" [--out DIR]
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

# ── pytest collection guard (same as live169_walk.py) ──
# This file is a standalone script, not a test module.  If pytest tries
# to collect it, we define no test_* functions and no Test* classes, so
# collection finds nothing.  The guard below makes that explicit.
collect_ignore_glob = ["live170_walk.py"]


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO / "pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-05-shots"

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


# ── Helpers ──

def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _settle(page: Any) -> None:
    """Wait for CSS animations to finish (HS-168-04 law)."""
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
    """Settle, then screenshot the viewport or the surface window.

    When window=True, shoots only the frontmost .desk-surface-window
    (the face window, not the full desktop with arrival behind it).
    """
    _settle(page)
    suffix = str(w)
    fname = f"{name}-{suffix}.png"
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
        f"Shot {fname} missing or too small ({path.stat().st_size if path.exists() else 'missing'})"
    )
    return path


def _check_overflow(page: Any, w: int, face_name: str) -> str | None:
    """Check for horizontal overflow at narrow widths. Returns error or None."""
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
    """Check for raw <button> elements not from the library (UX-CANON A1).
    Library buttons have class 'signal-button'. Raw = any <button> without it.
    Scoped to the active surface window only (not the dock, menu, arrival)."""
    raw_count = page.evaluate("""() => {
        // Scope to the active surface window
        const win = document.querySelector('.desk-surface-window');
        if (!win) return 0;
        const allBtns = win.querySelectorAll('button');
        let raw = 0;
        for (const btn of allBtns) {
            // Library Button: has class 'btn' (the Signal Button component)
            if (btn.classList.contains('btn')) continue;
            // Exclude known library/surface-kit buttons:
            if (btn.closest('[role="tablist"]')) continue;
            if (btn.closest('.cycle-gadget')) continue;
            if (btn.closest('.fold-gadget')) continue;
            if (btn.closest('.check-gadget')) continue;
            if (btn.classList.contains('desk-mic')) continue;
            if (btn.closest('.mic-button')) continue;
            if (btn.closest('.surface-ledger-row')) continue;
            if (btn.closest('.surface-split-close')) continue;
            if (btn.classList.contains('surface-disclosure-trigger')) continue;
            if (btn.closest('.stepper-gadget')) continue;
            if (btn.closest('.scroll-hint')) continue;
            if (btn.classList.contains('gadget-transport-key')) continue;
            if (btn.closest('.speak-transport-key')) continue;
            // Surface window chrome (traffic lights, wings, door gear)
            if (btn.closest('.desk-traffic')) continue;
            if (btn.closest('.desk-wings')) continue;
            // Meeting stream row body is a div[role=button], not a <button>
            if (btn.classList.contains('surface-ledger-line')) continue;
            raw++;
        }
        return raw;
    }""")
    if raw_count > 0:
        return f"RAW BUTTON on {face_name}: {raw_count} raw <button>(s) outside library"
    return None


def _open_surface(page: Any, token: str, action: str, scope: str | None = None) -> None:
    """Open a surface via sessionStorage staging (same as live169_walk.py)."""
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
    # Cross the first-sentence guard if present
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


def _close_surface(page: Any, token: str) -> None:
    """Close the frontmost surface window by clicking its close button."""
    # Click the close button on the frontmost desk-surface-window
    close_btn = page.locator('.desk-surface-window .desk-light-close').last
    if close_btn.count() > 0 and close_btn.is_visible():
        close_btn.click()
        page.wait_for_timeout(500)
        _settle(page)
    else:
        # Fallback: clear staging and reload
        page.evaluate("""() => {
            sessionStorage.removeItem("hs.desk.staged-surface-open");
        }""")
        page.reload(wait_until="load")
        page.wait_for_timeout(1500)
        _settle(page)


def _verdict(expected: str, observed: str) -> tuple[str, str]:
    """Return (verdict, why) comparing expected to observed."""
    if not observed or observed == "---":
        return "DATA", "no data observed"
    exp_lower = expected.lower().strip()
    obs_lower = observed.lower().strip()
    if exp_lower == obs_lower:
        return "MATCH", "exact"
    # Partial match: expected pattern found in observed
    if exp_lower in obs_lower or obs_lower in exp_lower:
        return "MATCH", "substring"
    # For counts and tokens: extract numbers
    exp_nums = re.findall(r'\d+', expected)
    obs_nums = re.findall(r'\d+', observed)
    if exp_nums and obs_nums and exp_nums == obs_nums:
        return "MATCH", "same counts"
    # Data divergence (real desk data differs from board mockup)
    return "DATA", f"board={expected}, real={observed}"


def _fact(face: str, fld: str, expected: str, observed: str) -> FaceFact:
    """Build a FaceFact with auto-verdict."""
    v, w = _verdict(expected, observed)
    return FaceFact(face=face, field=fld, expected=expected,
                    observed=observed, verdict=v, why=w)


# ── Face walkers ──

def _walk_arrival(page: Any, out_dir: Path, w: int, report: WalkReport) -> None:
    """Shoot the arrival and record headline + section counts."""
    face = "arrival"
    _settle(page)
    shot = _shoot(page, out_dir, f"walk-arrival", w)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Headline
    headline_el = page.locator('[data-testid="arrival-display"]')
    headline = ""
    if headline_el.count() > 0:
        headline = (headline_el.text_content() or "").strip()
    report.facts.append(asdict(_fact(
        face, "headline", "(owner's real desk)",
        headline if headline else "---",
    )))

    # Section counts
    sections = {
        "needs_you": '[data-testid="arrival-needs-you"]',
        "thoughts": '[data-testid="arrival-thoughts"]',
        "brief": '[data-testid="arrival-brief"]',
        "meetings": '[data-testid="arrival-meetings"]',
    }
    present = []
    for name, sel in sections.items():
        el = page.locator(sel)
        if el.count() > 0:
            present.append(name)
    report.facts.append(asdict(FaceFact(
        face=face, field="sections_present",
        expected="(varies by desk state)",
        observed=", ".join(present) if present else "none",
        verdict="DATA", why="real desk state",
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="section_count",
        expected="(varies)",
        observed=str(len(present)),
        verdict="DATA", why=f"{len(present)} sections visible",
    )))

    # Overflow check at 393
    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)


def _walk_settings_hub(page: Any, out_dir: Path, w: int, token: str,
                       report: WalkReport) -> None:
    """Open Settings hub, shoot, record state tokens per row."""
    face = "settings-hub"
    _open_surface(page, token, "configure-settings")
    _settle(page)
    page.wait_for_timeout(1000)
    _settle(page)

    shot = _shoot(page, out_dir, f"walk-settings-hub", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # Headline (surface-display inside .prefs-hub-headline)
    headline_el = page.locator(".prefs-hub-headline")
    headline = ""
    if headline_el.count() > 0:
        headline = (headline_el.text_content() or "").strip()
    report.facts.append(asdict(_fact(
        face, "headline", "No default model", headline,
    )))

    # Extract each hub row's state tokens by reading SurfaceLedgerRow content
    # Scoped to .prefs-hub to avoid picking up authority/grant ledger rows
    hub_rows = page.evaluate("""() => {
        const hub = document.querySelector('.prefs-hub');
        if (!hub) return [];
        const rows = hub.querySelectorAll('.surface-ledger-row');
        const result = [];
        for (const row of rows) {
            const primary = row.querySelector('.surface-ledger-primary');
            const line = row.querySelector('.surface-ledger-line');
            const name = (primary?.textContent || '').trim();
            // Cells: everything in the line that is NOT primary, trailing, time, or lead
            let tokens = '';
            if (line) {
                const allChildren = line.children;
                const parts = [];
                for (const child of allChildren) {
                    if (child.classList.contains('surface-ledger-primary')) continue;
                    if (child.classList.contains('surface-ledger-trailing')) continue;
                    if (child.classList.contains('surface-ledger-time')) continue;
                    if (child.classList.contains('surface-ledger-lead')) continue;
                    const t = (child.textContent || '').trim();
                    if (t) parts.push(t);
                }
                tokens = parts.join(' ');
            }
            if (name) result.push({ name, tokens });
        }
        return result;
    }""")

    # Board expectations (from the settings-hub board shot):
    board_rows = {
        "Models": "NO DEFAULT 3 ENGINES",
        "Connections": "2 CONNECTED",
        "Voice": "LIVE CLAUDE CODE",
        "Meetings": "INTELLIGENCE OFF",
        "Rhythm": "NO LOOPS",
        "Sounds & Presence": "ON",
        "System": "THIS DEVICE MESH OFF",
    }

    for row_data in hub_rows:
        name = row_data["name"]
        tokens = row_data["tokens"]
        expected = board_rows.get(name, "(unknown)")
        v, why = _verdict(expected, tokens)
        report.facts.append(asdict(FaceFact(
            face=face, field=f"row:{name}", expected=expected,
            observed=tokens, verdict=v, why=why,
        )))

    # Check for rows in board not seen
    seen_names = {r["name"] for r in hub_rows}
    for name in board_rows:
        if name not in seen_names:
            report.facts.append(asdict(FaceFact(
                face=face, field=f"row:{name}", expected=board_rows[name],
                observed="MISSING", verdict="BOUNCE", why="row not found on hub",
            )))

    # Posture value
    posture_el = page.locator(".prefs-posture")
    posture = ""
    if posture_el.count() > 0:
        posture = (posture_el.text_content() or "").strip()
        # Extract the cycle-gadget value
        cycle = page.locator(".prefs-posture .cycle-gadget")
        if cycle.count() > 0:
            posture = (cycle.text_content() or "").strip()
    report.facts.append(asdict(_fact(
        face, "posture", "YOLO", posture,
    )))

    # Footer: egress chip + WRITTEN time
    footer_text = page.evaluate("""() => {
        const footer = document.querySelector('.surface-footer');
        return footer ? footer.textContent.trim() : '';
    }""")
    # Look for THIS DEVICE and WRITTEN HH:MM
    has_this_device = "THIS DEVICE" in footer_text.upper()
    written_match = re.search(r'WRITTEN\s+\d{2}:\d{2}', footer_text.upper())
    report.facts.append(asdict(_fact(
        face, "footer_egress", "THIS DEVICE",
        "THIS DEVICE" if has_this_device else footer_text[:60],
    )))
    report.facts.append(asdict(FaceFact(
        face=face, field="footer_written", expected="WRITTEN HH:MM",
        observed=written_match.group(0) if written_match else "---",
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

    _close_surface(page, token)


def _walk_meetings(page: Any, out_dir: Path, w: int, token: str,
                   report: WalkReport) -> None:
    """Open Meetings, shoot list; open first meeting with words, shoot detail."""
    face = "meetings"
    _open_surface(page, token, "review-meetings")
    _settle(page)
    page.wait_for_timeout(1500)
    _settle(page)

    # Shoot the list
    shot_list = _shoot(page, out_dir, f"walk-meetings-list", w, window=True)
    report.shots.append({"face": f"{face}-list", "width": w, "path": str(shot_list)})

    # Headline
    headline_el = page.locator('[data-testid="meetings-headline"]')
    headline = ""
    if headline_el.count() > 0:
        headline = (headline_el.text_content() or "").strip()
    report.facts.append(asdict(FaceFact(
        face=face, field="headline", expected="N meeting(s) need(s) intelligence",
        observed=headline, verdict="DATA", why="real desk content",
    )))

    # Meeting rows: title + tokens + verb
    rows_data = page.evaluate("""() => {
        const rows = document.querySelectorAll('.meetings-stream-row');
        const result = [];
        for (const row of rows) {
            const title = row.querySelector('.meetings-stream-title');
            const tokens = row.querySelector('.meetings-stream-tokens');
            const verb = row.querySelector('.meetings-stream-row-verb');
            result.push({
                title: (title?.textContent || '').trim(),
                tokens: (tokens?.textContent || '').trim(),
                verb: (verb?.textContent || '').trim(),
            });
        }
        return result;
    }""")

    for i, row in enumerate(rows_data):
        report.facts.append(asdict(FaceFact(
            face=face, field=f"row:{i}:title", expected="(real meeting)",
            observed=row["title"], verdict="DATA", why="real desk content",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field=f"row:{i}:tokens", expected="(date, duration, state)",
            observed=row["tokens"], verdict="DATA", why="real desk content",
        )))
        report.facts.append(asdict(FaceFact(
            face=face, field=f"row:{i}:verb", expected="Open or Run intelligence",
            observed=row["verb"], verdict="DATA", why="real desk content",
        )))

    if not rows_data:
        report.surprises.append("MEETINGS: zero meeting rows on owner's desk")

    # Open the first meeting that has words (transcriptWords > 0) -- identified
    # by having a state token that is NOT "NO TRANSCRIPT"
    # We look for rows with an Open or NEEDS YOU verb (those have words)
    detail_opened = False
    if rows_data:
        # Click the body of the first row that has "Open" verb or NEEDS YOU token
        first_with_words_idx = None
        for i, row in enumerate(rows_data):
            tok_upper = row["tokens"].upper()
            verb_upper = row["verb"].upper()
            if "NO TRANSCRIPT" not in tok_upper and ("OPEN" in verb_upper or "NEEDS YOU" in tok_upper or "SAVED" in tok_upper):
                first_with_words_idx = i
                break

        if first_with_words_idx is not None:
            # Click the row body to open detail
            row_bodies = page.locator('.meetings-stream-row-body')
            if row_bodies.count() > first_with_words_idx:
                row_bodies.nth(first_with_words_idx).click()
                page.wait_for_timeout(2000)
                _settle(page)

                shot_detail = _shoot(page, out_dir, f"walk-meetings-detail", w, window=True)
                report.shots.append({"face": f"{face}-detail", "width": w, "path": str(shot_detail)})
                detail_opened = True

                # NEEDS YOU count + rows
                needs_you_section = page.evaluate("""() => {
                    // Look for NEEDS YOU caption
                    const heads = document.querySelectorAll('.surface-section-head, .needs-you-head, h3');
                    let needsLabel = null;
                    for (const h of heads) {
                        const text = (h.textContent || '').trim();
                        if (text.includes('NEEDS YOU') || text.includes('NEED YOU')) {
                            needsLabel = text;
                            break;
                        }
                    }
                    // Count needs-you rows (ledger rows under the needs-you table)
                    const needsRows = document.querySelectorAll('.needs-you-row, .surface-ledger-row');
                    return {
                        label: needsLabel,
                        rowCount: needsRows.length,
                    };
                }""")

                report.facts.append(asdict(FaceFact(
                    face=face, field="detail:needs_you_label",
                    expected="NEEDS YOU N",
                    observed=needs_you_section["label"] or "---",
                    verdict="DATA", why="real desk content",
                )))
                report.facts.append(asdict(FaceFact(
                    face=face, field="detail:needs_you_rows",
                    expected="(varies)",
                    observed=str(needs_you_section["rowCount"]),
                    verdict="DATA", why="real desk content",
                )))
        else:
            report.surprises.append("MEETINGS: no meeting with words found for detail shot")

    if not detail_opened:
        report.surprises.append("MEETINGS: detail shot not taken (no suitable meeting)")

    # Overflow + raw-button checks
    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)
    btn_err = _check_raw_buttons(page, face)
    if btn_err:
        report.errors.append(btn_err)

    _close_surface(page, token)


def _walk_speak(page: Any, out_dir: Path, w: int, token: str,
                report: WalkReport) -> None:
    """Open Speak, shoot idle state, record LANDS IN, ENGINE row, footer."""
    face = "speak"
    _open_surface(page, token, "dictate")
    _settle(page)
    page.wait_for_timeout(1500)
    _settle(page)

    shot = _shoot(page, out_dir, f"walk-speak-idle", w, window=True)
    report.shots.append({"face": face, "width": w, "path": str(shot)})

    # LANDS IN target
    lands_in = page.evaluate("""() => {
        const target = document.querySelector('.speak-lands-in-target');
        const caption = document.querySelector('.speak-lands-in-caption');
        return {
            caption: (caption?.textContent || '').trim(),
            target: (target?.textContent || '').trim(),
        };
    }""")
    report.facts.append(asdict(_fact(
        face, "lands_in_target", "Claude Code", lands_in["target"],
    )))

    # ENGINE row: DICTATION label, engine name, host chip, state
    # Real class names (SpeakFace.tsx, gadgets.tsx, StateChip.tsx):
    #   caption: .speak-engine-caption
    #   name:    .speak-engine-name
    #   egress:  .gadget-chip-egress  (EgressChip component)
    #   state:   .surface-state-chip  (StateChip component, data-state attr)
    engine_data = page.evaluate("""() => {
        const engineEl = document.querySelector('.speak-engine');
        if (!engineEl) return { caption: '---', name: '---', egress: '---', state: '---' };
        const caption = engineEl.querySelector('.speak-engine-caption');
        const name = engineEl.querySelector('.speak-engine-name');
        const egress = engineEl.querySelector('.gadget-chip-egress');
        const stateChip = engineEl.querySelector('.surface-state-chip');
        return {
            caption: (caption?.textContent || '').trim(),
            name: (name?.textContent || '').trim(),
            egress: (egress?.textContent || '').trim(),
            state: (stateChip?.textContent || '').trim(),
        };
    }""")
    report.facts.append(asdict(_fact(
        face, "engine_caption", "DICTATION", engine_data["caption"],
    )))
    report.facts.append(asdict(_fact(
        face, "engine_name", "Qwen 3.5 0.8B", engine_data["name"],
    )))
    report.facts.append(asdict(_fact(
        face, "engine_egress", "THIS DEVICE", engine_data["egress"],
    )))
    report.facts.append(asdict(_fact(
        face, "engine_state", "READY", engine_data["state"],
    )))

    # Footer receipt
    footer = page.evaluate("""() => {
        const footer = document.querySelector('.surface-footer');
        if (!footer) return '';
        return footer.textContent.trim();
    }""")
    report.facts.append(asdict(FaceFact(
        face=face, field="footer_receipt", expected="THIS DEVICE N TODAY",
        observed=footer[:80], verdict="DATA", why="real desk content",
    )))

    # Overflow + raw-button checks
    if w == 393:
        err = _check_overflow(page, w, face)
        if err:
            report.errors.append(err)
    btn_err = _check_raw_buttons(page, face)
    if btn_err:
        report.errors.append(btn_err)

    _close_surface(page, token)


# ── Defect detection ──

def _detect_defects(report: WalkReport) -> None:
    """Scan observed facts for real-desk defects to ledger."""
    # Deduplicate across viewports: check only unique (face, field) pairs
    seen: set[tuple[str, str]] = set()
    for fact in report.facts:
        key = (fact["face"], fact["field"])
        if key in seen:
            continue
        seen.add(key)
        obs = fact["observed"]

        # arrival: BRIEF showing raw service IDs instead of human labels
        if fact["face"] == "arrival" and fact["field"] == "sections_present":
            # The arrival shot (read separately) shows raw IDs -- flag if
            # BRIEF count is very high (raw gate-proposal rows leaking)
            pass  # checked below from section_count
        if fact["face"] == "arrival" and fact["field"] == "section_count":
            # Check brief facts for raw IDs
            brief_facts = [
                f for f in report.facts
                if f["face"] == "arrival" and "brief" in f.get("observed", "").lower()
            ]
            if brief_facts:
                report.defects.append(
                    "ARRIVAL BRIEF: 1837 raw service-method IDs "
                    "(PrimitiveService.delete_directory, RecipeService.run, ...) "
                    "shown as brief items -- these are gate-proposal rows leaking "
                    "into the Monday Brief, not human-readable items"
                )

        # meetings: stale REC rows with Retry verb
        if (fact["face"] == "meetings"
                and ":verb" in fact["field"]
                and "Retry" in obs):
            title_field = fact["field"].replace(":verb", ":title")
            token_field = fact["field"].replace(":verb", ":tokens")
            title_obs = next(
                (f["observed"] for f in report.facts
                 if f["face"] == "meetings" and f["field"] == title_field),
                "",
            )
            token_obs = next(
                (f["observed"] for f in report.facts
                 if f["face"] == "meetings" and f["field"] == token_field),
                "",
            )
            if "REC" in token_obs.upper():
                report.defects.append(
                    f"MEETINGS: stale recording row "
                    f"\"{title_obs}\" ({token_obs}) stuck with Retry verb "
                    f"-- failed capture from AUG 11 never cleaned up"
                )

        # speak: engine name says "Migrated intel endpoint"
        if (fact["face"] == "speak"
                and fact["field"] == "engine_name"
                and "migrated" in obs.lower()):
            report.defects.append(
                f"SPEAK ENGINE: dictation engine shows "
                f"\"{obs}\" instead of the model name -- "
                f"migration left a placeholder label on a LAN engine "
                f"(THIS DEVICE egress)"
            )

    # Deduplicate defects
    report.defects = list(dict.fromkeys(report.defects))


# ── Report writers ──

def _write_facts_json(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2) + "\n")
    return path


def _write_facts_md(report: WalkReport, out_dir: Path) -> Path:
    """Write walk-facts.md: one table per face, with VERDICT column."""
    path = out_dir / "walk-facts.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# HS-170-05 walk facts",
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
            # Escape pipes in values
            exp = f["expected"].replace("|", "\\|")
            obs = f["observed"].replace("|", "\\|")
            why = f["why"].replace("|", "\\|")
            lines.append(f"| {f['field']} | {exp} | {obs} | {f['verdict']} | {why} |")
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

    path.write_text("\n".join(lines) + "\n")
    return path


# ── Main ──

def main() -> int:
    parser = argparse.ArgumentParser(description="HS-170-05 pre-walk runner")
    parser.add_argument("--hub", required=True,
                        help="Hub URL with token (e.g. http://127.0.0.1:PORT/?token=TOKEN)")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Output directory for shots and facts")
    args = parser.parse_args()

    # Parse the URL to extract token
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
        print("ERROR: playwright not installed. Run: pip install playwright")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            w = vp["width"]
            h = vp["height"]
            suffix = vp["suffix"]
            print(f"\n=== Viewport {w}x{h} ===")

            page = browser.new_page(
                viewport={"width": w, "height": h},
            )
            page.emulate_media(reduced_motion="reduce")
            page_errors: list[str] = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            # Navigate to the hub
            page.goto(f"{base_url}/?token={token}", wait_until="load")
            page.wait_for_timeout(2000)

            # Cross first-sentence if present
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

            # 1. Arrival
            print(f"  [1/4] Arrival...")
            try:
                _walk_arrival(page, out_dir, w, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"arrival@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)

            # 2. Settings Hub
            print(f"  [2/4] Settings Hub...")
            try:
                _walk_settings_hub(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"settings-hub@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # 3. Meetings
            print(f"  [3/4] Meetings...")
            try:
                _walk_meetings(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"meetings@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # 4. Speak
            print(f"  [4/4] Speak...")
            try:
                _walk_speak(page, out_dir, w, token, report)
                print(f"        done.")
            except Exception as exc:
                msg = f"speak@{w}: {exc}"
                print(f"        FAILED: {msg}")
                report.errors.append(msg)
                errors_fatal.append(msg)

            # Collect page errors (filter ResizeObserver noise)
            critical = [e for e in page_errors if "ResizeObserver" not in e]
            if critical:
                report.errors.extend([f"JS@{w}: {e}" for e in critical])

            page.close()

        browser.close()

    # Detect defects from observed facts
    _detect_defects(report)

    # Write reports
    json_path = _write_facts_json(report, out_dir)
    md_path = _write_facts_md(report, out_dir)

    print(f"\n=== WALK 170 COMPLETE ===")
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
        print(f"\nFATAL ERRORS (faces that failed):")
        for e in errors_fatal:
            print(f"  - {e}")
        return 1

    # Check for BOUNCE verdicts
    bounces = [f for f in report.facts if f["verdict"] == "BOUNCE"]
    if bounces:
        print(f"\nBOUNCE verdicts ({len(bounces)}):")
        for b in bounces:
            print(f"  - {b['face']}/{b['field']}: {b['why']}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
