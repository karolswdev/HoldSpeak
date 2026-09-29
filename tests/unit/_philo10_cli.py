"""PHILO-10-02: the shared rig of the CLI channel fences (a real hub on an isolated HOME).

The hub, its routes, its kernel and each channel's REAL ``plan`` run as they
ship; only the process edge (``channel_cli.CLI_RUNNER``) is canned: a
recording runner that answers ``gh`` and ``acli`` the way the grounding probes
recorded them. It reads the body from the ``--body-file`` / ``--from-json``
path while the command "runs" (the private file exists only then), so a fence
compares the bytes the CLI would read with the preview's digest. No real ``gh``
or ``acli`` ever runs here, and no account is touched.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub  # noqa: E402

SITE, EMAIL = "acme.atlassian.net", "owner@acme.example"
STATUS_OK = f"✓ Authenticated\n  Site: {SITE}\n  Email: {EMAIL}\n  Authentication Type: api_token\n"


class Call:
    def __init__(self, argv: list[str], body: Optional[bytes], mode: Optional[int], thread: str) -> None:
        self.argv, self.body, self.mode, self.thread = argv, body, mode, thread


class Canned:
    """The process edge: answers by argv; records argv, the body file's bytes and its mode."""

    def __init__(self, *, login: str = "octo-owner") -> None:
        self.login = login
        self.calls: list[Call] = []
        self.lock = threading.Lock()
        #: argv[:n] prefix -> a callable(argv) returning (code, stdout, stderr) or raising.
        self.answers: dict[tuple[str, ...], Callable[[list[str]], Any]] = {}
        self.on_create: Optional[Callable[[list[str]], None]] = None

    @staticmethod
    def _body(argv: list[str]) -> tuple[Optional[bytes], Optional[int]]:
        for flag in ("--body-file", "--from-json"):
            if flag in argv:
                path = argv[argv.index(flag) + 1]
                return Path(path).read_bytes(), stat.S_IMODE(os.stat(path).st_mode)
        return None, None

    def creates(self) -> list[Call]:
        return [c for c in self.calls if c.body is not None]

    def __call__(self, argv: Any, **_kwargs: Any) -> Any:
        argv = [str(a) for a in argv]
        body, mode = self._body(argv)
        with self.lock:
            self.calls.append(Call(argv, body, mode, threading.current_thread().name))
        for prefix, answer in self.answers.items():
            if tuple(argv[:len(prefix)]) == prefix:
                return _completed(argv, *answer(argv))
        if argv[:3] == ["gh", "api", "user"]:
            return _completed(argv, 0, json.dumps({"login": self.login, "id": 7}), "")
        if argv[:3] in (["gh", "issue", "comment"], ["gh", "pr", "comment"]):
            if self.on_create:
                self.on_create(argv)
            repo = argv[argv.index("--repo") + 1]
            path = "pull" if argv[1] == "pr" else "issues"
            return _completed(argv, 0, f"https://github.com/{repo}/{path}/{argv[3]}#issuecomment-99001\n", "")
        if argv[:4] == ["acli", "jira", "auth", "switch"] or argv[:4] == ["acli", "confluence", "auth", "switch"]:
            return _completed(argv, 0, "✓ Switched\n", "")
        if argv[:4] == ["acli", "jira", "auth", "status"] or argv[:4] == ["acli", "confluence", "auth", "status"]:
            return _completed(argv, 0, STATUS_OK, "")
        if argv[:5] == ["acli", "jira", "workitem", "comment", "create"]:
            if self.on_create:
                self.on_create(argv)
            return _completed(argv, 0, json.dumps({"id": "10042", "self": "https://acme.atlassian.net/rest/api/3/"
                                                  "issue/10001/comment/10042"}), "")
        if argv[:4] == ["acli", "confluence", "blog", "create"]:
            if self.on_create:
                self.on_create(argv)
            return _completed(argv, 0, json.dumps({"id": "5550001", "_links": {"webui": "/spaces/OPS/blog/5550001"}}), "")
        return _completed(argv, 1, "", f"canned: no answer for {argv[:4]}")


def _completed(argv: list[str], code: int, out: str, err: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(argv, code, out, err)


def install(monkeypatch: pytest.MonkeyPatch, canned: Optional[Canned] = None) -> Canned:
    from holdspeak.services import channel_cli

    canned = canned or Canned()
    monkeypatch.setattr(channel_cli, "CLI_RUNNER", canned)
    return canned


def save(hub: Hub, channel: str, name: str = "", **fields: Any) -> dict[str, Any]:
    defaults: dict[str, dict[str, Any]] = {
        "github": {"repo": "acme/payments", "kind": "issue", "number": 42},
        "jira": {"site": SITE, "email": EMAIL, "key": "PAY-7"},
        "confluence": {"site": SITE, "email": EMAIL, "space_id": "98304"},
    }
    body = {"name": name or f"{channel} scratch", "channel": channel, **defaults[channel], **fields}
    return hub.client.post("/api/channels/destinations", json=body).json()
