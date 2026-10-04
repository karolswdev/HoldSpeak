"""``holdspeak.mcp.aio.run_async``: the one way an MCP tool body runs a coroutine."""
from __future__ import annotations

import asyncio
import threading

from holdspeak.mcp import aio


async def _loop_of() -> asyncio.AbstractEventLoop:
    return asyncio.get_running_loop()


def test_with_no_loop_it_runs_the_coroutine() -> None:
    assert isinstance(aio.run_async(_loop_of()), asyncio.AbstractEventLoop)


def test_inside_a_running_loop_it_answers_and_never_refuses() -> None:
    async def caller() -> bool:
        return aio.run_async(_loop_of()) is not asyncio.get_running_loop()

    assert asyncio.run(caller()) is True


def test_from_a_worker_thread_it_runs_on_the_hub_loop() -> None:
    hub = asyncio.new_event_loop()
    thread = threading.Thread(target=hub.run_forever, daemon=True)
    thread.start()
    aio.set_hub_loop(hub)
    try:
        assert aio.run_async(_loop_of()) is hub
    finally:
        aio.set_hub_loop(None)
        hub.call_soon_threadsafe(hub.stop)
        thread.join(5)
        hub.close()
