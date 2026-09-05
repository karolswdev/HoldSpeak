"""Cached needs-you aggregate (HS-171-03).

Moves the N+1 aggregation out of the route into a pure function
(``build_aggregate``) and wraps it in a stale-while-refresh cache
(``cached_aggregate``).  The cadence sweep calls ``invalidate`` after
each tick; the route reads ``cached_aggregate`` which is O(1) on a warm
cache.

The sibling HeartbeatService (holdspeak/services/heartbeat_service.py)
can call ``build_aggregate`` or ``cached_aggregate`` directly -- this
module is the SINGLE owner of the aggregate shape.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable

log = logging.getLogger(__name__)

_SEVERITY_ORDER = {"danger": 0, "warning": 1, "info": 2}


# ── Pure aggregate builder (the N+1 lives here, nowhere else) ─────────


def build_aggregate(
    *,
    list_projects: Callable[..., list[dict[str, Any]]],
    room: Callable[..., dict[str, Any]],
    principal: Any,
    door_upcoming: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build the full needs-you payload.

    Parameters mirror the dependencies the route used to close over:
    ``list_projects`` and ``room`` come from ProjectService;
    ``door_upcoming`` from DoorService._upcoming (optional).

    Returns the SAME shape the route returned before, plus ``computedAt``.
    """
    projects = list_projects(principal, {"include_archived": False})
    items: list[dict[str, Any]] = []
    project_ids: set[str] = set()

    for proj in projects:
        pid = proj.get("id") or ""
        if not pid:
            continue
        try:
            rm = room(principal, pid)
        except Exception:
            continue
        needs = rm.get("needsYou", {})
        if needs.get("state") != "ok":
            continue
        for item in needs.get("items") or []:
            items.append({
                "projectId": pid,
                "projectName": proj.get("name") or proj.get("title") or "",
                "ref": item.get("title", ""),
                "title": item.get("title", ""),
                "why": item.get("why", ""),
                "ageToken": item.get("since", ""),
                "source": item.get("source", ""),
                "verbHref": item.get("url"),
                "severity": item.get("severity", "info"),
            })
            project_ids.add(pid)

    items.sort(key=lambda r: (
        _SEVERITY_ORDER.get(r.get("severity", "info"), 2),
        r.get("ageToken") or "",
    ))

    next_item = None
    if door_upcoming is not None:
        try:
            upcoming = door_upcoming(datetime.now())
            if upcoming:
                first = upcoming[0]
                next_item = {
                    "label": first.get("title", ""),
                    "at": first.get("starts_at"),
                }
        except Exception:
            pass

    computed_at = datetime.now().isoformat()
    return {
        "count": len(items),
        "projects": sorted(project_ids),
        "items": items,
        "next": next_item,
        "computedAt": computed_at,
        "stale": False,
        "sweepId": None,
    }


# ── Stale-while-refresh cache ────────────────────────────────────────


class NeedsYouCache:
    """Thread-safe stale-while-refresh cache for the aggregate.

    ``max_age_s`` defaults to 900 (15 min, matching the default cadence
    interval).  A call to ``invalidate()`` marks the cache stale
    immediately; the next ``get()`` triggers a rebuild via the
    ``builder`` callback.
    """

    def __init__(
        self,
        builder: Callable[[], dict[str, Any]],
        *,
        max_age_s: float = 900.0,
    ) -> None:
        self._builder = builder
        self._max_age_s = max_age_s
        self._lock = threading.Lock()
        self._data: dict[str, Any] | None = None
        self._computed_at: float = 0.0
        self._sweep_id: str | None = None

    def get(self, *, force: bool = False) -> dict[str, Any]:
        """Return the cached aggregate; rebuild on miss or force."""
        now = time.monotonic()
        with self._lock:
            if not force and self._data is not None and (now - self._computed_at) < self._max_age_s:
                return self._data

        # Build outside the lock (the N+1 is slow).
        data = self._builder()
        with self._lock:
            data["stale"] = False
            data["sweepId"] = self._sweep_id
            self._data = data
            self._computed_at = time.monotonic()
        return data

    def invalidate(self, *, sweep_id: str | None = None) -> None:
        """Mark the cache stale; the next ``get()`` will rebuild."""
        with self._lock:
            self._data = None
            self._computed_at = 0.0
            if sweep_id is not None:
                self._sweep_id = sweep_id

    def peek(self) -> dict[str, Any] | None:
        """Return the cached data without rebuilding (for tests)."""
        with self._lock:
            if self._data is None:
                return None
            age = time.monotonic() - self._computed_at
            stale = age >= self._max_age_s
            return {**self._data, "stale": stale}


def cached_aggregate(
    cache: NeedsYouCache,
    *,
    force: bool = False,
    max_age_s: float | None = None,
) -> dict[str, Any]:
    """Convenience wrapper: read from the cache, optionally force.

    ``max_age_s`` is ignored here (lifetime is set on the cache); the
    parameter exists so the sibling HeartbeatService can call this with
    a signature that mirrors the design doc.
    """
    return cache.get(force=force)


__all__ = [
    "build_aggregate",
    "cached_aggregate",
    "NeedsYouCache",
]
