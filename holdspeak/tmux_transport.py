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
        # A LITERAL carriage return, not the named `Enter` key: current Claude
        # Code TUIs (observed on 2.1.x) drop a lone named-Enter send-keys but
        # submit on the raw \r byte. Found live by the HSM-17-04 inject proof --
        # answers were "delivered" yet sat unsubmitted in the composer.
        _run_tmux(["tmux", "send-keys", "-t", target, "-l", "\r"], timeout_s=timeout_s)
    return TmuxDelivery(pane=target, submitted=submit)


def send_keys_to_pane(
    *,
    pane: str,
    keys: list[tuple[str, str]],
    timeout_s: float = 2.0,
) -> TmuxDelivery:
    """Send a sequence of keys to a tmux pane — the control half of the
    transport, beside the literal ``send_text_to_pane``.

    Each item in ``keys`` is ``("named", "<tmux-key>")`` (a named key such as
    ``C-c``, ``Escape``, ``Up`` — sent as a ``send-keys`` argument) or
    ``("literal", "<text>")`` (a literal run — sent with ``-l``). Named and
    literal are NEVER mixed in a single ``send-keys`` call: each item is its
    own ordered call, so ``C-c`` interrupts and a literal types, in order.
    Callers must pre-validate named keys against the allow-list
    (``coder_steering`` does); this transport does not interpret the strings.
    """

    target = str(pane or "").strip()
    if not target:
        raise TmuxTransportError("tmux pane target is required")
    if not keys:
        raise TmuxTransportError("tmux key sequence is required")
    if shutil.which("tmux") is None:
        raise TmuxTransportError("tmux executable not found")

    for kind, value in keys:
        if kind == "literal":
            _run_tmux(["tmux", "send-keys", "-t", target, "-l", value], timeout_s=timeout_s)
        elif kind == "named":
            # No -l: tmux interprets the argument as a key name (C-c, Up, …).
            _run_tmux(["tmux", "send-keys", "-t", target, value], timeout_s=timeout_s)
        else:  # pragma: no cover - callers normalize; guard the transport anyway
            raise TmuxTransportError(f"unknown key kind: {kind!r}")
    return TmuxDelivery(pane=target, submitted=False)


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


__all__ = [
    "TmuxDelivery",
    "TmuxTransportError",
    "send_keys_to_pane",
    "send_text_to_pane",
]
