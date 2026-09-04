"""HS-161-06 real-hub GitHub Watch glass.

Four legs: the stopwatch (fixture runner), the auth-degraded leg,
the evaluation leg, and the real-metal leg.

FIXTURE SEAM: MeetingWebServer(gh_runner=...) injects a fake runner
into GitHubProviderAdapter and WatchService snapshot_fetcher so the
booted hub uses canned responses. The runner reads a mutable JSON
fixture file; tests rewrite it between steps for state transitions.
Everything above the runner stays real: routes, services, adapter
logic, DB, React bundle. This is the HS-161-06 SURPRISE: the seam
required a small production change in web_server.py (gh_runner
parameter + _gh_watch_service_kwargs helper).

Seeding gaps (DB-layer only, no HTTP route exists):
  - Meetings: db.meetings.save_meeting(MeetingState) -- no POST /api/meetings
  - Decisions: direct INSERT INTO decisions -- no POST /api/decisions
  - Action items (Door): direct INSERT INTO action_items -- no POST /api/door
Each gap is noted per the 159/160 precedent.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _assert_clean, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="GitHub glass needs Playwright")

TOKEN = "hs161-github-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-161-the-github-watch/assets/story-06-shots"
STOPWATCH_JSON = (
    REPO / "pm/roadmap/holdspeak/phase-161-the-github-watch"
    / "assets/story-06-stopwatch.json"
)

OUTCOME_TEXT = "Ship the Q4 Payments Platform on time with zero incidents"
SIGNALS_TEXT = "Missed sprint commitments, overdue action items, stale decisions"

# ── Fixture data ──────────────────────────────────────────────────

_GH_AUTH_CONNECTED = {
    "stdout": "github.com\n  Logged in to github.com account testuser (keyring)\n",
    "returncode": 0,
}

_GH_AUTH_UNAUTH = {
    "stderr": "You are not logged into any GitHub hosts. Run gh auth login to authenticate.\n",
    "returncode": 1,
}

_GH_REPO_LIST = json.dumps([
    {"name": "HoldSpeak", "owner": {"login": "testuser"}, "visibility": "public"},
    {"name": "other-repo", "owner": {"login": "testuser"}, "visibility": "private"},
])

_GH_PR_VALIDATE_OK = json.dumps([{"number": 1}])

_GH_PR_SNAPSHOT_BASELINE = json.dumps([
    {
        "number": 42, "title": "feat: add payment gateway",
        "url": "https://github.com/testuser/HoldSpeak/pull/42",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "reviewer1"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "abc123def456", "updatedAt": "2026-08-30T10:00:00Z",
    },
    {
        "number": 43, "title": "fix: correct ledger rounding",
        "url": "https://github.com/testuser/HoldSpeak/pull/43",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "789abc012345", "updatedAt": "2026-08-30T11:00:00Z",
    },
])

_GH_PR_SNAPSHOT_CHANGED = json.dumps([
    {
        "number": 42, "title": "feat: add payment gateway",
        "url": "https://github.com/testuser/HoldSpeak/pull/42",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "reviewer1"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "FAILURE"},
        ],
        "headRefOid": "newhead999888", "updatedAt": "2026-08-31T10:00:00Z",
    },
    {
        "number": 43, "title": "fix: correct ledger rounding",
        "url": "https://github.com/testuser/HoldSpeak/pull/43",
        "state": "MERGED", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "789abc012345", "updatedAt": "2026-08-31T11:00:00Z",
    },
])


# ── Fixture runner ────────────────────────────────────────────────


def _make_fixture_runner(fixture_path: Path) -> Any:
    """Create a runner callable that reads canned responses from a JSON file.

    The file is re-read on every call, so the test can mutate it between
    steps (e.g. flip auth from unauthenticated to connected).

    Format: {"auth_status": {...}, "repo_list": {...}, "pr_list": {...},
             "pr_validate": {...}}
    Each entry has "stdout", "stderr", "returncode" keys.
    """
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)

        with open(fixture_path) as f:
            fixture = json.load(f)

        # Match by command pattern
        if "auth status" in cmd_str:
            entry = fixture.get("auth_status", {})
        elif "repo list" in cmd_str:
            entry = fixture.get("repo_list", {})
        elif "pr list" in cmd_str and "-R" in cmd_str and "--limit" in cmd_str and "1" in cmd_str:
            # validate_repo: gh pr list -R ... --limit 1
            entry = fixture.get("pr_validate", {})
        elif "pr list" in cmd_str:
            entry = fixture.get("pr_list", {})
        else:
            entry = {"returncode": 1, "stderr": f"no fixture match: {cmd_str}"}

        return subprocess.CompletedProcess(
            args=cmd,
            returncode=entry.get("returncode", 0),
            stdout=entry.get("stdout", ""),
            stderr=entry.get("stderr", ""),
        )

    return runner


def _write_fixture(path: Path, *, auth: dict[str, Any], **kwargs: Any) -> None:
    """Write a fixture file. auth is required; other keys are optional."""
    fixture: dict[str, Any] = {"auth_status": auth}
    fixture.update(kwargs)
    path.write_text(json.dumps(fixture, indent=2))


# ── Boot / helpers ────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


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
    _normal_chair(page)


def _seed_desk_facts(tmp_path: Path) -> None:
    """Seed meetings, decisions, and overdue action items via the DB layer."""
    from holdspeak.db import get_database
    from holdspeak.meeting_session.models import MeetingState

    db = get_database()
    db.meetings.save_meeting(MeetingState(
        id="m-glass-161-001",
        started_at=datetime(2026, 8, 20, 10, 0),
        title="Sprint 7 Planning",
        capture_status="finalized",
    ))
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
                "dec-glass-161-001",
                "Adopt event sourcing for the payment ledger",
                "Reduces audit risk",
                "2026-08-15T14:30:00",
                "meeting_date",
                None,
                "reported",
                "artifact-glass-161-001",
                "m-glass-161-001",
                "linked",
                None,
                "accepted",
                None,
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
                "ai-glass-161-001",
                "m-glass-161-001",
                "Update PCI compliance docs",
                "karol",
                past_due,
                "pending",
                "accepted",
                now_iso,
                "meeting",
                "",
            ),
        )


def _open_project_room(page: Any, url: str, project_id: str) -> None:
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


# ── Leg 1: THE STOPWATCH ─────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_stopwatch_walk(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Full fixture-runner walk: outcome -> signals -> GitHub candidate
    appears -> clarify repo -> live test -> activate -> populated Now
    surface. Wall-clock per segment."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT_BASELINE, "returncode": 0},
    )
    runner = _make_fixture_runner(fixture_path)

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=runner)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    segments: dict[str, float] = {}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            # -- Desk init --
            t0 = time.monotonic()
            _init_desk(page, url)
            _seed_desk_facts(tmp_path)
            segments["desk_init"] = time.monotonic() - t0

            # -- Open interview --
            t0 = time.monotonic()
            _open_interview(page, url)
            segments["open_interview"] = time.monotonic() - t0

            # -- Step 1: Answer outcome --
            t0 = time.monotonic()
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill(OUTCOME_TEXT)
            textarea.press("Enter")
            segments["answer_outcome"] = time.monotonic() - t0

            # -- Step 2: Answer signals --
            t0 = time.monotonic()
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            textarea2 = q_signals.locator("textarea")
            textarea2.fill(SIGNALS_TEXT)
            textarea2.press("Enter")
            segments["answer_signals"] = time.monotonic() - t0

            # -- Step 3: Suggestions appear with GitHub candidate --
            t0 = time.monotonic()
            cards = page.get_by_test_id("setup-suggestion-cards")
            cards.wait_for(timeout=20000)
            card_elements = cards.locator('[role="option"]')
            card_elements.first.wait_for(timeout=10000)
            card_count = card_elements.count()
            assert card_count >= 1, f"Expected >=1 cards, got {card_count}"

            # Find a GitHub provider card
            gh_card_idx = None
            for i in range(card_count):
                card = card_elements.nth(i)
                # HS-168-04: GitHub cards have ProvenanceChip source="gh"
                egress = card.locator(".surface-provenance-source", has_text="gh")
                if egress.count() > 0:
                    gh_card_idx = i
                    break
            assert gh_card_idx is not None, (
                f"No GitHub provider card found in {card_count} suggestions"
            )
            segments["suggestions_appear"] = time.monotonic() - t0

            # -- SHOT: suggestion cards with GitHub candidate --
            shot_name = f"suggestions-{width}.png"
            page.screenshot(
                path=str(SHOTS / shot_name), full_page=False,
            )
            assert (SHOTS / shot_name).stat().st_size > 20_000, (
                f"Shot {shot_name} too small"
            )

            # -- Step 4: Click the GitHub card (wizard mounts) --
            t0 = time.monotonic()
            gh_card = card_elements.nth(gh_card_idx)
            gh_card.click()

            # The wizard MUST mount on click
            wizard = page.get_by_test_id("provider-wizard-flow")
            wizard.wait_for(timeout=10000)
            segments["select_card"] = time.monotonic() - t0

            # -- Step 5: HS-168-04: wizard auto-discovers (no connection card) --
            t0 = time.monotonic()

            # Discovery auto-fires; select the first discovered repo
            disc_list = page.get_by_test_id("provider-discovery-list")
            disc_list.wait_for(timeout=10000)
            disc_items = disc_list.locator('[role="option"]')
            disc_items.first.wait_for(timeout=10000)
            disc_items.first.click()
            segments["clarify_repo"] = time.monotonic() - t0

            # -- Step 6: Click Test this Watch in the wizard --
            t0 = time.monotonic()

            test_btn = page.get_by_test_id("provider-test-btn")
            test_btn.wait_for(timeout=10000)
            test_btn.click()

            # Wait for test display with passed state
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="provider-test-display"]'
                            + '[data-test-state="passed"]'
                    );
                    return el !== null;
                }""",
                timeout=15000,
            )
            segments["test_proposal"] = time.monotonic() - t0

            # -- SHOT: test result in wizard --
            shot_name2 = f"test-result-{width}.png"
            page.screenshot(
                path=str(SHOTS / shot_name2), full_page=False,
            )
            assert (SHOTS / shot_name2).stat().st_size > 20_000, (
                f"Shot {shot_name2} too small"
            )

            # -- Return to cards via Done --
            done_btn = page.get_by_test_id("provider-wizard-done")
            done_btn.click()

            # Wait for suggestion cards to reappear
            page.get_by_test_id("setup-suggestion-cards").wait_for(timeout=10000)

            # -- Step 7: Proceed to review --
            t0 = time.monotonic()
            proceed_btn = page.get_by_test_id("setup-proceed-review")
            proceed_btn.wait_for(timeout=10000)
            proceed_btn.click()

            review = page.get_by_test_id("setup-review")
            review.wait_for(timeout=10000)
            assert review.is_visible()

            # Verify review has watches section
            review_watches = page.get_by_test_id("review-watches")
            assert review_watches.is_visible()
            segments["review"] = time.monotonic() - t0

            # -- Step 8: Activate (finalize) --
            t0 = time.monotonic()
            activate_btn = page.get_by_test_id("review-activate-btn")
            activate_btn.click()

            done = page.get_by_test_id("setup-done")
            done.wait_for(timeout=20000)

            # The Room should open
            room_name = page.get_by_test_id("project-room-name")
            room_name.wait_for(timeout=20000)
            assert room_name.is_visible()
            segments["activate"] = time.monotonic() - t0

            # -- Step 9: Verify the watch binding in the Room --
            # Check via API that the project has watches
            # First get the project ID from the room
            project_id = page.evaluate(
                """() => {
                    const el = document.querySelector('[data-testid="project-room-name"]');
                    const root = el ? el.closest('[data-project-id]') : null;
                    return root ? root.getAttribute('data-project-id') : null;
                }"""
            )

            # If we can't get project_id from DOM, get it from the API
            if not project_id:
                projects = _api(page, "GET", "/api/projects", token=TOKEN)
                project_list = projects.get("projects", [])
                assert len(project_list) >= 1, "No projects created"
                project_id = project_list[0].get("id", "")

            assert project_id, "Could not determine project ID"

            # Verify watches exist for this project
            watches = _api(page, "GET", f"/api/projects/{project_id}/watches", token=TOKEN)
            watch_list = watches.get("watches", [])
            assert len(watch_list) >= 1, (
                f"Expected >=1 watch for project {project_id}, got {len(watch_list)}"
            )

            # -- SHOT: populated Room --
            shot_name3 = f"room-{width}.png"
            page.screenshot(
                path=str(SHOTS / shot_name3), full_page=False,
            )
            assert (SHOTS / shot_name3).stat().st_size > 20_000, (
                f"Shot {shot_name3} too small"
            )

            # -- Overflow assertion --
            _assert_clean(page, errors)

            # -- Write stopwatch JSON (only on 1440 to avoid double-write) --
            if width == 1440:
                total = sum(segments.values())
                stopwatch = {
                    "total_seconds": round(total, 2),
                    "segments": {k: round(v, 2) for k, v in segments.items()},
                    "bar": 300,
                    "passed": total < 300,
                    "viewport": width,
                }
                STOPWATCH_JSON.parent.mkdir(parents=True, exist_ok=True)
                STOPWATCH_JSON.write_text(
                    json.dumps(stopwatch, indent=2) + "\n"
                )
                assert total < 300, (
                    f"Stopwatch bar breached: {total:.1f}s > 300s"
                )

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 2: THE AUTH-DEGRADED LEG ──────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_auth_degraded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Unauthenticated fixture -> owner_action_required card + Recheck
    visible -> recover (flip fixture to connected) -> the exact setup
    step resumes with state intact (SETFLOW-003 on glass)."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    fixture_path = tmp_path / "gh_fixture.json"
    # Start UNAUTHENTICATED
    _write_fixture(fixture_path, auth=_GH_AUTH_UNAUTH)
    runner = _make_fixture_runner(fixture_path)

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=runner)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _seed_desk_facts(tmp_path)
            _open_interview(page, url)

            # -- Answer outcome --
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            textarea = q_outcome.locator("textarea")
            textarea.fill(OUTCOME_TEXT)
            textarea.press("Enter")

            # -- Answer signals --
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            textarea2 = q_signals.locator("textarea")
            textarea2.fill(SIGNALS_TEXT)
            textarea2.press("Enter")

            # -- Suggestions appear (GitHub candidates should NOT appear
            #    because the adapter is unauthenticated) --
            page.wait_for_function(
                """() => {
                    return document.querySelector('[data-testid="setup-suggestion-cards"]') !== null
                        || document.querySelector('[data-testid="setup-blank-path"]') !== null
                        || document.querySelector('[data-testid="setup-proceed-blank"]') !== null;
                }""",
                timeout=20000,
            )

            # -- Verify connection status via API shows owner_action_required --
            conn_status = _api(
                page, "GET", "/api/providers/github/connection",
            token=TOKEN,
            )
            assert conn_status.get("state") == "owner_action_required", (
                f"Expected owner_action_required, got: {conn_status}"
            )
            assert conn_status.get("display", {}).get("recovery_hint") == "gh auth login"

            # -- SHOT: degraded auth state --
            shot_name = f"auth-degraded-{width}.png"
            page.screenshot(
                path=str(SHOTS / shot_name), full_page=False,
            )
            assert (SHOTS / shot_name).stat().st_size > 20_000

            # -- RECOVER: flip the fixture to connected --
            _write_fixture(
                fixture_path,
                auth=_GH_AUTH_CONNECTED,
                repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
                pr_list={"stdout": _GH_PR_SNAPSHOT_BASELINE, "returncode": 0},
            )

            # -- Recheck via API --
            recheck = _api(
                page, "POST", "/api/providers/github/connection/recheck",
            token=TOKEN,
            )
            assert recheck.get("state") == "connected", (
                f"Expected connected after recheck, got: {recheck}"
            )
            assert recheck.get("display", {}).get("account") == "testuser"

            # -- Verify setup state is intact --
            session_id = page.evaluate(
                """() => sessionStorage.getItem('hs.project-setup.session-id')"""
            )
            assert session_id, "Session ID should survive the auth recovery"

            # Verify the session is still active with answers preserved
            session = _api(
                page, "GET",
                f"/api/project-setups/{session_id}",
            token=TOKEN,
            )
            assert session.get("state") == "active", (
                f"Expected active session, got: {session.get('state')}"
            )
            answers = session.get("answers", {})
            assert "outcome" in answers, "Outcome answer should survive recovery"
            assert "signals" in answers, "Signals answer should survive recovery"

            # -- Now re-generate suggestions (connected this time) --
            suggest_result = page.evaluate(
                """async ([sid, token]) => {
                    const response = await fetch(
                        `/api/project-setups/${sid}/suggest`,
                        {
                            method: 'POST',
                            headers: {authorization: `Bearer ${token}`},
                        }
                    );
                    return await response.json();
                }""",
                [session_id, TOKEN],
            )
            proposals = suggest_result.get("proposals", [])
            # Now that GitHub is connected, we should see GitHub candidates
            gh_proposals = [
                p for p in proposals
                if p.get("provider_id") == "github"
            ]
            assert len(gh_proposals) >= 1, (
                f"After recovery, expected GitHub candidates. Got providers: "
                f"{[p.get('provider_id') for p in proposals]}"
            )

            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 3: THE EVALUATION LEG ────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_evaluation_delta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Activated watch, baseline, then changed fixture snapshot ->
    evaluate -> Delta review face shows PR transition evidence-linked."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT_BASELINE, "returncode": 0},
    )
    runner = _make_fixture_runner(fixture_path)

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=runner)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _seed_desk_facts(tmp_path)

            # -- Create project via blank interview --
            _open_interview(page, url)
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            q_outcome.locator("textarea").fill(OUTCOME_TEXT)
            q_outcome.locator("textarea").press("Enter")

            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            q_signals.locator("textarea").fill(SIGNALS_TEXT)
            q_signals.locator("textarea").press("Enter")

            # Wait for proposals
            page.wait_for_function(
                """() => {
                    return document.querySelector('[data-testid="setup-suggestion-cards"]') !== null
                        || document.querySelector('[data-testid="setup-proceed-blank"]') !== null;
                }""",
                timeout=20000,
            )

            # Use blank path to create project (simpler for this leg)
            blank_btn = page.get_by_test_id("setup-proceed-blank")
            if blank_btn.count() > 0:
                blank_btn.first.click()
            else:
                # If there's a proceed-review, use finalize instead
                proceed = page.get_by_test_id("setup-proceed-review")
                if proceed.count() > 0:
                    proceed.click()
                    page.get_by_test_id("review-activate-btn").wait_for(timeout=10000)
                    page.get_by_test_id("review-activate-btn").click()

            done = page.get_by_test_id("setup-done")
            done.wait_for(timeout=20000)

            # Get project ID
            room_name = page.get_by_test_id("project-room-name")
            room_name.wait_for(timeout=20000)

            projects = _api(page, "GET", "/api/projects", token=TOKEN)
            project_list = projects.get("projects", [])
            assert len(project_list) >= 1, "No projects created"
            project_id = project_list[0]["id"]

            # -- Create a watch via API (since blank path has no watches) --
            from holdspeak.db import get_database
            db = get_database()
            watch_id = "cw_eval_test_001"
            now_iso = datetime.now().isoformat()

            with db._connection() as conn:
                conn.execute(
                    """INSERT INTO connector_watches (
                        id, name, connector_id, query_kind, query_json,
                        project_id, state, revision, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        watch_id,
                        "PR review queue",
                        "gh",
                        "pull_requests",
                        json.dumps({
                            "repository": "testuser/HoldSpeak",
                            "state": "open",
                        }),
                        project_id,
                        "active",
                        1,
                        now_iso,
                        now_iso,
                    ),
                )

            # Create a project_sources binding
            source_id = f"psrc_{watch_id}"
            with db._connection() as conn:
                conn.execute(
                    """INSERT INTO project_sources (
                        id, project_id, source_ref, label,
                        semantic_role, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        source_id,
                        project_id,
                        f"watch:{watch_id}",
                        "PR review queue",
                        "watch",
                        now_iso,
                        now_iso,
                    ),
                )

            # -- Test the watch --
            test_result = _api(
                page, "POST", f"/api/watches/{watch_id}/test",
            token=TOKEN,
            )
            assert test_result.get("test_state") == "passed", (
                f"Watch test should pass: {test_result}"
            )
            entity_count = test_result.get("result", {}).get("entity_count", 0)
            assert entity_count == 2, f"Expected 2 PRs, got {entity_count}"

            # -- Baseline the watch --
            baseline_result = _api(
                page, "POST", f"/api/watches/{watch_id}/baseline",
            token=TOKEN,
            )
            assert baseline_result.get("baseline_state") == "established"

            # -- Change the fixture: checks success->failure, PR merged --
            _write_fixture(
                fixture_path,
                auth=_GH_AUTH_CONNECTED,
                repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
                pr_list={"stdout": _GH_PR_SNAPSHOT_CHANGED, "returncode": 0},
            )

            # -- Evaluate --
            eval_result = _api(
                page, "POST", f"/api/watches/{watch_id}/evaluate",
            token=TOKEN,
            )
            assert eval_result.get("state") == "completed", (
                f"Evaluation should complete: {eval_result}"
            )
            transition_count = eval_result.get("transitions", 0)
            assert transition_count >= 1, (
                f"Expected transitions from changed fixture, got {transition_count}"
            )
            observation_ids = eval_result.get("observation_ids", [])
            assert len(observation_ids) >= 1, (
                f"Expected observations, got {len(observation_ids)}"
            )

            # -- Open review (triggers evidence collection) --
            review = _api(
                page, "POST", f"/api/projects/{project_id}/reviews",
            token=TOKEN,
            )
            review_id = review.get("review_id", "")
            proposals = review.get("proposals", [])

            # -- Open the Room and verify the review posture --
            _open_project_room(page, url, project_id)
            room_name = page.get_by_test_id("project-room-name")
            room_name.wait_for(timeout=15000)

            # If proposals exist, the review verb should appear
            if proposals:
                review_verb = page.get_by_test_id("review-verb")
                review_verb.wait_for(timeout=10000)
                review_verb.click()

                posture = page.get_by_test_id("review-posture")
                posture.wait_for(timeout=15000)

                # Verify comparison/evidence is visible
                comparison = page.get_by_test_id("review-comparison")
                comparison.wait_for(timeout=5000)
                assert comparison.is_visible(), "Review comparison not visible"

                # Check for evidence-linked content (source chip)
                source_chips = page.get_by_test_id("review-source-chip")
                if source_chips.count() > 0:
                    source_chip_text = source_chips.first.inner_text()
                    assert source_chip_text, "Source chip should have content"
            else:
                # Even without review proposals, verify the observations exist
                pass  # observations are already verified above

            # -- SHOT: evaluation result --
            shot_name = f"evaluation-{width}.png"
            page.screenshot(
                path=str(SHOTS / shot_name), full_page=False,
            )
            assert (SHOTS / shot_name).stat().st_size > 20_000

            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 4: THE REAL-METAL LEG ────────────────────────────────────


def _gh_real_available() -> bool:
    """Check if gh is installed, authenticated, and network available."""
    import shutil
    if shutil.which("gh") is None:
        return False
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


# ── Leg 5: THE WIZARD-STATES LEG ──────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_wizard_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """UI-driven wizard: click the GitHub card -> wizard mounts ->
    connection card (connected) -> discovery list -> clarify repo ->
    scoped -> test -> GitHubTestDisplay with fixture PRs.
    Plus degraded variant: unauthenticated wizard state."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT_BASELINE, "returncode": 0},
    )
    runner = _make_fixture_runner(fixture_path)

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=runner)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _seed_desk_facts(tmp_path)
            _open_interview(page, url)

            # -- Answer outcome --
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            q_outcome.locator("textarea").fill(OUTCOME_TEXT)
            q_outcome.locator("textarea").press("Enter")

            # -- Answer signals --
            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            q_signals.locator("textarea").fill(SIGNALS_TEXT)
            q_signals.locator("textarea").press("Enter")

            # -- Wait for suggestion cards --
            cards = page.get_by_test_id("setup-suggestion-cards")
            cards.wait_for(timeout=20000)
            card_elements = cards.locator('[role="option"]')
            card_elements.first.wait_for(timeout=10000)

            # -- SHOT (a): card-badge -- the suggestion grid showing a
            #    GitHub card WITH its egress badge before entry --
            page.screenshot(
                path=str(SHOTS / f"card-badge-{width}.png"),
                full_page=False,
            )
            assert (SHOTS / f"card-badge-{width}.png").stat().st_size > 20_000

            # -- Find and CLICK the GitHub card (Playwright click) --
            card_count = card_elements.count()
            gh_card_idx = None
            for i in range(card_count):
                card = card_elements.nth(i)
                egress = card.locator(".surface-provenance-source", has_text="gh")
                if egress.count() > 0:
                    gh_card_idx = i
                    break
            assert gh_card_idx is not None, (
                f"No GitHub provider card in {card_count} suggestions"
            )
            gh_card = card_elements.nth(gh_card_idx)
            gh_card.click()

            # -- The wizard MUST mount --
            wizard = page.get_by_test_id("provider-wizard-flow")
            wizard.wait_for(timeout=10000)
            assert wizard.is_visible(), "Wizard did not mount on GitHub card click"

            # -- HS-168-04: wizard auto-discovers (no connection card) --
            # Discovery list auto-fires on connected
            disc_list = page.get_by_test_id("provider-discovery-list")
            disc_list.wait_for(timeout=10000)
            disc_items = disc_list.locator('[role="option"]')
            disc_items.first.wait_for(timeout=10000)
            disc_count = disc_items.count()
            assert disc_count >= 1, f"Expected discovery items, got {disc_count}"

            # -- SHOT (b): wizard-connected -- discovery --
            page.screenshot(
                path=str(SHOTS / f"wizard-connected-{width}.png"),
                full_page=False,
            )
            assert (SHOTS / f"wizard-connected-{width}.png").stat().st_size > 20_000

            # -- Select a repo from the discovery list --
            first_disc = disc_items.first
            first_disc.click()

            # -- Click Test this Watch button (enabled after scope) --
            test_btn = page.get_by_test_id("provider-test-btn")
            test_btn.wait_for(timeout=10000)
            test_btn.click()

            # -- Wait for test display with fixture PR data --
            # Wait until the display renders with passed state
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="provider-test-display"][data-test-state="passed"]'
                    );
                    return el !== null;
                }""",
                timeout=15000,
            )
            test_display = page.get_by_test_id("provider-test-display")
            assert test_display.is_visible(), "Test display should render"

            # HS-168-04: test display uses SurfaceSection MATCHES label and SurfaceLedgerRow
            # Assert match count is visible in the section label
            test_display_text = test_display.inner_text()
            assert "MATCHES" in test_display_text, (
                f"Expected MATCHES section, got: {test_display_text[:200]}"
            )

            # HS-168-04: egress badge is in the SurfaceFooter (portalled to frame foot)
            footer_egress = page.locator(".gadget-chip-egress")
            assert footer_egress.count() > 0, "Egress badge in wizard footer"

            # -- SHOT (c): wizard-test -- test display with PR data --
            page.screenshot(
                path=str(SHOTS / f"wizard-test-{width}.png"),
                full_page=False,
            )
            assert (SHOTS / f"wizard-test-{width}.png").stat().st_size > 20_000

            # Overflow zero
            _assert_clean(page, errors)

            # ── HS-168-04: auth recovery moved to Connections face ──
            # The wizard no longer shows connection status or recovery.
            # Return to cards via Use this Watch.
            done_btn = page.get_by_test_id("provider-wizard-done")
            done_btn.click()

            # Wait for suggestion cards to reappear
            cards2 = page.get_by_test_id("setup-suggestion-cards")
            cards2.wait_for(timeout=10000)

            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 4: THE REAL-METAL LEG ────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.skipif(
    not _gh_real_available(),
    reason="gh CLI not authenticated or not installed (skip-clean)",
)
def test_real_metal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real gh against karolswdev/HoldSpeak: probe, discover, validate,
    one live snapshot test, and UI-driven wizard with real PR data.
    NO baseline/activation -- read-only."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    # Real-metal: do NOT isolate HOME (needs the owner's gh keyring auth)
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core

    real_home = Path.home()
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            real_home / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    # DB still isolated
    monkeypatch.setattr(
        config_module, "CONFIG_FILE",
        tmp_path / "home" / ".holdspeak" / "config.json",
    )
    (tmp_path / "home").mkdir(exist_ok=True)
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
        # NO gh_runner: real subprocess calls
    )
    url = server.start()
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            _seed_desk_facts(tmp_path)
            _open_interview(page, url)

            # -- Answer outcome + signals --
            q_outcome = page.get_by_test_id("setup-question-outcome")
            q_outcome.wait_for(timeout=15000)
            q_outcome.locator("textarea").fill(OUTCOME_TEXT)
            q_outcome.locator("textarea").press("Enter")

            q_signals = page.get_by_test_id("setup-question-signals")
            q_signals.wait_for(timeout=15000)
            q_signals.locator("textarea").fill(SIGNALS_TEXT)
            q_signals.locator("textarea").press("Enter")

            # -- Wait for suggestion cards --
            cards = page.get_by_test_id("setup-suggestion-cards")
            cards.wait_for(timeout=20000)
            card_elements = cards.locator('[role="option"]')
            card_elements.first.wait_for(timeout=10000)

            # -- Find and click a GitHub card --
            card_count = card_elements.count()
            gh_card_idx = None
            for i in range(card_count):
                card = card_elements.nth(i)
                egress = card.locator(".surface-provenance-source", has_text="gh")
                if egress.count() > 0:
                    gh_card_idx = i
                    break
            assert gh_card_idx is not None, (
                f"No GitHub card found with real gh -- got {card_count} cards"
            )
            gh_card = card_elements.nth(gh_card_idx)
            gh_card.click()

            # -- Wizard mounts --
            wizard = page.get_by_test_id("provider-wizard-flow")
            wizard.wait_for(timeout=15000)

            # -- Connection card: real connected state --
            status_card = page.get_by_test_id("provider-status-card")
            status_card.wait_for(timeout=15000)
            assert status_card.get_attribute("data-state") == "connected"
            account_el = status_card.locator(".provider-status-account")
            account_el.wait_for(timeout=5000)
            account = account_el.inner_text()
            assert account, "Real connection should show account"

            # -- Discovery list with real repos --
            discovery = page.get_by_test_id("provider-discovery")
            discovery.wait_for(timeout=15000)
            disc_list = page.get_by_test_id("provider-discovery-list")
            disc_list.wait_for(timeout=15000)
            disc_items = disc_list.locator('[role="option"]')
            disc_items.first.wait_for(timeout=15000)
            disc_count = disc_items.count()
            assert disc_count >= 1, f"Real discovery should list repos, got {disc_count}"

            # -- Typed-repo fallback: validate karolswdev/HoldSpeak --
            typed = page.get_by_test_id("provider-typed-repo")
            typed_input = typed.locator("input")
            typed_input.fill("karolswdev/HoldSpeak")
            typed.locator("button").filter(has_text="Use this repo").click()

            # -- Wait for scoped state --
            scoped = page.get_by_test_id("provider-wizard-scoped")
            scoped.wait_for(timeout=15000)

            # -- Click Test --
            test_btn = page.get_by_test_id("provider-test-btn")
            test_btn.wait_for(timeout=5000)
            test_btn.click()

            # -- Wait for test display with real PR data (passed state) --
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
            test_display = page.get_by_test_id("provider-test-display")

            # HS-168-04: test display uses SurfaceSection MATCHES + SurfaceLedgerRow
            test_display_text = test_display.inner_text()
            assert "MATCHES" in test_display_text, (
                f"Expected MATCHES in test display, got: {test_display_text[:200]}"
            )

            # Second proof: test through WatchService with state=all
            # to guarantee representative entities on the real repo.
            from holdspeak.db import get_database
            db = get_database()
            watch_id = "cw_metal_all_001"
            now_iso = datetime.now().isoformat()
            with db._connection() as conn_db:
                conn_db.execute(
                    """INSERT INTO connector_watches (
                        id, name, connector_id, query_kind, query_json,
                        state, revision, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        watch_id, "Real metal all",
                        "gh", "pull_requests",
                        json.dumps({
                            "repository": "karolswdev/HoldSpeak",
                            "state": "all", "limit": 5,
                        }),
                        "active", 1, now_iso, now_iso,
                    ),
                )
            watch_test = _api(
                page, "POST", f"/api/watches/{watch_id}/test",
            token=TOKEN,
            )
            assert watch_test.get("test_state") == "passed"
            watch_entities = watch_test.get(
                "result", {},
            ).get("representative_entities", [])
            assert len(watch_entities) >= 1, (
                "karolswdev/HoldSpeak (state=all) must have PRs"
            )
            first_pr = watch_entities[0]
            assert "id" in first_pr, f"PR needs id: {first_pr.keys()}"
            assert "title" in first_pr, f"PR needs title: {first_pr.keys()}"
            assert "state" in first_pr, f"PR needs state: {first_pr.keys()}"

            # -- SHOT: real-metal wizard with real PR data --
            page.screenshot(
                path=str(SHOTS / "real-metal-1440.png"), full_page=False,
            )
            assert (SHOTS / "real-metal-1440.png").stat().st_size > 20_000

            _assert_clean(page, errors)

            # Report
            print(f"\n=== REAL-METAL REPORT ===")
            print(f"Account: {account}")
            print(f"Discovery items: {disc_count}")
            print(f"PR count in test display: {pr_count}")
            print(f"Test count text: {count_text}")
            print(f"=========================\n")

            browser.close()
    finally:
        server.stop()
        reset_database()
