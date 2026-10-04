"""The one way an MCP tool body runs a coroutine.

MCP dispatch is synchronous; some services are async. Every tool that calls an
async service goes through :func:`run_async`. It never refuses:

- Inside the hub, the coroutine runs on the hub's event loop (the loop the web
  routes use), and the calling worker thread waits for the result. The hub
  registers its loop with :func:`set_hub_loop` at startup.
- With no hub loop (a unit test, the bare diagnosis hatch), ``asyncio.run``.
- If the caller is itself on a running loop, the coroutine runs to completion on
  a short-lived thread with its own loop. The caller's loop waits; it does not fail.
"""
from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

_hub_loop: asyncio.AbstractEventLoop | None = None


def set_hub_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    """The hub's composition root names its event loop here (``None`` at shutdown)."""
    global _hub_loop
    _hub_loop = loop


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run *coro* to completion from synchronous tool code and return its result."""
    try:
        here = asyncio.get_running_loop()
    except RuntimeError:
        here = None
    hub = _hub_loop
    if here is None:
        if hub is not None and hub.is_running():
            return asyncio.run_coroutine_threadsafe(coro, hub).result()
        return asyncio.run(coro)

    # The caller is on a running loop: it cannot wait on that loop for itself.
    box: dict[str, Any] = {}

    def work() -> None:
        try:
            box["value"] = asyncio.run(coro)
        except BaseException as exc:  # carried to the caller below
            box["error"] = exc

    thread = threading.Thread(target=work, name="holdspeak-mcp-async", daemon=True)
    thread.start()
    thread.join()
    if "error" in box:
        raise box["error"]
    return box["value"]
