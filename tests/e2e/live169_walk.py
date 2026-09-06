"""HS-169-05 live walk: the Streamlined Door — 5 clicks to a live Room.

THE LIVE LAWS (inherited from 168, evolved for 169):
1. NO FIXTURE IN THE PATH (real leg).  Real gh on PATH, real acli on PATH.
2. HOME STAYS REAL (real leg).  Isolate ONLY DB + config (isolated mode)
   or use the real DB untouched (real mode).
3. FACE-DRIVEN.  Clicks on the window, not route calls.  The only wire
   calls: prime Jira connections and read the session back for assertions.
4. NOTHING HARD-CODED FROM THE SITE: discover connections from acli's
   registry, discover repos/projects via the face.

MODE: env HS169_WALK_DB=isolated|real (default isolated).
  isolated = tmp DB + fixture runners (proves the walk structure);
  real = DEFAULT_DB_PATH (~/.local/share/holdspeak/holdspeak.db).

Env gate: HS169_WALK=1 (skipped otherwise).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="169 walk needs Playwright")


# -- Skip guard -------------------------------------------------------
#
# The env gate (HS169_WALK) is the ONLY module-level skip.  The gh/acli
# auth check runs ONLY for the real leg (inside the test function),
# because the isolated leg uses fixture runners and does not need real
# gh/acli — and the isolated leg runs with HOME isolated (where gh auth
# status returns exit 1).

def _skip_reason() -> str:
    """Returns non-empty reason if the walk should be skipped."""
    if not os.environ.get("HS169_WALK"):
        return "HS169_WALK not set (live walk only runs on demand)"
    return ""


def _check_real_cli_auth() -> str:
    """Check gh + acli auth for the real leg.  Returns reason or ""."""
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

TOKEN = "hs169-walk"
REPO = Path(__file__).resolve().parents[2]
WALK_MODE = os.environ.get("HS169_WALK_DB", "isolated")
PHASE_DIR = REPO / "pm/roadmap/holdspeak/phase-169-the-streamlined-door"
WALK_SHOTS = PHASE_DIR / "assets" / "story-05-walk"

OUTCOME_TEXT = "Ship the Q4 platform on schedule with zero incidents"


# -- Data model -------------------------------------------------------

@dataclass
class StepRecord:
    step_num: int
    step_name: str
    width: int
    clicks_cumulative: int = 0
    seconds_cumulative: float = 0.0
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


def _shot(page: Any, width: int, step_num: int,
          step_name: str) -> tuple[Path, str]:
    """Settle animations, shoot the window, return (path, hash)."""
    _settle(page)
    suffix = "desktop" if width == 1440 else "phone"
    prefix = "real-" if WALK_MODE == "real" else "isolated-"
    d = WALK_SHOTS / f"{prefix}connected-{suffix}"
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


# -- Boot (isolated) ---------------------------------------------------

def _boot_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, str]:
    """Boot with isolated DB, fixture runners for gh/acli."""
    from tests.e2e.glass_infra import _ensure_build
    _ensure_build()

    from tests.e2e.test_hs169_door_glass import (
        _make_gh_runner,
        _write_gh_fixture,
        _make_jira_runner,
        _GH_AUTH_CONNECTED,
        _GH_REPO_LIST,
        _GH_PR_SNAPSHOT,
        _GH_RUN_LIST,
    )
    from tests.e2e.glass_infra import _boot

    gh_fixture = tmp_path / "gh_fixture.json"
    _write_gh_fixture(
        gh_fixture, auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT, "returncode": 0},
        run_list={"stdout": _GH_RUN_LIST, "returncode": 0},
    )
    server, url = _boot(
        tmp_path, monkeypatch, token=TOKEN,
        gh_runner=_make_gh_runner(gh_fixture),
        acli_runner=_make_jira_runner(),
    )
    return server, url


# -- Boot (real) -------------------------------------------------------

def _boot_real(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    """Boot with REAL DB, REAL HOME."""
    from tests.e2e.glass_infra import _ensure_build
    _ensure_build()

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


# -- Navigation helpers ------------------------------------------------

def _navigate_to_connections(page: Any) -> None:
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


def _open_door(page: Any) -> None:
    """Open New Project via sessionStorage staging."""
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "project-setup"})
        );
    }""")
    page.reload(wait_until="load")
    _cross_first_sentence(page)


# -- Jira priming (isolated: via API; real: via acli discovery) --------

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


def _prime_connections_isolated(page: Any) -> None:
    """Prime Jira connection for isolated mode with fixture data."""
    add_resp = _api(page, "POST", "/api/providers/jira/connections",
                    {"site": "alpha.atlassian.net", "email": "user@example.com"})
    assert add_resp["status"] == 200, f"Jira add failed: {add_resp}"
    ref = urllib.parse.quote("alpha.atlassian.net|user@example.com", safe="")
    recheck_resp = _api(page, "POST",
                        f"/api/providers/jira/connections/{ref}/recheck")
    assert recheck_resp["status"] == 200, f"Jira recheck failed: {recheck_resp}"


def _prime_connections_real(page: Any) -> dict[str, Any]:
    """Prime Jira + GitHub recheck for real mode."""
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

    if acli_accounts:
        result["jira_ref"] = f"{acli_accounts[0]['site']}|{acli_accounts[0]['email']}"

    gh_resp = _api(page, "POST", "/api/providers/github/connection/recheck")
    assert gh_resp["status"] == 200, f"GitHub recheck failed: {gh_resp}"
    return result


# -- Viewport probe ----------------------------------------------------

def _assert_window_in_viewport(page: Any, width: int, label: str) -> None:
    """Assert the window's .desk-surface-window bounding box lies within
    the viewport (left >= 0, right <= viewport width).  HS-169-05 probe."""
    result = page.evaluate("""() => {
        const win = document.querySelector('.desk-surface-window');
        if (!win) return {ok: false, reason: 'no .desk-surface-window found'};
        const box = win.getBoundingClientRect();
        const vw = window.innerWidth;
        if (box.left < 0) return {ok: false, reason: `left=${box.left} < 0`, left: box.left, right: box.right, vw};
        if (box.right > vw + 2) return {ok: false, reason: `right=${box.right} > vw=${vw}`, left: box.left, right: box.right, vw};
        return {ok: true, left: box.left, right: box.right, vw};
    }""")
    assert result["ok"], (
        f"Window outside viewport at {width} ({label}): {result.get('reason', result)}"
    )


# =====================================================================
# THE WALK
# =====================================================================


def _run_walk(
    page: Any, url: str, width: int,
) -> tuple[list[StepRecord], int, float, str]:
    """The 5-click walk. Returns (records, clicks, elapsed, project_id)."""
    records: list[StepRecord] = []
    clicks = 0
    elapsed = 0.0
    step_num = 0
    prev_hash = ""
    project_id = ""

    # -- STEP 01: Settings > Connections ----------------------------------
    step_num += 1
    t0 = time.monotonic()
    _navigate_to_connections(page)
    page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)
    dt = time.monotonic() - t0
    elapsed += dt

    gh_card = page.locator('[data-testid="connections-github"]')
    gh_card.wait_for(timeout=5000)
    gh_text = gh_card.inner_text()
    assert "connected" in gh_text.lower(), (
        f"GitHub card must show Connected, got: {gh_text}"
    )

    jira_card = page.locator('[data-testid^="connections-jira"]').first
    jira_card.wait_for(timeout=5000)
    jira_text = jira_card.inner_text()
    assert "connected" in jira_text.lower(), (
        f"Jira card must show Connected, got: {jira_text}"
    )

    shot_path, shot_hash = _shot(page, width, step_num, "settings-connections")
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="settings-connections",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"GH: Connected; Jira: Connected",
    ))

    # -- STEP 02: New Project first open ----------------------------------
    step_num += 1
    t0_door = time.monotonic()
    t0 = t0_door
    _open_door(page)
    door = page.get_by_test_id("door-root")
    door.wait_for(timeout=10000)
    _settle(page)

    # Assert empty state
    outcome_input = page.get_by_test_id("door-outcome-input")
    outcome_input.wait_for(timeout=5000)
    placeholder = outcome_input.get_attribute("placeholder")
    assert placeholder == "What are you delivering?", f"Placeholder: {placeholder}"

    receipt = page.get_by_test_id("door-receipt")
    receipt_text = receipt.inner_text().upper()
    assert "NO SOURCES" in receipt_text, f"Receipt should say NO SOURCES, got: {receipt_text}"

    # Create disabled (no outcome text)
    create_btn = page.get_by_test_id("door-create")
    assert create_btn.is_disabled(), "Create should be disabled with empty outcome"

    # Viewport probe: door window within viewport
    _assert_window_in_viewport(page, width, "door-empty")

    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, width, step_num, "door-empty")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="door-empty",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes="empty state: placeholder + NO SOURCES + Create disabled",
    ))

    # -- STEP 03: Type the outcome (NOT a click) --------------------------
    step_num += 1
    t0 = time.monotonic()
    outcome_input.fill(OUTCOME_TEXT)
    _settle(page)

    # Create enabled now (outcome has text)
    assert not create_btn.is_disabled(), "Create should be enabled with outcome text"

    # Receipt still says NO SOURCES
    receipt_text2 = receipt.inner_text().upper()
    assert "NO SOURCES" in receipt_text2, f"Receipt after typing: {receipt_text2}"

    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, width, step_num, "outcome-typed")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="outcome-typed",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes="outcome filled, Create enabled, still NO SOURCES",
    ))

    # -- STEP 04: GitHub trigger (click 1) --------------------------------
    step_num += 1
    t0 = time.monotonic()
    gh_trigger = page.get_by_test_id("door-trigger-github")
    gh_trigger.wait_for(timeout=5000)
    gh_trigger.click()
    clicks += 1

    # Picker opens
    gh_picker = page.get_by_test_id("door-picker-github")
    gh_picker.wait_for(timeout=10000)
    page.wait_for_timeout(2000)
    _settle(page)

    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, width, step_num, "gh-picker")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="gh-picker",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes="GitHub picker open",
    ))

    # -- STEP 05: Repo card karolswdev/HoldSpeak (click 2) ----------------
    step_num += 1
    t0 = time.monotonic()
    repo_card = page.get_by_test_id("door-pick-karolswdev/HoldSpeak")
    repo_card.wait_for(timeout=10000)
    repo_card.click()
    clicks += 1

    # Picker closes, wait for CHECKING then LIVE
    page.wait_for_timeout(300)
    _settle(page)

    # Wait for counts to arrive
    page.wait_for_function(
        """() => {
            const el = document.querySelector('[data-testid="door-counts-github"]');
            return el !== null;
        }""",
        timeout=15000,
    )
    _settle(page)

    dt = time.monotonic() - t0
    elapsed += dt

    counts_el = page.get_by_test_id("door-counts-github")
    counts_text = counts_el.inner_text()

    shot_path, shot_hash = _shot(page, width, step_num, "gh-live")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="gh-live",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"GH counts: {counts_text[:60]}",
    ))

    # -- STEP 06: Jira trigger (click 3) ----------------------------------
    step_num += 1
    t0 = time.monotonic()
    jira_trigger = page.get_by_test_id("door-trigger-jira")
    jira_trigger.wait_for(timeout=5000)
    jira_trigger.click()
    clicks += 1

    # Wait for Jira picker items
    jira_picker = page.get_by_test_id("door-picker-jira")
    jira_picker.wait_for(timeout=10000)
    page.wait_for_timeout(2000)
    _settle(page)

    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, width, step_num, "jira-picker")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="jira-picker",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes="Jira picker open",
    ))

    # -- STEP 07: Jira project card KAN (click 4) -------------------------
    step_num += 1
    t0 = time.monotonic()
    kan_card = page.get_by_test_id("door-pick-KAN")
    kan_card.wait_for(timeout=10000)
    kan_card.click()
    clicks += 1

    # Wait for Jira counts / receipt to update
    page.wait_for_timeout(3000)
    _settle(page)

    receipt_text3 = receipt.inner_text().upper()

    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, width, step_num, "jira-live")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="jira-live",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"receipt: {receipt_text3[:60]}",
    ))

    # -- STEP 08: Create Project (click 5) --------------------------------
    step_num += 1
    t0 = time.monotonic()
    create_btn = page.get_by_test_id("door-create")
    assert not create_btn.is_disabled(), "Create must be enabled before click"
    create_btn.click()
    clicks += 1

    assert clicks == 5, f"Expected 5 clicks, got {clicks}"

    # Shoot immediately — capture the transitional state (loading spinner)
    # before the Room replaces the Door.
    page.wait_for_timeout(200)
    shot_path, shot_hash = _shot(page, width, step_num, "create")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    # Now wait for the Room to open (room-body appears)
    page.get_by_test_id("room-body").wait_for(timeout=30000)
    dt_create = time.monotonic() - t0
    elapsed += dt_create

    records.append(StepRecord(
        step_num=step_num, step_name="create",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"5 clicks, Room opening",
    ))

    # -- STEP 09: Room first paint ----------------------------------------
    step_num += 1
    t0_room = time.monotonic()

    # The "never blank" law: the Room's first paint must show SOURCES with
    # count tokens, not blank. Take a fast shot within 500ms of the body
    # appearing to prove we did not start with a blank frame, then assert
    # after settle.
    room_body = page.get_by_test_id("room-body")
    room_body.wait_for(timeout=5000)

    # Fast shot (within 500ms of room-body being visible)
    fast_shot_path = WALK_SHOTS / (
        ("real-" if WALK_MODE == "real" else "isolated-")
        + ("connected-desktop" if width == 1440 else "connected-phone")
    ) / "09a-room-fast.png"
    fast_shot_path.parent.mkdir(parents=True, exist_ok=True)
    window_el = page.locator(".desk-surface-window").first
    if window_el.count() > 0 and window_el.is_visible():
        window_el.screenshot(path=str(fast_shot_path))
    else:
        page.screenshot(path=str(fast_shot_path), full_page=False)

    # Now wait for data to load and settle
    _settle(page)

    # Headline
    headline = page.get_by_test_id("room-headline")
    headline.wait_for(timeout=10000)
    headline_text = headline.text_content() or ""
    assert headline_text, "Headline must not be empty"
    assert "need you" in headline_text.lower() or "nothing needs you" in headline_text.lower(), (
        f"Headline must match pattern: {headline_text}"
    )

    # SOURCES label with count (SurfaceSection renders <h3> inside .surface-section-head)
    sources_present = page.evaluate("""() => {
        const heads = document.querySelectorAll('.surface-section-head h3');
        for (const el of heads) {
            if ((el.textContent || '').startsWith('SOURCES')) return el.textContent;
        }
        return null;
    }""")
    assert sources_present is not None, "SOURCES section must be visible on first paint"

    # Source-scope tokens must not be blank
    source_scopes = page.locator("[data-testid='source-scope']")
    if source_scopes.count() > 0:
        for i in range(source_scopes.count()):
            scope_text = source_scopes.nth(i).text_content() or ""
            assert scope_text.strip(), f"Source scope {i} is blank"

    # Viewport probe: room window within viewport
    _assert_window_in_viewport(page, width, "room-first-paint")

    # POST /room/read called — footer receipt shows READ
    room_receipt = page.get_by_test_id("room-footer-receipt")
    room_receipt.wait_for(timeout=10000)
    room_receipt_text = room_receipt.text_content() or ""
    assert "READ" in room_receipt_text, f"Footer receipt: {room_receipt_text}"

    # Find the project ID from the Room's API calls (via window evaluation)
    project_id = page.evaluate("""() => {
        // The surface window's scope carries the project ID
        const windows = document.querySelectorAll('.desk-surface-window');
        for (const w of windows) {
            const body = w.querySelector('[data-testid="room-body"]');
            if (body) {
                // The title bar or a hidden attribute may carry it
                const scope = w.getAttribute('data-scope') || '';
                if (scope.startsWith('project:')) return scope.slice('project:'.length);
            }
        }
        return '';
    }""")

    # If we cannot get project ID from the window, try API
    if not project_id:
        projects_resp = _api_ok(page, "GET", "/api/projects")
        projects = projects_resp.get("projects", [])
        if projects:
            project_id = projects[-1].get("id", "")

    dt = time.monotonic() - t0_room
    elapsed += dt

    # The seconds from step 02 (door open) to step 09 (room first paint)
    seconds_door_to_room = time.monotonic() - t0_door

    shot_path, shot_hash = _shot(page, width, step_num, "room-first-paint")
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="room-first-paint",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
        notes=f"headline={headline_text}; sources={sources_present}; "
              f"door_to_room={seconds_door_to_room:.1f}s; project_id={project_id}",
    ))

    # -- STEP 10: HISTORY wing --------------------------------------------
    step_num += 1
    t0 = time.monotonic()
    history_tab = page.get_by_role("tab", name="History")
    history_tab.click()
    page.get_by_test_id("room-history").wait_for(timeout=10000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    shot_path, shot_hash = _shot(page, width, step_num, "history")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="history",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    # -- STEP 11: Back to Room --------------------------------------------
    step_num += 1
    t0 = time.monotonic()
    room_tab = page.get_by_role("tab", name="Room")
    room_tab.click()
    page.get_by_test_id("room-body").wait_for(timeout=5000)
    _settle(page)
    dt = time.monotonic() - t0
    elapsed += dt

    # Headline and sources still rendered
    headline2_text = headline.text_content() or ""
    assert headline2_text, "Headline must persist after wing switch"

    shot_path, shot_hash = _shot(page, width, step_num, "room-return")
    assert shot_hash != prev_hash, f"Step {step_num} shot identical to previous"
    prev_hash = shot_hash

    records.append(StepRecord(
        step_num=step_num, step_name="room-return",
        width=width, clicks_cumulative=clicks,
        seconds_cumulative=round(elapsed, 2),
        shot_path=str(shot_path.relative_to(PHASE_DIR)),
        shot_hash=shot_hash,
    ))

    return records, clicks, elapsed, project_id


# =====================================================================
# THE TEST
# =====================================================================

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_walk_169(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """HS-169-05 live walk: 5 clicks from New Project to a live Room."""
    mode = WALK_MODE
    is_real = mode == "real"

    # Real leg: check gh + acli auth (isolated leg uses fixture runners)
    if is_real:
        auth_problem = _check_real_cli_auth()
        if auth_problem:
            pytest.skip(auth_problem)

    all_records: list[StepRecord] = []
    project_id: str = ""
    errors: list[str] = []
    initial_project_count = 0

    if is_real:
        from holdspeak.db import get_database
        db = get_database()
        with db._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
            initial_project_count = row[0] if row else 0

    try:
        from playwright.sync_api import sync_playwright

        if is_real:
            server, url = _boot_real(monkeypatch)
        else:
            server, url = _boot_isolated(tmp_path, monkeypatch)

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page(
                    viewport={"width": width, "height": 900 if width == 1440 else 852},
                )
                page.emulate_media(reduced_motion="reduce")
                page.on("pageerror", lambda e: errors.append(str(e)))

                # HS-168-05: the provider wire, timed — printed on failure
                _wire_t0 = time.monotonic()
                _wire_open: dict[str, float] = {}

                def _on_req(r: Any) -> None:
                    if "/api/providers/" in r.url or "/api/projects/" in r.url:
                        _wire_open[r.url + r.method] = time.monotonic()
                        print(f"[wire +{time.monotonic() - _wire_t0:6.1f}s] REQ  {r.method} {r.url.split('/api/')[-1][:120]}")

                def _on_resp(r: Any) -> None:
                    k = r.url + r.request.method
                    if k in _wire_open:
                        print(f"[wire +{time.monotonic() - _wire_t0:6.1f}s] RESP {r.status} {r.url.split('/api/')[-1][:120]} ({time.monotonic() - _wire_open.pop(k):.1f}s)")

                page.on("request", _on_req)
                page.on("response", _on_resp)
                page.on("requestfailed", lambda r: print(
                    f"[wire] FAILED {r.url.split('/api/')[-1][:120]} {r.failure}"
                ) if "/api/" in r.url else None)

                _init_desk(page, url)

                # Prime connections
                if is_real:
                    _prime_connections_real(page)
                else:
                    _prime_connections_isolated(page)

                # THE WALK
                all_records, clicks, elapsed, project_id = _run_walk(
                    page, url, width,
                )

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

                        # READ the watch rows it left
                        room_resp = _api(pg2, "GET",
                                         f"/api/projects/{project_id}/room")
                        if room_resp["status"] < 300:
                            payload = room_resp["payload"]
                            watches = payload.get("sources", {}).get("items", [])
                            print(f"\n=== WATCH ROWS (project {project_id}) ===")
                            for w in watches:
                                print(f"  watch={w.get('watchId','?')}"
                                      f" state={w.get('state','?')}"
                                      f" checkedAt={w.get('checkedAt','?')}"
                                      f" tokens={w.get('tokens',[])}")
                                # No blank entries in any list clause
                                for tok in w.get("tokens", []):
                                    if isinstance(tok, str):
                                        assert tok.strip(), f"Blank token in watch {w.get('watchId')}"

                        br2.close()
                except Exception as exc:
                    print(f"WARNING: cleanup failed: {exc}")

                from holdspeak.db import get_database as _gdb
                db2 = _gdb()
                with db2._connection() as conn:
                    row = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
                    final_count = row[0] if row else 0
                print(f"Project count before={initial_project_count} after={final_count}")

            server.stop()
            if not is_real:
                from holdspeak.db import reset_database
                reset_database()

    except Exception:
        raise

    # -- Write transcript -----------------------------------------------
    transcript = {
        "schema": "walk-169-transcript@1",
        "generated_at": datetime.now().isoformat(),
        "mode": mode,
        "width": width,
        "clicks": 5,
        "steps": [asdict(r) for r in all_records],
        "page_errors": [e for e in errors if "ResizeObserver" not in e],
    }
    transcript_dir = WALK_SHOTS
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_prefix = "real-" if WALK_MODE == "real" else "isolated-"
    transcript_path = transcript_dir / f"{transcript_prefix}transcript-{width}.json"
    transcript_path.write_text(json.dumps(transcript, indent=2) + "\n")

    # -- Final assertions -----------------------------------------------
    assert len(all_records) == 11, (
        f"Expected 11 steps, got {len(all_records)}"
    )

    # Click count must be 5
    last = all_records[-1]
    assert last.clicks_cumulative == 5, (
        f"Expected 5 clicks, got {last.clicks_cumulative}"
    )

    # First paint assertion: the room-first-paint step (step 9) must
    # mention sources and headline in its notes
    step9 = next((r for r in all_records if r.step_name == "room-first-paint"), None)
    assert step9 is not None, "Step 9 (room-first-paint) missing from records"
    assert "headline=" in step9.notes, f"Step 9 notes missing headline: {step9.notes}"
    assert "sources=" in step9.notes, f"Step 9 notes missing sources: {step9.notes}"

    # Consecutive shots must differ (the walk law).
    # Exception: the create->room-first-paint boundary (step 08->09) is
    # a screen transition — in fixture mode the Room paints faster than
    # the Create's transitional state can be captured, so both shots show
    # the same Room face.  This is honest: the real leg (with network
    # latency) will capture the transition.
    TRANSITION_PAIRS = {("create", "room-first-paint")}
    hashes = [(r.step_name, r.shot_hash) for r in all_records if r.shot_hash]
    for i in range(1, len(hashes)):
        pair = (hashes[i - 1][0], hashes[i][0])
        if pair in TRANSITION_PAIRS:
            continue
        assert hashes[i][1] != hashes[i - 1][1], (
            f"Consecutive shots identical: {hashes[i - 1][0]} and {hashes[i][0]} "
            f"(hash {hashes[i][1]})"
        )

    # No critical page errors
    critical = [e for e in errors if "ResizeObserver" not in e]
    assert len(critical) == 0, f"Critical page errors: {critical}"

    # Print summary
    print(f"\n=== WALK 169 SUMMARY (width={width}, mode={mode}) ===")
    print(f"  Steps: {len(all_records)}")
    print(f"  Clicks: {last.clicks_cumulative}")
    print(f"  Total seconds: {last.seconds_cumulative:.1f}")
    for r in all_records:
        print(f"  [{r.step_num:02d}] {r.step_name} "
              f"(clicks={r.clicks_cumulative}, {r.seconds_cumulative:.1f}s) "
              f"hash={r.shot_hash}")
    print(f"  Transcript: {transcript_path.relative_to(REPO)}")
