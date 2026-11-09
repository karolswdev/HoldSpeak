"""The verbs of the coder sessions and their steering (``/api/coders``) on ``CoderService``, on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb
once: its call, its HTTP method and path, and its MCP tool schema.
``web/routes/system/coders.py`` produces the routes and ``mcp/families/declared.py`` the
tools from these rows, both through ``OperationRegistry.invoke``.

A read is ``thread="evidence_read"`` and stays MCP and HTTP only (the seeded
thread palettes do not grow, ``services/thread_modes.py``); a write is
``thread="effect_proposal"``. A launched agent reads these reads and never
calls these writes (``services/conductor_launch.py`` derives both rules from
the rows). Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from holdspeak.operations import OperationDescriptor

CODER_OPERATIONS: tuple[OperationDescriptor, ...] = ()

__all__ = ["CODER_OPERATIONS"]
