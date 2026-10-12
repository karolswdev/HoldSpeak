"""Room glass helpers shared by the live Room browser tests.

Copied verbatim from tests/e2e/test_hs173_health_glass.py when that file was
parked by the test diet (2026-10-11); its rows moved to vitest and Python
successors. test_philo10_02_nudge_unknown_glass.py still drives the nudge card
in a browser and seeds through these helpers.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _normal_chair, _settle

TOKEN = "hs173-health"


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
            if ((b.classList.contains('btn') || b.classList.contains('btn--chrome')) ||
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



def open_room_folds(page: Any) -> None:
    """PHILO-17 refit: the Room folds its secondary sections (Sources,
    Pages, Decisions and owed, Since you looked, Files, People, Briefs; in
    History, Writes). A test that reads one opens the folds first, as the
    owner presses them open."""
    page.locator("[data-testid=room-body] .room-fold").first.wait_for(state="attached", timeout=20_000)
    page.evaluate("() => document.querySelectorAll('.room-fold > details').forEach((d) => { d.open = true; })")
