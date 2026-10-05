from __future__ import annotations

import pytest

from holdspeak.db.relationships import qualified_ref
from holdspeak.workrooms import WorkroomContext


def test_workroom_context_round_trips_only_identity_and_orientation() -> None:
    context = WorkroomContext.desk(
        action="edit-workflow",
        subject_ref="workflow:wf-7",
        draft_ref="note:draft-2",
        run_ref="artifact:run-3",
    )

    assert WorkroomContext.from_mapping(context.to_dict()) == context
    assert context.return_ref == "workflow:wf-7"


def test_workroom_context_is_forward_tolerant_but_refuses_content() -> None:
    context = WorkroomContext.from_mapping({
        "version": 2,
        "origin": "desk",
        "subject_ref": "meeting:m1",
        "action": "review-meeting",
        "return_to": "desk",
        "future_hint": {"ignored": True},
    })
    assert context.version == 2

    with pytest.raises(ValueError, match="authored content"):
        WorkroomContext.from_mapping({
            "version": 1,
            "origin": "desk",
            "action": "dictate",
            "return_to": "desk",
            "transcript": "private words",
        })


@pytest.mark.parametrize("return_to", ["https://example.com", "/settings", ""])
def test_workroom_context_has_no_open_return_destination(return_to: str) -> None:
    with pytest.raises(ValueError, match="return destination"):
        WorkroomContext.from_mapping({
            "version": 1,
            "origin": "desk",
            "action": "configure-integration",
            "subject_ref": "integration:slack",
            "return_to": return_to,
        })


def test_integration_is_a_qualified_desk_subject() -> None:
    assert qualified_ref("integration:slack") == "integration:slack"
