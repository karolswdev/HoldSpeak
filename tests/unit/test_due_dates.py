"""A said due becomes the day it names (Betterment daily D0).

The words are read against the meeting's own day. The recon's week: the
platform sync is Thursday 15 October 2026, the 1:1 with Theo Friday 16.
"""
from __future__ import annotations

from datetime import date

import pytest

from holdspeak.due_dates import resolve_due, stored_due

THURSDAY = date(2026, 10, 15)
FRIDAY = date(2026, 10, 16)


@pytest.mark.parametrize(("said", "anchor", "day"), [
    ("Wednesday", THURSDAY, date(2026, 10, 21)),
    ("by Wednesday", THURSDAY, date(2026, 10, 21)),
    ("Tuesday", THURSDAY, date(2026, 10, 20)),
    # The same weekday as the meeting is the next one, a week on.
    ("Thursday", THURSDAY, date(2026, 10, 22)),
    ("Monday", FRIDAY, date(2026, 10, 19)),
    ("by Monday morning", FRIDAY, date(2026, 10, 19)),
    ("Friday next week", THURSDAY, date(2026, 10, 23)),
    ("next Friday", THURSDAY, date(2026, 10, 23)),
    ("Friday EOD", THURSDAY, date(2026, 10, 16)),
    ("this week", THURSDAY, date(2026, 10, 16)),
    ("next week", THURSDAY, date(2026, 10, 23)),
    ("today", THURSDAY, THURSDAY),
    ("end of day", THURSDAY, THURSDAY),
    ("tomorrow", THURSDAY, FRIDAY),
    ("in two weeks", THURSDAY, date(2026, 10, 29)),
    ("Nov 5", THURSDAY, date(2026, 11, 5)),
    ("5th of November", THURSDAY, date(2026, 11, 5)),
    ("November 5, 2027", THURSDAY, date(2027, 11, 5)),
    # A month and day already past is next year's.
    ("Sep 3", THURSDAY, date(2027, 9, 3)),
    ("2026-11-01", THURSDAY, date(2026, 11, 1)),
])
def test_said_words_name_a_day(said: str, anchor: date, day: date) -> None:
    assert resolve_due(said, anchor) == day


@pytest.mark.parametrize("said", ["soon", "after the launch", "ASAP-ish", "Q4", "", None])
def test_words_that_name_no_day_stay_words(said: str | None) -> None:
    assert resolve_due(said, THURSDAY) is None


def test_stored_due_keeps_the_said_words_beside_the_date() -> None:
    assert stored_due("Friday next week", THURSDAY) == ("2026-10-23", "Friday next week")
    assert stored_due("after the launch", THURSDAY) == ("after the launch", "after the launch")
    assert stored_due("2026-10-20", THURSDAY) == ("2026-10-20", None)
    assert stored_due(None, THURSDAY) == (None, None)
    # No meeting day: the words stay words.
    assert stored_due("Wednesday", None) == ("Wednesday", "Wednesday")
