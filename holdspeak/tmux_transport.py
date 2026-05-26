"""tmux transport for agent reply delivery."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


class TmuxTransportError(RuntimeError):
    """Raised when a tmux reply cannot be delivered."""


@dataclass(frozen=True)
class TmuxDelivery:
    pane: str
    submitted: bool


def send_text_to_pane(
    *,
    pane: str,
    text: str,
    submit: bool = True,
    timeout_s: float = 2.0,
) -> TmuxDelivery:
    """Send literal text to a tmux pane, optionally followed by Enter."""

    target = str(pane or "").strip()
    message = str(text or "")
    if not target:
        raise TmuxTransportError("tmux pane target is required")
    if not message.strip():
        raise TmuxTransportError("tmux reply text is required")
    if shutil.which("tmux") is None:
        raise TmuxTransportError("tmux executable not found")

    _run_tmux(["tmux", "send-keys", "-t", target, "-l", message], timeout_s=timeout_s)
    if submit:
        _run_tmux(["tmux", "send-keys", "-t", target, "Enter"], timeout_s=timeout_s)
    return TmuxDelivery(pane=target, submitted=submit)


def _run_tmux(cmd: list[str], *, timeout_s: float) -> None:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TmuxTransportError(f"tmux command timed out: {cmd[1:]}") from exc
    except OSError as exc:
        raise TmuxTransportError(f"tmux command failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise TmuxTransportError(detail or f"tmux exited with {completed.returncode}")


__all__ = ["TmuxDelivery", "TmuxTransportError", "send_text_to_pane"]
