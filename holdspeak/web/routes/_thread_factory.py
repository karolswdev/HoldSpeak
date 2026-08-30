"""Shared ThreadService factory for routes that start turns (HS-151-04).

Both ``threads.py`` and ``primitives/recipes.py`` (the chat alias) need
an identically wired ThreadService — same broadcast, same kernel broker.
One factory, no copies.
"""
from __future__ import annotations

from typing import Any

from ..context import WebContext


def thread_service_from_ctx(ctx: WebContext) -> Any:
    """Build a ThreadService wired to the kernel broker and bus broadcast."""
    from ...db import get_database
    from ...kernel.runtime import _service as _kernel_service
    from ...services.thread_service import ThreadService

    from ...config import Config
    from ...mcp.tools import dispatch as mcp_dispatch

    broadcast = ctx.broadcast or (lambda t, d: None)
    return ThreadService(
        get_database(),
        broadcast=broadcast,
        broker=_kernel_service(),
        # HS-152-03: the Hands are live on the hub.  Execution = the
        # in-process MCP dispatch (settled design D2); the posture the
        # truth table reads is the desk's own control_mode.
        tool_dispatch_fn=mcp_dispatch,
        control_mode_fn=lambda: Config.load().control_mode,
    )
