"""HS-200-12 real-hub glass: a real meeting to reviewed outcomes.

One booted hub on an isolated HOME (``glass_infra._boot``), its own
lifespan-started intel drainer (HS-200-42), the REAL import route, the REAL
``Run intelligence`` trigger, the REAL plugin host running the REAL
``decision_capture`` and ``action_owner_enforcer`` plugins, and the REAL
proposal bridge.  The ONLY fake is the provider engine's completion text
(``ScriptedIntel``): the JSON a model returns for each extractor.

The summary path and the parked proposal path are exercised separately, both
at 1440 and 393:

  1. SUMMARY.  A transcript is imported, run with the disclosed selection
     hash, and reaches a real drainer-backed summary-ready state.
  2. REVIEW.  After the summary precondition, the old proposal assertions stay
     live.  A transcript linked to a Room should produce five proposals.  The
     Review wing shows them on three axes with their spans and typed unknowns.
     One is edited in place and one is confirmed.
  3. PROCESSING.  After the same summary precondition, a second meeting's first
     attempt loses the action extractor, so the job is retried.  The two
     decisions attempt 1 produced are on the face NOW; the owner keeps both;
     the face reads `ATTEMPT 2 · SAME JOB` with `ALREADY KEPT 2`.  Attempt 2
     then succeeds and mints nothing twice.

The proposal scenarios carry a strict xfail only after the live summary
precondition.  The ratified HS-201 analysis-only amendment deliberately parks
the old plugin-to-proposal pipeline; a future return makes these XPASS loudly.

Shots to: pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-12-shots/
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    REPO,
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Meeting outcomes glass needs Playwright")

TOKEN = "hs200-outcomes-glass"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-12-shots"

DEC = "decision_capture"
ACT = "action_owner_enforcer"

# Sep 7, 11:00 local: the board's meeting.  Turns at the board's minutes.
STARTED = datetime(2026, 9, 7, 11, 0, 0)
TRANSCRIPT_SRT = """1
00:00:00,000 --> 00:02:00,000
Karol: Let's start with the cut-over sequencing for the payments platform.

2
00:18:00,000 --> 00:21:00,000
Priya: Cut-over runs on the read replica first, then we flip writes.

3
00:31:00,000 --> 00:33:00,000
Marek: I think the freeze window should move to Sunday two in the morning.

4
00:33:00,000 --> 00:35:00,000
Priya: I'll confirm the freeze window with the payments team.

5
00:40:00,000 --> 00:42:00,000
Marek: Someone needs to write the rollback runbook before we go.

6
00:44:00,000 --> 00:46:00,000
Karol: We should also check the numbers again before Friday.
"""

DECISIONS_JSON = json.dumps({
    "decisions": [
        {"decision": "Cut-over runs on the read replica first", "rationale": None,
         "source_timestamp": 1100.0},
        {"decision": "Freeze window moves to Sunday 02:00", "rationale": "less traffic",
         "source_timestamp": 1900.0},
    ],
    "open_questions": [],
})
ACTIONS_JSON = json.dumps({
    "action_items": [
        {"task": "Confirm the freeze window with the payments team", "owner": None, "due": None},
        {"task": "Draft the rollback runbook", "owner": None, "due": None},
        {"task": "Book the war room for the cut-over night", "owner": "Karol", "due": "Friday"},
    ],
})


# ── the one fake ────────────────────────────────────────────────────


def _scripted_engine():
    from tests.unit.test_meeting_deferred_admission import FakeIntel

    class ScriptedIntel(FakeIntel):
        def __init__(self) -> None:
            super().__init__()
            self.fail_plugins: set[str] = set()
            self.plugin_calls: list[str] = []

        def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
            system = str(messages[0].get("content") or "") if messages else ""
            plugin = DEC if "decisions and open questions" in system else ACT
            self.plugin_calls.append(plugin)
            if plugin in self.fail_plugins:
                raise RuntimeError(f"{plugin}: provider exploded")
            return DECISIONS_JSON if plugin == DEC else ACTIONS_JSON

    return ScriptedIntel()


def _wire_provider(monkeypatch: pytest.MonkeyPatch, engine: Any) -> None:
    """The provider seam only: the hub's queue, executor, host, plugins,
    bridge and routes are the product's own."""
    from tests.unit.test_meeting_deferred_admission import (
        _Route,
        _assign_deferred_queue_routes,
    )
    from holdspeak.db import get_database

    _assign_deferred_queue_routes(get_database())
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route((DEC, ACT)),
    )


def _boot_with_fast_retry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Boot with a 2s retry backoff so the processing face's attempt 2 is
    reachable inside the rig's patience (the product default is 30s).

    The owner claim is taken here, as the hub command takes it at boot
    (``runtime/ownership.py``): the in-process glass server does not run
    that step, and the drainer is scheduled work that runs in the owner
    alone (HS-200-42) -- without the claim the lifespan starts no drainer.
    """
    from holdspeak.runtime_lock import claim_database, current_lock

    home = tmp_path / "home"
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    (home / ".holdspeak" / "config.json").write_text(
        json.dumps({"meeting": {"intel_retry_base_seconds": 2, "intel_retry_max_seconds": 4}}),
        encoding="utf-8",
    )
    assert current_lock() is None, "this process already owns a database"
    lock = claim_database(tmp_path / "holdspeak.db")
    assert lock.held, "the rig could not claim its own tmp database"
    return _boot(tmp_path, monkeypatch, token=TOKEN)


# ── browser helpers ─────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _import_transcript(page: Any, title: str) -> str:
    """The REAL import route, as the face uses it (multipart)."""
    result = page.evaluate(
        """async ([token, title, body, startedMs]) => {
          const form = new FormData();
          form.append("file", new Blob([body], {type: "text/plain"}), "architecture-review.srt");
          form.append("title", title);
          form.append("started_at_ms", String(startedMs));
          const response = await fetch("/api/meetings/import", {
            method: "POST",
            headers: {authorization: `Bearer ${token}`},
            body: form,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [TOKEN, title, TRANSCRIPT_SRT, int(STARTED.timestamp() * 1000)],
    )
    assert result["status"] == 202, result
    meeting_id = str(result["payload"]["meeting_id"])
    # The import parses in a worker thread; wait for the segments to land.
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        detail = _api(page, "GET", f"/api/meetings/{meeting_id}", token=TOKEN)
        if len(detail.get("segments") or []) == 6:
            return meeting_id
        time.sleep(0.2)
    raise AssertionError("the import never produced six segments")


def _create_project(page: Any, name: str, command_id: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for HS-200-12 meeting outcomes glass.",
        "command_id": command_id,
    }, token=TOKEN)
    return created["project"]["id"]


def _wait(predicate, *, timeout: float = 60.0, step: float = 0.25) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return predicate()


def _review(page: Any, meeting_id: str) -> dict[str, Any]:
    return _api(page, "GET", f"/api/meetings/{meeting_id}/outcome-review", token=TOKEN)


def _run_intelligence(page: Any, meeting_id: str) -> dict[str, Any]:
    """Post the hash the existing SERVICE route fixture discloses."""
    detail = _api(page, "GET", f"/api/meetings/{meeting_id}", token=TOKEN)
    planned = detail["planned_route"]
    assert planned["status"] == "ready" and planned["legs"], planned
    assert planned["selection_hash"], planned
    return _api(
        page,
        "POST",
        f"/api/meetings/{meeting_id}/intelligence/run",
        {"expected_selection_hash": planned["selection_hash"]},
        token=TOKEN,
    )


def _diagnose(meeting_id: str) -> dict[str, Any]:
    """Everything the hub knows about one meeting's read, for a failing
    assertion: the job lineage with its errors, the attempt ledger, the
    plugin runs.  A CI failure must name its mechanism, not its symptom."""
    from holdspeak.db import get_database

    db = get_database()
    with db._connection() as conn:
        jobs = [dict(r) for r in conn.execute(
            "SELECT job_id, origin_job_id, status, lifecycle_posture, attempts, last_error, "
            "requested_at, updated_at, transcript_hash FROM intel_jobs WHERE meeting_id = ? "
            "ORDER BY requested_at", (meeting_id,),
        )]
        attempts = [dict(r) for r in conn.execute(
            "SELECT job_id, event_kind, attempt, outcome, error, created_at FROM intel_job_attempts "
            "WHERE meeting_id = ? ORDER BY id", (meeting_id,),
        )]
        meeting = dict(conn.execute(
            "SELECT intel_status, intel_status_detail, "
            "(SELECT COUNT(*) FROM segments s WHERE s.meeting_id = m.id) AS segments "
            "FROM meetings m WHERE id = ?", (meeting_id,),
        ).fetchone() or {})
    runs = [
        (r.plugin_id, r.status, getattr(r, "error", None))
        for r in db.plugins.list_plugin_runs(meeting_id, limit=50)
    ]
    return {"meeting": meeting, "jobs": jobs, "attempts": attempts, "plugin_runs": runs}


def _open_review_wing(page: Any, url: str, meeting_id: str) -> None:
    page.evaluate(
        """([scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "review-meetings", scope})
          );
        }""",
        [f"meeting:{meeting_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=12_000)
    page.locator(".surface-split-detail .surface-display").first.wait_for(timeout=12_000)
    page.get_by_role("tab", name="Review").click()
    page.locator("[data-testid='meeting-review']").wait_for(timeout=12_000)
    _settle(page)


# Shots are evidence, written only on request (lane 15's convention): the
# suite must not rewrite tracked PNGs on every run (the 388-PNG scar).
WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS", "").strip() not in ("", "0", "false", "no")


def _shot(page: Any, name: str, width: int) -> None:
    _settle(page)
    if not WRITE_SHOTS:
        return
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"), full_page=True)


def _title_visible(page: Any, expected: str) -> None:
    """The subject is in the title bar and VISIBLE: the text matches and the
    box is at least 120px wide or nothing is clipped (counsel's 393 ruling)."""
    title = page.locator(".desk-surface-window").first.locator(".desk-window-title").first
    assert (title.text_content() or "").strip() == expected, title.text_content()
    box = title.evaluate(
        "el => ({w: el.getBoundingClientRect().width, sw: el.scrollWidth, cw: el.clientWidth})"
    )
    assert box["w"] >= 120 or box["sw"] <= box["cw"], box
    assert "Architecture" in (title.text_content() or "")
    # Every wing is reachable: inside the viewport, no horizontal scroll.
    wings = page.evaluate("""() => Array.from(document.querySelectorAll('.desk-surface-window .desk-wing'))
        .map(w => [w.textContent.trim(), Math.round(w.getBoundingClientRect().right)])""")
    assert wings and all(right <= page.viewport_size["width"] for _, right in wings), wings
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def _chip_labels(page: Any, test_id: str) -> list[str]:
    return [
        el.get_attribute("aria-label") or ""
        for el in page.query_selector_all(f"[data-testid='{test_id}'] .surface-state-chip")
    ]


def _no_raw_buttons(page: Any, width: int) -> None:
    raw = page.evaluate("""() => {
        const body = document.querySelector('[data-testid="meeting-review"]');
        if (!body) return ["no review face"];
        return Array.from(body.querySelectorAll('button'))
            .filter(b => !b.classList.contains('btn')
                      && !b.classList.contains('desk-mic')
                      && !b.classList.contains('surface-disclosure-trigger')
                      && !b.classList.contains('surface-edit-in-place')
                      && !b.classList.contains('surface-plan-action-btn'))
            .map(b => (b.textContent || '').trim().slice(0, 40));
    }""")
    assert raw == [], f"raw buttons at {width}: {raw}"


# ── the rig ─────────────────────────────────────────────────────────


SUMMARY_AMENDMENT_XFAIL = (
    "HS-201 ratified analysis-only summary amendment; parked proposal pipeline"
)


@pytest.fixture
def meeting_outcomes_rig(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
    height: int,
) -> Any:
    """Boot one real hub and prove its summary path before proposal tests run.

    The fixture intentionally owns the precondition for the two proposal
    scenarios.  A failure before ``yield`` is an ERROR, so a broken import,
    route disclosure, queue admission, drainer, or summary cannot be hidden by
    the strict xfail marker on the parked proposal assertions.
    """
    _ensure_build()
    server, url = _boot_with_fast_retry(tmp_path, monkeypatch)
    engine = _scripted_engine()
    from holdspeak import intel_queue_conductor as conductor
    from holdspeak.db import get_database
    from playwright.sync_api import sync_playwright

    _wire_provider(monkeypatch, engine)
    assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"

    errors: list[str] = []
    browser: Any = None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", f"hs200-12-proj-{width}")

            # The fixture's live precondition: import all six transcript
            # segments, post the exact disclosed selection hash, and let the
            # hub's real drainer publish the base summary.
            summary_meeting = _import_transcript(page, "Summary-ready meeting")
            _api(page, "POST", f"/api/projects/{project_id}/meetings/{summary_meeting}", token=TOKEN)
            before = _api(page, "GET", f"/api/meetings/{summary_meeting}", token=TOKEN)
            assert len(before["segments"]) == 6, before
            planned = before["planned_route"]
            assert planned["status"] == "ready" and planned["legs"], planned
            assert planned["selection_hash"], planned
            run = _run_intelligence(page, summary_meeting)
            assert run["state"] == "queued" and run["drainer"] == "running", run
            assert run["planned_route"]["selection_hash"] == planned["selection_hash"], run
            assert _wait(
                lambda: (
                    (detail := _api(page, "GET", f"/api/meetings/{summary_meeting}", token=TOKEN))
                    .get("intel_status", {}).get("state") == "ready"
                    and detail.get("intel")
                ),
                timeout=90.0,
            ), (_api(page, "GET", f"/api/meetings/{summary_meeting}", token=TOKEN), _diagnose(summary_meeting))
            summary_detail = _api(page, "GET", f"/api/meetings/{summary_meeting}", token=TOKEN)
            assert len(summary_detail["segments"]) == 6, summary_detail
            assert summary_detail["intel_status"]["state"] == "ready", summary_detail
            assert summary_detail["intel"]["summary"] == engine.result.summary
            summary_review = _review(page, summary_meeting)
            assert summary_review["job"]["status"] == "succeeded", summary_review
            assert summary_review["coverage"]["turns"] == 6
            assert summary_review["coverage"]["read"] == 6
            assert summary_review["coverage"]["state"] == "available"

            rig = {
                "page": page,
                "url": url,
                "engine": engine,
                "conductor": conductor,
                "db": get_database(),
                "project_id": project_id,
                "width": width,
                "summary_meeting": summary_meeting,
                "summary_run": run,
                "summary_detail": summary_detail,
                "errors": errors,
            }
            yield rig
            _assert_clean(page, errors)
            browser.close()
            browser = None
    finally:
        if browser is not None:
            browser.close()
        # ``server.stop()`` joins the hub thread for 10s; hold the thread until
        # it is really gone before releasing this fixture's database claim.
        from holdspeak.runtime_lock import release_database

        hub_thread = server._thread
        server.stop()
        if hub_thread is not None:
            hub_thread.join(120)
            assert not hub_thread.is_alive(), "the hub thread outlived its stop"
        conductor.stop_intel_queue_conductor()
        release_database()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.timeout(420)
@pytest.mark.parametrize("width,height", [(1440, 1200), (393, 900)])
def test_meeting_summary_ready(
    meeting_outcomes_rig: dict[str, Any],
    width: int,
) -> None:
    """The disclosed run produces a six-segment summary on both glasses."""
    detail = meeting_outcomes_rig["summary_detail"]
    run = meeting_outcomes_rig["summary_run"]
    assert len(detail["segments"]) == 6
    assert run["state"] == "queued" and run["drainer"] == "running"
    assert run["planned_route"]["selection_hash"]
    assert detail["intel_status"]["state"] == "ready"
    assert detail["intel"]["summary"]
    assert meeting_outcomes_rig["width"] == width


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.timeout(420)
@pytest.mark.parametrize("width,height", [(1440, 1200), (393, 900)])
def test_meeting_review_proposals_stay_live_under_amendment(
    meeting_outcomes_rig: dict[str, Any],
    request: pytest.FixtureRequest,
) -> None:
    """Keep the complete m1 Review assertions live behind a strict xfail."""
    page = meeting_outcomes_rig["page"]
    url = meeting_outcomes_rig["url"]
    engine = meeting_outcomes_rig["engine"]
    project_id = meeting_outcomes_rig["project_id"]
    db = meeting_outcomes_rig["db"]
    width = meeting_outcomes_rig["width"]

    # ── REVIEW: the real import, the real trigger, the drainer ──
    m1 = _import_transcript(page, "Architecture review")
    _api(page, "POST", f"/api/projects/{project_id}/meetings/{m1}", token=TOKEN)
    run = _run_intelligence(page, m1)
    assert run["state"] == "queued" and run["drainer"] == "running", run
    request.node.add_marker(pytest.mark.xfail(strict=True, reason=SUMMARY_AMENDMENT_XFAIL))
    assert _wait(lambda: len(_review(page, m1)["proposals"]) == 5, timeout=90.0), (
        _review(page, m1), engine.plugin_calls, _diagnose(m1),
    )
    review = _review(page, m1)
    assert review["job"]["status"] == "succeeded" and review["job"]["attempt"] == 1, review["job"]
    assert review["coverage"] == {
        "turns": 6, "read": 6, "state": "available",
        "observed_at": review["coverage"]["observed_at"],
    }
    kinds = sorted(p["kind"] for p in review["proposals"])
    assert kinds == ["action", "action", "action", "decision", "decision"], kinds
    assert all(p["job_id"] == review["job"]["job_id"] for p in review["proposals"])
    assert {p["support"] for p in review["proposals"]} == {"supported", "source_linked", "unknown"}

    _open_review_wing(page, url, m1)
    headline = page.locator("[data-testid='review-headline']")
    assert headline.text_content() == "5 to review", headline.text_content()
    assert page.locator("[data-testid='review-confirm']").count() == 5
    assert page.locator("[data-testid='review-more']").count() == 5
    assert page.get_by_role("button", name="Open the Project: Q4 platform").count() == 1
    coverage = page.locator("[data-testid='review-coverage']").text_content() or ""
    assert "6 OF 6 TURNS" in coverage and "AVAILABLE" in coverage, coverage
    supports = [(el.text_content() or "").strip() for el in page.query_selector_all("[data-testid='review-support']")]
    assert sorted(supports) == sorted(["✓SUPPORTED", "○LINKED", "✓SUPPORTED", "○LINKED", "⚠UNSUPPORTED"]), supports
    spans = [(el.text_content() or "") for el in page.query_selector_all("[data-testid='review-span']")]
    assert "MTG 09-07 · 11:18–11:21" in spans, spans
    assert page.locator("[data-testid='review-no-source']").count() == 1
    unknowns = [(el.text_content() or "") for el in page.query_selector_all("[data-testid='review-unknown']")]
    assert sum("OWNER · UNKNOWN" in u for u in unknowns) == 2, unknowns
    assert sum("DUE · UNKNOWN" in u for u in unknowns) == 2, unknowns
    window = page.locator(".desk-surface-window").first
    _title_visible(page, "Architecture review")
    body_text = window.locator(".desk-surface-body").text_content() or ""
    assert "Architecture review" not in body_text, body_text[:300]
    assert " 0 " not in body_text
    _no_raw_buttons(page, width)
    _shot(page, "review-five", width)

    first_decision = page.locator("[data-testid='review-row-decision']").first
    first_decision.locator("[data-testid='review-more']").click()
    first_decision.locator("[data-testid='review-edit']").click()
    editor = first_decision.get_by_role("textbox").first
    editor.wait_for(timeout=5000)
    editor.fill("Cut-over runs on the read replica first, writes stay frozen")
    editor.press("Enter")
    page.locator("[data-testid='review-receipt']").filter(has_text="EDITED").wait_for(timeout=10_000)
    assert first_decision.locator("[data-testid='review-support'] .surface-state-chip").get_attribute("aria-label") == "LINKED · EDITED"
    assert (first_decision.locator("[data-testid='review-was']").text_content() or "").startswith("WAS · ")
    _shot(page, "review-edited", width)
    edited = [p for p in _review(page, m1)["proposals"] if p["text"].endswith("writes stay frozen")]
    assert len(edited) == 1 and edited[0]["support"] == "source_linked", edited
    assert edited[0]["support_record"]["invalidation_reason"] == "text_edited"

    first_decision.locator("[data-testid='review-confirm']").click()
    page.locator("[data-testid='review-receipt']").filter(has_text="CONFIRMED").wait_for(timeout=10_000)
    assert first_decision.get_attribute("data-state") == "confirmed"
    assert first_decision.locator("[data-testid='review-acceptance'] .surface-state-chip").get_attribute("aria-label") == "ACCEPTED"
    assert "DECISION RECORD · KEPT" in (first_decision.locator("[data-testid='review-kept']").text_content() or "")
    assert page.locator("[data-testid='review-headline']").text_content() == "4 to review"
    assert page.locator("[data-testid='review-accepted']").text_content() == "ACCEPTED 1"
    _shot(page, "review-confirmed", width)
    kept = [p for p in _review(page, m1)["proposals"] if p["state"] == "confirmed"]
    assert len(kept) == 1 and kept[0]["decision_record_id"] and kept[0]["commitment_id"], kept
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM decision_record_sources WHERE source_type = 'meeting' AND source_ref = ?",
            (m1,),
        ).fetchone()[0] == 1
        record = conn.execute(
            "SELECT decision_text FROM decision_records WHERE id = ?",
            (kept[0]["decision_record_id"],),
        ).fetchone()
    assert record["decision_text"].endswith("writes stay frozen")


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.timeout(420)
@pytest.mark.parametrize("width,height", [(1440, 1200), (393, 900)])
def test_meeting_partial_chain_retry_stays_live_under_amendment(
    meeting_outcomes_rig: dict[str, Any],
    request: pytest.FixtureRequest,
) -> None:
    """Keep the complete m2 retry assertions live behind a strict xfail."""
    page = meeting_outcomes_rig["page"]
    url = meeting_outcomes_rig["url"]
    engine = meeting_outcomes_rig["engine"]
    conductor = meeting_outcomes_rig["conductor"]
    project_id = meeting_outcomes_rig["project_id"]
    db = meeting_outcomes_rig["db"]
    width = meeting_outcomes_rig["width"]

    engine.fail_plugins = {ACT}
    m2 = _import_transcript(page, "Architecture review, take two")
    _api(page, "POST", f"/api/projects/{project_id}/meetings/{m2}", token=TOKEN)
    run = _run_intelligence(page, m2)
    assert run["state"] == "queued" and run["drainer"] == "running", run
    request.node.add_marker(pytest.mark.xfail(strict=True, reason=SUMMARY_AMENDMENT_XFAIL))
    assert _wait(
        lambda: len(_review(page, m2)["proposals"]) == 2
        and _review(page, m2)["job"]["status"] == "queued",
        timeout=90.0,
    ), (_review(page, m2), engine.plugin_calls, _diagnose(m2))
    engine.fail_plugins = set()
    review2 = _review(page, m2)
    assert review2["job"]["attempt"] == 2 and review2["job"]["same_job"] is True, review2["job"]
    assert all(p["job_attempt"] == 1 and p["kind"] == "decision" for p in review2["proposals"])
    for p in review2["proposals"]:
        _api(page, "POST", f"/api/proposals/{p['id']}/confirm", {}, token=TOKEN)

    _open_review_wing(page, url, m2)
    _title_visible(page, "Architecture review, take two")
    assert page.locator("[data-testid='review-headline']").text_content() == "Reading the meeting"
    assert page.locator("[data-testid='review-attempt']").text_content() == "ATTEMPT 2 · SAME JOB"
    assert page.locator("[data-testid='review-job']").text_content().startswith("JOB ")
    kept_verb = page.get_by_role("button", name="ALREADY KEPT")
    assert kept_verb.count() == 1
    assert page.locator("[data-testid='review-kept-row']").count() == 2
    assert page.locator("[data-testid='review-kept-open']").count() == 2
    assert page.locator("[data-testid='review-confirm']").count() == 0
    assert page.get_by_role("button", name="Accept reviewed").is_disabled()
    coverage2 = page.locator("[data-testid='review-coverage']").text_content() or ""
    assert "NOT YET READ" in coverage2 and "OF 6" not in coverage2, coverage2
    _no_raw_buttons(page, width)
    _shot(page, "processing-attempt-2", width)

    conductor.wake_intel_queue_conductor()
    assert _wait(lambda: _review(page, m2)["job"]["status"] == "succeeded", timeout=90.0), (
        _review(page, m2)["job"], _diagnose(m2),
    )
    final = _review(page, m2)
    assert len(final["proposals"]) == 5, [(p["kind"], p["text"], p["state"]) for p in final["proposals"]]
    assert sorted(p["state"] for p in final["proposals"]) == ["confirmed", "confirmed", "proposed", "proposed", "proposed"]
    assert all(p["job_attempt"] == 2 for p in final["proposals"] if p["kind"] == "action")
    with db._connection() as conn:
        assert conn.execute(
            """SELECT COUNT(*) FROM decision_records AS r
               JOIN decision_record_sources AS s ON s.record_id = r.id
               WHERE s.source_type = 'meeting' AND s.source_ref = ?""",
            (m2,),
        ).fetchone()[0] == 2
        assert conn.execute(
            "SELECT COUNT(*) FROM follow_through_proposals WHERE meeting_id = ?", (m2,)
        ).fetchone()[0] == 5
