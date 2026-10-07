"""PHILO-14 A1 (#939, Astra's P2): one Project, one number.

The needs-you answer carries each Room's own NEEDS YOU count (``roomCounts``),
the number the Room's head says ("N open here"), so the screen's drawer and
the Dock show the Room's number, not the desk rule's per-Project share (which
leaves out a Room's issues, its action items and what the owner waits on)."""
from __future__ import annotations

from holdspeak.services.needs_you_aggregate import LastKnownStore, build_aggregate


def _room(items):
    return {"needsYou": {"state": "ok", "items": items, "count": len(items)}, "observed_at": "2026-10-07T08:00:00"}


def test_room_counts_are_each_rooms_own_count() -> None:
    rooms = {
        "p1": _room([
            {"title": "Fix the flaky check", "kind": "issue", "source": "github"},
            {"title": "Write the runbook", "kind": "action_item"},
            {"title": "Sam: send the status", "kind": "commitment", "commitment_id": "c1"},
        ]),
        "p2": _room([]),
    }
    answer = build_aggregate(
        list_projects=lambda *_a, **_k: [{"id": "p1", "name": "One"}, {"id": "p2", "name": "Two"}],
        room=lambda _principal, pid: rooms[pid],
        principal=None,
        last_known=LastKnownStore(),
    )
    # The Room counts all three; the desk rule keeps only the commitment.
    assert answer["roomCounts"] == {"p1": 3, "p2": 0}
    assert [row["projectId"] for row in answer["items"]] == ["p1"]


def test_a_room_that_could_not_be_read_has_no_count() -> None:
    answer = build_aggregate(
        list_projects=lambda *_a, **_k: [{"id": "p1", "name": "One"}],
        room=lambda _principal, _pid: {"needsYou": {"state": "degraded", "error_code": "x"}},
        principal=None,
        last_known=LastKnownStore(),
    )
    assert answer["roomCounts"] == {}
