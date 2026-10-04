"""The one way an MCP tool body runs a coroutine.

MCP dispatch is synchronous; some services are async. Every tool that calls an
async service goes through :func:`run_async`.

- Inside the hub, the coroutine runs on the hub's event loop (the loop the web
  routes use, the loop that owns the hub's futures and tasks), and the calling
  worker thread waits for the result. The hub registers its loop with
  :func:`set_hub_loop` at startup. ``POST /api/mcp`` runs every tool call on a
  worker thread, so a tool always arrives here off the loop.
- With no hub loop (a unit test, the bare diagnosis hatch), ``asyncio.run``.
- A caller on a running event loop is a programming error: synchronous code
  cannot wait on its own loop, and loop-bound work must not move to another
  loop. ``run_async`` raises :class:`RuntimeError`; the caller must ``await``
  the service, or call the tool from a worker thread.
"""
from __future__ import annotations

import asyncio
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
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        coro.close()
        raise RuntimeError(
            "MCP tool code called run_async on a running event loop. "
            "Await the service, or run the tool call on a worker thread."
        )
    hub = _hub_loop
    if hub is not None and hub.is_running():
        return asyncio.run_coroutine_threadsafe(coro, hub).result()
    return asyncio.run(coro)
