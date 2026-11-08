# PARKED 2026-11-08 (HS-S56): deprecated since HS-153-01 ("Default-to-Desk was wrong
# for unbound threads"); no caller in holdspeak/, scripts/, uat/, MCP or by string;
# only its own tests read it (parked beside it). palette_for is the one palette read.
from __future__ import annotations

from typing import TYPE_CHECKING

from holdspeak.services.thread_modes import _DESK_TOOLS, palette_for
from holdspeak.services.thread_tools import TOOL_NAMES

if TYPE_CHECKING:
    from holdspeak.db import Database


def allowed_tools_for_thread(db: "Database", thread_id: str) -> frozenset[str]:
    """Return the effective tool palette for a thread.

    mode allow-list intersected with TOOL_NAMES; no mode -> Desk's list.

    .. deprecated:: HS-153-01
        Callers in ThreadService should use ``palette_for`` instead,
        which returns None when no mode is bound (caller uses CHAT_PALETTE).
        This function is kept for backward compat.
    """
    palette = palette_for(db, thread_id)
    if palette is None:
        return _DESK_TOOLS & TOOL_NAMES
    return palette
