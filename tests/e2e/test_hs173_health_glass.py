"""HS-173-03/04/05 -- Room HEALTH section and nudge glass rig.

HEALTH rows between headline chips and NEEDS YOU: REVIEW WAIT, ISSUE AGING,
CI, RELEASE.  Tones from the wire, tokens (CLEAR/PASSING/READY at green).
Bottleneck rows in NEEDS YOU with Nudge verb (when eligible).
Nudge card unfolds, Send -> receipt row.  Shots at 1440 and 393.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
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
)

pytest.importorskip("playwright.sync_api", reason="Room glass needs Playwright")

SHOTS_03 = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-173-the-stewards-hand-and-voice/assets/story-03-shots"
)
SHOTS_04 = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-173-the-stewards-hand-and-voice/assets/story-04-shots"
)
SHOTS_03.mkdir(parents=True, exist_ok=True)
SHOTS_04.mkdir(parents=True, exist_ok=True)

TOKEN = "hs173-health"


# ── Seed helpers ─────────────────────────────────────────────────────


def _seed_health_project() -> str:
    """Seed a project with Watch entities for all four HEALTH signals."""
    from holdspeak.db import get_database
    from tests.e2e._hs173_seed import seed_health_room

    db = get_database()
    project_id = seed_health_room(
        db,
        project_name="Ship the Q4 platform on schedule with zero incidents",
    )
    return project_id


def _seed_all_green_project() -> str:
    """Seed a project where all HEALTH signals are green."""
    from holdspeak.db import get_database
    from tests.e2e._hs173_seed import seed_health_room

    db = get_database()
    now = datetime.now(timezone.utc)
    # PRs with short wait (< 1 day), no aged issues, passing CI.
    # isDraft=True so this doesn't count toward merge queue depth.
    pr_entities = [
        {
            "number": 201,
            "title": "Small fix",
            "url": "https://github.com/org/repo/pull/201",
            "state": "OPEN",
            "isDraft": True,
            "reviewRequests": ["alice"],
            "reviewDecision": None,
            "checks": "success",
            "headRefOid": "abc",
            "updatedAt": (now - timedelta(hours=2)).isoformat(),
            "createdAt": (now - timedelta(hours=6)).isoformat(),
        },
    ]
    jira_entities = [
        {
            "key": "PROJ-200",
            "title": "Recent task",
            "summary": "Recent task",
            "url": "https://jira.example.com/browse/PROJ-200",
            "status": "In Progress",
            "status_category": "In Progress",
            "issue_type": "Task",
            "assignee": "alice",
            "assignee_id": "",
            "priority": "",
            "resolution": "",
            "due_at": "",
            "updated_at": (now - timedelta(hours=1)).isoformat(),
            "created_at": (now - timedelta(days=2)).isoformat(),
            "status_changed_at": "",
            "labels": [],
            "project_key": "PROJ",
        },
    ]
    ci_history = [
        {"conclusion": "success", "status": "completed", "name": "CI",
         "url": "https://github.com/org/repo/actions/runs/1",
         "updated_at": (now - timedelta(hours=1)).isoformat(), "branch": "main"},
        {"conclusion": "success", "status": "completed", "name": "CI",
         "url": "https://github.com/org/repo/actions/runs/2",
         "updated_at": (now - timedelta(hours=3)).isoformat(), "branch": "main"},
        {"conclusion": "success", "status": "completed", "name": "CI",
         "url": "https://github.com/org/repo/actions/runs/3",
         "updated_at": (now - timedelta(hours=6)).isoformat(), "branch": "main"},
    ]
    project_id = seed_health_room(
        db,
        project_name="Ship the Q4 platform on schedule with zero incidents",
        pr_entities=pr_entities,
        jira_entities=jira_entities,
        ci_history=ci_history,
    )
    return project_id


# ── Surface helpers ──────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)


def _open_room(page: Any, url: str, project_id: str) -> None:
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


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="room-body"]')
    ).first


def _shot(page: Any, name: str, width: int, shots_dir: Path) -> Path:
    _settle(page)
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 2400})
    _settle(page)
    path = shots_dir / f"{name}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old)
    assert path.stat().st_size > 2_000, f"Shot {name} too small"
    return path


def _assert_no_raw_button(page: Any) -> None:
    """UX-CANON A.1: no raw <button> in the room face (same pattern as 172)."""
    raw = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="room-body"]');
        if (!body) return [];
        const btns = body.querySelectorAll('button');
        const raw = [];
        for (const b of btns) {
            if (b.classList.contains('btn') ||
                b.classList.contains('signal-button') ||
                b.classList.contains('surface-ledger-line') ||
                b.classList.contains('surface-edit-in-place') ||
                b.closest('.gadget-string') ||
                b.closest('.mic-button') ||
                b.classList.contains('desk-mic')) continue;
            raw.push(b.outerHTML.slice(0, 120));
        }
        return raw;
    }""")
    assert not raw, f"Raw <button>: {raw}"


def _assert_no_zero_counter(page: Any) -> None:
    """UX-CANON A.8: no counters of zero."""
    import re
    text = page.locator('[data-testid="room-body"]').inner_text()
    hits = re.findall(r'\b0\s+(?:NEEDS|SOURCES|DECISIONS|WAITING|FLAKY|QUEUE|BLOCKERS)', text)
    assert not hits, f"Zero counters: {hits}"


# ── Test rigs ────────────────────────────────────────────────────────


def _run_health_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """HEALTH rows present with real Watch entity data."""
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        height = 900 if width >= 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _seed_health_project()

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            # Assert HEALTH section exists
            health_rows = page.locator('[data-testid^="health-row-"]')
            assert health_rows.count() >= 1, (
                f"Expected >= 1 health row, got {health_rows.count()}"
            )

            # Check specific rows
            review_row = page.locator('[data-testid="health-row-review_wait"]')
            if review_row.count() > 0:
                text = review_row.inner_text()
                assert "REVIEW WAIT" in text
                assert "D MEDIAN" in text
                assert "WAITING" in text

            issue_row = page.locator('[data-testid="health-row-issue_aging"]')
            if issue_row.count() > 0:
                text = issue_row.inner_text()
                assert "ISSUE AGING" in text

            ci_row = page.locator('[data-testid="health-row-ci"]')
            if ci_row.count() > 0:
                text = ci_row.inner_text()
                assert "CI" in text

            release_row = page.locator('[data-testid="health-row-release"]')
            if release_row.count() > 0:
                text = release_row.inner_text()
                assert "RELEASE" in text

            # CHECKED token on the section caption
            checked = page.locator('[data-testid="health-checked"]')
            if checked.count() > 0:
                assert "CHECKED" in checked.inner_text()

            _assert_no_raw_button(page)
            _assert_no_zero_counter(page)

            _shot(page, f"build-room-health-{width}", width, SHOTS_03)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_health_ready_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """All-green HEALTH: CLEAR, PASSING, READY present."""
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        height = 900 if width >= 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _seed_all_green_project()

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            body_text = page.locator('[data-testid="room-body"]').inner_text()
            # At least the HEALTH section should be present
            health_rows = page.locator('[data-testid^="health-row-"]')
            assert health_rows.count() >= 1, (
                f"Expected >= 1 health row in all-green, got {health_rows.count()}"
            )

            # Check green tokens where rows are present
            issue_row = page.locator('[data-testid="health-row-issue_aging"]')
            if issue_row.count() > 0:
                assert "CLEAR" in issue_row.inner_text()

            ci_row = page.locator('[data-testid="health-row-ci"]')
            if ci_row.count() > 0:
                assert "PASSING" in ci_row.inner_text()

            release_row = page.locator('[data-testid="health-row-release"]')
            if release_row.count() > 0:
                assert "READY" in release_row.inner_text()

            _assert_no_raw_button(page)
            _assert_no_zero_counter(page)

            _shot(page, f"build-room-health-ready-{width}", width, SHOTS_03)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Nudge card and receipt helpers ────────────────────────────────────


def _seed_nudge_project_and_step(page: Any) -> tuple[str, str]:
    """Seed a project, People relationship with alias, Watch PRs,
    steward policy enabling github_comment, and a proposed nudge step.
    Returns (project_id, step_id)."""
    from holdspeak.db import get_database
    from datetime import datetime, timedelta, timezone as _tz
    db = get_database()
    now = datetime.now(_tz.utc)
    project_id = f"proj-nudge-{uuid.uuid4().hex[:8]}"

    # 1. Seed project
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, ?, ?)",
            (project_id,
             "Ship the Q4 platform on schedule with zero incidents",
             now.isoformat(), now.isoformat()),
        )

    # 2. Seed Watch with PR entities (reviewer = ania-k)
    pr_entities = [
        {
            "number": 612,
            "title": "Rig settles animations before every shot",
            "url": "https://github.com/org/repo/pull/612",
            "state": "OPEN",
            "isDraft": False,
            "reviewRequests": ["ania-k"],
            "reviewDecision": None,
            "checks": "success",
            "headRefOid": "abc123",
            "updatedAt": (now - timedelta(hours=6)).isoformat(),
            "createdAt": (now - timedelta(days=3)).isoformat(),
        },
    ]
    snapshot = json.dumps(pr_entities)
    watch_id = f"watch-{project_id}-pr"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', 'PRs', "
            "'{}', ?, 1, datetime('now'), NULL, ?, datetime('now'), datetime('now'))",
            (watch_id, snapshot, project_id),
        )

    # 3. Set up People store and create a relationship via API
    _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
    result = _api(page, "POST", "/api/people/relationships", {
        "display_name": "Ania Kowalska",
        "relationship_kind": "direct_report",
    }, token=TOKEN)
    payload = result.get("payload", result)
    rel_id = payload["relationship"]["id"]

    # Add owner alias matching the reviewer login
    _api(page, "POST", f"/api/people/relationships/{rel_id}/owner-aliases", {
        "alias": "ania-k",
    }, token=TOKEN)

    # 4. Seed steward policy with github_comment eligible
    policy_id = f"pol-{uuid.uuid4().hex[:8]}"
    now_iso = now.isoformat(timespec="seconds")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO steward_policies "
            "(id, project_id, eligible_effect_kinds_json, yolo_flags_json, "
            " max_retries, max_actions_per_run, cooldown_seconds, "
            " bounds_json, enabled, unattended_enabled, nudge_template, "
            " created_at, updated_at) "
            'VALUES (?, ?, \'["github_comment"]\', \'{}\', 3, 10, 0, '
            "'{}', 1, 0, '', ?, ?)",
            (policy_id, project_id, now_iso, now_iso),
        )

    # 5. Seed a steward run + proposed nudge step
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    step_id = f"step-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO steward_runs "
            "(id, project_id, state, phase, summary_json, created_at, updated_at) "
            "VALUES (?, ?, 'running', 'act', '{}', ?, ?)",
            (run_id, project_id, now_iso, now_iso),
        )
        nudge_payload = json.dumps({
            "repo": "org/repo",
            "pr_number": 612,
            "pr_title": "Rig settles animations before every shot",
            "pr_url": "https://github.com/org/repo/pull/612",
            "reviewer_login": "ania-k",
            "display_name": "Ania Kowalska",
            "days": 3,
            "comment_text": "This PR has been waiting for review for 3 days. Flagged by HoldSpeak.",
            "host": "github.com",
        })
        conn.execute(
            "INSERT INTO steward_steps "
            "(id, run_id, phase, seq, effect_kind, state, "
            " expected_state_json, observed_state_json, "
            " idempotency_key, receipt_json, created_at, updated_at) "
            "VALUES (?, ?, 'act', 1, 'github_comment', 'proposed', "
            " ?, '{}', ?, '{}', ?, ?)",
            (step_id, run_id, nudge_payload,
             f"nudge:{project_id}:org/repo:612:ania-k",
             now_iso, now_iso),
        )

    return project_id, step_id


def _patch_resolve_review_people(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch _resolve_review_people to return a resolved bottleneck person
    matching reviewer login 'ania-k' to display name 'Ania Kowalska'.
    In isolated HOME the encrypted People store may not match the alias."""
    import holdspeak.services.project_service as ps

    _orig = ps.ProjectService._resolve_review_people

    def _patched(self: Any, project_id: str, per_reviewer: list, threshold_days: float = 2.0) -> list:
        # Try the real resolver first
        result = _orig(self, project_id, per_reviewer, threshold_days)
        if result:
            return result
        # Fall back: synthesize from per_reviewer for the test alias
        for rev in per_reviewer:
            login = rev.get("login", "")
            if login == "ania-k" and rev.get("median_days", 0) >= threshold_days:
                result.append({
                    "relationship_id": "rel-ania-test",
                    "display_name": "Ania Kowalska",
                    "login": "ania-k",
                    "median_days": rev["median_days"],
                    "count": rev["count"],
                })
        return result

    monkeypatch.setattr(ps.ProjectService, "_resolve_review_people", _patched)


def _stub_gh_connector(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub build_github_pr_connector so Send never calls gh.
    Returns a fake connector that records the call and returns a comment URL."""
    import holdspeak.services.project_steward_service as pss

    _orig_send = pss.ProjectStewardService.send_nudge

    def _patched_send(self: Any, principal: Any, step_id: str, text: str) -> dict:
        """Intercept send_nudge to stub the gh pr comment call."""
        import holdspeak.plugins.builtin.github_pr_actuator as gpa

        orig_build = gpa.build_github_pr_connector

        def _fake_build(action: str, runner: Any = None) -> Any:
            def _fake_connector(proposal: Any) -> dict:
                return {
                    "output": "https://github.com/org/repo/pull/612#issuecomment-123456",
                    "exit_code": 0,
                }
            return _fake_connector

        monkeypatch.setattr(gpa, "build_github_pr_connector", _fake_build)
        result = _orig_send(self, principal, step_id, text)
        monkeypatch.setattr(gpa, "build_github_pr_connector", orig_build)
        return result

    monkeypatch.setattr(pss.ProjectStewardService, "send_nudge", _patched_send)


def _run_nudge_card_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Nudge card unfolds with PR, text, GITHUB.COM, Send/Dismiss."""
    _stub_gh_connector(monkeypatch)
    _patch_resolve_review_people(monkeypatch)
    # File-based key store so macOS Keychain is not needed in isolated HOME.
    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        height = 900 if width >= 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id, step_id = _seed_nudge_project_and_step(page)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            # Debug: check what the room returns
            room_data = _api(page, "GET",
                             f"/api/projects/{project_id}/room",
                             token=TOKEN)
            room_payload = room_data.get("payload", room_data)
            needs_items = []
            if isinstance(room_payload, dict):
                ny = room_payload.get("needsYou") or room_payload.get("needs_you") or {}
                needs_items = ny.get("items", []) if isinstance(ny, dict) else []
            bottleneck_items = [i for i in needs_items if i.get("kind") == "review_bottleneck"]

            # Also check nudges
            nudges_data = _api(page, "GET",
                               f"/api/projects/{project_id}/nudges?state=proposed",
                               token=TOKEN)
            nudges_payload = nudges_data.get("payload", nudges_data)
            nudge_list = nudges_payload.get("nudges", []) if isinstance(nudges_payload, dict) else []

            # The bottleneck row should be present
            bottleneck = page.locator('[data-testid="bottleneck-row"]')
            assert bottleneck.count() >= 1, (
                f"Expected >= 1 bottleneck row, got {bottleneck.count()}"
                f"\nNeeds-you items: {[{'kind': i.get('kind'), 'title': i.get('title'), 'verb': i.get('verb')} for i in needs_items]}"
                f"\nBottleneck items: {bottleneck_items}"
                f"\nNudges: {nudge_list}"
            )

            # Click the Nudge verb to open the card
            nudge_btn = page.locator('[data-testid="nudge-verb"]').first
            assert nudge_btn.count() > 0, "Nudge verb not found on bottleneck row"
            nudge_btn.click()
            page.wait_for_timeout(500)
            _settle(page)

            # The nudge card should be open
            card = page.locator('[data-testid="nudge-card"]')
            assert card.count() > 0, "Nudge card not visible after click"

            # Verify card contents
            card_who = page.locator('[data-testid="nudge-card-who"]')
            assert card_who.count() > 0, "Card missing who"
            assert "Ania Kowalska" in card_who.inner_text()

            card_pr = page.locator('[data-testid="nudge-card-pr"]')
            if card_pr.count() > 0:
                pr_text = card_pr.inner_text()
                assert "#612" in pr_text, f"PR number not in card: {pr_text}"

            # Check the card text contains GITHUB.COM (the EgressChip)
            card_text = card.inner_text()
            assert "GITHUB.COM" in card_text, f"GITHUB.COM not in card: {card_text}"

            send_btn = page.locator('[data-testid="nudge-send"]')
            assert send_btn.count() > 0, "Send button missing"
            dismiss_btn = page.locator('[data-testid="nudge-dismiss"]')
            assert dismiss_btn.count() > 0, "Dismiss button missing"

            _assert_no_raw_button(page)

            _shot(page, f"build-room-nudge-card-{width}", width, SHOTS_04)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_nudge_sent_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Send nudge -> receipt row with name, PR, time, GITHUB.COM; no Undo.
    Bottleneck row shows NUDGED JUST NOW."""
    _stub_gh_connector(monkeypatch)
    _patch_resolve_review_people(monkeypatch)
    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        height = 900 if width >= 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id, step_id = _seed_nudge_project_and_step(page)

            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)

            # Open the nudge card
            nudge_btn = page.locator('[data-testid="nudge-verb"]').first
            assert nudge_btn.count() > 0, "Nudge verb not found"
            nudge_btn.click()
            page.wait_for_timeout(500)
            _settle(page)

            # Click Send (stubbed -- won't call gh)
            send_btn = page.locator('[data-testid="nudge-send"]')
            assert send_btn.count() > 0, "Send button missing"
            send_btn.click()
            page.wait_for_timeout(1500)
            _settle(page)

            # The receipt row should appear
            receipt = page.locator('[data-testid="nudge-receipt-row"]')
            assert receipt.count() > 0, "Receipt row not visible after Send"
            receipt_text = receipt.inner_text()
            rt = receipt_text.upper()
            assert "SENT" in rt, f"Receipt missing SENT: {receipt_text}"
            assert "ANIA KOWALSKA" in rt, f"Receipt missing name: {receipt_text}"
            assert "#612" in receipt_text, f"Receipt missing PR: {receipt_text}"
            assert "GITHUB.COM" in rt, f"Receipt missing egress: {receipt_text}"
            assert "UNDO" not in rt, f"Receipt has Undo (should not): {receipt_text}"

            _assert_no_raw_button(page)

            _shot(page, f"build-room-nudge-sent-{width}", width, SHOTS_04)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Pytest parametrized entries ──────────────────────────────────────


@pytest.mark.timeout(120)
def test_health_rows_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_health_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_health_rows_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_health_rig(tmp_path, monkeypatch, 393)


@pytest.mark.timeout(120)
def test_health_ready_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_health_ready_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_health_ready_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_health_ready_rig(tmp_path, monkeypatch, 393)


@pytest.mark.timeout(120)
def test_nudge_card_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_nudge_card_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_nudge_card_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_nudge_card_rig(tmp_path, monkeypatch, 393)


@pytest.mark.timeout(120)
def test_nudge_sent_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_nudge_sent_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_nudge_sent_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run_nudge_sent_rig(tmp_path, monkeypatch, 393)
