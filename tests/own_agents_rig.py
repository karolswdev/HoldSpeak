"""Private fake Claude and tmux rig; no owner process or provider."""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
import pytest
FAKE = Path(__file__).resolve().parents[1] / "docs/internal/betterment/agents/rig/fake_claude.py"

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


