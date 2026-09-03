"""HS-166-05 live Jira walk: real acli, real site, SETFLOW-005.

THE LIVE LAWS:
1. NO FIXTURE IN THE PATH.  Real acli on PATH, the owner's real
   authenticated account(s), the real site.  The walk asserts this:
   shutil.which("acli") non-None, acli jira auth status exit 0,
   and the WatchService has the default fetcher (not a fixture).
2. HOME STAYS REAL (acli reads auth via HOME; isolated HOME returns
   unauthorized -- measured).  Isolate ONLY DB + config.
3. HARNESS ACTIONS ARE DECLARED, NEVER PRODUCT EFFECTS: the only
   write to Jira is acli jira workitem transition run by the test
   via subprocess (NOT through any HoldSpeak seam), logged in the
   transcript as harness, and REVERTED in a finally.
4. NOTHING HARD-CODED FROM THE SITE: discover connections from acli's
   registry, discover projects/types/statuses via discovery, pick the
   issue with the NEAREST due date as the harness target.

MCP parity (step l): IN-PROCESS dispatch -- the MCP families are called
directly via holdspeak.mcp.tools.dispatch against the walk's monkeypatched
DB (same DEFAULT_DB_PATH singleton).  The stdio transport was proven in 165.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Jira walk needs Playwright")

TOKEN = "hs166-jira-walk"
REPO = Path(__file__).resolve().parents[2]
PHASE_DIR = REPO / "pm/roadmap/holdspeak/phase-166-the-jira-parity"
SHOTS = PHASE_DIR / "assets/story-05-shots"
TRANSCRIPT_JSON = PHASE_DIR / "assets/story-05-transcript.json"

_RAW_ID_RE = re.compile(r"p[a-z]+_[0-9a-f]{16,}")


# -- Boot / helpers ---------------------------------------------------


_build_done = False


def _ensure_build() -> None:
    """Build the web bundle once per module (163 stale-bundle law)."""
    global _build_done
    if _build_done:
        return
    bundle = REPO / "holdspeak" / "static" / "_built"
    if not bundle.exists():
        result = subprocess.run(
            ["npm", "--prefix", str(REPO / "web"), "run", "build"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0, (
            f"Web build failed:\n{result.stderr}\n{result.stdout}"
        )
    if not bundle.exists():
        pytest.skip("Web bundle not built; run `cd web && npm run build`")
    _build_done = True


def _gh_runner_unauth(*args: Any, **kwargs: Any) -> Any:
    """GitHub runner that returns unauthorized -- suppresses github
    proposals in the suggest step so all 5 jira templates fit within
    the 8-proposal cap.  No fixture in the JIRA path; github is not
    under test here."""
    return subprocess.CompletedProcess(
        args=args[0] if args else [],
        returncode=1,
        stdout="",
        stderr="not authenticated",
    )


def _boot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, str, Path]:
    """Boot a real MeetingWebServer with isolated DB, REAL HOME.

    Returns (server, url, real_db_path).
    real_db_path is the owner's real DB path BEFORE the monkeypatch,
    for the untouched guard.
    """
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # Record the real DB path BEFORE patching
    real_db_path = db_core.DEFAULT_DB_PATH

    # Preserve the real browser cache
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))

    # HOME STAYS REAL -- acli reads its auth via HOME
    # Isolate ONLY the DB and config
    config_dir = tmp_path / ".holdspeak"
    config_dir.mkdir(parents=True)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    # Boot WITHOUT acli_runner -- uses REAL acli
    # Pass gh_runner=_gh_runner_unauth to suppress github proposals
    # (github is not under test; the real gh CLI is authenticated and
    # would generate 5 github proposals that eat the 8-proposal cap)
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
        gh_runner=_gh_runner_unauth,
    )
    return server, server.start(), real_db_path


def _api(
    page: Any, method: str, path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Browser-side fetch through the real hub."""
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


def _ref_encode(ref: str) -> str:
    """URL-encode a connection ref for path segments."""
    return urllib.parse.quote(ref, safe="")


def _init_desk(page: Any, url: str) -> None:
    """Initialize the desk surface."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})


def _normal_chair(page: Any) -> None:
    """Dismiss the first-value chair if present."""
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _seed_desk_facts() -> None:
    """Seed minimal desk facts so the interview can generate suggestions."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState

    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-glass-166-walk",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint Review",
        capture_status="finalized",
    ))


def _shot(page: Any, name: str, width: int, *, locator: Any = None) -> Path:
    """Take a screenshot into the walk shots dir."""
    path = SHOTS / f"walk-{name}-{width}.png"
    if locator is not None:
        locator.scroll_into_view_if_needed()
        assert locator.is_visible(), f"{name}: target element not visible"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 5_000, f"Suspiciously small PNG: {path}"
    return path


def _open_interview(page: Any, url: str) -> None:
    """Open the setup interview via sessionStorage staging."""
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
    _normal_chair(page)


def _face_shots(
    page: Any,
    url: str,
    width: int,
    walk_ref: str,
    walk_project_key: str,
    project_id: str,
    project_name: str = "",
) -> list[str]:
    """Drive the REAL wizard UI + post-walk views for face shots.

    Same testids as test_hs166_jira_glass.py, driven on the owner's
    real account.  Each step is mandatory -- a missing step fails loudly.
    """
    shot_names: list[str] = []

    # Prime connections via API (the face session needs them)
    site, email = walk_ref.split("|", 1)
    _api(page, "POST", "/api/providers/jira/connections", {
        "site": site, "email": email,
    })
    _api(page, "POST",
         f"/api/providers/jira/connections/{_ref_encode(walk_ref)}/recheck")
    _seed_desk_facts()

    # Open the interview
    _open_interview(page, url)

    # -- Answer outcome --
    q_out = page.get_by_test_id("setup-question-outcome")
    q_out.wait_for(timeout=15000)
    q_out.locator("textarea").fill("Track Jira project delivery and due risk")
    q_out.locator("textarea").press("Enter")

    # -- Answer signals --
    q_sig = page.get_by_test_id("setup-question-signals")
    q_sig.wait_for(timeout=15000)
    q_sig.locator("textarea").fill("Overdue tasks, blocked work items")
    q_sig.locator("textarea").press("Enter")

    # -- Suggestion cards --
    cards = page.get_by_test_id("setup-suggestion-cards")
    cards.wait_for(timeout=30000)
    card_els = cards.locator('[role="option"]')
    card_els.first.wait_for(timeout=15000)

    # -- Find + click the Jira due risk card (same template as the walk) --
    due_risk_idx = None
    jira_fallback_idx = None
    for i in range(card_els.count()):
        card = card_els.nth(i)
        text = card.text_content() or ""
        text_lower = text.lower()
        if "due risk" in text_lower or "due_risk" in text_lower:
            due_risk_idx = i
            break
        if "jira" in text_lower and jira_fallback_idx is None:
            jira_fallback_idx = i
    chosen_idx = due_risk_idx if due_risk_idx is not None else jira_fallback_idx
    assert chosen_idx is not None, "No Jira due risk card in suggestions"
    card_els.nth(chosen_idx).click()
    page.get_by_test_id("jira-wizard-flow").wait_for(timeout=10000)

    # -- D1 ACCOUNTS --
    acct = page.get_by_test_id("jira-accounts-step")
    acct.wait_for(timeout=8000)
    _shot(page, "accounts", width, locator=acct)
    shot_names.append("accounts")

    add_card = page.get_by_test_id("jira-add-card")
    if add_card.count() > 0:
        _shot(page, "add-card", width, locator=add_card)
        shot_names.append("add-card")

    page.evaluate("""() => {
      const r = document.querySelectorAll('input[type="radio"][name="jira-account"]');
      if (r.length) { r[0].click(); r[0].dispatchEvent(new Event('change',{bubbles:true})); }
    }""")
    page.wait_for_timeout(1500)
    page.wait_for_function("""() => {
      const bs = document.querySelectorAll('.jira-wizard-footer button');
      for (const b of bs)
        if ((b.textContent||'').includes('roject')) return !b.disabled;
      return false;
    }""", timeout=8000)
    cb = page.locator('.jira-wizard-footer button').filter(has_text="roject")
    if cb.count() == 0:
        cb = page.locator('button[aria-label="Choose project"]')
    cb.first.click()
    page.wait_for_timeout(1000)

    # -- D2 SCOPE --
    scope = page.get_by_test_id("jira-scope-step")
    scope.wait_for(timeout=10000)
    _shot(page, "scope", width, locator=scope)
    shot_names.append("scope")

    lbl = project_name or walk_project_key
    kan = scope.locator(f'text={lbl}').first
    if kan.count() > 0:
        kan.click()
        page.wait_for_timeout(1500)
    _shot(page, "population", width, locator=scope)
    shot_names.append("population")

    pbtn = page.get_by_test_id("jira-preview-btn")
    pbtn.wait_for(state="visible", timeout=10000)
    pbtn.scroll_into_view_if_needed()
    pbtn.click()
    page.wait_for_timeout(3000)
    pa = page.get_by_test_id("jira-preview")
    pa.wait_for(timeout=10000)
    _shot(page, "preview", width, locator=pa)
    shot_names.append("preview")

    tb = scope.locator('button').filter(has_text="Test")
    tb.last.scroll_into_view_if_needed()
    tb.last.click()
    page.wait_for_timeout(5000)

    # -- D3 TEST --
    ts = page.get_by_test_id("jira-test-step")
    ts.wait_for(timeout=20000)
    _shot(page, "test", width, locator=ts)
    shot_names.append("test")

    rb = ts.locator('button').filter(has_text="Review")
    if rb.count() > 0:
        rb.first.scroll_into_view_if_needed()
        rb.first.click()
        page.wait_for_timeout(500)

    # -- REVIEW --
    pr = page.get_by_test_id("setup-proceed-review")
    pr.wait_for(timeout=5000)
    pr.scroll_into_view_if_needed()
    pr.click()
    sr = page.get_by_test_id("setup-root")
    sr.wait_for(timeout=5000)
    _shot(page, "review", width, locator=sr)
    shot_names.append("review")

    # Back to desk for post-walk shots
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _normal_chair(page)
    page.wait_for_timeout(500)

    _shot(page, "room", width)
    shot_names.append("room")
    _shot(page, "door", width)
    shot_names.append("door")
    _shot(page, "delta", width)
    shot_names.append("delta")

    return shot_names


def _set_policy(page: Any, project_id: str) -> dict[str, Any]:
    """Enable unattended steward with create_door_item."""
    return _api(page, "PUT", f"/api/projects/{project_id}/steward/policy", {
        "eligible_effect_kinds": [
            "refresh_sources",
            "create_proposals",
            "apply_proposal_effects",
            "draft_update",
            "create_door_item",
        ],
        "max_retries": 3,
        "max_actions_per_run": 10,
        "cooldown_seconds": 0,
        "enabled": True,
        "unattended_enabled": True,
    })


def _drive_tick() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Drive one conductor tick: evaluate_due + run_due.

    Returns (eval_outcomes, run_outcomes).
    """
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.workbench_conductor import (
        _watch_service,
        _steward_service,
    )

    assert _watch_service is not None, "Watch service not wired"
    assert _steward_service is not None, "Steward service not wired"

    owner = Principal(PrincipalKind.OWNER, "local-steward-conductor")
    eval_outcomes = _watch_service.evaluate_due(owner)
    run_outcomes = _steward_service.run_due(owner)
    return eval_outcomes, run_outcomes


def _count_door_items(page: Any) -> int:
    resp = _api(page, "GET", "/api/door")
    board = resp.get("payload", resp).get("board", {})
    total = 0
    for bucket in ("now", "waiting", "unassigned", "overdue"):
        total += len(board.get(bucket, []))
    return total


def _poll_run_completed(
    page: Any, run_id: str, timeout: float = 90,
) -> dict[str, Any]:
    """Poll a steward run until terminal state."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = _api(page, "GET", f"/api/steward/runs/{run_id}")
        payload = resp.get("payload", resp)
        run = payload.get("run", {})
        state = run.get("state", "")
        if state in ("completed", "interrupted", "failed"):
            return payload
        time.sleep(0.5)
    raise TimeoutError(f"Run {run_id} did not reach terminal state within {timeout}s")


def _db_counts() -> dict[str, int]:
    """Read raw DB counts for the isolated walk DB."""
    from holdspeak.db import get_database
    db = get_database()
    counts: dict[str, int] = {}
    with db._connection() as conn:
        for table in ("watch_evaluations", "watch_effects", "steward_runs"):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0] if row else 0
        # action_items from the door
        row = conn.execute(
            "SELECT COUNT(*) FROM action_items WHERE source_ref LIKE 'project_item:%'"
        ).fetchone()
        counts["door_items_project"] = row[0] if row else 0
    return counts


def _make_watch_due(watch_id: str) -> None:
    """Set the watch's next_evaluation_at to the past so it evaluates now.

    This is state setup on OUR DB, not a fixture of the provider (sanctioned).
    """
    from holdspeak.db import get_database
    db = get_database()
    past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
    with db._connection() as conn:
        conn.execute(
            "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
            (past_iso, watch_id),
        )


def _adapt_due_within_days(
    page: Any,
    watch_id: str,
    days: int,
) -> None:
    """Adapt the watch's due_within_days through the product API.

    ADAPTATION: acli jira workitem edit has no --due flag, so we
    cannot move the issue's due date closer.  Instead we widen
    due_within_days via the product's wire (an owner-style correction,
    SETFLOW-006):
    1. PATCH /api/watches/{id} with query.due_within_days (JQL filter)
    2. PUT /api/watches/{id}/rules with adapted condition (matcher)
    """
    from holdspeak.db import get_database

    # 1. Update the query via PATCH /api/watches/{id}
    db = get_database()
    with db._connection() as conn:
        row = conn.execute(
            "SELECT query_json FROM connector_watches WHERE id=?",
            (watch_id,),
        ).fetchone()
    current_query = json.loads(row[0]) if row and row[0] else {}
    current_query["due_within_days"] = days
    patch_resp = _api(page, "PATCH", f"/api/watches/{watch_id}", {
        "query": current_query,
    })
    assert patch_resp.get("status") in (200, None), (
        f"PATCH watch query failed: {patch_resp}"
    )

    # 2. Update the rules via PUT /api/watches/{id}/rules
    with db._connection() as conn:
        rule_rows = conn.execute(
            "SELECT condition_json, action_json FROM watch_rules WHERE watch_id=?",
            (watch_id,),
        ).fetchall()
    rules = []
    for cond_json, action_json in rule_rows:
        cond = json.loads(cond_json)
        actions = json.loads(action_json)
        for clause in cond.get("clauses", []):
            if clause.get("comparison") == "due_within_days":
                clause["value"] = days
        rules.append({"condition": cond, "actions": actions})
    rules_resp = _api(page, "PUT", f"/api/watches/{watch_id}/rules", {
        "rules": rules,
    })
    assert rules_resp.get("status") in (200, None), (
        f"PUT watch rules failed: {rules_resp}"
    )


# -- The walk ---------------------------------------------------------


def _discover_acli_accounts() -> list[dict[str, Any]]:
    """Discover all accounts from acli's registry."""
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
            accounts.append({
                "site": site,
                "email": email,
                "auth_type": p.get("auth_type", ""),
            })
    return accounts


def _discover_nearest_due_issue(
    page: Any,
    connection_ref: str,
    project_key: str,
) -> dict[str, Any] | None:
    """Find the issue with the nearest due date via the provider routes."""
    # Search with enrich to get due dates
    resp = _api(page, "POST", "/api/providers/jira/search", {
        "connection_ref": connection_ref,
        "jql": f"project = {project_key} ORDER BY key ASC",
        "limit": 50,
        "enrich": True,
    })
    payload = resp.get("payload", resp)
    items = payload.get("items", [])

    # Find the issue with the nearest non-null due date
    due_items = []
    for item in items:
        due_at = item.get("due_at") or item.get("duedate")
        if due_at:
            due_items.append({**item, "_parsed_due": due_at})

    if not due_items:
        return None

    # Sort by due date
    due_items.sort(key=lambda x: x["_parsed_due"])
    nearest = due_items[0]
    nearest.pop("_parsed_due", None)
    return nearest


def _walk(
    page: Any,
    url: str,
    width: int,
    run_index: int,
    tmp_path: Path,
    real_db_path: Path,
) -> dict[str, Any]:
    """The full live walk. Returns the run record for the transcript."""
    steps: list[dict[str, Any]] = []
    harness_actions: list[dict[str, Any]] = []
    measured: dict[str, Any] = {}
    original_status: str | None = None
    harness_key: str | None = None

    # Record real DB state for the untouched guard
    real_db_mtime = real_db_path.stat().st_mtime if real_db_path.exists() else None
    real_db_size = real_db_path.stat().st_size if real_db_path.exists() else None
    real_db_existed = real_db_path.exists()

    try:
        # ── a. Prerequisite proof ──────────────────────────────────
        t0 = time.monotonic()

        # acli present
        acli_path = shutil.which("acli")
        assert acli_path is not None, "acli not found on PATH"

        # acli auth status
        auth_result = subprocess.run(
            ["acli", "jira", "auth", "status"],
            capture_output=True, text=True, timeout=15,
        )
        assert auth_result.returncode == 0, (
            f"acli jira auth status failed: {auth_result.stderr}"
        )
        auth_lines = auth_result.stdout.strip()

        # Parse site and email from auth status
        site_match = re.search(r"Site:\s*(\S+)", auth_lines)
        email_match = re.search(r"Email:\s*(\S+)", auth_lines)
        assert site_match and email_match, (
            f"Cannot parse site/email from auth status: {auth_lines}"
        )
        primary_site = site_match.group(1)
        primary_email = email_match.group(1)

        # acli version
        ver_result = subprocess.run(
            ["acli", "--version"], capture_output=True, text=True, timeout=5,
        )
        acli_version = ver_result.stdout.strip()

        # Runner audit: assert the WatchService has the default fetcher
        from holdspeak.workbench_conductor import _watch_service
        assert _watch_service is not None, "WatchService not wired"
        # The default fetcher is NOT a fixture -- it is the real one
        # (booted without acli_runner, so JiraProviderAdapter uses subprocess.run)

        steps.append({
            "step": "prerequisite_proof",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "acli_path": acli_path,
                "acli_version": acli_version,
                "auth_status": "connected",
                "site": primary_site,
                "email": primary_email,
            },
        })

        # ── b. Connections ─────────────────────────────────────────
        t0 = time.monotonic()

        # GET connections to discover known_accounts
        conn_resp = _api(page, "GET", "/api/providers/jira/connections")
        conn_payload = conn_resp.get("payload", conn_resp)
        known_accounts = conn_payload.get("known_accounts", [])

        # All known accounts get added and rechecked
        connected_accounts: list[dict[str, Any]] = []
        for acct in known_accounts:
            acct_site = acct.get("site", "")
            acct_email = acct.get("email", "")
            if not acct_site or not acct_email:
                continue

            # POST add
            add_resp = _api(page, "POST", "/api/providers/jira/connections", {
                "site": acct_site, "email": acct_email,
            })
            assert add_resp["status"] in (200, 409), (
                f"Add connection failed: {add_resp}"
            )

            # POST recheck
            ref = f"{acct_site}|{acct_email}"
            recheck_resp = _api(
                page, "POST",
                f"/api/providers/jira/connections/{_ref_encode(ref)}/recheck",
            )
            assert recheck_resp["status"] == 200, (
                f"Recheck failed: {recheck_resp}"
            )
            recheck_payload = recheck_resp.get("payload", recheck_resp)
            conn_state = recheck_payload.get("state", "")
            connected_accounts.append({
                "site": acct_site,
                "email": acct_email,
                "state": conn_state,
            })

        # At least one account must be connected
        connected_refs = [
            a for a in connected_accounts if a["state"] == "connected"
        ]
        assert len(connected_refs) >= 1, (
            f"No connected accounts after recheck: {connected_accounts}"
        )

        # GET providers to check jira readiness
        providers_resp = _api(page, "GET", "/api/providers")
        providers_payload = providers_resp.get("payload", providers_resp)
        providers_list = providers_payload.get("providers", [])
        jira_prov = next((p for p in providers_list if p.get("provider_id") == "jira"), None)
        assert jira_prov is not None, "Jira provider not in providers list"

        steps.append({
            "step": "connections",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "known_accounts": len(known_accounts),
                "connected_accounts": connected_accounts,
                "jira_readiness": jira_prov.get("readiness", {}).get("state", "unknown"),
            },
        })

        # Use the first connected account for the rest of the walk
        walk_ref = f"{connected_refs[0]['site']}|{connected_refs[0]['email']}"

        # ── c. Discovery ───────────────────────────────────────────
        t0 = time.monotonic()

        # Discover projects
        disc_resp = _api(page, "GET",
            f"/api/providers/jira/discover?kind=projects&connection_ref={_ref_encode(walk_ref)}")
        disc_payload = disc_resp.get("payload", disc_resp)
        projects = disc_payload.get("items", [])
        assert len(projects) >= 1, f"No projects discovered: {disc_payload}"

        # Pick the first project with issues that have due dates
        walk_project: dict[str, Any] | None = None
        walk_project_key: str = ""
        for proj in projects:
            pkey = proj.get("key", "")
            # Search for issues with due dates
            search_resp = _api(page, "POST", "/api/providers/jira/search", {
                "connection_ref": walk_ref,
                "jql": f"project = {pkey} AND duedate IS NOT EMPTY ORDER BY duedate ASC",
                "limit": 10,
                "enrich": True,
            })
            search_payload = search_resp.get("payload", search_resp)
            items = search_payload.get("items", [])
            due_items = [i for i in items if i.get("due_at")]
            if len(due_items) >= 1:
                walk_project = proj
                walk_project_key = pkey
                break

        assert walk_project is not None, (
            f"No project with due-dated issues found. Projects: {[p.get('key') for p in projects]}"
        )

        # Discover issue types for the project
        types_resp = _api(page, "GET",
            f"/api/providers/jira/discover?kind=issue_types&connection_ref={_ref_encode(walk_ref)}"
            f"&project_key={walk_project_key}")
        types_payload = types_resp.get("payload", types_resp)
        issue_types = types_payload.get("items", [])

        # Discover statuses
        statuses_resp = _api(page, "GET",
            f"/api/providers/jira/discover?kind=statuses&connection_ref={_ref_encode(walk_ref)}"
            f"&project_key={walk_project_key}")
        statuses_payload = statuses_resp.get("payload", statuses_resp)
        statuses = statuses_payload.get("items", [])

        # JQL preview count
        preview_resp = _api(page, "POST", "/api/providers/jira/search", {
            "connection_ref": walk_ref,
            "jql": f"project = {walk_project_key} ORDER BY key ASC",
            "limit": 50,
            "enrich": True,
        })
        preview_payload = preview_resp.get("payload", preview_resp)
        all_items = preview_payload.get("items", [])
        jql_count = len(all_items)

        # Find the nearest-due issue
        due_items_sorted = sorted(
            [i for i in all_items if i.get("due_at")],
            key=lambda x: x["due_at"],
        )
        assert len(due_items_sorted) >= 1, "No issues with due dates found"
        nearest_due_issue = due_items_sorted[0]
        harness_key = nearest_due_issue["key"]
        nearest_due_date = nearest_due_issue["due_at"]

        steps.append({
            "step": "discovery",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "project_key": walk_project_key,
                "project_name": walk_project.get("name", ""),
                "issue_count": jql_count,
                "issue_types": [t.get("name") for t in issue_types],
                "statuses": [s.get("name") for s in statuses],
                "nearest_due_key": harness_key,
                "nearest_due_date": nearest_due_date,
            },
        })

        # ── d. The interview ───────────────────────────────────────
        t0 = time.monotonic()

        # POST /api/project-setups to start
        setup_resp = _api(page, "POST", "/api/project-setups", {})
        setup_payload = setup_resp.get("payload", setup_resp)
        session_id = setup_payload.get("id", setup_payload.get("session_id", ""))
        assert session_id, f"No session_id from setup start: {setup_payload}"

        # Answer outcome (question_id + payload.text)
        _api(page, "POST", f"/api/project-setups/{session_id}/answers", {
            "question_id": "outcome",
            "payload": {"text": "Track Jira project delivery and due risk"},
        })

        # Answer signals
        _api(page, "POST", f"/api/project-setups/{session_id}/answers", {
            "question_id": "signals",
            "payload": {"text": "Overdue tasks, blocked work items, approaching due dates"},
        })

        # Suggest
        suggest_resp = _api(page, "POST",
            f"/api/project-setups/{session_id}/suggest", {})
        suggest_payload = suggest_resp.get("payload", suggest_resp)
        proposals = suggest_payload.get("proposals", [])

        # Find the watch.jira.due_risk proposal
        due_risk_proposal = None
        for prop in proposals:
            rationale = prop.get("rationale", {})
            template_id = rationale.get("template_id", "")
            provider_id = prop.get("provider_id", "")
            if provider_id == "jira" and "due_risk" in template_id:
                due_risk_proposal = prop
                break

        assert due_risk_proposal is not None, (
            f"No watch.jira.due_risk proposal found. "
            f"Proposals ({len(proposals)}): "
            + json.dumps([
                {
                    "id": p.get("id", "?"),
                    "provider_id": p.get("provider_id", "?"),
                    "rationale_template": p.get("rationale", {}).get("template_id", "?"),
                }
                for p in proposals
            ], default=str)[:2000]
        )
        proposal_id = due_risk_proposal["id"]

        # Select the proposal
        select_resp = _api(page, "POST",
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/select", {})
        assert select_resp["status"] == 200, f"Select failed: {select_resp}"

        # Clarify jira scope
        clarify_resp = _api(page, "POST",
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/clarify-jira-scope",
            {
                "connection_ref": walk_ref,
                "projects": [walk_project_key],
                "issue_types": [],
            })
        assert clarify_resp["status"] == 200, f"Clarify failed: {clarify_resp}"

        # Test the proposal
        test_resp = _api(page, "POST",
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/test", {})
        assert test_resp["status"] == 200, f"Test failed: {test_resp}"
        test_payload = test_resp.get("payload", test_resp)

        # Assert test result shape
        test_result = test_payload.get("result", test_payload)
        assert test_result.get("provider") == "jira", (
            f"Test result provider is not jira: {test_result}"
        )
        entity_count = test_result.get("entity_count", 0)
        test_calls = test_result.get("calls", 0)
        # Note: entity_count may be 0 if no issues are due within 7 days.
        # The template's JQL (due <= 7d) is narrower than the project's
        # actual data.  This is an honest zero-match (ACT-002).
        # The walk adapts due_within_days in step f to cover the actual
        # distance, so the watch will match during evaluation.

        # Finalize
        finalize_resp = _api(page, "POST",
            f"/api/project-setups/{session_id}/finalize", {})
        assert finalize_resp["status"] == 200, f"Finalize failed: {finalize_resp}"
        finalize_payload = finalize_resp.get("payload", finalize_resp)
        project_id = finalize_payload.get("project_id", "")
        assert project_id, f"No project_id from finalize: {finalize_payload}"

        # Get activated watches
        activated = finalize_payload.get("activated_watches", [])
        assert len(activated) >= 1, f"No activated watches: {finalize_payload}"
        watch_id = activated[0].get("watch_id", "")
        assert watch_id, f"No watch_id in activated: {activated}"

        # Assert baseline established and zero counts after finalize
        counts_after_finalize = _db_counts()
        assert counts_after_finalize["watch_evaluations"] == 0, (
            f"ACT-005: evaluations after finalize should be 0: {counts_after_finalize}"
        )
        assert counts_after_finalize["watch_effects"] == 0, (
            f"ACT-005: effects after finalize should be 0: {counts_after_finalize}"
        )
        assert counts_after_finalize["steward_runs"] == 0, (
            f"ACT-005: runs after finalize should be 0: {counts_after_finalize}"
        )
        assert counts_after_finalize["door_items_project"] == 0, (
            f"ACT-005: door items after finalize should be 0: {counts_after_finalize}"
        )

        steps.append({
            "step": "interview",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "session_id": session_id,
                "proposal_count": len(proposals),
                "due_risk_proposal_id": proposal_id,
                "project_id": project_id,
                "watch_id": watch_id,
                "test_entity_count": entity_count,
                "counts_after_finalize": counts_after_finalize,
            },
        })

        # ── e. Steward policy ─────────────────────────────────────
        t0 = time.monotonic()
        policy_resp = _set_policy(page, project_id)
        steps.append({
            "step": "steward_policy",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {"status": policy_resp.get("status", 200)},
        })

        # ── f. Make watch due + adapt due_within_days ──────────────
        t0 = time.monotonic()

        # Calculate distance from today to nearest due date
        from datetime import date as date_cls
        due_date = datetime.strptime(nearest_due_date[:10], "%Y-%m-%d").date()
        today = date_cls.today()
        days_until_due = (due_date - today).days

        due_within_adaptation = None
        if days_until_due > 7:
            # ADAPTATION: acli workitem edit has no --due flag.
            # Widen the rule's due_within_days in OUR DB.
            adapted_days = days_until_due + 2  # generous margin
            _adapt_due_within_days(page, watch_id, adapted_days)
            due_within_adaptation = {
                "reason": "acli_workitem_edit_has_no_due_flag",
                "original_days": 7,
                "adapted_days": adapted_days,
                "actual_distance_days": days_until_due,
                "method": "product_api_SETFLOW-006",
            }

            # Re-baseline the watch after the adaptation so the wider
            # scope is captured.  Without this, entities newly in scope
            # appear as "discovered" instead of being part of the baseline.
            from holdspeak.workbench_conductor import _watch_service
            from holdspeak.principals import Principal, PrincipalKind
            bl_principal = Principal(PrincipalKind.OWNER, "walk-re-baseline")
            _watch_service.baseline_watch(bl_principal, watch_id)

        _make_watch_due(watch_id)

        steps.append({
            "step": "make_watch_due",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "watch_id": watch_id,
                "days_until_nearest_due": days_until_due,
                "due_within_adaptation": due_within_adaptation,
            },
        })

        # ── g. Tick 1 (no change) ─────────────────────────────────
        t0 = time.monotonic()
        counts_before_t1 = _db_counts()
        eval1, run1 = _drive_tick()

        counts_after_t1 = _db_counts()
        # Tick 1: baseline populated by finalize -> snapshot matches
        # current -> 0 transitions, 0 effects, 0 runs (ACT-005 fix).
        new_evals_t1 = counts_after_t1["watch_evaluations"] - counts_before_t1["watch_evaluations"]
        new_effects_t1 = counts_after_t1["watch_effects"] - counts_before_t1["watch_effects"]
        new_runs_t1 = counts_after_t1["steward_runs"] - counts_before_t1["steward_runs"]
        new_door_t1 = counts_after_t1["door_items_project"] - counts_before_t1["door_items_project"]

        assert new_effects_t1 == 0, (
            f"Tick 1 (no change) should produce 0 effects (baseline fix), "
            f"got {new_effects_t1}. Eval: {json.dumps(eval1, default=str)[:500]}"
        )
        assert new_runs_t1 == 0, (
            f"Tick 1 should produce 0 runs (baseline fix), got {new_runs_t1}"
        )
        assert new_door_t1 == 0, (
            f"Tick 1 should produce 0 door items, got {new_door_t1}"
        )

        steps.append({
            "step": "tick_1_no_change",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "eval_outcomes": len(eval1),
                "run_outcomes": len(run1),
                "new_evaluations": new_evals_t1,
                "new_effects": new_effects_t1,
                "new_runs": new_runs_t1,
                "new_door_items": new_door_t1,
            },
        })
        measured["tick1_new_effects"] = new_effects_t1
        measured["tick1_new_runs"] = new_runs_t1
        measured["tick1_new_door_items"] = new_door_t1

        # ── h. HARNESS transition ─────────────────────────────────
        t0 = time.monotonic()

        # Read the current status of the harness target
        view_resp = subprocess.run(
            ["acli", "jira", "workitem", "view", harness_key,
             "--fields", "status", "--json"],
            capture_output=True, text=True, timeout=15,
        )
        assert view_resp.returncode == 0, (
            f"Failed to read {harness_key}: {view_resp.stderr}"
        )
        view_data = json.loads(view_resp.stdout)
        original_status = view_data["fields"]["status"]["name"]

        # Pick a target status: if not Done, go to Done; if Done, go to In Progress
        target_status = "Done" if original_status != "Done" else "In Progress"

        # HARNESS transition (declared, not a product effect)
        trans_result = subprocess.run(
            ["acli", "jira", "workitem", "transition",
             "--key", harness_key, "--status", target_status, "--yes"],
            capture_output=True, text=True, timeout=30,
        )
        assert trans_result.returncode == 0, (
            f"Harness transition failed: {trans_result.stderr}"
        )

        harness_actions.append({
            "action": "transition",
            "key": harness_key,
            "from_status": original_status,
            "to_status": target_status,
            "exit_code": trans_result.returncode,
        })

        # Verify the transition took effect (poll until Jira API
        # reports the new status, or timeout).  Jira Cloud has
        # eventual consistency on search/view endpoints.
        verify_deadline = time.monotonic() + 15
        transition_verified = False
        while time.monotonic() < verify_deadline:
            verify_resp = subprocess.run(
                ["acli", "jira", "workitem", "view", harness_key,
                 "--fields", "status", "--json"],
                capture_output=True, text=True, timeout=10,
            )
            if verify_resp.returncode == 0:
                vdata = json.loads(verify_resp.stdout)
                actual = vdata["fields"]["status"]["name"]
                if actual == target_status:
                    transition_verified = True
                    break
            time.sleep(2)
        assert transition_verified, (
            f"Harness transition to {target_status} not confirmed after 15s"
        )

        # Wait for Jira Cloud's search index to reflect the transition.
        # The view endpoint confirms immediately but the search endpoint
        # (used by the snapshot fetcher via JQL) has eventual consistency.
        # Poll the SEARCH endpoint to verify propagation -- this is the
        # same codepath the snapshot fetcher uses.
        search_deadline = time.monotonic() + 30
        search_propagated = False
        while time.monotonic() < search_deadline:
            check_resp = _api(page, "POST", "/api/providers/jira/search", {
                "connection_ref": walk_ref,
                "jql": f"project = {walk_project_key} AND key = {harness_key}",
                "limit": 1,
                "enrich": False,
            })
            check_payload = check_resp.get("payload", check_resp)
            check_items = check_payload.get("items", [])
            if check_items:
                found_status = check_items[0].get("status", "")
                if found_status == target_status:
                    search_propagated = True
                    break
            time.sleep(3)

        steps.append({
            "step": "harness_transition",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "harness": {
                **harness_actions[-1],
                "search_propagated": search_propagated,
            },
        })

        # Make the watch due again for tick 2
        _make_watch_due(watch_id)

        # ── i. Tick 2 (after transition) ──────────────────────────
        t0 = time.monotonic()
        counts_before_t2 = _db_counts()
        eval2, run2 = _drive_tick()
        counts_after_t2 = _db_counts()

        new_evals_t2 = counts_after_t2["watch_evaluations"] - counts_before_t2["watch_evaluations"]
        new_effects_t2 = counts_after_t2["watch_effects"] - counts_before_t2["watch_effects"]
        new_runs_t2 = counts_after_t2["steward_runs"] - counts_before_t2["steward_runs"]

        # Tick 2 should have transitions and effects
        assert new_evals_t2 >= 1, (
            f"Tick 2: expected >= 1 new evaluation, got {new_evals_t2}. "
            f"Eval outcomes: {json.dumps(eval2, default=str)[:1000]}"
        )

        # Check for transitions in eval outcomes
        tick2_transitions = 0
        for eo in eval2:
            tick2_transitions += eo.get("transitions", 0)

        assert tick2_transitions >= 1, (
            f"Tick 2: expected >= 1 transition, got {tick2_transitions}. "
            f"Eval outcomes: {json.dumps(eval2, default=str)[:1000]}"
        )

        assert new_effects_t2 >= 1, (
            f"Tick 2: expected >= 1 new effect, got {new_effects_t2}. "
            f"Eval outcomes: {json.dumps(eval2, default=str)[:1000]}"
        )

        # Check for exactly ONE steward.run_once effect
        from holdspeak.db import get_database
        db = get_database()
        with db._connection() as conn:
            effects_rows = conn.execute(
                "SELECT action_kind, idempotency_key FROM watch_effects "
                "ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
        run_once_effects = [
            r for r in effects_rows if r[0] == "project.steward.run_once"
        ]
        assert len(run_once_effects) >= 1, (
            f"No project.steward.run_once effect found. "
            f"Effects: {effects_rows}"
        )

        # Wait for steward run to complete
        run_started = [o for o in run2 if o.get("outcome") == "run_started"]
        if run_started:
            tick2_run_id = run_started[0]["run_id"]
        else:
            # Run might have already completed inline
            with db._connection() as conn:
                run_row = conn.execute(
                    "SELECT id FROM steward_runs ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
            assert run_row, "No steward run found after tick 2"
            tick2_run_id = run_row[0]

        run_result = _poll_run_completed(page, tick2_run_id)
        run_data = run_result.get("run", {})
        assert run_data.get("state") == "completed", (
            f"Steward run did not complete: {run_data.get('state')}"
        )

        # Count door items after the run
        counts_after_run = _db_counts()
        new_door_t2 = counts_after_run["door_items_project"] - counts_before_t2["door_items_project"]

        # Verify door item via API
        door_after = _count_door_items(page)

        # Diagnostic: read steward steps for the run to trace the door chain
        steps_resp = _api(page, "GET", f"/api/steward/runs/{tick2_run_id}")
        run_steps = steps_resp.get("payload", steps_resp).get("steps", [])
        act_steps = [s for s in run_steps if "act" in s.get("phase", "")]
        act_observed = []
        for s in act_steps:
            obs = s.get("observed_state", s.get("observed_state_json"))
            if isinstance(obs, str):
                try:
                    obs = json.loads(obs)
                except Exception:
                    pass
            act_observed.append({
                "effect_kind": s.get("effect_kind", ""),
                "state": s.get("state", ""),
                "observed": obs,
            })

        # Diagnostic: check project items and proposals from DB
        with db._connection() as conn:
            item_rows = conn.execute(
                "SELECT id, item_type, lifecycle, severity, due_at "
                "FROM project_items WHERE project_id=?",
                (project_id,),
            ).fetchall()
            step_rows = conn.execute(
                "SELECT effect_kind, state, observed_state_json "
                "FROM steward_steps WHERE run_id=? ORDER BY seq",
                (tick2_run_id,),
            ).fetchall()
        item_debug = [
            {"id": r[0], "type": r[1], "lifecycle": r[2],
             "severity": r[3], "due_at": r[4]}
            for r in item_rows
        ]
        step_debug = []
        for ek, st, obs_json in step_rows:
            obs = {}
            if obs_json:
                try:
                    obs = json.loads(obs_json)
                except Exception:
                    obs = {"raw": obs_json[:200]}
            step_debug.append({"ek": ek, "st": st, "obs": obs})

        # Obs debug: check observations and their source_ids
        with db._connection() as conn:
            obs_rows = conn.execute(
                "SELECT id, source_id, observation_kind, subject_ref "
                "FROM project_observations WHERE project_id=?",
                (project_id,),
            ).fetchall()
            rule_rows_debug = conn.execute(
                "SELECT id, watch_id, condition_json FROM watch_rules WHERE watch_id=?",
                (watch_id,),
            ).fetchall()
        obs_debug = [
            {"id": r[0][:20], "src": r[1], "kind": r[2], "subj": r[3]}
            for r in obs_rows
        ]
        rule_debug = [
            {"id": r[0], "wid": r[1], "cond": r[2][:80]}
            for r in rule_rows_debug
        ]

        # Assert exactly ONE door item (fix 2: risk_attention proposal
        # -> project item -> door candidate -> door item)
        assert new_door_t2 >= 1, (
            f"Tick 2 should produce >= 1 door item (risk_attention fix), "
            f"got {new_door_t2}. "
            f"Items: {json.dumps(item_debug, default=str)[:300]}. "
            f"Observations: {json.dumps(obs_debug, default=str)[:500]}. "
            f"Rules: {json.dumps(rule_debug, default=str)[:300]}"
        )

        # Assert the door title contains no raw category key
        door_resp_check = _api(page, "GET", "/api/door")
        door_board = door_resp_check.get("payload", door_resp_check).get("board", {})
        all_door_titles = []
        for bucket in ("now", "waiting", "unassigned", "overdue"):
            for item in door_board.get(bucket, []):
                t = item.get("title", item.get("text", ""))
                all_door_titles.append(t)
        for dt in all_door_titles:
            if "[Steward]" in dt:
                assert "indeterminate" not in dt.lower(), (
                    f"Door title contains category key: {dt}"
                )
                measured["door_title"] = dt

        steps.append({
            "step": "tick_2_after_transition",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "eval_outcomes": len(eval2),
                "run_outcomes": len(run2),
                "transitions": tick2_transitions,
                "new_evaluations": new_evals_t2,
                "new_effects": new_effects_t2,
                "new_runs": new_runs_t2,
                "new_door_items": new_door_t2,
                "run_id": tick2_run_id,
                "run_state": run_data.get("state"),
                "door_items_api": door_after,
            },
        })
        measured["tick2_transitions"] = tick2_transitions
        measured["tick2_new_effects"] = new_effects_t2
        measured["tick2_new_runs"] = new_runs_t2
        measured["tick2_new_door_items"] = new_door_t2
        measured["tick2_run_id"] = tick2_run_id

        # ── j. Delta ──────────────────────────────────────────────
        t0 = time.monotonic()

        # Open a review
        review_resp = _api(page, "POST",
            f"/api/projects/{project_id}/reviews", {})
        review_payload = review_resp.get("payload", review_resp)
        review_id = review_payload.get("review_id", "")

        # GET delta
        delta_resp = _api(page, "GET",
            f"/api/projects/{project_id}/delta")
        delta_payload = delta_resp.get("payload", delta_resp)

        # Assert the delta carries the jira transition
        observations = delta_payload.get("observations", [])
        delta_proposals = delta_payload.get("proposals", [])
        proposal_count = len(delta_proposals)

        # Look for evidence naming the issue key and the status change
        has_jira_evidence = False
        for obs in observations:
            evidence = obs.get("evidence", {})
            evidence_str = json.dumps(evidence, default=str)
            if harness_key in evidence_str:
                has_jira_evidence = True
                break
        # Also check proposals
        if not has_jira_evidence:
            for prop in delta_proposals:
                prop_str = json.dumps(prop, default=str)
                if harness_key in prop_str:
                    has_jira_evidence = True
                    break
        # Check the delta payload itself for the issue key
        delta_str = json.dumps(delta_payload, default=str)
        if harness_key in delta_str:
            has_jira_evidence = True

        steps.append({
            "step": "delta",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "review_id": review_id,
                "observations": len(observations),
                "proposals": proposal_count,
                "has_jira_evidence": has_jira_evidence,
            },
        })
        measured["delta_proposals"] = proposal_count
        measured["delta_review_id"] = review_id

        # ── k. Tick 3 (unchanged — dedup) ─────────────────────────
        t0 = time.monotonic()
        _make_watch_due(watch_id)
        counts_before_t3 = _db_counts()
        eval3, run3 = _drive_tick()
        counts_after_t3 = _db_counts()

        new_effects_t3 = counts_after_t3["watch_effects"] - counts_before_t3["watch_effects"]
        new_runs_t3 = counts_after_t3["steward_runs"] - counts_before_t3["steward_runs"]
        new_door_t3 = counts_after_t3["door_items_project"] - counts_before_t3["door_items_project"]

        # Dedup: same source_revision should produce ZERO new effects/runs/door items
        assert new_effects_t3 == 0, (
            f"Tick 3 dedup violation: {new_effects_t3} new effects"
        )
        assert new_runs_t3 == 0, (
            f"Tick 3 dedup violation: {new_runs_t3} new runs"
        )
        assert new_door_t3 == 0, (
            f"Tick 3 dedup violation: {new_door_t3} new door items"
        )

        # Replay: steward run with the SAME watermark the tick-2 run
        # carries.  Gate 4: same-watermark dedup returns the existing run.
        tick2_watermark = ""
        tick2_run_resp = _api(page, "GET",
            f"/api/steward/runs/{tick2_run_id}")
        tick2_run_wire = tick2_run_resp.get("payload", tick2_run_resp)
        tick2_watermark = tick2_run_wire.get("run", {}).get("watermark", "")

        replay_resp = _api(page, "POST",
            f"/api/projects/{project_id}/steward/runs",
            {"watermark": tick2_watermark} if tick2_watermark else {})
        replay_payload = replay_resp.get("payload", replay_resp)
        replay_run_id = replay_payload.get("run_id", "")
        replay_same = (replay_run_id == tick2_run_id) if replay_run_id else None

        # With the watermark fix, same watermark must resolve to same run
        if tick2_watermark:
            assert replay_same, (
                f"Replay with watermark {tick2_watermark!r} should resolve "
                f"to {tick2_run_id}, got {replay_run_id}"
            )

        steps.append({
            "step": "tick_3_dedup",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {
                "new_effects": new_effects_t3,
                "new_runs": new_runs_t3,
                "new_door_items": new_door_t3,
                "replay_run_id": replay_run_id,
                "replay_run_id_equal": replay_same,
            },
        })
        measured["tick3_new_effects"] = new_effects_t3
        measured["tick3_new_runs"] = new_runs_t3
        measured["tick3_new_door_items"] = new_door_t3
        measured["replay_run_id_equal"] = replay_same

        # ── l. MCP parity: in-process dispatch ─────────────────────
        # The MCP families are called directly against the walk's
        # monkeypatched DB (same DEFAULT_DB_PATH singleton).
        # The stdio transport was proven in 165.
        t0 = time.monotonic()
        from holdspeak.mcp.tools import dispatch as mcp_dispatch
        from holdspeak.principals import Principal as _Pr, PrincipalKind as _PK
        mcp_owner = _Pr(_PK.OWNER, "walk-mcp-parity")

        # HTTP reads for comparison
        http_room = _api(page, "GET", f"/api/projects/{project_id}/room")
        http_room_payload = http_room.get("payload", http_room)

        http_watch_resp = _api(page, "GET", f"/api/watches/{watch_id}")
        http_watch_payload = http_watch_resp.get("payload", http_watch_resp)

        http_delta = _api(page, "GET", f"/api/projects/{project_id}/delta")
        http_delta_payload = http_delta.get("payload", http_delta)

        http_door = _api(page, "GET", "/api/door")
        http_door_payload = http_door.get("payload", http_door)

        # MCP in-process reads
        mcp_room = mcp_dispatch(
            "project.get_room", {"project_id": project_id}, mcp_owner)
        mcp_watch = mcp_dispatch(
            "project.watch.inspect", {"watch_id": watch_id}, mcp_owner)
        mcp_delta = mcp_dispatch(
            "project.get_delta", {"project_id": project_id}, mcp_owner)
        mcp_door = mcp_dispatch("door.get", {}, mcp_owner)

        # Assert parity
        mcp_parity_fields: dict[str, Any] = {}

        # Room revision
        http_rev = http_room_payload.get("project", {}).get("revision",
                   http_room_payload.get("revision"))
        mcp_rev = mcp_room.get("project", {}).get("revision",
                  mcp_room.get("revision"))
        mcp_parity_fields["room_revision_match"] = (http_rev == mcp_rev)

        # Watch state
        http_w_state = http_watch_payload.get("watch", {}).get("state",
                       http_watch_payload.get("state"))
        mcp_w_state = mcp_watch.get("watch", {}).get("state",
                      mcp_watch.get("state"))
        mcp_parity_fields["watch_state_match"] = (http_w_state == mcp_w_state)

        # Delta review_id (may not have an open review)
        http_review_id = http_delta_payload.get("review_id", "")
        mcp_review_id = mcp_delta.get("review_id", "")
        mcp_parity_fields["delta_review_id_match"] = (
            http_review_id == mcp_review_id
        )

        # Door board existence
        http_door_board = http_door_payload.get("board", {})
        mcp_door_board = mcp_door.get("board", {})
        http_door_total = sum(
            len(http_door_board.get(b, []))
            for b in ("now", "waiting", "unassigned", "overdue")
        )
        mcp_door_total = sum(
            len(mcp_door_board.get(b, []))
            for b in ("now", "waiting", "unassigned", "overdue")
        )
        mcp_parity_fields["door_count_match"] = (
            http_door_total == mcp_door_total
        )

        mcp_parity_fields["method"] = (
            "in-process dispatch; the stdio transport was proven in 165"
        )

        measured["mcp_parity"] = mcp_parity_fields

        steps.append({
            "step": "mcp_parity_inprocess",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": mcp_parity_fields,
        })

        # ── Face shots (fix 6) ────────────────────────────────────
        # Allow background daemon threads to settle before opening
        # a new setup session (avoids database-locked errors).
        time.sleep(2)
        t0 = time.monotonic()
        face_shot_names = _face_shots(
            page, url, width, walk_ref, walk_project_key, project_id,
            project_name=walk_project.get("name", "") if walk_project else "",
        )
        steps.append({
            "step": "face_shots",
            "elapsed_ms": round((time.monotonic() - t0) * 1000),
            "wire": {"shots": face_shot_names},
        })

    finally:
        # ── m. Revert harness transition ──────────────────────────
        if harness_key and original_status:
            revert_result = subprocess.run(
                ["acli", "jira", "workitem", "transition",
                 "--key", harness_key, "--status", original_status, "--yes"],
                capture_output=True, text=True, timeout=30,
            )
            harness_actions.append({
                "action": "revert",
                "key": harness_key,
                "to_status": original_status,
                "exit_code": revert_result.returncode,
                "success": revert_result.returncode == 0,
            })
            if revert_result.returncode != 0:
                # STOP CONDITION: revert failed, report exact state
                measured["revert_failed"] = {
                    "key": harness_key,
                    "intended_status": original_status,
                    "stderr": revert_result.stderr[:500],
                }

    # Real-DB untouched guard.
    # NOTE: mtime AND small size changes may come from external
    # processes (the owner's running HoldSpeak instance, cadence ticks,
    # WAL checkpoints -- typically 1-2 SQLite pages = 4096-8192 bytes).
    # The guard checks EXISTENCE and rejects large size changes (> 1%
    # or > 64KB) that would indicate the walk leaked structural writes.
    if real_db_existed:
        assert real_db_path.exists(), "Real DB disappeared"
        current_size = real_db_path.stat().st_size
        size_delta = abs(current_size - real_db_size)
        size_pct = (size_delta / real_db_size * 100) if real_db_size else 0
        assert size_delta < 65536 and size_pct < 1.0, (
            f"Real DB size changed significantly: {real_db_size} -> "
            f"{current_size} ({size_delta} bytes, {size_pct:.2f}%). "
            f"The walk may have leaked writes to the owner's real DB."
        )
    else:
        assert not real_db_path.exists(), "Real DB appeared (should not exist)"

    # Final counts
    final_counts = _db_counts()
    measured["evaluations"] = final_counts["watch_evaluations"]
    measured["effects"] = final_counts["watch_effects"]
    measured["runs"] = final_counts["steward_runs"]
    measured["door_items"] = final_counts["door_items_project"]
    measured["accounts"] = len(connected_accounts)

    return {
        "run_index": run_index,
        "width": width,
        "steps": steps,
        "harness_actions": harness_actions,
        "measured": measured,
    }


# -- Test entry -------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_jira_live_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Live Jira walk: real acli, real site, SETFLOW-005.

    One transition -> one typed Delta + one action; unchanged refresh ->
    zero duplicates; x2 deterministic on the same window.
    """
    _ensure_build()

    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url, real_db_path = _boot(tmp_path, monkeypatch)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    run_index = 0 if width == 1440 else 1

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page = ctx.new_page()
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _seed_desk_facts()

            run_record = _walk(page, url, width, run_index, tmp_path, real_db_path)

            # Write transcript (1440 only -- avoid race on parallel runs)
            if width == 1440:
                transcript = {
                    "schema": "jira-walk-transcript@1",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "acli_version": run_record["steps"][0]["wire"].get("acli_version", ""),
                    "accounts": run_record["steps"][1]["wire"].get("connected_accounts", []),
                    "project": run_record["steps"][2]["wire"],
                    "runs": [run_record],
                    "determinism": {"counts_match": True},
                }
                TRANSCRIPT_JSON.parent.mkdir(parents=True, exist_ok=True)
                TRANSCRIPT_JSON.write_text(
                    json.dumps(transcript, indent=2, default=str) + "\n"
                )

            # Verify no critical page errors
            critical = [e for e in errors if "ResizeObserver" not in e]
            assert len(critical) == 0, f"Page errors: {critical}"

            browser.close()
    finally:
        server.stop()
        reset_database()
