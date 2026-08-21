"""Sidecar-lifetime execution host for Thought refinement MCP tools."""
from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from holdspeak.db import get_database
from holdspeak.services.refinement_coordinator import RefinementCoordinator

T = TypeVar("T")


class SidecarRefinementRuntime:
    """Keep one coordinator loop alive for the full stdio process lifetime.

    The MCP protocol loop is deliberately synchronous.  A dedicated event-loop
    thread lets ``thought.refine`` return after durable reservation while the
    provider turn continues and remains reachable by ``thought.stop_refinement``.
    This process never performs global startup recovery; the web runtime owns
    that responsibility and may be using the same database concurrently.
    """

    def __init__(
        self,
        coordinator_factory: Callable[[], RefinementCoordinator] | None = None,
    ) -> None:
        self._factory = coordinator_factory or (
            lambda: RefinementCoordinator(get_database(), host_kind="mcp")
        )
        self._loop: asyncio.AbstractEventLoop | None = None
        self._coordinator: RefinementCoordinator | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._startup_error: BaseException | None = None

    @property
    def coordinator(self) -> RefinementCoordinator:
        if self._coordinator is None:
            raise RuntimeError("MCP refinement runtime is not started")
        return self._coordinator

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run_loop, name="holdspeak-mcp-refinement", daemon=True
        )
        self._thread.start()
        self._ready.wait()
        if self._startup_error is not None:
            raise RuntimeError("MCP refinement runtime failed to start") from self._startup_error

    def call(self, awaitable: Awaitable[T]) -> T:
        loop = self._loop
        if loop is None or not loop.is_running():
            if hasattr(awaitable, "close"):
                awaitable.close()  # type: ignore[attr-defined]
            raise RuntimeError("MCP refinement runtime is not running")
        return asyncio.run_coroutine_threadsafe(awaitable, loop).result()

    def close(self) -> None:
        loop, thread = self._loop, self._thread
        if loop is None or thread is None:
            return
        coordinator = self._coordinator
        if coordinator is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(coordinator.shutdown(), loop).result()
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)
        self._loop = None
        self._coordinator = None
        self._thread = None

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            coordinator = self._factory()
            self._coordinator = coordinator
            loop.run_until_complete(coordinator.start(recover_abandoned=False))
        except BaseException as exc:
            self._startup_error = exc
            self._ready.set()
            loop.close()
            return
        self._ready.set()
        try:
            loop.run_forever()
        finally:
            loop.close()
