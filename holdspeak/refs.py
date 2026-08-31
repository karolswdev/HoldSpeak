"""Qualified-ref grammar for Project Rooms (REF-001..004).

A qualified ref encodes a citizen type and an opaque local identity as
``type:id``.  This module is the single authority for parsing,
formatting, and validating those refs.  It is PURE: no DB, no IO,
no side-effects.

Canonical-vs-alias ruling (REF-003)
------------------------------------
Canonical: ``people:``  (every existing emitter produces this form;
5 of 6 existing parsers match it).  Alias: ``person:``
(thread_service.py:311 is the sole consumer).  See
docs/internal/project-rooms/CONTRACTS-P0.md for the full evidence.

Unknown-type handling (REF-004)
-------------------------------
``parse()`` accepts any syntactically valid ref.  The returned
``QualifiedRef`` carries an ``is_registered`` flag.  ``format()``
refuses to emit an unregistered type (raises ``UnregisteredTypeError``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import FrozenSet, Mapping

# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------

# Canonical citizen types from SRS_DOMAIN_DRIVER SS3.2, mapped to the
# ref prefixes evidenced in the codebase.  Planned types (no emission
# evidence yet) are included so the set is closed from day one.
CITIZEN_TYPES: FrozenSet[str] = frozenset({
    "meeting",       # Meeting
    "decision",      # Decision
    "action_item",   # Door / follow-through
    "people",        # Person / participant  (canonical; alias "person")
    "thread",        # Thread
    "note",          # Note
    "artifact",      # Artifact
    "workbench",     # Workbench
    "agent",         # Agent / Recipe
    "repo",          # Repo / delivery system  (planned -- no emission evidence)
    "watch",         # Watch
    "kernel",        # Kernel / Desk object    (planned -- no emission evidence)
})

# Aliases: parse() resolves these to the canonical form; format()
# refuses them (callers must supply the canonical name).
_ALIASES: Mapping[str, str] = {
    "person": "people",       # REF-003: settled by evidence weight
    "door": "action_item",    # SRS names citizen "Door"; code uses "action_item"
}


# ------------------------------------------------------------------
# Errors
# ------------------------------------------------------------------

class RefError(ValueError):
    """Base for qualified-ref errors."""


class MalformedRefError(RefError):
    """The string is not syntactically ``<type>:<id>``."""


class UnregisteredTypeError(RefError):
    """format() was asked to emit an unregistered (or aliased) type."""


# ------------------------------------------------------------------
# Value object
# ------------------------------------------------------------------

# Ref format: one or more non-colon chars, a colon, one or more chars.
_REF_RE = re.compile(r"^([^:]+):(.+)$")


@dataclass(frozen=True, slots=True)
class QualifiedRef:
    """An immutable qualified reference to a citizen.

    ``type`` is always the canonical form (aliases resolved at parse
    time).  ``id`` is the opaque local identity -- the module never
    interprets its content.
    """

    type: str
    id: str

    @property
    def is_registered(self) -> bool:
        """True when the type belongs to the closed citizen registry."""
        return self.type in CITIZEN_TYPES

    def __str__(self) -> str:
        return f"{self.type}:{self.id}"


# ------------------------------------------------------------------
# API
# ------------------------------------------------------------------

def resolve_alias(type_name: str) -> str:
    """Return the canonical type for *type_name* (identity if not aliased)."""
    return _ALIASES.get(type_name, type_name)


def parse(ref: str) -> QualifiedRef:
    """Parse a ``type:id`` string into a :class:`QualifiedRef`.

    Aliases are resolved to the canonical form.  Unknown types produce
    a ``QualifiedRef`` with ``is_registered == False`` (REF-004).

    Raises :class:`MalformedRefError` if *ref* lacks the ``type:id``
    structure.
    """
    if not isinstance(ref, str) or not ref:
        raise MalformedRefError(f"Expected a non-empty string, got {ref!r}")
    m = _REF_RE.match(ref)
    if m is None:
        raise MalformedRefError(f"Not a valid qualified ref: {ref!r}")
    raw_type, raw_id = m.group(1), m.group(2)
    canonical_type = resolve_alias(raw_type)
    return QualifiedRef(type=canonical_type, id=raw_id)


def format(type_name: str, id: str) -> str:  # noqa: A002
    """Format a canonical ``type:id`` string.

    Raises :class:`UnregisteredTypeError` if *type_name* is not in
    ``CITIZEN_TYPES`` (aliases are also refused -- callers must supply
    the canonical name).

    Raises :class:`MalformedRefError` if *id* is empty.
    """
    if type_name not in CITIZEN_TYPES:
        if type_name in _ALIASES:
            raise UnregisteredTypeError(
                f"{type_name!r} is an alias for {_ALIASES[type_name]!r}; "
                f"use the canonical name"
            )
        raise UnregisteredTypeError(
            f"{type_name!r} is not a registered citizen type"
        )
    if not id:
        raise MalformedRefError("id must be non-empty")
    return f"{type_name}:{id}"
