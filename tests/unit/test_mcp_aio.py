"""``holdspeak.mcp.aio.run_async``: the one way an MCP tool body runs a coroutine."""
from __future__ import annotations

import asyncio
import threading
from collections.abc import Iterator

import pytest

from holdspeak.mcp import aio


@pytest.fixture()
def hub() -> Iterator[asyncio.AbstractEventLoop]:
    """A real running loop, registered as the hub's loop."""
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    aio.set_hub_loop(loop)
    try:
        yield loop
    finally:
        aio.set_hub_loop(None)
        loop.call_soon_threadsafe(loop.stop)
        thread.join(5)
        loop.close()


def test_with_no_hub_and_no_loop_it_runs_the_coroutine() -> None:
    async def answer() -> int:
        return 7

    assert aio.run_async(answer()) == 7


def test_from_a_worker_thread_it_awaits_a_hub_owned_future(hub: asyncio.AbstractEventLoop) -> None:
    """The coroutine awaits a Future the hub loop owns; it must run on that loop."""
    owned: asyncio.Future[str] = asyncio.run_coroutine_threadsafe(_make_future(), hub).result(5)
    hub.call_soon_threadsafe(hub.call_later, 0.05, owned.set_result, "from the hub")

    async def wait() -> str:
        return await owned

    assert aio.run_async(wait()) == "from the hub"


def test_on_the_hub_loop_thread_it_raises_a_clear_error_and_moves_nothing(hub: asyncio.AbstractEventLoop) -> None:
    """Astra on #766: a sync caller on the loop thread got "attached to a different loop"."""
    owned: asyncio.Future[str] = asyncio.run_coroutine_threadsafe(_make_future(), hub).result(5)
    ran: list[str] = []

    async def wait() -> str:
        ran.append("started")
        return await owned

    async def sync_caller_on_the_loop() -> str:
        try:
            aio.run_async(wait())
        except RuntimeError as exc:
            return str(exc)
        return "no error"

    message = asyncio.run_coroutine_threadsafe(sync_caller_on_the_loop(), hub).result(5)
    assert "running event loop" in message and "different loop" not in message, message
    assert ran == []  # the hub-owned work never started on another loop
    assert not owned.done()


def test_on_any_other_running_loop_it_raises_the_same_error() -> None:
    async def answer() -> int:
        return 7

    async def caller() -> None:
        aio.run_async(answer())

    with pytest.raises(RuntimeError, match="running event loop"):
        asyncio.run(caller())


async def _make_future() -> "asyncio.Future[str]":
    return asyncio.get_running_loop().create_future()
