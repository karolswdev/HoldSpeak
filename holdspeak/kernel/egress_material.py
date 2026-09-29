"""What an ``external.egress`` admission binds and what its native result keeps (PHILO-10-03).

A typed concern carved beside ``kernel/external_egress.py`` (the kernel density guard).
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

_DIGEST = re.compile(r"^(?:sha256:)?([0-9a-f]{64})$")


def frozen_digest(payload_material: Any) -> str:
    """PHILO-10-03: ``{"payload_digest": <sha256>}`` names the frozen bytes' own digest.

    A caller that froze its exact transport bytes (the email channel: the
    provider's request body, frozen at prepare) passes their digest; the
    admission binds THAT digest, not a hash of a description of it. Any other
    material is hashed as before. ``""`` when the material is not that form.
    """
    if isinstance(payload_material, Mapping) and set(payload_material) == {"payload_digest"}:
        found = _DIGEST.fullmatch(str(payload_material["payload_digest"] or ""))
        if found:
            return "sha256:" + found.group(1)
    return ""


def payload_digest_of(payload_material: Any) -> str:
    """The admission's ``payload_digest``: the frozen bytes' own digest, else the material hashed (as before)."""
    frozen = frozen_digest(payload_material)
    if frozen:
        return frozen
    try:
        encoded = json.dumps(payload_material, separators=(",", ":"), sort_keys=True, default=str)
    except (TypeError, ValueError):
        encoded = repr(payload_material)
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()


def sanitized_error(exc: BaseException) -> str:
    """What a native result keeps of a transport exception: its type, never its text.

    PHILO-10-03 (Codex Astra r3 finding 2): ``str(exc)`` can carry a header, a
    key or the body the sender held; the type name cannot.
    """
    return type(exc).__name__
