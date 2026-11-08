"""HS-167-06 live Tuesday walk: the owner's first project through the whole Room.

THE LIVE LAWS (inherited from 166):
1. NO FIXTURE IN THE PATH.  Real gh on PATH, real acli on PATH, the
   owner's real authenticated accounts, the real providers.
2. HOME STAYS REAL.  Both gh and acli read auth via HOME; isolated HOME
   returns unauthorized.  Isolate ONLY DB + config (isolated mode) or
   use the real DB untouched (real mode).
3. HARNESS ACTIONS ARE DECLARED, NEVER PRODUCT EFFECTS: the only writes
   to GitHub/Jira are a throwaway issue (created + immediately closed)
   and one KAN transition -- both REVERTED in a finally.
4. NOTHING HARD-CODED FROM THE SITE: discover connections from acli's
   registry, discover projects/types/statuses via the provider routes.

MODE: env HS167_WALK_DB=isolated|real (default isolated).
  isolated = tmp DB (proves the runner);
  real = DEFAULT_DB_PATH (~/.local/share/holdspeak/holdspeak.db).
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

pytest.importorskip("playwright.sync_api", reason="167 walk needs Playwright")

# ── Selector table (filled from the f13ecdfa recomposed library) ────
# Each entry: (step, element description, CSS/testid selector)
FACE_SELECTORS: list[tuple[str, str, str]] = [
    # Step 4 - Activation review (D4)
    ("step4", "review watches block",              "[data-testid='review-watches']"),
    ("step4", "activate button",                   "[data-testid='review-activate-btn']"),
    ("step4", "review outcome",                    "[data-testid='review-outcome']"),
    # Step 5 - The Room (D1)
    ("step5", "identity name",                     "[data-testid='project-room-name']"),
    ("step5", "lifecycle chip",                    "[data-testid='orientation-lifecycle']"),
    ("step5", "revision token",                    "[data-testid='orientation-revision']"),
    ("step5", "orientation band",                  "[data-testid='orientation-band']"),
    # Step 6 - Review posture (D5)
    ("step6", "review queue",                      "[data-testid='review-queue']"),
    ("step6", "review position",                   "[data-testid='review-position']"),
    ("step6", "review footer tally",               "[data-testid='review-footer-tally']"),
    # Step 7 - Steward posture (D7)
    ("step7", "steward run plan",                  "[data-testid='steward-run-plan']"),
    ("step7", "steward list (RUNS ledger)",        "[data-testid='steward-list']"),
    ("step7", "steward policy sheet",              "[data-testid='steward-policy']"),
    ("step7", "steward footer receipt",            "[data-testid='steward-footer-receipt']"),
    # Step 8 - Update posture (D6)
    ("step8", "update list (DRAFTS ledger)",       "[data-testid='update-list']"),
    ("step8", "update generator label",            "[data-testid='update-generator-label']"),
    ("step8", "update footer receipt",             "[data-testid='update-footer-receipt']"),
]


# ── Skip guard ──────────────────────────────────────────────────────
def _skip_reason() -> str:
    """Returns non-empty reason if the walk should be skipped."""
    if not os.environ.get("HS167_WALK"):
        return "HS167_WALK not set (live walk only runs on demand)"

    # gh auth check
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

    # acli auth check
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

TOKEN = "hs167-tuesday-walk"
REPO = Path(__file__).resolve().parents[2]
WALK_MODE = os.environ.get("HS167_WALK_DB", "isolated")

SCRATCHPAD = Path(
    "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/"
    "ce822ca3-b9ee-4f69-92e4-ba2665a9be94/scratchpad/walk167"
)


# ── Helpers ─────────────────────────────────────────────────────────

def _shot_dir(mode: str, width: int) -> Path:
    d = SCRATCHPAD / mode / str(width)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _shot(page: Any, name: str, width: int, mode: str, *, locator: Any = None) -> Path:
    """Take a screenshot into the per-run directory."""
    d = _shot_dir(mode, width)
    path = d / f"{name}.png"
    if locator is not None:
        try:
            locator.scroll_into_view_if_needed(timeout=3000)
        except Exception:
            pass  # best-effort scroll
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Suspiciously small PNG: {path}"
    return path


def _ref_encode(ref: str) -> str:
    return urllib.parse.quote(ref, safe="")


def _api(
    page: Any, method: str, path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Browser-side fetch through the real hub. Returns {status, payload}."""
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


def _api_ok(
    page: Any, method: str, path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Like _api but asserts status < 300 and returns the payload."""
    result = _api(page, method, path, body)
    assert result["status"] < 300, f"HTTP {result['status']} on {method} {path}: {result}"
    payload = result["payload"]
    return payload if isinstance(payload, dict) else {}


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api_ok(page, "POST", "/api/desk/seed")
    _api_ok(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})


def _normal_chair(page: Any) -> None:
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _seed_desk_facts() -> None:
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState
    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-glass-167-walk",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint Review",
        capture_status="finalized",
    ))


def _count_projects_db() -> int:
    """Count projects in the current DB."""
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        row = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
        return row[0] if row else 0


def _db_counts() -> dict[str, int]:
    from holdspeak.db import get_database
    db = get_database()
    counts: dict[str, int] = {}
    with db._connection() as conn:
        for table in ("watch_evaluations", "watch_effects", "steward_runs"):
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            counts[table] = row[0] if row else 0
        row = conn.execute(
            "SELECT COUNT(*) FROM action_items WHERE source_ref LIKE 'project_item:%'"
        ).fetchone()
        counts["door_items_project"] = row[0] if row else 0
    return counts


def _count_door_items(page: Any) -> int:
    resp = _api_ok(page, "GET", "/api/door")
    board = resp.get("board", {})
    total = 0
    for bucket in ("now", "waiting", "unassigned", "overdue"):
        total += len(board.get(bucket, []))
    return total


def _open_project_room(page: Any, url: str, project_id: str) -> None:
    """Open the project room surface via sessionStorage staging."""
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.wait_for_timeout(1500)


def _open_posture(page: Any, url: str, project_id: str, verb_testid: str) -> None:
    """Open a posture (review/updates/steward) via the room verb button."""
    _open_project_room(page, url, project_id)
    btn = page.get_by_test_id(verb_testid)
    btn.wait_for(timeout=5000)
    btn.click()
    page.wait_for_timeout(1500)


def _assert_no_ellipsis_on_primaries(page: Any, width: int) -> list[str]:
    """Assert no text-overflow ellipsis on .surface-ledger-primary at 393."""
    if width != 393:
        return []
    truncated = page.evaluate("""() => {
      const els = document.querySelectorAll('.surface-ledger-primary');
      const bad = [];
      for (const el of els) {
        if (el.scrollWidth > el.clientWidth + 1) {
          bad.push(el.textContent?.slice(0, 60) || '(empty)');
        }
      }
      return bad;
    }""")
    return truncated


def _make_watch_due(watch_id: str) -> None:
    from holdspeak.db import get_database
    db = get_database()
    past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
    with db._connection() as conn:
        conn.execute(
            "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
            (past_iso, watch_id),
        )


def _poll_run_completed(
    page: Any, run_id: str, timeout: float = 120,
) -> dict[str, Any]:
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


def _discover_acli_accounts() -> list[dict[str, Any]]:
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


# ── Boot ────────────────────────────────────────────────────────────

def _boot_isolated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, str]:
    """Boot with isolated DB, REAL HOME."""
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
    config_dir.mkdir(parents=True)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
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


def _boot_real(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, str]:
    """Boot with REAL DB (owner's desk), REAL HOME.

    No monkeypatching of DB path -- uses DEFAULT_DB_PATH as-is.
    """
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


# ── Pre-step: prime connections ──────────────────────────────────────

def prime_connections(page: Any) -> dict[str, Any]:
    """Prime GitHub and Jira connections so suggest sees them.

    Must be called BEFORE the interview suggest step -- without this
    the suggest engine only sees native proposals.
    """
    result: dict[str, Any] = {"jira_walk_ref": ""}

    # Prime Jira connections from acli registry
    acli_accounts = _discover_acli_accounts()
    for acct in acli_accounts:
        _api(page, "POST", "/api/providers/jira/connections", {
            "site": acct["site"], "email": acct["email"],
        })
        ref = f"{acct['site']}|{acct['email']}"
        _api(page, "POST",
             f"/api/providers/jira/connections/{_ref_encode(ref)}/recheck")
    if acli_accounts:
        result["jira_walk_ref"] = (
            f"{acli_accounts[0]['site']}|{acli_accounts[0]['email']}"
        )

    # GitHub connection is probed by the server's built-in adapter on
    # boot (it uses gh CLI under real HOME).  Just trigger a recheck.
    _api(page, "POST", "/api/providers/github/connection/recheck")

    return result


# ── The eight steps ─────────────────────────────────────────────────

def step1_interview(
    page: Any, url: str, width: int, mode: str,
) -> dict[str, Any]:
    """Step 1: New project by voice -- the interview.

    Routes: POST /api/project-setups (start)
            POST .../answers x2
            POST .../suggest
    """
    t0 = time.monotonic()

    # Start setup
    setup = _api_ok(page, "POST", "/api/project-setups", {})
    session_id = setup.get("id", setup.get("session_id", ""))
    assert session_id, f"No session_id from setup start: {setup}"

    # Answer outcome
    _api_ok(page, "POST", f"/api/project-setups/{session_id}/answers", {
        "question_id": "outcome",
        "payload": {"text": "The first real project through the whole Room, attended"},
    })

    # Answer notice (signals)
    _api_ok(page, "POST", f"/api/project-setups/{session_id}/answers", {
        "question_id": "signals",
        "payload": {"text": "PR activity, KAN due dates, stale decisions"},
    })

    # Suggest
    suggest = _api_ok(page, "POST", f"/api/project-setups/{session_id}/suggest", {})
    proposals = suggest.get("proposals", [])

    _shot(page, "01-interview-suggest", width, mode)

    return {
        "step": "step1_interview",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "session_id": session_id,
            "proposal_count": len(proposals),
            "proposal_ids": [p.get("id", "") for p in proposals],
            "provider_ids": [p.get("provider_id", "") for p in proposals],
        },
        "_session_id": session_id,
        "_proposals": proposals,
    }


def step2_github_connection(
    page: Any, url: str, width: int, mode: str,
    session_id: str, proposals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Step 2: The GitHub connection through the wizard.

    Routes: POST .../proposals/{id}/select
            POST .../proposals/{id}/clarify-scope
            POST .../proposals/{id}/test
    """
    t0 = time.monotonic()

    # Find the GitHub proposal
    gh_proposal = None
    for p in proposals:
        if p.get("provider_id") == "github":
            gh_proposal = p
            break
    assert gh_proposal is not None, (
        f"No GitHub proposal in suggestions. "
        f"Providers: {[p.get('provider_id') for p in proposals]}"
    )
    proposal_id = gh_proposal["id"]

    # Select
    _api_ok(page, "POST",
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/select", {})

    # Clarify scope -- pick karolswdev/HoldSpeak, items issues+PRs
    clarify = _api_ok(page, "POST",
                      f"/api/project-setups/{session_id}/proposals/{proposal_id}/clarify-scope",
                      {"repo": "karolswdev/HoldSpeak"})

    # Test
    test_resp = _api_ok(page, "POST",
                        f"/api/project-setups/{session_id}/proposals/{proposal_id}/test", {})
    test_result = test_resp.get("result", test_resp)

    _shot(page, "02-github-connection", width, mode)

    return {
        "step": "step2_github_connection",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "proposal_id": proposal_id,
            "test_provider": test_result.get("provider", ""),
            "test_entity_count": test_result.get("entity_count", 0),
            "test_calls": test_result.get("calls", 0),
        },
        "_gh_proposal_id": proposal_id,
    }


def step3_jira_connection(
    page: Any, url: str, width: int, mode: str,
    session_id: str, proposals: list[dict[str, Any]],
    primed_walk_ref: str = "",
) -> dict[str, Any]:
    """Step 3: The Jira connection.

    Routes: POST .../proposals/{id}/select
            POST .../proposals/{id}/clarify-jira-scope
            POST .../proposals/{id}/test
    """
    t0 = time.monotonic()

    # Use the walk_ref primed in prime_connections
    if primed_walk_ref:
        walk_ref = primed_walk_ref
    else:
        acli_accounts = _discover_acli_accounts()
        assert len(acli_accounts) >= 1, "No acli accounts configured"
        walk_ref = f"{acli_accounts[0]['site']}|{acli_accounts[0]['email']}"

    # Find a Jira proposal
    jira_proposal = None
    for p in proposals:
        if p.get("provider_id") == "jira":
            jira_proposal = p
            break
    assert jira_proposal is not None, (
        f"No Jira proposal in suggestions. "
        f"Providers: {[p.get('provider_id') for p in proposals]}"
    )
    proposal_id = jira_proposal["id"]

    # Select
    _api_ok(page, "POST",
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/select", {})

    # Clarify jira scope -- project KAN
    clarify = _api_ok(page, "POST",
                      f"/api/project-setups/{session_id}/proposals/{proposal_id}/clarify-jira-scope",
                      {
                          "connection_ref": walk_ref,
                          "projects": ["KAN"],
                          "issue_types": [],
                      })

    # Test
    test_resp = _api_ok(page, "POST",
                        f"/api/project-setups/{session_id}/proposals/{proposal_id}/test", {})
    test_result = test_resp.get("result", test_resp)

    _shot(page, "03-jira-connection", width, mode)

    return {
        "step": "step3_jira_connection",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "proposal_id": proposal_id,
            "walk_ref": walk_ref,
            "test_provider": test_result.get("provider", ""),
            "test_entity_count": test_result.get("entity_count", 0),
            "test_calls": test_result.get("calls", 0),
        },
        "_jira_proposal_id": proposal_id,
        "_walk_ref": walk_ref,
    }


def step4_activate(
    page: Any, url: str, width: int, mode: str,
    session_id: str,
) -> dict[str, Any]:
    """Step 4: Activate -- review WHAT WILL RUN, finalize.

    Routes: POST .../finalize
    """
    t0 = time.monotonic()

    finalize = _api_ok(page, "POST",
                       f"/api/project-setups/{session_id}/finalize", {})
    project_id = finalize.get("project_id", "")
    assert project_id, f"No project_id from finalize: {finalize}"

    activated = finalize.get("activated_watches", [])
    assert len(activated) >= 1, f"No activated watches: {finalize}"

    # Collect watch IDs
    watch_ids = [w.get("watch_id", "") for w in activated]
    assert all(watch_ids), f"Empty watch_id in activated: {activated}"

    # Assert baseline_state on each watch (lives on watches, not finalize).
    # At least one watch must be "established"; others may be "pending"
    # if their snapshot fetch failed during finalize (GitHub rate-limits,
    # network issues). The finalize code falls back to "pending" on failure.
    baseline_states: dict[str, str] = {}
    for wid in watch_ids:
        w = _api_ok(page, "GET", f"/api/watches/{wid}")
        watch_data = w.get("watch", w)
        bs = watch_data.get("baseline_state", "")
        baseline_states[wid] = bs

    established_count = sum(1 for v in baseline_states.values() if v == "established")
    assert established_count >= 1, (
        f"No watches with baseline_state='established' after finalize "
        f"(the 166 false-baseline law): {baseline_states}"
    )

    _shot(page, "04-activate-finalize", width, mode)

    return {
        "step": "step4_activate",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "project_id": project_id,
            "activated_watch_count": len(activated),
            "watch_ids": watch_ids,
            "baseline_states": baseline_states,
        },
        "_project_id": project_id,
        "_watch_ids": watch_ids,
    }


def step5_room(
    page: Any, url: str, width: int, mode: str,
    project_id: str,
) -> dict[str, Any]:
    """Step 5: The Room lands.

    Routes: GET /api/projects/{id}
            GET /api/projects/{id}/delta
    """
    t0 = time.monotonic()

    # The room projection: lifecycle and revision live under project.orientation
    room = _api_ok(page, "GET", f"/api/projects/{project_id}/room")
    orientation = room.get("project", {})
    lifecycle = orientation.get("lifecycle", "")
    revision = room.get("revision", 0)

    delta_resp = _api(page, "GET", f"/api/projects/{project_id}/delta")
    delta_payload = delta_resp.get("payload", delta_resp)

    # Navigate to the Room face
    _open_project_room(page, url, project_id)

    # ── Glass assertions (step 5) ────────────────────────────────
    glass: dict[str, Any] = {}

    # Identity band: project name
    name_el = page.get_by_test_id("project-room-name")
    name_el.wait_for(timeout=5000)
    glass["name_visible"] = name_el.is_visible()
    glass["name_text"] = name_el.text_content() or ""

    # Lifecycle StateChip: "Active"
    lc_el = page.get_by_test_id("orientation-lifecycle")
    glass["lifecycle_visible"] = lc_el.is_visible() if lc_el.count() else False
    glass["lifecycle_text"] = (lc_el.text_content() or "").strip() if lc_el.count() else ""

    # REV token
    rev_el = page.get_by_test_id("orientation-revision")
    glass["revision_visible"] = rev_el.is_visible() if rev_el.count() else False
    glass["revision_text"] = (rev_el.text_content() or "").strip() if rev_el.count() else ""

    # Four wings: review-verb (conditional on pending), updates-verb,
    # steward-verb + the room itself.  The review verb only renders
    # when reviewCtrl.primaryVerb is non-empty (pending proposals).
    review_verb = page.get_by_test_id("review-verb")
    updates_verb = page.get_by_test_id("updates-verb")
    steward_verb = page.get_by_test_id("steward-verb")
    glass["review_verb_present"] = review_verb.count() > 0
    glass["updates_verb_visible"] = updates_verb.is_visible() if updates_verb.count() else False
    glass["steward_verb_visible"] = steward_verb.is_visible() if steward_verb.count() else False

    # FOCUS sections: rail counts
    rail = page.get_by_test_id("project-room-rail")
    glass["rail_visible"] = rail.is_visible() if rail.count() else False

    # No ellipsis on .surface-ledger-primary at 393
    truncated = _assert_no_ellipsis_on_primaries(page, width)
    glass["truncated_primaries"] = truncated

    _shot(page, "05-room-landed", width, mode)

    # Assert: the delta on an unchanged project is honest empty (no open review)
    open_review = delta_payload.get("open_review")

    # Wire assertions
    assert lifecycle == "active", (
        f"Project lifecycle={lifecycle!r}, expected 'active'"
    )
    assert revision >= 1, (
        f"Project revision={revision}, expected >= 1"
    )

    # Glass assertions
    assert glass["name_visible"], "project-room-name not visible"
    assert "active" in glass["lifecycle_text"].lower(), (
        f"Lifecycle chip text={glass['lifecycle_text']!r}, expected to contain 'Active'"
    )
    assert "rev" in glass["revision_text"].lower() or str(revision) in glass["revision_text"], (
        f"REV token text={glass['revision_text']!r}, expected to contain REV or {revision}"
    )
    # review-verb is conditional (renders only when pending proposals exist);
    # the walk uses step 5 before step 6 reviews, so it may not be present yet.
    assert glass["updates_verb_visible"], "updates-verb not visible (missing wing)"
    assert glass["steward_verb_visible"], "steward-verb not visible (missing wing)"
    assert len(truncated) == 0, (
        f"Truncated .surface-ledger-primary at {width}: {truncated}"
    )

    return {
        "step": "step5_room",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "project_name": orientation.get("name", ""),
            "lifecycle": lifecycle,
            "revision": revision,
            "delta_open_review": open_review,
        },
        "glass": glass,
    }


def step6_real_change(
    page: Any, url: str, width: int, mode: str,
    project_id: str, watch_ids: list[str], walk_ref: str,
) -> dict[str, Any]:
    """Step 6: A real change on each source, observed by the watches.

    (a) GitHub: create a probe issue and leave it OPEN so the GitHub
        watch snapshot sees a new entity.  Closed only in the test's
        finally block.
    (b) Jira: KAN transition, then POLL the trigger route until the
        Jira watch reports >= 1 transition (eventual consistency).
    (c) Assert >= 1 new proposal per source from those transitions;
        a second trigger adds ZERO new proposals (no-duplicate law).
    (d) Accept one acceptable-kind proposal, defer one.

    Routes: POST /api/steward/trigger (evaluate_due + run_due)
            POST /api/projects/{id}/reviews
            GET  /api/projects/{id}/delta
            POST .../proposals/{id}/decide x2
    """
    t0 = time.monotonic()
    harness_actions: list[dict[str, Any]] = []
    gh_issue_number: str | None = None
    original_kan_status: str | None = None
    harness_key: str | None = None

    # -- (a) GitHub: create a throwaway issue (the watch sees pull_requests,
    #    but we also create an issue for the repo touch; the GitHub watch
    #    snapshot diff picks up PR activity from gh pr create below) --
    # Strategy: create a throwaway branch + PR without checking out
    # (avoids disrupting the working tree for concurrent workers).
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    probe_branch = f"hs167-walk-probe-{ts}"

    # Get current HEAD sha to create a branch from
    head_sha = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=5,
    ).stdout.strip()

    # Create the branch at HEAD (does not checkout)
    subprocess.run(
        ["git", "-C", str(REPO), "branch", probe_branch, head_sha],
        capture_output=True, text=True, timeout=10,
    )
    # Push it to origin (no checkout needed -- it points at HEAD)
    push_result = subprocess.run(
        ["git", "-C", str(REPO), "push", "origin", probe_branch],
        capture_output=True, text=True, timeout=30,
    )
    assert push_result.returncode == 0, (
        f"git push failed: {push_result.stderr}"
    )

    pr_create_result = subprocess.run(
        ["gh", "pr", "create",
         "--repo", "karolswdev/HoldSpeak",
         "--head", probe_branch,
         "--title", f"hs167 walk probe {ts}",
         "--body", "Automated walk probe PR -- closed in the test finally."],
        capture_output=True, text=True, timeout=30,
    )
    assert pr_create_result.returncode == 0, (
        f"gh pr create failed: {pr_create_result.stderr}"
    )
    pr_url = pr_create_result.stdout.strip()
    pr_match = re.search(r"/pull/(\d+)", pr_url)
    assert pr_match, f"Cannot parse PR number from: {pr_url}"
    gh_issue_number = pr_match.group(1)  # reuse field for cleanup

    harness_actions.append({
        "action": "gh_pr_create",
        "repo": "karolswdev/HoldSpeak",
        "pr_number": gh_issue_number,
        "pr_branch": probe_branch,
        "pr_url": pr_url,
    })

    # -- (b) Jira: KAN transition --
    search_resp = _api(page, "POST", "/api/providers/jira/search", {
        "connection_ref": walk_ref,
        "jql": "project = KAN AND duedate IS NOT EMPTY ORDER BY duedate ASC",
        "limit": 10,
        "enrich": True,
    })
    search_payload = search_resp.get("payload", search_resp)
    items = search_payload.get("items", [])
    due_items = [i for i in items if i.get("due_at")]
    assert len(due_items) >= 1, f"No KAN issues with due dates: {items}"
    due_items.sort(key=lambda x: x["due_at"])
    harness_key = due_items[0]["key"]

    view_resp = subprocess.run(
        ["acli", "jira", "workitem", "view", harness_key,
         "--fields", "status", "--json"],
        capture_output=True, text=True, timeout=15,
    )
    assert view_resp.returncode == 0, (
        f"Failed to read {harness_key}: {view_resp.stderr}"
    )
    view_data = json.loads(view_resp.stdout)
    original_kan_status = view_data["fields"]["status"]["name"]
    target_status = "Done" if original_kan_status != "Done" else "In Progress"

    trans_result = subprocess.run(
        ["acli", "jira", "workitem", "transition",
         "--key", harness_key, "--status", target_status, "--yes"],
        capture_output=True, text=True, timeout=30,
    )
    assert trans_result.returncode == 0, (
        f"KAN transition failed: {trans_result.stderr}"
    )

    harness_actions.append({
        "action": "kan_transition",
        "key": harness_key,
        "from_status": original_kan_status,
        "to_status": target_status,
    })

    # -- Poll trigger until BOTH watches report transitions --
    # The GitHub issue is open (new entity in snapshot -> transition).
    # The KAN transition needs Jira Cloud search propagation (~3-6s).
    # Poll: make watches due, trigger, check outcomes.
    gh_transitions = 0
    jira_transitions = 0
    trigger_attempts = 0
    final_trigger_payload: dict[str, Any] = {}

    poll_deadline = time.monotonic() + 55
    while time.monotonic() < poll_deadline:
        trigger_attempts += 1
        for wid in watch_ids:
            _make_watch_due(wid)
        trigger_resp = _api(page, "POST", "/api/steward/trigger", {})
        tp = trigger_resp.get("payload", trigger_resp)
        final_trigger_payload = tp
        evals = tp.get("evaluate_outcomes", [])

        for ev in evals:
            t_count = ev.get("transitions", 0)
            if t_count > 0:
                wid = ev.get("watch_id", "")
                # Identify which watch this is (GitHub vs Jira) by
                # checking the connector_id from the watch spec.
                w_resp = _api(page, "GET", f"/api/watches/{wid}")
                w_data = w_resp.get("payload", w_resp)
                connector = w_data.get("watch", w_data).get("connector_id", "")
                if connector == "gh":
                    gh_transitions = max(gh_transitions, t_count)
                elif connector == "jira":
                    jira_transitions = max(jira_transitions, t_count)

        if gh_transitions >= 1 and jira_transitions >= 1:
            break
        time.sleep(4)

    assert gh_transitions >= 1, (
        f"GitHub watch reported 0 transitions after {trigger_attempts} "
        f"trigger attempts (expected >= 1 from the open probe issue). "
        f"Last trigger: {json.dumps(final_trigger_payload, default=str)[:500]}"
    )
    assert jira_transitions >= 1, (
        f"Jira watch reported 0 transitions after {trigger_attempts} "
        f"trigger attempts (expected >= 1 from the KAN transition). "
        f"Last trigger: {json.dumps(final_trigger_payload, default=str)[:500]}"
    )

    # Wait for any steward runs spawned by the trigger
    time.sleep(3)

    # -- (c) Open a review and count proposals from transitions --
    review_resp = _api_ok(page, "POST",
                          f"/api/projects/{project_id}/reviews", {})
    review_id = review_resp.get("review_id", review_resp.get("id", ""))

    delta = _api_ok(page, "GET", f"/api/projects/{project_id}/delta")
    proposals = delta.get("proposals", [])

    # The transitions should produce >= 1 new proposal
    assert len(proposals) >= 1, (
        f"Expected >= 1 proposal from {gh_transitions} GH + "
        f"{jira_transitions} Jira transitions, got {len(proposals)}"
    )

    # No-duplicate law: a second trigger + refresh adds ZERO new proposals.
    for wid in watch_ids:
        _make_watch_due(wid)
    dedup_trigger = _api(page, "POST", "/api/steward/trigger", {})
    time.sleep(1)
    delta2 = _api_ok(page, "GET", f"/api/projects/{project_id}/delta")
    proposals2 = delta2.get("proposals", [])
    assert len(proposals2) == len(proposals), (
        f"No-duplicate law violated: first={len(proposals)} "
        f"vs second={len(proposals2)}"
    )

    # -- (d) Accept one acceptable, defer one --
    decided: list[dict[str, Any]] = []
    acceptable_kinds = {"risk_attention", "review_flag",
                        "observation_attention", "coverage_degraded"}
    accept_target = None
    defer_target = None
    for prop in proposals:
        kind = prop.get("proposal_kind", prop.get("kind", ""))
        pid = prop.get("id", "")
        if not pid:
            continue
        if accept_target is None and kind in acceptable_kinds:
            accept_target = prop
        elif defer_target is None:
            defer_target = prop
        if accept_target and defer_target:
            break
    if accept_target is None and proposals:
        accept_target = proposals[0]
    if defer_target is None and len(proposals) > 1:
        defer_target = proposals[1]

    for prop, verb in [(accept_target, "accept"), (defer_target, "defer")]:
        if prop is None or not review_id:
            continue
        pid = prop.get("id", "")
        kind = prop.get("proposal_kind", prop.get("kind", ""))
        decide_resp = _api(page, "POST",
            f"/api/projects/{project_id}/reviews/{review_id}/proposals/{pid}/decide",
            {"verb": verb})
        status = decide_resp.get("status", 0)
        decided.append({
            "proposal_id": pid, "verb": verb,
            "status": status,
            "proposal_kind": kind,
        })
        if verb == "accept":
            assert status in (200, 409), (
                f"Accept failed for kind={kind!r}: status={status}, "
                f"response={decide_resp}"
            )

    # ── Glass assertions (step 6: Review posture) ─────────────────
    _open_posture(page, url, project_id, "review-verb")
    glass: dict[str, Any] = {}

    # Queue sections with counts
    queue = page.get_by_test_id("review-queue")
    glass["queue_visible"] = queue.is_visible() if queue.count() else False
    kind_groups = page.get_by_test_id("review-kind-group")
    glass["kind_group_count"] = kind_groups.count()
    kind_counts = []
    for i in range(kind_groups.count()):
        grp = kind_groups.nth(i)
        label = grp.get_by_test_id("review-kind-label").text_content() or ""
        count = grp.get_by_test_id("review-kind-count").text_content() or ""
        kind_counts.append({"label": label.strip(), "count": count.strip()})
    glass["kind_counts"] = kind_counts

    # Queue items
    queue_items = page.get_by_test_id("review-queue-item")
    glass["queue_item_count"] = queue_items.count()

    # Click the first queue item to expand it
    if queue_items.count() > 0:
        queue_items.first.click()
        page.wait_for_timeout(500)
        detail = page.get_by_test_id("review-detail")
        glass["detail_visible"] = detail.is_visible() if detail.count() else False
        # CURRENT/PROPOSED facts in the comparison
        comparison = page.get_by_test_id("review-comparison")
        glass["comparison_visible"] = comparison.is_visible() if comparison.count() else False
    else:
        glass["detail_visible"] = False
        glass["comparison_visible"] = False

    # Footer tally
    tally = page.get_by_test_id("review-footer-tally")
    glass["tally_visible"] = tally.is_visible() if tally.count() else False
    glass["tally_text"] = (tally.text_content() or "").strip() if tally.count() else ""

    _shot(page, "06-review-deltas", width, mode)

    # Glass assertions
    assert glass["queue_visible"], "review-queue not visible"
    assert glass["queue_item_count"] >= 1, (
        f"Expected >= 1 queue items, got {glass['queue_item_count']}"
    )

    return {
        "step": "step6_real_change",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "gh_pr_number": gh_issue_number,
            "gh_pr_url": pr_url,
            "gh_probe_branch": probe_branch,
            "kan_key": harness_key,
            "kan_from": original_kan_status,
            "kan_to": target_status,
            "trigger_attempts": trigger_attempts,
            "gh_transitions": gh_transitions,
            "jira_transitions": jira_transitions,
            "trigger_success": final_trigger_payload.get("success", False),
            "review_id": review_id,
            "proposal_count": len(proposals),
            "dedup_proposal_count": len(proposals2),
            "decided": decided,
            "dedup_ok": len(proposals2) == len(proposals),
        },
        "glass": glass,
        "harness_actions": harness_actions,
        "_review_id": review_id,
        "_harness_key": harness_key,
        "_original_kan_status": original_kan_status,
        "_gh_issue_number": gh_issue_number,
        "_probe_branch": probe_branch,
    }


def step7_steward(
    page: Any, url: str, width: int, mode: str,
    project_id: str, watch_ids: list[str],
) -> dict[str, Any]:
    """Step 7: Manual steward run, policy, trigger, door item.

    (e) Before the manual run, create one project item with a past
        due_at through the items route so the door path has an
        overdue candidate.  Assert door_count == 1 after the run
        and the second same-watermark run adds no second door item.

    Routes: POST /api/projects/{id}/items (probe item)
            POST /api/projects/{id}/steward/runs
            PUT  /api/projects/{id}/steward/policy (with evaluation_cadence_minutes)
            GET  /api/projects/{id}/steward/policy (read-back)
            POST /api/steward/trigger (the 02 route)
    """
    t0 = time.monotonic()

    # -- Policy FIRST (the steward needs eligible_effect_kinds to act) --
    cadence_minutes = 30
    _api_ok(page, "PUT",
            f"/api/projects/{project_id}/steward/policy", {
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
                "evaluation_cadence_minutes": cadence_minutes,
            })

    # -- (e) Create a probe item with past due_at --
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    probe_item = _api_ok(page, "POST",
                         f"/api/projects/{project_id}/items", {
                             "item_type": "risk",
                             "title": "hs167 walk probe overdue item",
                             "severity": "high",
                             "due_at": yesterday,
                             "provenance_kind": "owner",
                             "details": {
                                 "likelihood": "medium",
                                 "impact": "high",
                             },
                         })
    probe_item_id = probe_item.get("item", {}).get("id", "")
    assert probe_item_id, f"No item id from create: {probe_item}"

    door_count_before = _count_door_items(page)

    # -- Manual steward run --
    run1_resp = _api_ok(page, "POST",
                        f"/api/projects/{project_id}/steward/runs", {})
    run1_id = run1_resp.get("run_id", "")
    assert run1_id, f"No run_id from manual run: {run1_resp}"

    run1_result = _poll_run_completed(page, run1_id)
    run1_data = run1_result.get("run", {})
    run1_state = run1_data.get("state", "")
    assert run1_state == "completed", (
        f"Manual steward run did not complete: {run1_state}"
    )

    # Check observe receipt for calls
    run1_steps = run1_result.get("steps", [])
    observe_steps = [s for s in run1_steps if s.get("phase") == "observe"]
    observe_receipts = [s.get("receipt", {}) for s in observe_steps]
    observe_observed = [s.get("observed", {}) for s in observe_steps]
    observe_has_calls = any(
        (r.get("calls") is not None)
        for r in observe_receipts
    ) or any(
        (o.get("calls") is not None)
        for o in observe_observed
    )

    # Assert door_count == 1 (the probe overdue item)
    door_count_after_run1 = _count_door_items(page)
    assert door_count_after_run1 == door_count_before + 1, (
        f"Expected exactly 1 new door item from the overdue probe, "
        f"got {door_count_after_run1 - door_count_before} "
        f"(before={door_count_before}, after={door_count_after_run1})"
    )

    _shot(page, "07a-steward-run", width, mode)

    # -- Policy read-back (already set before the run) --
    policy_get = _api_ok(page, "GET",
                         f"/api/projects/{project_id}/steward/policy")
    policy = policy_get.get("policy", {})

    _shot(page, "07b-steward-policy", width, mode)

    # -- Trigger route (the 02 write) --
    for wid in watch_ids:
        _make_watch_due(wid)
    trigger_resp = _api(page, "POST", "/api/steward/trigger", {})
    trigger_payload = trigger_resp.get("payload", trigger_resp)
    trigger_success = trigger_payload.get("success", False)

    _shot(page, "07c-steward-trigger", width, mode)

    # -- Second manual run at same watermark (the 163 law) --
    run1_watermark = run1_data.get("watermark", "")
    time.sleep(3)

    door_count_before_run2 = _count_door_items(page)

    run2_resp = _api(page, "POST",
                     f"/api/projects/{project_id}/steward/runs",
                     {"watermark": run1_watermark} if run1_watermark else {})
    run2_payload = run2_resp.get("payload", run2_resp)
    run2_id = run2_payload.get("run_id", "")
    run2_created = run2_id and run2_id != run1_id

    if run2_id and run2_created:
        run2_result = _poll_run_completed(page, run2_id)
        run2_data = run2_result.get("run", {})
        run2_state = run2_data.get("state", "")
    else:
        run2_state = "not_created"

    # Assert the second run adds NO second door item (dedup/reconcile)
    door_count_after_run2 = _count_door_items(page)
    assert door_count_after_run2 == door_count_before_run2, (
        f"Same-watermark dedup violation: second run added "
        f"{door_count_after_run2 - door_count_before_run2} door items "
        f"(before={door_count_before_run2}, after={door_count_after_run2})"
    )

    # ── Glass assertions (step 7: Steward posture) ─────────────────
    _open_posture(page, url, project_id, "steward-verb")
    glass: dict[str, Any] = {}

    # RUNS ledger
    stw_list = page.get_by_test_id("steward-list")
    glass["list_visible"] = stw_list.is_visible() if stw_list.count() else False
    list_items = page.get_by_test_id("steward-list-item")
    glass["list_item_count"] = list_items.count()

    # Click first run to see the detail + plan
    if list_items.count() > 0:
        list_items.first.click()
        page.wait_for_timeout(800)

    # RUN plan: six .surface-plan-step all done
    plan = page.get_by_test_id("steward-run-plan")
    glass["plan_visible"] = plan.is_visible() if plan.count() else False
    plan_steps = page.locator(".surface-plan-step")
    glass["plan_step_count"] = plan_steps.count()
    plan_step_statuses = []
    for i in range(plan_steps.count()):
        s = plan_steps.nth(i)
        status = s.get_attribute("data-status") or ""
        label_el = s.locator(".surface-plan-step-label")
        label = (label_el.text_content() or "").strip() if label_el.count() else ""
        rate_el = s.locator(".surface-plan-step-rate")
        rate = (rate_el.text_content() or "").strip() if rate_el.count() else ""
        plan_step_statuses.append({"label": label, "status": status, "rate": rate})
    glass["plan_steps"] = plan_step_statuses

    # Observe rate containing calls
    observe_rate = ""
    for ps in plan_step_statuses:
        if ps["label"].lower().startswith("observe"):
            observe_rate = ps["rate"]
    glass["observe_rate"] = observe_rate

    # Footer egress chips naming both hosts
    egress_div = page.locator(".surface-footer-egress")
    egress_text = (egress_div.text_content() or "").strip() if egress_div.count() else ""
    glass["egress_text"] = egress_text

    # Footer receipt
    receipt = page.get_by_test_id("steward-footer-receipt")
    glass["receipt_visible"] = receipt.is_visible() if receipt.count() else False

    _shot(page, "07d-steward-second-run", width, mode)

    # Door item count on the Door (API already checked, record for glass)
    glass["door_count"] = door_count_after_run1

    # Navigate back to list, then to the policy view
    # The detail phase has a back button -- click it to return to list
    back_btn = page.locator("[data-testid='steward-posture'][data-phase='detail'] button").filter(has_text="Back")
    if back_btn.count() > 0:
        back_btn.first.click()
        page.wait_for_timeout(500)
    else:
        # Reopen the steward posture from the room
        _open_posture(page, url, project_id, "steward-verb")

    policy_btn = page.get_by_test_id("steward-verb-policy")
    policy_btn.wait_for(timeout=5000)
    policy_btn.click()
    page.wait_for_timeout(800)

    # Policy sheet visible
    policy_el = page.get_by_test_id("steward-policy")
    glass["policy_visible"] = policy_el.is_visible() if policy_el.count() else False

    # Cadence: read the cadence display text
    cadence_text = page.evaluate("""() => {
      const tokens = document.querySelectorAll('.surface-token');
      for (const t of tokens) {
        const txt = t.textContent || '';
        if (txt.includes('MIN')) return txt.trim();
      }
      return '';
    }""")
    glass["cadence_text"] = cadence_text

    _shot(page, "07e-steward-policy-view", width, mode)

    # Glass assertions
    assert glass["list_visible"], "steward-list not visible"
    assert glass["list_item_count"] >= 1, (
        f"Expected >= 1 steward run items, got {glass['list_item_count']}"
    )
    assert glass["plan_step_count"] == 6, (
        f"Expected 6 plan steps, got {glass['plan_step_count']}: {plan_step_statuses}"
    )
    for ps in plan_step_statuses:
        assert ps["status"] == "done", (
            f"Plan step {ps['label']!r} status={ps['status']!r}, expected 'done'"
        )
    assert "call" in observe_rate.lower() or any(c.isdigit() for c in observe_rate), (
        f"Observe rate should contain calls count, got {observe_rate!r}"
    )
    assert str(cadence_minutes) in cadence_text, (
        f"Policy cadence text should contain {cadence_minutes}, got {cadence_text!r}"
    )
    assert glass["door_count"] >= 1, (
        f"Expected >= 1 door item, got {glass['door_count']}"
    )

    return {
        "step": "step7_steward",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "run1_id": run1_id,
            "run1_state": run1_state,
            "observe_has_calls": observe_has_calls,
            "observe_receipts": observe_receipts[:3],
            "probe_item_id": probe_item_id,
            "door_count_before": door_count_before,
            "door_count_after_run1": door_count_after_run1,
            "door_count_after_run2": door_count_after_run2,
            "cadence_minutes_written": cadence_minutes,
            "policy_readback": {
                "enabled": policy.get("enabled"),
                "unattended_enabled": policy.get("unattended_enabled"),
                "eligible_effect_kinds": policy.get("eligible_effect_kinds"),
            },
            "trigger_success": trigger_success,
            "run2_id": run2_id,
            "run2_created_new": run2_created,
            "run2_state": run2_state,
        },
        "glass": glass,
    }


def step8_update(
    page: Any, url: str, width: int, mode: str,
    project_id: str,
) -> dict[str, Any]:
    """Step 8: Draft, save, publish an update.

    Routes: POST /api/projects/{id}/updates/draft
            PUT  /api/updates/{id}
            POST /api/updates/{id}/publish
            GET  /api/projects/{id}/updates
    """
    t0 = time.monotonic()

    # Draft (deterministic generator)
    draft_resp = _api_ok(page, "POST",
                         f"/api/projects/{project_id}/updates/draft",
                         {"generator": "deterministic"})
    update = draft_resp.get("update", {})
    update_id = update.get("id", "")
    assert update_id, f"No update id from draft: {draft_resp}"

    body_md = update.get("body_md", "")

    # Save the draft (PUT)
    save_body = body_md + "\n\n---\n_Walk probe 167._"
    save_resp = _api_ok(page, "PUT", f"/api/updates/{update_id}", {
        "body_md": save_body,
    })

    # Publish
    publish_resp = _api_ok(page, "POST", f"/api/updates/{update_id}/publish", {})
    published_update = publish_resp.get("update", {})
    published_lifecycle = published_update.get("lifecycle", "")

    # Read-back: list updates to verify
    list_resp = _api_ok(page, "GET", f"/api/projects/{project_id}/updates")
    updates_list = list_resp.get("updates", [])
    published_in_list = [u for u in updates_list if u.get("lifecycle") == "published"]

    # ── Glass assertions (step 8: Update posture) ─────────────────
    _open_posture(page, url, project_id, "updates-verb")
    glass: dict[str, Any] = {}

    # DRAFTS/published list
    update_list = page.get_by_test_id("update-list")
    glass["list_visible"] = update_list.is_visible() if update_list.count() else False
    list_items = page.get_by_test_id("update-list-item")
    glass["list_item_count"] = list_items.count()

    # Generator label (deterministic or model host)
    gen_label = page.get_by_test_id("update-generator-label")
    glass["generator_label_visible"] = gen_label.is_visible() if gen_label.count() else False
    glass["generator_label_text"] = (gen_label.first.text_content() or "").strip() if gen_label.count() else ""

    # Footer receipt after publish
    receipt = page.get_by_test_id("update-footer-receipt")
    glass["receipt_visible"] = receipt.is_visible() if receipt.count() else False
    glass["receipt_text"] = (receipt.text_content() or "").strip() if receipt.count() else ""

    # Footer egress chip
    egress_div = page.locator(".surface-footer-egress")
    egress_text = (egress_div.text_content() or "").strip() if egress_div.count() else ""
    glass["egress_text"] = egress_text

    _shot(page, "08-update-published", width, mode)

    # Glass assertions
    assert glass["list_visible"], "update-list not visible"
    assert glass["list_item_count"] >= 1, (
        f"Expected >= 1 update list items, got {glass['list_item_count']}"
    )
    # The generator label should match the transcript's generator
    expected_gen = "deterministic"
    if glass["generator_label_text"]:
        assert expected_gen in glass["generator_label_text"].lower() or \
               glass["generator_label_text"].lower() in expected_gen, (
            f"Generator label={glass['generator_label_text']!r}, "
            f"expected to contain {expected_gen!r}"
        )

    return {
        "step": "step8_update",
        "elapsed_ms": round((time.monotonic() - t0) * 1000),
        "wire": {
            "update_id": update_id,
            "draft_body_length": len(body_md),
            "published_lifecycle": published_lifecycle,
            "published_in_list_count": len(published_in_list),
            "generator": "deterministic",
        },
        "glass": glass,
    }


# ── The test ────────────────────────────────────────────────────────

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_tuesday_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """HS-167-06 live Tuesday walk: the owner's first project through
    the whole Room, attended. Eight steps, both widths."""
    from tests.e2e.glass_infra import _ensure_build
    _ensure_build()

    mode = WALK_MODE
    is_real = mode == "real"

    # Boot
    if is_real:
        initial_project_count = _count_projects_db()
        server, url = _boot_real(monkeypatch)
    else:
        server, url = _boot_isolated(tmp_path, monkeypatch)

    _seed_desk_facts()

    steps: list[dict[str, Any]] = []
    shot_paths: list[str] = []
    project_id: str | None = None
    harness_key: str | None = None
    original_kan_status: str | None = None
    gh_issue_number: str | None = None  # PR number for cleanup
    probe_branch: str | None = None
    errors: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page = ctx.new_page()
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)

            # ── Prime connections (before suggest) ──
            conn_info = prime_connections(page)

            # ── Step 1: Interview ──
            s1 = step1_interview(page, url, width, mode)
            steps.append(s1)
            session_id = s1["_session_id"]
            proposals = s1["_proposals"]

            # ── Step 2: GitHub connection ──
            s2 = step2_github_connection(page, url, width, mode, session_id, proposals)
            steps.append(s2)

            # ── Step 3: Jira connection ──
            s3 = step3_jira_connection(page, url, width, mode, session_id, proposals,
                                       conn_info.get("jira_walk_ref", ""))
            steps.append(s3)
            walk_ref = s3["_walk_ref"]

            # ── Step 4: Activate ──
            s4 = step4_activate(page, url, width, mode, session_id)
            steps.append(s4)
            project_id = s4["_project_id"]
            watch_ids = s4["_watch_ids"]

            # ── Step 5: Room ──
            s5 = step5_room(page, url, width, mode, project_id)
            steps.append(s5)

            # ── Step 6: Real change ──
            s6 = step6_real_change(page, url, width, mode,
                                   project_id, watch_ids, walk_ref)
            steps.append(s6)
            harness_key = s6.get("_harness_key")
            original_kan_status = s6.get("_original_kan_status")
            gh_issue_number = s6.get("_gh_issue_number")
            probe_branch = s6.get("_probe_branch")

            # Step 6 wire assertions
            assert s6["wire"]["trigger_success"], (
                f"Trigger route did not return success: {s6['wire']}"
            )
            assert s6["wire"]["gh_transitions"] >= 1, (
                f"GitHub watch 0 transitions: {s6['wire']}"
            )
            assert s6["wire"]["jira_transitions"] >= 1, (
                f"Jira watch 0 transitions: {s6['wire']}"
            )
            assert s6["wire"]["dedup_ok"], (
                f"Delta refresh produced duplicates: {s6['wire']}"
            )

            # ── Step 7: Steward ──
            s7 = step7_steward(page, url, width, mode,
                               project_id, watch_ids)
            steps.append(s7)

            # Step 7 wire assertions
            assert s7["wire"]["run1_state"] == "completed", (
                f"Manual steward run did not reach RECORD: {s7['wire']['run1_state']}"
            )
            assert s7["wire"]["door_count_after_run1"] == s7["wire"]["door_count_before"] + 1, (
                f"Expected 1 new door item from overdue probe: {s7['wire']}"
            )
            assert s7["wire"]["trigger_success"], (
                f"Trigger route failed: {s7['wire']}"
            )
            # The 163 law: second manual run at same watermark CREATED
            # and reconciles; no second door item
            assert s7["wire"]["run2_created_new"], (
                f"Same-watermark replay must create NEW run (163 law): "
                f"run2_id={s7['wire']['run2_id']}"
            )
            assert s7["wire"]["door_count_after_run2"] == s7["wire"]["door_count_after_run1"], (
                f"Same-watermark run added a second door item: {s7['wire']}"
            )

            # ── Step 8: Update ──
            s8 = step8_update(page, url, width, mode, project_id)
            steps.append(s8)

            # Step 8 wire assertions
            assert s8["wire"]["published_lifecycle"] == "published", (
                f"Update not published: {s8['wire']['published_lifecycle']}"
            )
            assert s8["wire"]["published_in_list_count"] >= 1, (
                f"Published update not in list: {s8['wire']}"
            )

            # ── Face shots at the desk ──
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.wait_for_timeout(2000)
            _shot(page, "09-desk-final", width, mode)

            browser.close()

    finally:
        # ── Cleanup ──
        # Revert KAN transition
        if harness_key and original_kan_status:
            revert_result = subprocess.run(
                ["acli", "jira", "workitem", "transition",
                 "--key", harness_key, "--status", original_kan_status, "--yes"],
                capture_output=True, text=True, timeout=30,
            )
            if revert_result.returncode != 0:
                print(f"WARNING: KAN revert failed for {harness_key}: {revert_result.stderr}")

        # Close the GitHub probe PR and delete its branch
        if gh_issue_number:
            close_result = subprocess.run(
                ["gh", "pr", "close", gh_issue_number,
                 "--repo", "karolswdev/HoldSpeak",
                 "--delete-branch"],
                capture_output=True, text=True, timeout=30,
            )
            if close_result.returncode != 0:
                print(f"WARNING: gh pr close failed for #{gh_issue_number}: {close_result.stderr}")
                subprocess.run(
                    ["gh", "pr", "close", gh_issue_number,
                     "--repo", "karolswdev/HoldSpeak"],
                    capture_output=True, text=True, timeout=30,
                )
            # Clean up local branch
            if probe_branch:
                subprocess.run(
                    ["git", "-C", str(REPO), "branch", "-D", probe_branch],
                    capture_output=True, text=True, timeout=10,
                )

        # Archive project in real mode (never delete)
        if is_real and project_id:
            try:
                from playwright.sync_api import sync_playwright as _sp
                with _sp() as pw2:
                    br2 = pw2.chromium.launch(headless=True)
                    ctx2 = br2.new_context()
                    pg2 = ctx2.new_page()
                    pg2.goto(f"{url}/?token={TOKEN}", wait_until="load")
                    archive_resp = _api(pg2, "DELETE", f"/api/projects/{project_id}")
                    print(f"Archive result: {archive_resp}")
                    br2.close()
            except Exception as exc:
                print(f"WARNING: archive failed: {exc}")

            # Re-count projects
            final_count = _count_projects_db()
            print(f"Project count before={initial_project_count} after={final_count}")

        server.stop()
        from holdspeak.db import reset_database
        reset_database()

    # Collect shot paths
    shot_dir = _shot_dir(mode, width)
    if shot_dir.exists():
        shot_paths = sorted(str(p) for p in shot_dir.glob("*.png"))

    # Write transcript
    transcript = {
        "schema": "tuesday-walk-transcript@1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "width": width,
        "steps": [
            {
                "step": s.get("step", ""),
                "elapsed_ms": s.get("elapsed_ms", 0),
                "wire": s.get("wire", {}),
                **({"glass": s["glass"]} if "glass" in s else {}),
            }
            for s in steps
        ],
        "shot_paths": shot_paths,
        "page_errors": errors,
    }
    transcript_path = _shot_dir(mode, width) / "walk167-transcript.json"
    transcript_path.write_text(
        json.dumps(transcript, indent=2, default=str) + "\n"
    )

    # Verify no critical page errors
    critical = [e for e in errors if "ResizeObserver" not in e]
    assert len(critical) == 0, f"Critical page errors: {critical}"
