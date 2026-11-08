"""Seed one connector_watches row for a test (the watch fold, 2026-11-08).

ReactionService.create_watch was the tests' legacy creator; it is parked.
This writes the same row through the same repository call
(``db.automations.create_watch``), with the same connector normalisation.
"""
from __future__ import annotations

import uuid
from typing import Any


def seed_watch(db: Any, *, connector_id: str, query_kind: str, name: str = "",
               query: dict[str, Any] | None = None, enabled: bool = True,
               watch_id: str | None = None) -> dict[str, Any]:
    connector = connector_id.strip().lower()
    if connector == "github":
        connector = "gh"
    return db.automations.create_watch(
        watch_id=watch_id or f"watch_{uuid.uuid4().hex[:12]}", connector_id=connector,
        query_kind=query_kind.strip().lower(), name=name.strip(), query=query or {},
        enabled=enabled,
    )
