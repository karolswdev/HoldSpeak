"""Real PHILO-12 artifact producers shared by focused and rig tests."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.synthesis import synthesize_and_persist
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import AskService
from holdspeak.services.support import _persist_run_artifact


OWNER = Principal(PrincipalKind.OWNER, "philo12-artifact-owner")


def mint_meeting_synthesis(db: Any) -> str:
    """Run the stored plugin-run synthesis producer and return its artifact ref."""
    meeting_id = "philo12-synthesis-meeting"
    db.meetings.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=datetime(2026, 9, 30, 9, 0, 0),
            title="Philo 12 synthesis",
        )
    )
    db.plugins.record_plugin_run(
        meeting_id=meeting_id,
        window_id="philo12-synthesis-window",
        plugin_id="requirements_extractor",
        plugin_version="1",
        status="success",
        idempotency_key="philo12-synthesis-run",
        output={
            "summary": "The synthesis producer stored this body.",
            "confidence_hint": 1.0,
            "active_intents": ["requirements"],
        },
    )
    drafts, _ = synthesize_and_persist(db, meeting_id)
    assert len(drafts) == 1
    return f"artifact:{drafts[0].artifact_id}"


def mint_run_output(db: Any) -> str:
    """Use the production run-output persistence producer without inference."""
    artifact_id = _persist_run_artifact(
        db=db,
        kind="recipe",
        name="Philo 12 run",
        user_input="source fixture",
        output="The real run output body.",
        sources=[{"source_type": "recipe", "source_ref": "philo12-recipe"}],
    )
    assert artifact_id
    return f"artifact:{artifact_id}"


def mint_ask_keep(db: Any, *, body: str = "The real Ask Keep body.") -> str:
    """Use Ask Keep's real artifact writer; ``keep`` does not run inference."""
    result = AskService(db, hub_model=lambda: "").keep(
        OWNER,
        body,
        [],
        lens="Philo 12",
    )
    return f"artifact:{result['artifact_id']}"
