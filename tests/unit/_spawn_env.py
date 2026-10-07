"""Conductor R2: read the agent credential a faked tmux spawn would hand its
session. The token rides a one-shot 0600 file the session command sources,
never argv; with tmux faked, nothing has sourced (or deleted) it yet."""
from __future__ import annotations

import shlex
from pathlib import Path

from holdspeak.coder_factory import CREDENTIAL_ENV


def env_file_of(argv: list[str]) -> Path:
    """The credential file the spawn's session command names."""
    command = argv[argv.index("-s") + 2]
    words = shlex.split(command.split(";", 1)[0])
    assert words[0] == ".", command
    return Path(words[1])


def token_of(argv: list[str]) -> str:
    """The token in the spawn's credential file."""
    for line in env_file_of(argv).read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{CREDENTIAL_ENV}="):
            return shlex.split(line.split("=", 1)[1])[0]
    raise AssertionError("no credential in the spawn's env file")


def strip_env(command: str) -> str:
    """The session command without the credential prefix (what a fake tmux
    reads as the launch's own command)."""
    if command.startswith(". "):
        parts = command.split("; ", 2)
        if len(parts) == 3 and parts[1].startswith("rm -f "):
            return parts[2]
    return command
