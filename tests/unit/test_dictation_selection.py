"""Unit tests for the pending dictation selection pin (HS-53-07)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from holdspeak import dictation_selection as ds


@pytest.fixture(autouse=True)
def _clear_pin():
    ds.clear_selected_record()
    yield
    ds.clear_selected_record()


def test_set_then_consume_returns_id_once() -> None:
    ds.set_selected_record(42)
    assert ds.consume_selected_record() == 42
    # one-shot: a second consume returns nothing
    assert ds.consume_selected_record() is None


def test_consume_empty_returns_none() -> None:
    assert ds.consume_selected_record() is None


def test_stale_pin_is_dropped_unused() -> None:
    t0 = datetime(2026, 6, 8, 12, 0, 0)
    ds.set_selected_record(7, now=t0)
    # Older than the window -> dropped, and cleared (not returned later either).
    assert ds.consume_selected_record(max_age_seconds=300, now=t0 + timedelta(seconds=301)) is None
    assert ds.consume_selected_record(now=t0 + timedelta(seconds=302)) is None


def test_fresh_pin_within_window_is_returned() -> None:
    t0 = datetime(2026, 6, 8, 12, 0, 0)
    ds.set_selected_record(9, now=t0)
    assert ds.consume_selected_record(max_age_seconds=300, now=t0 + timedelta(seconds=120)) == 9


def test_set_replaces_prior_pin() -> None:
    ds.set_selected_record(1)
    ds.set_selected_record(2)
    assert ds.consume_selected_record() == 2


def test_garbage_id_is_ignored() -> None:
    ds.set_selected_record("not-a-number")  # type: ignore[arg-type]
    assert ds.peek_selected_record() is None
    ds.set_selected_record(None)  # type: ignore[arg-type]
    assert ds.peek_selected_record() is None


def test_clear_drops_pending() -> None:
    ds.set_selected_record(5)
    ds.clear_selected_record()
    assert ds.peek_selected_record() is None
    assert ds.consume_selected_record() is None


def test_peek_does_not_consume() -> None:
    ds.set_selected_record(11)
    assert ds.peek_selected_record() == 11
    assert ds.peek_selected_record() == 11  # still there
    assert ds.consume_selected_record() == 11
