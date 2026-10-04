#!/usr/bin/env python3
"""Mint the PHILO-13 A2 ``needs you`` oracle week.

The fixture is deliberately a producer, not a projection double.  Meetings
and their action items go through :class:`MeetingState` and
``save_meeting``; the A2 Room row goes through the real proposal bridge; the
muted project goes through heartbeat settings.  ``export`` reads the same
services that the Desk reads and then marks A1 done through the real HTTP
action-item route.

Usage (always with an isolated ``HOME``)::

    HOME=/tmp/philo13-home uv run python scripts/philo13_needs_you_fixture.py \
        seed --db /tmp/philo13-home/.local/share/holdspeak/holdspeak.db
    HOME=/tmp/philo13-home uv run python scripts/philo13_needs_you_fixture.py \
        export --db /tmp/philo13-home/.local/share/holdspeak/holdspeak.db

``seed`` creates one fresh oracle database.  ``export`` expects that database
and records before/after inputs around the real A1 route mutation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import pwd
from typing import Any, Iterator
import uuid as _stdlib_uuid


ORACLE_SCHEMA = "philo13-needs-you-oracle@1"
OWNER_IDENTITY = "Karol"

PROJECT_ID = "philo13-a2-project"
MUTED_PROJECT_ID = "philo13-a2-muted-project"
MAIN_MEETING_ID = "philo13-a2-meeting"
MUTED_MEETING_ID = "philo13-a2-muted-meeting"
FAILED_MEETING_ID = "philo13-a2-failed-meeting"
STORED_MEETING_ID = "philo13-a2-stored-meeting"

A1_ID = "philo13-a2-A1"
A2_ID = "philo13-a2-A2"
A3_ID = "philo13-a2-A3"
A4_ID = "philo13-a2-A4"
M1_ID = "philo13-a2-M1"
D1_ID = "philo13-a2-D1"
DEDUP_MEETING_ID = "philo13-a2-dedup-meeting"
DEDUP_ACTION_ID = "philo13-a2-dedup-A2"

A1_TASK = "A1 close the overdue release note"
A2_TASK = "A2 confirm the room commitment"
A3_TASK = "A3 wait for Priya's review"
A4_TASK = "A4 assign the owner"
A1_ROOM_TASK = "A1 room release milestone"
M1_TASK = "M1 muted project attention"
D1_TASK = "D1 completed action"

PROPOSAL_ARTIFACT_ID = "philo13-a2-action-artifact"

_ORACLE_MEETING_IDS = frozenset({
    MAIN_MEETING_ID,
    MUTED_MEETING_ID,
    FAILED_MEETING_ID,
    STORED_MEETING_ID,
})


def _expected_refs() -> list[str]:
    """The member refs the real aggregate is required to return.

    The Room producer's ref is its stable title, while Door and meeting refs
    are their persisted IDs.  Keep this contract explicit: an alias such as
    ``A2Room`` would hide a changed producer ref.
    """
    return [A1_ID, A2_TASK, A3_ID, A4_ID, "blocker:engines", FAILED_MEETING_ID]


def _owner_home() -> Path:
    """Return the real account home even when HOME is temporarily isolated."""
    return Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()


def validate_isolated_db(db_path: Path, home: Path | None = None) -> tuple[Path, Path]:
    """Validate the explicit database target before any product opens it.

    A fixture must be below the caller's isolated HOME and must never point at
    the account's real home.  The check uses ``pwd`` because ``Path.home()``
    follows the caller's HOME and therefore cannot identify the owner's desk
    after a test has isolated it.
    """
    target = Path(db_path).expanduser()
    if not target.is_absolute():
        raise ValueError("--db must be an absolute path")
    home_value = str(home) if home is not None else os.environ.get("HOME", "").strip()
    if not home_value:
        raise ValueError("HOME must name an isolated fixture directory")
    isolated_home = Path(home_value).expanduser()
    if not isolated_home.is_absolute():
        raise ValueError("fixture HOME must be an absolute path")
    if isolated_home.is_symlink():
        raise ValueError("fixture HOME must not be a symlink")
    isolated_home = isolated_home.resolve()
    target = target.resolve()
    real_home = _owner_home()
    if isolated_home == real_home or isolated_home.is_relative_to(real_home):
        raise ValueError("fixture HOME must be outside the owner's real HOME")
    if target == real_home or target.is_relative_to(real_home):
        raise ValueError("--db points into the owner's real HOME")
    if not target.is_relative_to(isolated_home):
        raise ValueError("--db must be below the isolated HOME")
    return target, isolated_home


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(v) for v in value]
    return value


class _FixedEntropy:
    """A local ``uuid`` module substitute used only by this fixture.

    The producer code still mints the UUID-backed chain and runs all of its
    validation.  Replacing the imported module namespace keeps the output
    stable without patching ``uuid.uuid4`` globally.
    """

    def __init__(self) -> None:
        # Producer IDs use ``uuid4().hex[:16]``.  Put the counter in the
        # leading half of the UUID so those producer IDs remain distinct.
        self._values = iter(
            _stdlib_uuid.UUID(int=(n << 112)) for n in range(1, 16)
        )

    def uuid4(self) -> _stdlib_uuid.UUID:
        return next(self._values)


@contextmanager
def _fixed_producer_entropy() -> Iterator[None]:
    import holdspeak.db.proposals as proposal_db
    import holdspeak.services.proposal_bridge_service as proposal_bridge

    old_db_uuid = proposal_db.uuid
    old_bridge_uuid = proposal_bridge.uuid
    fixed = _FixedEntropy()
    proposal_db.uuid = fixed  # type: ignore[assignment]
    proposal_bridge.uuid = fixed  # type: ignore[assignment]
    try:
        yield
    finally:
        proposal_db.uuid = old_db_uuid  # type: ignore[assignment]
        proposal_bridge.uuid = old_bridge_uuid  # type: ignore[assignment]


def _meeting(
    meeting_id: str,
    title: str,
    started_at: datetime,
    *,
    intel_status: str,
    summary: str = "",
    action_items: list[dict[str, Any]] | None = None,
    segments: list[tuple[str, float]] | None = None,
) -> Any:
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    rows = action_items or []
    transcript = [
        TranscriptSegment(text=text, speaker=OWNER_IDENTITY, start_time=stamp, end_time=stamp + 1.0)
        for text, stamp in (segments or [])
    ]
    return MeetingState(
        id=meeting_id,
        started_at=started_at,
        ended_at=started_at + timedelta(minutes=30),
        title=title,
        segments=transcript,
        intel=IntelSnapshot(timestamp=started_at.timestamp(), summary=summary, action_items=rows),
        intel_status=intel_status,
        intel_status_detail=("Fixture summary failure" if intel_status == "failed" else None),
        capture_status="finalized",
    )


def _action(
    item_id: str,
    task: str,
    *,
    owner: str | None,
    due: str | None,
    status: str = "pending",
    created_at: str,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": due,
        "status": status,
        "review_state": "accepted",
        "source_timestamp": None,
        "created_at": created_at,
    }


@contextmanager
def _route_client(db: Any, now: datetime | None = None) -> Iterator[Any]:
    """Build the real HTTP read/write routes over this isolated Database."""
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    import holdspeak.db as db_package
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.door import build_door_router
    from holdspeak.web.routes.inference_assignments import build_inference_assignments_router
    from holdspeak.web.routes.meetings import build_meetings_router
    from holdspeak.web.routes.projects import build_projects_router

    owner = Principal(PrincipalKind.OWNER, OWNER_IDENTITY)
    project_service = ProjectService(db)
    door_service = DoorService(
        FollowThroughService(db), RefinementThoughtService(db),
        db.scheduled_recordings, db.calendar_events, db=db,
        clock=(lambda: now) if now is not None else None,
    )
    assignment_service = InferenceAssignmentService(db)
    ctx = WebContext(
        get_state=lambda: {}, project_service=project_service,
        door_service=door_service, inference_assignment_service=assignment_service,
        meeting_service=MeetingService(db),
    )
    app = FastAPI()

    @app.middleware("http")
    async def _owner(request: Request, call_next: Any) -> Any:
        request.state.principal = owner
        return await call_next(request)

    app.include_router(build_projects_router(ctx))
    app.include_router(build_door_router(ctx))
    app.include_router(build_inference_assignments_router(ctx))
    app.include_router(build_meetings_router(ctx))

    # The needs-you route's shared last-known store asks the package-level
    # database accessor.  Bind that accessor only for this isolated client;
    # the route and its operation still execute their real producers.
    old_get_database = db_package.get_database
    db_package.get_database = lambda: db  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            yield client
    finally:
        db_package.get_database = old_get_database  # type: ignore[assignment]


@contextmanager
def _fixed_project_entropy() -> Iterator[None]:
    """Stabilize IDs for the real project route producers only."""
    import holdspeak.project_contracts as project_contracts
    import holdspeak.services.project_service as project_service

    old_contract_uuid = project_contracts.uuid
    old_service_uuid = project_service.uuid
    fixed = _FixedEntropy()
    project_contracts.uuid = fixed  # type: ignore[assignment]
    project_service.uuid = fixed  # type: ignore[assignment]
    try:
        yield
    finally:
        project_contracts.uuid = old_contract_uuid  # type: ignore[assignment]
        project_service.uuid = old_service_uuid  # type: ignore[assignment]


def _create_projects_and_links(db: Any, *, m1_due: str, a1_room_due: str) -> dict[str, str]:
    """Use the actual project create/link/item routes for fixture producers."""
    with _fixed_project_entropy(), _route_client(db) as client:
        created = []
        for name in ("A2 oracle room", "M1 muted room"):
            response = client.post("/api/projects", json={"name": name})
            if response.status_code != 200 or not response.json().get("success"):
                raise RuntimeError(f"real project create route failed: {response.status_code} {response.text}")
            created.append(str(response.json()["project"]["id"]))
        project_id, muted_project_id = created
        for target, meeting_id in (
            (project_id, MAIN_MEETING_ID), (muted_project_id, MUTED_MEETING_ID),
        ):
            response = client.post(f"/api/projects/{target}/meetings/{meeting_id}", json={})
            if response.status_code != 200 or not response.json().get("success"):
                raise RuntimeError(f"real project link route failed: {response.status_code} {response.text}")
        response = client.post(
            f"/api/projects/{muted_project_id}/items",
            json={
                "item_type": "milestone", "title": M1_TASK,
                "lifecycle": "planned", "severity": "high", "due_at": m1_due,
            },
        )
        if response.status_code != 200 or not response.json().get("success"):
            raise RuntimeError(f"real project item route failed: {response.status_code} {response.text}")
        m1_id = str(response.json()["item"]["id"])
        response = client.post(
            f"/api/projects/{project_id}/items",
            json={
                "item_type": "milestone", "title": A1_ROOM_TASK,
                "lifecycle": "planned", "severity": "high", "due_at": a1_room_due,
            },
        )
        if response.status_code != 200 or not response.json().get("success"):
            raise RuntimeError(f"real Room milestone producer failed: {response.status_code} {response.text}")
        a1_room_item_id = str(response.json()["item"]["id"])
    return {
        "project_id": project_id,
        "muted_project_id": muted_project_id,
        "m1_id": m1_id,
        "a1_room_item_id": a1_room_item_id,
    }


def _seed_meetings_and_projects(db: Any, now: datetime) -> dict[str, Any]:
    today = now.date()
    yesterday = today - timedelta(days=1)
    main_started = now.replace(hour=9, minute=0, second=0, microsecond=0)
    muted_started = now.replace(hour=10, minute=0, second=0, microsecond=0)

    # A2 is produced below by the real proposal confirmation chain.  Keeping
    # a second MeetingState action here would make the merged Door/Room graph
    # show two candidates for one commitment.
    main_actions = [
        _action(A1_ID, A1_TASK, owner=OWNER_IDENTITY, due=yesterday.isoformat(), created_at=main_started.isoformat()),
        _action(A3_ID, A3_TASK, owner="Priya", due=(today + timedelta(days=7)).isoformat(), created_at=main_started.isoformat()),
        _action(A4_ID, A4_TASK, owner=None, due=None, created_at=main_started.isoformat()),
        _action(D1_ID, D1_TASK, owner=OWNER_IDENTITY, due=yesterday.isoformat(), status="done", created_at=main_started.isoformat()),
    ]
    main_segments = [(A1_TASK, 1.0), (A2_TASK, 2.0), (A3_TASK, 3.0), (A4_TASK, 4.0)]
    db.meetings.save_meeting(_meeting(
        MAIN_MEETING_ID, "A2 oracle actions", main_started,
        intel_status="completed", summary="Oracle action summary",
        action_items=main_actions, segments=main_segments,
    ))
    # M1 is created below by the real project item route.  It is an actual
    # Room attention producer, so its mute is observable even though Door
    # cards do not carry project ids.
    db.meetings.save_meeting(_meeting(
        MUTED_MEETING_ID, "M1 muted meeting", muted_started,
        intel_status="completed", summary="Muted project summary",
        action_items=[], segments=[],
    ))
    project_ids = _create_projects_and_links(
        db,
        m1_due=yesterday.isoformat(),
        a1_room_due=(today + timedelta(days=1)).isoformat(),
    )

    db.meetings.save_meeting(_meeting(
        FAILED_MEETING_ID, "F1 failed summary", now - timedelta(hours=2),
        intel_status="failed", summary="",
    ))
    db.meetings.save_meeting(_meeting(
        STORED_MEETING_ID, "S1 stored summary", now - timedelta(hours=3),
        intel_status="completed", summary="S1 stored summary",
    ))
    return {
        "today": today.isoformat(),
        "yesterday": yesterday.isoformat(),
        "main_started_at": main_started.isoformat(),
        **project_ids,
    }


def _clear_existing_assignments(db: Any) -> list[dict[str, Any]]:
    """Clear startup-adopted assignments through the owner HTTP route."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    owner = Principal(PrincipalKind.OWNER, OWNER_IDENTITY)
    service = InferenceAssignmentService(db)
    active = service.list_assignments(owner).get("assignments", [])
    if not active:
        return []
    cleared: list[dict[str, Any]] = []
    with _route_client(db) as client:
        for projection in active:
            scope = dict(projection["scope"])
            parsed = service._scope(scope)
            capability = scope.get("capability_id")
            if not capability:
                affected = service._affected_capabilities(parsed)
                if not affected:
                    raise RuntimeError(f"assignment has no clearable capability: {scope}")
                capability = affected[0].id
            body = {
                "command_id": f"philo13-clear-{projection['id']}",
                "expected_revision": int(projection["revision"]),
                "scope": scope,
                "capability_id": capability,
            }
            response = client.post("/api/inference/assignments/clear", json=body)
            if response.status_code != 200:
                raise RuntimeError(
                    f"real assignment clear route failed: {response.status_code} {response.text}"
                )
            cleared.append({
                "scope": scope, "capability_id": capability,
                "revision": int(response.json().get("revision", 0)),
                "method": "POST", "path": "/api/inference/assignments/clear",
                "body": body,
            })
    return cleared


def _confirm_a2(db: Any, *, due: str) -> dict[str, Any]:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db.plugins.record_artifact(
        artifact_id=PROPOSAL_ARTIFACT_ID,
        meeting_id=MAIN_MEETING_ID,
        artifact_type="action_items",
        title="A2 oracle action extraction",
        structured_json={"action_items": [{
            "task": A2_TASK, "owner": OWNER_IDENTITY,
            "due": "", "source_timestamp": 2.0,
        }]},
        status="accepted",
        plugin_id="action_owner_enforcer",
        plugin_version="fixture",
    )
    with _fixed_producer_entropy():
        bridge = ProposalBridgeService(db)
        proposals = bridge.bridge_meeting_artifacts(MAIN_MEETING_ID)
        a2 = next((row for row in proposals if row.text == A2_TASK), None)
        if a2 is None:
            raise RuntimeError("the real action-item producer did not create the A2 proposal")
        # The proposal has a real due field from its producer.  Supplying
        # today's explicit fixture date is an owner confirmation through the
        # same bridge chain.
        owner = Principal(PrincipalKind.OWNER, OWNER_IDENTITY)
        result = bridge.confirm_proposal(owner, a2.id, due=due)
    if result.get("state") != "confirmed":
        raise RuntimeError(f"the real A2 confirmation failed: {result}")
    return {
        "proposal_id": a2.id,
        "proposal_kind": a2.kind,
        "decision_id": result.get("decision_id"),
        "decision_record_id": result.get("decision_record_id"),
        "action_item_id": result.get("action_item_id"),
        "commitment_id": result.get("commitment_id"),
        "source": "ProposalBridgeService.confirm_proposal",
    }


def _set_mute(db: Any, muted_project_id: str) -> dict[str, Any]:
    from holdspeak.services.heartbeat_service import HeartbeatService

    settings = HeartbeatService(db).update_settings({"muted_projects": [muted_project_id]})
    if muted_project_id not in settings.get("muted_projects", []):
        raise RuntimeError("heartbeat settings did not retain the muted project")
    return settings


def _engine_facts(db: Any) -> dict[str, Any]:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    summary = InferenceAssignmentService(db).assignment_summary(
        Principal(PrincipalKind.OWNER, OWNER_IDENTITY)
    )
    wanted = {"speech.transcribe", "meeting.deferred_analysis"}
    rows = {
        str(row.get("id")): row
        for row in summary.get("task_overrides", [])
        if str(row.get("id")) in wanted
    }
    missing = sorted(cap for cap in wanted if cap not in rows)
    if missing:
        raise RuntimeError(f"assignment producer omitted capabilities: {missing}")
    assigned = [cap for cap, row in rows.items() if row.get("effective", {}).get("status") == "assigned"]
    if assigned:
        raise RuntimeError(f"oracle requires no speech/summary engine assignment: {assigned}")
    return {"summary": summary, "capabilities": rows, "read": "ok"}


def _seed_evidence(
    db: Any,
    now: datetime,
    a2: dict[str, Any],
    settings: dict[str, Any],
    project_ids: dict[str, str],
) -> dict[str, Any]:
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    owner = Principal(PrincipalKind.OWNER, OWNER_IDENTITY)
    project = ProjectService(db)
    return {
        "action_items": [
            _jsonable(asdict(item)) for item in db.meetings.list_action_items(include_completed=True)
            if item.id in {A1_ID, A3_ID, A4_ID, D1_ID, a2.get("action_item_id")}
        ],
        "meeting_projects": {
            MAIN_MEETING_ID: db.projects.get_meeting_projects(MAIN_MEETING_ID),
            MUTED_MEETING_ID: db.projects.get_meeting_projects(MUTED_MEETING_ID),
        },
        "room_commitments": project.room(owner, project_ids["project_id"]).get("commitments"),
        "room_needs_you": project.needs_you(owner),
        "heartbeat": {"muted_projects": settings.get("muted_projects", [])},
        "a2_chain": a2,
        "summary_states": {
            FAILED_MEETING_ID: db.meetings.get_meeting(FAILED_MEETING_ID).intel_status,
            STORED_MEETING_ID: db.meetings.get_meeting(STORED_MEETING_ID).intel_status,
        },
    }


def seed_week(db_path: Path, *, home: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    """Create the oracle week in a fresh or existing empty hub database.

    A live hub has already created its SQLite file before this command runs.
    Opening that file is safe; re-seeding any oracle meeting ID is not.
    """
    path, isolated_home = validate_isolated_db(db_path, home)
    path.parent.mkdir(parents=True, exist_ok=True)
    from holdspeak.db import Database

    clock = now or datetime.now().replace(microsecond=0)
    db = Database(path)
    try:
        existing = [
            meeting_id for meeting_id in sorted(_ORACLE_MEETING_IDS)
            if db.meetings.get_meeting(meeting_id) is not None
        ]
        if existing:
            raise FileExistsError(
                f"oracle meeting IDs already exist: {', '.join(existing)}"
            )
        dates = _seed_meetings_and_projects(db, clock)
        chain = _confirm_a2(db, due=clock.date().isoformat())
        settings = _set_mute(db, dates["muted_project_id"])
        cleared = _clear_existing_assignments(db)

        # Router composition and a fresh Database instance must not resurrect
        # the migrated speech assignment head that an empty hub creates.
        db.close()
        db = Database(path)
        with _route_client(db, clock) as client:
            assignment_response = client.get("/api/inference/assignments")
            if assignment_response.status_code != 200:
                raise RuntimeError(
                    "assignment read after database reopen failed: "
                    f"{assignment_response.status_code} {assignment_response.text}"
                )
            reopened_assignments = assignment_response.json()
        engines = _engine_facts(db)
        evidence = _seed_evidence(db, clock, chain, settings, dates)
        evidence["assignmentClear"] = {
            "cleared": cleared,
            "afterReopen": reopened_assignments,
        }
        ids = {
            "project": dates["project_id"], "mutedProject": dates["muted_project_id"],
            "mainMeeting": MAIN_MEETING_ID, "mutedMeeting": MUTED_MEETING_ID,
            "failedMeeting": FAILED_MEETING_ID, "storedMeeting": STORED_MEETING_ID,
            "A1": A1_ID, "A2": chain["action_item_id"], "A3": A3_ID, "A4": A4_ID,
            "M1": dates["m1_id"], "A1Room": dates["a1_room_item_id"], "D1": D1_ID,
            **{key: value for key, value in chain.items() if key.endswith("_id") or key == "proposal_id"},
        }
        before = _inputs(db, clock)
        wiring = _assert_oracle_inputs(before, ids)
        evidence["oracleWiring"] = wiring
        return {
            "schema": ORACLE_SCHEMA, "mode": "seed", "db": str(path), "home": str(isolated_home),
            "now": clock.isoformat(), "dates": dates, "ids": ids,
            "before": before,
            "mutation": {"method": "PATCH", "path": f"/api/all-action-items/{A1_ID}", "body": {"status": "done"}},
            "expectedRefs": _expected_refs(), "expectedCount": 6, "producerEvidence": evidence,
            "assignments": engines, "heartbeat": settings,
        }
    finally:
        db.close()


def _inputs(db: Any, now: datetime) -> dict[str, Any]:
    from holdspeak.services.heartbeat_service import HeartbeatService

    def read_json(response: Any, label: str) -> dict[str, Any]:
        if response.status_code != 200:
            raise RuntimeError(f"{label} route failed: {response.status_code} {response.text}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError(f"{label} route returned a non-object payload")
        return payload

    with _route_client(db, now) as client:
        door = read_json(client.get("/api/door"), "Door")
        room = read_json(client.get("/api/desk/needs-you?fresh=1"), "needs-you")
        assignments = read_json(
            client.get("/api/inference/assignments"), "assignment"
        )
        meetings_wire = read_json(
            client.get("/api/meetings?limit=500&offset=0"), "meeting"
        )
    heartbeat = HeartbeatService(db).get_settings()
    meeting_rows = meetings_wire.get("meetings", [])
    if not isinstance(meeting_rows, list):
        raise RuntimeError("meeting route did not return a meetings list")
    # ``items`` is the full membership answer (Door cards merged in);
    # ``roomItems`` is the Room rows alone, the browser twin's input.
    room_items = room.get("roomItems", [])
    if not isinstance(room_items, list):
        raise RuntimeError("needs-you route did not return a roomItems list")
    return {
        "now": now.isoformat(),
        "door": door,
        "needsYou": room,
        "roomItems": _jsonable(room_items),
        "roomAggregate": room,
        "assignments": _jsonable(assignments),
        "assignmentRead": "ok",
        "meetings": _jsonable(meeting_rows),
        "meetingsWire": _jsonable(meetings_wire),
        "heartbeat": _jsonable(heartbeat),
        "mutedProjects": list(heartbeat.get("muted_projects", [])),
    }


def _actual_ids(db: Any) -> dict[str, str]:
    """Read the IDs minted by the producer chain from the reopened DB."""
    a2 = next(
        (item for item in db.meetings.list_action_items(include_completed=True)
         if item.task == A2_TASK),
        None,
    )
    if a2 is None:
        raise RuntimeError("real A2 action-item producer did not persist its action")
    main_links = db.projects.get_meeting_projects(MAIN_MEETING_ID)
    muted_links = db.projects.get_meeting_projects(MUTED_MEETING_ID)
    if len(main_links) != 1 or len(muted_links) != 1:
        raise RuntimeError("oracle meeting/project links are not singular")
    project_id = str(main_links[0]["project_id"])
    muted_project_id = str(muted_links[0]["project_id"])
    m1 = next(
        (item for item in db.projects.list_project_items(muted_project_id)
         if item.get("title") == M1_TASK),
        None,
    )
    if m1 is None:
        raise RuntimeError("real M1 project-item producer did not persist its item")
    a1_room = next(
        (item for item in db.projects.list_project_items(project_id)
         if item.get("title") == A1_ROOM_TASK),
        None,
    )
    if a1_room is None:
        raise RuntimeError("real A1 Room milestone producer did not persist its item")
    proposals = db.proposals.list_proposals(meeting_id=MAIN_MEETING_ID, state="confirmed")
    proposal = next((row for row in proposals if row.text == A2_TASK), None)
    if proposal is None or not proposal.decision_record_id or not proposal.commitment_id:
        raise RuntimeError("real A2 proposal bridge chain is incomplete")
    with db._connection() as conn:
        decision_row = conn.execute(
            "SELECT source_id FROM decision_records WHERE id = ?",
            (proposal.decision_record_id,),
        ).fetchone()
    if decision_row is None:
        raise RuntimeError("real A2 decision record has no decision ID")
    return {
        "project": project_id,
        "mutedProject": muted_project_id,
        "mainMeeting": MAIN_MEETING_ID,
        "mutedMeeting": MUTED_MEETING_ID,
        "failedMeeting": FAILED_MEETING_ID,
        "storedMeeting": STORED_MEETING_ID,
        "A1": A1_ID,
        "A2": str(a2.id),
        "A3": A3_ID,
        "A4": A4_ID,
        "M1": str(m1["id"]),
        "A1Room": str(a1_room["id"]),
        "D1": D1_ID,
        "proposal_id": str(proposal.id),
        "decision_id": str(decision_row["source_id"]),
        "decision_record_id": str(proposal.decision_record_id),
        "commitment_id": str(proposal.commitment_id),
        "action_item_id": str(a2.id),
    }


def _assert_oracle_inputs(inputs: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    """Fence the real route payloads before the browser consumes them."""
    board = inputs.get("door", {}).get("board", {})
    cards = [card for lane in ("overdue", "now", "waiting", "unassigned")
             for card in board.get(lane, [])]
    for item_id, lane in ((ids["A1"], "overdue"), (ids["A3"], "waiting"), (ids["A4"], "unassigned")):
        if item_id not in {str(card.get("id")) for card in board.get(lane, [])}:
            raise RuntimeError(f"Door route omitted {item_id} from {lane}")
    a2_cards = [card for card in cards if str(card.get("id")) == ids["A2"]]
    if len(a2_cards) != 1:
        raise RuntimeError(f"Door route emitted {len(a2_cards)} A2 cards")
    room_items = inputs.get("roomItems", [])
    a2_room = [
        row for row in room_items
        if row.get("source") == "commitment" and row.get("ref") == A2_TASK
    ]
    if len(a2_room) != 1:
        raise RuntimeError(f"Room route emitted {len(a2_room)} A2 commitment rows")
    if a2_room[0].get("actionItemId") != ids["A2"]:
        raise RuntimeError("A2 Room actionItemId does not match the Door card ID")
    if any(str(card.get("id")) == ids["D1"] for card in cards):
        raise RuntimeError("Door route emitted the completed D1 action")
    if any(str(row.get("id")) == ids["D1"] for row in room_items):
        raise RuntimeError("Room route emitted the completed D1 action")
    if any(row.get("source") == "item" and row.get("ref") == A1_TASK for row in room_items):
        raise RuntimeError("Room route emitted a title-colliding A1 milestone")
    muted_rows = [row for row in room_items if row.get("ref") == M1_TASK]
    if len(muted_rows) != 1 or muted_rows[0].get("muted") is not True:
        raise RuntimeError("Room route did not mark the muted M1 row")
    meeting_rows = inputs.get("meetings", [])
    failed = [row for row in meeting_rows if str(row.get("id")) == ids["failedMeeting"]]
    if len(failed) != 1 or str(failed[0].get("intel_status") or failed[0].get("intelStatus")).lower() != "failed":
        raise RuntimeError("meeting route did not return the failed F1 summary state")
    return {
        "doorA2Id": str(a2_cards[0].get("id")),
        "roomA2Ref": a2_room[0].get("ref"),
        "roomA2ActionItemId": a2_room[0].get("actionItemId"),
        "completedD1InDoor": False,
        "completedD1InRoom": False,
        "mutedM1Ref": muted_rows[0].get("ref"),
        "failedMeeting": failed[0].get("id"),
    }


def _done_route(db: Any, *, project_id: str, project_item_id: str) -> dict[str, Any]:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.meetings.action_items import build_action_items_router
    from holdspeak.web.routes.projects import build_projects_router

    owner = Principal(PrincipalKind.OWNER, OWNER_IDENTITY)
    app = FastAPI()

    @app.middleware("http")
    async def _owner(request: Request, call_next: Any) -> Any:
        request.state.principal = owner
        return await call_next(request)

    ctx = WebContext(
        get_state=lambda: {}, meeting_service=MeetingService(db),
        project_service=ProjectService(db),
    )
    app.include_router(build_action_items_router(ctx))
    app.include_router(build_projects_router(ctx))
    path = f"/api/all-action-items/{A1_ID}"
    body = {"status": "done"}
    with TestClient(app) as client:
        response = client.patch(path, json=body)
        payload = response.json()
        status = response.status_code
        if status == 200 and payload.get("success"):
            room_response = client.post(
                f"/api/projects/{project_id}/items/{project_item_id}/transition",
                json={"verb": "reached"},
            )
            room_payload = room_response.json()
    if status != 200 or not payload.get("success"):
        raise RuntimeError(f"real A1 done route failed ({status}): {payload}")
    if room_response.status_code != 200 or not room_payload.get("success"):
        raise RuntimeError(
            f"real A1 Room duplicate transition failed ({room_response.status_code}): {room_payload}"
        )
    return {
        "method": "PATCH", "path": path, "body": body, "status": status,
        "response": payload,
        "relatedProducerMutation": {
            "method": "POST",
            "path": f"/api/projects/{project_id}/items/{project_item_id}/transition",
            "body": {"verb": "reached"},
            "status": room_response.status_code,
            "response": room_payload,
        },
    }


def export_week(db_path: Path, *, home: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    """Export real projection inputs before and after the A1 route mutation."""
    path, isolated_home = validate_isolated_db(db_path, home)
    if not path.exists():
        raise FileNotFoundError(f"oracle database does not exist: {path}; run seed first")
    from holdspeak.db import Database

    clock = now or datetime.now().replace(microsecond=0)
    db = Database(path)
    try:
        before = _inputs(db, clock)
        ids = _actual_ids(db)
        _assert_oracle_inputs(before, ids)
        mutation = _done_route(
            db,
            project_id=ids["project"],
            project_item_id=ids["A1Room"],
        )
        after = _inputs(db, clock)
        return {
            "schema": ORACLE_SCHEMA, "mode": "export", "db": str(path), "home": str(isolated_home),
            "before": before, "after": after,
            "expectedRefs": _expected_refs(),
            "expectedBeforeCount": 6, "expectedAfterCount": 5,
            "actualMutation": mutation,
            "mutation": mutation,
            "actualMutationPath": mutation["path"],
            "actualMutationBody": mutation["body"],
            "ids": ids,
        }
    finally:
        db.close()


def dedup_probe(db_path: Path, *, home: Path | None = None, now: datetime | None = None) -> dict[str, Any]:
    """Mint a separate real-producer case with one Door/Room duplicate.

    The canonical week deliberately keeps the A1 Room milestone title
    separate from the A1 Door action.  This probe adds a second real Door
    action with the A2 title, then links its meeting to the canonical project
    through the project meeting route.  The canonical A2 Room commitment
    covers only the original A2 action ID, so the second Door action remains
    as a duplicate projection for the browser's merge.  The six-member oracle
    returned by ``seed`` and ``export`` is unchanged.
    """
    path, isolated_home = validate_isolated_db(db_path, home)
    clock = now or datetime.now().replace(microsecond=0)
    seeded = seed_week(path, home=isolated_home, now=clock)
    from holdspeak.db import Database

    db = Database(path)
    try:
        project_id = str(seeded["ids"]["project"])
        tomorrow = (clock.date() + timedelta(days=1)).isoformat()
        db.meetings.save_meeting(_meeting(
            DEDUP_MEETING_ID,
            "A2 dedup producer meeting",
            clock.replace(hour=11, minute=0, second=0, microsecond=0),
            intel_status="completed",
            summary="A2 duplicate action producer",
            action_items=[_action(
                DEDUP_ACTION_ID,
                A2_TASK,
                owner="Priya",
                due=tomorrow,
                created_at=clock.isoformat(),
            )],
            segments=[(A2_TASK, 1.0)],
        ))
        with _route_client(db, clock) as client:
            response = client.post(
                f"/api/projects/{project_id}/meetings/{DEDUP_MEETING_ID}",
                json={},
            )
            if response.status_code != 200 or not response.json().get("success"):
                raise RuntimeError(
                    f"real dedup-probe project meeting route failed: {response.status_code} {response.text}"
                )
            linked_meeting = response.json()

        inputs = _inputs(db, clock)
        board = inputs.get("door", {}).get("board", {})
        door_cards = [
            card
            for lane in ("overdue", "now", "waiting", "unassigned")
            for card in board.get(lane, [])
        ]
        door_card = next((card for card in door_cards if str(card.get("id")) == DEDUP_ACTION_ID), None)
        room_row = next(
            (
                row for row in inputs.get("roomItems", [])
                if row.get("source") == "commitment"
                and row.get("ref") == A2_TASK
                and row.get("projectId") == project_id
            ),
            None,
        )
        if door_card is None:
            raise RuntimeError("dedup probe Door route omitted the second genuine A2 action")
        if room_row is None:
            raise RuntimeError("dedup probe Room route omitted the canonical A2 commitment")
        if str(door_card.get("text")) != A2_TASK:
            raise RuntimeError("dedup probe Door title does not match the Room title")
        if str(room_row.get("title")) != A2_TASK:
            raise RuntimeError("dedup probe Room title does not match the Door title")
        if str(room_row.get("actionItemId")) == DEDUP_ACTION_ID:
            raise RuntimeError("dedup probe Room commitment unexpectedly covers the duplicate action")
        return {
            "schema": ORACLE_SCHEMA,
            "mode": "dedup-probe",
            "db": str(path),
            "home": str(isolated_home),
            "now": clock.isoformat(),
            "before": inputs,
            # These remain the canonical six-ref oracle.  The probe changes
            # only the producer inputs used by the C4 mutation fence.
            "expectedRefs": seeded["expectedRefs"],
            "expectedCount": seeded["expectedCount"],
            "expectedMutantCount": seeded["expectedCount"] + 1,
            "producerEvidence": {
                "doorRoute": {
                    "path": "/api/door",
                    "id": str(door_card.get("id")),
                    "title": str(door_card.get("text")),
                    "projectId": str(door_card.get("project_id") or ""),
                },
                "roomRoute": {
                    "path": "/api/desk/needs-you?fresh=1",
                    "id": str(room_row.get("id")),
                    "ref": str(room_row.get("ref")),
                    "title": str(room_row.get("title")),
                    "projectId": str(room_row.get("projectId")),
                    "source": str(room_row.get("source")),
                    "actionItemId": str(room_row.get("actionItemId") or ""),
                },
                "linkedMeeting": {
                    "projectId": project_id,
                    "meetingId": DEDUP_MEETING_ID,
                    "actionItemId": DEDUP_ACTION_ID,
                    "title": A2_TASK,
                    "route": f"POST /api/projects/{project_id}/meetings/{DEDUP_MEETING_ID}",
                    "success": bool(linked_meeting.get("success")),
                },
                "duplicateDoorRef": str(door_card.get("id")),
                "duplicateProjectId": project_id,
                "duplicateTitle": A2_TASK,
            },
        }
    finally:
        db.close()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("seed", "export", "dedup-probe"):
        command = sub.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
        command.add_argument("--home", type=Path, default=None,
                             help="isolated HOME; defaults to the HOME environment")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "seed":
            result = seed_week(args.db, home=args.home)
        elif args.mode == "export":
            result = export_week(args.db, home=args.home)
        else:
            result = dedup_probe(args.db, home=args.home)
        print(json.dumps(_jsonable(result), indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"PHILO13_NEEDS_YOU_FIXTURE_BLOCKED {type(exc).__name__}: {exc}", file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "A1_ID", "A2_ID", "A3_ID", "A4_ID", "M1_ID", "D1_ID",
    "FAILED_MEETING_ID", "STORED_MEETING_ID", "PROJECT_ID", "MUTED_PROJECT_ID",
    "dedup_probe", "export_week", "main", "seed_week", "validate_isolated_db",
]
