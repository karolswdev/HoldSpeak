"""AG15: the owner-started Claude pane on the real Agents face.

The pane and fake producer are OS processes in this test's own tmux socket.
The hub discovers that pane through the product route, and the Answer press
uses the admitted process-input path; no screen-shaped fixture stands in for
either producer.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="AG15 own-agent glass needs Playwright")

TOKEN = "ag15-own-agents"
SHOTS = evidence_dir("ag15-own-agents")
FAKE = Path(__file__).resolve().parents[2] / "docs" / "internal" / "betterment" / "agents" / "rig" / "fake_claude.py"


def _tmux_env(home: Path, socket_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({"HOME": str(home), "TMUX_TMPDIR": str(socket_dir)})
    env.pop("TMUX", None)
    return env


def _start_fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, str], str]:
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    # macOS appends ``tmux-<uid>/default`` and has a short Unix-socket path
    # limit.  Keep this isolated socket under /tmp rather than pytest's long
    # worker path.
    socket_dir = Path(tempfile.mkdtemp(prefix="hsag15-", dir="/tmp"))
    run_dir = tmp_path / "fake-agent"
    run_dir.mkdir(parents=True, exist_ok=True)
    fake = run_dir / "claude"
    shutil.copy2(FAKE, fake)
    fake.chmod(0o755)
    env = _tmux_env(home, socket_dir)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("TMUX_TMPDIR", str(socket_dir))
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.setenv("HOLDSPEAK_OWN_AGENTS", "on")
    subprocess.run(
        ["tmux", "-f", "/dev/null", "new-session", "-d", "-s", "ag15", "-c", str(run_dir)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    time.sleep(0.5)
    subprocess.run(
        ["tmux", "-f", "/dev/null", "send-keys", "-t", "ag15:0", "-l", str(fake)],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["tmux", "-f", "/dev/null", "send-keys", "-t", "ag15:0", "Enter"],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    _wait_for_pane(env, "FAKE Claude Code", 30)
    subprocess.run(
        ["tmux", "-f", "/dev/null", "send-keys", "-t", "ag15:0", "-l", "isolated own-agent glass"],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["tmux", "-f", "/dev/null", "send-keys", "-t", "ag15:0", "Enter"],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    _wait_for_pane(env, "I found two places", 30)
    return env, str(home)


def _wait_for_pane(env: dict[str, str], text: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pane = subprocess.run(
            ["tmux", "-f", "/dev/null", "capture-pane", "-p", "-t", "ag15:0"],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if text in pane:
            return
        time.sleep(0.25)
    raise AssertionError(f"isolated fake Claude did not show {text!r}")


def _open_agents(page: Any) -> Any:
    conductor = page.locator(".conductor-window")
    if not conductor.count() or not conductor.is_visible():
        dock = page.locator(".desk-dock [data-app='conductor']")
        if dock.count() and dock.first.is_visible():
            dock.first.click()
        else:
            page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
            menu = page.locator(".desk-verbbar-menu")
            menu.wait_for()
            menu.locator("[role^=menuitem]").filter(
                has=page.locator(".desk-menu-label", has_text=re.compile(r"^Agents$")),
            ).click()
    conductor.wait_for(timeout=15_000)
    fold = conductor.locator("details.cw-own-agents")
    fold.wait_for(timeout=30_000)
    if fold.get_attribute("open") is None:
        fold.locator("summary").click()
    own = conductor.locator("[data-testid='conductor-own-agents']")
    own.wait_for(timeout=30_000)
    return own


@pytest.mark.timeout(180)
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_owner_started_agent_is_real_on_the_agents_face(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    env, home = _start_fake(tmp_path, monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    # The shared glass boot keeps owner-pane discovery off for every ordinary
    # rig. Opt in only after this test has created its private tmux server.
    monkeypatch.setenv("HOLDSPEAK_OWN_AGENTS", "on")
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=2 if width == 393 else 1,
                is_mobile=width == 393,
                has_touch=width == 393,
            )
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            own = _open_agents(page)
            row = own.locator("[data-testid='conductor-ask-row']")
            row.wait_for(timeout=30_000)
            assert "I found two places for the rollback flag" in (row.text_content() or "")
            assert row.get_by_role("button", name="Answer").count() >= 1
            assert row.get_by_role("button", name="Stop").count() == 0
            row.scroll_into_view_if_needed()
            page.screenshot(path=str(SHOTS / f"own-agent-asks-{width}.png"), full_page=False)

            row.get_by_role("textbox", name=re.compile("Answer")).fill("config")
            with page.expect_response(lambda response: "/api/coders/own-agents/answer" in response.url) as answer_response:
                row.get_by_role("button", name="Answer").last.click()
            response = answer_response.value
            assert response.status < 300, response.text()
            log = Path(home) / "fake-agent.log"
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if log.exists() and "ANSWER RECEIVED: 'config'" in log.read_text():
                    break
                time.sleep(0.25)
            assert log.exists() and "ANSWER RECEIVED: 'config'" in log.read_text()

            # The same process advances to a real approval prompt. Reload the
            # face so this read is a fresh producer/transport observation.
            _wait_for_pane(env, "Do you want to proceed?", 30)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            own = _open_agents(page)
            held = own.locator("[data-testid='conductor-ask-row']")
            held.wait_for(timeout=30_000)
            assert held.get_by_role("button", name="Allow").count() >= 1
            held.scroll_into_view_if_needed()
            page.screenshot(path=str(SHOTS / f"own-agent-approval-{width}.png"), full_page=False)
            with page.expect_response(lambda response: "/api/coders/own-agents/answer" in response.url) as allow_response:
                held.get_by_role("button", name="Allow").first.click()
            response = allow_response.value
            assert response.status < 300, response.text()
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if log.exists() and "PERMISSION KEY RECEIVED" in log.read_text():
                    break
                time.sleep(0.25)
            assert log.exists() and "PERMISSION KEY RECEIVED" in log.read_text()
            browser.close()
    finally:
        server.stop()
        subprocess.run(
            ["tmux", "-f", "/dev/null", "kill-server"],
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
