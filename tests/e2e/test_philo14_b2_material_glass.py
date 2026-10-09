"""PHILO-14 B2: the material pass, on a real hub (PROPOSAL §3 Movement B).

The bevel grammar (contract.md "The bevel grammar") on the live faces: the
Chair, Needs you, a Project drawer, the Conductor, an agent's lane and
Settings, at 1440 and 393. A real hub on an isolated HOME, seeded with the
hub's own producers (the C4 agents seed and the A2 Project seed). Nothing
leaves the machine.

On every face the rig reads the computed material, not the class names:

- a plated library Button is raised (`--bevel-raised`); pressed it sinks;
- a pressable token (FilterTokens, ProjectButton) wears the light bevel
  (`--bevel-raised-soft`), the active filter sunken (`--bevel-sunken-soft`);
- a StateChip is a lamp: no plate, a lit square beside its word;
- a `surface-token[data-chip]` fact is flat: no plate, no bevel;
- a window body wears the well (`--bevel-sunken`).

Shots to `.tmp/evidence-shots/B2-<face>-<width>.png`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle
from .test_philo14_a2_drawer_glass import PROJECT, _seed as _seed_drawer
from .test_philo14_c4_conductor_glass import _seed as _seed_agents

pytest.importorskip("playwright.sync_api", reason="the material glass needs Playwright")

TOKEN = "p14-b2-material"
SHOTS = evidence_dir("")
SIZES = {1440: 900, 393: 852}
T = 20_000
LAMP_WORDS = {"success": "OK", "working": "WORKING", "warning": "WARN", "failure": "FAILED", "active": "ASKS"}

# The material of one face, read from the computed styles.
MATERIAL_JS = r"""(root) => {
  const scope = root ? document.querySelector(root) : document;
  if (!scope) return null;
  // Each token resolved on a fresh probe (an unknown token would read "none").
  const resolve = (value) => {
    const probe = document.createElement('div');
    probe.style.boxShadow = value;
    document.body.appendChild(probe);
    const v = getComputedStyle(probe).boxShadow;
    probe.remove();
    return v;
  };
  const raised = resolve('var(--bevel-raised)');
  const sunken = resolve('var(--bevel-sunken)');
  const soft = resolve('var(--bevel-raised-soft)');
  const softSunken = resolve('var(--bevel-sunken-soft)');
  // On the Steel plate (the title bar: Raw) the grammar rides --wb-raised.
  const wbRaised = resolve('var(--wb-raised)');
  const wbSunken = resolve('var(--wb-sunken)');
  const seen = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const TOKEN = '.surface-filter-token, .surface-project-button';
  const btns = [...scope.querySelectorAll('.btn:not(:disabled):not([aria-pressed="true"])')]
    .filter(seen).filter((b) => !b.matches(TOKEN));
  const tokens = [...scope.querySelectorAll('.surface-filter-token.btn:not(:disabled), .surface-project-button.btn:not(:disabled)')].filter(seen);
  const chips = [...scope.querySelectorAll('.surface-state-chip')].filter(seen);
  const facts = [...scope.querySelectorAll('.surface-token[data-chip]')].filter(seen);
  const BODY = '.desk-pullout-body, .desk-surface-body, .chair-window-body';
  const bodies = [...scope.querySelectorAll(BODY)].filter(seen)
    .filter((b) => !b.parentElement || !b.parentElement.closest(BODY));
  return {
    raised, sunken, soft, softSunken, wbRaised, wbSunken,
    tokens: tokens.map((t) => ({ name: (t.textContent || '').trim().slice(0, 40),
      active: t.hasAttribute('data-filter-active'), shadow: getComputedStyle(t).boxShadow })),
    buttons: btns.map((b) => ({ name: (b.textContent || '').trim().slice(0, 40), shadow: getComputedStyle(b).boxShadow })),
    chips: chips.map((c) => {
      const lamp = c.querySelector('.surface-state-chip-icon');
      const s = getComputedStyle(c);
      const l = lamp ? getComputedStyle(lamp) : null;
      const glyph = lamp ? lamp.textContent : '';
      return { name: c.getAttribute('aria-label'), state: c.dataset.state,
               word: (c.textContent || '').slice(glyph.length).trim(),
               border: s.borderTopWidth, bg: s.backgroundColor,
               lampW: l ? l.width : null, lampShadow: l ? l.boxShadow : null };
    }),
    facts: facts.map((f) => { const s = getComputedStyle(f); const b = getComputedStyle(f, '::before');
      return { text: (f.textContent || '').slice(0, 30), tone: f.dataset.tone || null,
               border: s.borderTopColor, shadow: s.boxShadow, bg: s.backgroundColor,
               lampW: b.content === 'none' ? null : b.width, lampShadow: b.boxShadow }; }),
    bodies: bodies.map((b) => getComputedStyle(b).boxShadow),
  };
}"""


def _assert_material(page: Any, face: str, root: str | None = None) -> dict[str, Any]:
    m = page.evaluate(MATERIAL_JS, root)
    assert m is not None, face
    raised, sunken = m["raised"], m["sunken"]
    assert "none" not in (raised, sunken, m["soft"], m["softSunken"]), m
    for b in m["buttons"]:
        assert b["shadow"].startswith((raised, m["wbRaised"])), (face, b, raised)
    for t in m["tokens"]:
        assert t["shadow"].startswith(m["softSunken"] if t["active"] else m["soft"]), (face, t)
    for c in m["chips"]:
        assert c["border"] == "0px", (face, c)
        assert c["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), (face, c)
        assert c["lampW"] == "10px", (face, c)
        assert c["lampShadow"].startswith(raised), (face, c)
        # Never colour alone: every lamp is named; a shown word IS its name;
        # a lit lamp with no word of its own is named by its state word.
        assert (c["name"] or "").strip(), (face, c)
        if c["word"]:
            assert c["name"] == c["word"], (face, c)
        elif c["state"] in LAMP_WORDS:
            assert c["name"] == LAMP_WORDS[c["state"]], (face, c)
    for f in m["facts"]:
        # The 1 px border stays, transparent, so no row moves.
        assert f["border"] == "rgba(0, 0, 0, 0)" and f["shadow"] == "none", (face, f)
        assert f["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), (face, f)
        if f["tone"] in ("warn", "danger", "ok"):
            assert f["lampW"] == "10px" and f["lampShadow"].startswith(raised), (face, f)
    for shadow in m["bodies"]:
        assert shadow.startswith(sunken), (face, shadow, sunken)
    return m


def _shoot(page: Any, name: str, width: int) -> None:
    _settle(page)
    page.wait_for_timeout(300)
    page.screenshot(path=str(SHOTS / f"B2-{name}-{width}.png"))


@pytest.mark.e2e
@pytest.mark.timeout(300)
def test_the_material_on_six_faces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.agent_context import event_log

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from holdspeak.db import get_database

        _seed_agents(tmp_path / "home")
        _seed_drawer(get_database())
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in SIZES.items():
                ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1,
                                          has_touch=width < 720, reduced_motion="reduce")
                page = ctx.new_page()
                page.set_default_timeout(45_000)
                page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)

                # 1. The Chair screen.
                page.reload(wait_until="load")
                _normal_chair(page)
                _shoot(page, "chair", width)
                _assert_material(page, f"chair-{width}", ".chair")

                # 2. Needs you (the smart drawer on the screen).
                needs_icon = page.locator(".desk-screen [data-object-id='drawer:needs']")
                needs_icon.wait_for(timeout=T)
                needs_icon.focus()
                page.keyboard.press("Enter")
                needs = page.locator(".desk-window-shell.chair-window[aria-label='Needs you']")
                needs.wait_for(timeout=T)
                _shoot(page, "needs", width)
                _assert_material(page, f"needs-{width}", ".desk-window-shell.chair-window[aria-label='Needs you']")

                # 3. A Project drawer.
                page.goto(f"{url}/?token={TOKEN}&open=project:{PROJECT}", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.wait_for(timeout=T)
                drawer.locator("[data-testid=drawer-facts]").wait_for(timeout=T)
                _shoot(page, "drawer", width)
                _assert_material(page, f"drawer-{width}", ".drawer-window")

                # 4. The Conductor.
                page.goto(f"{url}/conductor", wait_until="load")
                _normal_chair(page)
                window = page.locator(".conductor-window")
                window.wait_for(timeout=T)
                asking = window.locator("[data-object-id='launch:launch_c4_runbook']")
                asking.wait_for(timeout=T)
                asking.click()
                _shoot(page, "conductor", width)
                _assert_material(page, f"conductor-{width}", ".conductor-window")

                # 5. The asking agent's lane.
                window.get_by_role("button", name="Open", exact=True).click()
                lane = page.locator(".is-lane")
                lane.wait_for(timeout=T)
                lane.locator("[data-testid='lane-rail']").wait_for(timeout=T)
                _shoot(page, "lane", width)
                _assert_material(page, f"lane-{width}", ".is-lane")

                # 6. Settings.
                page.goto(f"{url}/settings", wait_until="load")
                _normal_chair(page)
                settings = page.locator(".desk-window[aria-label='Settings']")
                settings.wait_for(timeout=T)
                _shoot(page, "settings", width)
                _assert_material(page, f"settings-{width}", ".desk-window[aria-label='Settings']")

                # A pressed plated Button sinks (:active, the grammar).
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

                if width == 393:
                    assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")
                _assert_clean(page, errors)
                ctx.close()
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.timeout(240)
@pytest.mark.parametrize("width", [1440, 393])
def test_a_held_filter_strip_is_flat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Astra r1 on #958: Settings → People under the environment override
    holds the access (the strip is the disabled Button state): every token
    is flat, the held value has no tint, through the real settings API."""
    _ensure_build()
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "read")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": SIZES[width]}, reduced_motion="reduce")
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            wire = _api(page, "GET", "/api/settings/people-access", token=TOKEN)
            assert wire["source"] == "env" and wire["effective"] == "read", wire
            page.goto(f"{url}/settings", wait_until="load")
            _normal_chair(page)
            row = page.locator(".surface-ledger-row", has=page.locator(".surface-ledger-primary", has_text="People"))
            row.get_by_role("button", name="Open", exact=True).click()
            strip = page.get_by_role("group", name="People MCP access", exact=True)
            strip.wait_for(timeout=T)
            _settle(page)
            strip.scroll_into_view_if_needed()
            tokens = strip.locator("button").evaluate_all("""bs => bs.map((b) => {
                const s = getComputedStyle(b);
                // Phase 16: the window remaps --disabled-bg (A1's interior),
                // so the ground is read where the token sits, not on <body>.
                const probe = document.createElement('div');
                probe.style.background = 'var(--disabled-bg)';
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
