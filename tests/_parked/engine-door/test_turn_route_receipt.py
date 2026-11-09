# PARKED 2026-11-09 (door/thought-dictation-meeting): the routed Thought projection (_routed_projection) is gone; the Thought projection names the engine the door ran.
# Moved from tests/unit/test_turn_route_receipt.py; its helpers are still there.

from tests.unit.test_turn_route_receipt import *  # noqa: F401,F403


def test_the_ask_projection_names_the_leg_that_answered(db) -> None:
    route = {"entries": [{"ordinal": 1, "profile_id": "p1", "deployment_revision_id": "lan", "boundary": "private_network"}]}
    result = AskService._routed_projection(
        SimpleNamespace(_db=db), {"output": "answer"}, {"lens": "Ask", "context_ids": [], "context_titles": []},
        None, route, route_leg_ordinal=1,
    )
    assert result["egress"] == {"scope": "private_network", "host": "192.168.1.43"}
    assert result["actual_placement"]["boundary"] == "private_network"
