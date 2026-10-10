"""PHILO-17 (lane windows) -- windows open well and come back as themselves.

The usability walks (docs/internal/philo/phase-17/USABILITY-INVENTORY.md U24,
U28): every app opened at (24,72) on top of the Chair's icon column; two in a
row sat exactly on each other; after a reload a project Room came back as
"Desk memory" and windows jumped. Through ONE real hub on an isolated HOME,
the built bundle, three browser contexts (three views, three localStorages):

  W1 context A (1440) opens Meetings and People from the Dock: neither sits on
     the left icon column, the two do not sit on each other, and Meetings opens
     wide enough for its record (U24).
  W2 A drags Meetings by the empty part of its tabbed title bar: it moves.
  W3 A opens the Room of one project (its drawer's Room verb): the window is
     named by the project.
  W4 A reloads: the same windows at the same places, the Room still the Room.
  W5 context B (1440, a fresh load, its own empty cache): the same windows at
     the same places; no "Desk memory" window. W5b with both views open, A
     drags the Room: B shows it there without a reload, B writes nothing, and
     nothing bounces back in either view.
  W6 context C (393, a fresh load): the same windows by name; no "Desk memory".

Shots: docs/internal/philo/phase-17/windows-shots/ (``.tmp/evidence-shots/``
unless HOLDSPEAK_EVIDENCE_WRITE=1).
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_frame_glass import ROOM, _seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the windows glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "philo17-windows"
SHOTS = evidence_dir("docs/internal/philo/phase-17/windows-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000

# Every window shell (shown or not: at 393 only the front sheet shows).
ALL_JS = r"""() => [...document.querySelectorAll('.desk-window-shell:not([data-departing])')]
  .map((s) => s.getAttribute('aria-label'))"""

WINS_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const r = s.getBoundingClientRect();
    return {name: s.getAttribute('aria-label'),
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
}"""

# The right edge of the desk's left icon columns (icons outside windows and
# the Dock), or 0 when the desk shows none: the icons at the left edge, then
# each placed icon that starts right beside them (a second drawer column).
ICONS_JS = r"""() => {
  const icons = [...document.querySelectorAll('.desk-icon')]
    .filter((e) => !e.closest('.desk-window, .desk-dock'))
    .map((e) => ({r: e.getBoundingClientRect(), placed: !!e.closest('.desk-screen-placed')}))
    .filter(({r}) => r.width > 0);
  let right = 0, edge = 60;
  for (let col = 0; ; col++) {
    const next = Math.max(right, ...icons.filter(({r, placed}) => r.left <= edge && (col === 0 || placed)).map(({r}) => r.right));
    if (next <= right) return right;
    right = next; edge = right + 24;
  }
}"""

# A point on the title bar of window `name` that hits the bar itself (not a
# tab, a gadget or the title): the empty part of the bar.
EMPTY_BAR_JS = r"""(name) => {
  const shell = [...document.querySelectorAll('.desk-window-shell')].find((s) => s.getAttribute('aria-label') === name);
  const head = shell && shell.querySelector('.desk-window-handle');
  if (!head) return null;
  const b = head.getBoundingClientRect();
  for (let x = b.left + 8; x < b.right - 8; x += 6) {
    const y = b.top + b.height / 2;
    if (document.elementFromPoint(x, y) === head) return {x, y, tabs: head.querySelectorAll('[role=tab]').length};
  }
  return null;
}"""


def _until(probe: Callable[[], Any], ok: Callable[[Any], bool], seconds: float = 8.0) -> Any:
    deadline = time.monotonic() + seconds
    value = probe()
    while not ok(value) and time.monotonic() < deadline:
        time.sleep(0.25)
        value = probe()
    return value


def _wins(page: Any) -> dict[str, list[int]]:
    _settle(page)
    return {w["name"]: w["rect"] for w in page.evaluate(WINS_JS)}


def _near(a: list[int], b: list[int], px: int = 2) -> bool:
    return all(abs(x - y) <= px for x, y in zip(a, b))


class TestWindowsOpenWell:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _seed()
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, browser: Any, width: int, *, onboard: bool = False) -> tuple[Any, Any, list[str]]:
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(T)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        # Every window write this view sends to the hub (a follower sends none).
        sent: list[str] = []
        page.on("request", lambda r: sent.append(r.url.split("/api/desk/windows", 1)[1])
                if "/api/desk/windows" in r.url and r.method == "POST" else None)
        page.hub_writes = sent  # type: ignore[attr-defined]
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        if onboard:
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        _settle(page)
        return ctx, page, errors

    def test_windows_open_clear_and_come_back(self) -> None:
        from playwright.sync_api import sync_playwright

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                # ── W1: two apps from the Dock ──────────────────────────────
                ctx_a, a, errors_a = self._page(browser, 1440, onboard=True)
                for app in ("Meetings", "People"):
                    a.locator(".desk-dock button").filter(has_text=app).first.click()
                    a.wait_for_timeout(900)
                wins = _until(lambda: _wins(a), lambda w: {"Meetings", "People"} <= set(w))
                icons = a.evaluate(ICONS_JS)
                if not {"Meetings", "People"} <= set(wins):
                    fails["W1 Meetings and People open"] = sorted(wins)
                else:
                    meetings, people = wins["Meetings"], wins["People"]
                    if meetings[:2] == people[:2]:
                        fails["W1 the two do not sit on each other"] = wins
                    for name in ("Meetings", "People"):
                        if icons and wins[name][0] < icons:
                            fails[f"W1 {name} clear of the icon column"] = {"rect": wins[name], "icons_right": icons}
                    if meetings[2] < 900:
                        fails["W1 Meetings opens wide enough (U24)"] = meetings
                a.screenshot(path=str(SHOTS / "1440-two-apps.png"))

                # ── W2: drag a tabbed app by the empty part of its bar ─────
                spot = a.evaluate(EMPTY_BAR_JS, "Meetings")
                if not spot:
                    fails["W2 Meetings' bar has an empty part"] = None
                else:
                    before = _wins(a).get("Meetings")
                    a.mouse.move(spot["x"], spot["y"])
                    a.mouse.down()
                    a.mouse.move(spot["x"] + 30, spot["y"] + 40, steps=8)
                    a.mouse.up()
                    a.wait_for_timeout(500)
                    after = _wins(a).get("Meetings")
                    if not before or not after or after[:2] == before[:2]:
                        fails["W2 the empty bar drags (U28b)"] = {"before": before, "after": after, "tabs": spot["tabs"]}

                # ── W3: the Room of one project ────────────────────────────
                a.get_by_role("button", name=f"{ROOM}, PROJECT").first.dblclick()
                drawer = a.locator(".desk-window-shell").filter(has=a.get_by_test_id("drawer-history"))
                drawer.get_by_role("button", name="Room", exact=True).click()
                wins_a = _until(lambda: _wins(a), lambda w: ROOM in w)
                if ROOM not in wins_a or "Desk memory" in wins_a:
                    fails["W3 the Room is named by its project"] = sorted(wins_a)
                a.wait_for_timeout(1200)  # the writes reach the hub (keepalive)
                wins_a = _wins(a)
                a.screenshot(path=str(SHOTS / "1440-A.png"))

                # ── W4: a reload keeps the windows and their places ─────────
                a.reload(wait_until="load")
                _normal_chair(a)
                reloaded = _until(lambda: _wins(a), lambda w: set(w) == set(wins_a))
                if set(reloaded) != set(wins_a):
                    fails["W4 the same windows after a reload"] = {"before": sorted(wins_a), "after": sorted(reloaded)}
                moved = {n: [wins_a[n], r] for n, r in reloaded.items() if n in wins_a and not _near(wins_a[n], r)}
                if moved:
                    fails["W4 the same places after a reload"] = moved
                a.screenshot(path=str(SHOTS / "1440-A-reloaded.png"))

                # ── W5: another view, a fresh load ──────────────────────────
                ctx_b, b, errors_b = self._page(browser, 1440)
                wins_b = _until(lambda: _wins(b), lambda w: set(w) == set(wins_a))
                if set(wins_b) != set(wins_a) or "Desk memory" in wins_b:
                    fails["W5 B shows the same windows (the Room as the Room)"] = {"A": sorted(wins_a), "B": sorted(wins_b)}
                moved = {n: [wins_a[n], r] for n, r in wins_b.items() if n in wins_a and not _near(wins_a[n], r)}
                if moved:
                    fails["W5 B shows them at the same places"] = moved
                b.screenshot(path=str(SHOTS / "1440-B-fresh.png"))

                # ── W5b: both views open; A moves the Room, B follows live ──
                # (Astra r1 on #1070): no reload; B writes nothing; nothing
                # bounces back in either view. The Room is A's front window.
                b_writes = len(b.hub_writes)
                start = _wins(a).get(ROOM)
                spot = a.evaluate(EMPTY_BAR_JS, ROOM)
                if not start or not spot:
                    fails["W5b the Room's bar is on A's glass"] = {"wins": sorted(_wins(a)), "spot": spot}
                else:
                    a.mouse.move(spot["x"], spot["y"])
                    a.mouse.down()
                    a.mouse.move(spot["x"] + 60, spot["y"] + 50, steps=10)
                    a.mouse.up()
                    moved_a = _until(lambda: _wins(a).get(ROOM), lambda r: bool(r) and r[:2] != start[:2])
                    seen_b = _until(lambda: _wins(b).get(ROOM), lambda r: bool(r) and bool(moved_a) and _near(r, moved_a))
                    if not moved_a or moved_a[:2] == start[:2]:
                        fails["W5b A moved the Room"] = {"start": start, "after": moved_a}
                    elif not seen_b or not _near(seen_b, moved_a):
                        fails["W5b B shows the Room where A put it"] = {"A": moved_a, "B": seen_b}
                    a.wait_for_timeout(1500)
                    later_a, later_b = _wins(a).get(ROOM), _wins(b).get(ROOM)
                    if moved_a and (not later_a or not _near(later_a, moved_a) or not later_b or not _near(later_b, moved_a)):
                        fails["W5b nothing bounces back"] = {"moved": moved_a, "A later": later_a, "B later": later_b}
                    if len(b.hub_writes) != b_writes:
                        fails["W5b B (a follower) writes nothing"] = b.hub_writes[b_writes:]
                b.screenshot(path=str(SHOTS / "1440-B-follows-A.png"))

                # ── W6: the phone, a fresh load ─────────────────────────────
                ctx_c, c, errors_c = self._page(browser, 393)
                names_c = _until(lambda: set(c.evaluate(ALL_JS)), lambda n: set(wins_a) <= n)
                if not set(wins_a) <= names_c or "Desk memory" in names_c:
                    fails["W6 the phone holds the same windows"] = {"A": sorted(wins_a), "C": sorted(names_c)}
                c.screenshot(path=str(SHOTS / "393-C-fresh.png"))

                errors = errors_a + errors_b + errors_c
                if errors:
                    fails["no page errors"] = errors[:5]
                for ctx in (ctx_a, ctx_b, ctx_c):
                    ctx.close()
            finally:
                browser.close()
        assert not fails, fails
