"""HOLDSPEAK_LOOP_WATCH=1: name each handler that holds the hub's event loop.

PERF-HUB 2026-10-28: one sync handler on the loop stalls every other request
(sprites and JS chunks too). With the switch on, asyncio debug logs each
callback over 100 ms, and a watcher thread names the code that held the loop:
it pings the loop every 50 ms and, when a ping waits more than 100 ms, logs the
innermost ``holdspeak`` frames of the loop thread. (asyncio's own line names a
Starlette task, never the route, so the frames are what tells the name.)

Off by default: debug mode and the watcher cost time on every call.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import threading
import time

log = logging.getLogger("holdspeak.loop_watch")

SLOW_S = 0.1
PING_S = 0.05


def enabled() -> bool:
    return os.environ.get("HOLDSPEAK_LOOP_WATCH", "").strip() == "1"


def _holder(loop_thread: int) -> str:
    frame = sys._current_frames().get(loop_thread)
    names: list[str] = []
    while frame is not None:
        path = frame.f_code.co_filename
        if f"{os.sep}holdspeak{os.sep}" in path and "loop_watch" not in path:
            names.append(f"{path.rsplit(os.sep + 'holdspeak' + os.sep, 1)[-1]}:"
                         f"{frame.f_code.co_name}:{frame.f_lineno}")
        frame = frame.f_back
    return " <- ".join(names[:4]) or "(no holdspeak frame)"


def _watch(loop: asyncio.AbstractEventLoop, loop_thread: int) -> None:
    while not loop.is_closed():
        served = threading.Event()
        try:
            loop.call_soon_threadsafe(served.set)
        except RuntimeError:  # the loop closed
            return
        if not served.wait(SLOW_S):
            started = time.monotonic() - SLOW_S
            holder = _holder(loop_thread)
            served.wait()
            log.warning("Loop held %.0f ms by %s", (time.monotonic() - started) * 1000, holder)
        time.sleep(PING_S)


def start(loop: asyncio.AbstractEventLoop) -> None:
    """Call on the loop (the hub's startup): debug mode plus the watcher thread."""
    loop.set_debug(True)
    loop.slow_callback_duration = SLOW_S
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    threading.Thread(
        target=_watch, args=(loop, threading.get_ident()),
        name="HoldSpeakLoopWatch", daemon=True,
    ).start()
    log.warning("Loop watch is ON: a handler that holds the loop over 100 ms is logged.")
