"""Per-family MCP tool modules aggregated by tools.py.

Each family module exports:

    TOOLS: list[dict]     -- MCP tool schemas (may be empty during scaffolding).
    dispatch(name, arguments, principal) -> Any
        Route a tool call to this family.  tools.py routes by name
        membership in TOOLS, so dispatch is only called for owned names;
        it raises LookupError for unowned names purely as a safety
        fallback, and any error it raises for an owned name surfaces to
        the caller.

The FAMILIES list below is the canonical import order; tools.py iterates
it to build the aggregated catalogue and dispatch chain.
"""
from __future__ import annotations

from holdspeak.mcp.families import (
    ask,
    cadence,
    coder,
    memory,
    people,
    plugin_job,
    reactions,
    sequence,
    settings,
    thought,
)

FAMILIES = [ask, settings, coder, cadence, sequence, memory, people, plugin_job, reactions, thought]
