"""HS-200-46 — the documentation-claims registry (see :mod:`registry`)."""
from __future__ import annotations

from .registry import (  # noqa: F401
    CLAIMS,
    KNOWN_FALSE_RATCHET,
    KNOWN_FALSE_RATCHET_DATE,
    KNOWN_FALSE_RATCHET_REASON,
    Claim,
    holding_claims,
    known_false_claims,
    markdown_table,
)
