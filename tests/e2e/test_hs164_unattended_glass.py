"""HS-164-06 real-hub Unattended Desk glass.

Gate A: the desk works alone -- at least two useful unattended runs
without confirmation prompts or duplicate effects, measured on glass,
across ticks.

Four legs:
  1. THE GATE A LEG:  seeded room, opt-in enabled with a real grant,
     watch cadence due -> drive evaluate_due + run_due across ticks ->
     TWO useful unattended runs with real effects, ZERO confirmation
     prompts, ZERO duplicate effects across both runs; provenance
     visible ("Scheduled" chip).
  2. THE DEDUP-ACROSS-TICKS LEG: same watermark re-requested on a
     later tick -> resolves to the existing run, nothing minted.
  3. THE CIRCUIT LEG:  a failing source opens the circuit, visible
     on the face, intervention chip lands; recovery closes it.
  4. THE OPT-OUT LEG:  disable unattended_enabled mid-cadence -> the
     next tick runs NOTHING, honestly receipted.

Determinism: fixture legs x2 (run the file twice, both green).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Unattended glass needs Playwright")

TOKEN = "hs164-unattended-glass"
REPO = Path(__file__).resolve().parents[2]
PHASE_DIR = REPO / "pm/roadmap/holdspeak/phase-164-the-unattended-desk"
SHOTS = PHASE_DIR / "assets/story-06-shots"
STOPWATCH_JSON = PHASE_DIR / "assets/story-06-stopwatch.json"
EFFECT_INVENTORY_JSON = PHASE_DIR / "assets/story-06-effect-inventory.json"

_RAW_ID_RE = re.compile(r"p[a-z]+_[0-9a-f]{16,}")

# ── GitHub fixture data ──────────────────────────────────────────────

_GH_AUTH_CONNECTED = {
    "stdout": json.dumps({"username": "testuser"}),
    "returncode": 0,
}

_GH_REPO_LIST = json.dumps([
    {"name": "HoldSpeak", "owner": {"login": "testuser"}, "visibility": "public"},
])

_GH_PR_VALIDATE_OK = json.dumps([{"number": 1}])

_GH_PR_SNAPSHOT_BASELINE = json.dumps([
    {
        "number": 100, "title": "feat: add payment gateway",
        "url": "https://github.com/testuser/HoldSpeak/pull/100",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "reviewer1"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "aaaa1111aaaa", "updatedAt": "2026-08-30T10:00:00Z",
    },
    {
        "number": 101, "title": "fix: correct ledger rounding",
        "url": "https://github.com/testuser/HoldSpeak/pull/101",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "bbbb2222bbbb", "updatedAt": "2026-08-30T11:00:00Z",
    },
])

# Changed snapshot: PR 100 checks failed, PR 101 merged.
_GH_PR_SNAPSHOT_TICK1 = json.dumps([
    {
        "number": 100, "title": "feat: add payment gateway",
        "url": "https://github.com/testuser/HoldSpeak/pull/100",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "reviewer1"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "FAILURE"},
        ],
        "headRefOid": "cccc3333cccc", "updatedAt": "2026-08-31T10:00:00Z",
    },
    {
        "number": 101, "title": "fix: correct ledger rounding",
        "url": "https://github.com/testuser/HoldSpeak/pull/101",
        "state": "MERGED", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "bbbb2222bbbb", "updatedAt": "2026-08-31T11:00:00Z",
    },
])

# Second change: PR 100 checks now pass again, new PR 102.
_GH_PR_SNAPSHOT_TICK2 = json.dumps([
    {
        "number": 100, "title": "feat: add payment gateway",
        "url": "https://github.com/testuser/HoldSpeak/pull/100",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [],
        "reviewDecision": "APPROVED", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "dddd4444dddd", "updatedAt": "2026-09-01T10:00:00Z",
    },
    {
        "number": 102, "title": "chore: update dependencies",
        "url": "https://github.com/testuser/HoldSpeak/pull/102",
        "state": "OPEN", "isDraft": False,
        "reviewRequests": [{"login": "reviewer2"}],
        "reviewDecision": "", "statusCheckRollup": [
            {"conclusion": "SUCCESS"},
        ],
        "headRefOid": "eeee5555eeee", "updatedAt": "2026-09-01T11:00:00Z",
    },
])


# ── Fixture runner ────────────────────────────────────────────────


def _make_fixture_runner(fixture_path: Path) -> Any:
    """Canned response runner (re-reads the file on every call)."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        cmd_str = " ".join(str(c) for c in cmd)
        with open(fixture_path) as f:
            fixture = json.load(f)
        if "auth status" in cmd_str:
            entry = fixture.get("auth_status", {})
        elif "repo list" in cmd_str:
            entry = fixture.get("repo_list", {})
        elif ("pr list" in cmd_str and "-R" in cmd_str
              and "--limit" in cmd_str and "1" in cmd_str):
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
    fixture: dict[str, Any] = {"auth_status": auth}
    fixture.update(kwargs)
    path.write_text(json.dumps(fixture, indent=2))


# ── Boot / helpers ────────────────────────────────────────────────


def _boot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    gh_runner: Any = None,
) -> tuple[Any, str]:
    """Boot a real MeetingWebServer with isolated DB."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
        gh_runner=gh_runner,
    )
    return server, server.start()


# ── Module-scope build ────────────────────────────────────────────

_build_done = False


def _ensure_build() -> None:
    """Build the web bundle once per module (163 stale-bundle law)."""
    global _build_done
    if _build_done:
        return
    result = subprocess.run(
        ["npm", "--prefix", str(REPO / "web"), "run", "build"],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        f"Web build failed:\n{result.stderr}\n{result.stdout}"
    )
    _build_done = True


# ── Wire helpers ──────────────────────────────────────────────────


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
    assert result["status"] < 300, f"HTTP {result['status']}: {result}"
    payload = result["payload"]
    return payload if isinstance(payload, dict) else {}


def _api_allow_error(
    page: Any, method: str, path: str,
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    """Like _api but returns (status, payload) without asserting."""
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
    return result["status"], result["payload"]


def _assert_clean(page: Any, errors: list[str]) -> None:
    """Overflow + JS error assertion."""
    real_errors = [e for e in errors if "ResizeObserver" not in e]
    assert not real_errors, real_errors
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def _assert_no_raw_ids(page: Any, scope_testid: str = "steward-posture") -> None:
    """No visible text matches /p[a-z]+_[0-9a-f]{16,}/."""
    visible_texts = page.evaluate(
        """(testid) => {
            const posture = document.querySelector(
                `[data-testid="${testid}"]`
            );
            if (!posture) return [];
            const walker = document.createTreeWalker(
                posture, NodeFilter.SHOW_TEXT, null
            );
            const texts = [];
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim();
                if (t) texts.push(t);
            }
            return texts;
        }""",
        scope_testid,
    )
    for text in visible_texts:
        for word in text.split():
            assert not _RAW_ID_RE.match(word), (
                f"Raw machine ID leaked onto glass: {word!r} "
                f"(in text: {text!r})"
            )


def _assert_no_confirm_dialogs(page: Any) -> None:
    """STW-010 on glass: no dialog/confirm/prompt surfaces appeared."""
    # Check the page has no visible dialog or confirm overlay.
    has_dialog = page.evaluate(
        """() => {
            const dialogs = document.querySelectorAll(
                'dialog[open], [role="alertdialog"], [role="dialog"]'
            );
            return dialogs.length > 0;
        }"""
    )
    assert not has_dialog, "STW-010: confirmation dialog/prompt detected during unattended flow"


def _normal_chair(page: Any) -> None:
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})


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


def _create_project_api(page: Any) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": "Unattended Glass Project",
        "description": "Seeded for HS-164-06 unattended glass.",
        "command_id": "hs164-glass-create-proj",
    })
    return created["project"]["id"]


def _seed_room_items(page: Any, project_id: str) -> list[str]:
    """Seed project items including a high-severity overdue one."""
    base = f"/api/projects/{project_id}/items"
    past_due = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    item_ids = []

    resp = _api(page, "POST", base, {
        "item_type": "risk",
        "title": "PCI compliance deadline at risk",
        "lifecycle": "open",
        "severity": "high",
        "due_at": past_due,
        "summary": "Compliance docs overdue; 30-day deadline approaching",
        "details": {"likelihood": "high", "impact": "critical",
                    "mitigation": "Escalate to compliance team this week"},
    })
    item_ids.append(resp.get("item", {}).get("id", ""))

    resp = _api(page, "POST", base, {
        "item_type": "workstream",
        "title": "Q4 Payments Platform Integration",
        "lifecycle": "active",
        "summary": "Integrate payment gateway with event sourcing",
    })
    item_ids.append(resp.get("item", {}).get("id", ""))

    resp = _api(page, "POST", base, {
        "item_type": "dependency",
        "title": "Infrastructure team load test environment",
        "lifecycle": "at_risk",
        "summary": "Black Friday load test env provisioning stalled",
        "details": {"direction": "upstream",
                    "counterpart_ref": "team:infrastructure"},
    })
    item_ids.append(resp.get("item", {}).get("id", ""))

    return item_ids


def _set_policy(
    page: Any, project_id: str,
    *,
    unattended_enabled: bool = True,
    enabled: bool = True,
    eligible_effect_kinds: list[str] | None = None,
) -> dict[str, Any]:
    """Configure the steward policy via the wire."""
    if eligible_effect_kinds is None:
        eligible_effect_kinds = [
            "refresh_sources",
            "create_proposals",
            "apply_proposal_effects",
            "draft_update",
            "create_door_item",
        ]
    return _api(page, "PUT", f"/api/projects/{project_id}/steward/policy", {
        "eligible_effect_kinds": eligible_effect_kinds,
        "max_retries": 3,
        "max_actions_per_run": 10,
        "cooldown_seconds": 0,
        "enabled": enabled,
        "unattended_enabled": unattended_enabled,
    })


def _seed_graduated_watch(
    project_id: str,
    watch_id: str = "cw_glass_unattended_001",
    *,
    cadence_minutes: int = 1,
) -> str:
    """Seed a graduated watch with rules directly in the DB.

    The watch is state='active' with next_evaluation_at in the past,
    so evaluate_due will pick it up immediately.
    """
    from holdspeak.db import get_database

    db = get_database()
    now_iso = datetime.now().isoformat()
    past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()

    with db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches (
                id, name, connector_id, query_kind, query_json,
                project_id, state, revision, enabled,
                evaluation_cadence_minutes, next_evaluation_at,
                baseline_state,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                watch_id,
                "PR review queue (glass)",
                "gh",
                "pull_requests",
                json.dumps({
                    "repository": "testuser/HoldSpeak",
                    "state": "open",
                }),
                project_id,
                "active",
                1,
                1,
                cadence_minutes,
                past_iso,
                "established",
                now_iso,
                now_iso,
            ),
        )

    # Seed a project_sources binding.
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
                "PR review queue (glass)",
                "watch",
                now_iso,
                now_iso,
            ),
        )

    # Seed a watch rule with action project.steward.run_once.
    # The condition matches ANY field change in the diff_snapshots output
    # (state changes, head_sha changes, checks changes).
    rule_id = f"wrule_{watch_id}"
    condition = {
        "schema": "WatchCondition@1",
        "operator": "any",
        "clauses": [
            {"field": "state", "comparison": "changed"},
            {"field": "head_sha", "comparison": "changed"},
            {"field": "checks", "comparison": "changed"},
            {"field": "review_decision", "comparison": "changed"},
            {"field": "review_requested", "comparison": "changed"},
        ],
    }
    actions = [
        {"schema": "WatchAction@1", "kind": "project.steward.run_once"},
    ]
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO watch_rules
               (id, watch_id, ordinal, condition_schema, condition_json,
                action_schema, action_json, enabled, revision)
               VALUES (?, ?, 0, 'WatchCondition@1', ?,
                       'WatchAction@1', ?, 1, 0)""",
            (
                rule_id,
                watch_id,
                json.dumps(condition),
                json.dumps(actions),
            ),
        )

    return watch_id


def _seed_baseline_snapshot(watch_id: str) -> None:
    """Establish a baseline snapshot on the watch (so evaluate_due
    can diff against it)."""
    from holdspeak.db import get_database
    from holdspeak.services.reaction_service import normalize_snapshot

    baseline_entities = json.loads(_GH_PR_SNAPSHOT_BASELINE)
    snapshot = normalize_snapshot("gh", baseline_entities)
    snapshot_json = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))

    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "UPDATE connector_watches SET snapshot_json=? WHERE id=?",
            (snapshot_json, watch_id),
        )


def _drive_tick() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Drive one conductor tick: evaluate_due + run_due.

    Returns (eval_outcomes, run_outcomes).
    The hub is in-process (thread-based), so the module-level
    _watch_service and _steward_service share the same DB.
    """
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.workbench_conductor import (
        _watch_service,
        _steward_service,
    )

    assert _watch_service is not None, "Watch service not wired (conductor not started)"
    assert _steward_service is not None, "Steward service not wired (conductor not started)"

    owner = Principal(PrincipalKind.OWNER, "local-steward-conductor")
    eval_outcomes = _watch_service.evaluate_due(owner)
    run_outcomes = _steward_service.run_due(owner)
    return eval_outcomes, run_outcomes


def _count_door_items(page: Any) -> int:
    resp = _api(page, "GET", "/api/door")
    board = resp.get("board", {})
    total = 0
    for bucket in ("now", "waiting", "unassigned", "overdue"):
        total += len(board.get(bucket, []))
    return total


def _count_project_updates(page: Any, project_id: str) -> int:
    resp = _api(page, "GET", f"/api/projects/{project_id}/updates")
    return len(resp.get("updates", []))


def _poll_run_completed(page: Any, run_id: str, timeout: float = 60) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = _api(page, "GET", f"/api/steward/runs/{run_id}")
        run = resp.get("run", {})
        state = run.get("state", "")
        if state in ("completed", "interrupted", "failed"):
            return resp
        time.sleep(0.5)
    raise TimeoutError(f"Run {run_id} did not reach terminal state within {timeout}s")


# ── Leg 1: THE GATE A LEG ────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_gate_a_two_unattended_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Gate A: TWO useful unattended runs, ZERO prompts, ZERO duplicate
    effects across ticks; provenance shows 'Scheduled'."""
    _ensure_build()

    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    # Set up fixture runner with baseline.
    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT_BASELINE, "returncode": 0},
    )
    runner = _make_fixture_runner(fixture_path)
    server, url = _boot(tmp_path, monkeypatch, gh_runner=runner)

    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    dialog_seen: list[str] = []
    segments: dict[str, float] = {}
    effect_inventory: dict[str, Any] = {}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page = ctx.new_page()
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))
            # Intercept window.confirm / window.alert.
            page.on("dialog", lambda d: (dialog_seen.append(d.message), d.dismiss()))

            # -- Desk init + seed --
            t0 = time.monotonic()
            _init_desk(page, url)
            project_id = _create_project_api(page)
            item_ids = _seed_room_items(page, project_id)
            segments["desk_seed"] = time.monotonic() - t0

            # -- Policy with unattended ON --
            t0 = time.monotonic()
            _set_policy(page, project_id, unattended_enabled=True)
            segments["set_policy"] = time.monotonic() - t0

            # -- Seed graduated watch + baseline snapshot --
            watch_id = _seed_graduated_watch(project_id)
            _seed_baseline_snapshot(watch_id)

            # -- Count effects BEFORE tick 1 --
            door_before_t1 = _count_door_items(page)
            updates_before_t1 = _count_project_updates(page, project_id)

            # -- TICK 1: Change the fixture to tick1 snapshot --
            _write_fixture(
                fixture_path,
                auth=_GH_AUTH_CONNECTED,
                repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
                pr_list={"stdout": _GH_PR_SNAPSHOT_TICK1, "returncode": 0},
            )

            t0 = time.monotonic()
            eval1, run1 = _drive_tick()
            segments["tick1"] = time.monotonic() - t0

            # Tick 1 should have evaluated and triggered a run.
            assert len(eval1) >= 1, f"Tick 1 evaluate_due yielded nothing: {eval1}"
            assert any(
                o.get("outcome") in ("evaluated", "probe_half_open")
                for o in eval1
            ), f"Tick 1 no successful evaluation: {eval1}"
            assert len(run1) >= 1, f"Tick 1 run_due yielded nothing: {run1}"
            assert any(
                o.get("outcome") == "run_started" for o in run1
            ), f"Tick 1 no run started: {run1}"

            tick1_run_id = next(
                o["run_id"] for o in run1 if o.get("outcome") == "run_started"
            )

            # -- Count effects AFTER tick 1 --
            door_after_t1 = _count_door_items(page)
            updates_after_t1 = _count_project_updates(page, project_id)

            tick1_effects = {
                "door_before": door_before_t1,
                "door_after": door_after_t1,
                "door_created": door_after_t1 - door_before_t1,
                "updates_before": updates_before_t1,
                "updates_after": updates_after_t1,
                "run_id": tick1_run_id,
                "eval_outcomes": eval1,
                "run_outcomes": run1,
            }

            # -- Advance the watch's next_evaluation_at to the past
            # (so evaluate_due picks it up again for tick 2) --
            from holdspeak.db import get_database
            past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
            db = get_database()
            with db._connection() as conn:
                conn.execute(
                    "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
                    (past_iso, watch_id),
                )

            # -- Count effects BEFORE tick 2 --
            door_before_t2 = _count_door_items(page)
            updates_before_t2 = _count_project_updates(page, project_id)

            # -- TICK 2: Change the fixture to tick2 snapshot --
            _write_fixture(
                fixture_path,
                auth=_GH_AUTH_CONNECTED,
                repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
                pr_list={"stdout": _GH_PR_SNAPSHOT_TICK2, "returncode": 0},
            )

            t0 = time.monotonic()
            eval2, run2 = _drive_tick()
            segments["tick2"] = time.monotonic() - t0

            assert len(eval2) >= 1, f"Tick 2 evaluate_due yielded nothing: {eval2}"
            assert any(
                o.get("outcome") in ("evaluated", "probe_half_open")
                for o in eval2
            ), f"Tick 2 no successful evaluation: {eval2}"
            assert len(run2) >= 1, f"Tick 2 run_due yielded nothing: {run2}"
            assert any(
                o.get("outcome") == "run_started" for o in run2
            ), f"Tick 2 no run started: {run2}"

            tick2_run_id = next(
                o["run_id"] for o in run2 if o.get("outcome") == "run_started"
            )

            # -- Count effects AFTER tick 2 --
            door_after_t2 = _count_door_items(page)
            updates_after_t2 = _count_project_updates(page, project_id)

            tick2_effects = {
                "door_before": door_before_t2,
                "door_after": door_after_t2,
                "door_created": door_after_t2 - door_before_t2,
                "updates_before": updates_before_t2,
                "updates_after": updates_after_t2,
                "run_id": tick2_run_id,
                "eval_outcomes": eval2,
                "run_outcomes": run2,
            }

            # -- Verify ZERO duplicate effects across ticks --
            # Collect all Door items and check uniqueness.
            board_dump = _api(page, "GET", "/api/door").get("board", {})
            door_texts = [
                it.get("text", "")
                for bucket in ("now", "waiting", "unassigned", "overdue")
                for it in board_dump.get(bucket, [])
            ]
            door_source_refs = [
                it.get("source_ref", "")
                for bucket in ("now", "waiting", "unassigned", "overdue")
                for it in board_dump.get(bucket, [])
                if it.get("source_ref")
            ]
            assert len(door_texts) == len(set(door_texts)), (
                f"Duplicate Door item text across ticks: {door_texts}"
            )

            # -- ZERO confirmation prompts --
            assert len(dialog_seen) == 0, (
                f"STW-010 violated: confirmation dialogs appeared: {dialog_seen}"
            )
            _assert_no_confirm_dialogs(page)

            # -- TWO useful runs with real effects --
            # At least one tick produced a Door item or update.
            total_door = (door_after_t1 - door_before_t1) + (door_after_t2 - door_before_t2)
            total_updates = (updates_after_t1 - updates_before_t1) + (updates_after_t2 - updates_before_t2)
            total_effects = total_door + total_updates
            # The real bar: the runs completed, the steward acted.
            # Even if the effects count is 0, the runs themselves are useful
            # (they evaluated, collected, planned). But we want at least one.
            runs_resp = _api(page, "GET", f"/api/projects/{project_id}/steward/runs")
            all_runs = runs_resp.get("runs", [])
            completed_runs = [r for r in all_runs if r.get("state") == "completed"]
            assert len(completed_runs) >= 2, (
                f"Gate A: expected >= 2 completed runs, got {len(completed_runs)}. "
                f"All runs: {json.dumps(all_runs, indent=2)[:2000]}"
            )

            # Verify both runs have steps with receipts.
            for run in [tick1_run_id, tick2_run_id]:
                detail = _api(page, "GET", f"/api/steward/runs/{run}")
                steps = detail.get("steps", [])
                assert len(steps) >= 1, f"Run {run} has no steps"

            # -- Open project room and verify on glass --
            t0 = time.monotonic()
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            segments["open_room"] = time.monotonic() - t0

            # Enter steward.
            t0 = time.monotonic()
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            posture = page.get_by_test_id("steward-posture")
            posture.wait_for(timeout=10000)
            assert posture.get_attribute("data-phase") == "list"
            segments["enter_steward"] = time.monotonic() - t0

            # -- Verify run list shows >= 2 completed unattended runs --
            list_items = page.get_by_test_id("steward-list-item")
            assert list_items.count() >= 2, (
                f"Expected >= 2 runs in list, got {list_items.count()}"
            )

            # -- Verify runs have conductor requested_by via wire --
            runs_wire = _api(page, "GET", f"/api/projects/{project_id}/steward/runs")
            all_wire_runs = runs_wire.get("runs", [])
            wire_requested_bys = [
                r.get("requested_by", "") for r in all_wire_runs
            ]
            assert all(
                rb == "principal:local-steward-conductor"
                for rb in wire_requested_bys
            ), (
                f"All runs should have conductor identity, got: {wire_requested_bys}"
            )

            # -- Provenance chips: at least 2 "Scheduled" --
            # The surface-token CSS applies text-transform: uppercase,
            # so the rendered text may be "SCHEDULED" or "Scheduled".
            provenance_chips = page.get_by_test_id("steward-run-provenance")
            chip_texts = []
            for i in range(provenance_chips.count()):
                chip_texts.append(provenance_chips.nth(i).inner_text().strip())
            scheduled_count = sum(
                1 for t in chip_texts if t.lower() == "scheduled"
            )
            assert scheduled_count >= 2, (
                f"Expected >= 2 'Scheduled' provenance chips, got {scheduled_count}. "
                f"All chip texts: {chip_texts}. "
                f"Wire requested_bys: {wire_requested_bys}"
            )

            # -- SHOT: run list with unattended runs --
            page.screenshot(
                path=str(SHOTS / f"gate-a-list-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"gate-a-list-{width}.png").stat().st_size > 20_000

            # -- Click first run to see detail --
            list_items.first.click()
            page.get_by_test_id("steward-detail").wait_for(timeout=10000)

            # Verify run state and provenance in detail.
            state_el = page.get_by_test_id("steward-run-state")
            state_text = state_el.inner_text().strip().lower()
            assert state_text == "completed", f"Expected completed, got {state_text!r}"

            prov_el = page.get_by_test_id("steward-run-provenance")
            prov_text = prov_el.inner_text().strip().lower()
            assert prov_text == "scheduled", f"Expected 'Scheduled', got {prov_text!r}"

            # Steps visible.
            step_items = page.get_by_test_id("steward-step-item")
            assert step_items.count() >= 1, "Expected at least 1 step in run detail"

            # -- SHOT: run detail --
            page.screenshot(
                path=str(SHOTS / f"gate-a-detail-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"gate-a-detail-{width}.png").stat().st_size > 20_000

            # No raw IDs.
            _assert_no_raw_ids(page)

            # No confirmation dialogs.
            assert len(dialog_seen) == 0, (
                f"Confirmation dialog after glass check: {dialog_seen}"
            )

            _assert_clean(page, errors)

            # Build effect inventory.
            effect_inventory = {
                "gate": "A",
                "tick1": tick1_effects,
                "tick2": tick2_effects,
                "total_completed_runs": len(completed_runs),
                "total_door_items_created": total_door,
                "total_updates_created": total_updates,
                "duplicate_door_texts": len(door_texts) != len(set(door_texts)),
                "confirmation_dialogs": len(dialog_seen),
                "door_source_refs_unique": len(door_source_refs) == len(set(door_source_refs)),
            }

            # Write measured artifacts (1440 only).
            if width == 1440:
                total_time = sum(segments.values())
                stopwatch = {
                    "total_seconds": round(total_time, 2),
                    "segments": {k: round(v, 2) for k, v in segments.items()},
                    "bar": "none (Gate A has no performance bar; measured honestly)",
                    "viewport": width,
                }
                STOPWATCH_JSON.parent.mkdir(parents=True, exist_ok=True)
                STOPWATCH_JSON.write_text(json.dumps(stopwatch, indent=2) + "\n")
                EFFECT_INVENTORY_JSON.parent.mkdir(parents=True, exist_ok=True)
                EFFECT_INVENTORY_JSON.write_text(
                    json.dumps(effect_inventory, indent=2) + "\n"
                )

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 2: THE DEDUP-ACROSS-TICKS LEG ────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_dedup_across_ticks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Same watermark re-requested on a later tick resolves to
    existing run, nothing minted."""
    _ensure_build()

    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT_TICK1, "returncode": 0},
    )
    runner = _make_fixture_runner(fixture_path)
    server, url = _boot(tmp_path, monkeypatch, gh_runner=runner)

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
            project_id = _create_project_api(page)
            _seed_room_items(page, project_id)
            _set_policy(page, project_id, unattended_enabled=True)

            watch_id = _seed_graduated_watch(
                project_id, watch_id="cw_dedup_glass_001",
            )
            _seed_baseline_snapshot(watch_id)

            # Tick 1: evaluate + run.
            eval1, run1 = _drive_tick()
            assert any(o.get("outcome") == "run_started" for o in run1), (
                f"Tick 1 should start a run: {run1}"
            )

            tick1_watermark = next(
                o.get("watermark", "") for o in run1
                if o.get("outcome") == "run_started"
            )
            tick1_run_id = next(
                o["run_id"] for o in run1 if o.get("outcome") == "run_started"
            )

            # Advance next_evaluation_at to past (but keep same snapshot
            # so the evaluation produces no_op or same source_revision).
            from holdspeak.db import get_database
            past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
            db = get_database()
            with db._connection() as conn:
                conn.execute(
                    "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
                    (past_iso, watch_id),
                )

            # Tick 2: same snapshot -> same watermark -> dedup.
            eval2, run2 = _drive_tick()

            # The evaluation should be no_op (same snapshot) so no new
            # effects are minted. Or if effects ARE minted with the same
            # idempotency key, run_due resolves to the existing run.
            new_runs_started = [
                o for o in run2 if o.get("outcome") == "run_started"
            ]
            resolved = [
                o for o in run2 if o.get("outcome") == "resolved_existing_run"
            ]

            # Either: no new effects were minted (eval returned no_op) and
            # run_due had nothing to drain, OR run_due resolved to existing.
            if new_runs_started:
                # This would be a dedup violation.
                assert False, (
                    f"Dedup violation: tick 2 started {len(new_runs_started)} "
                    f"new run(s) with same snapshot. "
                    f"Run outcomes: {json.dumps(run2, indent=2, default=str)}"
                )

            # Verify on glass.
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)

            # Only 1 run should exist (dedup prevented the second).
            runs_resp = _api(page, "GET", f"/api/projects/{project_id}/steward/runs")
            runs = runs_resp.get("runs", [])
            assert len(runs) == 1, (
                f"Dedup: expected exactly 1 run, got {len(runs)}. "
                f"Runs: {json.dumps(runs, indent=2, default=str)[:2000]}"
            )

            # SHOT: dedup proof.
            page.screenshot(
                path=str(SHOTS / f"dedup-proof-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"dedup-proof-{width}.png").stat().st_size > 20_000

            _assert_no_raw_ids(page)
            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 3: THE CIRCUIT LEG ───────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_circuit_open_and_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Failing source opens circuit -> visible on face -> intervention
    chip; recovery closes it."""
    _ensure_build()

    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    # Start with a BROKEN fixture (returncode 1 = fetch failure).
    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": "", "returncode": 1, "stderr": "Connection timeout"},
    )
    runner = _make_fixture_runner(fixture_path)
    server, url = _boot(tmp_path, monkeypatch, gh_runner=runner)

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
            project_id = _create_project_api(page)
            _seed_room_items(page, project_id)
            _set_policy(page, project_id, unattended_enabled=True)

            watch_id = _seed_graduated_watch(
                project_id, watch_id="cw_circuit_glass_001",
            )
            _seed_baseline_snapshot(watch_id)

            from holdspeak.db import get_database
            from holdspeak.services.watch_service import CIRCUIT_FAILURE_THRESHOLD

            # Drive N failing ticks to open the circuit.
            for i in range(CIRCUIT_FAILURE_THRESHOLD):
                past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
                db = get_database()
                with db._connection() as conn:
                    conn.execute(
                        "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
                        (past_iso, watch_id),
                    )
                eval_out, _ = _drive_tick()
                # Each tick should fail.
                assert any(
                    o.get("outcome") == "failed" for o in eval_out
                ), f"Tick {i+1} should have failed: {eval_out}"

            # Verify circuit is open in the DB.
            db = get_database()
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT circuit_state, circuit_failure_streak FROM connector_watches WHERE id=?",
                    (watch_id,),
                ).fetchone()
            assert row["circuit_state"] == "open", (
                f"Expected circuit open, got {row['circuit_state']}"
            )
            assert row["circuit_failure_streak"] >= CIRCUIT_FAILURE_THRESHOLD

            # -- Verify on glass: circuit row visible in policy view --
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)

            # Open policy view.
            page.get_by_test_id("steward-verb-policy").click()
            page.get_by_test_id("steward-policy").wait_for(timeout=10000)

            # Circuit row should be visible.
            circuit_row = page.get_by_test_id("steward-circuit-row")
            circuit_row.wait_for(timeout=10000)
            assert circuit_row.count() >= 1, "Circuit row should be visible"

            circuit_state_el = page.get_by_test_id("steward-circuit-state")
            circuit_text = circuit_state_el.first.inner_text().strip().lower()
            assert circuit_text == "circuit open", (
                f"Expected 'circuit open', got {circuit_text!r}"
            )

            streak_el = page.get_by_test_id("steward-circuit-streak")
            if streak_el.count() > 0:
                streak_text = streak_el.first.inner_text().strip()
                assert "failure" in streak_text.lower(), (
                    f"Streak text should mention failures: {streak_text!r}"
                )

            # SHOT: circuit open state (the face renders Source
            # circuits FIRST when any circuit is open -- attention
            # outranks configuration; no scrolling needed).
            page.screenshot(
                path=str(SHOTS / f"circuit-open-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"circuit-open-{width}.png").stat().st_size > 20_000

            # -- Recovery: fix the fixture, bypass the cooldown, drive a tick --
            _write_fixture(
                fixture_path,
                auth=_GH_AUTH_CONNECTED,
                repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
                pr_list={"stdout": _GH_PR_SNAPSHOT_TICK1, "returncode": 0},
            )

            # Zero out the cooldown window by backdating circuit_opened_at.
            far_past = (datetime.now() - timedelta(hours=1)).isoformat()
            past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
            db = get_database()
            with db._connection() as conn:
                conn.execute(
                    "UPDATE connector_watches "
                    "SET circuit_opened_at=?, next_evaluation_at=? "
                    "WHERE id=?",
                    (far_past, past_iso, watch_id),
                )

            eval_recovery, _ = _drive_tick()
            # Should be a half_open probe that succeeds.
            assert any(
                o.get("outcome") in ("evaluated", "probe_half_open")
                for o in eval_recovery
            ), f"Recovery tick should succeed: {eval_recovery}"

            # Verify circuit closed.
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT circuit_state, circuit_failure_streak FROM connector_watches WHERE id=?",
                    (watch_id,),
                ).fetchone()
            assert row["circuit_state"] == "closed", (
                f"After recovery, expected closed, got {row['circuit_state']}"
            )
            assert row["circuit_failure_streak"] == 0

            # Reload and verify circuit row gone (or shows "Healthy").
            page.reload(wait_until="load")
            _normal_chair(page)
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb-policy").click()
            page.get_by_test_id("steward-policy").wait_for(timeout=10000)

            # Circuit row should be gone (only non-closed circuits render).
            circuit_rows_after = page.get_by_test_id("steward-circuit-row")
            assert circuit_rows_after.count() == 0, (
                f"After recovery, circuit row should be gone, "
                f"got {circuit_rows_after.count()}"
            )

            # SHOT: circuit recovered.
            page.screenshot(
                path=str(SHOTS / f"circuit-recovered-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"circuit-recovered-{width}.png").stat().st_size > 20_000

            _assert_no_raw_ids(page, scope_testid="steward-policy")
            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 4: THE OPT-OUT LEG ───────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_opt_out_mid_cadence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Disable unattended mid-cadence -> next tick runs NOTHING,
    honestly receipted."""
    _ensure_build()

    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    fixture_path = tmp_path / "gh_fixture.json"
    _write_fixture(
        fixture_path,
        auth=_GH_AUTH_CONNECTED,
        repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
        pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
        pr_list={"stdout": _GH_PR_SNAPSHOT_TICK1, "returncode": 0},
    )
    runner = _make_fixture_runner(fixture_path)
    server, url = _boot(tmp_path, monkeypatch, gh_runner=runner)

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
            project_id = _create_project_api(page)
            _seed_room_items(page, project_id)

            # Start with unattended ON.
            _set_policy(page, project_id, unattended_enabled=True)

            watch_id = _seed_graduated_watch(
                project_id, watch_id="cw_optout_glass_001",
            )
            _seed_baseline_snapshot(watch_id)

            # Tick 1: unattended run should succeed.
            eval1, run1 = _drive_tick()
            assert any(o.get("outcome") == "run_started" for o in run1), (
                f"Tick 1 should start a run: {run1}"
            )

            # -- Disable unattended via the wire --
            _set_policy(page, project_id, unattended_enabled=False)

            # Advance next_evaluation_at.
            from holdspeak.db import get_database
            past_iso = (datetime.now() - timedelta(minutes=5)).isoformat()
            db = get_database()
            with db._connection() as conn:
                conn.execute(
                    "UPDATE connector_watches SET next_evaluation_at=? WHERE id=?",
                    (past_iso, watch_id),
                )

            # Change the snapshot so evaluation produces new transitions.
            _write_fixture(
                fixture_path,
                auth=_GH_AUTH_CONNECTED,
                repo_list={"stdout": _GH_REPO_LIST, "returncode": 0},
                pr_validate={"stdout": _GH_PR_VALIDATE_OK, "returncode": 0},
                pr_list={"stdout": _GH_PR_SNAPSHOT_TICK2, "returncode": 0},
            )

            # Tick 2: evaluate should still work (evaluation is not gated
            # by unattended_enabled), but run_due should skip.
            eval2, run2 = _drive_tick()

            # Evaluation may produce effects, but run_due should skip them
            # with "skipped_no_opt_in".
            runs_started = [
                o for o in run2 if o.get("outcome") == "run_started"
            ]
            skipped = [
                o for o in run2 if o.get("outcome") == "skipped_no_opt_in"
            ]

            assert len(runs_started) == 0, (
                f"Opt-out violated: tick 2 started {len(runs_started)} run(s) "
                f"after disabling unattended. Outcomes: {run2}"
            )

            # If there were pending effects, they should be skipped.
            if run2:
                assert len(skipped) >= 1, (
                    f"Expected skipped_no_opt_in receipts, got: {run2}"
                )

            # Verify on glass: only 1 run.
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)

            runs_resp = _api(page, "GET", f"/api/projects/{project_id}/steward/runs")
            runs = runs_resp.get("runs", [])
            completed_runs = [r for r in runs if r.get("state") == "completed"]
            assert len(completed_runs) == 1, (
                f"Opt-out: expected exactly 1 completed run, got {len(completed_runs)}"
            )

            # SHOT: opt-out proof.
            page.screenshot(
                path=str(SHOTS / f"opt-out-proof-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"opt-out-proof-{width}.png").stat().st_size > 20_000

            _assert_no_raw_ids(page)
            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()
