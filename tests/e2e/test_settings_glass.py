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

import re
import sqlite3

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


def _settings_directory(page: Any, base: str, token: str) -> Any:
    """Request the directory explicitly, even if Settings remembered a wing."""
    page.goto(f"{base}/?token={token}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=token)
    page.evaluate("""() => sessionStorage.setItem('hs.desk.staged-surface-open',
        JSON.stringify({key: 'configure-settings', scope: 'settings'}))""")
    page.reload(wait_until="load")
    _normal_chair(page)
    directory = page.locator("#surface-settings .settings-home")
    directory.wait_for(timeout=10_000)
    return directory


def _open_directory_module(page: Any, directory: Any, label: str, module: str) -> None:
    row = directory.locator(".surface-ledger-row").filter(
        has=page.locator(".surface-ledger-primary", has_text=re.compile(rf"^{re.escape(label)}$")))
    row.get_by_role("button", name=f"Open {label}", exact=True).click()
    page.locator(f"#surface-settings [data-settings-module='{module}']").wait_for()


@pytest.mark.parametrize("width", [1440, 393])
def test_summary_controls_own_the_row_height(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """The Summary controls must finish above Recording at both widths."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    out = evidence_dir("surface-repair-first-use")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852}, reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            directory = _settings_directory(page, base, TOKEN)
            _open_directory_module(page, directory, "Meetings", "meetings")
            controls = page.get_by_test_id("settings-summary-controls")
            controls.wait_for()
            _settle(page)
            controls.scroll_into_view_if_needed()
            geometry = controls.evaluate("""el => {
              const row = el.closest('.gadget-row').getBoundingClientRect();
              const next = [...el.closest('[data-settings-module=meetings]').querySelectorAll('.gadget-group-label')]
                .find(e => e.textContent === 'Recording').getBoundingClientRect();
              const children = [...el.children].map(e=>e.getBoundingClientRect()).filter(r=>r.width&&r.height);
              return {row:row.toJSON(),next:next.toJSON(),children:children.map(r=>r.toJSON())};
            }""")
            page.screenshot(path=str(out / f"settings-meetings-{width}.png"))
            assert geometry["next"]["top"] >= geometry["row"]["bottom"], geometry
            assert all(child["bottom"] <= geometry["row"]["bottom"] + 1 for child in geometry["children"]), geometry
            engines = page.get_by_test_id("settings-engines-link")
            _pointer_owned(page, engines, f"Engines at {width}")
            engines.click()
            engine_home = page.locator("#surface-settings [data-settings-view=models]")
            engine_home.get_by_test_id("runson-root").wait_for()
            engine_home.get_by_test_id("runson-fact").filter(has_text="No engine yet").wait_for()
            assert errors == [], errors
            browser.close()
    finally:
        server.stop()



@pytest.mark.parametrize("width", [1440, 393])
def test_short_stepper_keeps_the_value_beside_its_touch_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """The number must fit after the phone's two 44 px arrow targets."""
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    out = evidence_dir("settings-short-steppers")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                reduced_motion="reduce",
            )
            directory = _settings_directory(page, base, TOKEN)
            _api(page, "PUT", "/api/settings/heartbeat", {
                "quiet_hours": {"start": 21, "end": 8},
            }, token=TOKEN)
            _open_directory_module(page, directory, "Rhythm", "rhythm")
            value = page.get_by_role("spinbutton", name="Quiet from", exact=True)
            value.wait_for()
            page.wait_for_function(
                "() => document.querySelector('input[aria-label=\"Quiet from\"]').value === '21'",
            )
            value.scroll_into_view_if_needed()
            geometry = value.evaluate("""el => {
                const style = getComputedStyle(el);
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                context.font = style.font;
                return {
                    available: el.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight),
                    needed: context.measureText(el.value).width,
                    input: el.getBoundingClientRect().toJSON(),
                };
            }""")
            page.screenshot(path=str(out / f"rhythm-{width}.png"))
            assert geometry["available"] >= geometry["needed"], geometry
            increase = page.get_by_role("button", name="Increase Quiet from", exact=True)
            _pointer_owned(page, increase, f"Increase Quiet from at {width}")
            increase.click()
            page.wait_for_function(
                "() => document.querySelector('input[aria-label=\"Quiet from\"]').value === '22'",
            )
            saved = _api(page, "GET", "/api/settings/heartbeat", token=TOKEN)
            assert saved["quiet_hours"]["start"] == 22
            browser.close()
    finally:
        server.stop()


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
            directory = _settings_directory(page, url, M_TOKEN)
            _open_directory_module(page, directory, "People", "people")
            strip = page.get_by_role("group", name="Agent access", exact=True)
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
            assert [t["text"] for t in tokens] == ["OFF", "READ", "READ AND WRITE"], tokens
            assert [t["text"] for t in tokens if t["active"]] == ["READ"], tokens
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


from .glass_infra import REPO  # noqa: E402 (the PHILO-9-07 section)

# ── PHILO-9-07 the project delegation grant (the HS-174 navigation helpers use G_TOKEN) ──
G_TOKEN = "hs174-remote-settings"  # the HS-174 navigation helpers use this token
AGENT = "sweep-runner"
DESK_AGENT = "desk-agent"
PAYMENTS, HIRING = "Payments ledger cutover", "Hiring loop"
G_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-shots")
SOURCE = REPO / "web" / "src" / "pages" / "cores" / "SettingsCore.tsx"
HEIGHT = {1440: 900, 393: 852}


def _constant(name: str) -> dict[str, str]:
    source = SOURCE.read_text(encoding="utf-8")
    if f"export const {name} = {{" not in source:
        return {}
    block = source.split(f"export const {name} = {{", 1)[1].split("} as const;", 1)[0]
    return dict(re.findall(r'(\w+): "([^"]+)"', block))


# The face as on main declares no project words: the fences fail on the rendered page.
P = {
    "allow": "Allow run and publish", "stop": "Stop run and publish", "live": "RUN AND PUBLISH ALLOWED",
    "stopped": "RUN AND PUBLISH STOPPED", "actAllow": "ALLOW RUN AND PUBLISH", "actStop": "STOP RUN AND PUBLISH",
    "projects": "Projects", "credentialRevoked": "CREDENTIAL REVOKED", "archived": "ARCHIVED",
    **_constant("PROJECT_GRANT_WORDS"),
}
W = _constant("GRANT_WORDS")


# ── the rendered-page probes ────────────────────────────────────────────

_g_OWNS_JS = """(el, target44) => {
  const r = el.getBoundingClientRect();
  const vw = window.innerWidth, vh = window.innerHeight;
  const cy = r.top + r.height / 2, cx = r.left + r.width / 2;
  const box = target44 ? {l: r.left, r: r.right, t: cy - 22, b: cy + 22} : {l: r.left, r: r.right, t: r.top, b: r.bottom};
  const pts = [[cx, cy], [box.l + 1, box.t + 1], [box.r - 1, box.t + 1], [box.l + 1, box.b - 1], [box.r - 1, box.b - 1],
               [cx, box.t + 1], [cx, box.b - 1], [box.l + 1, cy], [box.r - 1, cy]];
  const style = getComputedStyle(el);
  return {
    rect: {x: r.left, y: r.top, w: r.width, h: r.height},
    visible: style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0,
    inViewport: r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh && r.width > 0 && r.height > 0,
    points: pts.map(([x, y]) => { const hit = document.elementFromPoint(x, y); return {x, y, owned: !!hit && (hit === el || el.contains(hit)),
      hit: hit ? (String(hit.className || hit.tagName).split(' ')[0] + ':' + (hit.textContent || '').trim().slice(0, 24)) : null}; }),
  };
}"""

_WINDOW_FACTS = """() => {
  const win = document.querySelector('.desk-settings-window') || document.querySelector('.desk-surface-window');
  const body = win.querySelector('.desk-surface-body');
  const txt = (e) => (e?.innerText ?? '').replace(/\\s+/g, ' ').trim();
  const small = [];
  const walker = document.createTreeWalker(win, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.textContent.trim();
    if (!t || /^[●○✓✗⚠—↻ℹ«»·▸▾]$/.test(t)) continue;
    const el = n.parentElement; const r = el.getBoundingClientRect();
    if (!r.width || getComputedStyle(el).visibility === 'hidden') continue;
    if (parseFloat(getComputedStyle(el).fontSize) < 12) small.push(t.slice(0, 40));
  }
  const parse = (c) => { const m = c.match(/[\\d.]+/g) || []; return {r:+m[0]||0, g:+m[1]||0, b:+m[2]||0, a: m[3] === undefined ? 1 : +m[3]}; };
  const blend = (top, under) => ({r: top.r*top.a + under.r*(1-top.a), g: top.g*top.a + under.g*(1-top.a), b: top.b*top.a + under.b*(1-top.a), a: 1});
  const bgOf = (el) => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) { const c = parse(getComputedStyle(e).backgroundColor); if (c.a > 0) { layers.push(c); if (c.a >= 1) break; } }
    let acc = {r: 0, g: 0, b: 0, a: 1};
    for (let i = layers.length - 1; i >= 0; i--) acc = blend(layers[i], acc);
    return acc;
  };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v/12.92 : ((v+0.055)/1.055)**2.4; }; return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b); };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return +((x + 0.05) / (y + 0.05)).toFixed(2); };
  const group = [...win.querySelectorAll('.gadget-group')].filter(g => /Remote access/.test(g.querySelector('.gadget-group-label')?.textContent || ''));
  const low = [];
  const scope = [...group, ...win.querySelectorAll('.desk-surface-foot')];
  for (const root of scope) for (const el of root.querySelectorAll('.surface-state-chip, .surface-token, .gadget-fact, .surface-receipt, .surface-ledger-count, .surface-disclosure-label')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !txt(el)) continue;
    // PHILO-14 B2 (Astra r1): a StateChip whose only text is its undrawn
    // lamp glyph draws no text, so it has no text contrast to read. It must
    // still be named (aria-label). Nothing else is exempt.
    if (el.matches('.surface-state-chip')) {
      const glyph = el.querySelector('.surface-state-chip-icon')?.textContent || '';
      const word = (el.textContent || '').slice(glyph.length).trim();
      if (!word) {
        if (!(el.getAttribute('aria-label') || '').trim()) low.push(['UNNAMED LAMP', 0]);
        continue;
      }
    }
    let paint = el;
    const inner = [...el.querySelectorAll('*')].filter(c => [...c.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
    if (!([...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) && inner.length) paint = inner[inner.length - 1];
    const fg = parse(getComputedStyle(paint).color); const bg = bgOf(paint);
    const value = ratio(fg.a < 1 ? blend(fg, bg) : fg, bg);
    if (value < 4.5) low.push([txt(el).slice(0, 40), value]);
  }
  return {
    small, low,
    raw: [...win.querySelectorAll('button')].filter(b => !String(b.className).includes('btn') && !b.closest('.gadget-cycle, select')).map(b => txt(b)),
    overflow: document.documentElement.scrollWidth > window.innerWidth || (body ? body.scrollWidth > body.clientWidth + 1 : false),
    dialogs: win.querySelectorAll('[role=dialog], .modal, .surface-popover, [role=menu]').length,
    top: win.getBoundingClientRect().top,
  };
}"""


def _readable(locator: Any, want: str) -> None:
    locator.first.wait_for(state="visible", timeout=8_000)
    text = (locator.first.inner_text() or "").strip()
    assert want in text, f"{want!r} not in {text!r}"
    locator.first.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = locator.first.evaluate(_g_OWNS_JS, False)
    assert probe["visible"] and probe["inViewport"], f"{want!r}: not readable: {probe}"
    uncovered = [p for p in probe["points"][:5] if not p["owned"]]
    assert not uncovered, f"{want!r}: covered at {uncovered}"


def _g_pointer_owned(page: Any, button: Any, label: str) -> None:
    target44 = page.viewport_size["width"] <= 420
    button.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = button.evaluate(_g_OWNS_JS, target44)
    assert probe["inViewport"], f"{label}: outside the viewport {probe['rect']}"
    page.evaluate("""() => { window.__pm = null; document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, {capture: true}); }""")
    for point in probe["points"]:
        assert point["owned"], f"{label}: elementFromPoint does not reach it at {point} (rect {probe['rect']})"
        page.mouse.move(point["x"], point["y"])
        reached = button.evaluate("(el) => !!window.__pm && (window.__pm === el || el.contains(window.__pm))")
        assert reached, f"{label}: a real pointermove at {point} lands elsewhere"


def _lawful(page: Any, width: int) -> dict[str, Any]:
    """Every state: the library Button owns its nine points; no small text, no overflow, contrast >= 4.5."""
    buttons = _g_remote(page).locator("button")
    for i in range(buttons.count()):
        button = buttons.nth(i)
        if button.evaluate("(el) => !!el.closest('.gadget-cycle, select')"):
            continue
        assert "btn" in (button.get_attribute("class") or ""), f"a verb that is not the library Button: {button.inner_text()!r}"
        _g_pointer_owned(page, button, f"{button.inner_text()!r} at {width}")
    foot = page.locator('[data-testid="foot-receipt"]')
    if foot.count():
        _g_pointer_owned(page, foot.first, f"the footer receipt at {width}")
    page.mouse.move(0, 0)
    facts = page.evaluate(_WINDOW_FACTS)
    assert facts["small"] == [], f"text under 12 px in the Settings window: {facts['small'][:5]}"
    assert facts["raw"] == [], f"a raw <button>: {facts['raw']}"
    assert facts["low"] == [], f"a chip or token under 4.5:1: {facts['low']}"
    assert not facts["overflow"], "horizontal overflow"
    assert facts["dialogs"] == 0, "a dialog, popover or menu is open: the pick is in place"
    return facts


def _g_remote(page: Any) -> Any:
    return page.locator(".gadget-group", has=page.locator(".gadget-group-label", has_text="Remote access")).last


def _row(page: Any, identity: str) -> Any:
    return _g_remote(page).locator(".surface-ledger-row", has=page.locator(".surface-ledger-primary", has_text=identity)).first


def _line(page: Any, identity: str, pid: str) -> Any:
    return _row(page, identity).locator(f'[data-testid="project-line-{pid}"]')


def _grant_rows(db_path: Path, identity: str = AGENT) -> list[tuple[str, str, str]]:
    conn = sqlite3.connect(str(db_path))
    try:
        return [tuple(r) for r in conn.execute(
            "SELECT project_id, state, revocation_reason FROM kernel_project_delegations WHERE agent_identity=? "
            "ORDER BY created_at, rowid", (identity,))]
    finally:
        conn.close()


def _kernel(page: Any, operation_id: str) -> dict[str, Any]:
    return _api(page, "GET", f"/api/kernel/read?refs=operation:{operation_id}&view=receipt", token=G_TOKEN)["objects"][0]


class _Rig:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        monkeypatch.setattr(principals, "agent_credentials", AgentCredentialStore())
        server, base = _boot(tmp_path, monkeypatch, token=G_TOKEN)
        self.server, self.base, self.db_path = server, base, tmp_path / "holdspeak.db"
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": HEIGHT[width]})
        page.emulate_media(reduced_motion="reduce")
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        # A refused grant act answers 403/409 by design: the browser's
        # resource-load line for it is not a page error.
        page.on("console", lambda m: errors.append(f"console: {m.text}")
                if m.type == "error" and "Failed to load resource" not in m.text else None)
        return browser, page, errors

    def _world(self, page: Any, *, credentials: bool = True) -> dict[str, str]:
        """Remote ON, two credentials (DESK, PROJECT), two projects -- the real routes only."""
        page.goto(f"{self.base}/?token={G_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/settings/remote", {"enabled": True}, token=G_TOKEN)
        tokens = {}
        if credentials:
            for identity, palette in ((DESK_AGENT, "DESK"), (AGENT, "PROJECT")):
                tokens[identity] = _api(page, "POST", "/api/settings/remote/credentials",
                                        {"identity": identity, "palette": palette}, token=G_TOKEN)["token"]
        pids = {name: _api(page, "POST", "/api/projects", {"name": name}, token=G_TOKEN)["project"]["id"]
                for name in (PAYMENTS, HIRING)}
        return {**pids, **{f"token:{k}": v for k, v in tokens.items()}}

    def _open(self, page: Any) -> None:
        _navigate_to_settings_hub(page, self.base)
        _open_system_module(page)
        _settle(page)

    def _open_projects(self, page: Any, identity: str = AGENT) -> None:
        trigger = _row(page, identity).locator("button", has_text=P["projects"])
        if trigger.get_attribute("aria-expanded") != "true":
            trigger.click()
        _row(page, identity).locator(f'[data-testid="project-lines-{identity}"] [data-testid="project-grant-verb"]').first.wait_for(timeout=8_000)

    def _shot(self, page: Any, name: str, width: int, *, focus: str = "") -> None:
        G_SHOTS.mkdir(parents=True, exist_ok=True)
        page.evaluate("""(focus) => {
          const g = [...document.querySelectorAll('.gadget-group')].find(g => g.querySelector('.gadget-group-label')?.textContent === 'Remote access');
          g?.scrollIntoView({block: 'start'});
          const last = (focus && document.querySelector(focus)) || document.querySelector('[data-testid=grant-receipt]') || document.querySelector('.surface-ledger-open');
          const body = document.querySelector('.desk-settings-window .desk-surface-body');
          if (last && body && last.getBoundingClientRect().bottom > body.getBoundingClientRect().bottom)
            body.scrollTop += last.getBoundingClientRect().bottom - body.getBoundingClientRect().bottom + 8;
        }""", focus)
        page.mouse.move(0, 0)
        page.wait_for_timeout(150)
        page.screenshot(path=str(G_SHOTS / f"{name}-{width}.png"), full_page=False)


class TestProjectGrantGlass(_Rig):

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_remote_off_keeps_a_credential_with_a_live_project_grant(self, width: int) -> None:
        """replaces: tests/e2e/test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_remote_off_keeps_a_credential_with_a_live_project_grant (moved: every verb owns its target to a real pointer; the window stays put)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{ids[PAYMENTS]}", {}, token=G_TOKEN)
            _api(page, "PUT", "/api/settings/remote", {"enabled": False}, token=G_TOKEN)
            self._open(page)
            assert _g_remote(page).locator(".surface-ledger-primary", has_text=DESK_AGENT).count() == 0
            self._open_projects(page)
            _readable(_line(page, AGENT, ids[PAYMENTS]).locator('[data-testid="project-grant-verb"]'), P["stop"])
            _readable(_row(page, AGENT).locator('[data-testid="credential-revoke"]'), W["revokeCredential"])
            _lawful(page, width)
            self._shot(page, "7b-off-credential", width)
            assert errors == [], errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put(self, width: int) -> None:
        """replaces: tests/e2e/test_philo9_07_project_grant_glass.py::TestProjectGrantGlass::test_the_owner_revokes_a_credential_the_grant_ends_first_and_the_window_stays_put (moved: every verb owns its target to a real pointer; the window stays put)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            pay = ids[PAYMENTS]
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{pay}", {}, token=G_TOKEN)
            self._open(page)
            _readable(_row(page, AGENT).locator('[data-testid="project-grant-summary"]'), P["live"])
            before = page.evaluate(_WINDOW_FACTS)["top"]
            _row(page, AGENT).locator('[data-testid="credential-revoke"]').click()
            page.wait_for_function(f"() => ![...document.querySelectorAll('.surface-ledger-primary')].some(e => e.textContent.includes('{AGENT}'))")
            assert _g_remote(page).locator('[data-testid^="project-delegation-row-"]').count() == 0, "an owner revoke left an orphan"
            assert _grant_rows(self.db_path) == [(pay, "REVOKED", "credential_revoked")]
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "STOPPED")
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            for word in ("SUCCEEDED", P["stopped"], P["credentialRevoked"], PAYMENTS, AGENT, "BY OWNER"):
                _readable(well, word)
            receipt = _kernel(page, well.get_attribute("data-operation-id"))
            assert (receipt["operation"]["name"], receipt["receipt"]["state"]) == ("project.delegation.revoke", "succeeded")
            facts = _lawful(page, width)
            # Canvas board 11's open: the window's top does not move after a credential revoke.
            assert facts["top"] == before, f"the Settings window moved: {before} -> {facts['top']}"
            self._shot(page, "11-credential-revoked", width)
            assert errors == [], errors
            browser.close()


class TestArchivedProjectGrant(_Rig):
    """Round three (Codex Astra r1 finding 2; Muad'Dib's ruling 2026-09-28): archive keeps a
    project's grants (the charter fixes archive's effect), so a LIVE grant on an archived
    project stays on the credential row, ARCHIVED, with its Stop and never an Allow."""

    @pytest.mark.e2e
    @pytest.mark.parametrize("remote", ["on", "off"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_archive_keeps_the_stop_and_its_receipt_on_and_off(self, width: int, remote: str) -> None:
        """replaces: tests/e2e/test_philo9_07_project_grant_glass.py::TestArchivedProjectGrant::test_archive_keeps_the_stop_and_its_receipt_on_and_off (moved: every verb owns its target to a real pointer; the window stays put)."""
        """Archive -> the line stays (ARCHIVED, Stop only) -> Stop -> the line goes, the receipt stays;
        with Remote Access ON and OFF (Codex Astra r2: Stop pressed in both states)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            pay = ids[PAYMENTS]
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{pay}", {}, token=G_TOKEN)
            _api(page, "DELETE", f"/api/projects/{pay}", token=G_TOKEN)  # the owner archives Payments
            _api(page, "PUT", "/api/settings/remote", {"enabled": remote == "on"}, token=G_TOKEN)
            self._open(page)
            _readable(_row(page, AGENT).locator('[data-testid="project-grant-summary"]'), PAYMENTS.upper())
            self._open_projects(page)
            line = _line(page, AGENT, pay)
            _readable(line.locator('[data-testid="project-archived"]'), P["archived"])
            _readable(line.locator('[data-testid="project-grant-chip"]'), P["live"])
            _readable(line.locator('[data-testid="project-grant-verb"]'), P["stop"])
            # Hiring (active, never granted) still offers Allow; the archived line never does.
            _readable(_line(page, AGENT, ids[HIRING]).locator('[data-testid="project-grant-verb"]'), P["allow"])
            _lawful(page, width)
            self._shot(page, f"12-archived-{remote}", width)
            # Stop: the line goes (no Allow on an archived project); the footer keeps its receipt.
            line.locator('[data-testid="project-grant-verb"]').click()
            page.wait_for_function(f"() => !document.querySelector('[data-testid=\"project-line-{pay}\"]')")
            assert _grant_rows(self.db_path) == [(pay, "REVOKED", "owner_revoked")]
            if remote == "off":
                # OFF: with no LIVE authority left, the credential row goes too.
                assert _g_remote(page).locator(".surface-ledger-primary", has_text=AGENT).count() == 0
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "STOPPED")
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            for word in ("SUCCEEDED", P["stopped"], PAYMENTS, AGENT, "BY OWNER"):
                _readable(well, word)
            receipt = _kernel(page, well.get_attribute("data-operation-id"))
            assert (receipt["operation"]["name"], receipt["receipt"]["state"]) == ("project.delegation.revoke", "succeeded")
            _lawful(page, width)
            self._shot(page, f"12-archived-stopped-{remote}", width)
            assert errors == [], errors
            browser.close()
