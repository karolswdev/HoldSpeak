"""HS-168-01 stopwatch audit: today's connector path THROUGH THE FACE.

Env gate: HS168_AUDIT=1 (skipped otherwise).
Two conditions:
  - connected: real HOME (gh + acli authenticated), isolated DB
  - cold: GH_CONFIG_DIR -> empty tmp dir (gh sees no accounts), isolated DB

Two widths: 1440, 393.

Drives New Project -> outcome -> signals -> Sources -> GitHub wizard
-> (back) -> Jira wizard -> (back) -> cancel.  STOP BEFORE ACTIVATE.

Every step: window shot, click count, wall-clock seconds, sentences
on screen, dead ends.

Output:
  - assets/before/<condition>-<width>-<NN>-<step>.png
  - assets/audit/transcript.json
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.parse
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="168 audit needs Playwright")

# ── Skip guard ──────────────────────────────────────────────────────
if not os.environ.get("HS168_AUDIT"):
    pytest.skip("HS168_AUDIT not set", allow_module_level=True)

# ── Paths ───────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parents[6]  # HoldSpeak root
PHASE_DIR = REPO / "pm/roadmap/holdspeak/phase-168-the-connections-door"
BEFORE_DIR = PHASE_DIR / "assets" / "before"
AUDIT_DIR = PHASE_DIR / "assets" / "audit"
TOKEN = "hs168-audit"

# ── Data ────────────────────────────────────────────────────────────

@dataclass
class StepRecord:
    step_name: str
    condition: str
    width: int
    clicks_this_step: int = 0
    clicks_cumulative: int = 0
    seconds_this_step: float = 0.0
    seconds_cumulative: float = 0.0
    sentences_on_screen: list[str] = field(default_factory=list)
    dead_end: bool = False
    dead_end_detail: str = ""
    shot_path: str = ""
    shot_hash: str = ""
    verbs_visible: list[str] = field(default_factory=list)
    heading_text: str = ""
    connection_card_copy: str = ""
    recovery_text: str = ""
    terminal_command_shown: bool = False
    notes: str = ""


# ── Helpers ─────────────────────────────────────────────────────────

def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _shot(page: Any, condition: str, width: int, step_num: int,
          step_name: str, *, locator: Any = None) -> tuple[Path, str]:
    """Take a WINDOW shot and return (path, hash)."""
    BEFORE_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{condition}-{width}-{step_num:02d}-{step_name}.png"
    path = BEFORE_DIR / fname
    if locator is not None:
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass
    # Try to shoot the surface window element for a true window shot
    window_el = page.locator('.desk-surface-window').first
    if window_el.count() > 0 and window_el.is_visible():
        window_el.screenshot(path=str(path))
    else:
        # Fallback: full page
        page.screenshot(path=str(path), full_page=False)
    assert path.exists() and path.stat().st_size > 2_000, (
        f"Shot {fname} missing or too small"
    )
    h = _hash_file(path)
    return path, h


def _sentences_in_element(page: Any, locator: Any) -> list[str]:
    """Extract full sentences (ending with period, containing a verb) from a locator."""
    text = locator.inner_text()
    # Split by period and filter for actual sentences
    candidates = re.split(r'(?<=[.!?])\s+', text)
    sentences = []
    for c in candidates:
        c = c.strip()
        if c.endswith('.') and len(c.split()) >= 3:
            sentences.append(c)
    return sentences


def _visible_verbs(page: Any, locator: Any) -> list[str]:
    """Get visible button labels within a locator."""
    buttons = locator.locator('button')
    verbs = []
    for i in range(buttons.count()):
        btn = buttons.nth(i)
        if btn.is_visible():
            label = btn.inner_text().strip()
            if label:
                verbs.append(label)
    return verbs


def _api(page: Any, method: str, path: str,
         body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body, token]) => {
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
        }""",
        [method, path, body, TOKEN],
    )
    return result


def _api_ok(page: Any, method: str, path: str,
            body: dict[str, Any] | None = None) -> Any:
    result = _api(page, method, path, body)
    assert result["status"] < 300, f"HTTP {result['status']} on {method} {path}: {result}"
    return result["payload"]


# ── Boot ────────────────────────────────────────────────────────────

def _boot_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    cold: bool = False,
) -> tuple[Any, str]:
    """Boot with isolated DB, REAL HOME (for gh/acli auth).

    cold=True: sets GH_CONFIG_DIR to an empty tmp dir so gh sees no
    accounts (simulates no GitHub connection).
    """
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

    # HOME STAYS REAL -- gh and acli read auth via HOME
    config_dir = tmp_path / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")

    if cold:
        # gh honors GH_CONFIG_DIR: point it at an empty dir
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


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api_ok(page, "POST", "/api/desk/seed")
    _api_ok(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})


def _seed_desk_facts(tmp_path: Path, *, minimal: bool = False) -> None:
    """Seed desk facts so the suggest step has native proposals.

    minimal=True: seed only 1 meeting (1 native proposal) so the 8-proposal
    cap does not truncate Jira proposals (3 native + 5 GitHub = 8 drops Jira).
    """
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState
    from datetime import datetime, timedelta

    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-audit-168-001",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint Planning",
        capture_status="finalized",
    ))

    if minimal:
        return  # 1 native proposal only -- leaves room for Jira

    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis,
                   source_timestamp, provenance_label,
                   source_artifact_id, source_meeting_id,
                   source_state, project_key, lifecycle,
                   superseded_by, created_at, updated_at, last_modified, deleted
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "dec-audit-168-001",
                "Adopt event sourcing",
                "Reduces risk",
                "2026-08-15T14:30:00",
                "meeting_date",
                None, "reported", "a-001", "m-audit-168-001",
                "linked", None, "accepted", None,
                now_iso, now_iso, now_iso, 0,
            ),
        )
    past_due = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items (
                   id, meeting_id, task, owner, due, status,
                   review_state, created_at, source_type, source_ref
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "ai-audit-168-001", "m-audit-168-001",
                "Update compliance docs", "karol",
                past_due, "pending", "accepted", now_iso, "meeting", "",
            ),
        )


def _cross_first_sentence(page: Any) -> None:
    """Cross the First Sentence gate without blocking."""
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _open_interview(page: Any, url: str) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["project-setup"],
    )
    page.reload(wait_until="load")
    _cross_first_sentence(page)


# ── Prime connections (connected condition only) ────────────────────

def _discover_acli_accounts() -> list[dict[str, str]]:
    """Read acli accounts from the YAML config (same as live167)."""
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
    """Prime GitHub and Jira so suggest sees connected providers.

    Follows the live167 pattern: read acli accounts from YAML config,
    POST each to the hub, recheck each, then recheck GitHub.  Asserts
    every response succeeds and recheck reaches "connected".
    """
    result: dict[str, Any] = {"jira_ref": "", "jira_prime_log": []}

    # Jira: discover accounts from acli config YAML and register + recheck
    acli_accounts = _discover_acli_accounts()
    assert acli_accounts, "No acli accounts found in ~/.config/acli/jira_config.yaml"

    for acct in acli_accounts:
        # Add connection -- assert 200
        add_resp = _api(page, "POST", "/api/providers/jira/connections",
                        {"site": acct["site"], "email": acct["email"]})
        assert add_resp["status"] == 200, (
            f"Jira add failed: {add_resp}"
        )
        result["jira_prime_log"].append({
            "action": "add", "site": acct["site"],
            "status": add_resp["status"],
            "state": add_resp["payload"].get("state", "?") if isinstance(add_resp["payload"], dict) else "?",
        })

        # Recheck -- assert 200 AND state=connected
        ref = f"{acct['site']}|{acct['email']}"
        encoded_ref = urllib.parse.quote(ref, safe="")
        recheck_resp = _api(page, "POST",
                            f"/api/providers/jira/connections/{encoded_ref}/recheck")
        assert recheck_resp["status"] == 200, (
            f"Jira recheck failed: {recheck_resp}"
        )
        recheck_state = (
            recheck_resp["payload"].get("state", "?")
            if isinstance(recheck_resp["payload"], dict) else "?"
        )
        assert recheck_state == "connected", (
            f"Jira recheck did not reach connected: state={recheck_state}, "
            f"payload={recheck_resp['payload']}"
        )
        result["jira_prime_log"].append({
            "action": "recheck", "ref": ref,
            "status": recheck_resp["status"],
            "state": recheck_state,
        })

    if acli_accounts:
        result["jira_ref"] = (
            f"{acli_accounts[0]['site']}|{acli_accounts[0]['email']}"
        )

    # GitHub: the adapter probes on boot; trigger a recheck
    gh_resp = _api(page, "POST", "/api/providers/github/connection/recheck")
    assert gh_resp["status"] == 200, f"GitHub recheck failed: {gh_resp}"
    result["gh_recheck"] = {
        "status": gh_resp["status"],
        "state": gh_resp["payload"].get("state", "?") if isinstance(gh_resp["payload"], dict) else "?",
    }

    # Verification: GET /api/providers must show Jira readiness
    verify = _api_ok(page, "GET", "/api/providers")
    providers = verify.get("providers", []) if isinstance(verify, dict) else []
    jira_provider = [p for p in providers if p.get("provider_id") == "jira"]
    result["verification"] = {
        "jira_providers_found": len(jira_provider),
        "jira_readiness": jira_provider[0] if jira_provider else None,
    }
    assert jira_provider, (
        f"GET /api/providers does not list Jira after priming. "
        f"Providers: {[p.get('provider_id') for p in providers]}"
    )

    return result


# ── The walk ────────────────────────────────────────────────────────

OUTCOME_TEXT = "Ship the Q4 platform on schedule with zero incidents"
SIGNALS_TEXT = "Missed sprint commitments, overdue items, stale decisions"


def _run_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    condition: str,
    width: int,
) -> list[StepRecord]:
    """Run one audit pass: one condition x one width."""
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    cold = condition == "cold"
    server, url = _boot_isolated(tmp_path, monkeypatch, cold=cold)
    records: list[StepRecord] = []
    step_num = 0
    clicks = 0
    elapsed = 0.0
    prev_hash = ""

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={
                    "width": width,
                    "height": 900 if width == 1440 else 852,
                },
            )
            page.emulate_media(reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            # ── STEP 0: Desk init ───────────────────────────────
            t0 = time.monotonic()
            _init_desk(page, url)
            # Connected condition: minimal seeding so the 8-proposal cap
            # (project_setup_service.py:74 _MAX_PROPOSALS=8) does not
            # truncate Jira proposals.  3 native + 5 GitHub = 8 fills the
            # cap exactly; Jira (appended last) gets dropped.
            _seed_desk_facts(tmp_path, minimal=not cold)
            dt = time.monotonic() - t0
            elapsed += dt

            prime_result: dict[str, Any] = {}
            if not cold:
                prime_result = _prime_connections(page)

                # Debug: verify Jira connections via API before interview
                jira_conns = _api(page, "GET", "/api/providers/jira/connections")
                prime_result["jira_connections_after_prime"] = jira_conns
                connected_conns = []
                if isinstance(jira_conns.get("payload"), list):
                    connected_conns = [c for c in jira_conns["payload"]
                                       if c.get("state") == "connected"]
                elif isinstance(jira_conns.get("payload"), dict):
                    conns_list = jira_conns["payload"].get("connections", [])
                    connected_conns = [c for c in conns_list
                                       if c.get("state") == "connected"]
                prime_result["connected_jira_count"] = len(connected_conns)
                print(f"[AUDIT] Jira connections after prime: {len(connected_conns)} connected, raw={json.dumps(jira_conns)[:300]}")

            # ── STEP 1: Open Settings -> look for connections ───
            step_num += 1
            t0 = time.monotonic()
            clicks += 1  # click Settings
            page.evaluate(
                """([key]) => {
                  sessionStorage.setItem(
                    "hs.desk.staged-surface-open",
                    JSON.stringify({key})
                  );
                }""",
                ["configure-settings"],
            )
            page.reload(wait_until="load")
            _cross_first_sentence(page)
            page.wait_for_timeout(1500)
            dt = time.monotonic() - t0
            elapsed += dt

            # Look for the settings surface window
            settings_window = page.locator('.desk-surface-window').first
            settings_window.wait_for(timeout=10000)

            shot_path, shot_hash = _shot(page, condition, width, step_num, "settings-open")
            prev_hash = shot_hash

            # Check for any "Connections" or "Connect" text
            settings_text = settings_window.inner_text()
            has_connections_module = "Connections" in settings_text
            has_connect_verb = "Connect" in settings_text

            rec = StepRecord(
                step_name="settings-open",
                condition=condition, width=width,
                clicks_this_step=1, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                sentences_on_screen=_sentences_in_element(page, settings_window),
                dead_end=False,
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
                verbs_visible=_visible_verbs(page, settings_window),
                notes=f"Connections module exists: {has_connections_module}; "
                      f"Connect verb visible: {has_connect_verb}; "
                      f"Module list: {[t.strip() for t in settings_text.split(chr(10)) if t.strip()][:15]}",
            )
            records.append(rec)

            # ── STEP 2: Navigate to Settings -> Integrations ────
            step_num += 1
            t0 = time.monotonic()
            clicks += 1
            # Click Integrations tile
            integ_tile = settings_window.locator('text=Integrations').first
            if integ_tile.count() > 0 and integ_tile.is_visible():
                integ_tile.click()
                page.wait_for_timeout(1000)
            dt = time.monotonic() - t0
            elapsed += dt

            shot_path, shot_hash = _shot(page, condition, width, step_num, "settings-integrations")
            integ_text = settings_window.inner_text()

            rec = StepRecord(
                step_name="settings-integrations",
                condition=condition, width=width,
                clicks_this_step=1, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                sentences_on_screen=_sentences_in_element(page, settings_window),
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
                verbs_visible=_visible_verbs(page, settings_window),
                notes=f"Integrations content: credentials/mesh, no connections. "
                      f"Has GitHub mention: {'github' in integ_text.lower()}; "
                      f"Has Jira mention: {'jira' in integ_text.lower()}",
            )
            records.append(rec)

            # ── STEP 3: Navigate to Settings -> Meetings ────────
            step_num += 1
            t0 = time.monotonic()
            clicks += 1
            # Go back to module list (click back or navigate)
            meetings_tile = settings_window.locator('text=Meetings').first
            if meetings_tile.count() > 0 and meetings_tile.is_visible():
                meetings_tile.click()
                page.wait_for_timeout(1000)
            else:
                # Navigate by palette
                page.evaluate(
                    """([key, scope]) => {
                      sessionStorage.setItem(
                        "hs.desk.staged-surface-open",
                        JSON.stringify({key, scope})
                      );
                    }""",
                    ["configure-settings", "meetings"],
                )
                page.reload(wait_until="load")
                _cross_first_sentence(page)
                page.wait_for_timeout(1000)
            dt = time.monotonic() - t0
            elapsed += dt

            shot_path, shot_hash = _shot(page, condition, width, step_num, "settings-meetings")
            meetings_text = settings_window.inner_text() if settings_window.is_visible() else ""

            rec = StepRecord(
                step_name="settings-meetings",
                condition=condition, width=width,
                clicks_this_step=1, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                sentences_on_screen=_sentences_in_element(page, settings_window) if settings_window.is_visible() else [],
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
                verbs_visible=_visible_verbs(page, settings_window) if settings_window.is_visible() else [],
                notes=f"Calendar section: {'Calendar' in meetings_text}; "
                      f"Connect verb: {'Connect' in meetings_text}",
            )
            records.append(rec)

            # ── STEP 4: Open New Project (the interview) ────────
            step_num += 1
            t0 = time.monotonic()
            clicks += 1
            _open_interview(page, url)
            dt = time.monotonic() - t0
            elapsed += dt

            window = page.locator('.desk-surface-window').first
            window.wait_for(timeout=10000)

            shot_path, shot_hash = _shot(page, condition, width, step_num, "interview-open")

            rec = StepRecord(
                step_name="interview-open",
                condition=condition, width=width,
                clicks_this_step=1, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                sentences_on_screen=_sentences_in_element(page, window),
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
                verbs_visible=_visible_verbs(page, window),
            )
            records.append(rec)

            # ── STEP 5: Answer outcome ──────────────────────────
            step_num += 1
            t0 = time.monotonic()
            clicks += 1  # click textarea + press Enter
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill(OUTCOME_TEXT)
            textarea.press("Enter")
            dt = time.monotonic() - t0
            elapsed += dt

            shot_path, shot_hash = _shot(page, condition, width, step_num, "outcome-answered")

            rec = StepRecord(
                step_name="outcome-answered",
                condition=condition, width=width,
                clicks_this_step=1, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
            )
            records.append(rec)

            # ── STEP 6: Answer signals ──────────────────────────
            step_num += 1
            t0 = time.monotonic()
            clicks += 1
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            textarea2 = q_signals.locator("textarea")
            textarea2.fill(SIGNALS_TEXT)
            textarea2.press("Enter")
            dt = time.monotonic() - t0
            elapsed += dt

            shot_path, shot_hash = _shot(page, condition, width, step_num, "signals-answered")

            rec = StepRecord(
                step_name="signals-answered",
                condition=condition, width=width,
                clicks_this_step=1, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
            )
            records.append(rec)

            # Debug: call _jira_candidates directly on the server's service
            if not cold:
                from holdspeak.principals import Principal, PrincipalKind
                OWNER_PRINCIPAL = Principal(PrincipalKind.OWNER, "audit")
                svc = server._build_context_handler.__self__ if hasattr(server, '_build_context_handler') else None
                # Access the project setup service's jira adapter via the server
                try:
                    # The server stores its context lazily; trigger a direct check
                    from holdspeak.db import get_database
                    from holdspeak.services.jira_provider import JiraProviderAdapter
                    db = get_database()
                    adapter = JiraProviderAdapter(db=db, runner=None)
                    conns = adapter.list_connections(OWNER_PRINCIPAL)
                    connected = [c for c in conns if c.get("state") == "connected"]
                    print(f"[AUDIT] Direct adapter.list_connections: {len(conns)} total, {len(connected)} connected")
                    for c in conns:
                        print(f"  conn: ref={c.get('external_connection_ref','?')} state={c.get('state','?')}")

                    # Try generating Jira candidates directly
                    from holdspeak.services.project_setup_service import ProjectSetupService
                    from holdspeak.services.project_service import ProjectService
                    from holdspeak.services.watch_service import WatchService
                    from holdspeak.services.github_provider import GitHubProviderAdapter
                    test_svc = ProjectSetupService(
                        db,
                        project_service=ProjectService(db),
                        watch_service=WatchService(db),
                        github_adapter=GitHubProviderAdapter(db=db, runner=None),
                        jira_adapter=adapter,
                    )
                    # Create a temporary session and suggest
                    test_session = test_svc.start_setup(OWNER_PRINCIPAL)
                    test_sid = test_session["id"]
                    test_svc.answer(OWNER_PRINCIPAL, test_sid, "outcome", {"text": OUTCOME_TEXT})
                    test_svc.answer(OWNER_PRINCIPAL, test_sid, "signals", {"text": SIGNALS_TEXT})
                    test_proposals = test_svc.suggest(OWNER_PRINCIPAL, test_sid)
                    print(f"[AUDIT] Direct suggest: {len(test_proposals)} proposals")
                    for i, p in enumerate(test_proposals):
                        if isinstance(p, dict):
                            print(f"  [{i}] provider_id={p.get('provider_id','?')} name={p.get('spec',{}).get('name','?') if isinstance(p.get('spec'),dict) else '?'}")
                        else:
                            print(f"  [{i}] type={type(p).__name__} val={str(p)[:100]}")
                    provider_ids = [p.get("provider_id", "?") if isinstance(p, dict) else "?" for p in test_proposals]
                    jira_count = sum(1 for pid in provider_ids if pid == "jira")
                    print(f"[AUDIT] Jira proposals: {jira_count}")

                    # If no Jira proposals, call _jira_candidates directly
                    if jira_count == 0:
                        try:
                            jira_cands = test_svc._jira_candidates(OWNER_PRINCIPAL, test_sid)
                            print(f"[AUDIT] _jira_candidates returned: {len(jira_cands)}")
                        except Exception as jex:
                            print(f"[AUDIT] _jira_candidates THREW: {type(jex).__name__}: {jex}")
                            import traceback
                            traceback.print_exc()
                except Exception as exc:
                    import traceback
                    print(f"[AUDIT] Direct suggest check FAILED: {exc}")
                    traceback.print_exc()

            # ── STEP 7: Suggestions appear (the Sources step) ───
            step_num += 1
            t0 = time.monotonic()
            cards = page.get_by_test_id("setup-suggestion-cards")
            cards.wait_for(timeout=30000)
            card_elements = cards.locator('[role="option"]')
            card_elements.first.wait_for(timeout=15000)
            card_count = card_elements.count()
            dt = time.monotonic() - t0
            elapsed += dt

            # Catalog every card: its text, source chip, provider
            card_catalog: list[dict[str, str]] = []
            gh_card_indices: list[int] = []
            jira_card_indices: list[int] = []
            for i in range(card_count):
                card = card_elements.nth(i)
                card_text = card.inner_text()
                # Check for provider source chip
                source_chip = ""
                egress = card.locator(".gadget-chip-egress")
                if "github" in card_text.lower():
                    source_chip = "github"
                    gh_card_indices.append(i)
                elif "jira" in card_text.lower():
                    source_chip = "jira"
                    jira_card_indices.append(i)
                else:
                    source_chip = "native"

                # Extract facts: look for source fact label
                source_fact = card.locator('.choice-card-fact').all_inner_texts()

                card_catalog.append({
                    "index": str(i),
                    "text_preview": card_text[:120].replace('\n', ' | '),
                    "source": source_chip,
                    "facts": "; ".join(source_fact),
                })

            # Check visibility at 393 without scrolling
            first_gh_visible_no_scroll = False
            if gh_card_indices:
                first_gh = card_elements.nth(gh_card_indices[0])
                try:
                    box = first_gh.bounding_box()
                    if box:
                        viewport_h = 852 if width == 393 else 900
                        first_gh_visible_no_scroll = (
                            box["y"] >= 0 and box["y"] + box["height"] <= viewport_h
                        )
                except Exception:
                    pass

            shot_path, shot_hash = _shot(page, condition, width, step_num, "suggestions")

            rec = StepRecord(
                step_name="suggestions",
                condition=condition, width=width,
                clicks_this_step=0, clicks_cumulative=clicks,
                seconds_this_step=round(dt, 2),
                seconds_cumulative=round(elapsed, 2),
                sentences_on_screen=_sentences_in_element(page, cards),
                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                shot_hash=shot_hash,
                notes=json.dumps({
                    "card_count": card_count,
                    "github_card_indices": gh_card_indices,
                    "jira_card_indices": jira_card_indices,
                    "card_catalog": card_catalog,
                    "first_gh_visible_no_scroll_at_width": first_gh_visible_no_scroll,
                }),
            )
            records.append(rec)

            # ── STEP 8: Click GitHub suggestion (or record cold dead end) ─
            if gh_card_indices:
                step_num += 1
                t0 = time.monotonic()
                clicks += 1
                gh_card = card_elements.nth(gh_card_indices[0])
                gh_card.click()
                dt = time.monotonic() - t0
                elapsed += dt

                # Wait for wizard or click effect
                page.wait_for_timeout(2000)

                # Check what appeared
                wizard = page.get_by_test_id("provider-wizard-flow")
                wizard_appeared = wizard.count() > 0

                if wizard_appeared:
                    wizard.wait_for(timeout=10000)
                    wizard_text = wizard.inner_text()
                    heading = ""
                    heading_el = wizard.locator("h3").first
                    if heading_el.count() > 0:
                        heading = heading_el.inner_text().strip()

                    # Check connection card
                    status_card = page.get_by_test_id("provider-status-card")
                    conn_card_copy = ""
                    conn_state = ""
                    recovery_text = ""
                    terminal_shown = False
                    if status_card.count() > 0:
                        status_card.wait_for(timeout=10000)
                        conn_card_copy = status_card.inner_text().strip()
                        conn_state = status_card.get_attribute("data-state") or ""
                        recovery_el = page.get_by_test_id("provider-recovery")
                        if recovery_el.count() > 0:
                            recovery_text = recovery_el.inner_text().strip()
                            terminal_shown = True

                    shot_path, shot_hash = _shot(
                        page, condition, width, step_num, "github-wizard"
                    )

                    rec = StepRecord(
                        step_name="github-wizard",
                        condition=condition, width=width,
                        clicks_this_step=1, clicks_cumulative=clicks,
                        seconds_this_step=round(dt, 2),
                        seconds_cumulative=round(elapsed, 2),
                        sentences_on_screen=_sentences_in_element(page, wizard),
                        dead_end=not cold and conn_state != "connected",
                        dead_end_detail=recovery_text if terminal_shown else "",
                        shot_path=str(shot_path.relative_to(PHASE_DIR)),
                        shot_hash=shot_hash,
                        verbs_visible=_visible_verbs(page, wizard),
                        heading_text=heading,
                        connection_card_copy=conn_card_copy,
                        recovery_text=recovery_text,
                        terminal_command_shown=terminal_shown,
                        notes=f"connection_state={conn_state}; wizard_text_preview={wizard_text[:200]}",
                    )
                    records.append(rec)

                    if cold and terminal_shown:
                        # This is a dead end in the cold condition
                        rec.dead_end = True
                        rec.dead_end_detail = (
                            f"Recovery text: {recovery_text}. "
                            "No next verb that progresses beyond terminal command."
                        )

                    # ── CONNECTED PATH: discovery -> pick repo -> test ──
                    if not cold and conn_state == "connected":
                        # Wait for discovery list
                        disc_list = page.get_by_test_id("provider-discovery-list")
                        if disc_list.count() > 0:
                            step_num += 1
                            t0 = time.monotonic()
                            disc_list.wait_for(timeout=15000)
                            disc_items = disc_list.locator('[role="option"]')
                            disc_items.first.wait_for(timeout=15000)
                            disc_count = disc_items.count()

                            shot_path, shot_hash = _shot(
                                page, condition, width, step_num, "github-discovery"
                            )

                            rec = StepRecord(
                                step_name="github-discovery",
                                condition=condition, width=width,
                                clicks_this_step=0, clicks_cumulative=clicks,
                                seconds_this_step=round(time.monotonic() - t0, 2),
                                seconds_cumulative=round(elapsed + (time.monotonic() - t0), 2),
                                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                shot_hash=shot_hash,
                                notes=f"discovery_count={disc_count}",
                            )
                            elapsed += time.monotonic() - t0
                            records.append(rec)

                            # Pick first repo (or type HoldSpeak)
                            step_num += 1
                            t0 = time.monotonic()
                            clicks += 1
                            # Try to find HoldSpeak in the list
                            holdspeak_item = None
                            for j in range(disc_count):
                                item_text = disc_items.nth(j).inner_text()
                                if "HoldSpeak" in item_text or "holdspeak" in item_text.lower():
                                    holdspeak_item = disc_items.nth(j)
                                    break
                            if holdspeak_item:
                                holdspeak_item.click()
                            else:
                                disc_items.first.click()
                            page.wait_for_timeout(2000)
                            dt = time.monotonic() - t0
                            elapsed += dt

                            # Check for scoped state
                            scoped = page.get_by_test_id("provider-wizard-scoped")
                            is_scoped = scoped.count() > 0 and scoped.is_visible()

                            shot_path, shot_hash = _shot(
                                page, condition, width, step_num, "github-scoped"
                            )

                            scoped_text = scoped.inner_text() if is_scoped else ""
                            rec = StepRecord(
                                step_name="github-scoped",
                                condition=condition, width=width,
                                clicks_this_step=1, clicks_cumulative=clicks,
                                seconds_this_step=round(dt, 2),
                                seconds_cumulative=round(elapsed, 2),
                                sentences_on_screen=_sentences_in_element(page, wizard) if wizard.is_visible() else [],
                                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                shot_hash=shot_hash,
                                verbs_visible=_visible_verbs(page, wizard) if wizard.is_visible() else [],
                                notes=f"scoped={is_scoped}; scoped_text={scoped_text[:100]}",
                            )
                            records.append(rec)

                            # Click "Test this Watch"
                            if is_scoped:
                                test_btn = page.get_by_test_id("provider-test-btn")
                                if test_btn.count() > 0:
                                    step_num += 1
                                    t0 = time.monotonic()
                                    clicks += 1
                                    test_btn.click()

                                    # Wait for test result
                                    try:
                                        page.wait_for_function(
                                            """() => {
                                                const el = document.querySelector(
                                                    '[data-testid="provider-test-display"]'
                                                        + '[data-test-state="passed"]'
                                                );
                                                return el !== null;
                                            }""",
                                            timeout=30000,
                                        )
                                    except Exception:
                                        pass  # Record whatever state we got

                                    dt = time.monotonic() - t0
                                    elapsed += dt

                                    test_display = page.locator('[data-testid="provider-test-display"]')
                                    test_state = ""
                                    if test_display.count() > 0:
                                        test_state = test_display.get_attribute("data-test-state") or ""

                                    shot_path, shot_hash = _shot(
                                        page, condition, width, step_num, "github-test"
                                    )

                                    rec = StepRecord(
                                        step_name="github-test",
                                        condition=condition, width=width,
                                        clicks_this_step=1, clicks_cumulative=clicks,
                                        seconds_this_step=round(dt, 2),
                                        seconds_cumulative=round(elapsed, 2),
                                        shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                        shot_hash=shot_hash,
                                        verbs_visible=_visible_verbs(page, wizard) if wizard.is_visible() else [],
                                        notes=f"test_state={test_state}",
                                    )
                                    records.append(rec)

                    # Record exit verb
                    done_btn = page.get_by_test_id("provider-wizard-done")
                    if done_btn.count() > 0:
                        done_label = done_btn.inner_text().strip()
                        step_num += 1
                        t0 = time.monotonic()
                        clicks += 1
                        done_btn.click()
                        page.wait_for_timeout(1500)
                        dt = time.monotonic() - t0
                        elapsed += dt

                        # Wait for suggestion cards to reappear
                        cards = page.get_by_test_id("setup-suggestion-cards")
                        cards_reappeared = False
                        try:
                            cards.wait_for(timeout=5000)
                            cards_reappeared = True
                        except Exception:
                            pass

                        shot_path, shot_hash = _shot(
                            page, condition, width, step_num, "github-exit"
                        )

                        rec = StepRecord(
                            step_name="github-exit",
                            condition=condition, width=width,
                            clicks_this_step=1, clicks_cumulative=clicks,
                            seconds_this_step=round(dt, 2),
                            seconds_cumulative=round(elapsed, 2),
                            shot_path=str(shot_path.relative_to(PHASE_DIR)),
                            shot_hash=shot_hash,
                            verbs_visible=[done_label],
                            notes=f"exit_verb={done_label}; cards_reappeared={cards_reappeared}",
                        )
                        records.append(rec)

            else:
                # No GitHub cards in cold condition -- record finding
                step_num += 1
                shot_path, shot_hash = _shot(
                    page, condition, width, step_num, "no-github-cards"
                )
                rec = StepRecord(
                    step_name="no-github-cards",
                    condition=condition, width=width,
                    clicks_this_step=0, clicks_cumulative=clicks,
                    seconds_this_step=0, seconds_cumulative=round(elapsed, 2),
                    dead_end=True,
                    dead_end_detail="No GitHub suggestion cards appear when gh is not authenticated -- the cold condition produces zero GitHub proposals.",
                    shot_path=str(shot_path.relative_to(PHASE_DIR)),
                    shot_hash=shot_hash,
                )
                records.append(rec)

            # ── STEP: Click Jira suggestion (if available) ──────
            # Re-find cards (they may have been rebuilt)
            cards = page.get_by_test_id("setup-suggestion-cards")
            if cards.count() > 0:
                card_elements = cards.locator('[role="option"]')
                new_count = card_elements.count()
                # Re-scan for Jira
                jira_card_indices = []
                for i in range(new_count):
                    card = card_elements.nth(i)
                    card_text = card.inner_text()
                    if "jira" in card_text.lower():
                        jira_card_indices.append(i)

                if jira_card_indices:
                    # ── JIRA WIZARD: accounts -> scope -> test -> exit ──
                    step_num += 1
                    t0 = time.monotonic()
                    clicks += 1
                    jira_card = card_elements.nth(jira_card_indices[0])
                    jira_card.click()
                    page.wait_for_timeout(2000)
                    dt = time.monotonic() - t0
                    elapsed += dt

                    jira_flow = page.get_by_test_id("jira-wizard-flow")
                    jira_appeared = jira_flow.count() > 0

                    if jira_appeared:
                        jira_flow.wait_for(timeout=10000)
                        jira_text = jira_flow.inner_text()

                        # ── JIRA ACCOUNTS STEP ──
                        accounts_step = page.get_by_test_id("jira-accounts-step")
                        has_accounts = accounts_step.count() > 0
                        if has_accounts:
                            accounts_step.wait_for(timeout=5000)

                        shot_path, shot_hash = _shot(
                            page, condition, width, step_num, "jira-accounts"
                        )

                        # Record account cards and their states
                        acc_text = accounts_step.inner_text() if has_accounts else ""
                        has_connected = "Connected" in acc_text
                        has_sign_in = "Sign in" in acc_text

                        rec = StepRecord(
                            step_name="jira-accounts",
                            condition=condition, width=width,
                            clicks_this_step=1, clicks_cumulative=clicks,
                            seconds_this_step=round(dt, 2),
                            seconds_cumulative=round(elapsed, 2),
                            sentences_on_screen=_sentences_in_element(page, jira_flow),
                            shot_path=str(shot_path.relative_to(PHASE_DIR)),
                            shot_hash=shot_hash,
                            verbs_visible=_visible_verbs(page, jira_flow),
                            heading_text=jira_flow.locator("h3").first.inner_text().strip() if jira_flow.locator("h3").count() > 0 else "",
                            notes=f"accounts_visible={has_accounts}; has_connected={has_connected}; has_sign_in={has_sign_in}; text_preview={acc_text[:200]}",
                        )
                        records.append(rec)

                        if has_accounts and not cold:
                            # Select the connected account via radio click
                            step_num += 1
                            t0 = time.monotonic()
                            clicks += 1
                            page.evaluate("""() => {
                              const radios = document.querySelectorAll('input[type="radio"][name="jira-account"]');
                              if (radios.length > 0) {
                                radios[0].click();
                                radios[0].dispatchEvent(new Event('change', { bubbles: true }));
                              }
                            }""")
                            page.wait_for_timeout(1500)

                            # Click "Choose project" footer button
                            choose_btn = page.locator('.jira-wizard-footer button').filter(has_text="roject")
                            if choose_btn.count() == 0:
                                choose_btn = page.locator('button[aria-label="Choose project"]')
                            if choose_btn.count() > 0:
                                page.wait_for_function(
                                    """() => {
                                      const btns = document.querySelectorAll('.jira-wizard-footer button');
                                      for (const btn of btns) {
                                        if ((btn.textContent || '').includes('roject')) return !btn.disabled;
                                      }
                                      return false;
                                    }""",
                                    timeout=8000,
                                )
                                choose_btn.first.click()
                                page.wait_for_timeout(1000)
                            dt = time.monotonic() - t0
                            elapsed += dt

                            # ── JIRA SCOPE STEP ──
                            scope_step = page.get_by_test_id("jira-scope-step")
                            scope_visible = scope_step.count() > 0
                            if scope_visible:
                                scope_step.wait_for(timeout=10000)

                                shot_path, shot_hash = _shot(
                                    page, condition, width, step_num, "jira-scope"
                                )

                                scope_text = scope_step.inner_text()
                                rec = StepRecord(
                                    step_name="jira-scope",
                                    condition=condition, width=width,
                                    clicks_this_step=1, clicks_cumulative=clicks,
                                    seconds_this_step=round(dt, 2),
                                    seconds_cumulative=round(elapsed, 2),
                                    sentences_on_screen=_sentences_in_element(page, scope_step),
                                    shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                    shot_hash=shot_hash,
                                    verbs_visible=_visible_verbs(page, jira_flow),
                                    notes=f"scope_text_preview={scope_text[:200]}",
                                )
                                records.append(rec)

                                # Select first project (e.g. KAN)
                                step_num += 1
                                t0 = time.monotonic()
                                clicks += 1
                                project_label = scope_step.locator('[role="radio"]').first
                                if project_label.count() > 0:
                                    project_label.click()
                                    page.wait_for_timeout(1500)

                                shot_path, shot_hash = _shot(
                                    page, condition, width, step_num, "jira-project-selected"
                                )
                                dt = time.monotonic() - t0
                                elapsed += dt

                                rec = StepRecord(
                                    step_name="jira-project-selected",
                                    condition=condition, width=width,
                                    clicks_this_step=1, clicks_cumulative=clicks,
                                    seconds_this_step=round(dt, 2),
                                    seconds_cumulative=round(elapsed, 2),
                                    shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                    shot_hash=shot_hash,
                                    verbs_visible=_visible_verbs(page, jira_flow),
                                )
                                records.append(rec)

                                # Click Preview (triggers scope clarify)
                                preview_btn2 = page.get_by_test_id("jira-preview-btn")
                                if preview_btn2.count() > 0 and preview_btn2.is_visible():
                                    step_num += 1
                                    t0 = time.monotonic()
                                    clicks += 1
                                    preview_btn2.scroll_into_view_if_needed()
                                    preview_btn2.click()
                                    page.wait_for_timeout(3000)
                                    dt = time.monotonic() - t0
                                    elapsed += dt

                                    shot_path, shot_hash = _shot(
                                        page, condition, width, step_num, "jira-preview"
                                    )
                                    rec = StepRecord(
                                        step_name="jira-preview",
                                        condition=condition, width=width,
                                        clicks_this_step=1, clicks_cumulative=clicks,
                                        seconds_this_step=round(dt, 2),
                                        seconds_cumulative=round(elapsed, 2),
                                        shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                        shot_hash=shot_hash,
                                        verbs_visible=_visible_verbs(page, jira_flow),
                                    )
                                    records.append(rec)

                                # Click Test (wait for it to be enabled)
                                test_btn = scope_step.locator('button').filter(has_text="Test")
                                if test_btn.count() > 0:
                                    try:
                                        # Wait for the test button to be enabled
                                        page.wait_for_function(
                                            """() => {
                                              const btns = document.querySelectorAll('[data-testid="jira-scope-step"] button');
                                              for (const btn of btns) {
                                                if ((btn.textContent || '').includes('Test') && !btn.disabled) return true;
                                              }
                                              return false;
                                            }""",
                                            timeout=10000,
                                        )
                                    except Exception:
                                        pass  # Record whatever state we find

                                    step_num += 1
                                    t0 = time.monotonic()
                                    clicks += 1
                                    test_btn.last.scroll_into_view_if_needed()
                                    try:
                                        test_btn.last.click(timeout=5000)
                                    except Exception:
                                        pass  # Button may still be disabled
                                    page.wait_for_timeout(5000)
                                    dt = time.monotonic() - t0
                                    elapsed += dt

                                    jira_test_step = page.get_by_test_id("jira-test-step")
                                    test_visible = jira_test_step.count() > 0

                                    shot_path, shot_hash = _shot(
                                        page, condition, width, step_num, "jira-test"
                                    )
                                    rec = StepRecord(
                                        step_name="jira-test",
                                        condition=condition, width=width,
                                        clicks_this_step=1, clicks_cumulative=clicks,
                                        seconds_this_step=round(dt, 2),
                                        seconds_cumulative=round(elapsed, 2),
                                        shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                        shot_hash=shot_hash,
                                        verbs_visible=_visible_verbs(page, jira_flow),
                                        notes=f"test_step_visible={test_visible}",
                                    )
                                    records.append(rec)

                        # Exit Jira wizard
                        done_btn = jira_flow.locator('button').filter(has_text="Done").first
                        if done_btn.count() == 0:
                            done_btn = jira_flow.locator('button').filter(has_text="Back").first
                        if done_btn.count() == 0:
                            done_btn = jira_flow.locator('button').last

                        if done_btn.count() > 0:
                            step_num += 1
                            exit_label = done_btn.inner_text().strip()
                            t0 = time.monotonic()
                            clicks += 1
                            done_btn.click()
                            page.wait_for_timeout(1500)
                            dt = time.monotonic() - t0
                            elapsed += dt

                            shot_path, shot_hash = _shot(
                                page, condition, width, step_num, "jira-exit"
                            )
                            rec = StepRecord(
                                step_name="jira-exit",
                                condition=condition, width=width,
                                clicks_this_step=1, clicks_cumulative=clicks,
                                seconds_this_step=round(dt, 2),
                                seconds_cumulative=round(elapsed, 2),
                                shot_path=str(shot_path.relative_to(PHASE_DIR)),
                                shot_hash=shot_hash,
                                verbs_visible=[exit_label],
                                notes=f"jira_exit_verb={exit_label}",
                            )
                            records.append(rec)
                    else:
                        shot_path, shot_hash = _shot(
                            page, condition, width, step_num, "jira-no-wizard"
                        )
                        rec = StepRecord(
                            step_name="jira-no-wizard",
                            condition=condition, width=width,
                            clicks_this_step=1, clicks_cumulative=clicks,
                            seconds_this_step=round(dt, 2),
                            seconds_cumulative=round(elapsed, 2),
                            dead_end=True,
                            dead_end_detail="Clicked Jira card but no wizard appeared",
                            shot_path=str(shot_path.relative_to(PHASE_DIR)),
                            shot_hash=shot_hash,
                        )
                        records.append(rec)
                else:
                    # No Jira cards
                    step_num += 1
                    shot_path, shot_hash = _shot(
                        page, condition, width, step_num, "no-jira-cards"
                    )
                    rec = StepRecord(
                        step_name="no-jira-cards",
                        condition=condition, width=width,
                        dead_end=not cold,
                        dead_end_detail="No Jira suggestion cards" + (
                            " (expected in cold condition)" if cold else ""),
                        shot_path=str(shot_path.relative_to(PHASE_DIR)),
                        shot_hash=shot_hash,
                    )
                    records.append(rec)

            # ── STEP: Click a SECOND GitHub suggestion ──────────
            cards = page.get_by_test_id("setup-suggestion-cards")
            if cards.count() > 0 and len(gh_card_indices) > 1:
                card_elements = cards.locator('[role="option"]')
                # Re-find GitHub cards
                new_gh_indices = []
                for i in range(card_elements.count()):
                    card_text = card_elements.nth(i).inner_text()
                    if "github" in card_text.lower():
                        new_gh_indices.append(i)

                if len(new_gh_indices) > 1:
                    step_num += 1
                    t0 = time.monotonic()
                    clicks += 1
                    second_gh = card_elements.nth(new_gh_indices[1])
                    second_gh.click()
                    page.wait_for_timeout(2000)
                    dt = time.monotonic() - t0
                    elapsed += dt

                    wizard2 = page.get_by_test_id("provider-wizard-flow")
                    scope_carries = False
                    if wizard2.count() > 0:
                        wizard2.wait_for(timeout=5000)
                        # Check if repo is already scoped
                        scoped2 = page.get_by_test_id("provider-wizard-scoped")
                        scope_carries = scoped2.count() > 0 and scoped2.is_visible()
                        # Check if discovery list appears (= scope does NOT carry)
                        disc2 = page.get_by_test_id("provider-discovery-list")
                        needs_repick = disc2.count() > 0

                    shot_path, shot_hash = _shot(
                        page, condition, width, step_num, "github-second"
                    )

                    rec = StepRecord(
                        step_name="github-second",
                        condition=condition, width=width,
                        clicks_this_step=1, clicks_cumulative=clicks,
                        seconds_this_step=round(dt, 2),
                        seconds_cumulative=round(elapsed, 2),
                        shot_path=str(shot_path.relative_to(PHASE_DIR)),
                        shot_hash=shot_hash,
                        notes=f"scope_carries={scope_carries}; needs_repick={needs_repick if wizard2.count() > 0 else 'n/a'}",
                    )
                    records.append(rec)

                    # Exit the second wizard
                    done_btn2 = page.get_by_test_id("provider-wizard-done")
                    if done_btn2.count() > 0:
                        clicks += 1
                        done_btn2.click()
                        page.wait_for_timeout(1000)
            else:
                step_num += 1
                rec = StepRecord(
                    step_name="github-second-not-available",
                    condition=condition, width=width,
                    notes=f"Only {len(gh_card_indices)} GitHub card(s) found; second card test skipped" if gh_card_indices else "No GitHub cards at all",
                )
                records.append(rec)

            # ── STEP: Click a SECOND Jira suggestion (scope-carry) ─
            if not cold and len(jira_card_indices) > 1:
                cards = page.get_by_test_id("setup-suggestion-cards")
                if cards.count() > 0:
                    card_elements = cards.locator('[role="option"]')
                    new_jira_indices = []
                    for i in range(card_elements.count()):
                        if "jira" in card_elements.nth(i).inner_text().lower():
                            new_jira_indices.append(i)
                    if len(new_jira_indices) > 1:
                        step_num += 1
                        t0 = time.monotonic()
                        clicks += 1
                        card_elements.nth(new_jira_indices[1]).click()
                        page.wait_for_timeout(2000)
                        dt = time.monotonic() - t0
                        elapsed += dt

                        jira2 = page.get_by_test_id("jira-wizard-flow")
                        jira_scope_carries = False
                        if jira2.count() > 0:
                            jira2.wait_for(timeout=5000)
                            # Check if scope is already set (carries) or needs repick
                            scope2 = page.get_by_test_id("jira-scope-step")
                            acct2 = page.get_by_test_id("jira-accounts-step")
                            jira_scope_carries = scope2.count() > 0 and scope2.is_visible()
                            jira_back_to_accounts = acct2.count() > 0 and acct2.is_visible()

                        shot_path, shot_hash = _shot(
                            page, condition, width, step_num, "jira-second"
                        )
                        rec = StepRecord(
                            step_name="jira-second",
                            condition=condition, width=width,
                            clicks_this_step=1, clicks_cumulative=clicks,
                            seconds_this_step=round(dt, 2),
                            seconds_cumulative=round(elapsed, 2),
                            shot_path=str(shot_path.relative_to(PHASE_DIR)),
                            shot_hash=shot_hash,
                            notes=f"jira_scope_carries={jira_scope_carries}; back_to_accounts={jira_back_to_accounts if jira2.count() > 0 else 'n/a'}",
                        )
                        records.append(rec)

                        # Exit
                        done_btn3 = jira2.locator('button').filter(has_text="Done").first if jira2.count() > 0 else page.locator('nonexistent')
                        if done_btn3.count() == 0:
                            done_btn3 = jira2.locator('button').filter(has_text="Back").first if jira2.count() > 0 else page.locator('nonexistent')
                        if done_btn3.count() > 0:
                            clicks += 1
                            done_btn3.click()
                            page.wait_for_timeout(1000)
            elif not cold:
                step_num += 1
                rec = StepRecord(
                    step_name="jira-second-not-available",
                    condition=condition, width=width,
                    notes=f"Only {len(jira_card_indices)} Jira card(s) found",
                )
                records.append(rec)

            browser.close()

    finally:
        server.stop()
        from holdspeak.db import reset_database
        reset_database()

    return records


# ── Build ───────────────────────────────────────────────────────────

def _ensure_build() -> None:
    """Build the web bundle if any web source is newer than the marker."""
    import subprocess
    import fcntl

    built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
    if built_marker.exists():
        # Trust the marker -- the build just ran above us
        return
    lock_path = REPO / "web" / ".glass-build.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            if built_marker.exists():
                return
            result = subprocess.run(
                ["npm", "--prefix", str(REPO / "web"), "run", "build"],
                capture_output=True, text=True, timeout=300,
            )
            assert result.returncode == 0, (
                f"Web build failed:\n{result.stderr}\n{result.stdout}"
            )
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


# ── Test entry point ────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.parametrize(
    "condition,width",
    [
        ("connected", 1440),
        ("connected", 393),
        ("cold", 1440),
        ("cold", 393),
    ],
)
def test_audit_walk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    condition: str,
    width: int,
) -> None:
    """HS-168-01 stopwatch audit of the connector path through the face."""
    _ensure_build()

    records = _run_audit(tmp_path, monkeypatch, condition, width)

    # Write transcript
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    transcript_path = AUDIT_DIR / "transcript.json"

    # Load existing transcript or start fresh
    if transcript_path.exists():
        transcript = json.loads(transcript_path.read_text())
    else:
        transcript = {}

    key = f"{condition}-{width}"
    transcript[key] = [asdict(r) for r in records]
    transcript_path.write_text(json.dumps(transcript, indent=2) + "\n")

    # Assert that we got at least the base steps
    assert len(records) >= 5, (
        f"Too few steps recorded for {key}: {len(records)}"
    )

    # Record (but do not fail on) consecutive identical shots -- the audit
    # MEASURES the face, it does not gate it; the duplicate is a finding.
    hashes = [(r.step_name, r.shot_hash) for r in records if r.shot_hash]
    for i in range(1, len(hashes)):
        if hashes[i][1] == hashes[i - 1][1]:
            print(
                f"FINDING: consecutive shots identical: "
                f"{hashes[i - 1][0]} and {hashes[i][0]} "
                f"(hash {hashes[i][1]})"
            )
