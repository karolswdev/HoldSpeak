"""HS-200-13 -- recall on glass, and the chain across a restart.

The three ratified boards (`assets/mockups/P5Recall`, `P5RecallPhone`,
`P5RecallQuiet`) against a REAL booted hub on an isolated HOME, at 1440 and
393, in the shape of `test_hs200_attention_glass.py`:

  recall  -- Monday's meeting (09-07) confirmed a decision that supersedes
             Saturday's (09-02) and left one commitment.  Desk memory is
             opened from the arrival, `freeze window` is searched: the
             CURRENT decision comes back first, accented, with its rationale,
             its source (`MTG 09-07 · 11:31`), its Project and `Carry into
             brief` (the one filled primary); the Saturday one sits under it
             dimmed, `SUPERSEDED BY DEC 09-07`; the commitment is OWED with
             `OWNER · UNKNOWN` / `DUE · UNKNOWN` typed and `Name an owner` as
             its one verb.  **The minute is measured**: from the arrival to
             `CARRIED`, and printed (`[hs200-13] recall minute …`); the
             target is 60 s on seeded data (design Addendum 4, Q4).
  quiet   -- `unfindablequasar`: `Nothing matches`, one true line, the five
             filters kept, no `Clear`.
  restart -- confirm from a meeting, carry, `needs-you` read once; the hub
             is stopped and a SECOND hub boots on the same HOME; recall finds
             the current decision with `carried: true`; the carry mark is
             readable by the manifest builder's seam (`pending_carries`) and
             resolves to the current record; the last-known observation is
             still there (AC5).

Every verb is the library Button (no raw <button>), one filled primary per
face, every interactive element inside the viewport at 393, at least three
type steps, no counter of zero.

Shots to phase-200-the-working-practice/assets/story-13-shots/ (only with
HOLDSPEAK_WRITE_SHOTS=1: shots are tracked evidence).
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

pytest.importorskip("playwright.sync_api", reason="Continuity glass needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-13-shots"
WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS") == "1"

TOKEN = "hs200-continuity"
MINUTE_TARGET_S = 60.0

SAT, SUN = "2026-09-02", "2026-09-07"
OLD_TEXT = "Freeze window is Saturday 02:00"
NEW_TEXT = "Freeze window is Sunday 02:00, not Saturday"
NEW_WHY = "Payments cannot drain the queue before 02:00 on a weekday."
CMT_TEXT = "Priya confirms the freeze window"

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]


# ── seeds (the product's own seams inside the isolated HOME) ─────────


def _create_project(page: Any, name: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-13 browser proof.",
        "command_id": f"hs200-13-{name.lower().replace(' ', '-')}-{int(time.time() * 1000)}",
    }, token=TOKEN)
    return created["project"]["id"]


def _seed_meeting(meeting_id: str, day: str, title: str) -> None:
    """A finalized meeting at 11:00 with the board's turns at its minutes."""
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, 3600, 'complete', 'finalized', 'desktop')",
            (meeting_id, f"{day}T11:00:00", f"{day}T12:00:00", title),
        )
        conn.execute("DELETE FROM segments WHERE meeting_id = ?", (meeting_id,))
        for start, text in ((0.0, "Let's start with the cut-over sequencing for the payments platform"),
                            (1080.0, "Cut-over runs on the read replica first, then we flip writes"),
                            (1860.0, NEW_TEXT), (1980.0, CMT_TEXT)):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, 'Marek', ?, ?)",
                (meeting_id, text, start, start + 60.0),
            )


def _propose(meeting_id: str, project_id: str, kind: str, text: str, *,
             segment_index: int, rationale: str | None = None) -> str:
    from holdspeak.db import get_database
    prop = get_database().proposals.create_proposal(
        meeting_id=meeting_id, project_id=project_id, kind=kind, text=text,
        source_plugin="decision_capture" if kind == "decision" else "action_owner_enforcer",
        segment_timestamp=1860.0, span_start=1860.0, span_end=1920.0,
        segment_index=segment_index, support="supported", rationale=rationale,
        model_host="192.168.1.43",
    )
    assert prop is not None
    return prop.id


def _seed_chain(page: Any) -> dict[str, Any]:
    """The board's story through the REAL routes: two meetings linked to the
    Room, three proposals confirmed, Saturday superseded by Sunday."""
    pid = _create_project(page, "Q4 Platform")
    _seed_meeting("m-sat", SAT, "Cut-over planning")
    _seed_meeting("m-sun", SUN, "Architecture review")
    for mid in ("m-sat", "m-sun"):
        _api(page, "POST", f"/api/projects/{pid}/meetings/{mid}", {}, token=TOKEN)
    old = _api(page, "POST", f"/api/proposals/{_propose('m-sat', pid, 'decision', OLD_TEXT, segment_index=2, rationale='Least traffic on Saturday')}/confirm", {}, token=TOKEN)
    new = _api(page, "POST", f"/api/proposals/{_propose('m-sun', pid, 'decision', NEW_TEXT, segment_index=2, rationale=NEW_WHY)}/confirm", {}, token=TOKEN)
    cmt = _api(page, "POST", f"/api/proposals/{_propose('m-sun', pid, 'action', CMT_TEXT, segment_index=3)}/confirm", {}, token=TOKEN)
    sealed = _api(page, "POST", f"/api/decision-records/{old['decision_record_id']}/supersede",
                  {"successor_id": new["decision_record_id"], "reason": "moved to Sunday"}, token=TOKEN)
    assert sealed["lifecycle"] == "superseded", sealed
    return {"project_id": pid, "old": old, "new": new, "cmt": cmt}


# ── glass helpers ────────────────────────────────────────────────────


def _arrive(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _open_desk_memory(page: Any) -> None:
    """Go -> Desk memory: the surface staged with NO scope."""
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          localStorage.removeItem("hs.desk-memory.recall.v1");
          sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}));
        }""",
        ["open-project-memory"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=15000)
    page.get_by_role("searchbox", name="Search the Desk").wait_for(timeout=10000)
    _settle(page)


def _search(page: Any, query: str) -> None:
    page.get_by_role("searchbox", name="Search the Desk").fill(query)
    page.locator(".desk-surface-window").get_by_role("button", name="Search desk memory", exact=True).click()
    page.get_by_test_id("recall-results").wait_for(timeout=10000)
    _settle(page)


def _shot(page: Any, name: str, width: int) -> Path | None:
    if not WRITE_SHOTS:
        return None
    SHOTS.mkdir(parents=True, exist_ok=True)
    # The results region took focus (the design's focus return) and scrolled
    # the head out; a shot is read beside its board from the top of the face.
    page.evaluate("""() => { for (const el of document.querySelectorAll('.desk-surface-body')) el.scrollTop = 0; }""")
    page.mouse.move(2, 2)
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _primaries(page: Any) -> list[str]:
    return page.evaluate("""() => [...document.querySelectorAll('.desk-surface-window .btn--primary')]
        .map(b => (b.textContent || '').trim())""")


def _raw_buttons(page: Any) -> list[str]:
    """Every <button> in the window that is not the library Button, the mic,
    a ledger line, or a library Disclosure trigger."""
    return page.evaluate("""() => {
        // The face and its footer; the frame's lights and wings are the
        // shell's species (the hs526 rig scopes the same way).
        const body = document.querySelector('.desk-surface-window .desk-surface-body, .desk-surface-body');
        if (!body) return ['no surface body'];
        const foot = document.querySelector('.surface-footer-layout');
        const raw = [];
        const all = [...body.querySelectorAll('button'), ...(foot ? foot.querySelectorAll('button') : [])];
        for (const btn of all) {
            const cls = btn.className || '';
            if (!cls.includes('btn') && !cls.includes('desk-mic') &&
                !cls.includes('surface-ledger-line') && !cls.includes('surface-row-open') &&
                !cls.includes('surface-disclosure-trigger') && !cls.includes('desk-window-light'))
                raw.push(cls + ' :: ' + (btn.textContent || '').trim());
        }
        return raw;
    }""")


def _overflowing(page: Any, width: int) -> list[str]:
    """Every interactive element of the face whose right edge passes the
    viewport (per element: scrollWidth alone cannot see a clipped ancestor)."""
    return page.evaluate("""(width) => {
        const out = [];
        const win = document.querySelector('.desk-surface-window') || document;
        const sel = 'button, a, input, [role="button"], [role="group"]';
        for (const el of win.querySelectorAll(sel)) {
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) continue;
            if (r.right > width + 0.5) out.push((el.className || el.tagName) + ' :: ' + (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 40) + ' right=' + r.right.toFixed(1));
        }
        return out;
    }""", width)


def _type_steps(page: Any) -> list[int]:
    return page.evaluate("""() => {
        const root = document.querySelector('[data-testid="desk-memory-body"]');
        const sizes = new Set();
        const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (walk.nextNode()) {
            const text = (walk.currentNode.textContent || '').trim();
            const parent = walk.currentNode.parentElement;
            if (parent && text) sizes.add(Math.round(parseFloat(getComputedStyle(parent).fontSize)));
        }
        return [...sizes].sort((a, b) => a - b);
    }""")


def _zero_counters(page: Any) -> list[str]:
    return page.evaluate("""() => [...document.querySelectorAll('[data-testid="desk-memory-body"] .surface-token, [data-testid="desk-memory-body"] h3')]
        .map(n => (n.textContent || '').trim()).filter(t => /(^|\\s)0(\\s|$)/.test(t))""")


def _canon(page: Any, width: int) -> None:
    assert _raw_buttons(page) == [], _raw_buttons(page)
    assert len(_primaries(page)) <= 1, _primaries(page)
    assert _zero_counters(page) == [], _zero_counters(page)
    steps = _type_steps(page)
    assert len(steps) >= 3, steps
    page.mouse.move(2, 2)
    assert page.evaluate("document.documentElement.scrollWidth") <= width
    over = _overflowing(page, width)
    assert over == [], f"elements past the viewport at {width}: {over}"


# ── legs ─────────────────────────────────────────────────────────────


def _run_recall(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 1100 if width > 393 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            chain = _seed_chain(page)

            # ── beat 6, measured: from the arrival to CARRIED ──
            t0 = time.monotonic()
            page.reload(wait_until="load")
            _normal_chair(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _open_desk_memory(page)
            assert page.get_by_test_id("recall-empty-token").text_content() == "SEARCH THE DESK"
            assert page.get_by_test_id("recall-display").count() == 0, "no display line before a search"
            _search(page, "freeze window")
            cards = page.locator("[data-testid='recall-card']")
            assert cards.count() == 2, cards.count()
            assert cards.nth(0).get_attribute("data-state") == "current"
            assert cards.nth(1).get_attribute("data-state") == "superseded"
            carry = page.get_by_role("button", name="Carry into brief", exact=True)
            assert carry.count() == 1
            carry.click()
            page.locator("[data-testid='recall-carry'][data-carried]").wait_for(timeout=10000)
            minute = time.monotonic() - t0
            print(f"[hs200-13] recall minute @{width}: {minute:.1f} s (target {MINUTE_TARGET_S:.0f} s)")
            assert minute < MINUTE_TARGET_S, f"the recall minute took {minute:.1f} s"
            if WRITE_SHOTS:
                SHOTS.mkdir(parents=True, exist_ok=True)
                facts_path = SHOTS / "recall-minute.json"
                facts = json.loads(facts_path.read_text()) if facts_path.exists() else {}
                facts[str(width)] = {"seconds": round(minute, 1), "target_seconds": MINUTE_TARGET_S,
                                     "measured_at": datetime.now().isoformat(timespec="seconds"),
                                     "beats": ["arrival", "open Desk memory", "search `freeze window`",
                                               "current + superseded on the face", "Carry into brief -> CARRIED"]}
                facts_path.write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n")

            # ── the face against the board ──
            # 1 current + 1 superseded + 1 owed + the two meetings whose turns
            # say "freeze window" (the board's `3 remembered` has no meeting
            # rows behind it; this seed has two, drawn under MEETINGS 2).
            assert (page.get_by_test_id("recall-display").text_content() or "").strip() == "5 remembered"
            assert page.get_by_test_id("recall-display").get_attribute("data-accent") == "true"
            assert page.get_by_test_id("recall-ref-token").text_content() == "REF · FREEZE WINDOW"
            assert (page.get_by_test_id("recall-searched-token").text_content() or "").startswith("SEARCHED ")
            current = cards.nth(0)
            assert (current.get_by_test_id("recall-card-title").text_content() or "") == NEW_TEXT
            assert [c.text_content() for c in current.get_by_test_id("recall-axis").all()] == ["DECISION", "SUPPORTED", "ACCEPTED"]
            assert current.get_by_test_id("recall-dec-token").text_content() == "DEC 09-07"
            assert current.get_by_test_id("recall-rationale").text_content() == NEW_WHY
            assert current.get_by_test_id("recall-source-token").text_content() == "MTG 09-07 · 11:31"
            assert current.get_by_role("button", name="Open source — MTG 09-07").count() == 1
            assert current.get_by_role("group", name="Project").get_by_role("button", name="Open the Project — Q4 Platform").count() == 1
            assert (page.get_by_test_id("recall-carry").text_content() or "").strip() == "CARRIED"
            superseded = cards.nth(1)
            assert (superseded.get_by_test_id("recall-card-title").text_content() or "") == OLD_TEXT
            assert superseded.get_by_test_id("recall-superseded-by").text_content() == "SUPERSEDED BY DEC 09-07"
            assert superseded.get_by_test_id("recall-dec-token").text_content() == "DEC 09-02"
            assert float(superseded.evaluate("el => getComputedStyle(el).opacity")) < 1.0
            assert superseded.get_by_role("button", name="Carry into brief").count() == 0
            # OWED: the commitment, its unknowns typed, ONE verb.
            owed = page.get_by_test_id("recall-owed-row")
            assert owed.count() == 1
            assert owed.get_by_test_id("recall-owed-title").text_content() == CMT_TEXT
            assert owed.get_by_test_id("recall-due-token").text_content() == "DUE · UNKNOWN"
            assert owed.get_by_test_id("recall-owner-token").text_content() == "OWNER · UNKNOWN"
            assert (owed.get_by_test_id("recall-owed-verb").text_content() or "").strip() == "Name an owner"
            assert owed.get_by_role("button", name="Mark done — " + CMT_TEXT).count() == 0
            # Sections carry real counts; no zero anywhere.
            body = page.get_by_test_id("desk-memory-body").text_content() or ""
            assert "CURRENT 1" in body and "SUPERSEDED 1" in body and "OWED 1" in body and "MEETINGS 2" in body
            # Canon: the one filled primary is spent (CARRIED reads secondary);
            # the library Button everywhere; inside the viewport at both widths.
            _canon(page, width)
            _shot(page, "recall", width)

            # The wire says the same thing the face does (AC1/AC2 by the shape).
            wire = _api(page, "GET", "/api/memory/recall?query=freeze+window", token=TOKEN)
            assert [c["id"] for c in wire["current"]] == [chain["new"]["decision_record_id"]]
            assert [c["id"] for c in wire["superseded"]] == [chain["old"]["decision_record_id"]]
            assert wire["current"][0]["carried"] is True
            assert [r["id"] for r in wire["owed"]] == [chain["cmt"]["commitment_id"]]

            # Name an owner: the well unfolds under the row (no modal), saves
            # through the follow-through verb, and the verb becomes Set a date.
            owed.get_by_test_id("recall-owed-verb").click()
            page.get_by_test_id("recall-owed-well").wait_for(timeout=5000)
            assert page.get_by_role("dialog").count() == 0
            page.get_by_role("textbox", name="Owner").fill("Priya")
            page.get_by_role("button", name="Save owner — " + CMT_TEXT).click()
            page.locator("[data-testid='recall-owed-row'][data-next-action='set_date']").wait_for(timeout=10000)
            _settle(page)
            assert page.get_by_test_id("recall-owner-token").count() == 0
            status = _api(page, "GET", "/api/follow-through/board", token=TOKEN)
            owed_cards = [c for lane in status.values() if isinstance(lane, list) for c in lane
                          if c.get("id") == chain["cmt"]["action_item_id"]]
            assert owed_cards and owed_cards[0]["status"] in ("open", "pending"), "naming an owner did not complete it (AC4)"
            _canon(page, width)
            _shot(page, "recall-owed-named", width)

            # ── the miss: filters kept, one true line, no Clear ──
            _search(page, "unfindablequasar")
            assert (page.get_by_test_id("recall-display").text_content() or "").strip() == "Nothing matches"
            assert page.get_by_test_id("recall-display").get_attribute("data-accent") is None
            assert page.get_by_test_id("recall-miss").text_content().strip() == "▤One project searched, it does not hold this"
            assert page.get_by_role("group", name="Filter the memory").get_by_role("button").count() == 5
            assert page.get_by_role("button", name="Clear").count() == 0
            assert page.locator("[data-testid='recall-card']").count() == 0
            _canon(page, width)
            _shot(page, "recall-quiet", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    from playwright.sync_api import sync_playwright
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    chain: dict[str, Any] = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            chain = _seed_chain(page)
            carried = _api(page, "POST", f"/api/decision-records/{chain['new']['decision_record_id']}/carry", {}, token=TOKEN)
            assert carried["replayed"] is False and carried["project_id"] == chain["project_id"]
            # One needs-you read: the durable last-known store remembers the Room.
            first = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            assert any(i["source"] == "commitment" and i["title"] == CMT_TEXT for i in first["items"]), first["items"]
            row = next(i for i in first["items"] if i["source"] == "commitment")
            assert row["nextAction"] == "name_owner" and row["actionItemId"] == chain["cmt"]["action_item_id"]
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

    # ── the SECOND hub on the same HOME (the same database file) ──
    server2, url2 = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url2}/?token={TOKEN}", wait_until="load")
            wire = _api(page, "GET", "/api/memory/recall?query=freeze+window", token=TOKEN)
            assert [c["id"] for c in wire["current"]] == [chain["new"]["decision_record_id"]], wire["current"]
            assert wire["current"][0]["carried"] is True, "the carry mark did not survive the restart"
            assert wire["current"][0]["rationale"] == NEW_WHY
            assert [c["id"] for c in wire["superseded"]] == [chain["old"]["decision_record_id"]]
            assert [r["id"] for r in wire["owed"]] == [chain["cmt"]["commitment_id"]]

            # The seam HS-200-11's manifest builder reads, on the restarted hub.
            from holdspeak.db import get_database
            from holdspeak.services.brief_carry import pending_carries
            from holdspeak.services.needs_you_aggregate import LastKnownStore
            marks = pending_carries(get_database(), chain["project_id"])
            assert len(marks) == 1, marks
            assert marks[0]["current_record_id"] == chain["new"]["decision_record_id"]
            assert marks[0]["ref"] == marks[0]["current_ref"] and marks[0]["superseded"] is False
            assert marks[0]["text"] == NEW_TEXT and marks[0]["rationale"] == NEW_WHY
            remembered = LastKnownStore(db_factory=get_database).recall(f"project:{chain['project_id']}")
            assert remembered is not None and any(i.get("source") == "commitment" for i in remembered["items"]), remembered

            # And a later preparation session still sees the commitment owed
            # on the arrival, with its next action.
            again = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            assert any(i["source"] == "commitment" and i["nextAction"] == "name_owner" for i in again["items"]), again["items"]
            _assert_clean(page, errors)
            browser.close()
    finally:
        server2.stop()


@pytest.mark.timeout(420)
class TestContinuityGlass:
    def test_recall_1440(self, tmp_path, monkeypatch) -> None:
        _run_recall(tmp_path, monkeypatch, 1440)

    def test_recall_393(self, tmp_path, monkeypatch) -> None:
        _run_recall(tmp_path, monkeypatch, 393)

    def test_chain_survives_a_hub_restart(self, tmp_path, monkeypatch) -> None:
        _run_restart(tmp_path, monkeypatch)
