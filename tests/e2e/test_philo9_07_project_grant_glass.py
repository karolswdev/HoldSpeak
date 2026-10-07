"""PHILO-9-07 -- the project delegation grant on the Remote Access ledger, fenced AS RENDERED.

The owner-ratified canvas (``pm/roadmap/holdspeak-philo/phase-9-the-room-on-
the-contract/assets/story-07-grant-canvas/README.md``, set A: "Ratify as
drawn") built into the real Settings window, driven through the REAL hub, the
REAL grant, credential and project routes and the REAL kernel, at 1440 x 900
and 393 x 852. After each transition the fence reads the RENDERED window:

* ``readable_text`` -- visible, in the viewport, nothing covers it;
* every verb is the library Button and owns its target at nine points
  (``elementFromPoint`` AND a real ``pointermove``: centre, four corners, four
  edge midpoints, inset 1 px; the painted face at 1440, the 44 px target at
  393), the ``Projects`` Disclosure and the footer receipt included;
* no text under 12 px in the window (a lone glyph exempt, UX-CANON C), no
  horizontal overflow, every chip and token at 4.5:1 or more against its
  composited background;
* no dialog, no popover: the per-project list opens in place.

The words come from the constants the face imports (``PROJECT_GRANT_WORDS``,
``GRANT_WORDS``), read here from the source.

Red on main: no ``Projects`` Disclosure, no project line, ``desk-agent``
reads ``ALL``, ``Allow filing`` on a PROJECT credential (``red_face`` below).
"""
from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path
from typing import Any

import pytest

import holdspeak.principals as principals
from holdspeak.principals import AgentCredentialStore

from .glass_infra import REPO, _api, _api_allow_error, _boot, _ensure_build, _settle
from .test_hs174_remote_settings_glass import _navigate_to_settings_hub, _open_system_module
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the grant glass needs Playwright")

TOKEN = "hs174-remote-settings"  # the HS-174 navigation helpers use this token
AGENT = "sweep-runner"
DESK_AGENT = "desk-agent"
PAYMENTS, HIRING = "Payments ledger cutover", "Hiring loop"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-shots")
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

_OWNS_JS = """(el, target44) => {
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
    // PHILO-14 B2: a lead StateChip with no word is a lamp (its glyph is
    // not drawn); a lamp is no text, so it has no text contrast to read.
    if (/^[●○✓✗⚠—↻ℹ«»·▸▾◆?]$/.test(txt(el))) continue;
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
    dialogs: document.querySelectorAll('[role=dialog], .modal, .surface-popover, [role=menu]').length,
    top: win.getBoundingClientRect().top,
  };
}"""


def _readable(locator: Any, want: str) -> None:
    locator.first.wait_for(state="visible", timeout=8_000)
    text = (locator.first.inner_text() or "").strip()
    assert want in text, f"{want!r} not in {text!r}"
    locator.first.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = locator.first.evaluate(_OWNS_JS, False)
    assert probe["visible"] and probe["inViewport"], f"{want!r}: not readable: {probe}"
    uncovered = [p for p in probe["points"][:5] if not p["owned"]]
    assert not uncovered, f"{want!r}: covered at {uncovered}"


def _pointer_owned(page: Any, button: Any, label: str) -> None:
    target44 = page.viewport_size["width"] <= 420
    button.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = button.evaluate(_OWNS_JS, target44)
    assert probe["inViewport"], f"{label}: outside the viewport {probe['rect']}"
    page.evaluate("""() => { window.__pm = null; document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, {capture: true}); }""")
    for point in probe["points"]:
        assert point["owned"], f"{label}: elementFromPoint does not reach it at {point} (rect {probe['rect']})"
        page.mouse.move(point["x"], point["y"])
        reached = button.evaluate("(el) => !!window.__pm && (window.__pm === el || el.contains(window.__pm))")
        assert reached, f"{label}: a real pointermove at {point} lands elsewhere"


def _lawful(page: Any, width: int) -> dict[str, Any]:
    """Every state: the library Button owns its nine points; no small text, no overflow, contrast >= 4.5."""
    buttons = _remote(page).locator("button")
    for i in range(buttons.count()):
        button = buttons.nth(i)
        if button.evaluate("(el) => !!el.closest('.gadget-cycle, select')"):
            continue
        assert "btn" in (button.get_attribute("class") or ""), f"a verb that is not the library Button: {button.inner_text()!r}"
        _pointer_owned(page, button, f"{button.inner_text()!r} at {width}")
    foot = page.locator('[data-testid="foot-receipt"]')
    if foot.count():
        _pointer_owned(page, foot.first, f"the footer receipt at {width}")
    page.mouse.move(0, 0)
    facts = page.evaluate(_WINDOW_FACTS)
    assert facts["small"] == [], f"text under 12 px in the Settings window: {facts['small'][:5]}"
    assert facts["raw"] == [], f"a raw <button>: {facts['raw']}"
    assert facts["low"] == [], f"a chip or token under 4.5:1: {facts['low']}"
    assert not facts["overflow"], "horizontal overflow"
    assert facts["dialogs"] == 0, "a dialog, popover or menu is open: the pick is in place"
    return facts


def _remote(page: Any) -> Any:
    return page.locator(".gadget-group", has=page.locator(".gadget-group-label", has_text="Remote access")).last


def _row(page: Any, identity: str) -> Any:
    return _remote(page).locator(".surface-ledger-row", has=page.locator(".surface-ledger-primary", has_text=identity)).first


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
    return _api(page, "GET", f"/api/kernel/read?refs=operation:{operation_id}&view=receipt", token=TOKEN)["objects"][0]


class _Rig:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        monkeypatch.setattr(principals, "agent_credentials", AgentCredentialStore())
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
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
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/settings/remote", {"enabled": True}, token=TOKEN)
        tokens = {}
        if credentials:
            for identity, palette in ((DESK_AGENT, "DESK"), (AGENT, "PROJECT")):
                tokens[identity] = _api(page, "POST", "/api/settings/remote/credentials",
                                        {"identity": identity, "palette": palette}, token=TOKEN)["token"]
        pids = {name: _api(page, "POST", "/api/projects", {"name": name}, token=TOKEN)["project"]["id"]
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
        SHOTS.mkdir(parents=True, exist_ok=True)
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
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"), full_page=False)


class TestProjectGrantGlass(_Rig):

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_allow_stop_refused_and_two_projects_on_the_rendered_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            pay, hire = ids[PAYMENTS], ids[HIRING]
            self._open(page)

            # Board 1: never granted. The PROJECT row has Projects and no desk
            # verb; desk-agent reads DESK and keeps its desk verb.
            row = _row(page, AGENT)
            _readable(row.locator("button", has_text=P["projects"]), P["projects"])
            assert row.locator('[data-testid="grant-verb"]').count() == 0, "a PROJECT credential offers the desk grant"
            _readable(_row(page, DESK_AGENT).locator('[data-testid="palette-token"]'), "DESK")
            _readable(_row(page, DESK_AGENT).locator('[data-testid="grant-verb"]'), W["allow"])
            _readable(row.locator('[data-testid="palette-token"]'), "PROJECT")
            self._open_projects(page)
            for pid in (pay, hire):
                assert _line(page, AGENT, pid).locator('[data-testid="project-grant-chip"]').count() == 0
                _readable(_line(page, AGENT, pid).locator('[data-testid="project-grant-verb"]'), P["allow"])
            _lawful(page, width)
            self._shot(page, "1-never", width)

            # Allow on Payments: ALLOWED + Stop; Hiring unchanged; the foot's receipt is the kernel's.
            _line(page, AGENT, pay).locator('[data-testid="project-grant-verb"]').click()
            chip = _line(page, AGENT, pay).locator('[data-testid="project-grant-chip"]')
            chip.wait_for(timeout=8_000)
            _readable(chip, P["live"])
            assert chip.get_attribute("data-state") == "success"
            _readable(_line(page, AGENT, pay).locator('[data-testid="project-grant-verb"]'), P["stop"])
            assert _line(page, AGENT, hire).locator('[data-testid="project-grant-chip"]').count() == 0
            _readable(_line(page, AGENT, hire).locator('[data-testid="project-grant-verb"]'), P["allow"])
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "ALLOWED")
            granted = _kernel(page, foot.get_attribute("data-operation-id"))
            assert (granted["operation"]["name"], granted["receipt"]["state"]) == ("project.delegation.grant", "succeeded")
            assert _grant_rows(self.db_path) == [(pay, "LIVE", "")]
            _lawful(page, width)
            self._shot(page, "3-live-open", width)

            # Closed: the row names the one live project.
            _row(page, AGENT).locator("button", has_text=P["projects"]).click()
            summary = _row(page, AGENT).locator('[data-testid="project-grant-summary"]')
            _readable(summary, P["live"])
            _readable(summary, PAYMENTS.upper())
            _lawful(page, width)
            self._shot(page, "2-live", width)

            # Stop: STOPPED + Allow; the receipt is owner_revoked.
            self._open_projects(page)
            _line(page, AGENT, pay).locator('[data-testid="project-grant-verb"]').click()
            page.wait_for_function("(w) => [...document.querySelectorAll('[data-testid=\"project-grant-chip\"]')].some(e => e.textContent.includes(w))", arg=P["stopped"])
            chip = _line(page, AGENT, pay).locator('[data-testid="project-grant-chip"]')
            _readable(chip, P["stopped"])
            assert chip.get_attribute("data-state") == "idle"
            _readable(_line(page, AGENT, pay).locator('[data-testid="project-grant-verb"]'), P["allow"])
            _readable(foot, "STOPPED")
            assert _kernel(page, foot.get_attribute("data-operation-id"))["operation"]["name"] == "project.delegation.revoke"
            assert _grant_rows(self.db_path)[-1] == (pay, "REVOKED", "owner_revoked")
            assert _row(page, AGENT).locator('[data-testid="project-grant-summary"]').count() == 0
            _lawful(page, width)
            self._shot(page, "4-stopped", width)

            # A refused Stop: another owner request stopped it first; the face still said LIVE.
            _line(page, AGENT, pay).locator('[data-testid="project-grant-verb"]').click()
            page.wait_for_function("(w) => [...document.querySelectorAll('[data-testid=\"project-grant-chip\"]')].some(e => e.textContent.includes(w))", arg=P["live"])
            _api(page, "DELETE", f"/api/settings/remote/delegations/{AGENT}/projects/{pay}", token=TOKEN)
            _line(page, AGENT, pay).locator('[data-testid="project-grant-verb"]').click()
            refused = _line(page, AGENT, pay).locator('[data-testid="grant-refused"]')
            refused.wait_for(timeout=8_000)
            assert refused.get_attribute("data-code") == "project_delegation_required"
            _readable(refused, "CANNOT STOP")
            _readable(refused, "NO GRANT")
            _readable(foot, "REFUSED")
            _readable(_line(page, AGENT, pay).locator('[data-testid="project-grant-chip"]'), P["stopped"])
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            for word in ("REFUSED", P["actStop"], "NO GRANT", PAYMENTS, AGENT, "BY OWNER"):
                _readable(well, word)
            assert well.get_attribute("data-operation-id") == foot.get_attribute("data-operation-id")
            refusal = _kernel(page, well.get_attribute("data-operation-id"))
            assert (refusal["operation"]["name"], refusal["receipt"]["outcome"]) == (
                "project.delegation.revoke", "project_delegation_required")
            _lawful(page, width)
            self._shot(page, "8-refused", width)

            # Two live projects: the closed row counts them.
            foot.click()
            for pid in (pay, hire):
                _line(page, AGENT, pid).locator('[data-testid="project-grant-verb"]').click()
                page.wait_for_function(
                    "([sel, w]) => document.querySelector(sel)?.textContent.includes(w)",
                    arg=[f'[data-testid="project-line-{pid}"] [data-testid="project-grant-chip"]', P["live"]])
            _row(page, AGENT).locator("button", has_text=P["projects"]).click()
            _readable(_row(page, AGENT).locator('[data-testid="project-grant-summary"]'), "2 PROJECTS")
            _lawful(page, width)
            self._shot(page, "9-two-projects", width)
            assert errors == [], errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_an_expired_grant_reads_stopped(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{ids[PAYMENTS]}",
                 {"expires_at": time.time() + 1.0}, token=TOKEN)
            time.sleep(1.4)
            assert [s for _p, s, _r in _grant_rows(self.db_path)] == ["LIVE"], "the stored row is still LIVE"
            self._open(page)
            assert _row(page, AGENT).locator('[data-testid="project-grant-summary"]').count() == 0
            self._open_projects(page)
            chip = _line(page, AGENT, ids[PAYMENTS]).locator('[data-testid="project-grant-chip"]')
            _readable(chip, P["stopped"])
            _readable(_line(page, AGENT, ids[PAYMENTS]).locator('[data-testid="project-grant-verb"]'), P["allow"])
            assert page.locator('[data-testid="foot-receipt"]').count() == 0, "expiry is not an owner act: no receipt"
            _lawful(page, width)
            self._shot(page, "5-expired", width)
            assert errors == [], errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_live_grants_with_no_credential_show_on_and_off_and_the_last_stop_keeps_its_receipt(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            pay = ids[PAYMENTS]
            _api(page, "PUT", f"/api/settings/remote/delegations/{DESK_AGENT}", {}, token=TOKEN)
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{pay}", {}, token=TOKEN)
            # Both credentials lost with their grants LIVE (a restart; never an owner revoke).
            for identity in (DESK_AGENT, AGENT):
                status, _ = _api_allow_error(page, "DELETE", "/api/principals/self", token=ids[f"token:{identity}"])
                assert status == 200
            self._open(page)
            desk_orphan = _remote(page).locator('[data-testid^="delegation-row-"]')
            project_orphan = _remote(page).locator('[data-testid^="project-delegation-row-"]')
            _readable(desk_orphan, DESK_AGENT)
            _readable(desk_orphan.locator('[data-testid="grant-verb"]'), W["stop"])
            _readable(project_orphan, AGENT)
            _readable(project_orphan, PAYMENTS.upper())
            _readable(project_orphan, W["noCredential"])
            _readable(project_orphan.locator('[data-testid="project-grant-chip"]'), P["live"])
            _readable(project_orphan.locator('[data-testid="project-grant-verb"]'), P["stop"])
            _lawful(page, width)
            self._shot(page, "6-orphan", width)

            _api(page, "PUT", "/api/settings/remote", {"enabled": False}, token=TOKEN)
            self._open(page)
            _readable(_remote(page).locator('[data-testid^="delegation-row-"] [data-testid="grant-verb"]'), W["stop"])
            _readable(_remote(page).locator('[data-testid^="project-delegation-row-"] [data-testid="project-grant-verb"]'), P["stop"])
            assert _remote(page).locator('[data-testid="issue-credential-btn"]').count() == 0
            _lawful(page, width)
            self._shot(page, "7-orphan-off", width)

            # Stop the desk orphan, then the last one: the project orphan.
            _remote(page).locator('[data-testid^="delegation-row-"] [data-testid="grant-verb"]').click()
            page.wait_for_function("() => document.querySelectorAll('[data-testid^=\"delegation-row-\"]').length === 0")
            _remote(page).locator('[data-testid^="project-delegation-row-"] [data-testid="project-grant-verb"]').click()
            page.wait_for_function("() => document.querySelectorAll('[data-testid^=\"project-delegation-row-\"]').length === 0")
            assert _remote(page).locator(".surface-ledger").count() == 0, "the ledger stayed with nothing to show"
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "STOPPED")
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            for word in ("SUCCEEDED", P["stopped"], PAYMENTS, AGENT, "BY OWNER"):
                _readable(well, word)
            assert _remote(page).locator(".surface-ledger [data-testid='grant-receipt']").count() == 0
            assert _grant_rows(self.db_path)[-1] == (pay, "REVOKED", "owner_revoked")
            _lawful(page, width)
            self._shot(page, "10-last-orphan-stopped", width)
            assert errors == [], errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_remote_off_keeps_a_credential_with_a_live_project_grant(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{ids[PAYMENTS]}", {}, token=TOKEN)
            _api(page, "PUT", "/api/settings/remote", {"enabled": False}, token=TOKEN)
            self._open(page)
            assert _remote(page).locator(".surface-ledger-primary", has_text=DESK_AGENT).count() == 0
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
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            pay = ids[PAYMENTS]
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{pay}", {}, token=TOKEN)
            self._open(page)
            _readable(_row(page, AGENT).locator('[data-testid="project-grant-summary"]'), P["live"])
            before = page.evaluate(_WINDOW_FACTS)["top"]
            _row(page, AGENT).locator('[data-testid="credential-revoke"]').click()
            page.wait_for_function(f"() => ![...document.querySelectorAll('.surface-ledger-primary')].some(e => e.textContent.includes('{AGENT}'))")
            assert _remote(page).locator('[data-testid^="project-delegation-row-"]').count() == 0, "an owner revoke left an orphan"
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
        """Archive -> the line stays (ARCHIVED, Stop only) -> Stop -> the line goes, the receipt stays;
        with Remote Access ON and OFF (Codex Astra r2: Stop pressed in both states)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            ids = self._world(page)
            pay = ids[PAYMENTS]
            _api(page, "PUT", f"/api/settings/remote/delegations/{AGENT}/projects/{pay}", {}, token=TOKEN)
            _api(page, "DELETE", f"/api/projects/{pay}", token=TOKEN)  # the owner archives Payments
            _api(page, "PUT", "/api/settings/remote", {"enabled": remote == "on"}, token=TOKEN)
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
                assert _remote(page).locator(".surface-ledger-primary", has_text=AGENT).count() == 0
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
