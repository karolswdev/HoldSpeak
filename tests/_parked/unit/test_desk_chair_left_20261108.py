"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/unit/test_desk_chair.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


def test_unlink_over_the_route_drops_the_room_and_keeps_the_arm(db: Any, ics: str) -> None:
    """replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_unlink_room (hub half)"""
    _seed_week_strip(db)
    resp = _client().delete("/api/calendar/events/ev-standup/link")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"unlinked": 1, "event_id": "ev-standup", "durable": True}

    with db._connection() as conn:
        links = conn.execute(
            "SELECT COUNT(*) FROM calendar_event_projects WHERE calendar_event_id='ev-standup'"
        ).fetchone()[0]
        receipts = conn.execute(
            "SELECT args_summary FROM pipeline_events "
            "WHERE service='CalendarEventLink' AND method='unlink'"
        ).fetchall()
    assert links == 0
    assert len(receipts) == 1 and json.loads(receipts[0]["args_summary"])["event_id"] == "ev-standup"

    standup = _calendar_rows(_projection(db, ics))["ev-standup"]
    assert "project_name" not in standup
    assert standup["armed"]["recording_id"] == "rec-standup"
