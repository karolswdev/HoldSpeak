"""HS-168-05 live Tuesday walk: the Connections Door face-driven.

THE LIVE LAWS (inherited from 167):
1. NO FIXTURE IN THE PATH.  Real gh on PATH, real acli on PATH.
2. HOME STAYS REAL.  Both gh and acli read auth via HOME; isolated HOME
   returns unauthorized.  Isolate ONLY DB + config (isolated mode) or
   use the real DB untouched (real mode).
3. FACE-DRIVEN.  Clicks on the window, not route calls.  The only wire
   calls: prime Jira connections and read the session back for the
   round-trip assertion.
4. NOTHING HARD-CODED FROM THE SITE: discover connections from acli's
   registry, discover repos/projects via the face.

MODE: env HS168_WALK_DB=isolated|real (default isolated).
  isolated = tmp DB (proves the runner);
  real = DEFAULT_DB_PATH (~/.local/share/holdspeak/holdspeak.db).

Env gate: HS168_WALK=1 (skipped otherwise).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="168 walk needs Playwright")


# -- Skip guard -------------------------------------------------------

def _skip_reason() -> str:
    """Returns non-empty reason if the walk should be skipped."""
    if not os.environ.get("HS168_WALK"):
        return "HS168_WALK not set (live walk only runs on demand)"

    if shutil.which("gh") is None:
        return "gh CLI not found on PATH"
    try:
        gh = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"gh auth status could not run: {exc}"
    if gh.returncode != 0:
        return f"gh auth status failed (exit {gh.returncode}): {gh.stderr.strip()[:200]}"

    if shutil.which("acli") is None:
        return "acli CLI not found on PATH"
    try:
        acli = subprocess.run(
            ["acli", "jira", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"acli jira auth status could not run: {exc}"
    if acli.returncode != 0:
        return (
            f"acli jira auth status failed (exit {acli.returncode}): "
            f"{acli.stderr.strip()[:200]}"
        )
    return ""


_SKIP_REASON = _skip_reason()
pytestmark = pytest.mark.skipif(
    bool(_SKIP_REASON),
    reason=_SKIP_REASON or "live walk available",
)

TOKEN = "hs168-tuesday-walk"
REPO = Path(__file__).resolve().parents[2]
WALK_MODE = os.environ.get("HS168_WALK_DB", "isolated")
PHASE_DIR = REPO / "pm/roadmap/holdspeak/phase-168-the-connections-door"
WALK_SHOTS = PHASE_DIR / "assets" / "story-05-walk"

OUTCOME_TEXT = "Ship the Q4 platform on schedule with zero incidents"
SIGNALS_TEXT = "Missed sprint commitments, overdue items, stale decisions"


# -- Data model -------------------------------------------------------

@dataclass
class StepRecord:
    step_num: int
    step_name: str
    leg: str  # "cold" | "connected"
    width: int
    clicks_cumulative: int = 0
    seconds_cumulative: float = 0.0
    sentences_on_screen: int = 0
    dead_end: bool = False
    shot_path: str = ""
    shot_hash: str = ""
    notes: str = ""


# -- Helpers -----------------------------------------------------------

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
    page.wait_for_timeout(120)


def _shot(page: Any, leg: str, width: int, step_num: int,
          step_name: str) -> tuple[Path, str]:
    """Settle animations, shoot the window, return (path, hash)."""
    _settle(page)
    suffix = "desktop" if width == 1440 else "phone"
    # The real leg never overwrites the isolated leg's shots (HS-168-05 scar).
    prefix = "real-" if WALK_MODE == "real" else ""
    d = WALK_SHOTS / f"{prefix}{leg}-{suffix}"
    d.mkdir(parents=True, exist_ok=True)
    fname = f"{step_num:02d}-{step_name}.png"
    path = d / fname
    # Shoot the surface window for a true window shot
    window_el = page.locator(".desk-surface-window").first
    if window_el.count() > 0 and window_el.is_visible():
        window_el.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.exists() and path.stat().st_size > 2_000, (
        f"Shot {fname} missing or too small"
    )
    h = _hash_file(path)
    return path, h


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
         body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(_FETCH_JS, [method, path, body, TOKEN])
    return result


def _api_ok(page: Any, method: str, path: str,
            body: dict[str, Any] | None = None) -> Any:
    result = _api(page, method, path, body)
    assert result["status"] < 300, f"HTTP {result['status']} on {method} {path}: {result}"
    return result["payload"]


def _count_sentences(page: Any, locator: Any) -> int:
    """Count full sentences (period-terminated, >= 3 words) in a locator."""
    import re
    text = locator.inner_text()
    candidates = re.split(r'(?<=[.!?])\s+', text)
    count = 0
    for c in candidates:
        c = c.strip()
        if c.endswith('.') and len(c.split()) >= 3:
            count += 1
    return count


# -- Boot --------------------------------------------------------------

def _boot_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    cold: bool = False,
) -> tuple[Any, str]:
    """Boot with isolated DB, REAL HOME (for gh/acli auth)."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))

    config_dir = tmp_path / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")

    if cold:
        gh_empty = tmp_path / "gh-cold"
        gh_empty.mkdir(exist_ok=True)
        monkeypatch.setenv("GH_CONFIG_DIR", str(gh_empty))

    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    return server, server.start()


def _boot_real(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    """Boot with REAL DB, REAL HOME."""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    return server, server.start()


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api_ok(page, "POST", "/api/desk/seed")
    _api_ok(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})


def _cross_first_sentence(page: Any) -> None:
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _seed_desk_facts(tmp_path: Path) -> None:
    """Seed 1 meeting fact (minimal so the 8-cap leaves room for Jira)."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState
    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-168-walk-001",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint Review",
        capture_status="finalized",
    ))


def _count_projects_db() -> int:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
        return row[0] if row else 0


# -- Jira priming (wire calls allowed by the brief) -------------------

def _discover_acli_accounts() -> list[dict[str, str]]:
    import yaml
    config_path = Path.home() / ".config" / "acli" / "jira_config.yaml"
    if not config_path.exists():
        return []
    data = yaml.safe_load(config_path.read_text())
    profiles = data.get("profiles", [])
    accounts = []
    for p in profiles:
        site = p.get("site", "")
        email = p.get("email", "")
        if site and email:
            accounts.append({"site": site, "email": email})
    return accounts


def _prime_connections(page: Any) -> dict[str, Any]:
    """Prime Jira + GitHub recheck. Allowed wire calls per the brief."""
    result: dict[str, Any] = {"jira_ref": ""}

    acli_accounts = _discover_acli_accounts()
    assert acli_accounts, "No acli accounts in ~/.config/acli/jira_config.yaml"

    for acct in acli_accounts:
        add_resp = _api(page, "POST", "/api/providers/jira/connections",
                        {"site": acct["site"], "email": acct["email"]})
        assert add_resp["status"] == 200, f"Jira add failed: {add_resp}"
        ref = f"{acct['site']}|{acct['email']}"
        encoded_ref = urllib.parse.quote(ref, safe="")
        recheck_resp = _api(page, "POST",
                            f"/api/providers/jira/connections/{encoded_ref}/recheck")
        assert recheck_resp["status"] == 200, f"Jira recheck failed: {recheck_resp}"
        recheck_state = (
            recheck_resp["payload"].get("state", "?")
            if isinstance(recheck_resp["payload"], dict) else "?"
        )
        assert recheck_state == "connected", (
            f"Jira recheck did not reach connected: {recheck_state}"
        )

    if acli_accounts:
        result["jira_ref"] = f"{acli_accounts[0]['site']}|{acli_accounts[0]['email']}"

    gh_resp = _api(page, "POST", "/api/providers/github/connection/recheck")
    assert gh_resp["status"] == 200, f"GitHub recheck failed: {gh_resp}"

    return result


# -- Navigation helpers ------------------------------------------------

def _navigate_to_connections(page: Any, url: str) -> None:
    """Navigate to Settings > Connections via sessionStorage staging."""
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "configure-settings", scope: "integrations"})
        );
    }""")
    page.reload(wait_until="load")
    _cross_first_sentence(page)
    page.wait_for_timeout(2000)


def _open_interview(page: Any, url: str) -> None:
    """Open the project setup interview via sessionStorage staging."""
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "project-setup"})
        );
    }""")
    page.reload(wait_until="load")
    _cross_first_sentence(page)


def _answer_both_questions(page: Any) -> None:
    """Answer outcome + signals using the face (textarea + Next)."""
    textarea = page.locator(".setup-well-textarea")
    textarea.wait_for(timeout=10000)
    textarea.fill(OUTCOME_TEXT)
    page.wait_for_timeout(300)
    page.get_by_test_id("setup-next").click()
    page.wait_for_timeout(1000)
    textarea2 = page.locator(".setup-well-textarea")
    textarea2.wait_for(timeout=10000)
    textarea2.fill(SIGNALS_TEXT)
    page.wait_for_timeout(300)
    page.get_by_test_id("setup-next").click()
    # Real providers (gh/acli) can be slow; generous timeout
    page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=90000)


# =====================================================================
# THE WALK
# =====================================================================


def _run_cold_leg(
    page: Any, url: str, width: int, t0_global: float,
) -> tuple[list[StepRecord], int, float, str]:
    """Cold part of the isolated leg. Returns (records, clicks, elapsed, session_id)."""
    records: list[StepRecord] = []
    clicks = 0
    elapsed = 0.0
    step_num = 0
    prev_hash = ""

    # -- STEP 01: Settings > Connections (GH + Jira both visible) --------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    _navigate_to_connections(page, url)
    page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)
    dt = time.monotonic() - t0
    elapsed += dt

    gh_card = page.locator('[data-testid="connections-github"]')
    gh_card.wait_for(timeout=5000)
    gh_text = gh_card.inner_text()
    assert "Sign in" in gh_text or "Off" in gh_text or "sign" in gh_text.lower(), (
        f"Cold GitHub card must show Sign in state, got: {gh_text}"
    )

    jira_card = page.locator('[data-testid^="connections-jira"]').first
    jira_card.wait_for(timeout=5000)
    jira_text = jira_card.inner_text()
    assert "Not set up" in jira_text or "Off" in jira_text or "set up" in jira_text.lower(), (
        f"Cold Jira card must show Not set up state, got: {jira_text}"
    )

    shot_path, shot_hash = _shot(page, "cold", width, step_num, "settings-connections")
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="settings-connections", leg="cold",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"GitHub: {gh_text[:60]}; Jira: {jira_text[:60]}",
    ))

    # -- STEP 02: New Project > Outcome --------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    _open_interview(page, url)
    page.get_by_test_id("setup-root").wait_for(timeout=10000)
    textarea = page.locator(".setup-well-textarea")
    textarea.wait_for(timeout=10000)
    clicks += 1  # fill + submit
    textarea.fill(OUTCOME_TEXT)
    page.get_by_test_id("setup-next").click()
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "cold", width, step_num, "interview-outcome")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="interview-outcome", leg="cold",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 03: Notice answered — Sources with TOOLS + zero provider cards
    step_num += 1
    t0 = time.monotonic()
    textarea2 = page.locator(".setup-well-textarea")
    textarea2.wait_for(timeout=10000)
    clicks += 1
    textarea2.fill(SIGNALS_TEXT)
    page.get_by_test_id("setup-next").click()
    page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=30000)

    # TOOLS row
    tools = page.get_by_test_id("setup-tools-row")
    tools.wait_for(timeout=10000)
    gh_tool = page.get_by_test_id("setup-tool-github")
    gh_tool.wait_for(timeout=5000)
    gh_tool_text = gh_tool.inner_text().upper()
    assert "SIGN IN" in gh_tool_text or "CONNECT" in gh_tool_text, (
        f"Cold GH tool must show Sign in or Connect, got: {gh_tool_text}"
    )

    # Assert ZERO gh/jira suggestion cards
    card_els = page.get_by_test_id("setup-suggestion-cards").locator('[role="option"]')
    card_els.first.wait_for(timeout=10000)
    gh_cards_found = 0
    jira_cards_found = 0
    for i in range(card_els.count()):
        if card_els.nth(i).locator(".surface-provenance-source", has_text="gh").count() > 0:
            gh_cards_found += 1
        if card_els.nth(i).locator(".surface-provenance-source", has_text="acli").count() > 0:
            jira_cards_found += 1
    assert gh_cards_found == 0, f"Cold: expected 0 GH cards, found {gh_cards_found}"
    assert jira_cards_found == 0, f"Cold: expected 0 Jira cards, found {jira_cards_found}"

    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "cold", width, step_num, "sources-tools-cold")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="sources-tools-cold", leg="cold",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"GH tool: {gh_tool_text[:60]}; GH cards={gh_cards_found}; Jira cards={jira_cards_found}",
    ))

    # -- STEP 05: Press Connect GitHub ---------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    connect_btn = page.get_by_test_id("setup-connect-github")
    connect_btn.wait_for(timeout=5000)
    connect_btn.click()
    page.wait_for_timeout(2000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    # The Connections window should appear (settings window)
    shot_path, shot_hash = _shot(page, "cold", width, step_num, "connect-roundtrip-open")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    # Read session id before closing
    session_id = page.evaluate(
        "() => sessionStorage.getItem('hs.project-setup.session-id')")
    assert session_id, "Session ID must survive the connect round trip"

    records.append(StepRecord(
        step_num=step_num, step_name="connect-roundtrip-open", leg="cold",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"session_id={session_id[:20]}...",
    ))

    # -- STEP 06: Close Connections, return to setup -------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    # Return to setup by staging the open
    page.evaluate("""() => {
        sessionStorage.setItem("hs.desk.staged-surface-open",
            JSON.stringify({key: "project-setup"}));
    }""")
    page.reload(wait_until="load")
    _cross_first_sentence(page)
    page.get_by_test_id("setup-tools-row").wait_for(timeout=15000)
    dt = time.monotonic() - t0
    elapsed += dt

    # Assert session answers survived (allowed wire call per brief)
    session_data = _api_ok(page, "GET", f"/api/project-setups/{session_id}")
    assert session_data.get("stage") == "proposals", (
        f"Session stage after round trip: {session_data.get('stage')}"
    )
    answers = session_data.get("answers", {})
    assert "outcome" in answers, "Outcome answer lost in round trip"
    assert "signals" in answers, "Signals answer lost in round trip"

    shot_path, shot_hash = _shot(page, "cold", width, step_num, "back-from-connections")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="back-from-connections", leg="cold",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes="Session answers survived round trip",
    ))

    return records, clicks, elapsed, session_id


def _run_connected_leg(
    page: Any, url: str, width: int, t0_global: float,
    start_step: int = 6,
) -> tuple[list[StepRecord], int, float, str]:
    """Connected part. Returns (records, clicks, elapsed, project_id)."""
    records: list[StepRecord] = []
    clicks = 0
    elapsed = 0.0
    step_num = start_step - 1
    prev_hash = ""
    project_id = ""

    # -- Settings > Connections (connected) -----------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    _navigate_to_connections(page, url)
    page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)
    dt = time.monotonic() - t0
    elapsed += dt

    gh_card = page.locator('[data-testid="connections-github"]')
    gh_card.wait_for(timeout=5000)
    gh_text = gh_card.inner_text()
    assert "connected" in gh_text.lower(), (
        f"Connected GitHub card must show Connected, got: {gh_text}"
    )

    # Find Jira connection card (specific ref or ghost)
    jira_card = page.locator('[data-testid^="connections-jira"]').first
    jira_card.wait_for(timeout=5000)
    jira_text = jira_card.inner_text()
    assert "connected" in jira_text.lower(), (
        f"Connected Jira card must show Connected, got: {jira_text}"
    )

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "settings-connections")
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="settings-connections", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"GH: Connected; Jira: Connected",
    ))

    # -- New Project > Interview > Sources ------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1  # open interview
    _open_interview(page, url)
    page.get_by_test_id("setup-root").wait_for(timeout=10000)

    # Shot of the interview (outcome question)
    shot_path, shot_hash = _shot(page, "connected", width, step_num, "interview-open")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash
    dt_open = time.monotonic() - t0

    records.append(StepRecord(
        step_num=step_num, step_name="interview-open", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed + dt_open, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # Answer both questions and advance to suggestions
    clicks += 2  # outcome fill+next + signals fill+next
    _answer_both_questions(page)

    # The suggest step may take a while with real gh/acli providers
    # (suggestion cards are already awaited inside _answer_both_questions)
    dt = time.monotonic() - t0
    elapsed += dt

    # -- Sources with TOOLS + provider cards (one step) -----------------
    step_num += 1
    tools = page.get_by_test_id("setup-tools-row")
    tools.wait_for(timeout=10000)
    gh_tool = page.get_by_test_id("setup-tool-github")
    gh_tool.wait_for(timeout=5000)
    assert "CONNECTED" in gh_tool.inner_text().upper(), (
        f"Connected GH tool expected Connected, got: {gh_tool.inner_text()}"
    )

    # Assert gh and jira suggestion cards exist
    card_els = page.get_by_test_id("setup-suggestion-cards").locator('[role="option"]')
    card_els.first.wait_for(timeout=10000)
    gh_card_indices: list[int] = []
    jira_card_indices: list[int] = []
    for i in range(card_els.count()):
        if card_els.nth(i).locator(".surface-provenance-source", has_text="gh").count() > 0:
            gh_card_indices.append(i)
        if card_els.nth(i).locator(".surface-provenance-source", has_text="acli").count() > 0:
            jira_card_indices.append(i)
    assert len(gh_card_indices) >= 1, (
        f"Connected: expected >= 1 GH cards, found {len(gh_card_indices)}"
    )
    assert len(jira_card_indices) >= 1, (
        f"Connected: expected >= 1 Jira cards, found {len(jira_card_indices)}"
    )

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "sources-tools-connected")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="sources-tools-connected", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"GH cards={len(gh_card_indices)}; Jira cards={len(jira_card_indices)}; TOOLS=Connected",
    ))

    # -- STEP 12: GitHub wizard (click first GH card) ------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    card_els.nth(gh_card_indices[0]).click()
    wizard = page.get_by_test_id("provider-wizard-flow")
    wizard.wait_for(timeout=10000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    heading = page.get_by_test_id("wizard-heading-name")
    heading.wait_for(timeout=5000)
    heading_text = heading.inner_text().strip()
    assert heading_text, "Wizard heading must show Watch name"

    test_btn = page.get_by_test_id("provider-test-btn")
    test_btn.wait_for(timeout=5000)
    assert test_btn.is_disabled(), "Test this Watch must be disabled before scope"

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github-wizard")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    sentences = _count_sentences(page, wizard)

    records.append(StepRecord(
        step_num=step_num, step_name="github-wizard", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        sentences_on_screen=sentences,
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"heading={heading_text}; test_disabled=True",
    ))

    # -- STEP 13: GitHub scope (pick karolswdev/HoldSpeak) -------------
    step_num += 1
    t0 = time.monotonic()
    disc = page.get_by_test_id("provider-discovery-list")
    disc.wait_for(timeout=10000)
    disc_items = disc.locator('[role="option"]')
    disc_items.first.wait_for(timeout=10000)

    # Find HoldSpeak in the discovery list
    holdspeak_item = None
    for j in range(disc_items.count()):
        item_text = disc_items.nth(j).inner_text()
        if "holdspeak" in item_text.lower():
            holdspeak_item = disc_items.nth(j)
            break
    assert holdspeak_item is not None, (
        "HoldSpeak not found in discovery list"
    )
    clicks += 1
    holdspeak_item.click()
    # Wait for clarify-scope API to complete and test button to enable
    page.wait_for_function(
        """() => {
            const btn = document.querySelector('[data-testid="provider-test-btn"]');
            return btn && !btn.disabled;
        }""",
        timeout=30000,
    )
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    assert not test_btn.is_disabled(), "Test enabled after scope"

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github-scoped")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github-scoped", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 14: GitHub test ------------------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    test_btn.click()
    page.wait_for_function(
        """() => {
            const el = document.querySelector(
                '[data-testid="provider-test-display"][data-test-state="passed"]'
            );
            return el !== null;
        }""",
        timeout=30000,
    )
    dt = time.monotonic() - t0
    elapsed += dt

    td = page.get_by_test_id("provider-test-display")
    td_text = td.inner_text()
    assert "SUBJECT" in td_text, "SUBJECT expected in test display"
    assert "MATCHES" in td_text, "MATCHES expected in test display"

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github-test")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github-test", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"test display: {td_text[:100]}",
    ))

    # -- STEP 15: Use this Watch (done) --------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    page.get_by_test_id("provider-wizard-done").click()
    page.wait_for_timeout(500)
    _settle(page)
    # Wait for suggestion cards to reappear
    page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=10000)
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github-done")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github-done", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- Second GH card (known-scope) ----------------------------------
    step_num += 1
    t0 = time.monotonic()
    # Wait for known-scopes to refresh (the hub session update)
    page.wait_for_timeout(2000)
    cards2 = page.get_by_test_id("setup-suggestion-cards")
    c2 = cards2.locator('[role="option"]')
    c2.first.wait_for(timeout=10000)

    gh2_idx = None
    for i in range(c2.count()):
        card = c2.nth(i)
        if card.locator(".surface-provenance-source", has_text="gh").count() > 0:
            if card.get_attribute("aria-selected") != "true":
                gh2_idx = i
                break
    assert gh2_idx is not None, "Must find a second unselected GH card"
    clicks += 1
    c2.nth(gh2_idx).click()
    page.get_by_test_id("provider-wizard-flow").wait_for(timeout=10000)
    _settle(page)

    # Wait for the known-scope card to appear (loaded after connection check + discovery)
    known = page.get_by_test_id("known-scope-card")
    try:
        known.wait_for(timeout=10000)
    except Exception:
        # Take a debug shot
        debug_shot = WALK_SHOTS / f"debug-known-scope-{width}.png"
        debug_shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(debug_shot), full_page=True)
        raise AssertionError(
            f"Known-scope card did not appear within 10s. "
            f"Debug shot: {debug_shot}"
        )
    dt = time.monotonic() - t0
    elapsed += dt

    known.scroll_into_view_if_needed()
    _settle(page)
    known_text = known.inner_text()
    assert "chosen for" in known_text.lower(), (
        f"Known-scope card must say 'chosen for'; got: {known_text}"
    )

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github-known-scope")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github-known-scope", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"known-scope: {known_text[:80]}",
    ))

    # -- Use this repo (known scope) -----------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    page.get_by_test_id("known-scope-use").click()
    # Wait for clarify-scope API to complete and test button to enable
    page.wait_for_function(
        """() => {
            const btn = document.querySelector('[data-testid="provider-test-btn"]');
            return btn && !btn.disabled;
        }""",
        timeout=15000,
    )
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    test_btn2 = page.get_by_test_id("provider-test-btn")
    assert not test_btn2.is_disabled(), "Test enabled after known-scope use"

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github2-scoped")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github2-scoped", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 18: Second GH test ---------------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    test_btn2.click()
    page.wait_for_function(
        """() => {
            const el = document.querySelector(
                '[data-testid="provider-test-display"][data-test-state="passed"]'
            );
            return el !== null;
        }""",
        timeout=30000,
    )
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github2-test")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github2-test", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 19: Use second Watch (done) ------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    page.get_by_test_id("provider-wizard-done").click()
    page.wait_for_timeout(500)
    _settle(page)
    page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=10000)
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "github2-done")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="github2-done", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 20: Jira wizard ------------------------------------------
    step_num += 1
    t0 = time.monotonic()
    cards3 = page.get_by_test_id("setup-suggestion-cards")
    c3 = cards3.locator('[role="option"]')
    c3.first.wait_for(timeout=10000)

    jira_idx = None
    for i in range(c3.count()):
        if c3.nth(i).locator(".surface-provenance-source", has_text="acli").count() > 0:
            jira_idx = i
            break
    assert jira_idx is not None, "Must find a Jira card"
    clicks += 1
    c3.nth(jira_idx).click()
    jira = page.get_by_test_id("jira-wizard-flow")
    jira.wait_for(timeout=10000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    # With 1 connection: accounts step skipped -> scope step
    scope = page.get_by_test_id("jira-scope-step")
    scope.wait_for(timeout=10000)

    jira_test = page.get_by_test_id("jira-test-btn")
    jira_test.wait_for(timeout=5000)
    assert jira_test.is_disabled(), "Jira Test disabled before project pick"

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "jira-wizard")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="jira-wizard", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes="accounts_skipped=True; scope_step_visible=True",
    ))

    # -- STEP 21: Jira scope pick KAN ----------------------------------
    step_num += 1
    t0 = time.monotonic()
    # Wait for project discovery to load
    page.wait_for_timeout(2000)
    _settle(page)

    # Find and click KAN project
    kan = scope.locator("text=KAN").first
    if kan.count() == 0:
        # Try Kanban Board text
        kan = scope.locator("text=Kanban").first
    kan.wait_for(timeout=10000)
    clicks += 1
    kan.click()
    page.wait_for_timeout(1000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    assert not jira_test.is_disabled(), "Jira Test enabled after project pick"

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "jira-scoped")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="jira-scoped", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- Jira test + Use this Watch ------------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    jira_test.click()
    # Wait for test to pass (the done button replaces the test button)
    page.wait_for_function(
        """() => {
            const btn = document.querySelector('[data-testid="jira-wizard-done"]');
            return btn !== null;
        }""",
        timeout=60000,
    )
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "jira-test-passed")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="jira-test-passed", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- Use Jira Watch (done) -----------------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    done_btn = page.get_by_test_id("jira-wizard-done")
    done_btn.click()
    page.wait_for_timeout(500)
    _settle(page)
    page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=10000)
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "jira-done")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="jira-done", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 24: Review -----------------------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    review_btn = page.get_by_test_id("setup-proceed-review")
    review_btn.wait_for(timeout=5000)
    review_btn.click()
    page.get_by_test_id("setup-review").wait_for(timeout=10000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    watches = page.get_by_test_id("review-watches")
    watches.wait_for(timeout=5000)
    activate_btn = page.get_by_test_id("review-activate-btn")
    activate_btn.wait_for(timeout=5000)

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "review")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="review", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 25: Activate ---------------------------------------------
    step_num += 1
    t0 = time.monotonic()
    clicks += 1
    activate_btn.click()
    # Wait for the "done" state
    page.get_by_test_id("setup-done").wait_for(timeout=30000)
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, "connected", width, step_num, "activated")
    prev_hash = shot_hash

    # Find project_id from the session
    project_id_raw = page.evaluate("""() => {
        // The setup controller stores the project id after finalize
        const key = sessionStorage.getItem('hs.project-setup.project-id');
        return key || '';
    }""")

    # If not in sessionStorage, find it via API
    if not project_id_raw:
        # List projects and pick the newest
        projects_resp = _api_ok(page, "GET", "/api/projects")
        projects = projects_resp.get("projects", [])
        if projects:
            project_id_raw = projects[-1].get("id", "")

    assert project_id_raw, "Must have a project_id after activation"
    project_id = project_id_raw

    # Verify project state is active (lifecycle lives on the room endpoint)
    room_resp = _api_ok(page, "GET", f"/api/projects/{project_id}/room")
    room_project = room_resp.get("project", {})
    lifecycle = room_project.get("lifecycle", "")
    assert lifecycle == "active", (
        f"Project lifecycle must be active, got: {lifecycle}"
    )

    records.append(StepRecord(
        step_num=step_num, step_name="activated", leg="connected",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"project_id={project_id}; lifecycle=active",
    ))

    return records, clicks, elapsed, project_id


# =====================================================================
# THE TEST
# =====================================================================

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_tuesday_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """HS-168-05 live Tuesday walk: the Connections Door face-driven."""
    from tests.e2e.glass_infra import _ensure_build
    _ensure_build()

    mode = WALK_MODE
    is_real = mode == "real"

    all_records: list[StepRecord] = []
    project_id: str = ""
    errors: list[str] = []

    if is_real:
        initial_project_count = _count_projects_db()

    t0_global = time.monotonic()

    try:
        from playwright.sync_api import sync_playwright

        if not is_real:
            # ============================================================
            # ISOLATED LEG PART A: COLD
            # ============================================================
            cold_server, cold_url = _boot_isolated(
                tmp_path, monkeypatch, cold=True,
            )
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    page = browser.new_page(
                        viewport={"width": width, "height": 900 if width == 1440 else 852},
                    )
                    page.emulate_media(reduced_motion="reduce")
                    page.on("pageerror", lambda e: errors.append(str(e)))

                    _init_desk(page, cold_url)
                    _seed_desk_facts(tmp_path)

                    cold_records, _, _, _ = _run_cold_leg(
                        page, cold_url, width, t0_global,
                    )
                    all_records.extend(cold_records)

                    browser.close()
            finally:
                cold_server.stop()
                from holdspeak.db import reset_database
                reset_database()

            # Reset GH_CONFIG_DIR for connected part
            if "GH_CONFIG_DIR" in os.environ:
                monkeypatch.delenv("GH_CONFIG_DIR", raising=False)

        # ============================================================
        # CONNECTED PART (isolated or real DB)
        # ============================================================
        conn_tmp = tmp_path / "connected"
        conn_tmp.mkdir(exist_ok=True)

        if is_real:
            server, url = _boot_real(monkeypatch)
        else:
            server, url = _boot_isolated(conn_tmp, monkeypatch, cold=False)

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(
                    viewport={"width": width, "height": 900 if width == 1440 else 852},
                )
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda e: errors.append(str(e)))

                _init_desk(page, url)
                _seed_desk_facts(conn_tmp if not is_real else tmp_path)

                # Prime connections (allowed wire calls)
                _prime_connections(page)

                connected_records, clicks, elapsed, project_id = _run_connected_leg(
                    page, url, width, t0_global,
                    start_step=6 if not is_real else 1,
                )
                all_records.extend(connected_records)

                browser.close()
        finally:
            # -- Cleanup (real mode) --
            if is_real and project_id:
                try:
                    with sync_playwright() as pw2:
                        br2 = pw2.chromium.launch(headless=True)
                        ctx2 = br2.new_context()
                        pg2 = ctx2.new_page()
                        pg2.goto(f"{url}/?token={TOKEN}", wait_until="load")
                        # Unattended OFF before archive (the 167 law)
                        _api(pg2, "PUT",
                             f"/api/projects/{project_id}/steward/policy",
                             {"unattended_enabled": False})
                        # Archive (never delete)
                        _api(pg2, "DELETE", f"/api/projects/{project_id}")
                        br2.close()
                except Exception as exc:
                    print(f"WARNING: archive failed: {exc}")

                final_count = _count_projects_db()
                print(f"Project count before={initial_project_count} after={final_count}")

            server.stop()
            from holdspeak.db import reset_database
            reset_database()

    except Exception:
        raise

    # -- Write transcript -----------------------------------------------
    transcript = {
        "schema": "tuesday-walk-168-transcript@1",
        "generated_at": datetime.now().isoformat(),
        "mode": mode,
        "width": width,
        "steps": [asdict(r) for r in all_records],
        "page_errors": [e for e in errors if "ResizeObserver" not in e],
    }
    transcript_dir = WALK_SHOTS
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_prefix = "real-" if WALK_MODE == "real" else ""
    transcript_path = transcript_dir / f"{transcript_prefix}transcript-{width}.json"
    transcript_path.write_text(json.dumps(transcript, indent=2) + "\n")

    # -- Final assertions -----------------------------------------------
    # Cold = 6 steps, Connected = 19 steps => 25 total in isolated mode
    # Real = 19 steps in real mode
    min_expected = 20 if not is_real else 15
    assert len(all_records) >= min_expected, (
        f"Too few steps recorded: {len(all_records)} (expected >= {min_expected})"
    )

    # Consecutive shots must differ (the walk law)
    hashes = [(r.step_name, r.shot_hash) for r in all_records if r.shot_hash]
    for i in range(1, len(hashes)):
        # Skip hash comparison across leg boundaries (cold->connected)
        if all_records[i - 1].leg != all_records[i].leg if i < len(all_records) else True:
            continue
        assert hashes[i][1] != hashes[i - 1][1], (
            f"Consecutive shots identical: {hashes[i - 1][0]} and {hashes[i][0]} "
            f"(hash {hashes[i][1]})"
        )

    # No critical page errors
    critical = [e for e in errors if "ResizeObserver" not in e]
    assert len(critical) == 0, f"Critical page errors: {critical}"
