"""Per-family MCP tool modules aggregated by tools.py.

Each family module exports:

    TOOLS: list[dict]     -- MCP tool schemas (may be empty during scaffolding).
    dispatch(name, arguments, principal) -> Any
        Route a tool call to this family.  Raises LookupError for names
        the family does not own so the caller can fall through.

The FAMILIES list below is the canonical import order; tools.py iterates
it to build the aggregated catalogue and dispatch chain.
"""
from __future__ import annotations

from holdspeak.mcp.families import (
    ask,
    cadence,
    coder,
    memory,
    plugin_job,
    sequence,
    settings,
)

FAMILIES = [ask, settings, coder, cadence, sequence, memory, plugin_job]
