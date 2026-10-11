"""PHILO-17 (phonepass) -- two phone-width defects, fenced AS RENDERED.

Through the real hub on an isolated HOME (the canvas week of
test_philo13_06_open_glass._seed: Priya's 1:1 is linked, so the People
drawer wears its `1:1 HH:MM` caption).

1. Rows hold still under the finger (393, touch). A recorder reads every
   drawn row's box on each animation frame. A row counts from the first
   frame it is drawn on the screen; after that every frame counts, also one
   that puts it below the fold. A row never moves more than 2 px; a row
   that leaves the page is not a move. CSS animations are off in the fence
   (the 4 px rise-in is motion, not layout). The cases:
   - the ⌘K list after `Payments` is typed (its reads in flight);
   - the cold ⌘K list with 11 Projects A-sorted, where the needs-you count
     lands late and promotes the 11th (`Payments ledger cutover`) over the
     section limit of 10;
   - the Room on `Payments ledger cutover`, opened from its row;
   - the same Room with one section's read (the connections read of Add
     sources) held 2.5 s, past the Room's first draw on the old timer;
   - the same Room with that read held 10 s, past the Room's 8 s cap: the
     body is drawn at the cap and Add sources fills its own place at the
     foot when the read lands.
2. The People caption touches nothing (1440 and 393): with a live agent
   flight (the Conductor wears its notch), the People icon's box (with its
   caption) intersects no other icon, lamp or count notch.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _room_opened, _settle
from .test_philo13_06_open_glass import _http, _seed
from .test_philo13_07_remembers_glass import SIZES, TOKEN, _Rig
from tests._evidence import evidence_dir

pytestmark = pytest.mark.chair_windows_open

SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-17/assets/phonepass-shots")
STILL = "*, *::before, *::after { animation: none !important; transition: none !important; }"
TOLERANCE = 2

# Rows keyed by element identity. First seen = drawn (visible, on screen);
# after that every frame counts wherever the row is (off screen too). A
# row with no box (gone, display none) is skipped for that frame.
RECORD_JS = r"""([sel, ms]) => { window.__rec = new Promise((resolve) => {
  const ids = new WeakMap(); let n = 0; const rows = {}; const t0 = performance.now();
  const H = window.innerHeight;
  const tick = () => {
    const now = Math.round(performance.now() - t0);
    for (const el of document.querySelectorAll(sel)) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      const y = Math.round(r.top);
      const k = ids.get(el);
      if (k === undefined) {
        if (r.top >= H || r.bottom <= 0 || getComputedStyle(el).visibility !== 'visible') continue;
        ids.set(el, ++n);
        const name = (el.getAttribute('data-testid') || el.id || (el.textContent || '').trim()).slice(0, 48);
        rows[n] = {name, first: y, at: now, worst: 0, last: y, worst_at: null};
      } else {
        const row = rows[k]; row.last = y;
        const d = Math.abs(y - row.first);
        if (d > row.worst) { row.worst = d; row.worst_at = now; }
      }
    }
    if (performance.now() - t0 < ms) requestAnimationFrame(tick); else resolve(Object.values(rows));
  };
  requestAnimationFrame(tick);
}); }"""
RESULT_JS = "() => window.__rec"

PALETTE_ROWS = "[id^=desk-palette-option-]"
ROOM_ROWS = ("#surface-project-memory .room-body button, #surface-project-memory .room-body li, "
             "#surface-project-memory .room-body [data-testid]")


def _moved(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if r["worst"] > TOLERANCE]


def _hold(page: Any, pattern: str, seconds: float) -> None:
    """Hold the first answer of one read for `seconds` (the request leaves
    at once; the answer waits). Later answers pass."""
    held = {"n": 0}

    def handle(route: Any) -> None:
        held["n"] += 1
        if held["n"] == 1:
            time.sleep(seconds)
        route.continue_()

    page.route(pattern, handle)


class TestRowsHoldStill(_Rig):
    def _open_room(self, page: Any, width: int, ms: int) -> list[dict[str, Any]]:
        self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
        page.locator("[aria-controls=desk-palette-listbox]").fill("Payments")
        opt = page.locator("[id='desk-palette-option-project.open.p-ledger']")
        opt.wait_for()
        page.wait_for_timeout(600)
        page.evaluate(RECORD_JS, [ROOM_ROWS, ms])
        self._press(page, opt, width)
        _room_opened(page)
        return page.evaluate(RESULT_JS)

    def test_palette_and_room_rows_do_not_move_under_the_finger_393(self) -> None:
        from playwright.sync_api import sync_playwright

        width = 393
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.add_style_tag(content=STILL)
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("[aria-controls=desk-palette-listbox]").wait_for()
                # His typing re-ranks the list (that is his own move); the
                # fence starts once the query is drawn, while its reads
                # (memory search, debounced 250 ms) are still in flight.
                page.locator("[aria-controls=desk-palette-listbox]").fill("Payments")
                page.evaluate(RECORD_JS, [PALETTE_ROWS, 2500])
                palette = page.evaluate(RESULT_JS)
                page.screenshot(path=str(SHOTS / "palette-393.png"))
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)

                room = self._open_room(page, width, 3500)
                _settle(page)
                page.screenshot(path=str(SHOTS / "room-393.png"))
                proof = {"palette": palette, "room": room}
                (SHOTS / "rows-393.json").write_text(json.dumps(proof, indent=1) + "\n")
                assert palette and room, proof
                assert any(r["name"] == "updates-verb" for r in room), "the Room drew no Draft update"
                assert not _moved(palette) and not _moved(room), {k: _moved(v) for k, v in proof.items()}
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.parametrize("hold", [2.5, 10.0], ids=["held-2s5", "held-past-cap"])
    def test_a_held_room_read_moves_no_drawn_row_393(self, hold: float) -> None:
        from playwright.sync_api import sync_playwright

        width = 393
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.add_style_tag(content=STILL)
                # Add sources' connections read (three provider rows, 368 px).
                _hold(page, "**/api/connections*", hold)
                room = self._open_room(page, width, int(hold * 1000) + 3500)
                _settle(page)
                tag = "2s5" if hold < 5 else "cap"
                page.screenshot(path=str(SHOTS / f"room-held-{tag}-393.png"))
                (SHOTS / f"room-held-{tag}-393.json").write_text(json.dumps(room, indent=1) + "\n")
                names = [r["name"] for r in room]
                assert "updates-verb" in names, names
                if hold > 8:
                    # drawn at the cap: Draft update before the held read landed,
                    # and the late section held its place with one line
                    verb = next(r for r in room if r["name"] == "updates-verb")
                    assert verb["at"] < hold * 1000, verb
                    # the late Sources section stands at the foot, its rows drawn
                    order = page.locator("#surface-project-memory [data-testid='room-add-sources']").evaluate(
                        "e => getComputedStyle(e.closest('.room-section-rise')).order")
                    assert order == "1", order
                    assert page.locator("#surface-project-memory [data-testid^='door-row-']").count(), \
                        "the held read never drew its rows"
                assert not _moved(room), _moved(room)
                assert not errors, errors
            finally:
                browser.close()

    def test_a_late_count_over_the_project_limit_moves_no_drawn_row_393(self) -> None:
        from playwright.sync_api import sync_playwright

        # 10 Projects A-sorted before `Payments ledger cutover`: it is the 11th
        # by name, and its count (1 open) ranks it first once the count lands.
        for i in range(1, 11):
            made = _http(self.base, "POST", "/api/projects", {"name": f"Aa project {i:02d}"})
            assert made.get("success"), made
        width = 393
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.add_style_tag(content=STILL)
                mode = {"counts": False}

                def needs(route: Any) -> None:
                    body = route.fetch().json()
                    body["items"] = []
                    body["coverage"] = []
                    # The late answer: `Payments ledger cutover` has 3 open.
                    body["projectCounts"] = {"p-ledger": 3} if mode["counts"] else {}
                    if mode["counts"]:
                        time.sleep(1.5)
                    route.fulfill(json=body)

                # Every read answers no counts until the palette opens (a
                # reload, so no count from before the route is held).
                page.route("**/api/desk/needs-you*", needs)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.locator(".desk-window-shell[aria-label='Needs you']").wait_for(timeout=15_000)
                page.wait_for_timeout(1500)
                page.add_style_tag(content=STILL)
                mode["counts"] = True
                self._press(page, page.locator("[aria-controls=desk-tool-shelf]").first, width)
                page.locator("#desk-palette-listbox").wait_for()
                page.evaluate(RECORD_JS, [PALETTE_ROWS, 4000])
                rows = page.evaluate(RESULT_JS)
                page.screenshot(path=str(SHOTS / "palette-limit-393.png"))
                (SHOTS / "palette-limit-393.json").write_text(json.dumps(rows, indent=1) + "\n")
                first = [r["name"] for r in rows if r["name"].startswith("desk-palette-option-project.open.")]
                assert "desk-palette-option-project.open.p-ledger" not in first[:10], first
                assert len(first) >= 10, first
                badge = page.locator("[id='desk-palette-option-project.open.p-ledger'] .desk-deck-badge")
                assert badge.count() and "OPEN" in badge.first.inner_text(), "the count never landed"
                assert not _moved(rows), _moved(rows)
                assert not errors, errors
            finally:
                browser.close()


CAPTION_JS = r"""() => {
  const box = (el) => { const r = el.getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height,
    name: el.closest('.desk-icon')?.getAttribute('data-object-id') + ' ' + el.className}; };
  const people = document.querySelector(".desk-screen .desk-icon[data-object-id='drawer:people']");
  const others = [...document.querySelectorAll('.desk-screen .desk-icon')].filter((e) => e !== people);
  return {people: people && box(people),
          caption: box(document.querySelector("[data-testid='desk-icon-caption-drawer:people']")),
          others: others.map(box),
          notches: [...document.querySelectorAll('.desk-screen .desk-icon-count, .desk-screen .desk-icon-lamp')]
            .filter((e) => !people.contains(e)).map(box)};
}"""


def _meets(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]


class TestCaptionTouchesNothing(_Rig):
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """The canvas week, plus live agent flights (the C4 Conductor seed),
        so the Conductor drawer under People wears its notch."""
        import holdspeak.agent_context as agent_context_pkg
        import holdspeak.delivery.factory_launch as factory_launch
        from holdspeak.agent_context import event_log

        from .test_philo14_c4_conductor_glass import _seed as conductor_seed

        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        state = tmp_path / "home" / ".holdspeak"
        state.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
        monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
        monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.ids = _seed(tmp_path / "home", base)
        conductor_seed(tmp_path / "home")
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_people_caption_overlaps_no_icon_or_notch(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.locator("[data-testid='desk-icon-caption-drawer:people']").wait_for(state="attached", timeout=20_000)
                conductor = page.locator(".desk-screen .desk-icon[data-object-id='drawer:conductor'] "
                                         ":is(.desk-icon-count, .desk-icon-lamp)")
                conductor.first.wait_for(state="attached", timeout=20_000)
                page.wait_for_timeout(600)
                _settle(page)
                found = page.evaluate(CAPTION_JS)
                (SHOTS / f"caption-{width}.json").write_text(json.dumps(found, indent=1) + "\n")
                people = found["people"]
                # The shot only: the windows stand over the screen, so they are
                # hidden for it (the boxes above were read with them drawn).
                page.add_style_tag(content=".desk-window-shell, .desk-window, .desk-pullout "
                                   "{ visibility: hidden !important; } .desk-screen { visibility: visible !important; }")
                if people:
                    x, y = max(0, people["x"] - 40), max(0, people["y"] - 130)
                    page.screenshot(path=str(SHOTS / f"caption-{width}.png"),
                                    clip={"x": x, "y": y, "width": min(320, width - x), "height": 400})
                assert people and found["caption"]["h"] > 0, found
                assert any("drawer:conductor" in n["name"] for n in found["notches"]), found["notches"]
                cap = found["caption"]
                assert cap["y"] + cap["h"] <= people["y"] + people["h"] + 0.5, found
                hits = [o for o in found["others"] + found["notches"] if _meets(people, o)]
                assert not hits, {"people": people, "touches": hits}
                assert not errors, errors
            finally:
                browser.close()
