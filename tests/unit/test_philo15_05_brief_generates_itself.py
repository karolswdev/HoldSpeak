"""PHILO-15 lane 05, ruling 2 (inventory gap 10): the morning Brief generates
itself.

The cadence thread's Brief job is ON by default and makes the day's Brief
once per local day at ``brief_hour`` (06:00), before the owner arrives. The
loop job (project, score, nudge) keeps its default: OFF. Quiet hours do not
hold the Brief: it is deterministic and sends nothing.

Real producers: the real CadenceMixin tick body, the real
MondayBriefService.generate over a real database, the real pipeline_events
receipt. The clock is the one fake.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.runtime.cadence import CadenceMixin


class _Runtime(CadenceMixin):
    def __init__(self) -> None:
        self.config = Config()  # the shipped defaults
        self.loop_ticks = 0

    def _cadence_service(self):  # the loop job: record, never run
        runtime = self

        class _Loop:
            def tick(self):
                runtime.loop_ticks += 1
                raise AssertionError("the loop job is off by default")

        return _Loop()


def _briefs(db: Database) -> list[str]:
    with db._connection() as conn:
        return [r["generated_at"] for r in conn.execute(
            "SELECT generated_at FROM monday_briefs ORDER BY generated_at"
        ).fetchall()]


def _receipts(db: Database) -> int:
    with db._connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM pipeline_events WHERE method='brief.regenerated'"
        ).fetchone()[0]


def test_the_brief_job_fires_once_per_local_day_at_its_hour(tmp_path: Path) -> None:
    db = Database(tmp_path / "brief.db")
    runtime = _Runtime()
    assert runtime._cadence_jobs_enabled() is True  # the thread starts on defaults
    clock = {"now": datetime(2026, 10, 8, 5, 55)}

    def tick() -> None:
        with patch("holdspeak.db.get_database", return_value=db), patch(
            "holdspeak.runtime.cadence.local_now", side_effect=lambda: clock["now"]
        ):
            runtime._cadence_tick_body()

    tick()  # 05:55: before the Brief hour (inside quiet hours)
    assert _briefs(db) == [] and _receipts(db) == 0

    clock["now"] = datetime(2026, 10, 8, 6, 0)
    tick()  # 06:00: the Brief is made, still inside quiet hours
    assert len(_briefs(db)) == 1 and _receipts(db) == 1

    for minute in (5, 30, 55):
        clock["now"] = datetime(2026, 10, 8, 7, minute)
        tick()  # the same local day: never twice
    clock["now"] = datetime(2026, 10, 8, 23, 50)
    tick()
    assert len(_briefs(db)) == 1 and _receipts(db) == 1

    clock["now"] = datetime(2026, 10, 9, 6, 1)
    tick()  # the next local day: once more
    assert len(_briefs(db)) == 2 and _receipts(db) == 2
    assert runtime.loop_ticks == 0  # the loop job kept its default: off


def test_the_brief_job_off_makes_no_brief(tmp_path: Path) -> None:
    db = Database(tmp_path / "off.db")
    runtime = _Runtime()
    runtime.config.cadence.brief_enabled = False
    assert runtime._cadence_jobs_enabled() is False  # no thread at all
    with patch("holdspeak.db.get_database", return_value=db), patch(
        "holdspeak.runtime.cadence.local_now", return_value=datetime(2026, 10, 8, 9, 0)
    ):
        runtime._cadence_tick_body()
    assert _briefs(db) == [] and _receipts(db) == 0


def test_the_cadence_status_names_the_brief_job(tmp_path: Path) -> None:
    # The Rhythm row's DAILY token reads this (web/src/pages/cores/CadenceCore.tsx).
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.cadence_service import CadenceService

    db = Database(tmp_path / "status.db")
    owner = Principal(PrincipalKind.OWNER, "philo15-05")
    status = CadenceService(db, Config().cadence).status(owner)
    assert status["enabled"] is False
    assert status["brief_job"] == {"enabled": True, "hour": 6}
