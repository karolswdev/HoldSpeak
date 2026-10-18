"""What each agent CLI engine run cost, and how it ended (Betterment E2).

One row per run in ``cli_engine_runs`` (``holdspeak/db/schema.py``): the
engine's profile id, when it ran, how it ended and the cost the CLI reported.
The Engines window reads two sums from it (today and this week, in the hub's
own time zone) and NOT SIGNED IN from the last run.

A write never breaks a run: a failed write is logged and the answer goes on.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from ..logging_config import get_logger

log = get_logger("intel.cli_engine_runs")

ANSWERED = "answered"
NOT_SIGNED_IN = "not_signed_in"
FAILED = "failed"
OUTCOMES = frozenset({ANSWERED, NOT_SIGNED_IN, FAILED})

#: Words an agent CLI prints when it has no sign-in (Claude Code:
#: "Invalid API key. Please run /login"; Codex: "Not logged in").
_SIGN_IN_WORDS = ("/login", "not logged in", "please log in", "please login", "invalid api key", "sign in")


def says_not_signed_in(stderr: str) -> bool:
    """True when the CLI's error output says that it has no sign-in."""
    text = " ".join(str(stderr or "").lower().split())
    return any(word in text for word in _SIGN_IN_WORDS)


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_run(
    profile_id: str,
    outcome: str,
    cost_usd: Optional[float] = None,
    *,
    db: Any = None,
    now: Optional[datetime] = None,
) -> None:
    """Add one run row. No profile id = no row (an engine built outside a job)."""
    if not str(profile_id or "").strip() or outcome not in OUTCOMES:
        return
    try:
        if db is None:
            from ..db import get_database

            db = get_database()
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO cli_engine_runs (profile_id, ran_at, outcome, cost_usd) VALUES (?, ?, ?, ?)",
                (str(profile_id), _stamp(now or datetime.now(timezone.utc)), outcome,
                 None if cost_usd is None else float(cost_usd)),
            )
    except Exception as exc:  # never break the run for its ledger
        log.warning(f"agent engine run not recorded: {exc}")


def _week_start(local_now: datetime) -> datetime:
    day = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return day - timedelta(days=day.weekday())


def spend_summary(db: Any, profile_ids: list[str], *, now: Optional[datetime] = None) -> dict[str, Any]:
    """Today's and this week's reported cost, and the last run's outcome.

    ``profile_ids`` names one engine (its profile row id and its model
    library id can differ). Today starts at local midnight; the week starts
    on Monday at local midnight.
    """
    ids = [str(pid) for pid in profile_ids if str(pid or "").strip()]
    summary: dict[str, Any] = {"todayUsd": 0.0, "weekUsd": 0.0, "lastOutcome": None}
    if not ids or db is None:
        return summary
    local_now = (now or datetime.now(timezone.utc)).astimezone()
    today = _stamp(local_now.replace(hour=0, minute=0, second=0, microsecond=0))
    week = _stamp(_week_start(local_now))
    id_list = json.dumps(ids)
    try:
        with db._connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(CASE WHEN ran_at >= ? THEN cost_usd END), 0) AS today,"
                " COALESCE(SUM(cost_usd), 0) AS week"
                " FROM cli_engine_runs"
                " WHERE profile_id IN (SELECT value FROM json_each(?)) AND ran_at >= ?",
                (today, id_list, week),
            ).fetchone()
            last = conn.execute(
                "SELECT outcome FROM cli_engine_runs"
                " WHERE profile_id IN (SELECT value FROM json_each(?)) ORDER BY id DESC LIMIT 1",
                (id_list,),
            ).fetchone()
    except Exception as exc:
        log.info(f"agent engine runs not read: {exc}")
        return summary
    if row is not None:
        summary["todayUsd"] = round(float(row["today"] or 0), 4)
        summary["weekUsd"] = round(float(row["week"] or 0), 4)
    if last is not None:
        summary["lastOutcome"] = str(last["outcome"])
    return summary


__all__ = [
    "ANSWERED",
    "FAILED",
    "NOT_SIGNED_IN",
    "record_run",
    "says_not_signed_in",
    "spend_summary",
]
