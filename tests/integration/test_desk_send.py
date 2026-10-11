"""Send, through the real hub (the test diet, 2026-10-11).

The hub boots over an isolated database and HOME with the real channel plans
and kernel; only the process edge (gh / acli) is canned
(``tests/unit/_philo10_cli.py``). Each test asserts the fact the browser test
it replaces asserted on the hub side.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from _philo10_cli import install, save  # noqa: E402
from _philo10_send import Hub, _boot, room, send, send_body, sends  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_a_held_acli_lock_is_refused_on_the_first_answer(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_a_held_acli_lock_is_refused_on_the_first_answer

    Another process holds the acli lock file: the owner's first press is
    answered 409 lock_timeout with a refused receipt, and nothing is created
    or recorded as a send.
    """
    from holdspeak.services import jira_provider

    canned = install(monkeypatch)
    monkeypatch.setattr(jira_provider._ACLI_LOCK, "_timeout", 0.2)
    _pid, update = room(hub)
    saved = save(hub, "jira", name="Jira PAY-121", key="PAY-121")
    dest = saved["destination"]["id"]
    body = send_body(hub, "inline", update, dest, "held-lock-1")

    lock = jira_provider._acli_lockfile_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    code = ('import fcntl,sys; f=open(sys.argv[1],"a"); fcntl.flock(f,fcntl.LOCK_EX); '
            'print("locked",flush=True); sys.stdin.read()')
    holder = subprocess.Popen([sys.executable, "-c", code, str(lock)], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout is not None and holder.stdout.readline().strip() == "locked"
        creates = len(canned.creates())
        answer = send(hub, body)
    finally:
        assert holder.stdin is not None
        holder.stdin.close()
        holder.wait(timeout=5)

    assert answer.status_code == 409, answer.text
    refused = answer.json()
    assert refused["code"] == "lock_timeout", refused
    assert (refused["receipt"]["state"], refused["receipt"]["outcome"]) == ("refused", "lock_timeout"), refused
    assert len(canned.creates()) == creates
    assert sends(hub) == []
