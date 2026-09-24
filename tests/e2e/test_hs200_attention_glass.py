"""HS-200-15 -- actionable attention, on glass.

The four ratified boards (`assets/mockups/P2Arrival`, `P2ArrivalOne`,
`P2ArrivalPhone`, `P2ArrivalQuiet`) against a REAL booted hub on an
isolated HOME, at 1440 and 393:

  one-project     -- his desk: ONE Project, `3 need you`, the Project
                     button withheld, one unreadable source above the
                     answer with its reason, token, observation and verb.
  three-projects  -- `17 need you across 3 projects`, `COVERAGE n OF m`,
                     `NEEDS YOU 5 OF 17`, five ranked rows (overdue first),
                     the Project button on every row, a `2 SOURCES` dedup
                     disclosure, `12 MORE · Show all` revealing in place,
                     the ranking strip as a filter -- and at 393 the strip
                     wraps inside its container (no horizontal scroll).
  quiet-all-clear -- `Nothing needs you` over COMPLETE coverage, with the
                     `N OF N AVAILABLE` chip in the head.

Projects are created through `POST /api/projects`; Watch snapshots are the
one thing no route can seed (they are what a Watch READS), so they are
written as rows the way `test_hs200_coverage_glass.py` writes them.

Shots to phase-200-the-working-practice/assets/story-15-shots/.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,    seed_meeting_engines,
)
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="Attention glass needs Playwright")

SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-15-shots")
#: Shots are tracked evidence: a plain suite run never rewrites them.  Set
#: HOLDSPEAK_WRITE_SHOTS=1 to (re)take them (counsel P1-7).
WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS") == "1"

TOKEN = "hs200-attention"
OWNER_LOGIN = "karolswdev"

pytestmark = [pytest.mark.e2e]


# ── seeds ────────────────────────────────────────────────────────────


def _utc_naive(delta: timedelta = timedelta()) -> str:
    """connector_watches stores NAIVE UTC (project_service.aware_iso)."""
    return (datetime.now(timezone.utc).replace(tzinfo=None) + delta).isoformat()


def _local_day(delta_days: int) -> str:
    return (datetime.now() + timedelta(days=delta_days)).strftime("%Y-%m-%d")


def _seed_gh_connection() -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (OWNER_LOGIN,),
        )


def _create_project(page: Any, name: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-15 browser proof.",
        "command_id": f"hs200-15-{uuid.uuid4().hex[:8]}",
    }, token=TOKEN)
    return created["project"]["id"]


def _seed_watch(
    project_id: str,
    *,
    watch_id: str,
    connector_id: str,
    query_kind: str,
    query: dict[str, Any],
    snapshot: list[dict[str, Any]] | None = None,
    last_success_at: str | None = None,
    last_error: str | None = None,
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                watch_id, connector_id, query_kind, f"{connector_id} {query_kind}",
                json.dumps(query, sort_keys=True), json.dumps(snapshot or []),
                last_success_at, last_error, project_id,
            ),
        )


def _pr(number: int, title: str, *, days_ago: int, checks: str = "passing") -> dict[str, Any]:
    return {
        "number": number, "title": title, "state": "OPEN",
        "url": f"https://github.com/karolswdev/HoldSpeak/pull/{number}",
        "reviewRequests": [OWNER_LOGIN], "checks": checks,
        "updatedAt": _utc_naive(-timedelta(days=days_ago)),
    }


def _issue(key: str, summary: str, *, due_days_ago: int) -> dict[str, Any]:
    return {
        "key": key, "summary": summary,
        "due_at": _local_day(-due_days_ago),
        "url": f"https://jira.example/browse/{key}",
    }


def _seed_proposal(project_id: str, text: str) -> None:
    """A meeting's proposal for the SAME obligation a Watch already names."""
    from holdspeak.db import get_database
    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES ('m-standup', ?, ?, 'Standup', 1800.0, 'complete', "
            " 'finalized', 'desktop')",
            ((now - timedelta(hours=2)).isoformat(),
             (now - timedelta(hours=1, minutes=30)).isoformat()),
        )
        conn.execute(
            "INSERT INTO follow_through_proposals "
            "(id, meeting_id, project_id, kind, text, due_hint, "
            " source_plugin, fingerprint, state, model_host, created_at) "
            "VALUES (?, 'm-standup', ?, 'action', ?, NULL, 'decision_capture', ?, "
            " 'proposed', '192.168.1.43', ?)",
            (f"prop-{uuid.uuid4().hex[:12]}", project_id, text,
             f"fp-{uuid.uuid4().hex[:16]}", now.isoformat()),
        )


def _seed_one_project(page: Any) -> str:
    """His desk: one Project, three items, one unreadable source."""
    _seed_gh_connection()
    pid = _create_project(page, "Q4 Platform")
    _seed_watch(
        pid, watch_id="w-q4-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/HoldSpeak"},
        last_success_at=_utc_naive(-timedelta(minutes=10)),
        snapshot=[
            _pr(612, "Rig settles animations before every shot", days_ago=3),
            _pr(618, "One composition root for the sidecar", days_ago=1),
            _pr(620, "Census reads the real projection", days_ago=0, checks="failing"),
        ],
    )
    _seed_watch(
        pid, watch_id="w-q4-jira", connector_id="jira", query_kind="issues",
        query={"jql": "project = KAN AND due < now()"},
        last_success_at=_utc_naive(-timedelta(minutes=31)),
        last_error="JQL parse error: The value 'KAN' does not exist for the field 'project'.",
    )
    return pid


def _seed_three_projects(page: Any) -> dict[str, str]:
    """Seventeen after dedup: 18 projections, one obligation seen twice."""
    _seed_gh_connection()
    q4 = _create_project(page, "Q4 Platform")
    gov = _create_project(page, "Governance")
    pay = _create_project(page, "Payments")

    # Q4 Platform: 2 overdue issues, 4 PRs waiting, a proposal for KAN-7's
    # runbook (the dedup), and the jira watch that cannot check.
    _seed_watch(
        q4, watch_id="w-q4-overdue", connector_id="jira", query_kind="issues",
        query={"jql": "project = KAN AND due < now()"},
        last_success_at=_utc_naive(-timedelta(minutes=12)),
        snapshot=[
            _issue("KAN-7", "Payments cut-over runbook", due_days_ago=2),
            _issue("KAN-12", "Rotate the staging credentials", due_days_ago=1),
        ],
    )
    _seed_watch(
        q4, watch_id="w-q4-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/HoldSpeak"},
        last_success_at=_utc_naive(-timedelta(minutes=10)),
        snapshot=[_pr(612 + n, f"Q4 change {n + 1}", days_ago=3 + n) for n in range(4)],
    )
    _seed_watch(
        q4, watch_id="w-q4-kan", connector_id="jira", query_kind="issues",
        query={"jql": "project = KAN AND status = Blocked"},
        last_success_at=_utc_naive(-timedelta(minutes=31)),
        last_error="JQL parse error: The value 'KAN' does not exist for the field 'project'.",
    )
    _seed_proposal(q4, "Payments cut-over runbook")

    # Governance: CI red on main, 5 PRs waiting, and a stale watch.
    _seed_watch(
        gov, watch_id="w-gov-ci", connector_id="gh", query_kind="branch_ci",
        query={"repository": "karolswdev/Governance", "branch": "main"},
        last_success_at=_utc_naive(-timedelta(minutes=40)),
        snapshot=[{
            "id": "ci-main", "branch": "main", "conclusion": "failure",
            "url": "https://github.com/karolswdev/Governance/actions",
            "updated_at": _utc_naive(-timedelta(minutes=40)),
        }],
    )
    _seed_watch(
        gov, watch_id="w-gov-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/Governance"},
        last_success_at=_utc_naive(-timedelta(minutes=9)),
        snapshot=[_pr(700 + n, f"Governance change {n + 1}", days_ago=1 + n) for n in range(5)],
    )
    _seed_watch(
        gov, watch_id="w-gov-stale", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/Platform"},
        last_success_at=_utc_naive(-timedelta(hours=9)),
        snapshot=[],
    )

    # Payments: 5 PRs waiting.
    _seed_watch(
        pay, watch_id="w-pay-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/Payments"},
        last_success_at=_utc_naive(-timedelta(minutes=7)),
        snapshot=[_pr(800 + n, f"Payments change {n + 1}", days_ago=2 + n) for n in range(5)],
    )
    return {"q4": q4, "gov": gov, "pay": pay}


LONG_TITLE = ("Rotate the staging credentials for the payments gateway and the "
              "reconciliation worker before the freeze")  # 90 chars
LONG_PROJECT = "Payments Platform Modernisation"  # 31 chars


def _seed_long_row(page: Any) -> str:
    """Counsel P0-2: the longest realistic row -- a 31-char Project, a
    90-char title, and the `2 SOURCES` disclosure ON that row -- beside
    a second Project so the Project button is drawn."""
    _seed_gh_connection()
    pid = _create_project(page, LONG_PROJECT)
    other = _create_project(page, "Governance")
    _seed_watch(
        pid, watch_id="w-long-jira", connector_id="jira", query_kind="issues",
        query={"jql": "project = KAN AND due < now()"},
        last_success_at=_utc_naive(-timedelta(minutes=12)),
        snapshot=[_issue("KAN-7", LONG_TITLE, due_days_ago=2)],
    )
    _seed_proposal(pid, LONG_TITLE)
    _seed_watch(
        pid, watch_id="w-long-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/HoldSpeak"},
        last_success_at=_utc_naive(-timedelta(minutes=10)),
        snapshot=[_pr(612 + n, f"Q4 change {n + 1}", days_ago=3 + n) for n in range(3)],
    )
    _seed_watch(
        other, watch_id="w-gov-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/Governance"},
        last_success_at=_utc_naive(-timedelta(minutes=9)),
        snapshot=[_pr(700, "Governance change 1", days_ago=1)],
    )
    return pid


def _seed_quiet(page: Any) -> str:
    """One Project, every source readable, nothing waiting on him."""
    _seed_gh_connection()
    pid = _create_project(page, "Q4 Platform")
    _seed_watch(
        pid, watch_id="w-q4-gh", connector_id="gh", query_kind="pull_requests",
        query={"repository": "karolswdev/HoldSpeak"},
        last_success_at=_utc_naive(-timedelta(minutes=1)),
        snapshot=[{
            "number": 630, "title": "Someone else's review", "state": "OPEN",
            "url": "https://github.com/karolswdev/HoldSpeak/pull/630",
            "reviewRequests": ["someone-else"], "checks": "passing",
            "updatedAt": _utc_naive(-timedelta(hours=1)),
        }],
    )
    return pid


# ── glass helpers ────────────────────────────────────────────────────


def _arrive(page: Any, url: str) -> None:
    # HS-201-01: the meeting path is pinned before every arrival in this
    # rig. A cold HOME has no engine, and the Chair now names that in a
    # SETUP row; this rig's subject is the attention band and coverage.
    seed_meeting_engines()
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)


def _reload_arrival(page: Any) -> None:
    page.reload(wait_until="load")
    _normal_chair(page)
    _settle(page)
    page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
    _settle(page)


def _shot(page: Any, name: str, width: int) -> Path | None:
    """Take a shot with the pointer parked off every row (no hover state)."""
    if not WRITE_SHOTS:
        return None
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.mouse.move(2, 2)
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _primaries(page: Any) -> list[str]:
    """Every filled primary on the WHOLE face (counsel P1-2): exactly one."""
    return page.evaluate("""() => [...document.querySelectorAll('.btn--primary')]
        .map(b => (b.className + ' :: ' + (b.textContent || '').trim()))""")


def _overflowing(page: Any, width: int) -> list[str]:
    """Every interactive element whose right edge passes the viewport
    (counsel P0-2): scrollWidth alone cannot see a clipped ancestor."""
    return page.evaluate("""(width) => {
        const out = [];
        // The arrival's own elements; the shell's dock and bell are its
        // business (they are clipped by the shell's overflow by design).
        const chair = document.querySelector('.chair') || document;
        const sel = 'button, a, [role="button"], [role="group"], .surface-disclosure-trigger, .surface-project-button';
        for (const el of chair.querySelectorAll(sel)) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            if (r.right > width + 0.5) out.push((el.className || el.tagName) + ' :: ' + (el.textContent || '').trim().slice(0, 40) + ' right=' + r.right.toFixed(1));
        }
        return out;
    }""", width)


def _raw_buttons(page: Any) -> list[str]:
    """Every <button> in the chair that is not the library Button, the mic,
    a ledger line, or a library Disclosure trigger (a library species that
    owns its own trigger)."""
    return page.evaluate("""() => {
        const chair = document.querySelector('[data-testid="chair"]') || document.querySelector('.chair');
        if (!chair) return [];
        const raw = [];
        for (const btn of chair.querySelectorAll('button')) {
            const cls = btn.className || '';
            if (!cls.includes('btn') && !cls.includes('desk-mic') &&
                !cls.includes('surface-ledger-line') &&
                !cls.includes('surface-disclosure-trigger')) raw.push(cls + ' :: ' + (btn.textContent || '').trim());
        }
        return raw;
    }""")


def _no_horizontal_scroll(page: Any, width: int) -> None:
    page.mouse.move(2, 2)
    scroll_width = page.evaluate("document.documentElement.scrollWidth")
    assert scroll_width <= width, f"horizontal overflow: scrollWidth {scroll_width} > {width}"
    over = _overflowing(page, width)
    assert over == [], f"elements past the viewport at {width}: {over}"
    strip = page.locator(".arrival-ranking").first
    if strip.count():
        box = strip.bounding_box()
        assert box is not None
        assert box["x"] + box["width"] <= width + 0.5, \
            f"the ranking strip overruns the viewport: {box}"
        for token in page.locator(".arrival-ranking .btn").all():
            tb = token.bounding_box()
            assert tb is not None and tb["x"] + tb["width"] <= width + 0.5, \
                f"a ranking token overruns the viewport: {tb}"


def _row_texts(page: Any, testid: str) -> list[str]:
    return [
        (row.text_content() or "").strip()
        for row in page.get_by_test_id(testid).all()
    ]


# ── legs ─────────────────────────────────────────────────────────────


def _run_one_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_one_project(page)
            _reload_arrival(page)

            wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            assert wire["count"] == 3, wire["items"]
            assert wire["projects"] and len(wire["projects"]) == 1
            assert wire["complete"] is False, wire["coverage"]
            assert [row["rankClass"] for row in wire["items"]] == [
                "no_due_date", "waiting", "waiting",
            ], [(r["title"], r["rankClass"]) for r in wire["items"]]
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-needs-you").wait_for(timeout=15000)
            _settle(page)

            # The display line: the TRUE total, the Project clause withheld.
            headline = (page.get_by_test_id("arrival-display").text_content() or "").strip()
            assert headline == "3 need you", headline
            assert page.get_by_role("group", name="Project").count() == 0, \
                "the Project button is withheld over one Project"

            # Coverage ABOVE the answer, with the source's own reason.
            coverage = page.get_by_test_id("arrival-coverage")
            assert coverage.count() == 1
            assert coverage.locator("[data-testid='arrival-coverage-reason']").first.text_content() == "JIRA REJECTED THE QUERY"
            assert "CANT CHECK" in (coverage.locator("[data-testid='arrival-coverage-token']").first.text_content() or "")
            observed = coverage.locator("[data-testid='arrival-coverage-observed']").first.text_content() or ""
            assert observed.startswith("OBSERVED "), observed
            assert (coverage.locator("[data-testid='arrival-coverage-verb']").first.text_content() or "").strip() == "Reconnect"
            boxes = page.evaluate("""() => ({
                coverage: document.querySelector('[data-testid="arrival-coverage"]').getBoundingClientRect().top,
                needs: document.querySelector('[data-testid="arrival-needs-you"]').getBoundingClientRect().top,
            })""")
            assert boxes["coverage"] < boxes["needs"], boxes

            section = page.get_by_test_id("arrival-needs-you")
            assert "NEEDS YOU 3" in (section.text_content() or "")
            rows = section.locator("[data-testid='arrival-needs-you-row']")
            assert rows.count() == 3
            assert page.get_by_test_id("arrival-needs-you-remainder").count() == 0, \
                "no remainder under three rows (A.8)"
            assert page.get_by_role("group", name="Ranking").count() == 1
            # The first row's verb is the one filled primary on the face.
            assert len(_primaries(page)) == 1, _primaries(page)
            assert _raw_buttons(page) == [], _raw_buttons(page)
            _no_horizontal_scroll(page, width)

            _shot(page, "one-project", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_three_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1100})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_three_projects(page)
            _reload_arrival(page)

            wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            assert wire["count"] == 17, [(r["title"], r["source"]) for r in wire["items"]]
            assert len(wire["projects"]) == 3
            assert wire["complete"] is False
            available = sum(1 for c in wire["coverage"] if c["state"] == "available")
            expected = len(wire["coverage"])
            gaps = [c for c in wire["coverage"] if c["state"] != "available"]
            assert {c["repair"]["token"] for c in gaps} >= {"CANT CHECK", "STALE"}, gaps
            first = wire["items"][0]
            assert first["title"].startswith("KAN-7"), first
            assert first["rankClass"] == "overdue" and first["dedupCount"] == 2, first
            assert {s["source"] for s in first["sources"]} == {"jira", "proposal"}
            assert wire["items"][1]["rankClass"] == "overdue"
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-needs-you").wait_for(timeout=15000)
            _settle(page)

            headline = (page.get_by_test_id("arrival-display").text_content() or "").strip()
            assert headline == "17 need you across 3 projects", headline

            coverage = page.get_by_test_id("arrival-coverage")
            assert f"COVERAGE · {available} OF {expected}" in (coverage.text_content() or "")
            assert coverage.locator("[data-testid='arrival-coverage-row']").count() == len(gaps)
            verbs = {(v.text_content() or "").strip()
                     for v in coverage.locator("[data-testid='arrival-coverage-verb']").all()}
            assert verbs >= {"Reconnect", "Retry"}, verbs

            section = page.get_by_test_id("arrival-needs-you")
            assert "NEEDS YOU 5 OF 17" in (section.text_content() or "")
            rows = section.locator("[data-testid='arrival-needs-you-row'], [data-testid='arrival-proposal-row']")
            assert rows.count() == 5, _row_texts(page, "arrival-needs-you-row")
            first_row = rows.nth(0)
            assert "KAN-7 Payments cut-over runbook" in (first_row.text_content() or "")
            assert (first_row.locator("[data-testid='arrival-why']").text_content() or "").startswith("OVERDUE · 2 DAY")
            assert rows.nth(1).locator("[data-testid='arrival-why']").text_content().startswith("OVERDUE")
            # The Project on every row, as a Button in a group.
            assert page.locator("[data-testid='arrival-needs-you-row'] [role='group'][aria-label='Project'] .btn").count() == 5
            # The dedup disclosure names both sources.
            # exact: the row line is a role=button whose name is computed
            # from its content, so a substring match would hit it too.
            trigger = page.get_by_role(
                "button", name="Sources: KAN-7 Payments cut-over runbook", exact=True,
            )
            assert trigger.count() == 1
            assert "2 SOURCES" in (trigger.text_content() or "")
            trigger.click()
            _settle(page)
            assert page.get_by_test_id("arrival-source").count() == 2
            assert page.get_by_test_id("arrival-source-open").count() == 2
            trigger.click()
            _settle(page)
            # One filled primary on the WHOLE face: the top row's verb.
            assert len(_primaries(page)) == 1, _primaries(page)
            assert _raw_buttons(page) == [], _raw_buttons(page)
            _no_horizontal_scroll(page, width)

            _shot(page, "three-projects", width)

            # The remainder: a real count, a real verb, revealed in place.
            assert (page.get_by_test_id("arrival-needs-you-remainder-count").text_content() or "").strip() == "12 MORE"
            page.get_by_role("button", name="Show all: the remaining 12").click()
            _settle(page)
            assert rows.count() == 17
            assert "NEEDS YOU 17" in (section.text_content() or "")
            _no_horizontal_scroll(page, width)
            _shot(page, "three-projects-all", width)
            page.get_by_role("button", name="Show fewer: hide the remaining 12").click()
            _settle(page)
            assert rows.count() == 5

            # The strip filters by class, and RANKED restores the key.
            strip = page.get_by_role("group", name="Ranking")
            strip.get_by_role("button", name="OVERDUE").click()
            _settle(page)
            assert rows.count() == 2, _row_texts(page, "arrival-needs-you-row")
            assert len(_primaries(page)) == 1, _primaries(page)
            strip.get_by_role("button", name="NOT RUN").click()
            _settle(page)
            assert (page.get_by_test_id("arrival-needs-you-none").text_content() or "").strip() == "NOTHING NOT RUN"
            strip.get_by_role("button", name="RANKED").click()
            _settle(page)
            assert rows.count() == 5

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_long_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Counsel P0-2: nothing extends past the viewport; one primary on the
    whole face; the sources disclosure opens with an Open per projection."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1100})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_long_row(page)
            _reload_arrival(page)
            wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            first = wire["items"][0]
            assert first["title"].startswith("KAN-7") and first["dedupCount"] == 2, first
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-needs-you").wait_for(timeout=15000)
            _settle(page)
            page.mouse.move(2, 2)

            row = page.locator("[data-testid='arrival-needs-you-row']").first
            assert LONG_TITLE in (row.text_content() or "")
            project = row.locator(".surface-project-button")
            assert project.count() == 1
            assert (project.get_attribute("aria-label") or "") == f"Open the Project: {LONG_PROJECT}"
            _no_horizontal_scroll(page, width)
            # The verb sits on the SAME line as the meta, at its right.
            boxes = page.evaluate("""() => {
                const row = document.querySelector('[data-testid="arrival-needs-you-row"]');
                const meta = row.querySelector('.arrival-needs-you-meta').getBoundingClientRect();
                const verb = row.querySelector('.surface-ledger-trailing .btn').getBoundingClientRect();
                const name = row.querySelector('.surface-ledger-primary').getBoundingClientRect();
                return {metaTop: meta.top, metaBottom: meta.bottom, verbTop: verb.top, verbBottom: verb.bottom,
                        verbRight: verb.right, nameBottom: name.bottom, rowRight: row.getBoundingClientRect().right};
            }""")
            assert boxes["verbRight"] <= width + 0.5, boxes
            if width <= 480:
                assert boxes["verbTop"] >= boxes["nameBottom"] - 1, f"the verb is under the name at 393: {boxes}"
                assert boxes["verbTop"] < boxes["metaBottom"] and boxes["verbBottom"] > boxes["metaTop"], \
                    f"the verb shares the meta line at 393: {boxes}"
            assert len(_primaries(page)) == 1, _primaries(page)

            _shot(page, "long-row", width)

            trigger = row.locator(".surface-disclosure-trigger").first
            trigger.click()
            _settle(page)
            opens = page.get_by_test_id("arrival-source-open")
            assert opens.count() == 2, "every projection keeps its own Open"
            titles = [t.text_content() for t in page.locator(".arrival-source-title").all()]
            assert titles == [f"KAN-7 {LONG_TITLE}", LONG_TITLE], titles
            _no_horizontal_scroll(page, width)
            assert len(_primaries(page)) == 1, _primaries(page)
            _shot(page, "long-row-sources", width)

            # The selected filter token is never the filled primary.
            page.get_by_role("group", name="Ranking").get_by_role("button", name="OVERDUE").click()
            _settle(page)
            assert len(_primaries(page)) == 1, _primaries(page)

            if width <= 480:
                # Counsel P1-8: scrolled to the end, the last section clears the
                # capture bar.
                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                page.wait_for_timeout(200)
                _settle(page)
                clear = page.evaluate("""() => {
                    const bar = document.querySelector('.arrival-capture-bar').getBoundingClientRect();
                    const sections = [...document.querySelectorAll('.chair > [data-testid^="arrival-"]')]
                        .filter(el => !el.classList.contains('arrival-capture-bar'));
                    const last = sections[sections.length - 1].getBoundingClientRect();
                    return {barTop: bar.top, lastBottom: last.bottom, lastId: sections[sections.length - 1].getAttribute('data-testid')};
                }""")
                assert clear["lastBottom"] <= clear["barTop"] + 0.5, clear
                _shot(page, "bar-clear", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_quiet_all_clear(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_quiet(page)
            _reload_arrival(page)

            wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            assert wire["count"] == 0, wire["items"]
            assert wire["complete"] is True, wire["coverage"]
            expected = len(wire["coverage"])
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _settle(page)

            headline = (page.get_by_test_id("arrival-display").text_content() or "").strip()
            assert headline == "Nothing needs you", headline
            chip = page.get_by_test_id("arrival-coverage-complete")
            assert chip.count() == 1
            assert f"{expected} OF {expected} AVAILABLE" in (chip.text_content() or "")
            assert (page.get_by_test_id("arrival-checked").text_content() or "").startswith("CHECKED")
            assert page.get_by_test_id("arrival-coverage").count() == 0
            assert page.get_by_test_id("arrival-needs-you").count() == 0
            assert page.get_by_role("group", name="Ranking").count() == 0
            assert page.get_by_test_id("arrival-no-calendar").count() == 1
            assert len(_primaries(page)) == 0, _primaries(page)
            assert _raw_buttons(page) == [], _raw_buttons(page)
            _no_horizontal_scroll(page, width)

            _shot(page, "quiet-all-clear", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── pytest entry points ──────────────────────────────────────────────


class TestAttentionGlass:
    """HS-200-15 -- the attention face at both viewports."""

    def test_one_project_1440(self, tmp_path, monkeypatch) -> None:
        _run_one_project(tmp_path, monkeypatch, 1440)

    def test_one_project_393(self, tmp_path, monkeypatch) -> None:
        _run_one_project(tmp_path, monkeypatch, 393)

    def test_three_projects_1440(self, tmp_path, monkeypatch) -> None:
        _run_three_projects(tmp_path, monkeypatch, 1440)

    def test_three_projects_393(self, tmp_path, monkeypatch) -> None:
        _run_three_projects(tmp_path, monkeypatch, 393)

    def test_long_row_1440(self, tmp_path, monkeypatch) -> None:
        _run_long_row(tmp_path, monkeypatch, 1440)

    def test_long_row_393(self, tmp_path, monkeypatch) -> None:
        _run_long_row(tmp_path, monkeypatch, 393)

    def test_quiet_all_clear_1440(self, tmp_path, monkeypatch) -> None:
        _run_quiet_all_clear(tmp_path, monkeypatch, 1440)

    def test_quiet_all_clear_393(self, tmp_path, monkeypatch) -> None:
        _run_quiet_all_clear(tmp_path, monkeypatch, 393)
