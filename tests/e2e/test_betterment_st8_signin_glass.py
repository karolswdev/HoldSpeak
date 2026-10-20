"""ST8 glass proof: a private fake ``gh`` signs in through the real pane.

The fake CLI writes only its normal ``hosts.yml`` marker after the owner
sends Enter in the embedded xterm.  The hub starts the native process in a
private tmux socket, observes the native exit marker, runs the existing Check
route, and the browser reads the durable ``Works`` row back at both widths.
"""
from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _ensure_build, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="ST8 glass needs Playwright")

TOKEN = "st8-glass"
SHOTS = evidence_dir("st8-signin")


def _fake_gh(bin_dir: Path) -> None:
    script = bin_dir / "gh"
    script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1 $2 $3\" = \"auth login --help\" ]; then\n"
        "  printf '%s\\n' '--web --hostname'; exit 0\n"
        "fi\n"
        "if [ \"$1 $2 $3\" = \"auth login --web\" ]; then\n"
        "  printf '%s\\n' 'FAKE GH: press Enter to finish browser sign-in'\n"
        "  IFS= read -r answer\n"
        "  mkdir -p \"${GH_CONFIG_DIR:-$HOME/.config/gh}\"\n"
        "  printf '%s\\n' 'github.com:' '  user: st8-owner' > \"${GH_CONFIG_DIR:-$HOME/.config/gh}/hosts.yml\"\n"
        "  printf '%s\\n' 'FAKE GH: signed in'\n"
        "  exit 0\n"
        "fi\n"
        "exit 1\n",
        encoding="utf-8",
    )
    script.chmod(0o755)


def _gh_runner() -> Any:
    import subprocess

    def run(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        cfg = Path(os.environ["GH_CONFIG_DIR"]) / "hosts.yml"
        if argv[1:3] == ["auth", "status"] and cfg.exists():
            return subprocess.CompletedProcess(
                argv, 0, stdout="Logged in to github.com account st8-owner (fake)\n", stderr=""
            )
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="not logged in")

    return run


def _navigate(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _api(page, "POST", "/api/connections/github/recheck", token=TOKEN)
    page.evaluate(
        """() => sessionStorage.setItem(
          "hs.desk.staged-surface-open",
          JSON.stringify({key: "configure-settings", scope: "integration:destinations"})
        )"""
    )
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    page.wait_for_selector('[data-testid="connections-github"]', timeout=15_000)


@pytest.mark.e2e
@pytest.mark.parametrize(("width", "height"), [(1440, 900), (393, 852)])
def test_private_native_signin_keys_marker_check_and_durable_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int,
) -> None:
    _ensure_build()
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _fake_gh(fake_bin)
    # macOS limits the expanded tmux socket path to 104 bytes.  The pytest
    # tmp path is intentionally long, so keep this private socket in a short
    # per-worker directory while the HOME and database remain isolated.
    tmux_tmp = Path(tempfile.mkdtemp(prefix="hs8-", dir="/tmp"))
    monkeypatch.setenv("PATH", f"{fake_bin}:{os.environ['PATH']}")
    monkeypatch.setenv("TMUX_TMPDIR", str(tmux_tmp))
    monkeypatch.setenv("HOLDSPEAK_OWN_AGENTS", "off")

    from tests.e2e.glass_infra import _boot

    server, base = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_gh_runner())
    errors: list[str] = []
    rechecks: list[str] = []
    commands: list[str] = []
    command_responses: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": height})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("response", lambda response: rechecks.append(response.url)
                     if response.request.method == "POST" and response.url.endswith("/api/connections/github/recheck") else None)
            page.on("request", lambda request: commands.append(request.post_data or "")
                     if request.method == "POST" and request.url.endswith("/api/delivery/terminal/commands") else None)
            page.on("response", lambda response: command_responses.append(
                f"{response.status}:{response.text()}"
            ) if response.request.method == "POST" and response.url.endswith("/api/delivery/terminal/commands") else None)
            _navigate(page, base)

            page.get_by_test_id("connections-github-show").click()
            terminal = page.locator('[data-testid^="connections-signin-terminal-"]')
            try:
                terminal.wait_for(timeout=15_000)
            except Exception:
                print("ST8 post-click body:", page.locator("body").inner_text())
                print("ST8 post-click github row:", page.get_by_test_id("connections-github").inner_text())
                raise
            # xterm owns keyboard focus in its hidden helper textarea;
            # focus that admitted input surface explicitly before Enter.
            helper = terminal.locator("textarea.xterm-helper-textarea")
            helper.focus()
            run_id = str(terminal.get_attribute("data-testid")).rsplit("-", 1)[-1]
            helper.press("Enter")
            deadline = time.monotonic() + 15
            signin_status: dict[str, Any] = {}
            while time.monotonic() < deadline:
                signin_status = _api(page, "GET", f"/api/connections/signin/{run_id}", token=TOKEN)
                if signin_status.get("status") != "running":
                    break
                time.sleep(0.25)
            print("ST8 command requests:", commands)
            print("ST8 command responses:", command_responses)
            assert signin_status.get("status") == "finished", {
                "status": signin_status, "commands": commands, "responses": command_responses,
            }
            assert signin_status.get("exit_code") == 0, signin_status
            page.locator('[data-testid="connections-github"] .surface-state-chip').get_by_text("Works").wait_for(timeout=15_000)
            assert any(url.endswith("/api/connections/github/recheck") for url in rechecks)

            body = _api(page, "GET", "/api/connections", token=TOKEN)
            github = next(tool for tool in body["tools"] if tool["provider_id"] == "github")
            assert github["state"] == "connected", github
            assert github["account"]["login"] == "st8-owner", github

            # A checked account's Sign in again uses the same native pane;
            # it must not fall back to a command the owner has to copy.
            page.get_by_test_id("connections-github-unfold").get_by_role(
                "button", name="Sign in again", exact=True,
            ).click()
            terminal.wait_for(timeout=15_000)
            helper = terminal.locator("textarea.xterm-helper-textarea")
            helper.focus()
            helper.press("Enter")
            terminal.wait_for(state="detached", timeout=15_000)
            page.locator('[data-testid="connections-github"] .surface-state-chip').get_by_text(
                "Works",
            ).wait_for(timeout=15_000)

            _settle(page)
            shot = SHOTS / f"st8-signin-{width}.png"
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(shot), full_page=True)
            assert shot.exists()
            browser.close()
    finally:
        server.stop()
        # The production terminal keeps final output available. This rig owns
        # a separate socket, so end only its sessions when the proof finishes.
        import subprocess

        for socket in tmux_tmp.glob("tmux-*/default"):
            subprocess.run(
                ["tmux", "-S", str(socket), "kill-server"],
                capture_output=True, check=False, timeout=5,
            )
    assert not errors, errors
