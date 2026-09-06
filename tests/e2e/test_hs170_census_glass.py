"""HS-170-01 -- THE CENSUS: shoot every surface at both widths.

Parametrized over EVERY surface key from applications.ts x {1440, 393}.
For each surface: stage the key, reload, cross the first sentence, wait
for the window, _settle, screenshot, and record per-surface metrics:
  - window size
  - count of raw <button> (not carrying the library Button's btn class)
  - count of text elements > 60 chars ending in a period (prose sentences)
  - distinct computed font-sizes (type steps)
  - whether any element clips outside the window
  - presence of a footer
  - count of .surface-token chips reading exactly "0" or starting with "0 "

Shots land in pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census/.
census.md carries the table.
"""
from __future__ import annotations

import json
import re
import textwrap
from datetime import datetime, timedelta
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

pytest.importorskip("playwright.sync_api", reason="Census glass needs Playwright")

CENSUS_DIR = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-170-the-great-pass/assets/census"
)
CENSUS_DIR.mkdir(parents=True, exist_ok=True)

TOKEN = "hs170-census"
WIDTHS = [1440, 393]


# ── Parse surface keys from applications.ts at test time ─────────

def _surface_keys() -> list[str]:
    """Read EVERY surface key from applications.ts (entries with a surface: block)."""
    app_ts = REPO / "web/src/desk/applications.ts"
    text = app_ts.read_text()
    # Find all action: "..." entries that are followed by a surface: { block
    # Strategy: split on each object start, find action + surface presence
    keys: list[str] = []
    # Regex: find action values in entries that have surface:
    # We look for blocks between { and the next top-level {
    entries = re.split(r'\n  \{', text)
    for entry in entries:
        action_m = re.search(r'action:\s*"([^"]+)"', entry)
        has_surface = re.search(r'surface:\s*\{', entry)
        if action_m and has_surface:
            keys.append(action_m.group(1))
    return keys


SURFACE_KEYS = _surface_keys()


# ── Seed helpers ────────────────────────────────────────────────

def _seed_project(pid: str = "census-proj") -> str:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, ?, "
            "'2026-09-01T00:00:00', '2026-09-04T10:00:00')",
            (pid, "Census Test Project", "2026-10-15"),
        )
    return pid


def _seed_gh_connection() -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh-census', 'github', 'karolswdev', 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
        )


def _seed_watch(project_id: str) -> None:
    from holdspeak.db import get_database
    db = get_database()
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                "w-census-prs", "gh", "pull_requests", "gh pull_requests",
                json.dumps({"repository": "karolswdev/HoldSpeak"}),
                json.dumps([
                    {"number": 700, "title": "Census test PR",
                     "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/700",
                     "reviewRequests": ["karolswdev"], "updatedAt": yesterday},
                ]),
                1, "2026-09-04T10:00:00", None, project_id,
            ),
        )


def _seed_meeting() -> str:
    from holdspeak.db import get_database
    db = get_database()
    mid = "census-meeting-1"
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'disabled', 'finalized', 'desktop')",
            (mid, "2026-09-04T09:00:00", "2026-09-04T09:30:00",
             "Census standup", 1800.0),
        )
    return mid


def _seed_dictation_entry() -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO dictation_journal "
            "(source, transcript, final_text, created_at) "
            "VALUES ('glass-test', 'test transcript for census', "
            "'Test dictation final text', datetime('now'))",
        )


def _seed_changes(project_id: str) -> None:
    from holdspeak.db import get_database
    db = get_database()
    now = datetime.now()
    rows = [
        ("census-chg-1", project_id, 1, "project.created", None, None, None, None, None,
         "{}", (now - timedelta(hours=3)).isoformat()),
        ("census-chg-2", project_id, 2, "project.updated", None, None, None, None, None,
         '{"purpose": "Census test"}',
         (now - timedelta(hours=1)).isoformat()),
    ]
    with db._connection() as conn:
        for row in rows:
            conn.execute(
                "INSERT OR IGNORE INTO project_changes "
                "(id, project_id, project_revision, change_kind, "
                " target_ref, actor_ref, command_id, before_hash, after_hash, "
                " summary_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )


# ── Measurement JS ──────────────────────────────────────────────

MEASURE_JS = """(windowSelector) => {
  const win = document.querySelector(windowSelector);
  if (!win) return { error: "no window found" };
  const winBox = win.getBoundingClientRect();

  // 1. Raw buttons: <button> NOT carrying .btn
  const allButtons = win.querySelectorAll("button");
  let rawButtons = 0;
  const rawButtonTexts = [];
  for (const b of allButtons) {
    if (!b.classList.contains("btn")) {
      rawButtons++;
      rawButtonTexts.push((b.textContent || "").trim().slice(0, 40));
    }
  }

  // 2. Sentences: text > 60 chars ending in a period
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  let sentences = 0;
  const sentenceTexts = [];
  while (walker.nextNode()) {
    const t = (walker.currentNode.textContent || "").trim();
    if (t.length > 60 && t.endsWith(".")) {
      sentences++;
      sentenceTexts.push(t.slice(0, 80));
    }
  }

  // 3. Type steps: distinct font-sizes of text nodes
  const fontSizes = new Set();
  const walker2 = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  while (walker2.nextNode()) {
    const parent = walker2.currentNode.parentElement;
    if (parent && walker2.currentNode.textContent.trim()) {
      fontSizes.add(Math.round(parseFloat(getComputedStyle(parent).fontSize) * 10) / 10);
    }
  }

  // 4. Clipping: any element box exceeds the window box
  let clipped = false;
  const allEls = win.querySelectorAll("*");
  for (const el of allEls) {
    const b = el.getBoundingClientRect();
    if (b.width === 0 || b.height === 0) continue;
    if (b.right > winBox.right + 2 || b.left < winBox.left - 2) {
      clipped = true;
      break;
    }
  }

  // 5. Footer presence
  const hasFooter = win.querySelector(".surface-footer, .desk-surface-foot") !== null;

  // 6. Zero counters: .surface-token reading exactly "0" or starting "0 "
  const tokens = win.querySelectorAll(".surface-token, [data-chip]");
  let zeroCounters = 0;
  const zeroTexts = [];
  for (const tok of tokens) {
    const text = (tok.textContent || "").trim();
    if (text === "0" || text.startsWith("0 ")) {
      zeroCounters++;
      zeroTexts.push(text.slice(0, 30));
    }
  }

  return {
    width: Math.round(winBox.width),
    height: Math.round(winBox.height),
    rawButtons,
    rawButtonTexts,
    sentences,
    sentenceTexts,
    typeSteps: [...fontSizes].sort((a, b) => a - b),
    clipped,
    hasFooter,
    zeroCounters,
    zeroTexts,
  };
}"""


# ── Core rig ────────────────────────────────────────────────────

class CensusResult:
    """Accumulates per-surface measurements for the table."""
    def __init__(self):
        self.rows: list[dict[str, Any]] = []

    def add(self, key: str, width: int, data: dict[str, Any], note: str = ""):
        self.rows.append({"key": key, "width": width, **data, "note": note})

    def write_md(self, path: Path) -> None:
        lines = [
            "# HS-170-01 Census",
            "",
            "| key | width | window | raw btns | sentences | type steps | clipped | footer | zero ctrs | notes |",
            "|-----|-------|--------|----------|-----------|------------|---------|--------|-----------|-------|",
        ]
        for r in sorted(self.rows, key=lambda x: (x["key"], x["width"])):
            w = r.get("width", "?")
            wsize = f'{r.get("windowW", "?")}x{r.get("windowH", "?")}'
            rb = r.get("rawButtons", "?")
            snt = r.get("sentences", "?")
            ts = r.get("typeSteps", "?")
            if isinstance(ts, list):
                ts = f'{len(ts)} ({", ".join(str(s) for s in ts)})'
            clip = "YES" if r.get("clipped") else "no"
            foot = "yes" if r.get("hasFooter") else "NO"
            zc = r.get("zeroCounters", "?")
            note = r.get("note", "")
            lines.append(f"| {r['key']} | {w} | {wsize} | {rb} | {snt} | {ts} | {clip} | {foot} | {zc} | {note} |")
        lines.append("")
        path.write_text("\n".join(lines))


def _open_surface(page: Any, key: str, scope: str | None = None) -> None:
    """Clear all surface windows, stage a surface key, and reload.

    The workspace is persisted to localStorage; without clearing it first,
    previous windows reopen on reload and `.first` always picks the stale one.
    """
    page.evaluate(
        """([key, scope]) => {
          // Clear persisted workspace so no stale windows reopen on reload
          localStorage.removeItem("hs.desk.workspace.v1");
          // Stage the new surface
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify(scope ? {key, scope} : {key})
          );
        }""",
        [key, scope],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _wait_for_surface_window(page: Any, timeout: int = 15000) -> bool:
    """Wait for a .desk-surface-window to appear. Returns True if found."""
    try:
        page.locator(".desk-surface-window").first.wait_for(timeout=timeout)
        return True
    except Exception:
        return False


def _count_surface_windows(page: Any) -> int:
    """Count how many surface windows are open."""
    return page.locator(".desk-surface-window").count()


def _shot_surface(page: Any, key: str, width: int) -> Path:
    """Screenshot the LAST surface window (most recently opened)."""
    _settle(page)
    path = CENSUS_DIR / f"{key}-{width}.png"
    windows = page.locator(".desk-surface-window")
    count = windows.count()
    if count > 0:
        windows.last.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    return path


def _measure_surface(page: Any) -> dict[str, Any]:
    """Run the measurement JS on the LAST visible surface window.

    After clearing workspace and staging one key, there should be exactly
    one window. The JS targets the last .desk-surface-window on the page.
    """
    count = page.locator(".desk-surface-window").count()
    if count == 0:
        return {"error": "no visible window"}
    # Use :last-of-type to hit the most recent window
    result = page.evaluate(MEASURE_JS, ".desk-surface-window:last-child")
    if result.get("error"):
        # Fallback: try plain selector
        result = page.evaluate(MEASURE_JS, ".desk-surface-window")
    return result


def _run_census(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
    census: CensusResult,
) -> None:
    """Core census rig: seed data, then iterate every surface."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Seed realistic data
            project_id = _seed_project()
            _seed_gh_connection()
            _seed_watch(project_id)
            _seed_meeting()
            _seed_dictation_entry()
            _seed_changes(project_id)

            # Cross the first sentence
            _normal_chair(page)

            # Full desk shot first
            _settle(page)
            desk_shot = CENSUS_DIR / f"desk-{width}.png"
            page.screenshot(path=str(desk_shot), full_page=False)
            print(f"[census] desk shot: {desk_shot.name} ({desk_shot.stat().st_size} bytes)")

            # Iterate every surface
            for key in SURFACE_KEYS:
                print(f"[census] {key} @ {width}...")

                # Determine scope for surfaces that need one
                scope = None
                if key == "open-project-memory":
                    scope = f"project:{project_id}"

                try:
                    _open_surface(page, key, scope)
                    found = _wait_for_surface_window(page, timeout=12000)
                    if not found:
                        note = "WINDOW DID NOT OPEN"
                        print(f"  -> {note}")
                        census.add(key, width, {
                            "windowW": 0, "windowH": 0,
                            "rawButtons": "?", "sentences": "?",
                            "typeSteps": "?", "clipped": False,
                            "hasFooter": False, "zeroCounters": "?",
                            "note": note,
                        })
                        # Still shoot whatever is on screen
                        _shot_surface(page, key, width)
                        continue

                    _settle(page)
                    page.wait_for_timeout(300)  # let data load
                    _settle(page)

                    # Measure
                    data = _measure_surface(page)
                    if "error" in data:
                        note = f"MEASURE ERROR: {data['error']}"
                        print(f"  -> {note}")
                        census.add(key, width, {
                            "windowW": 0, "windowH": 0,
                            "rawButtons": "?", "sentences": "?",
                            "typeSteps": "?", "clipped": False,
                            "hasFooter": False, "zeroCounters": "?",
                            "note": note,
                        })
                        _shot_surface(page, key, width)
                        continue

                    # Screenshot
                    shot_path = _shot_surface(page, key, width)
                    shot_size = shot_path.stat().st_size if shot_path.exists() else 0

                    # Build row
                    notes_parts = []
                    if data.get("rawButtons", 0) > 0:
                        notes_parts.append(f"raw btns: {data.get('rawButtonTexts', [])}")
                    if data.get("sentences", 0) > 0:
                        notes_parts.append(f"sentences: {data.get('sentenceTexts', [])}")
                    if data.get("zeroCounters", 0) > 0:
                        notes_parts.append(f"zeros: {data.get('zeroTexts', [])}")
                    if data.get("clipped"):
                        notes_parts.append("CLIPPING")
                    ts_list = data.get("typeSteps", [])
                    if isinstance(ts_list, list) and len(ts_list) < 3:
                        notes_parts.append(f"ONLY {len(ts_list)} type steps")

                    note = "; ".join(notes_parts) if notes_parts else ""

                    census.add(key, width, {
                        "windowW": data.get("width", 0),
                        "windowH": data.get("height", 0),
                        "rawButtons": data.get("rawButtons", 0),
                        "sentences": data.get("sentences", 0),
                        "typeSteps": ts_list,
                        "clipped": data.get("clipped", False),
                        "hasFooter": data.get("hasFooter", False),
                        "zeroCounters": data.get("zeroCounters", 0),
                        "note": note,
                    })

                    size = f'{data.get("width", 0)}x{data.get("height", 0)}'
                    print(f"  -> {size} | raw={data.get('rawButtons',0)} | "
                          f"sent={data.get('sentences',0)} | "
                          f"steps={len(ts_list)} | "
                          f"clip={'Y' if data.get('clipped') else 'n'} | "
                          f"foot={'y' if data.get('hasFooter') else 'N'} | "
                          f"zero={data.get('zeroCounters',0)} | "
                          f"shot={shot_size}B")

                    # No explicit close needed: _open_surface clears
                    # localStorage workspace before reload

                except Exception as exc:
                    note = f"ERROR: {str(exc)[:120]}"
                    print(f"  -> {note}")
                    census.add(key, width, {
                        "windowW": 0, "windowH": 0,
                        "rawButtons": "?", "sentences": "?",
                        "typeSteps": "?", "clipped": False,
                        "hasFooter": False, "zeroCounters": "?",
                        "note": note,
                    })

            print(f"[census] width {width} done, {len(census.rows)} total rows so far")

            real_errors = [e for e in errors if "ResizeObserver" not in e]
            if real_errors:
                print(f"[census] JS errors (non-fatal): {real_errors[:5]}")

            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.timeout(900)
def test_census_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """HS-170-01: shoot every surface at both widths and write the census table."""
    census = CensusResult()
    for width in WIDTHS:
        sub = tmp_path / str(width)
        sub.mkdir(parents=True, exist_ok=True)
        _run_census(sub, monkeypatch, width, census)
    census.write_md(CENSUS_DIR / "census.md")
    print(f"[census] wrote census.md with {len(census.rows)} rows")
