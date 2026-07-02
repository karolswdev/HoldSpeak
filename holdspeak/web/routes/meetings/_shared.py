"""Helpers shared across the meetings route submodules (Phase 72 split)."""

from __future__ import annotations

from typing import Optional


def _parse_facet_date(value: Optional[str], *, end_of_day: bool = False):
    """Parse a facet date param (ISO date or datetime); None on blank/garbage.

    A bare date used as the range end is made inclusive of the whole day.
    """
    from datetime import datetime

    text = (value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if end_of_day and len(text) == 10:  # a bare YYYY-MM-DD
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    return parsed
