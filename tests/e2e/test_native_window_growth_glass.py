"""A saved content-sized frame stays reachable when its CSS minimum grows.

The marker exercises Thought's production growth rule. It is synthetic DOM
content, not microphone, transcript, or provider evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

from tests._evidence import evidence_dir
from .chair_windows import open_chair_window
from .test_native_thought_voice_glass import (
    HEIGHT, THOUGHT, TOKEN, _isolated_boot, _new_note, _start, _target_check,
)
from .glass_infra import _ensure_build

pytest.importorskip("playwright.sync_api", reason="window growth glass needs Playwright")
pytestmark = [pytest.mark.e2e]
SHOTS = evidence_dir("native-window-growth")


def _frame_state(frame: Any) -> dict[str, Any]:
    return frame.evaluate("""el => {
      const r = el.getBoundingClientRect();
      const root = getComputedStyle(document.documentElement);
      const bottom = Math.max(
        parseFloat(root.getPropertyValue('--desk-work-bottom')) || 0,
        parseFloat(root.getPropertyValue('--desk-dock-h')) || 0);
      const saved = JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || '{}');
      return {id: el.id, top: r.top, bottom: r.bottom, height: r.height,
        bandBottom: innerHeight - bottom, inlineHeight: el.style.height,
        savedRect: saved.panel?.rects?.[el.id] ?? null,
        zoomed: saved.panel?.max?.includes(el.id) ?? false};
    }""")


def _drag(page: Any, handle: Any, dy: float, during: Callable[[], None] | None = None) -> None:
    box = handle.bounding_box()
    assert box, "window gesture handle is painted"
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, y + dy, steps=12)
    if during:
        during()
    page.mouse.up()


def _owner_sticky(page: Any, frame: Any, height: int) -> None:
    """The owner's small arranged note. A note opens at 760 x 560 (owner
    2026-10-27, pullouts/size.ts); these cases start from a sticky he made
    smaller with the grip."""
    # The open flies out of the object: measure once its motion ends.
    page.wait_for_function("id => !document.getElementById(id).getAnimations().some((a) => a.playState === 'running')",
                           arg=frame.get_attribute("id"))
    now = frame.evaluate("el => el.getBoundingClientRect().height")
    _drag(page, frame.locator(".desk-window-grip"), height - now)
    page.wait_for_function("([id, h]) => Math.abs(document.getElementById(id).getBoundingClientRect().height - h) <= 2",
                           arg=[frame.get_attribute("id"), height])


def _grow(frame: Any) -> None:
    frame.evaluate("""el => {
      const marker = document.createElement('div');
      marker.className = 'thought-voice-recovery';
      marker.dataset.syntheticGrowth = 'true';
      marker.textContent = 'Synthetic content growth';
      el.querySelector('.thought-note-window').appendChild(marker);
    }""")


def _ungrow(frame: Any) -> None:
    frame.evaluate("el => el.querySelector('[data-synthetic-growth]')?.remove()")


@pytest.mark.parametrize("owner_height", [360, 500])
def test_arranged_frame_lifts_on_growth_without_saving_new_height(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, owner_height: int,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            _start(page, base)
            _new_note(page, 1440)
            frame = page.locator(THOUGHT).first
            frame.locator(".thought-note-body .cm-content").wait_for()
            frame_id = frame.get_attribute("id")
            assert frame_id and frame_id.startswith("pullout:note:")
            note_id = frame_id.removeprefix("pullout:note:")

            _owner_sticky(page, frame, owner_height)
            _drag(page, frame.locator(".desk-pullout-head"), 330 if owner_height == 360 else 220)
            page.wait_for_function("id => !!JSON.parse(localStorage.getItem('hs.desk.workspace.v1') || '{}').panel?.rects?.[id]", arg=frame_id)
            before = _frame_state(frame)
            assert before["savedRect"] and abs(before["savedRect"]["h"] - owner_height) <= 2, before
            assert before["top"] > 200 and before["bottom"] <= before["bandBottom"] + 1, before

            _grow(frame)
            page.wait_for_function("""id => {
              const el = document.getElementById(id);
              const r = el?.getBoundingClientRect();
              const root = getComputedStyle(document.documentElement);
              const bottom = Math.max(parseFloat(root.getPropertyValue('--desk-work-bottom')) || 0,
                parseFloat(root.getPropertyValue('--desk-dock-h')) || 0);
              return r && r.height >= 638 && r.bottom <= innerHeight - bottom + 1;
            }""", arg=frame_id)
            grown = _frame_state(frame)
            assert grown["top"] < before["top"] - 10, (before, grown)
            assert grown["savedRect"]["h"] == before["savedRect"]["h"], (before, grown)
            assert grown["savedRect"]["w"] == before["savedRect"]["w"]
            assert grown["savedRect"]["x"] == before["savedRect"]["x"]
            assert grown["inlineHeight"] == before["inlineHeight"]
            page.screenshot(path=str(SHOTS / f"arranged-growth-{owner_height}-1440.png"))

            if owner_height == 500:
                frame.locator(".desk-gadget-zoom").click()
                page.wait_for_function("id => JSON.parse(localStorage.getItem('hs.desk.workspace.v1')).panel.max.includes(id)", arg=frame_id)
                frame.locator(".desk-gadget-zoom").click()
                page.wait_for_function("id => !JSON.parse(localStorage.getItem('hs.desk.workspace.v1')).panel.max.includes(id)", arg=frame_id)
                restored = _frame_state(frame)
                assert restored["bottom"] <= restored["bandBottom"] + 1, restored
                assert restored["savedRect"]["h"] == owner_height, restored

            _ungrow(frame)
            page.wait_for_function("id => Math.abs(document.getElementById(id).getBoundingClientRect().height - JSON.parse(localStorage.getItem('hs.desk.workspace.v1')).panel.rects[id].h) <= 2", arg=frame_id)
            frame.locator(".desk-gadget-close").first.click()
            frame.wait_for(state="detached")
            page.goto(f"{base}/?token={TOKEN}&open=note:{note_id}", wait_until="load")
            reopened = page.locator(THOUGHT).first
            reopened.locator(".thought-note-body .cm-content").wait_for()
            compact = _frame_state(reopened)
            assert abs(compact["height"] - owner_height) <= 2, compact
            assert compact["savedRect"]["h"] == owner_height, compact
            (SHOTS / f"arranged-growth-{owner_height}-1440.json").write_text(
                json.dumps({"before": before, "grown": grown, "reopened": compact}, indent=2) + "\n"
            )
            browser.close()
    finally:
        server.stop()


def test_unarranged_frame_remains_auto_height(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            _start(page, base)
            frame = open_chair_window(page, "Needs you")
            frame.wait_for(state="visible")
            before = _frame_state(frame)
            assert before["savedRect"] is None and before["inlineHeight"] == "auto", before
            frame.locator(".desk-gadget-zoom").click()
            page.wait_for_function("id => JSON.parse(localStorage.getItem('hs.desk.workspace.v1')).panel.max.includes(id)", arg=before["id"])
            frame.locator(".desk-gadget-zoom").click()
            page.wait_for_function("id => !JSON.parse(localStorage.getItem('hs.desk.workspace.v1')).panel.max.includes(id)", arg=before["id"])
            restored = _frame_state(frame)
            assert restored["savedRect"] is None and restored["inlineHeight"] == "auto", restored
            assert abs(restored["height"] - before["height"]) <= 2, (before, restored)
            browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("gesture", ["head", "grip"])
def test_growth_waits_for_owner_gesture_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gesture: str,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            _start(page, base)
            _new_note(page, 1440)
            frame = page.locator(THOUGHT).first
            frame.locator(".thought-note-body .cm-content").wait_for()
            _owner_sticky(page, frame, 360)
            _drag(page, frame.locator(".desk-pullout-head"), 330)
            before = _frame_state(frame)
            assert before["savedRect"] and before["top"] > 300, before
            held: dict[str, Any] = {}

            def grow_while_held() -> None:
                _grow(frame)
                page.wait_for_function(
                    "id => document.getElementById(id)?.getBoundingClientRect().height >= 638",
                    arg=before["id"],
                )
                held.update(_frame_state(frame))
                assert held["bottom"] > held["bandBottom"] + 100, held
                assert held["top"] > 300, held

            handle = frame.locator(".desk-pullout-head" if gesture == "head" else ".desk-window-grip")
            _drag(page, handle, 10, during=grow_while_held)
            page.wait_for_function("""id => {
              const el = document.getElementById(id);
              const r = el?.getBoundingClientRect();
              const root = getComputedStyle(document.documentElement);
              const bottom = Math.max(parseFloat(root.getPropertyValue('--desk-work-bottom')) || 0,
                parseFloat(root.getPropertyValue('--desk-dock-h')) || 0);
              return r && r.bottom <= innerHeight - bottom + 1;
            }""", arg=before["id"])
            after = _frame_state(frame)
            assert after["top"] < held["top"] - 10, (held, after)
            assert after["savedRect"]["h"] < 640, after
            browser.close()
    finally:
        server.stop()


@pytest.mark.parametrize("command", ["Meta+Enter", "Meta+Shift+E"])
def test_growth_during_presentation_lifts_after_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="no-preference")
            page.set_default_timeout(20_000)
            _start(page, base)
            _new_note(page, 1440)
            frame = page.locator(THOUGHT).first
            frame.locator(".thought-note-body .cm-content").wait_for()
            if command == "Meta+Enter":
                open_chair_window(page, "Needs you")
            _drag(page, frame.locator(".desk-pullout-head"), 330)
            before = _frame_state(frame)
            assert before["savedRect"] and before["bottom"] <= before["bandBottom"] + 1, before
            frame.locator(".desk-pullout-title").first.click()
            page.keyboard.press(command)
            page.wait_for_function("id => !!document.getElementById(id)?.dataset.plate", arg=before["id"])
            _grow(frame)
            page.keyboard.press("Escape")
            page.wait_for_function("""id => {
              const el = document.getElementById(id);
              const r = el?.getBoundingClientRect();
              const root = getComputedStyle(document.documentElement);
              const bottom = Math.max(parseFloat(root.getPropertyValue('--desk-work-bottom')) || 0,
                parseFloat(root.getPropertyValue('--desk-dock-h')) || 0);
              return el && !el.dataset.plate && r.height >= 638 && r.bottom <= innerHeight - bottom + 1;
            }""", arg=before["id"])
            after = _frame_state(frame)
            assert after["savedRect"]["h"] == before["savedRect"]["h"], (before, after)
            assert after["top"] < before["top"] - 10, (before, after)
            browser.close()
    finally:
        server.stop()


def test_saved_frame_already_oversize_on_reopen_lifts_at_mount(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": HEIGHT[1440]}, reduced_motion="no-preference")
            page.set_default_timeout(20_000)
            _start(page, base)
            _new_note(page, 1440)
            frame = page.locator(THOUGHT).first
            frame.locator(".thought-note-body .cm-content").wait_for()
            _owner_sticky(page, frame, 360)
            _drag(page, frame.locator(".desk-pullout-head"), 330)
            before = _frame_state(frame)
            assert before["savedRect"] and before["top"] > 300, before
            note_id = before["id"].removeprefix("pullout:note:")
            frame.locator(".desk-gadget-close").first.click()
            frame.wait_for(state="detached")
            # Synthetic CSS minimum is present before the product scripts
            # mount the reopened saved frame; no expected rect is injected.
            page.add_init_script("""(() => {
              const apply = () => {
                const style = document.createElement('style');
                style.textContent = '.desk-next .desk-pullout.thought-workspace-window { min-height: 640px !important; }';
                (document.head || document.documentElement).appendChild(style);
              };
              if (document.documentElement) apply();
              else document.addEventListener('DOMContentLoaded', apply, {once: true});
            })()""")
            page.goto(f"{base}/?token={TOKEN}&open=note:{note_id}", wait_until="load")
            reopened = page.locator(THOUGHT).first
            reopened.locator(".thought-note-body .cm-content").wait_for()
            page.wait_for_function("""id => {
              const el = document.getElementById(id);
              const r = el?.getBoundingClientRect();
              const root = getComputedStyle(document.documentElement);
              const bottom = Math.max(parseFloat(root.getPropertyValue('--desk-work-bottom')) || 0,
                parseFloat(root.getPropertyValue('--desk-dock-h')) || 0);
              return r && r.height >= 638 && r.bottom <= innerHeight - bottom + 1;
            }""", arg=before["id"])
            after = _frame_state(reopened)
            assert after["top"] < before["top"] - 10, (before, after)
            assert after["savedRect"]["h"] == before["savedRect"]["h"] == 360, (before, after)
            browser.close()
    finally:
        server.stop()


def test_phone_sheet_growth_keeps_sheet_and_controls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _isolated_boot(tmp_path, monkeypatch)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": HEIGHT[393]},
                                    has_touch=True, is_mobile=True, reduced_motion="reduce")
            page.set_default_timeout(20_000)
            _start(page, base)
            _new_note(page, 393)
            frame = page.locator(THOUGHT).first
            frame.locator(".thought-note-body .cm-content").wait_for()
            before = _frame_state(frame)
            _grow(frame)
            page.wait_for_function("id => !!document.getElementById(id)?.querySelector('[data-synthetic-growth]')", arg=before["id"])
            grown = _frame_state(frame)
            assert abs(grown["top"] - before["top"]) <= 1, (before, grown)
            assert grown["savedRect"] == before["savedRect"], (before, grown)
            _target_check(page, THOUGHT)
            page.screenshot(path=str(SHOTS / "sheet-growth-393.png"))
            browser.close()
    finally:
        server.stop()
