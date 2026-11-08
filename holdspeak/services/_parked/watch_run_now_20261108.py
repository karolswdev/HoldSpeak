"""Parked 2026-11-08: ``watch_service._run_now``.

An Automation's event start ran its occurrence item through the async
``WorkbenchService.run_item``; this helper ran that coroutine from the
watch's sync sweep. The start now runs a Program of one prompt step
(``automation_runs.run_as_program``), which is sync, so nothing calls it.
"""
from __future__ import annotations

from typing import Any


def _run_now(coro: Any) -> Any:
    """Run one coroutine to its end from sync code, on or off an event loop."""
    import asyncio
    import threading

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    box: dict[str, Any] = {}

    def target() -> None:
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as exc:  # handed back to the caller's thread
            box["error"] = exc

    thread = threading.Thread(target=target, name="watch-automation-run")
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box.get("value")
