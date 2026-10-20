"""Needs you in a real browser: touch, cross-window latency and geometry.

Kept by the test diet (push 2, 2026-10-12), one file for the Needs-you app:

* the long row at 393 (HS-200-15, re-faced by PHILO-14 A5): the verb sits
  under the name, and scrolled to the end the drawer's last part clears the
  Needs-you window body (exact geometry);
* ONE number (PHILO-13-03): the Chair head and the bell agree, and Done on a
  row moves both within 1 s with no reload, at 1440 (mouse) and 393 (touch).

Was tests/e2e/test_hs200_attention_glass.py and
tests/e2e/test_philo13_03_needs_you_glass.py. Their other legs: the wire
(rank, merge, count, coverage) is tests/unit/test_attention.py; the faces
(one project, three projects, the quiet all-clear, source rows, one primary)
are web/src/desk/needs/__tests__/NeedsDrawer.test.tsx and
web/src/desk/chair/arrivalAttention.test.tsx; the 1440 fit is the desk sweep's.

Projects are created through `POST /api/projects`; Watch snapshots are the
one thing no route can seed (they are what a Watch READS), so they are
written as rows.
"""
from __future__ import annotations

import json
import os
import re
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

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = [pytest.mark.e2e, pytest.mark.chair_windows_open]


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


# ── glass helpers ────────────────────────────────────────────────────

#: The drawer's member rows (not the source rows, not the waiting or muted lists).
MEMBERS = "[data-testid='needs-list'] ul.needs-list > [data-testid='needs-row']"
#: The drawer's source rows (a source not read, no calendar).
SOURCES = "[data-testid='needs-source-row']"


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


# ── legs ─────────────────────────────────────────────────────────────


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
            page.locator(MEMBERS).first.wait_for(timeout=15000)
            _settle(page)
            page.mouse.move(2, 2)

            row = page.locator(MEMBERS).first
            assert LONG_TITLE in (row.text_content() or "")
            assert page.locator(MEMBERS).filter(has_text=LONG_TITLE).count() == 1
            _no_horizontal_scroll(page, width)
            boxes = page.evaluate("""() => {
                const row = document.querySelector('[data-testid="needs-row"]');
                const verb = row.querySelector('.needs-row-verbs .btn').getBoundingClientRect();
                const name = row.querySelector('.needs-row-name').getBoundingClientRect();
                return {verbTop: verb.top, verbRight: verb.right, nameBottom: name.bottom};
            }""")
            assert boxes["verbRight"] <= width + 0.5, boxes
            if width <= 480:
                assert boxes["verbTop"] >= boxes["nameBottom"] - 1, f"the verb is under the name at 393: {boxes}"
            assert len(_primaries(page)) == 1, _primaries(page)

            _shot(page, "long-row", width)

            if width <= 480:
                # Counsel P1-8: scrolled to the end, the drawer's last part
                # clears the Needs-you window body's lower edge.
                page.evaluate("""() => { const b = document.querySelector('.chair-window--needs .chair-window-body');
                    b.scrollTop = b.scrollHeight; }""")
                page.wait_for_timeout(200)
                _settle(page)
                clear = page.evaluate("""() => {
                    const body = document.querySelector('.chair-window--needs .chair-window-body');
                    const bar = body.getBoundingClientRect();
                    const parts = [...body.querySelectorAll('[data-testid="needs-drawer"] > *')]
                        .filter(el => el.getBoundingClientRect().height > 0);
                    const last = parts[parts.length - 1].getBoundingClientRect();
                    return {barTop: bar.bottom, lastBottom: last.bottom};
                }""")
                assert clear["lastBottom"] <= clear["barTop"] + 0.5, clear
                _shot(page, "bar-clear", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── pytest entry points ──────────────────────────────────────────────


class TestAttentionGlass:
    """HS-200-15 -- the attention face at both viewports."""

    def test_long_row_393(self, tmp_path, monkeypatch) -> None:
        _run_long_row(tmp_path, monkeypatch, 393)


# ── ONE meaning of "needs you" (PHILO-13-03, A2-W) ──────────────────────
# Was tests/e2e/test_philo13_03_needs_you_glass.py. The oracle week is minted
# through the real producers (scripts/philo13_needs_you_fixture.py seed_week);
# the hub restarts on that database. The Chair head and the bell show the
# same number; Done on a row (a tap at 393) moves both, and the Dock carries
# no copy, within 1 s and with no reload; no visible "need(s) you" carries
# another number; Meetings never says "needs you"; the Room's NEEDS YOU is
# its project's filter, with no number (Betterment P3). (The Meetings headline cases are
# web/src/pages/cores/history/__tests__/meetingsHeadline.philo1303.test.ts.)

ONE_TOKEN = "philo13-03-needs-you"
ONE_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-03-shots")
SIZES = {1440: 900, 393: 852}
A1_TASK = "A1 close the overdue release note"

# The three readers of the ONE number, and every "need(s) you" on the glass.
READERS = r"""() => {
  const num = (e) => { const m = ((e && e.innerText) || '').match(/\d+/); return m ? Number(m[0]) : null; };
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const said = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const t = n.textContent.replace(/\s+/g, ' ').trim();
    if (/needs? you/i.test(t) && vis(n.parentElement)) said.push(t);
  }
  for (const e of document.querySelectorAll('[aria-label]')) {
    const t = e.getAttribute('aria-label');
    if (/\d+\s+needs? you/i.test(t)) said.push('aria:' + t);
  }
  const head = document.querySelector('[data-testid=arrival-display]');
  const bell = document.querySelector('.desk-bell strong');
  const intel = document.querySelector('.desk-dock [aria-label^="Today"] .desk-dock-badge');
  const memory = document.querySelector('.desk-dock [aria-label^="Missed"] .desk-dock-badge');
  return { said, head: head ? head.innerText : null, head_n: num(head), bell: num(bell),
           intel: num(intel), memory: memory ? num(memory) : null };
}"""

# Resolves with the milliseconds from the press until head, bell and Dock all
# read `target` (polled each animation frame; no reload in between).
AGREE = r"""(target) => new Promise((resolve) => {
  const t0 = window.__p13PressAt;
  const read = (sel) => { const e = document.querySelector(sel); const m = ((e && e.innerText) || '').match(/\d+/); return m ? Number(m[0]) : null; };
  const tick = () => {
    const head = read('[data-testid=arrival-display]');
    const bell = read('.desk-bell strong');
    const intel = read('.desk-dock [aria-label^="Today"] .desk-dock-badge');
    if (head === target && bell === target && intel === target) {
      resolve({ ms: Math.round(performance.now() - t0), head, bell, intel });
      return;
    }
    if (performance.now() - t0 > 10000) { resolve({ ms: null, head, bell, intel }); return; }
    requestAnimationFrame(tick);
  };
  tick();
})"""


def _numbers_said(said: list[str]) -> list[int]:
    out: list[int] = []
    for text in said:
        for match in re.finditer(r"(\d+)\s+needs?\s+you", text, re.IGNORECASE):
            out.append(int(match.group(1)))
    return out


@pytest.mark.chair_windows_open
class TestOneNeedsYou:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        from scripts.philo13_needs_you_fixture import seed_week

        server, _ = _boot(tmp_path, monkeypatch, token=ONE_TOKEN)
        try:
            self.week = seed_week(tmp_path / "holdspeak.db", home=tmp_path)
        finally:
            server.stop()
        # The hub restarts on the seeded database (the Dock atlas case's
        # `seed_needs_you_week` restart): no cached projection survives.
        server, base = _boot(tmp_path, monkeypatch, token=ONE_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={ONE_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=ONE_TOKEN)
        page.reload(wait_until="load")
        _normal_chair(page)
        return browser, page, errors

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.evaluate("() => { window.__p13PressAt = performance.now(); }")
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            page.evaluate("() => { window.__p13PressAt = performance.now(); }")
            loc.click()

    @staticmethod
    def _shot(page: Any, name: str, width: int) -> None:
        _settle(page)
        page.screenshot(path=str(ONE_SHOTS / f"{name}-{width}.png"))

    @staticmethod
    def _staged_open(page: Any, key: str, scope: str | None = None) -> None:
        page.evaluate(
            """([key, scope]) => sessionStorage.setItem(
                 "hs.desk.staged-surface-open", JSON.stringify(scope ? {key, scope} : {key}))""",
            [key, scope],
        )
        page.reload(wait_until="load")
        _normal_chair(page)

    def _agree_on(self, page: Any, n: int) -> dict[str, Any]:
        page.wait_for_function(
            """(n) => {
              const r = (s) => { const e = document.querySelector(s); const m = ((e && e.innerText) || '').match(/\\d+/); return m ? Number(m[0]) : null; };
              return r('[data-testid=arrival-display]') === n && r('.desk-bell strong') === n;
            }""",
            arg=n, timeout=20_000,
        )
        return page.evaluate(READERS)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_one_number_everywhere_and_done_moves_all_three(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        record: dict[str, Any] = {"width": width, "touch": width < 720,
                                  "oracle": {"expectedRefs": self.week["expectedRefs"],
                                             "expectedCount": self.week["expectedCount"]}}
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                # ── one number: 6 on the head, bell and Today Dock tile ──
                before = self._agree_on(page, 6)
                record["before"] = before
                assert before["head_n"] == before["bell"] == 6, before
                assert before["intel"] == 6 and before["memory"] is None, before
                said = _numbers_said(before["said"])
                assert said and all(n == 6 for n in said), before["said"]

                # ── the drawer's counted rows are the members the head counts ──
                # Betterment D1 (#1277): the drawer also lists the rows the one
                # count rule leaves out (what a person owes him: A3 waits on
                # Priya), marked not counted. They never change the number.
                rows = page.locator("[data-testid='needs-list'] ul.needs-list > [data-testid='needs-row']")
                counted = page.locator(
                    "[data-testid='needs-list'] ul.needs-list > [data-testid='needs-row'][data-counted='true']")
                listed_only = page.locator(
                    "[data-testid='needs-list'] ul.needs-list > [data-testid='needs-row'][data-counted='false']")
                record["chair_rows"] = rows.count()
                record["chair_counted_rows"] = counted.count()
                record["chair_listed_only"] = listed_only.all_inner_texts()
                assert counted.count() == 6, counted.all_inner_texts()
                assert rows.count() == counted.count() + listed_only.count(), rows.all_inner_texts()
                assert all(A1_TASK not in text for text in record["chair_listed_only"]), record["chair_listed_only"]
                assert not re.search(r"needs? you", page.locator("[data-testid='needs-list']").inner_text(), re.IGNORECASE)
                self._shot(page, "a2w-chair-6", width)

                # ── Done on A1 -> all three read 5 within 1 s, no reload ──
                row = page.locator("[data-testid='needs-row']", has_text=A1_TASK).first
                done = row.get_by_role("button", name=re.compile(r"^Done: "))
                nav = []
                page.on("framenavigated", lambda frame: nav.append(frame.url))
                self._press(page, done, width)
                latency = page.evaluate(AGREE, 5)
                record["done_latency"] = latency
                assert latency["ms"] is not None, latency
                assert latency["ms"] <= 1000, latency
                assert not nav, f"the page navigated: {nav}"
                after = page.evaluate(READERS)
                record["after"] = after
                assert after["intel"] == 5 and after["memory"] is None, after
                said = _numbers_said(after["said"])
                assert said and all(n == 5 for n in said), after["said"]
                self._shot(page, "a2w-chair-done-5", width)

                # ── Meetings counts summaries, never "needs you" ──
                self._staged_open(page, "review-meetings")
                page.locator(".desk-surface-window").first.wait_for(timeout=15_000)
                page.locator(".meetings-headline, [data-testid='meetings-headline'], .surface-display").first.wait_for(timeout=15_000)
                _settle(page)
                meetings = page.evaluate(READERS)
                record["meetings"] = {"said": meetings["said"]}
                window_text = page.locator(".desk-surface-window").first.inner_text()
                record["meetings"]["headline"] = page.locator(".desk-surface-window .surface-display").first.inner_text()
                assert not re.search(r"needs? you", window_text, re.IGNORECASE), window_text[:400]
                assert all(n == 5 for n in _numbers_said(meetings["said"])), meetings["said"]
                self._shot(page, "a2w-meetings", width)

                # ── the Room says where the project stands ──
                self._staged_open(page, "open-project-memory", f"project:{self.week['ids']['project']}")
                head = page.locator("[data-testid='room-headline']")
                head.wait_for(timeout=15_000)
                _settle(page)
                room_head = head.inner_text().strip()
                record["room"] = {"headline": room_head}
                # Betterment P3: the Room's head says where the project stands.
                assert re.fullmatch(r"On track|New|Not all read|(?:At risk|Blocked)(?:: .+)?", room_head), room_head
                room = page.evaluate(READERS)
                record["room"]["said"] = room["said"]
                assert all(n == 5 for n in _numbers_said(room["said"])), room["said"]
                room_window = page.locator("[data-testid='room-headline']").locator(
                    "xpath=ancestor::*[contains(@class,'desk-surface-window') or contains(@class,'desk-window-shell')][1]")
                if room_window.count():
                    text = room_window.first.inner_text()
                    # Betterment P3: the project's own filter of the one Needs
                    # you list is named NEEDS YOU (DESIGN.md "The words").
                    record["room"]["needs_you"] = bool(re.search(r"NEEDS YOU", text))
                self._shot(page, "a2w-room", width)

                record["page_errors"] = errors
                assert not errors, errors
            finally:
                (ONE_SHOTS / f"a2w-glass-{width}.json").write_text(json.dumps(record, indent=2, default=str))
                browser.close()
