"""PHILO-14 A0c: the list species show the 32 px set drawn at 32, on glass.

A real hub on an isolated HOME and the built bundle. The drawer (seeded as
the A2 glass seeds it) and the Conductor (seeded as the C4 glass seeds it)
are switched to their List view; the Components window's object-species
gallery holds the other list species (Needs you rows, the confirm line, the
PR card). In Chromium, every list-row sprite is a file under
`desk/sprites/32/` whose natural size is 32 x 32 (drawn at 32, shown 1:1),
and every icon-view sprite stays the 64 px file. The lane window opened from
the Conductor wears the 32 px sprite of ITS agent in its title bar: the
Codex launch's lane loads `32/agent-codex.png` (identity, not size alone).

Shots (1440 and 393) to `.tmp/evidence-shots/p14-a0c/`: the drawer's list,
the Conductor's list, the gallery's Needs you rows and the lane. The shots
are taken before the checks, so the same file run on main gives the
"before" shots.

WHAT IT DOES NOT PROVE: the Needs you drawer of lane A5 (not on main yet; it
composes NeedsRow, which this lane wires); a real phone.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the A0c glass needs Playwright")

TOKEN = "p14-a0c-list"
SHOTS = evidence_dir("p14-a0c")
SIZES = ((1440, 900), (393, 852))
T = 20_000

_SPRITES_JS = """(root) => [...root.querySelectorAll(SEL)].map((img) => ({
  src: img.getAttribute('src') || '', w: img.naturalWidth, h: img.naturalHeight,
  shown: Math.round(parseFloat(getComputedStyle(img).width)),
}))"""


def _sprites(scope: Any, selector: str) -> list[dict[str, Any]]:
    scope.locator(selector).first.wait_for(state="attached", timeout=T)
    scope.page.wait_for_function(
        "(sel) => [...document.querySelectorAll(sel)].every((i) => i.complete && i.naturalWidth > 0)",
        arg=selector, timeout=T)
    return scope.evaluate(_SPRITES_JS.replace("SEL", repr(selector)))


def _assert_32(found: list[dict[str, Any]], where: str) -> None:
    assert found, f"{where}: no sprite"
    for s in found:
        assert "/desk/sprites/32/" in s["src"], (where, s)
        assert (s["w"], s["h"]) == (32, 32), (where, s)


def _list_view(page: Any, group: str) -> None:
    """Press List in a view strip (at 393 the strip may fold into one menu)."""
    strip = page.get_by_role("group", name=group)
    strip.wait_for(timeout=T)
    direct = strip.get_by_role("button", name="List", exact=True)
    if direct.count():
        direct.click()
    else:
        strip.get_by_role("button").first.click()
        page.get_by_role("menuitemradio", name="List").or_(page.get_by_role("menuitem", name="List")).first.click()
    _settle(page)


@pytest.mark.e2e
@pytest.mark.timeout(300)
def test_the_list_species_wear_the_32px_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.agent_context import event_log

    from . import test_philo14_a2_drawer_glass as a2
    from . import test_philo14_c4_conductor_glass as c4

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    checks: list[tuple[str, list[dict[str, Any]]]] = []
    identity: list[tuple[str, str, list[dict[str, Any]]]] = []
    icons: list[dict[str, Any]] = []
    try:
        from holdspeak.db import get_database

        a2._seed(get_database())
        c4._seed(tmp_path / "home")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            for width, height in SIZES:
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                page.set_default_timeout(45_000)
                page.on("pageerror", lambda e: errors.append(str(e)[:200]))
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "PUT", f"/api/projects/{a2.PROJECT}/resources/note:n-risks", {}, token=TOKEN)

                # 1. The drawer, icons first (the 64 stays), then its List.
                page.goto(f"{url}/?token={TOKEN}&open=project:{a2.PROJECT}", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.wait_for(timeout=T)
                page.wait_for_function(
                    "() => document.querySelectorAll('.drawer-window [data-object-id]').length > 0", timeout=T)
                _settle(page)
                if drawer.locator(".desk-icon-art > img").count():
                    icons += _sprites(drawer, ".desk-icon-art > img:first-child")
                _list_view(page, "Drawer view")
                drawer.locator(".object-list-row").first.wait_for(timeout=T)
                page.wait_for_timeout(300)
                page.screenshot(path=str(SHOTS / f"drawer-list-{width}.png"))
                checks.append((f"drawer list {width}", _sprites(drawer, ".object-list-open img")))

                # 2. The Conductor's List.
                page.goto(f"{url}/conductor?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                window = page.locator(".conductor-window")
                window.wait_for(timeout=T)
                window.locator("[data-object-id='launch:launch_c4_runbook']").wait_for(timeout=T)
                _settle(page)
                _list_view(page, "Conductor view")
                window.locator(".object-list-row").first.wait_for(timeout=T)
                page.wait_for_timeout(300)
                page.screenshot(path=str(SHOTS / f"conductor-list-{width}.png"))
                checks.append((f"conductor list {width}", _sprites(window, ".object-list-open img")))
                # Identity, not size alone (Astra r1 on #956): each agent row wears ITS agent.
                identity.append((f"conductor codex row {width}", "agent-codex", _sprites(
                    window, ".object-list-row[data-object-id='launch:launch_c4_recon'] .object-list-open img")))
                identity.append((f"conductor claude row {width}", "agent-claude-code", _sprites(
                    window, ".object-list-row[data-object-id='launch:launch_c4_runbook'] .object-list-open img")))

                # 3a. The Codex launch's lane: its title wears the Codex sprite.
                window.locator(".object-list-row[data-object-id='launch:launch_c4_recon'] button").first.click()
                window.get_by_role("button", name="Open", exact=True).click()
                codex_lane = page.locator(".is-lane")
                codex_lane.wait_for(timeout=T)
                codex_lane.locator("[data-testid='lane-rail']").wait_for(timeout=T)
                page.wait_for_timeout(300)
                page.screenshot(path=str(SHOTS / f"lane-codex-{width}.png"))
                identity.append((f"codex lane title {width}", "agent-codex",
                                 _sprites(page.locator("body"), ".is-lane .desk-session-glyph")))
                page.goto(f"{url}/conductor?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                window = page.locator(".conductor-window")
                window.wait_for(timeout=T)
                window.locator(".object-list-row").first.wait_for(timeout=T)
                _settle(page)

                # 3. The lane opened from the asking agent's row.
                window.locator(".object-list-row[data-object-id='launch:launch_c4_runbook'] button").first.click()
                window.get_by_role("button", name="Open", exact=True).click()
                lane = page.locator(".is-lane")
                lane.wait_for(timeout=T)
                lane.locator("[data-testid='lane-rail']").wait_for(timeout=T)
                page.wait_for_timeout(300)
                page.screenshot(path=str(SHOTS / f"lane-{width}.png"))
                checks.append((f"lane title icon {width}", _sprites(page.locator("body"), ".is-lane .desk-session-glyph")))

                # 4. The gallery: Needs you rows, the confirm line, the PR card, the list.
                page.goto(f"{url}/design/components?token={TOKEN}", wait_until="load")
                gallery = page.locator("[data-testid=object-species-gallery]")
                gallery.wait_for(state="attached", timeout=T)
                needs = gallery.locator(".needs-list").first
                needs.scroll_into_view_if_needed()
                _settle(page)
                page.wait_for_timeout(300)
                page.screenshot(path=str(SHOTS / f"needs-you-{width}.png"))
                for name, sel in (("needs rows", ".needs-row > img"), ("object list", ".object-list-open img"),
                                  ("confirm line", ".confirm-line-ends img"), ("pr card", ".pr-card-line img")):
                    if gallery.locator(sel).count():
                        checks.append((f"gallery {name} {width}", _sprites(gallery, sel)))
                page.close()
            browser.close()
    finally:
        server.stop()

    for where, found in checks:
        _assert_32(found, where)
    # The list cell shows the 32 at 1:1 (the Needs row's 40 px cell pads it).
    for where, found in checks:
        if "lane title" in where:
            continue
        assert all(s["shown"] == 32 for s in found), (where, found)
    for where, name, found in identity:
        assert found, where
        for s in found:
            assert s["src"].endswith(f"/desk/sprites/32/{name}.png"), (where, s)
    # The icon view keeps the 64 px set.
    assert icons, "no drawer icon read"
    for s in icons:
        assert "/desk/sprites/32/" not in s["src"] and (s["w"], s["h"]) == (64, 64), s
    assert not errors, errors
