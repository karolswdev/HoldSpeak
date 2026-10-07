"""tmux transport for agent reply delivery."""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass

from .errors import HoldSpeakError


#: Text longer than this, or with a newline, is pasted as one bracketed paste
#: instead of typed (Conductor R1, ``send_text_to_pane``).
PASTE_ABOVE_CHARS = 200


class TmuxTransportError(HoldSpeakError):
    """Raised when a tmux reply cannot be delivered."""

    code: str = "TMUX_TRANSPORT_ERROR"


#: The pause between the text and its submit. Codex CLI 0.159 reads text
#: typed this fast as a paste and swallows a carriage return that follows it
#: at once (the text stays in its composer); after 0.1 s it submits
#: (observed, Conductor R3). Claude Code submits either way.
SUBMIT_PAUSE_SECONDS = 0.3


@dataclass(frozen=True)
class TmuxDelivery:
    pane: str
    submitted: bool


#: The control characters a typed text may carry: tab and newline only.
_ALLOWED_CONTROLS = frozenset({"\t", "\n"})


def plain_text(text: str) -> str:
    """The text as the pane gets it: CRLF (and a lone CR's pair) normalized
    to LF; refused when it carries any other C0 or C1 control or DEL
    (Conductor R1, Astra on #916: an embedded ESC[201~ ends a bracketed
    paste early, a Ctrl-C or a CR acts in the agent's TUI). Ordinary
    Unicode is kept."""
    normalized = text.replace("\r\n", "\n")
    for char in normalized:
        code = ord(char)
        if (code < 0x20 and char not in _ALLOWED_CONTROLS) or 0x7F <= code <= 0x9F:
            raise TmuxTransportError(
                f"the text carries a terminal control (U+{code:04X}); nothing was typed"
            )
    return normalized


def send_text_to_pane(
    *,
    pane: str,
    text: str,
    submit: bool = True,
    timeout_s: float = 2.0,
) -> TmuxDelivery:
    """Send literal text to a tmux pane, optionally followed by Enter."""

    target = str(pane or "").strip()
    message = plain_text(str(text or ""))
    if not target:
        raise TmuxTransportError("tmux pane target is required")
    if not message.strip():
        raise TmuxTransportError("tmux reply text is required")
    if shutil.which("tmux") is None:
        raise TmuxTransportError("tmux executable not found")

    if "\n" in message or len(message) > PASTE_ABOVE_CHARS:
        # One bracketed paste (Conductor R1). Typed fast with ``send-keys -l``,
        # a long or multi-line text reaches Claude Code 2.1.x as several
        # guessed paste chunks plus typed characters, and on a real launch
        # the chunks were lost: the agent got only the brief's last lines.
        # ``paste-buffer -p`` brackets the text when the agent asked for
        # bracketed paste (Claude Code and Codex do), so it arrives whole;
        # ``-r`` keeps each newline as it is; ``-d`` deletes the buffer.
        buffer = f"hs-{uuid.uuid4().hex[:12]}"
        _run_tmux(["tmux", "load-buffer", "-b", buffer, "-"], timeout_s=timeout_s, stdin=message)
        _run_tmux(
            ["tmux", "paste-buffer", "-p", "-r", "-d", "-b", buffer, "-t", target],
            timeout_s=timeout_s,
        )
    else:
        _run_tmux(["tmux", "send-keys", "-t", target, "-l", message], timeout_s=timeout_s)
    if submit:
        time.sleep(SUBMIT_PAUSE_SECONDS)
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

    # A literal run is typed text: no terminal control rides in it (a
    # control is a named key, from the allow-list). Read all first: a refused
    # run sends nothing, not the keys before it.
    for kind, value in keys:
        if kind == "literal":
            plain_text(value)
    for kind, value in keys:
        if kind == "literal":
            _run_tmux(["tmux", "send-keys", "-t", target, "-l", value], timeout_s=timeout_s)
        elif kind == "named":
            # No -l: tmux interprets the argument as a key name (C-c, Up, …).
            _run_tmux(["tmux", "send-keys", "-t", target, value], timeout_s=timeout_s)
        else:  # pragma: no cover - callers normalize; guard the transport anyway
            raise TmuxTransportError(f"unknown key kind: {kind!r}")
    return TmuxDelivery(pane=target, submitted=False)


def _run_tmux(cmd: list[str], *, timeout_s: float, stdin: str | None = None) -> None:
    try:
        completed = subprocess.run(
            cmd,
            input=stdin,
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
    "plain_text",
    "send_text_to_pane",
]
