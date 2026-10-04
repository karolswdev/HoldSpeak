"""The time phrase parser (MEMORY-DESIGN.md §3.2, the Time retriever).

Every case has a fixed ``now`` in a fixed zone (America/Denver), so the
ranges are exact and the DST changes of that zone are real.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from holdspeak.memory.timeparse import instant, parse_time_phrase, read_time_phrase

DENVER = ZoneInfo("America/Denver")
SUNDAY = datetime(2026, 10, 4, 15, 30, tzinfo=DENVER)    # a Sunday
MONDAY = datetime(2026, 9, 28, 10, 0, tzinfo=DENVER)     # a Monday


def _range(question: str, now: datetime) -> tuple[str, str]:
    found = parse_time_phrase(question, now, DENVER)
    assert found is not None, question
    return found.time_from, found.time_to


# ── the ten phrases of the brief, asked on a Sunday ──────────────────────

@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("what did I send last week", ("2026-09-21T00:00:00-06:00", "2026-09-28T00:00:00-06:00")),
        ("what did we decide in September", ("2026-09-01T00:00:00-06:00", "2026-10-01T00:00:00-06:00")),
        ("since Monday", ("2026-09-28T00:00:00-06:00", "2026-10-04T15:30:00-06:00")),
        ("yesterday", ("2026-10-03T00:00:00-06:00", "2026-10-04T00:00:00-06:00")),
        ("this morning", ("2026-10-04T00:00:00-06:00", "2026-10-04T12:00:00-06:00")),
        ("last month", ("2026-09-01T00:00:00-06:00", "2026-10-01T00:00:00-06:00")),
        ("two weeks ago", ("2026-09-14T00:00:00-06:00", "2026-09-21T00:00:00-06:00")),
        ("on Tuesday", ("2026-09-29T00:00:00-06:00", "2026-09-30T00:00:00-06:00")),
        ("in Q3", ("2026-07-01T00:00:00-06:00", "2026-10-01T00:00:00-06:00")),
        ("today", ("2026-10-04T00:00:00-06:00", "2026-10-05T00:00:00-06:00")),
    ],
)
def test_the_brief_phrases_on_a_sunday(question: str, expected: tuple[str, str]) -> None:
    assert _range(question, SUNDAY) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("the day before yesterday", ("2026-10-02T00:00:00-06:00", "2026-10-03T00:00:00-06:00")),
        ("yesterday afternoon", ("2026-10-03T12:00:00-06:00", "2026-10-03T18:00:00-06:00")),
        ("last night", ("2026-10-03T18:00:00-06:00", "2026-10-04T06:00:00-06:00")),
        ("this week", ("2026-09-28T00:00:00-06:00", "2026-10-05T00:00:00-06:00")),
        ("last weekend", ("2026-09-26T00:00:00-06:00", "2026-09-28T00:00:00-06:00")),
        ("the past week", ("2026-09-27T15:30:00-06:00", "2026-10-04T15:30:00-06:00")),
        ("in the last 3 days", ("2026-10-01T15:30:00-06:00", "2026-10-04T15:30:00-06:00")),
        ("a few days ago", ("2026-10-01T00:00:00-06:00", "2026-10-02T00:00:00-06:00")),
        ("three months ago", ("2026-07-01T00:00:00-06:00", "2026-08-01T00:00:00-06:00")),
        ("Friday", ("2026-10-02T00:00:00-06:00", "2026-10-03T00:00:00-06:00")),
        ("on Sep 15", ("2026-09-15T00:00:00-06:00", "2026-09-16T00:00:00-06:00")),
        ("the 3rd of August", ("2026-08-03T00:00:00-06:00", "2026-08-04T00:00:00-06:00")),
        ("on 2026-09-15", ("2026-09-15T00:00:00-06:00", "2026-09-16T00:00:00-06:00")),
        ("since September", ("2026-09-01T00:00:00-06:00", "2026-10-04T15:30:00-06:00")),
        ("May 2025", ("2025-05-01T00:00:00-06:00", "2025-06-01T00:00:00-06:00")),
        ("in Q4 2025", ("2025-10-01T00:00:00-06:00", "2026-01-01T00:00:00-07:00")),
        ("in 2025", ("2025-01-01T00:00:00-07:00", "2026-01-01T00:00:00-07:00")),
    ],
)
def test_the_other_patterns(question: str, expected: tuple[str, str]) -> None:
    assert _range(question, SUNDAY) == expected


def test_a_bare_month_is_the_most_recent_past_one() -> None:
    # In October, "in November" is last November; "in October" is this one.
    assert _range("in November", SUNDAY)[0] == "2025-11-01T00:00:00-06:00"
    assert _range("in October", SUNDAY) == ("2026-10-01T00:00:00-06:00", "2026-11-01T00:00:00-06:00")
    # A day that has not come yet this year is last year's.
    assert _range("on December 24", SUNDAY)[0] == "2025-12-24T00:00:00-07:00"


# ── a Monday: the week starts today ──────────────────────────────────────

def test_on_a_monday() -> None:
    assert _range("last week", MONDAY) == ("2026-09-21T00:00:00-06:00", "2026-09-28T00:00:00-06:00")
    assert _range("this week", MONDAY) == ("2026-09-28T00:00:00-06:00", "2026-10-05T00:00:00-06:00")
    assert _range("yesterday", MONDAY) == ("2026-09-27T00:00:00-06:00", "2026-09-28T00:00:00-06:00")
    # "on Monday" asked on a Monday is last week's Monday: today has its own word.
    assert _range("on Monday", MONDAY) == ("2026-09-21T00:00:00-06:00", "2026-09-22T00:00:00-06:00")
    assert _range("since Monday", MONDAY) == ("2026-09-21T00:00:00-06:00", "2026-09-28T10:00:00-06:00")


# ── month and year boundaries ────────────────────────────────────────────

def test_a_month_boundary() -> None:
    now = datetime(2026, 10, 1, 9, 0, tzinfo=DENVER)
    assert _range("yesterday", now) == ("2026-09-30T00:00:00-06:00", "2026-10-01T00:00:00-06:00")
    assert _range("last month", now) == ("2026-09-01T00:00:00-06:00", "2026-10-01T00:00:00-06:00")
    assert _range("this month", now) == ("2026-10-01T00:00:00-06:00", "2026-11-01T00:00:00-06:00")


def test_a_year_boundary() -> None:
    now = datetime(2026, 1, 2, 9, 0, tzinfo=DENVER)  # a Friday
    assert _range("last month", now) == ("2025-12-01T00:00:00-07:00", "2026-01-01T00:00:00-07:00")
    assert _range("last year", now) == ("2025-01-01T00:00:00-07:00", "2026-01-01T00:00:00-07:00")
    assert _range("in Q4", now) == ("2025-10-01T00:00:00-06:00", "2026-01-01T00:00:00-07:00")
    assert _range("in December", now) == ("2025-12-01T00:00:00-07:00", "2026-01-01T00:00:00-07:00")
    assert _range("two weeks ago", now) == ("2025-12-15T00:00:00-07:00", "2025-12-22T00:00:00-07:00")
    assert _range("last week", now) == ("2025-12-22T00:00:00-07:00", "2025-12-29T00:00:00-07:00")
    assert _range("Dec 31", now) == ("2025-12-31T00:00:00-07:00", "2026-01-01T00:00:00-07:00")


# ── the DST changes of the owner's zone ──────────────────────────────────

def test_the_autumn_dst_change() -> None:
    # Denver leaves DST at 02:00 on Sunday 2026-11-01: that day has 25 hours.
    now = datetime(2026, 11, 4, 12, 0, tzinfo=DENVER)  # a Wednesday, -07:00
    assert _range("last week", now) == ("2026-10-26T00:00:00-06:00", "2026-11-02T00:00:00-07:00")
    assert _range("on Sunday", now) == ("2026-11-01T00:00:00-06:00", "2026-11-02T00:00:00-07:00")
    start, end = (datetime.fromisoformat(value) for value in _range("on Sunday", now))
    assert (end - start).total_seconds() == 25 * 3600


def test_the_spring_dst_change() -> None:
    # Denver enters DST at 02:00 on Sunday 2026-03-08: that day has 23 hours.
    now = datetime(2026, 3, 9, 8, 0, tzinfo=DENVER)
    assert _range("yesterday", now) == ("2026-03-08T00:00:00-07:00", "2026-03-09T00:00:00-06:00")
    start, end = (datetime.fromisoformat(value) for value in _range("yesterday", now))
    assert (end - start).total_seconds() == 23 * 3600


def test_now_in_another_zone_is_read_in_the_owner_zone() -> None:
    # 03:00 UTC on Monday is still Sunday evening in Denver.
    now = datetime(2026, 9, 28, 3, 0, tzinfo=timezone.utc)
    assert _range("today", now) == ("2026-09-27T00:00:00-06:00", "2026-09-28T00:00:00-06:00")


# ── the phrase leaves the question ───────────────────────────────────────

def test_the_phrase_leaves_the_question() -> None:
    found, rest = read_time_phrase("what did I send Dana last week?", SUNDAY, DENVER)
    assert found.phrase == "last week"
    assert rest == "what did I send Dana ?"
    found, rest = read_time_phrase("what did we decide since last week", SUNDAY, DENVER)
    assert found.phrase == "since last week"
    assert found.time_from == "2026-09-21T00:00:00-06:00"
    assert rest == "what did we decide"


@pytest.mark.parametrize(
    "question",
    [
        "plain question about the gateway",
        "this may take a while",
        "notes from Jan",
        "the march to production",
        "weekly review",
        "Q35 widget",
        "",
    ],
)
def test_no_phrase(question: str) -> None:
    assert parse_time_phrase(question, SUNDAY, DENVER) is None


# ── the stored time shapes ───────────────────────────────────────────────

def test_instant_reads_every_stored_shape() -> None:
    # A SQLite stamp is UTC.
    assert instant("2026-09-22 18:00:00", DENVER) == datetime(2026, 9, 22, 18, 0, tzinfo=timezone.utc)
    # An ISO time with an offset is exact.
    assert instant("2026-09-22T18:00:00+00:00", DENVER) == datetime(2026, 9, 22, 18, 0, tzinfo=timezone.utc)
    assert instant("2026-09-22T18:00:00Z", DENVER) == datetime(2026, 9, 22, 18, 0, tzinfo=timezone.utc)
    # A bare ISO time is the hub's local wall time.
    assert instant("2026-09-22T12:00:00", DENVER) == datetime(2026, 9, 22, 18, 0, tzinfo=timezone.utc)
    assert instant("2026-09-22", DENVER) == datetime(2026, 9, 22, 6, 0, tzinfo=timezone.utc)
    assert instant("", DENVER) is None
    assert instant("not a time", DENVER) is None
