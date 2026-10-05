"""CadenceService (CAD-1-04) — the orchestrated tick.

One tick = collect (project + score loops from sources) -> reload open loops ->
decide which are due under the policy. Phase 1 RETURNS the due set; it does not
render or deliver nudges (surfaces are Phase 2+) and performs no external side
effect. The service is driven by the in-runtime `CadenceMixin` thread (only when
enabled) and by `holdspeak cadence run-now` (synchronously, even when disabled).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from holdspeak.timestamps import aware, local_now, utc_iso
from typing import Optional

from .collector import LoopCollector
from .models import OpenLoop
from .policies import seed_policies
from .scheduler import SchedulerConfig, due_loops


@dataclass
class TickResult:
    at: str
    projected: int = 0
    open_loops: int = 0
    due: list[OpenLoop] = field(default_factory=list)

    @property
    def due_count(self) -> int:
        return len(self.due)


class CadenceService:
    def __init__(self, db, config):
        self._db = db
        self._config = config  # a CadenceConfig
        self._collector = LoopCollector(db)
        self._seeded = False

    def _ensure_seeded(self) -> None:
        if not self._seeded:
            seed_policies(self._db)
            self._seeded = True

    def _scheduler_config(self) -> SchedulerConfig:
        c = self._config
        return SchedulerConfig(
            pressure=getattr(c, "pressure", "normal"),
            quiet_hours_start=getattr(c, "quiet_hours_start", 22),
            quiet_hours_end=getattr(c, "quiet_hours_end", 8),
            max_nudges_per_day=getattr(c, "max_nudges_per_day", 12),
        )

    def _nudged_today(self, now: datetime) -> int:
        """Count nudges created today (Phase 1 creates none, so this is 0)."""
        start = utc_iso(aware(now).replace(hour=0, minute=0, second=0, microsecond=0))
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM cadence_nudges WHERE julianday(created_at) >= julianday(?)", (start,)
            ).fetchone()
        return int(row["n"]) if row else 0

    def tick(self, now: Optional[datetime] = None) -> TickResult:
        """One cadence pass: project the open loops and find the due ones.

        A tick writes with no request (the cadence thread runs it): when it
        changed a row it announces itself, one ``desk_changed`` frame
        (2026-10-05).
        """
        from holdspeak.runtime.announce_scope import announce_writes

        with announce_writes("cadence", "tick") as name:
            result = self._tick(now)
            for loop in result.due:
                name(str(getattr(loop, "id", "") or ""))
            return result

    def _tick(self, now: Optional[datetime] = None) -> TickResult:
        now = aware(now) if now else local_now()
        self._ensure_seeded()
        projected = self._collector.collect(now=now)
        open_loops = self._db.cadence.list_loops()  # excludes terminal, ordered by score
        due = due_loops(
            open_loops,
            now=now,
            config=self._scheduler_config(),
            nudged_today=self._nudged_today(now),
        )
        return TickResult(
            at=utc_iso(now),
            projected=len(projected),
            open_loops=len(open_loops),
            due=due,
        )
