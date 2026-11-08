"""One maker of prefixed random ids (HS-S54).

``new_id("note")`` is ``note_`` and twelve hex characters of a fresh UUID4,
made at call time: the shape the desk primitives, Threads, recipes,
Workbenches and the built-in skills store. A module that makes these ids
imports this one (``from holdspeak.ids import new_id as _new_id``), so a test
can still patch the module's own ``_new_id``.

Ids of another shape keep their own maker on purpose: Programs use a hyphen
(``program-…``), the phone uses ``secrets.token_hex(8)``.
"""
from __future__ import annotations

import uuid

__all__ = ["new_id"]


def new_id(prefix: str) -> str:
    """``<prefix>_`` and twelve fresh UUID4 hex characters."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
