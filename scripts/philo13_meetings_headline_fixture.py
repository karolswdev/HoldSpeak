#!/usr/bin/env python3
"""Mint the PHILO-13-03 Meetings-headline cases through the real producers.

The meetings are saved and enqueued by the stop-handoff producer, and the REAL
intel queue executor (``process_next_intel_job``) runs, fails, retries or
holds each summary: the deferred-queue rig of
``tests/e2e/test_philo13_04_faces_glass.py`` (only the provider's completion
text and the plugin route are doubles). Each case is read back through the
real ``GET /api/meetings`` list route, so the rows are the wire the Meetings
window reads.

Usage (always with an isolated HOME outside the owner's)::

    HOME=/tmp/x uv run python scripts/philo13_meetings_headline_fixture.py --home /tmp/x

Prints ``{"cases": {"stored": [...], "running": [...], "queued": [...],
"retrying": [...], "failed": [...], "rerun_running": [...]}}``: the list rows
of each case.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pwd
import sys
import threading
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

MEETING_ID = "philo13-a2w-headline"

# Called with the rig's Database just before each case's list read; the glass
# fence uses it to copy the database at that instant (a held run included).
ON_READ: Any = None


def _isolated(home: Path) -> Path:
    real = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    home = home.expanduser().resolve()
    if home == real or home.is_relative_to(real):
        raise SystemExit("--home must be outside the owner's real HOME")
    return home


def _rows(db: Any) -> list[dict[str, Any]]:
    from scripts.philo13_needs_you_fixture import _route_client

    if ON_READ is not None:
        ON_READ(db)
    with _route_client(db) as client:
        response = client.get("/api/meetings?limit=50")
        if response.status_code != 200:
            raise RuntimeError(f"/api/meetings answered {response.status_code}: {response.text}")
        return list(response.json()["meetings"])


def _case(home: Path, name: str, steps: Any) -> list[dict[str, Any]]:
    import pytest

    from tests.e2e.test_philo13_04_faces_glass import _outcome_meeting
    from tests.unit.test_phase200_meeting_outcomes import _rig

    rig = home / name
    rig.mkdir(parents=True, exist_ok=False)
    with pytest.MonkeyPatch.context() as mp:
        db, engine = _rig(rig, mp)
        _outcome_meeting(db, MEETING_ID, "Payments cut-over review")
        return steps(db, engine, mp)


def _drain(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    from holdspeak.intel_queue import process_next_intel_job

    while process_next_intel_job():
        pass
    return _rows(db)


def _rerun(db: Any) -> None:
    db.intel.enqueue_intel_job(
        MEETING_ID, transcript_hash=db.meetings.get_meeting(MEETING_ID).transcript_hash(),
        reason="re-run")


def _hold(db: Any, engine: Any) -> list[dict[str, Any]]:
    """Read the rows while the REAL executor holds the run at the provider."""
    from holdspeak.intel_queue import process_next_intel_job

    entered, release = threading.Event(), threading.Event()
    real_analyze = engine.analyze

    def held(transcript: str, **kwargs: Any) -> Any:
        entered.set()
        release.wait(60.0)
        return real_analyze(transcript, **kwargs)

    engine.analyze = held  # the provider answers only after the read
    worker = threading.Thread(target=process_next_intel_job, daemon=True)
    worker.start()
    try:
        if not entered.wait(60.0):
            raise RuntimeError("the executor never reached the provider")
        return _rows(db)
    finally:
        release.set()
        worker.join(60.0)


def _fail_once(engine: Any, attempts: int) -> None:
    from holdspeak.intel_queue import process_next_intel_job

    engine.error = "provider failed"
    assert process_next_intel_job(retry_max_attempts=attempts) is True


def stored(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    """The run finished: the summary is stored."""
    return _drain(db, engine, mp)


def running(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    """The first run is with the provider: no summary stored yet."""
    return _hold(db, engine)


def queued(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    """Enqueued at stop handoff; this hub has no drainer."""
    return _rows(db)


def retrying(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    """The first run failed once and waits for its retry."""
    _fail_once(engine, 3)
    return _rows(db)


def failed(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    """The first run failed for good."""
    _fail_once(engine, 1)
    return _rows(db)


def rerun_running(db: Any, engine: Any, mp: Any) -> list[dict[str, Any]]:
    """A stored summary whose re-run is with the provider."""
    _drain(db, engine, mp)
    _rerun(db)
    return _hold(db, engine)


CASES = {"stored": stored, "running": running, "queued": queued,
         "retrying": retrying, "failed": failed, "rerun_running": rerun_running}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", required=True, type=Path)
    args = parser.parse_args(argv)
    home = _isolated(args.home)
    out = {"cases": {name: _case(home, name, fn) for name, fn in CASES.items()}}
    json.dump(out, sys.stdout, default=str)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
