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

MCP-006: each family import is individually guarded so a broken unrelated
family cannot suppress any healthy family's tools.  Degraded families are
recorded in DEGRADED_FAMILIES for structured reporting.
"""
from __future__ import annotations

import importlib
import logging
from types import ModuleType
from typing import Any

_log = logging.getLogger(__name__)

# Ordered list of family module names under holdspeak.mcp.families.
_FAMILY_MODULE_NAMES: list[str] = [
    "ask",
    "settings",
    "coder",
    "cadence",
    "sequence",
    "memory",
    "people",
    "plugin_job",
    "reactions",
    "thought",
    "inference",
    "model_library",
    "inference_assignments",
    "concierge",
    "door",
    "thread",
    "project",
]

# MCP-006 isolation: import each family, record failures.
FAMILIES: list[ModuleType] = []
DEGRADED_FAMILIES: dict[str, str] = {}

for _name in _FAMILY_MODULE_NAMES:
    try:
        _mod = importlib.import_module(f"holdspeak.mcp.families.{_name}")
        FAMILIES.append(_mod)
    except Exception as _exc:
        _log.error("MCP family %s failed to load: %s", _name, _exc)
        DEGRADED_FAMILIES[_name] = str(_exc)

# Re-export the successfully loaded modules as module-level names so
# existing code that does `from holdspeak.mcp.families import door` etc.
# continues to work (these are all present when nothing is broken).
import sys as _sys
_this = _sys.modules[__name__]
for _fam in FAMILIES:
    _short = _fam.__name__.rsplit(".", 1)[-1]
    setattr(_this, _short, _fam)

del _name, _sys, _this, _short, _fam  # type: ignore[name-defined]
# _mod may be unbound if last family failed, guard the del
try:
    del _mod  # type: ignore[name-defined]
except NameError:
    pass
