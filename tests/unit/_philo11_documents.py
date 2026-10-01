"""Real PHILO-11 document producers shared by focused and rig tests."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from holdspeak.db.decisions import backfill_decisions
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.people import production_people_store
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.people_service import PeopleService


OWNER = Principal(PrincipalKind.OWNER, "philo11-source-owner")
TRANSCRIPT_SENTINEL = "TRANSCRIPT-SENTINEL-DO-NOT-EXPORT"


def create_people_fixture(keystore_path: Path, principal: Principal = OWNER) -> PeopleService:
    """Create a real encrypted People sidecar using an explicit file key store.

    The environment variable is the production composition seam.  It keeps a
    subprocess hub on the same encrypted sidecar without touching the native
    login keychain.
    """
    os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = str(keystore_path)
    store = production_people_store()
    store.initialize()
    service = PeopleService(store)
    relationship = service.create_relationship(principal, {"display_name": "Avery"})
    request = service.create_request(principal, relationship["id"], {"body": "Review the rollout plan"})
    service.accept_request(principal, request["id"])
    return service


def mint_documents(
    db: Any,
    principal: Principal = OWNER,
    *,
    now: datetime | None = None,
    people_keystore_path: Path | None = None,
) -> dict[str, str]:
    """Mint all eight source records through their real producers.

    The returned values are document references.  This helper only writes the
    durable source stores; it does not render, preview, prepare, or send.
    """
    # Project update: repository insert + service publish is the same producer
    # used by the Room update flow, with no model call.
    project_id = "philo11-project"
    db.projects.create_project(project_id=project_id, name="Philo 11")
    db.project_updates.insert_update(
        update_id="philo11-update",
        project_id=project_id,
        project_revision=1,
        body_md="# Published update\n\nThe source fixture is durable.\n",
    )
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService

    ProjectUpdateService(db, project_service=ProjectService(db)).publish_update(
        principal, "philo11-update"
    )

    # Desk decision: PrimitiveService is the real producer used by the desk.
    from holdspeak.services.primitive_service import PrimitiveService

    desk = PrimitiveService(db).create_decision(
        principal,
        decision_id="desk-philo11",
        title="Use stored source bytes",
        status="accepted",
        deciders=[principal.identity],
        context_markdown="The channel must read a stored record.",
        decision_markdown="Render from the durable source by id.",
        alternatives=[{"name": "Caller body", "reason": "It is not a stored source."}],
        consequences_markdown="Preview and Send have one source of truth.",
    )

    # Meeting and its intelligence are stored by the real meeting repository;
    # the decisions projection is then performed by the real DB projector.
    meeting = MeetingState(
        id="philo11-meeting",
        started_at=datetime(2026, 9, 29, 9, 0, 0),
        title="Source review",
        segments=[
            TranscriptSegment(
                text=TRANSCRIPT_SENTINEL,
                speaker="Avery",
                start_time=1.0,
                end_time=2.0,
            )
        ],
        intel=IntelSnapshot(
            timestamp=1.0,
            topics=["Document sources"],
            summary="The channel reads durable records.",
            action_items=[{
                "id": "philo11-action",
                "task": "Check the frozen bytes",
                "owner": None,
                "due": None,
                "status": "pending",
                "review_state": "accepted",
                "source_timestamp": None,
                "created_at": "2026-09-29T09:00:00",
            }],
        ),
    )
    db.meetings.save_meeting(meeting)

    # Monday brief: its generator is the real producer.  The meeting above is
    # inside this window, so it contributes a stored item.  Same-day generate
    # returns one durable id; the source renderer later reads it by id.
    brief = MondayBriefService(db).generate(principal, now=now or datetime(2026, 9, 29, 10, 0, 0))
    for section_items in brief.sections.values():
        if section_items:
            MondayBriefService(db).shelve(principal, section_items[0].id, "acknowledged")
            break

    if people_keystore_path is not None:
        create_people_fixture(people_keystore_path, principal)

    db.plugins.record_artifact(
        artifact_id="philo11-decisions",
        meeting_id=meeting.id,
        artifact_type="decisions",
        title="Meeting decisions",
        structured_json={"decisions": [{"decision": "Use one document registry", "rationale": "One source of truth."}]},
        plugin_id="philo11-fixture",
    )
    with db._connection() as conn:
        backfill_decisions(conn)
    lifecycle = db.decisions.list(meeting_id=meeting.id)[0]
    records = DecisionRecordService(db)
    record = records.create_from_meeting(principal, lifecycle.id)
    records.update_record(
        principal,
        record["id"],
        {"owner": "Avery", "review_date": "2026-10-10"},
    )
    successor = records.create(
        principal,
        decision_text="Use one document registry (successor)",
        rationale="The successor keeps the same source identity while refining the record.",
        owner="Avery",
        review_date="2026-11-10",
        source_type="meeting",
        source_id=f"{lifecycle.id}:successor",
    )
    records.supersede(
        principal,
        record["id"],
        successor["id"],
        reason="The source record was refined after review.",
    )

    return {
        "project_update": f"project_update:{'philo11-update'}",
        "monday_brief": f"monday_brief:{brief.id}",
        "desk_decision": f"desk_decision:{desk['id']}",
        "meeting_decision": f"meeting_decision:{lifecycle.id}",
        "decision_record": f"decision_record:{record['id']}",
        "meeting_summary": f"meeting_summary:{meeting.id}",
        "meeting_digest": f"meeting_digest:{meeting.id}",
        "meeting_followup": f"meeting_followup:{meeting.id}",
    }
