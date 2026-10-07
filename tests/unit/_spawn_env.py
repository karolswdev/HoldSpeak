"""Conductor R2: what a faked tmux spawn hands its session.

The spawn's command is ``/bin/sh -c BOOTSTRAP holdspeak-agent <file> <cmd>``:
the token rides a one-shot 0600 file the bootstrap reads and deletes, never
argv. A fake tmux stands in for that bootstrap with ``consume`` (it reads the
file and deletes it, as the real one does); ``token_of`` then answers what
the session received.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.coder_factory import BOOTSTRAP

_RECEIVED: dict[str, str] = {}


def _base(argv: list[str]) -> int:
    return argv.index("-s") + 2


def is_bootstrap(argv: list[str]) -> bool:
    i = _base(argv)
    return argv[i:i + 3] == ["/bin/sh", "-c", BOOTSTRAP]


def env_file_of(argv: list[str]) -> Path:
    """The credential file the spawn's bootstrap reads."""
    assert is_bootstrap(argv), argv
    return Path(argv[_base(argv) + 4])


def command_of(argv: list[str]) -> str:
    """The launch's own command ("" = a login shell)."""
    i = _base(argv)
    if is_bootstrap(argv):
        return argv[i + 5]
    return argv[i] if len(argv) > i else ""


def consume(argv: list[str]) -> None:
    """What the session's bootstrap does: read the token, delete the file."""
    if not is_bootstrap(argv):
        return
    path = env_file_of(argv)
    _RECEIVED[str(path)] = path.read_text(encoding="utf-8").strip()
    path.unlink()


def token_of(argv: list[str]) -> str:
    """The token the spawn handed its session."""
    path = env_file_of(argv)
    if str(path) in _RECEIVED:
        return _RECEIVED[str(path)]
    return path.read_text(encoding="utf-8").strip()


def strip_env(command: str) -> str:  # kept for older callers: commands carry no prefix now
    return command
