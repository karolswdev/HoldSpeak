"""PHILO-13-14 (C4) -- a palette that knows his week and does verbs, on glass.

Through the real hub on an isolated HOME, at 1440x900 (mouse, keyboard) and
393x852 (touch). The week is minted by the real producers: the Chair canvas
week (test_philo13_11_chair_glass._seed: the projects, the decisions, the
meetings, Avery / Jordan / Sam / Priya Nair in the People store), the fresh
Desk seed (PUT /api/setup/onboarding applies it: the `People & vocabulary`
note), three thoughts through the notes route (each titled `Thought`, one
body names `Kafka offsets`), and a REAL FILE destination in a scratch folder.

One assert per acceptance line:

* `Priya` -> the top row is her (PEOPLE); one press opens People on her.
* `Prep 1:1 with Priya Nair` -> People on her, on Prep.
* a word inside a thought (`kafka`) -> that thought; one press opens it.
* `send` -> `Send <front document> to Team updates` leads; the pick opens the
  window's SEND well on Team updates with the hub's preview in view; zero
  `channel_sends` rows and zero new `kernel_operations` rows until he
  presses Send; his press shows the outcome the hub records (SAVED, one
  `sent` row, the file in the folder).
* `Draft update for Payments ledger cutover` -> the Room in its Update posture.
* `People` -> `Open People` first, above the `People & vocabulary` note; one
  Escape closes the shelf with the query typed.
* H-C4 (Astra #756): a meeting saved by the real meeting producer, titled
  `Vendor roadmap review` (no name in its title or its text), whose speakers
  are Dana Okafor and Me, is found by `Dana` through the list row's
  `attendees`; one press opens it. Red before #756 (the list row carried no
  attendees), green after.

The on-glass reader reads the open shelf and the SEND well: zero clipped
text, zero overlaps. Shots go to
pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-14-shots/ under
HOLDSPEAK_EVIDENCE_WRITE=1 (``.tmp/evidence-shots/`` otherwise).
"""
from __future__ import annotations

import json
import shutil
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle, park_builtin_folder
from .test_philo13_11_chair_glass import _seed as _canvas_seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the palette glass needs Playwright")

TOKEN = "philo13-14-palette"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-14-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
FREEZE = "pullout:decision:d-freeze"
ROOM = "surface-project-memory"
NEEDLE = "Ask Jordan about the Kafka offsets before the cutover."


def _http(base: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        base + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"authorization": f"Bearer {TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}


class TestPaletteKnowsHisWeek:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        park_builtin_folder()  # the desk these boards were drawn on (glass_infra.park_builtin_folder)
        self.base, self.home = base, tmp_path / "home"
        _canvas_seed(self.home)
        _http(base, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
        self.people = {r["display_name"]: r["id"] for r in _http(base, "GET", "/api/people/relationships")["relationships"]}
        self.thoughts = []
        for body in ("Lunch on Friday with the team.", NEEDLE, "Book the offsite room."):
            self.thoughts.append(_http(base, "POST", "/api/notes", {"title": "Thought", "body_markdown": body})["note"]["id"])
        # A short scratch folder (the well prints the path; pytest's tmp path is long).
        self.scratch = Path(tempfile.mkdtemp(prefix="p13c4-", dir="/tmp"))
        self.folder = self.scratch / "Team updates"
        self.folder.mkdir()
        self.dest = _http(base, "POST", "/api/channels/destinations",
                          {"name": "Team updates", "channel": "file", "folder": str(self.folder)})["destination"]["id"]
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            server.stop()
            shutil.rmtree(self.scratch, ignore_errors=True)

    # ── the rig ──────────────────────────────────────────────────────────

    def _sends(self, ref: str) -> list[dict[str, Any]]:
        """The hub's own send rows for one document, read from its DB."""
        with self.db._connection() as conn:
            rows = conn.execute("SELECT id, state, proof_json FROM channel_sends WHERE document_ref = ?", (ref,)).fetchall()
        return [{"id": r[0], "state": r[1], "proof": json.loads(r[2] or "{}")} for r in rows]

    def _ops(self) -> list[tuple[str, str]]:
        with self.db._connection() as conn:
            return [(r[0], r[1]) for r in conn.execute(
                "SELECT operation_id, name FROM kernel_operations ORDER BY created_at").fetchall()]

    def _press(self, loc: Any, ms: int = 700) -> None:
        loc = loc.first
        loc.scroll_into_view_if_needed()
        if self.phone:
            b = loc.bounding_box()
            assert b, "nothing to tap"
            self.page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        else:
            loc.click()
        self.page.wait_for_timeout(ms)

    def _home(self, open_ref: str | None = None) -> None:
        page = self.page
        page.goto(f"{self.base}/?token={TOKEN}" + (f"&open={open_ref}" if open_ref else ""), wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1500)

    def _query(self, q: str) -> list[dict[str, Any]]:
        """Gesture 1: open the palette (⌘K at 1440, the Search tap at 393); then type."""
        page = self.page
        if page.locator("#desk-tool-shelf").count() == 0:
            if self.phone:
                self._press(page.locator("button[aria-controls=desk-tool-shelf]"), 500)
            else:
                page.keyboard.press("Meta+k")
                page.wait_for_timeout(400)
        box = page.locator("input[aria-controls=desk-palette-listbox]")
        box.wait_for(timeout=T)
        box.fill(q)
        page.wait_for_timeout(900)
        return self._rows()

    def _rows(self) -> list[dict[str, Any]]:
        return self.page.evaluate("""() => [...document.querySelectorAll('#desk-palette-listbox [role=option]')]
            .map((o) => ({id: o.id.replace('desk-palette-option-', ''), text: o.innerText.replace(/\\s+/g, ' ').trim(),
                          selected: o.getAttribute('aria-selected') === 'true'}))""")

    def _run_top(self, rows: list[dict[str, Any]]) -> None:
        """Gesture 2: Enter runs the top hit (1440); a tap on it (393)."""
        if self.phone:
            self._press(self.page.locator(f"[id='desk-palette-option-{rows[0]['id']}']"), 1200)
        else:
            self.page.keyboard.press("Enter")
            self.page.wait_for_timeout(1200)

    def _glass(self, sel: str, board: str) -> None:
        _settle(self.page)
        f = _rendered_text_faults(self.page, sel, on_glass=True)
        assert f["scopes"], f"{board}-{self.width}: nothing visible at {sel}"
        assert not f["clipped"] and not f["overlaps"], f"{board}-{self.width} {sel}: {f}"
        self.read += 1

    def _shot(self, board: str) -> None:
        _settle(self.page)
        self.page.screenshot(path=str(SHOTS / f"{board}-{self.width}.png"))

    def _front(self, title: str, text: str = "") -> None:
        self.page.wait_for_function(
            """([title, text]) => [...document.querySelectorAll('.desk-window-shell, .desk-window, .desk-pullout')]
                .some((w) => w.classList.contains('is-front') && (w.getAttribute('aria-label') || '').includes(title)
                  && (w.innerText || '').includes(text))""", arg=[title, text], timeout=T)

    def _lens(self) -> str | None:
        return self.page.evaluate("""() => { const t = document.querySelector('.people-lenses [role=tab][aria-selected=true]');
            return t ? t.textContent.trim() : null; }""")

    def _in_view(self, sel: str, board: str) -> None:
        ok = self.page.evaluate("""(sel) => { const e = [...document.querySelectorAll(sel)].find((x) => x.checkVisibility());
            if (!e) return 'absent'; const r = e.getBoundingClientRect();
            if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth) return 'off screen ' + JSON.stringify(r);
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return hit && (e.contains(hit) || hit.contains(e)) ? 'ok' : 'covered by ' + (hit?.className || hit?.tagName); }""", sel)
        assert ok == "ok", f"{board}-{self.width} {sel}: {ok}"

    # ── the case ─────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_palette_knows_his_week_and_does_verbs(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        self.width, self.phone, self.read = width, width <= 720, 0
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                      has_touch=self.phone, reduced_motion="reduce")
            page = self.page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                self._walk()
                assert self.read >= 8, self.read
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_meeting_is_found_by_an_attendee(self, width: int) -> None:
        from datetime import datetime, timedelta

        from holdspeak.meeting_session import MeetingState, TranscriptSegment
        from playwright.sync_api import sync_playwright

        start = (datetime.now() - timedelta(hours=5)).replace(microsecond=0)
        self.db.meetings.save_meeting(MeetingState(
            id="m-vendor", started_at=start, ended_at=start + timedelta(minutes=30), title="Vendor roadmap review",
            segments=[TranscriptSegment(text="The second quarter plan holds.", speaker="Dana Okafor", start_time=1.0, end_time=4.0),
                      TranscriptSegment(text="Agreed, ship the pilot.", speaker="Me", start_time=4.0, end_time=6.0)],
            intel_status="disabled"))
        row = next(m for m in _http(self.base, "GET", "/api/meetings?limit=24")["meetings"] if m["id"] == "m-vendor")
        assert "dana" not in json.dumps({k: v for k, v in row.items() if k != "attendees"}).lower(), row
        self.width, self.phone, self.read = width, width <= 720, 0
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                      has_touch=self.phone, reduced_motion="reduce")
            page = self.page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                self._home()
                rows = self._query("Dana")
                assert rows and rows[0]["id"] == "meeting:m-vendor", (row.get("attendees"), rows)
                assert "Vendor roadmap review" in rows[0]["text"] and "MEETING" in rows[0]["text"], rows[0]
                self._glass("#desk-tool-shelf", "C4-7")
                self._shot("C4-7-attendee-finds-meeting")
                self._run_top(rows)
                self._front("Vendor roadmap review")
                assert page.locator("#desk-tool-shelf").count() == 0
                self._shot("C4-7b-attendee-meeting-window")
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()

    def _walk(self) -> None:
        page = self.page
        priya = self.people["Priya Nair"]

        # 1. `Priya` -> her window (2 gestures: the palette, the top row).
        self._home()
        rows = self._query("Priya")
        assert rows and rows[0]["id"] == f"people:{priya}" and rows[0]["selected"], rows
        assert "Priya Nair" in rows[0]["text"] and "PERSON" in rows[0]["text"], rows[0]
        self._glass("#desk-tool-shelf", "C4-1")
        self._shot("C4-1-priya-row")
        self._run_top(rows)
        self._front("People", "Priya Nair")
        assert page.locator("#desk-tool-shelf").count() == 0
        self._shot("C4-1b-priya-window")

        # 2. `Prep 1:1 with Priya Nair` -> her window on Prep.
        self._home()
        rows = self._query("prep priya")
        prep = [r for r in rows if r["id"] == f"week.prep.{priya}"]
        assert prep and "Prep 1:1 with Priya Nair" in prep[0]["text"] and rows[0]["id"] == prep[0]["id"], rows
        self._glass("#desk-tool-shelf", "C4-2")
        self._shot("C4-2-prep-row")
        self._run_top(rows)
        self._front("People", "Priya Nair")
        page.wait_for_function("() => document.querySelector('.people-lenses [role=tab][aria-selected=true]')?.textContent.trim() === 'Prep'",
                               timeout=T)
        self._shot("C4-2b-prep-window")

        # 3. A word inside a thought finds it (three thoughts, all titled `Thought`).
        self._home()
        rows = self._query("kafka")
        needle = f"note:{self.thoughts[1]}"
        assert rows and rows[0]["id"] == needle, rows
        assert not [r for r in rows if r["id"] in (f"note:{self.thoughts[0]}", f"note:{self.thoughts[2]}")], rows
        self._glass("#desk-tool-shelf", "C4-3")
        self._shot("C4-3-thought-word")
        self._run_top(rows)
        self._front("Kafka offsets", "Kafka offsets")   # the window is named by the note's first words
        self._shot("C4-3b-thought-window")

        # 4. `send` -> Send <front document> to Team updates; the pick opens the preview; nothing sent.
        self._home("decision:d-freeze")
        page.locator(f"[id='{FREEZE}']").wait_for(timeout=T)
        ref = "desk_decision:d-freeze"
        ops_before = self._ops()
        rows = self._query("send")
        assert rows and rows[0]["id"] == f"week.send.{self.dest}", rows
        assert rows[0]["text"].startswith("▸ Send Freeze the old ledger on Nov 5 to Team updates") or \
            "Send Freeze the old ledger on Nov 5 to Team updates" in rows[0]["text"], rows[0]
        # The destination he picks is whole on the glass (the row wraps; no ellipsis).
        cut = page.evaluate("""(id) => { const l = document.getElementById(id)?.querySelector('.desk-deck-label');
            return l ? {sw: l.scrollWidth, cw: l.clientWidth, sh: l.scrollHeight, ch: l.clientHeight} : null; }""",
                            f"desk-palette-option-week.send.{self.dest}")
        assert cut and cut["sw"] <= cut["cw"] + 1 and cut["sh"] <= cut["ch"] + 1, cut
        self._glass("#desk-tool-shelf", "C4-4")
        self._shot("C4-4-send-row")
        self._run_top(rows)
        well = f"[id='{FREEZE}'] [data-testid=send-open][data-destination='Team updates']"
        page.locator(f"{well} [data-testid=send-preview]").wait_for(timeout=T)
        page.wait_for_function(f"() => document.querySelector(\"[id='{FREEZE}'] [data-testid=send-well]\")?.dataset.arrived === 'true'",
                               timeout=T)
        page.wait_for_timeout(900)
        self._in_view(f"{well} [data-testid=send-preview-field] dd", "C4-4b")
        self._in_view(f"{well} [data-testid=send-verbs] .btn--primary", "C4-4b")
        assert self._sends(ref) == [], self._sends(ref)
        new_ops = [o for o in self._ops() if o not in ops_before]
        assert new_ops == [], new_ops
        self._glass(f"[id='{FREEZE}'] [data-testid=send-well]", "C4-4b")
        self._shot("C4-4b-send-preview-in-view")
        # His press: the outcome the hub records.
        self._press(page.locator(f"{well} [data-testid=send-verbs] .btn--primary"), 1800)
        for _ in range(100):
            rows_db = self._sends(ref)
            if rows_db and rows_db[0]["state"] == "sent":
                break
            page.wait_for_timeout(100)
        assert len(rows_db) == 1 and rows_db[0]["state"] == "sent", rows_db
        assert Path(rows_db[0]["proof"]["path"]).resolve().parent == self.folder.resolve()
        assert Path(rows_db[0]["proof"]["path"]).is_file()
        receipt = page.locator(f"[id='{FREEZE}'] [data-testid=send-history] [data-testid=history-row]").first
        receipt.wait_for(timeout=T)
        text = receipt.inner_text()
        assert "Team updates" in text and "SAVED" in text, text
        receipt.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        self._glass(f"[id='{FREEZE}'] [data-testid=send-well]", "C4-4c")
        self._shot("C4-4c-sent-receipt")

        # 5. `Draft update for <project>` -> the Room in its Update posture.
        self._home()
        rows = self._query("draft update payments")
        assert rows and rows[0]["id"] == "week.draft-update.p-ledger", rows
        assert "Draft update for Payments ledger cutover" in rows[0]["text"], rows[0]
        self._glass("#desk-tool-shelf", "C4-5")
        self._shot("C4-5-draft-update-row")
        self._run_top(rows)
        page.locator(f"[id='{ROOM}'] [data-testid=update-posture][data-phase=list]").wait_for(timeout=T)
        self._in_view(f"[id='{ROOM}'] [data-testid=update-verb-draft-deterministic]", "C4-5b")
        self._glass(f"[id='{ROOM}'] [data-testid=update-posture]", "C4-5b")
        self._shot("C4-5b-room-update-posture")

        # 6. `People` -> the People app first, above the note; one Escape closes the shelf.
        self._home()
        rows = self._query("People")
        ids = [r["id"] for r in rows]
        assert ids[0] == "desk.open-people" and rows[0]["selected"], rows
        assert "note:hs-seed-people-vocabulary" in ids and ids.index("desk.open-people") < ids.index("note:hs-seed-people-vocabulary"), ids
        self._glass("#desk-tool-shelf", "C4-6")
        self._shot("C4-6-people-app-first")
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        assert page.locator("#desk-tool-shelf").count() == 0, "one Escape left the shelf open"
        self._shot("C4-6b-one-escape-closed")
