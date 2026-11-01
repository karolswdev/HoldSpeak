"""The Later words and the night window on the day the clocks change
(2026-11-01 in America/Denver: 02:00 MDT goes back to 01:00 MST, so 01:30
happens twice).

``local.replace(hour=13)`` kept the morning's offset: "At 13:00" pressed at
01:30 MDT came out 12:00 MST, and "Tomorrow" from the evening before came out
an hour early. ``wall_clock`` builds the wall time on its date first; this
pins the zone and checks both 01:30s.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import pytest

from holdspeak.services.briefing_service import later_until
from holdspeak.services.program_night import window
from holdspeak.services.reach_service import parse_later
from holdspeak.services.wall_clock import at_local, next_local

MDT = timezone(timedelta(hours=-6))
MST = timezone(timedelta(hours=-7))
FIRST = datetime(2026, 11, 1, 1, 30, tzinfo=MDT)   # 07:30 UTC
SECOND = datetime(2026, 11, 1, 1, 30, tzinfo=MST)  # 08:30 UTC


@pytest.fixture(autouse=True)
def denver():
    before = os.environ.get("TZ")
    os.environ["TZ"] = "America/Denver"
    time.tzset()
    yield
    if before is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = before
    time.tzset()


@pytest.mark.parametrize("now", [FIRST, SECOND], ids=["first-0130", "second-0130"])
def test_at_13_is_13_00_mst_from_either_0130(now: datetime) -> None:
    for at in (later_until("at_13", now), parse_later("at_13", now), next_local(now, 13)):
        assert at.astimezone(MST) == datetime(2026, 11, 1, 13, 0, tzinfo=MST), at
        assert at.astimezone().strftime("%H:%M") == "13:00"


@pytest.mark.parametrize("now", [FIRST, SECOND], ids=["first-0130", "second-0130"])
def test_tonight_and_tomorrow_keep_their_wall_time(now: datetime) -> None:
    assert later_until("tonight", now).astimezone(MST) == datetime(2026, 11, 1, 19, 0, tzinfo=MST)
    assert later_until("tomorrow", now).astimezone(MST) == datetime(2026, 11, 2, 7, 0, tzinfo=MST)
    assert parse_later("tomorrow", now, quiet=(22, 8)).astimezone(MST) == datetime(2026, 11, 2, 8, 0, tzinfo=MST)


def test_tomorrow_from_the_evening_before_is_not_an_hour_early() -> None:
    evening = datetime(2026, 10, 31, 21, 0, tzinfo=MDT)
    assert later_until("tomorrow", evening).astimezone(MST) == datetime(2026, 11, 1, 7, 0, tzinfo=MST)
    assert at_local(evening, 7, days=1).strftime("%H:%M") == "07:00"


def test_the_night_window_across_the_change_ends_at_its_wall_time() -> None:
    start, end = window({"start": "23:30", "end": "07:00"}, SECOND)
    assert start.astimezone(MDT) == datetime(2026, 10, 31, 23, 30, tzinfo=MDT)
    assert end.astimezone(MST) == datetime(2026, 11, 1, 7, 0, tzinfo=MST)
