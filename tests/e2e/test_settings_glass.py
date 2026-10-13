"""Settings, rendered: what jsdom cannot read (an exact geometry relation and
a real pointer). The faces' words and states are vitest
(web/src/desk/__tests__/settings.app.test.tsx) on the hub's recorded answers
(tests/integration/test_desk_settings.py).

* Remote access (PHILO-7-02 round two, Astra's check on built, finding 4):
  the REAL scroll-edge position. The body is scrolled to its top, then
  ``Issue credential`` is scrolled into view MINIMALLY (``block: nearest``, as
  a browser brings a focused control in). Its target's centre and corners
  (44 px at 393) are owned by it for ``elementFromPoint`` AND a real
  ``pointermove``: the footer never lies over them.

Moved from test_philo7_02_grant_glass.py (push 2 of the test diet,
2026-10-12; the source is parked in tests/e2e/_parked/).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import holdspeak.principals as principals
from holdspeak.principals import AgentCredentialStore

from .glass_infra import _api, _boot, _ensure_build, _settle
from .settings_rig import _navigate_to_settings_hub, _open_system_module
from tests._evidence import evidence_dir
from .glass_infra import _assert_clean, _normal_chair
from .material_rig import MATERIAL_JS

pytest.importorskip("playwright.sync_api", reason="the Settings glass needs Playwright")

TOKEN = "hs174-remote-settings"  # the HS-174 navigation helpers use this token
IDENTITY = "desk-agent"

_OWNS_JS = """(el, target44) => {
  const r = el.getBoundingClientRect();
  const vw = window.innerWidth, vh = window.innerHeight;
  // At 393 a verb's target is 44 px tall around its face (UX-CANON C); at
  // 1440 the painted face. The centre and four corners, inset 1 px.
  const cy = r.top + r.height / 2;
  const box = target44 ? {l: r.left, r: r.right, t: cy - 22, b: cy + 22} : {l: r.left, r: r.right, t: r.top, b: r.bottom};
  const pts = [[(box.l + box.r) / 2, cy], [box.l + 1, box.t + 1],
               [box.r - 1, box.t + 1], [box.l + 1, box.b - 1], [box.r - 1, box.b - 1]];
  const style = getComputedStyle(el);
  return {
    rect: {x: r.left, y: r.top, w: r.width, h: r.height},
    visible: style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0,
    inViewport: r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh && r.width > 0 && r.height > 0,
    points: pts.map(([x, y]) => { const hit = document.elementFromPoint(x, y); return {x, y, owned: !!hit && (hit === el || el.contains(hit)),
      hit: hit ? (String(hit.className || hit.tagName).split(' ')[0] + ':' + (hit.textContent || '').trim().slice(0, 24)) : null}; }),
    fontPx: parseFloat(style.fontSize),
  };
}"""


def _pointer_owned(page: Any, button: Any, label: str, *, scrolled: bool = False) -> None:
    target44 = page.viewport_size["width"] <= 420
    """elementFromPoint AND a real pointermove at the centre + four corners.

    The verb is first scrolled to the middle of its scroll container, unless
    the caller placed it (``scrolled``: the scroll-edge case).
    """
    if not scrolled:
        button.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = button.evaluate(_OWNS_JS, target44)
    assert probe["inViewport"], f"{label}: outside the viewport {probe['rect']}"
    page.evaluate("""() => { window.__pm = null; document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, {capture: true}); }""")
    for point in probe["points"]:
        assert point["owned"], f"{label}: elementFromPoint does not reach it at {point} (rect {probe['rect']})"
        page.mouse.move(point["x"], point["y"])
        reached = button.evaluate("(el) => !!window.__pm && (window.__pm === el || el.contains(window.__pm))")
        assert reached, f"{label}: a real pointermove at {point} lands elsewhere"


def _remote(page: Any) -> Any:
    return page.locator(".gadget-group", has=page.locator(".gadget-group-label", has_text="Remote access")).last



class TestRemoteAccessGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        monkeypatch.setattr(principals, "agent_credentials", AgentCredentialStore())
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.emulate_media(reduced_motion="reduce")
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        return browser, page, errors

    def _open(self, page: Any) -> None:
        _navigate_to_settings_hub(page, self.base)
        _open_system_module(page)
        _settle(page)

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_minimally_scrolled_verb_clears_the_footer(self, width: int) -> None:
        """The REAL scroll-edge position: the body scrolled to its top, then
        ``Issue credential`` scrolled into view MINIMALLY (``block: nearest``,
        as a browser brings a focused control in). Its target corners must not
        lie under the footer."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/settings/remote", {"enabled": True}, token=TOKEN)
            _api(page, "POST", "/api/settings/remote/credentials", {"identity": IDENTITY, "palette": "DESK"}, token=TOKEN)
            self._open(page)
            issue = _remote(page).locator('[data-testid="issue-credential-btn"]')
            page.evaluate("() => { const b = document.querySelector('.desk-surface-body'); if (b) b.scrollTop = 0; }")
            issue.evaluate("(el) => el.scrollIntoView({block: 'nearest', inline: 'nearest'})")
            _pointer_owned(page, issue.first, f"Issue credential, minimally scrolled, at {width}", scrolled=True)
            assert errors == [], errors
            browser.close()


# ═══ merged from the e2e-high-2 lane ═══
# The Settings app, AS RENDERED: what only a real browser proves of Settings.
#
# Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
# focus, keys, touch, hover or an exact geometry relation (or a computed style
# jsdom cannot compute). Through the real hub on an isolated HOME, at 1440 and
# 393 (PHILO-14 B2, the material pass):
#
# * a plated library Button pressed by the mouse sinks (`:active`: --bevel-sunken,
#   or --wb-sunken on the Steel plate);
# * Settings -> People under the environment override holds the access: every
#   token of the strip is flat (no shadow) on the window's own disabled ground,
#   and the held value READ is the active one.
#
# The material of every window and wing at rest is the desk sweep's `material`
# fence (tests/e2e/test_desk_sweep.py, through tests/e2e/material_rig.py).
pytest.importorskip("playwright.sync_api", reason="the Settings glass needs Playwright")


M_TOKEN = "settings-glass"
SHOTS = evidence_dir("")
SIZES = {1440: 900, 393: 852}
T = 20_000


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", list(SIZES))
def test_a_pressed_button_sinks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """replaces: tests/e2e/test_philo14_b2_material_glass.py::test_the_material_on_six_faces
    (the pressed leg; the six faces at rest are the sweep's `material` fence)."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=M_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": SIZES[width]}, reduced_motion="reduce")
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.goto(f"{url}/?token={M_TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=M_TOKEN)
            page.goto(f"{url}/settings", wait_until="load")
            _normal_chair(page)
            settings = page.locator(".desk-window[aria-label='Settings']")
            settings.wait_for(timeout=T)
            _settle(page)
            verb = settings.locator(".btn:not(:disabled)").first
            box = verb.bounding_box()
            assert box is not None
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            pressed = verb.evaluate("(el) => getComputedStyle(el).boxShadow")
            page.mouse.up()
            m = page.evaluate(MATERIAL_JS, None)
            # Phase 16 (the kit Verb is the Steel plate): on the Steel the
            # grammar rides --wb-raised / --wb-sunken (contract.md "The
            # bevel grammar"), so a pressed Verb sinks to --wb-sunken.
            assert pressed.startswith((m["sunken"], m["wbSunken"])), (pressed, m["sunken"], m["wbSunken"])
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", list(SIZES))
def test_a_held_filter_strip_is_flat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """replaces: tests/e2e/test_philo14_b2_material_glass.py::test_a_held_filter_strip_is_flat

    Astra r1 on #958: Settings -> People under the environment override
    holds the access (the strip is the disabled Button state): every token
    is flat, the held value has no tint, through the real settings API."""
    _ensure_build()
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "read")
    server, url = _boot(tmp_path, monkeypatch, token=M_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": SIZES[width]}, reduced_motion="reduce")
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.goto(f"{url}/?token={M_TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=M_TOKEN)
            wire = _api(page, "GET", "/api/settings/people-access", token=M_TOKEN)
            assert wire["source"] == "env" and wire["effective"] == "read", wire
            page.goto(f"{url}/settings", wait_until="load")
            _normal_chair(page)
            page.locator("[data-testid='settings-more']").click()  # PHILO-17 REFIT: People folds under More settings
            row = page.locator(".surface-ledger-row", has=page.locator(".surface-ledger-primary", has_text="People"))
            row.get_by_role("button", name="Open", exact=True).click()
            strip = page.get_by_role("group", name="People MCP access", exact=True)
            strip.wait_for(timeout=T)
            _settle(page)
            strip.scroll_into_view_if_needed()
            tokens = strip.locator("button").evaluate_all("""bs => bs.map((b) => {
                const s = getComputedStyle(b);
                const probe = document.createElement('div');
                probe.style.background = 'var(--disabled-bg)';
                // The disabled ground as the strip's own window reads it:
                // A1's interior remap sets --disabled-bg per window, so a
                // probe on <body> read the page's dark ground instead.
                b.parentElement.appendChild(probe);
                const ground = getComputedStyle(probe).backgroundColor;
                probe.remove();
                return {text: b.innerText.trim(), disabled: b.disabled, active: b.hasAttribute('data-filter-active'),
                        shadow: s.boxShadow, bg: s.backgroundColor, ground};
            })""")
            page.screenshot(path=str(SHOTS / f"B2-held-filters-{width}.png"))
            assert len(tokens) == 3 and all(t["disabled"] for t in tokens), tokens
            assert all(t["shadow"] == "none" for t in tokens), tokens
            assert all(t["bg"] == t["ground"] for t in tokens), tokens
            assert [t["text"] for t in tokens if t["active"]] == ["READ"], tokens
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
