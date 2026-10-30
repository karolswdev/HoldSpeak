"""Independent terminal views against real shells on a private tmux socket.

The browser uses the production discovery, grant, command, stream and Desk
window routes. No agent CLI, provider, microphone or owner tmux is involved.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api")
pytestmark = [pytest.mark.e2e, pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is required")]
TOKEN = "terminal-workspace-glass"
SHOTS = evidence_dir("terminal-workspace")


def _tmux(*args: str) -> str:
    result = subprocess.run(["tmux", *args], check=True, capture_output=True, text=True, timeout=8)
    return result.stdout.strip()


def _capture(pane: str) -> str:
    return _tmux("capture-pane", "-p", "-t", pane, "-S", "-100")


def _eventually(predicate: Any, *, seconds: float = 12) -> Any:
    until = time.monotonic() + seconds
    last = None
    while time.monotonic() < until:
        last = predicate()
        if last:
            return last
        time.sleep(0.1)
    raise AssertionError(f"Terminal observation did not arrive: {last!r}")


def _open(page: Any, descriptor: dict[str, Any]) -> Any:
    page.get_by_test_id(f"terminal-open-{descriptor['id']}").click()
    frame = page.locator(f'[id="terminal:{descriptor["id"]}"]')
    frame.wait_for(state="visible")
    return frame


def _inventory(page: Any, base: str) -> Any:
    # Raising is a presentation act through the existing shared OS contract.
    _api(page, "POST", "/api/desk/windows/surface-terminals/open", token=TOKEN)
    frame = page.locator('[id="surface-terminals"]')
    frame.wait_for(state="visible")
    return frame


def _type(frame: Any, words: str) -> None:
    frame.get_by_test_id("terminal-enable-typing").click()
    # The press requests a grant. Keyboard input is permitted only after the
    # rendered acknowledgement, which can take longer under the broad rig.
    frame.get_by_role("button", name="View only", exact=True).wait_for(state="visible")
    helper = frame.locator("textarea.xterm-helper-textarea")
    helper.focus()
    helper.type(words, delay=45)
    helper.press("Enter")


@pytest.mark.parametrize(("width", "height"), [(1440, 900), (393, 852)])
def test_independent_input_persistent_views_and_close_without_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    _ensure_build()
    # HOME alone does not isolate tmux. Its Unix-socket path must be short
    # on macOS and is owned exclusively by this test, including teardown.
    sockets = Path(tempfile.mkdtemp(prefix="hsterm-", dir="/tmp"))
    monkeypatch.setenv("TMUX_TMPDIR", str(sockets))
    monkeypatch.delenv("TMUX", raising=False)
    server = None
    try:
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        name_a, name_b = "terminal-proof-a", "terminal-proof-b"
        _tmux("-f", "/dev/null", "new-session", "-d", "-s", name_a, "-x", "90", "-y", "28", "bash --noprofile --norc")
        _tmux("new-session", "-d", "-s", name_b, "-x", "90", "-y", "28", "bash --noprofile --norc")
        pane_a = _tmux("list-panes", "-t", name_a, "-F", "#{pane_id}")
        pane_b = _tmux("list-panes", "-t", name_b, "-F", "#{pane_id}")
        assert pane_a != pane_b
        socket_path = _tmux("display-message", "-p", "-t", name_a, "#{socket_path}")
        assert Path(socket_path).resolve().is_relative_to(sockets.resolve())

        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": width, "height": height}, has_touch=width == 393)
            page = context.new_page()
            page.emulate_media(reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            response = page.goto(f"{base}/terminals?token={TOKEN}", wait_until="load")
            assert response is not None and response.status == 200, "Terminals deep link must serve the React shell"
            inventory = page.locator('[id="surface-terminals"]')
            try:
                inventory.wait_for(state="visible", timeout=15_000)
            except Exception:
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / f"failed-inventory-{width}.png"))
                print("Terminals startup:", page.locator("body").inner_text()[:5000], "errors:", errors)
                raise
            sessions = _api(page, "GET", "/api/delivery/terminal/sessions", token=TOKEN)
            assert sessions["status"] == "ok", sessions
            a = next(row for row in sessions["sessions"] if row["session"] == name_a)
            b = next(row for row in sessions["sessions"] if row["session"] == name_b)
            assert a["id"] != b["id"] and a["target"]["target_id"] != b["target"]["target_id"]
            working = tmp_path / "shell-folder"
            working.mkdir()
            inventory.get_by_test_id("terminal-new").click()
            inventory.get_by_role("textbox", name="Shell name", exact=True).fill("terminal-proof-created")
            inventory.get_by_role("textbox", name="Folder (optional)", exact=True).fill(str(working))
            inventory.get_by_role("button", name="Create shell", exact=True).click()
            created = _eventually(lambda: next((row for row in _api(
                page, "GET", "/api/delivery/terminal/sessions", token=TOKEN,
            )["sessions"] if row["session"] == "terminal-proof-created"), None))
            actual_folder = _tmux("display-message", "-p", "-t", "terminal-proof-created", "#{pane_current_path}")
            assert Path(actual_folder).resolve() == working.resolve()
            made_view = page.locator(f'[id="terminal:{created["id"]}"]')
            made_view.wait_for(state="visible")
            made_view.get_by_role("button", name=re.compile(r"^Back from " if width == 393 else r"^Close ")).click()
            made_view.wait_for(state="detached")
            _tmux("has-session", "-t", "terminal-proof-created")
            _inventory(page, base)
            first = _open(page, a)
            marker_a = f"observed-A-{width}"
            _type(first, f"printf '{marker_a}\\n'")
            _eventually(lambda: marker_a in [line.strip() for line in _capture(pane_a).splitlines()])
            # An Escape belongs to the TUI. It must not dismiss the frame.
            first.locator("textarea.xterm-helper-textarea").press("Escape")
            assert first.is_visible()
            if width == 1440:
                # Reflow follows this window's width, even on a wide Desk.
                # The physical pane stays wide/tall and must scroll within
                # the smaller well rather than hiding below clipped chrome.
                frame_box = first.bounding_box()
                grip = first.locator(".desk-window-grip").bounding_box()
                assert frame_box and grip
                start_x, start_y = grip["x"] + grip["width"] / 2, grip["y"] + grip["height"] / 2
                page.mouse.move(start_x, start_y)
                page.mouse.down()
                page.mouse.move(start_x + 480 - frame_box["width"], start_y + 360 - frame_box["height"], steps=8)
                page.mouse.up()
                _settle(page)
                small = first.bounding_box()
                assert small and small["width"] <= 520 and small["height"] <= 400, small
                well = first.locator(".terminal-well")
                screen = first.locator(".terminal-well-screen")
                well_box, screen_box = well.bounding_box(), screen.bounding_box()
                assert well_box and screen_box and screen_box["y"] + screen_box["height"] <= well_box["y"] + well_box["height"] + 1
                assert screen.evaluate("element => element.scrollHeight > element.clientHeight")
                screen.evaluate("element => element.scrollTop = element.scrollHeight")
                assert screen.evaluate("element => element.scrollTop > 0")
                screen.evaluate("element => element.scrollTop = 0")
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / "workspace-narrow-desktop.png"))

            _inventory(page, base)
            second = _open(page, b)
            marker_b = f"observed-B-{width}"
            _type(second, f"printf '{marker_b}\\n'")
            try:
                _eventually(lambda: marker_b in [line.strip() for line in _capture(pane_b).splitlines()])
            except AssertionError as error:
                SHOTS.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(SHOTS / f"failed-input-{width}.png"))
                raise AssertionError(f"Independent input not observed. A={_capture(pane_a)!r}; B={_capture(pane_b)!r}; view={second.inner_text()!r}") from error
            assert marker_b not in _capture(pane_a)
            assert marker_a not in _capture(pane_b)
            assert page.locator('[id^="terminal:"]').count() == 2
            if width == 1440:
                _inventory(page, base)
                inventory.get_by_test_id("terminal-tile").click()
                _eventually(lambda: len(_api(page, "GET", "/api/desk/windows", token=TOKEN)["windows"]) >= 3)
            before = _api(page, "GET", "/api/desk/windows", token=TOKEN)
            terminal_rows = {row["id"]: row for row in before["windows"] if row["id"].startswith("terminal:")}
            assert len(terminal_rows) == 2
            if width == 1440:
                assert terminal_rows[f"terminal:{a['id']}"]["x"] != terminal_rows[f"terminal:{b['id']}"]["x"]
            # The inventory is not the owner of a terminal subscription. A
            # reload with only terminal frames must discover and restore them.
            _api(page, "POST", "/api/desk/windows/surface-terminals/close", token=TOKEN)
            page.reload(wait_until="load")
            page.locator(f'[id="terminal:{b["id"]}"] .xterm').wait_for(state="visible")
            restored = _api(page, "GET", "/api/desk/windows", token=TOKEN)
            after_rows = {row["id"]: row for row in restored["windows"] if row["id"].startswith("terminal:")}
            for ident, row in terminal_rows.items():
                assert ident in after_rows
                assert [after_rows[ident][k] for k in ("x", "y", "w", "h")] == [row[k] for k in ("x", "y", "w", "h")]
            # Restore/focus A, close the window through its own frame and prove
            # the actual producer remains alive. Phone Back returns inventory.
            _inventory(page, base)
            first = _open(page, a)
            close = first.get_by_role("button", name=re.compile(r"^Back from " if width == 393 else r"^Close "))
            close.click()
            first.wait_for(state="detached")
            _tmux("has-session", "-t", name_a)
            assert marker_a in _capture(pane_a)
            _inventory(page, base)
            reopened = _open(page, a)
            reopened.locator(".xterm").wait_for(state="visible")
            # The default face stays quiet, and its shared menus/search remain
            # reachable by keyboard without dismissing the terminal itself.
            keys = reopened.get_by_role("button", name="Keys", exact=True)
            keys.click()
            page.get_by_role("menuitem", name="Ctrl-C", exact=True).wait_for(state="visible")
            page.keyboard.press("Escape")
            assert reopened.is_visible()
            reopened.get_by_test_id("terminal-find").click()
            finder = reopened.get_by_role("textbox", name="Find in scrollback", exact=True)
            finder.fill(marker_a)
            finder.press("Enter")
            reopened.get_by_test_id("terminal-find").click()
            finder.wait_for(state="detached")
            if width == 393:
                for button in (keys, reopened.get_by_test_id("terminal-enable-typing"), reopened.get_by_test_id("terminal-find")):
                    box = button.bounding_box()
                    assert box and box["width"] >= 44 and box["height"] >= 44, box
                screen = reopened.locator(".terminal-well-screen")
                assert screen.evaluate("element => element.scrollWidth > element.clientWidth")
                screen.evaluate("element => element.scrollLeft = 100")
                assert screen.evaluate("element => element.scrollLeft > 0")
                screen.evaluate("element => element.scrollLeft = 0")
            if width == 1440:
                inventory = _inventory(page, base)
                inventory.get_by_test_id("terminal-tile").click()
            _settle(page)
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"workspace-{width}.png"))
            layout = page.evaluate("""() => {
                const rect = (element) => {
                    const r = element.getBoundingClientRect();
                    return {x:r.x, y:r.y, width:r.width, height:r.height,
                        right:r.right, bottom:r.bottom};
                };
                const tokens = getComputedStyle(document.documentElement);
                const luminance = (token) => {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = tokens.getPropertyValue(token).trim();
                    ctx.fillRect(0, 0, 1, 1);
                    const rgb = [...ctx.getImageData(0, 0, 1, 1).data].slice(0,3)
                        .map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
                    return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
                };
                const foreground = luminance('--text-on-accent');
                const background = luminance('--desk-terminal-screen');
                return {
                    terminal_text_contrast: (Math.max(foreground, background) + .05)
                        / (Math.min(foreground, background) + .05),
                    dock: rect(document.querySelector('.desk-dock')),
                    terminals: [...document.querySelectorAll('[id^="terminal:"]')]
                        .filter(element => element.getBoundingClientRect().width > 0)
                        .map(element => ({id:element.id, frame:rect(element),
                            composer:rect(element.querySelector('[data-testid="terminal-composer"]')),
                            status:rect(element.querySelector('[data-testid="terminal-status"]'))})),
                };
            }""")
            (SHOTS / f"observation-{width}.json").write_text(json.dumps({
                "viewport": width, "source": "production browser + isolated hub + private real tmux",
                "db": str(tmp_path / "holdspeak.db"), "socket": socket_path,
                "targets": [a["id"], b["id"]], "observed": [marker_a, marker_b],
                "close_kept_session": True, "restored_geometry": True, "page_errors": errors,
                "layout": layout,
            }, indent=2))
            assert not errors, errors
            assert layout["terminal_text_contrast"] >= 4.5, layout
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert layout["terminals"], layout
            for terminal in layout["terminals"]:
                frame, composer, status = (terminal[key] for key in ("frame", "composer", "status"))
                assert -1 <= frame["x"] and frame["right"] <= width + 1, terminal
                assert 0 <= frame["y"] and frame["bottom"] <= height + 1, terminal
                assert frame["y"] <= composer["y"] < composer["bottom"] <= frame["bottom"] + 1, terminal
                assert composer["bottom"] <= status["bottom"] <= layout["dock"]["y"] + 1, terminal
            browser.close()
    finally:
        if server is not None:
            server.stop()
        for socket in sockets.glob("tmux-*/default"):
            subprocess.run(["tmux", "-S", str(socket), "kill-server"], capture_output=True, timeout=5, check=False)
        shutil.rmtree(sockets, ignore_errors=True)
