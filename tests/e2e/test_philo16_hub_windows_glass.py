"""PHILO-16 (lane 16b) -- the hub owns the desk's windows, on glass.

COMPOSITOR.md §13 L1: every browser is one view of the same desk; an agent
reaches the same windows. Through ONE real hub on an isolated HOME, the built
bundle, two browser contexts (two views, two localStorages):

  B1 context A (1440) opens Brief, The week and Needs you, drags Brief and
     seats The week; the hub's rows hold the three (GET /api/desk/windows):
     The week minimized, Brief arranged as share+px strings (never pixels).
  B2 context B (a fresh load at 1440, its own empty cache) shows the same
     windows: Brief at the same rect, The week seated (not on the glass).
  B3 B raises A's NEAR window; A follows without a reload (its data-plane
     turns front).
  B4 the MCP tool ``desk_window.arrange`` (the hub's one dispatcher, in this
     process) tiles Brief and Needs you; both contexts show the tile.
  B5 context C at 393 (a fresh load): Go lists the same three Chair windows
     open; The week is seated in its cache of the hub's rows.
  B6 A opens the Project drawer (Payments ledger cutover); a fresh view D
     shows it (Astra r1 M4).

Shots: docs/internal/philo/phase-16/b-shots/ (``.tmp/evidence-shots/``
unless HOLDSPEAK_EVIDENCE_WRITE=1).
"""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any, Callable

import pytest

from .chair_windows import open_chair_window
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_philo13_11_frame_glass import _seed
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the hub windows glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "philo16-hub-windows"
SHOTS = evidence_dir("docs/internal/philo/phase-16/b-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000
THREE = ("Brief", "The week", "Needs you")
IDS = {"Brief": "chair:brief", "The week": "chair:week", "Needs you": "chair:needs"}

WINS_JS = r"""() => {
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden'; };
  return [...document.querySelectorAll('.desk-window-shell:not([data-departing])')].filter(visible).map((s) => {
    const r = s.getBoundingClientRect();
    return {name: s.getAttribute('aria-label'), plane: s.dataset.plane || null,
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]}; });
}"""

BAND_JS = r"""() => {
  const st = getComputedStyle(document.documentElement);
  const top = parseFloat(st.getPropertyValue('--desk-work-top'));
  const band = parseFloat(st.getPropertyValue('--desk-work-bottom'));
  const dock = parseFloat(st.getPropertyValue('--desk-dock-h'));
  const bottom = Number.isFinite(dock) ? Math.max(band, dock) : band;
  return {x: 10, y: top, w: innerWidth - 20, h: innerHeight - top - bottom};
}"""

CACHE_JS = r"""() => { const d = JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || 'null') || {};
  const p = d.panel || {}; return {min: p.min || [], depth: p.depth || {}, closed: (d.chair || {}).closed || []}; }"""


def _wins(page: Any) -> dict[str, dict[str, Any]]:
    _settle(page)
    return {w["name"]: w for w in page.evaluate(WINS_JS)}


def _until(probe: Callable[[], Any], ok: Callable[[Any], bool], seconds: float = 8.0) -> Any:
    deadline = time.monotonic() + seconds
    value = probe()
    while not ok(value) and time.monotonic() < deadline:
        time.sleep(0.25)
        value = probe()
    return value


def _drag(page: Any, selector: str, dx: float, dy: float) -> None:
    box = page.locator(selector).first.bounding_box()
    assert box, f"nothing to drag: {selector}"
    x, y = box["x"] + min(60, box["width"] / 3), box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + dx / 2, y + dy / 2, steps=5)
    page.mouse.move(x + dx, y + dy, steps=5)
    page.mouse.up()


def _window_menu(page: Any, label: str) -> None:
    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    page.locator(".desk-verbbar-menu [role^='menuitem']").filter(has_text=label).first.click()


def _to_front(page: Any, name: str) -> None:
    """Window ▸ Chair ▸ name: picking an open Chair window brings it in front."""
    page.locator(".desk-verbbar-item[data-menu-id='window'] button").click()
    page.locator(".desk-verbbar-menu").wait_for()
    sub = page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')")
    sub.scroll_into_view_if_needed()
    sub.click()
    page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')").click()
    page.wait_for_timeout(300)


def _side_by_side(pw_browser: Any, left: Path, right: Path, out: Path) -> None:
    """One shot of two: the two contexts' shots drawn side by side."""
    def uri(path: Path) -> str:
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()

    page = pw_browser.new_page(viewport={"width": 2900, "height": 960}, device_scale_factor=0.5)
    page.set_content(
        "<body style='margin:0;background:#222;display:flex;gap:20px;padding:20px;font:14px sans-serif;color:#ddd'>"
        f"<figure style='margin:0'><figcaption>context A</figcaption><img src='{uri(left)}' width=1440></figure>"
        f"<figure style='margin:0'><figcaption>context B (fresh load)</figcaption><img src='{uri(right)}' width=1440></figure>"
        "</body>")
    page.wait_for_timeout(300)
    page.screenshot(path=str(out), full_page=True)
    page.close()


class TestHubWindows:
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
        # Every window write this view sends to the hub, in order (evidence).
        sent: list[str] = []
        page.on("request", lambda r: sent.append(
            f"{r.url.split('/api/desk/windows', 1)[1] or '/'} {r.post_data or ''}")
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

    def _rows(self, page: Any) -> dict[str, dict[str, Any]]:
        listed = _api(page, "GET", "/api/desk/windows", token=TOKEN)
        return {w["id"]: w for w in listed["windows"]}

    def test_one_desk_two_views(self) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.mcp import tools as mcp_tools
        from holdspeak.principals import Principal, PrincipalKind

        fails: dict[str, Any] = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                # ── B1: context A opens three, drags one, seats one ─────────
                ctx_a, a, errors_a = self._page(browser, 1440, onboard=True)
                for name in THREE:
                    open_chair_window(a, name)
                a.wait_for_timeout(500)
                _drag(a, ".desk-window-shell[aria-label='Brief'] .desk-pullout-title", -160, 70)
                a.wait_for_timeout(400)
                _to_front(a, "The week")
                _window_menu(a, "Iconify")
                rows = _until(lambda: self._rows(a), lambda r: (
                    set(IDS.values()) <= set(r) and r["chair:week"]["minimized"] and r["chair:brief"]["arranged"]))
                if not set(IDS.values()) <= set(rows):
                    fails["B1 the hub holds the three windows"] = sorted(rows)
                else:
                    if not rows["chair:week"]["minimized"]:
                        fails["B1 The week is seated on the hub"] = rows["chair:week"]
                    brief = rows["chair:brief"]
                    if not brief["arranged"] or not all(isinstance(brief[k], str) and "%" in brief[k] for k in "xywh"):
                        fails["B1 Brief's rect is share+px on the hub"] = brief
                (SHOTS / "hub-rows.json").write_text(json.dumps(
                    _api(a, "GET", "/api/desk/windows", token=TOKEN), indent=2) + "\n")
                wins_a = _wins(a)
                a.screenshot(path=str(SHOTS / "1440-A.png"))

                # ── B2: context B, a fresh load, shows the same desk ────────
                ctx_b, b, errors_b = self._page(browser, 1440)
                wins_b = _until(lambda: _wins(b), lambda w: {"Brief", "Needs you"} <= set(w))
                if not {"Brief", "Needs you"} <= set(wins_b):
                    fails["B2 B shows the open windows"] = sorted(wins_b)
                if "The week" in wins_b:
                    fails["B2 The week is seated in B (not on the glass)"] = wins_b["The week"]
                if "Brief" in wins_a and "Brief" in wins_b and wins_a["Brief"]["rect"] != wins_b["Brief"]["rect"]:
                    fails["B2 Brief at the same rect in A and B"] = {"A": wins_a["Brief"]["rect"], "B": wins_b["Brief"]["rect"]}
                fronts = {label: [n for n, w in wins.items() if w["plane"] == "front"]
                          for label, wins in (("A", wins_a), ("B", wins_b))}
                if fronts["A"] != fronts["B"] or len(fronts["A"]) != 1:
                    fails["B2 one front, the same in A and B"] = fronts
                cache_b = b.evaluate(CACHE_JS)
                if "chair:week" not in cache_b["min"] or any(IDS[n] in cache_b["closed"] for n in THREE):
                    fails["B2 B's cache is the hub's rows"] = cache_b
                b.screenshot(path=str(SHOTS / "1440-B.png"))
                _side_by_side(browser, SHOTS / "1440-A.png", SHOTS / "1440-B.png", SHOTS / "1440-A-and-B.png")

                # ── B3: B raises A's near window; A follows ─────────────────
                planes_a = {n: w["plane"] for n, w in _wins(a).items()}
                near = next((n for n, p in planes_a.items() if p == "near"), None)
                if near is None:
                    fails["B3 A has a near window"] = planes_a
                else:
                    _to_front(b, near)
                    followed = _until(lambda: _wins(a), lambda w: w.get(near, {}).get("plane") == "front")
                    if followed.get(near, {}).get("plane") != "front":
                        fails["B3 A follows B's raise without a reload"] = {
                            n: w["plane"] for n, w in followed.items()}
                    a.screenshot(path=str(SHOTS / "1440-A-follows-B.png"))

                # ── B4: an agent tiles two through MCP; both views follow ───
                owner = Principal(PrincipalKind.OWNER, "philo16-owner")
                mcp_tools.dispatch("desk_window.arrange", {"rects": {
                    "chair:brief": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"},
                    "chair:needs": {"x": "0%", "y": "-1/2", "w": "1/2", "h": "100%"},
                }}, owner)
                band = a.evaluate(BAND_JS)
                half = band["w"] / 2

                def tiled(w: dict[str, Any]) -> bool:
                    if "Brief" not in w or "Needs you" not in w:
                        return False
                    bx, _, bw, _ = w["Brief"]["rect"]
                    nx, _, nw, _ = w["Needs you"]["rect"]
                    return abs(bx - band["x"]) <= 2 and abs(bw - half) <= 3 and abs(nx - (band["x"] + half)) <= 3

                for label, page in (("A", a), ("B", b)):
                    seen = _until(lambda: _wins(page), tiled)
                    if not tiled(seen):
                        fails[f"B4 {label} shows the agent's tile"] = {
                            n: w["rect"] for n, w in seen.items()} | {"band": band}
                a.screenshot(path=str(SHOTS / "1440-A-tile.png"))
                b.screenshot(path=str(SHOTS / "1440-B-tile.png"))
                _side_by_side(browser, SHOTS / "1440-A-tile.png", SHOTS / "1440-B-tile.png",
                              SHOTS / "1440-A-and-B-tile.png")

                # ── B5: 393, a fresh load: the same set, the same seat ──────
                ctx_c, c, errors_c = self._page(browser, 393)
                cache_c = _until(lambda: c.evaluate(CACHE_JS), lambda v: "chair:week" in v["min"])
                if "chair:week" not in cache_c["min"] or any(IDS[n] in cache_c["closed"] for n in THREE):
                    fails["B5 393 holds the hub's set and seat"] = cache_c
                c.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
                c.locator(".desk-verbbar-menu").wait_for()
                checked = {}
                for name in THREE:
                    row = c.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')").first
                    checked[name] = row.get_attribute("aria-checked") if row.count() else None
                if any(checked.get(n) != "true" for n in THREE):
                    fails["B5 393 Go lists the open Chair windows"] = checked
                c.screenshot(path=str(SHOTS / "393-C-go-chair.png"))
                c.keyboard.press("Escape")

                # ── B6 (Astra r1 M4): a Project drawer follows into a fresh view ──
                a.goto(f"{self.base}/?token={TOKEN}&open=project:p-ledger", wait_until="load")
                _normal_chair(a)
                a.locator(".drawer-window").first.wait_for(timeout=T)
                drawer_row = _until(lambda: self._rows(a), lambda r: "drawer:project:p-ledger" in r)
                if drawer_row.get("drawer:project:p-ledger", {}).get("object_ref") != "project:p-ledger":
                    fails["B6 the hub holds A's Project drawer"] = sorted(drawer_row)
                ctx_d, d, errors_d = self._page(browser, 1440)
                try:
                    d.locator(".drawer-window").first.wait_for(timeout=10_000)
                except Exception:
                    fails["B6 a fresh view shows A's Project drawer"] = sorted(_wins(d))
                d.screenshot(path=str(SHOTS / "1440-D-drawer.png"))
                if errors_d:
                    fails["page errors D"] = errors_d
                ctx_d.close()

                (SHOTS / "hub-writes.json").write_text(json.dumps(
                    {"A": a.hub_writes, "B": b.hub_writes, "C": c.hub_writes}, indent=2) + "\n")
                if c.hub_writes:
                    fails["B5 a 393 load writes nothing to the hub"] = c.hub_writes
                rows_end = self._rows(a)
                (SHOTS / "hub-rows-end.json").write_text(json.dumps(rows_end, indent=2) + "\n")
                for label, errors in (("A", errors_a), ("B", errors_b), ("C", errors_c)):
                    if errors:
                        fails[f"page errors {label}"] = errors
                for ctx in (ctx_a, ctx_b, ctx_c):
                    ctx.close()
            finally:
                browser.close()
        assert not fails, json.dumps(fails, indent=2, default=str)
