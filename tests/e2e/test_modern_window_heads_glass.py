"""Shared window-head geometry on the real Speak surface.

This is deliberately a small browser check. CSS and React unit tests cannot
prove that the feedback and depth controls keep their hit ownership while a
real window changes from a desktop frame to a narrow sheet.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows

pytest.importorskip("playwright.sync_api", reason="the window-head glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "modern-window-heads-glass"
SHOTS = evidence_dir("modern-window-heads")
SIZES = ((1440, 900), (393, 852), (280, 800))
T = 30_000


def _open_speak(page: Any, base: str) -> Any:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    clear_hub_windows(page, TOKEN)
    page.goto(f"{base}/dictation?token={TOKEN}", wait_until="load")
    _normal_chair(page)
    window = page.locator(".desk-window-shell[aria-label='Speak']")
    window.wait_for(timeout=T)
    _settle(page)
    return window


def _head_facts(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const shell = document.querySelector('.desk-window-shell.is-front');
          const head = shell?.querySelector(':scope > .desk-pullout-head');
          if (!shell || !head) return {error: 'front window head missing'};
          const sr = shell.getBoundingClientRect();
          const hr = head.getBoundingClientRect();
          const depth = head.querySelector('.desk-gadget-depth');
          const depthRect = depth?.getBoundingClientRect();
          const shellStyle = getComputedStyle(shell);
          const shellInteriorRight = sr.right - (parseFloat(shellStyle.borderRightWidth) || 0);
          const actions = [...head.querySelectorAll('button')].filter((b) => {
            const r = b.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
          }).map((button) => {
            const r = button.getBoundingClientRect();
            const x = r.left + r.width / 2;
            const y = r.top + r.height / 2;
            const hit = document.elementFromPoint(x, y);
            return {
              name: button.getAttribute('aria-label') || button.textContent?.trim(),
              left: r.left, right: r.right, top: r.top, bottom: r.bottom,
              centerOwned: hit === button || button.contains(hit),
            };
          });
          return {
            shell: {left: sr.left, right: sr.right, top: sr.top, bottom: sr.bottom},
            head: {left: hr.left, right: hr.right, top: hr.top, bottom: hr.bottom},
            depthRight: depthRect?.right ?? null,
            shellInteriorRight,
            actions,
            fixedActions: [...head.querySelectorAll('.desk-gadget')].filter((b) => {
              const r = b.getBoundingClientRect();
              return r.width > 0 && r.height > 0;
            }).map((button) => button.getAttribute('aria-label') || button.textContent?.trim()),
            folded: Boolean(head.querySelector('.desk-wings.is-folded')),
            feedback: Boolean(head.querySelector('.desk-gadget-feedback')),
          };
        }"""
    )


@pytest.mark.parametrize("width,height", SIZES, ids=[str(width) for width, _ in SIZES])
def test_shared_window_head_stays_inside_frame_when_resized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int
) -> None:
    """Feedback, wings and close/depth keep real bounds and center ownership."""
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
                has_touch=width < 720,
                is_mobile=width < 720,
            )
            page = context.new_page()
            page.set_default_timeout(T)
            window = _open_speak(page, base)
            page.set_viewport_size({"width": width, "height": height})
            page.wait_for_timeout(250)
            _settle(page)

            facts = _head_facts(page)
            assert "error" not in facts, facts
            fixed_names = facts["fixedActions"]
            if width == 1440:
                # The initial Speak seat is intentionally narrow enough to
                # exercise folding. Widen its real right edge, then prove the
                # same strip unfolds without changing any head target.
                edge = window.locator(".desk-window-edge-r")
                edge.wait_for(timeout=T)
                edge_box = edge.bounding_box()
                assert edge_box, "Speak has no right resize edge"
                page.mouse.move(
                    edge_box["x"] + edge_box["width"] / 2,
                    edge_box["y"] + edge_box["height"] / 2,
                )
                page.mouse.down()
                page.mouse.move(
                    edge_box["x"] + edge_box["width"] / 2 + 520,
                    edge_box["y"] + edge_box["height"] / 2,
                    steps=8,
                )
                page.mouse.up()
                page.wait_for_function(
                    "id => document.getElementById(id)?.getBoundingClientRect().width > 900",
                    arg=window.get_attribute("id"),
                    timeout=T,
                )
                page.wait_for_timeout(120)
                widened = _head_facts(page)
                assert not widened["folded"], widened
                assert widened["fixedActions"] == fixed_names, widened
                assert abs(widened["depthRight"] - widened["shellInteriorRight"]) <= 1, widened
                facts = widened
            shell, head = facts["shell"], facts["head"]
            assert head["left"] >= shell["left"] - 1, facts
            assert head["right"] <= shell["right"] + 1, facts
            assert facts["depthRight"] is not None, facts
            assert abs(facts["depthRight"] - facts["shellInteriorRight"]) <= 1, facts
            assert facts["feedback"], facts
            assert all(action["centerOwned"] for action in facts["actions"]), facts
            assert all(
                action["left"] >= shell["left"] - 1
                and action["right"] <= shell["right"] + 1
                for action in facts["actions"]
            ), facts
            if width == 1440:
                # The resize seam must survive both directions. The widened
                # identity returns as the same target set after a phone sheet
                # and then unfolds again at the original viewport.
                page.set_viewport_size({"width": 393, "height": 852})
                page.wait_for_timeout(250)
                _settle(page)
                phone = _head_facts(page)
                assert phone["folded"], phone
                assert phone["fixedActions"] == [
                    "Back from Speak", "Give feedback on Speak", "To back Speak",
                ], phone
                assert all(action["centerOwned"] for action in phone["actions"]), phone
                assert all(
                    action["left"] >= phone["shell"]["left"] - 1
                    and action["right"] <= phone["shell"]["right"] + 1
                    for action in phone["actions"]
                ), phone
                assert abs(phone["depthRight"] - phone["shellInteriorRight"]) <= 1, phone
                page.set_viewport_size({"width": 1440, "height": 900})
                page.wait_for_timeout(250)
                _settle(page)
                restored = _head_facts(page)
                assert not restored["folded"], restored
                assert restored["fixedActions"] == fixed_names, restored
                assert abs(restored["depthRight"] - restored["shellInteriorRight"]) <= 1, restored
            # The wide Speak head uses tabs only while their measured allocation
            # fits. Narrow sheets use the same shared folded strip species.
            if width <= 393:
                assert facts["folded"], facts
            shot = SHOTS / f"speak-head-{width}.png"
            page.screenshot(path=str(shot), full_page=False)
            assert shot.is_file() and shot.stat().st_size > 2_000
            browser.close()
    finally:
        server.stop()
