"""PARKED: compatibility doubles for the retired Concierge summary resolver.

Real assignment-owner states are covered by test_summary_assignment_door.py.
"""
from typing import Any
from unittest.mock import MagicMock
from holdspeak.services.errors import NotFound
from tests.unit.test_concierge_service import _head_db

def test_summary_projection_says_off_after_the_assignment_was_cleared() -> None:
    from holdspeak.services.concierge_service import summary_assignment_projection

    svc = MagicMock()
    svc.get_assignment.side_effect = NotFound("inference assignment", "x")

    projection = summary_assignment_projection(
        assignment_service=svc, principal=MagicMock(), db=_head_db(4, 1)
    )

    assert projection["status"] == "off"
    assert projection["assignmentRevision"] == 4
    assert projection["profileId"] is None


def test_summary_projection_stays_unassigned_when_nothing_was_ever_written() -> None:
    from holdspeak.services.concierge_service import summary_assignment_projection

    svc = MagicMock()
    svc.get_assignment.side_effect = NotFound("inference assignment", "x")
    db = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.fetchone.return_value = None
    db._connection = MagicMock(return_value=conn)

    projection = summary_assignment_projection(
        assignment_service=svc, principal=MagicMock(), db=db
    )

    assert projection["status"] == "unassigned"
    assert projection["assignmentRevision"] == 0


