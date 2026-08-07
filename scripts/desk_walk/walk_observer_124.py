"""HS-124-10 observer layer walk.

Run with:
    uv run python scripts/desk_walk/walk_observer_124.py

This walk uses a new temporary SQLite database and calls observed services
without a hub, proving that the observer persists service-layer events.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from holdspeak.db.core import Database
from holdspeak.services.desk_service import DeskService
from holdspeak.services.event_query_service import EventQueryService
from holdspeak.services.observer import _correlation_id
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.profile_service import ProfileService
from holdspeak.services.settings_service import SettingsService
from holdspeak.services.sqlite_observer import SQLiteObserver


Check = Callable[[], None]


def _check(label: str, action: Check, failures: list[str]) -> None:
    """Run one walk assertion while allowing the summary to report failures."""
    try:
        action()
    except Exception as exc:
        print(f"FAIL {label}: {type(exc).__name__}: {exc}")
        failures.append(label)
    else:
        print(f"PASS {label}")


def main() -> None:
    failures: list[str] = []
    steps_total = 7

    with tempfile.TemporaryDirectory(prefix="holdspeak-observer-124-") as tempdir:
        db = Database(Path(tempdir) / "walk.db")
        observer = SQLiteObserver(db._connection)
        principal = SimpleNamespace(
            kind=SimpleNamespace(value="walk"),
            identity="observer-124-walk",
        )
        primitives = PrimitiveService(db, observer=observer)
        profiles = ProfileService(db, observer=observer)
        settings = SettingsService(db, observer=observer)
        desk = DeskService(db, observer=observer)
        events = EventQueryService(db)

        _check(
            "PrimitiveService lists notes",
            lambda: assert_empty_notes(primitives.list_notes(principal)),
            failures,
        )
        _check(
            "PrimitiveService creates note",
            lambda: assert_note(primitives.create_note(principal, title="Walk note")),
            failures,
        )
        _check(
            "ProfileService lists profiles",
            lambda: assert_profiles(profiles.list_profiles(principal)),
            failures,
        )
        _check(
            "SettingsService gets settings",
            lambda: assert_settings(settings.get_settings(principal)),
            failures,
        )
        _check("DeskService health", lambda: assert_health(desk.health()), failures)

        recorded_events = events.recent(principal)
        stats = events.stats(principal)

        def assert_event_quality() -> None:
            assert len(recorded_events) >= 4, f"expected >= 4 events, got {len(recorded_events)}"
            assert all(event["duration_ms"] > 0 for event in recorded_events)
            assert all(event["service"] and event["method"] for event in recorded_events)
            distinct_services = {event["service"] for event in recorded_events}
            assert len(distinct_services) >= 3, f"expected >= 3 services, got {len(distinct_services)}"
            assert stats["total_events"] == len(recorded_events)
            assert len(stats["by_service"]) >= 3

        _check("Observer records complete service events", assert_event_quality, failures)

        correlation_id = "observer-124-correlated-pair"
        token = _correlation_id.set(correlation_id)
        try:
            primitives.list_notes(principal)
            profiles.list_profiles(principal)
        finally:
            _correlation_id.reset(token)
        correlated_events = events.by_correlation(principal, correlation_id)

        def assert_correlated_pair() -> None:
            assert len(correlated_events) == 2, (
                f"expected exactly 2 correlated events, got {len(correlated_events)}"
            )
            assert {event["service"] for event in correlated_events} == {
                "PrimitiveService",
                "ProfileService",
            }
            assert {event["method"] for event in correlated_events} == {
                "list_notes",
                "list_profiles",
            }

        _check("Correlation query returns the correlated pair", assert_correlated_pair, failures)

        summary = {
            "walk": "observer_124",
            "steps_passed": steps_total - len(failures),
            "steps_total": steps_total,
            "events_recorded": len(recorded_events),
            "distinct_services": len({event["service"] for event in recorded_events}),
        }

    print(json.dumps(summary))
    if failures:
        raise SystemExit(1)


def assert_empty_notes(notes: list[dict[str, object]]) -> None:
    assert notes == []


def assert_note(note: dict[str, object]) -> None:
    assert note["title"] == "Walk note"


def assert_profiles(result: dict[str, object]) -> None:
    assert "profiles" in result


def assert_settings(result: dict[str, object]) -> None:
    assert isinstance(result, dict)


def assert_health(result: dict[str, str]) -> None:
    assert result == {"status": "ok"}


if __name__ == "__main__":
    main()
