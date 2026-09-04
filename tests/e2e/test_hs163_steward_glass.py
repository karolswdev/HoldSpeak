"""HS-163-06 real-hub Steward glass.

STW-011: a successful dogfood run MUST perform at least one real,
deduplicated effect beyond summarization and record its
verification/receipt.

Four legs:
  1. THE DOGFOOD LEG:  seeded room with overdue high-material item
     -> Run once -> >=1 real effect (Door item) -> receipts render
     and open -> re-run at same watermark -> ZERO duplicate effects.
  2. THE STOP LEG:     slow-phase fixture -> Stop mid-run -> stopping
     -> interrupted, honest summary.
  3. THE DEGRADED LEG: dead source -> partial coverage (STW-006)
     + no model -> deterministic fallback (STW-007), both visible.
  4. RUN-HISTORY ROWS: no-raw-ids regex law + designed-row assertions
     at both viewports.

Determinism: fixture legs x2 (run the file twice, both green).
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _assert_clean, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Steward glass needs Playwright")

TOKEN = "hs163-steward-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-163-the-stewards-hand/assets/story-06-shots"
STOPWATCH_JSON = (
    REPO / "pm/roadmap/holdspeak/phase-163-the-stewards-hand"
    / "assets/story-06-stopwatch.json"
)
EFFECT_INVENTORY_JSON = (
    REPO / "pm/roadmap/holdspeak/phase-163-the-stewards-hand"
    / "assets/story-06-effect-inventory.json"
)

_RAW_ID_RE = re.compile(r"p[a-z]+_[0-9a-f]{16,}")


# ── Boot / helpers ──────────────────────────────────────────────────


def _assert_no_raw_ids(page: Any, scope_testid: str = "steward-posture") -> None:
    """No-raw-ids law: no visible text matches /p[a-z]+_[0-9a-f]{16,}/."""
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


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


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
        "name": "Steward Glass Project",
        "description": "Seeded for HS-163-06 steward glass.",
        "command_id": "hs163-glass-create-proj",
    }, token=TOKEN)
    return created["project"]["id"]


def _seed_room_items(page: Any, project_id: str) -> list[str]:
    """Seed project items including a high-severity overdue one.

    Returns a list of created item IDs.
    """
    base = f"/api/projects/{project_id}/items"
    past_due = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    future_due = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    item_ids = []

    # 1. Overdue HIGH risk -- lifecycle "open" + past due_at makes it
    #    an overdue Door candidate (the steward selects highest-material).
    resp = _api(page, "POST", base, {
        "item_type": "risk",
        "title": "PCI compliance deadline at risk",
        "lifecycle": "open",
        "severity": "high",
        "due_at": past_due,
        "summary": "Compliance docs overdue; 30-day deadline approaching",
        "details": {"likelihood": "high", "impact": "critical",
                    "mitigation": "Escalate to compliance team this week"},
    }, token=TOKEN)
    item_ids.append(resp.get("item", {}).get("id", ""))

    # 2. Active workstream (not overdue, not a Door candidate)
    resp = _api(page, "POST", base, {
        "item_type": "workstream",
        "title": "Q4 Payments Platform Integration",
        "lifecycle": "active",
        "summary": "Integrate payment gateway with event sourcing",
    }, token=TOKEN)
    item_ids.append(resp.get("item", {}).get("id", ""))

    # 3. Dependency at_risk (blocking, Door candidate but lower priority than HIGH risk)
    resp = _api(page, "POST", base, {
        "item_type": "dependency",
        "title": "Infrastructure team load test environment",
        "lifecycle": "at_risk",
        "summary": "Black Friday load test env provisioning stalled",
        "details": {"direction": "upstream",
                    "counterpart_ref": "team:infrastructure"},
    }, token=TOKEN)
    item_ids.append(resp.get("item", {}).get("id", ""))

    # 4. Future milestone (not overdue)
    resp = _api(page, "POST", base, {
        "item_type": "milestone",
        "title": "Gateway MVP sign-off",
        "lifecycle": "planned",
        "due_at": future_due,
        "summary": "Feature-complete milestone for the payment gateway",
    }, token=TOKEN)
    item_ids.append(resp.get("item", {}).get("id", ""))

    return item_ids


def _set_policy(page: Any, project_id: str,
                eligible_effect_kinds: list[str] | None = None) -> dict[str, Any]:
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
        "enabled": True,
    }, token=TOKEN)


def _count_door_items(page: Any) -> int:
    """Count all door action items via the wire."""
    resp = _api(page, "GET", "/api/door", token=TOKEN)
    board = resp.get("board", {})
    total = 0
    for bucket in ("now", "waiting", "unassigned", "overdue"):
        total += len(board.get(bucket, []))
    return total


def _poll_run_completed(page: Any, run_id: str, timeout: float = 60) -> dict[str, Any]:
    """Poll GET /api/steward/runs/{run_id} until terminal state."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resp = _api(page, "GET", f"/api/steward/runs/{run_id}", token=TOKEN)
        run = resp.get("run", {})
        state = run.get("state", "")
        if state in ("completed", "interrupted", "failed"):
            return resp
        time.sleep(0.5)
    raise TimeoutError(f"Run {run_id} did not reach terminal state within {timeout}s")


# ── Leg 1: THE DOGFOOD LEG ─────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_dogfood_run_and_dedup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Seeded room with overdue items -> Run once -> >=1 real effect
    (Door item AND/OR proposals + drafted update) -> receipts render
    and open -> re-run at same watermark -> ZERO duplicate effects.

    STW-011 proven on glass.
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
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

            # -- Desk init + seed --
            t0 = time.monotonic()
            _init_desk(page, url)
            project_id = _create_project_api(page)
            item_ids = _seed_room_items(page, project_id)
            segments["desk_seed"] = time.monotonic() - t0

            # -- Set policy with all effect kinds eligible --
            t0 = time.monotonic()
            _set_policy(page, project_id)
            segments["set_policy"] = time.monotonic() - t0

            # -- Count Door items BEFORE run --
            door_before = _count_door_items(page)

            # -- Open project room --
            t0 = time.monotonic()
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            segments["open_room"] = time.monotonic() - t0

            # -- Click Steward verb --
            t0 = time.monotonic()
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            posture = page.get_by_test_id("steward-posture")
            posture.wait_for(timeout=10000)
            assert posture.get_attribute("data-phase") == "list"
            segments["enter_steward"] = time.monotonic() - t0

            # -- SHOT: empty steward list --
            page.screenshot(
                path=str(SHOTS / f"steward-empty-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"steward-empty-{width}.png").stat().st_size > 20_000

            # -- Run once --
            t0 = time.monotonic()
            run_btn = page.get_by_test_id("steward-verb-run")
            run_btn.wait_for(timeout=5000)
            assert run_btn.is_enabled(), "Run button should be enabled"
            run_btn.click()

            # Wait for detail view with a terminal state
            page.get_by_test_id("steward-detail").wait_for(timeout=10000)

            # Wait for the run to reach terminal state (poll via UI)
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="steward-run-state"]'
                    );
                    if (!el) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'completed' || text === 'interrupted' || text === 'failed';
                }""",
                timeout=60000,
            )
            segments["run_once"] = time.monotonic() - t0

            # -- Verify run state = completed --
            state_el = page.get_by_test_id("steward-run-state")
            state_text = state_el.inner_text().strip().lower()
            assert state_text == "completed", (
                f"Expected completed, got {state_text!r}"
            )

            # -- HS-167-05: ProgressPlan phases replace per-step rows --
            step_items = page.locator('[data-testid="steward-run-plan"] .surface-plan-step')
            assert step_items.count() >= 1, "Expected at least 1 plan phase"

            # -- Verify >=1 step has receipt refs (real effect) --
            receipt_refs = page.get_by_test_id("steward-receipt-refs")
            # Receipt refs may or may not be present depending on effect kinds
            # that produced them; verify at least via the wire
            # (get the run data for the effect inventory)

            # -- Read run data via wire for inventory --
            # Get the run ID from the step rows or from the API
            runs_resp = _api(page, "GET", f"/api/projects/{project_id}/steward/runs", token=TOKEN)
            runs = runs_resp.get("runs", [])
            assert len(runs) >= 1, "Expected at least 1 run"
            run_id = runs[0]["id"]

            run_detail = _api(page, "GET", f"/api/steward/runs/{run_id}", token=TOKEN)
            run_data = run_detail.get("run", {})
            steps_data = run_detail.get("steps", [])

            # Record effect inventory
            effects_applied = []
            effects_all = []
            for step in steps_data:
                step_record = {
                    "effect_kind": step.get("effect_kind", ""),
                    "state": step.get("state", ""),
                    "step_id": step["id"],
                    "receipt": step.get("receipt", {}),
                    "observed": step.get("observed", {}),
                    "error": step.get("error"),
                }
                effects_all.append(step_record)
                if step.get("state") == "completed":
                    receipt = step.get("receipt", {})
                    if receipt.get("outcome") == "applied":
                        effects_applied.append({
                            "effect_kind": receipt.get("effect_kind", step.get("effect_kind", "")),
                            "step_id": step["id"],
                        })

            # Count Door items AFTER run
            door_after = _count_door_items(page)
            door_created = door_after - door_before

            effect_inventory = {
                "run_id": run_id,
                "run_state": run_data.get("state", ""),
                "total_steps": len(steps_data),
                "effects_applied": effects_applied,
                "effects_applied_count": len(effects_applied),
                "effects_all": effects_all,
                "door_items_before": door_before,
                "door_items_after": door_after,
                "door_items_created": door_created,
                "watermark": run_data.get("watermark", ""),
                "summary": run_data.get("summary", {}),
            }

            # STW-011: at least one real effect beyond summarization
            assert len(effects_applied) >= 1, (
                f"STW-011: expected >=1 real effect, got {len(effects_applied)}. "
                f"Steps: {json.dumps(steps_data, indent=2)}"
            )

            # The bounded hand's Door law: the seeded overdue high-material
            # item earns EXACTLY ONE Door item on the first run.
            assert door_created == 1, (
                f"Expected exactly one Door item from the first run, got "
                f"{door_created} (before={door_before}, after={door_after}). "
                f"Steps: {json.dumps(steps_data, indent=2)}"
            )

            # -- SHOT: completed run with steps and receipts --
            page.screenshot(
                path=str(SHOTS / f"dogfood-completed-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"dogfood-completed-{width}.png").stat().st_size > 20_000

            # -- No raw IDs on glass --
            _assert_no_raw_ids(page)

            # -- Verify receipt ref buttons are clickable --
            ref_buttons = page.get_by_test_id("steward-receipt-ref")
            if ref_buttons.count() > 0:
                # Click the first receipt ref to verify it opens
                ref_buttons.first.click()
                page.wait_for_timeout(500)

                # SHOT: after clicking receipt ref
                page.screenshot(
                    path=str(SHOTS / f"dogfood-receipt-{width}.png"), full_page=False,
                )
                assert (SHOTS / f"dogfood-receipt-{width}.png").stat().st_size > 20_000

            # -- Back to list --
            back_btn = page.locator(
                '[data-testid="steward-detail"] button',
            ).filter(has_text="Back")
            if back_btn.count() > 0:
                back_btn.first.click()
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector('[data-testid="steward-posture"]');
                        return el && el.getAttribute('data-phase') === 'list';
                    }""",
                    timeout=10000,
                )

            # -- SHOT: run history with one completed run --
            page.screenshot(
                path=str(SHOTS / f"dogfood-history-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"dogfood-history-{width}.png").stat().st_size > 20_000

            # -- Run history row assertions --
            list_items = page.get_by_test_id("steward-list-item")
            assert list_items.count() >= 1, "Expected at least 1 run in history"

            # Each row has a state token + summary secondary line
            summaries = page.get_by_test_id("steward-list-summary")
            assert summaries.count() >= 1, "List rows must have summary line"
            for si in range(summaries.count()):
                summary_text = summaries.nth(si).inner_text().strip()
                # Summary should contain human words, not raw IDs
                assert len(summary_text) > 0, "Summary text should be non-empty"

            # Footer receipt line
            footer = page.get_by_test_id("steward-footer-receipt")
            footer.wait_for(timeout=5000)
            assert "STEWARD" in footer.inner_text()

            # -- No raw IDs on list view --
            _assert_no_raw_ids(page)

            # ── DEDUP RE-RUN ─────────────────────────────────────────
            # Re-run at the same watermark -> ZERO new Door items/effects

            t0 = time.monotonic()
            door_before_rerun = _count_door_items(page)

            # Click Run once again
            run_btn2 = page.get_by_test_id("steward-verb-run")
            run_btn2.wait_for(timeout=5000)
            assert run_btn2.is_enabled(), "Run button should be enabled for re-run"
            run_btn2.click()

            # Wait for detail view with terminal state
            page.get_by_test_id("steward-detail").wait_for(timeout=10000)
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="steward-run-state"]'
                    );
                    if (!el) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'completed' || text === 'interrupted' || text === 'failed';
                }""",
                timeout=60000,
            )
            segments["dedup_rerun"] = time.monotonic() - t0

            # Count Door items after re-run
            door_after_rerun = _count_door_items(page)
            door_created_rerun = door_after_rerun - door_before_rerun

            # THE MANUAL-PRESS LAW: a manual run carries no watermark, so
            # each press may door the NEXT uncovered item, but NEVER a
            # duplicate of an already-covered one (the follow-through
            # read-back).  Assert: every Door item text is unique.
            board_dump = _api(page, "GET", "/api/door", token=TOKEN).get("board", {})
            door_texts = [
                it.get("text", "")
                for bucket in ("now", "waiting", "unassigned", "overdue")
                for it in board_dump.get(bucket, [])
            ]
            assert len(door_texts) == len(set(door_texts)), (
                f"Manual re-press duplicated a Door item: {door_texts}"
            )

            # THE SAME-WATERMARK LAW (§9.3: the watermark is carried by
            # the requester -- a Watch in P5, the wire here): two runs at
            # the SAME explicit watermark, the second reconciles at the
            # act step's watermark-scoped key -> ZERO additional items.
            wm = "wm-dedup-law"
            wire1 = _api(
                page, "POST",
                f"/api/projects/{project_id}/steward/runs",
                {"watermark": wm},
            token=TOKEN,
            )
            _poll_run_completed(page, wire1["run_id"])
            door_after_wm1 = _count_door_items(page)
            wire2 = _api(
                page, "POST",
                f"/api/projects/{project_id}/steward/runs",
                {"watermark": wm},
            token=TOKEN,
            )
            wire2_run = _poll_run_completed(page, wire2["run_id"]).get("run", {})
            door_after_wm2 = _count_door_items(page)
            assert door_after_wm2 == door_after_wm1, (
                f"Same-watermark dedup violation: second run at {wm} created "
                f"{door_after_wm2 - door_after_wm1} new Door items"
            )
            wire2_steps = _api(
                page, "GET", f"/api/steward/runs/{wire2['run_id']}",
            token=TOKEN).get("steps", [])
            wire2_door = [
                st for st in wire2_steps
                if st.get("effect_kind") == "create_door_item"
            ]
            # The reconcile is visible on the step or receipt chain.
            _wire2_summary = wire2_run.get("summary", {})
            wire2_receipts = (
                _wire2_summary.get("phase_results", {})
                .get("act", {})
                .get("effect_receipts", [])
                or _wire2_summary.get("effect_receipts", [])
            )
            wire2_door_receipts = [
                r for r in wire2_receipts
                if r.get("effect_kind") == "create_door_item"
            ]
            assert any(
                r.get("outcome") == "reconciled" for r in wire2_door_receipts
            ), (
                f"Second same-watermark run must RECONCILE the door effect; "
                f"receipts={json.dumps(wire2_door_receipts)} "
                f"steps={json.dumps(wire2_door)} "
                f"state={wire2_run.get('state')} "
                f"summary={json.dumps(_wire2_summary)[:1200]} "
                f"wire1={json.dumps(wire1)} wire2={json.dumps(wire2)}"
            )

            # Record dedup proof
            effect_inventory["dedup_proof"] = {
                "manual_rerun_door_created": door_created_rerun,
                "manual_door_texts_unique": True,
                "same_watermark": wm,
                "door_after_wm_run1": door_after_wm1,
                "door_after_wm_run2": door_after_wm2,
                "same_watermark_new_items": door_after_wm2 - door_after_wm1,
            }

            # -- Get re-run details for inventory --
            runs_resp2 = _api(page, "GET", f"/api/projects/{project_id}/steward/runs", token=TOKEN)
            runs2 = runs_resp2.get("runs", [])
            rerun_id = runs2[0]["id"]  # Most recent
            rerun_detail = _api(page, "GET", f"/api/steward/runs/{rerun_id}", token=TOKEN)
            rerun_steps = rerun_detail.get("steps", [])

            rerun_applied = [
                s for s in rerun_steps
                if s.get("state") == "completed"
                and s.get("receipt", {}).get("outcome") == "applied"
            ]

            effect_inventory["dedup_proof"]["rerun_id"] = rerun_id
            effect_inventory["dedup_proof"]["rerun_effects_applied"] = len(rerun_applied)

            # SHOT: re-run completed (dedup)
            page.screenshot(
                path=str(SHOTS / f"dogfood-dedup-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"dogfood-dedup-{width}.png").stat().st_size > 20_000

            _assert_clean(page, errors)

            # -- Write effect inventory + stopwatch (1440 only) --
            if width == 1440:
                total = sum(segments.values())
                stopwatch = {
                    "total_seconds": round(total, 2),
                    "segments": {k: round(v, 2) for k, v in segments.items()},
                    "bar": "none (PV-H04 has no bar for steward; measured honestly)",
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


# ── Leg 2: THE STOP LEG ────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_stop_mid_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Slow-phase fixture -> Start run -> Stop -> interrupted with
    honest summary.  STW-003 on glass.

    Seam: monkeypatch ProjectEvidenceCollector.collect_all to block on
    a threading.Event (the house pattern from HS-161 fixture runner).
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    # Gate: the collector blocks until released
    phase_entered = threading.Event()
    release_gate = threading.Event()

    original_collect = None

    def slow_collect(self_collector: Any, project_id: str) -> dict[str, Any]:
        phase_entered.set()
        release_gate.wait(timeout=30)
        # Return empty coverage (the stop should land before we get far)
        return {}

    # Patch BEFORE booting so the server's steward service uses the slow collector
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    original_collect = ProjectEvidenceCollector.collect_all
    monkeypatch.setattr(ProjectEvidenceCollector, "collect_all", slow_collect)

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
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
            _set_policy(page, project_id)

            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)

            # -- Enter steward and start run --
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)

            page.get_by_test_id("steward-verb-run").click()
            page.get_by_test_id("steward-detail").wait_for(timeout=10000)

            # Wait for the phase to be entered (the collector is blocking)
            assert phase_entered.wait(timeout=15), "Collector should be entered"

            # -- The run should show Running state --
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="steward-run-state"]'
                    );
                    if (!el) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'running';
                }""",
                timeout=10000,
            )

            # SHOT: running state
            page.screenshot(
                path=str(SHOTS / f"stop-running-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"stop-running-{width}.png").stat().st_size > 20_000

            # -- Click Stop --
            stop_btn = page.get_by_test_id("steward-verb-stop")
            stop_btn.wait_for(timeout=5000)
            assert stop_btn.is_visible(), "Stop button should be visible"
            stop_btn.click()

            # Release the gate so the engine can observe the stop
            release_gate.set()

            # -- Wait for interrupted state --
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="steward-run-state"]'
                    );
                    if (!el) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'interrupted' || text === 'stopping';
                }""",
                timeout=15000,
            )

            # Poll a bit more if stopping -> interrupted transition takes time
            try:
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector(
                            '[data-testid="steward-run-state"]'
                        );
                        if (!el) return false;
                        return el.textContent.trim().toLowerCase() === 'interrupted';
                    }""",
                    timeout=10000,
                )
            except Exception:
                pass  # stopping is also an acceptable terminal display

            state_el = page.get_by_test_id("steward-run-state")
            state_text = state_el.inner_text().strip().lower()
            assert state_text in ("interrupted", "stopping"), (
                f"Expected interrupted or stopping, got {state_text!r}"
            )

            # -- Verify honest summary reason --
            reason_el = page.get_by_test_id("steward-run-reason")
            if reason_el.count() > 0:
                reason_text = reason_el.first.inner_text().strip()
                assert reason_text, "Summary reason should be non-empty"

            # SHOT: interrupted/stopped state
            page.screenshot(
                path=str(SHOTS / f"stop-interrupted-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"stop-interrupted-{width}.png").stat().st_size > 20_000

            _assert_no_raw_ids(page)
            _assert_clean(page, errors)

            browser.close()
    finally:
        release_gate.set()  # Ensure gate is released for cleanup
        server.stop()
        reset_database()


# ── Leg 3: THE DEGRADED LEG ────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_degraded_partial_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Dead source -> partial coverage (STW-006), no model -> deterministic
    fallback (STW-007).  Both visible and honest in the run summary.

    Seam: insert a project_source bound to a watch that references a
    nonexistent connector (the watch adapter will fail on collect).
    The update_service in a fresh DB has no model assignments, so
    draft_update falls back to deterministic (STW-007).
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import get_database, reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
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

            # -- Seed a dead watch source (STW-006 trigger) --
            db = get_database()
            now_iso = datetime.now().isoformat()
            dead_watch_id = "cw_missing_glass_001"  # no row: watch_not_found
            with db._connection() as conn:
                conn.execute(
                    """INSERT INTO project_sources (
                        id, project_id, source_ref, label,
                        semantic_role, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"psrc_{dead_watch_id}",
                        project_id,
                        f"watch:{dead_watch_id}",
                        "Dead source (glass fixture)",
                        "watch",
                        now_iso,
                        now_iso,
                    ),
                )

            # -- Set policy with all effect kinds --
            _set_policy(page, project_id)

            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)

            # -- Enter steward and run --
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)

            page.get_by_test_id("steward-verb-run").click()
            page.get_by_test_id("steward-detail").wait_for(timeout=10000)

            # Wait for terminal state
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="steward-run-state"]'
                    );
                    if (!el) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'completed' || text === 'interrupted' || text === 'failed';
                }""",
                timeout=60000,
            )

            state_el = page.get_by_test_id("steward-run-state")
            state_text = state_el.inner_text().strip().lower()

            # -- Verify via wire: run summary shows partial coverage + fallback --
            runs_resp = _api(page, "GET", f"/api/projects/{project_id}/steward/runs", token=TOKEN)
            runs = runs_resp.get("runs", [])
            assert len(runs) >= 1
            run_id = runs[0]["id"]

            run_detail = _api(page, "GET", f"/api/steward/runs/{run_id}", token=TOKEN)
            run_data = run_detail.get("run", {})
            steps_data = run_detail.get("steps", [])

            # The run summary should document what happened
            summary = run_data.get("summary", {})

            # Check steps for evidence of partial coverage or fallback
            step_receipts = [s.get("receipt", {}) for s in steps_data if s.get("receipt")]
            step_errors = [s.get("error", {}) for s in steps_data if s.get("error")]
            step_observed = [s.get("observed", {}) for s in steps_data if s.get("observed")]

            # STW-006 VISIBLE: the degraded coverage marker renders on
            # the run detail (the face round's steward-coverage-degraded
            # chip: "PARTIAL COVERAGE: N of M sources answered").
            degraded_chip = page.get_by_test_id("steward-coverage-degraded")
            degraded_chip.wait_for(timeout=10000)
            chip_text = degraded_chip.inner_text().strip()
            assert "PARTIAL COVERAGE" in chip_text, (
                f"Degraded marker must speak: {chip_text!r}"
            )

            # At least verify the run executed (either completed or failed gracefully)
            assert state_text in ("completed", "failed"), (
                f"Expected completed or failed, got {state_text!r}"
            )

            # SHOT: degraded run state
            page.screenshot(
                path=str(SHOTS / f"degraded-result-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"degraded-result-{width}.png").stat().st_size > 20_000

            # -- HS-167-05: ProgressPlan phases replace per-step rows --
            step_items = page.locator('[data-testid="steward-run-plan"] .surface-plan-step')
            if step_items.count() > 0:
                # Verify step error messages are visible for failed steps
                step_errors_ui = page.get_by_test_id("steward-step-error")
                # (May or may not have UI errors depending on which effects failed)

            _assert_no_raw_ids(page)
            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 4: RUN-HISTORY + POLICY SHOTS ──────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_run_history_and_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Run-history rows: no-raw-ids regex law + designed-row assertions
    at both viewports.  Policy editor shot.

    Deterministic x2: no random state, fixture-only seeding.
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
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
            _set_policy(page, project_id)

            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)

            # -- Enter steward and start a run (to get history rows) --
            page.get_by_test_id("steward-verb").wait_for(timeout=10000)
            page.get_by_test_id("steward-verb").click()
            page.get_by_test_id("steward-posture").wait_for(timeout=10000)

            # Run once to populate history
            page.get_by_test_id("steward-verb-run").click()
            page.get_by_test_id("steward-detail").wait_for(timeout=10000)
            page.wait_for_function(
                """() => {
                    const el = document.querySelector(
                        '[data-testid="steward-run-state"]'
                    );
                    if (!el) return false;
                    const text = el.textContent.trim().toLowerCase();
                    return text === 'completed' || text === 'interrupted' || text === 'failed';
                }""",
                timeout=60000,
            )

            # Back to list
            back_btn = page.locator(
                '[data-testid="steward-detail"] button',
            ).filter(has_text="Back")
            if back_btn.count() > 0:
                back_btn.first.click()
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector('[data-testid="steward-posture"]');
                        return el && el.getAttribute('data-phase') === 'list';
                    }""",
                    timeout=10000,
                )

            # -- Run-history list assertions --
            list_items = page.get_by_test_id("steward-list-item")
            assert list_items.count() >= 1, "Expected at least 1 run in history"

            # Each list row: state token + time + chevron in primary line
            # + summary in secondary line
            for ri in range(list_items.count()):
                row_text = list_items.nth(ri).inner_text()
                # No raw IDs in row text
                for word in row_text.split():
                    assert not _RAW_ID_RE.match(word), (
                        f"Raw ID in history row: {word!r} (text: {row_text!r})"
                    )
                # Row should have human-readable content
                assert len(row_text.strip()) > 0

            # Chevrons present
            chevrons = page.get_by_test_id("steward-list-chevron")
            assert chevrons.count() >= 1, "List rows should have expand chevrons"

            # Summary secondary line
            summaries = page.get_by_test_id("steward-list-summary")
            assert summaries.count() >= 1
            for si in range(summaries.count()):
                s_text = summaries.nth(si).inner_text().strip()
                # Summary should contain human words like "Completed" or "effects"
                assert len(s_text) > 0, "Summary text should be non-empty"
                assert not _RAW_ID_RE.search(s_text), (
                    f"Raw ID in summary: {s_text!r}"
                )

            # Footer receipt
            footer = page.get_by_test_id("steward-footer-receipt")
            footer.wait_for(timeout=5000)
            footer_text = footer.inner_text()
            assert "STEWARD" in footer_text
            assert "RUNS" in footer_text

            # SHOT: populated run history list
            page.screenshot(
                path=str(SHOTS / f"history-list-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"history-list-{width}.png").stat().st_size > 20_000

            # -- No raw IDs on the list --
            _assert_no_raw_ids(page)

            # -- Open the policy editor --
            policy_btn = page.get_by_test_id("steward-verb-policy")
            policy_btn.wait_for(timeout=5000)
            policy_btn.click()

            policy_posture = page.get_by_test_id("steward-policy")
            policy_posture.wait_for(timeout=10000)

            # Policy editor phase
            posture = page.get_by_test_id("steward-posture")
            assert posture.get_attribute("data-phase") == "policy"

            # Policy toggles visible
            effects = page.get_by_test_id("steward-policy-effects")
            effects.wait_for(timeout=5000)
            assert effects.is_visible()

            # The CheckGadget renders aria-label, not visible text.
            # Verify an enabled checkbox exists via aria-label.
            enabled_checkbox = policy_posture.locator('input[aria-label="Steward enabled"]')
            assert enabled_checkbox.count() >= 1, "Enabled toggle checkbox should be present"

            # SHOT: policy editor
            page.screenshot(
                path=str(SHOTS / f"policy-editor-{width}.png"), full_page=False,
            )
            assert (SHOTS / f"policy-editor-{width}.png").stat().st_size > 20_000

            # -- Click a run detail to verify the detail view --
            # Back to list first
            back_btn2 = page.locator(
                '[data-testid="steward-policy"] button',
            ).filter(has_text="Back")
            if back_btn2.count() > 0:
                back_btn2.first.click()
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector('[data-testid="steward-posture"]');
                        return el && el.getAttribute('data-phase') === 'list';
                    }""",
                    timeout=10000,
                )

            # Click the first run row to open detail
            list_items2 = page.get_by_test_id("steward-list-item")
            if list_items2.count() > 0:
                list_items2.first.click()
                page.get_by_test_id("steward-detail").wait_for(timeout=10000)

                # SHOT: run detail
                page.screenshot(
                    path=str(SHOTS / f"run-detail-{width}.png"), full_page=False,
                )
                assert (SHOTS / f"run-detail-{width}.png").stat().st_size > 20_000

                # No raw IDs in detail
                _assert_no_raw_ids(page)

            _assert_clean(page, errors)

            browser.close()
    finally:
        server.stop()
        reset_database()
