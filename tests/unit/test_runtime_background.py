"""The hub's background work lives in one runtime module (2026-11-08).

``holdspeak/runtime/background.py`` starts what the lifespan started and stops
it again; ``web_server`` calls ``start_background`` and ``Stopper.stop``. The
move is one way: background never imports ``web_server``.

The keystore warm and two conductors (workbench, scheduled recording) start a
thread with no switch (the calendar conductor refreshes once and starts none);
every other thread has a switch or runs only in the database owner. With every
switch off, only those three threads start; one switch on adds exactly its
thread.
"""
from __future__ import annotations

import ast
import asyncio
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).parents[2]

UNSWITCHED = {
    "keystore-warm",
    "workbench-conductor",
    "scheduled-recording-conductor",
}

SWITCHES_OFF = {
    "HOLDSPEAK_AGENT_STATE": "off",
    "HOLDSPEAK_ACTIVE_TARGET": "off",
    "HOLDSPEAK_DESKTOP_NOTIFY": "0",
    "HOLDSPEAK_MACOS_CALENDAR": "0",
    "HOLDSPEAK_CLI_ENGINES": "off",
    "HOLDSPEAK_RESTART_CHECK": "off",
    "HOLDSPEAK_SCREEN_RULES": "off",
    "HOLDSPEAK_CALLS": "off",
    "HOLDSPEAK_LINE": "off",
    "HOLDSPEAK_RECORDINGS": "off",
    "HOLDSPEAK_MIC_CHECK": "off",
    "HOLDSPEAK_PROGRAMS": "off",
    "HOLDSPEAK_PHONE": "off",
    "HOLDSPEAK_TELEGRAM": "off",
    "HOLDSPEAK_LOOP_WATCH": "0",
}


class _Coordinator:
    async def start(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None


class _Host:
    port = 8795
    voice_session = None

    def __init__(self) -> None:
        self.loops_started = 0

    def broadcast(self, _type: str, _data: object) -> None:
        return None

    def _conductor_start_meeting(self, *_a, **_k) -> None:
        return None

    def _conductor_stop_meeting(self, *_a, **_k) -> None:
        return None

    def _memory_live_check(self) -> str:
        return "idle"

    def start_loop_tasks(self, _web_ctx: object) -> None:
        self.loops_started += 1

    def start_liveness_task(self) -> None:
        self.loops_started += 1


def _started_threads(monkeypatch, tmp_path, extra_env: dict[str, str]) -> set[str]:
    import faulthandler

    from holdspeak import keystore
    from holdspeak.db import get_database, reset_database
    from holdspeak.runtime.background import start_background

    for key, value in {**SWITCHES_OFF, **extra_env}.items():
        monkeypatch.setenv(key, value)
    release = threading.Event()
    # The keystore is never opened in a test; the named thread still starts.
    monkeypatch.setattr(keystore, "warm", lambda: release.wait(10))
    monkeypatch.setattr(faulthandler, "register", lambda *_a, **_k: None)
    reset_database()
    get_database(tmp_path / f"background-{len(extra_env)}.db")
    web_ctx = SimpleNamespace(
        gate_service=None,
        project_update_service=None,
        meeting_service=None,
        project_steward_service=None,
        watch_service=None,
        inference_default_service=None,
    )
    hub = SimpleNamespace(
        web_ctx=web_ctx,
        refinement_coordinator=_Coordinator(),
        project_service=SimpleNamespace(recover_ask_tasks_on_startup=lambda: []),
    )
    host = _Host()

    async def run() -> set[str]:
        before = {t.ident for t in threading.enumerate()}
        stopper = await start_background(hub, host)
        # asyncio.to_thread's pool workers (asyncio_N) are not started work.
        started = {
            t.name for t in threading.enumerate()
            if t.ident not in before and not t.name.startswith("asyncio_")
        }
        release.set()
        await stopper.stop()
        return started

    try:
        started = asyncio.run(run())
    finally:
        reset_database()
    assert host.loops_started == 2
    return started


def test_every_switch_off_starts_only_the_unswitched_threads(monkeypatch, tmp_path) -> None:
    assert _started_threads(monkeypatch, tmp_path, {}) == UNSWITCHED


@pytest.mark.parametrize(
    ("switch", "value", "thread"),
    [("HOLDSPEAK_LOOP_WATCH", "1", "HoldSpeakLoopWatch"), ("HOLDSPEAK_PHONE", "on", "phone-sweep")],
)
def test_one_switch_on_starts_exactly_its_thread(monkeypatch, tmp_path, switch, value, thread) -> None:
    started = _started_threads(monkeypatch, tmp_path, {switch: value})
    assert started - UNSWITCHED == {thread}
