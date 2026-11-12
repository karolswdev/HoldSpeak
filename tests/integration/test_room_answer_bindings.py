"""Room writes use the exact saved object shown by the read, on both doors."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError
from holdspeak.services.preparation_brief_service import PreparationBriefService
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.proposal_bridge_service import ProposalBridgeService
from holdspeak.services.watch_service import WatchService
from tests.integration.test_desk_project_room import _hub
from tests.watch_seed import seed_watch

OWNER = Principal(PrincipalKind.OWNER, "room-bindings")
OPERATIONS = ("confirm", "dismiss", "retire", "accept", "answer", "discard")


@pytest.fixture
def hub(tmp_path, monkeypatch):
    with _hub(tmp_path, monkeypatch) as live:
        yield live


def scenario(hub, operation):
    db = hub.db
    project = ProjectService(db)
    pid = project.create_project(OWNER, {"name": "Room bindings"})["id"]
    if operation in ("confirm", "dismiss"):
        from holdspeak.meeting_session import MeetingState
        from holdspeak.timestamps import utc_now
        db.meetings.save_meeting(MeetingState(id="binding-meeting", title="Planning", started_at=utc_now(), segments=[]))
        proposal = db.proposals.create_proposal(meeting_id="binding-meeting", project_id=pid, kind="decision", text="Read the replica first", source_plugin="decision_capture")
        service = ProposalBridgeService(db)
        read = service.list_project_proposals(pid)[0]
        def write(binding):
            return getattr(service, operation + "_proposal")(OWNER, proposal.id, binding=binding)
        def changed():
            service.edit_proposal(OWNER, proposal.id, text="Read the primary first")
        def saved():
            return db.proposals.get_proposal(proposal.id).state
        return f"/api/proposals/{proposal.id}/{operation}", {}, read, write, changed, saved, "proposed", "confirmed" if operation == "confirm" else "dismissed"
    if operation == "retire":
        watch = seed_watch(db, watch_id="binding-watch", connector_id="gh", query_kind="pull_requests", name="Source", query={"repository": "acme/app"})
        db.automations.update_watch_spec(watch["id"], project_id=pid, state="active")
        service = WatchService(db)
        read = service.get_watch(OWNER, watch["id"])
        def write(binding):
            return service.retire_watch(OWNER, watch["id"], binding=binding)
        def changed():
            service.pause_watch(OWNER, watch["id"])
        def saved():
            return db.automations.get_watch(watch["id"])["state"]
        return f"/api/watches/{watch['id']}/retire", {}, read, write, changed, saved, "active", "retired"
    if operation in ("accept", "answer"):
        delta = db.project_observations
        delta.insert_review(review_id="binding-review", project_id=pid, status="open", opened_at="2026-11-11T12:00:00+00:00")
        delta.insert_proposal(proposal_id="binding-proposal", project_id=pid, review_window_key="binding-review", proposal_kind="review_flag", target_ref="project:" + pid, title="Review this")
        service = ProjectDeltaService(db, None, project_service=project)
        window = service.get_review(OWNER, pid, "binding-review")
        read = window if operation == "accept" else window["proposals"][0]
        def write(binding):
            if operation == "accept":
                return service.accept_review(OWNER, pid, "binding-review", binding=binding)
            return service.decide_proposal(OWNER, pid, "binding-proposal", "accept", review_id="binding-review", binding=binding)
        def changed():
            with db._connection() as conn:
                delta.update_proposal_in_transaction(conn, "binding-proposal", lifecycle="deferred")
        def saved():
            return delta.get_review("binding-review")["status"] if operation == "accept" else delta.get_proposal("binding-proposal")["lifecycle"]
        suffix = "accept" if operation == "accept" else "proposals/binding-proposal/decide"
        return f"/api/projects/{pid}/reviews/binding-review/{suffix}", {} if operation == "accept" else {"verb": "accept"}, read, write, changed, saved, "open", "accepted"
    service = PreparationBriefService(db, project_service=project)
    read = service.prepare(OWNER, pid, "Plan the next review", generator="deterministic")
    def write(binding):
        return service.discard(OWNER, read["id"], binding=binding)
    def changed():
        service.keep(OWNER, read["id"])
    def saved():
        return service.get_brief(OWNER, read["id"])["lifecycle"]
    return f"/api/briefs/{read['id']}/discard", {}, read, write, changed, saved, "draft", "discarded"


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("transport", ("service", "http"))
@pytest.mark.parametrize("case", ("missing", "missing_id", "missing_revision", "stale", "good", "wrong_object"))
def test_answer_requires_the_saved_binding(hub, operation, transport, case):
    path, body, read, write, changed, saved, before, after = scenario(hub, operation)
    binding = read.get("binding")
    if case != "missing":
        assert binding and binding["id"] and binding["revision"]
    if case == "missing":
        binding = None
    elif case == "stale":
        changed()
        before = saved()
    elif case == "missing_id":
        binding = {"revision": binding["revision"]}
    elif case == "missing_revision":
        binding = {"id": binding["id"]}
    elif case == "wrong_object":
        binding = {**binding, "id": "another-object"}
    if transport == "service":
        if case == "good":
            write(binding)
        else:
            with pytest.raises(ConflictError, match="Nothing changed. Read again") as refused:
                write(binding)
            assert refused.value.code == "answer_stale"
    else:
        response = hub.client.post(path, json={**body, **({"binding": binding} if binding else {})})
        assert response.status_code == (200 if case == "good" else 409), response.text
        if case != "good":
            assert "Nothing changed. Read again" in response.text
    assert saved() == (after if case == "good" else before)


@pytest.mark.parametrize("operation", OPERATIONS)
def test_record_binding_refusals(hub, operation):
    """The face replays real reads and HTTP errors, never invented payloads."""
    path, body, read, _, changed, _, _, _ = scenario(hub, operation)
    import re
    match = re.match(r"/api/projects/([^/]+)/", path)
    pid = match[1] if match else read["project_id"]
    gets = {}
    for suffix in ("room", "proposals?state=proposed", "briefs/route", "briefs/manifest", "briefs?lifecycle=kept"):
        url = f"/api/projects/{pid}/{suffix}"
        response = hub.client.get(url)
        assert response.status_code == 200, response.text
        gets[url] = response.json()
    if operation in ("accept", "answer"):
        url = f"/api/projects/{pid}/reviews/binding-review"
        gets[url] = hub.ok("GET", url)
    if operation == "discard":
        gets[f"/api/briefs/{read['id']}"] = {"brief": read}
    missing = hub.client.post(path, json=body)
    changed()
    stale = hub.client.post(path, json={**body, "binding": read["binding"]})
    assert missing.status_code == stale.status_code == 409
    import os
    if os.environ.get("HOLDSPEAK_WIRE_WRITE"):
        target = Path("web/src/features/project-room/__tests__/room-wires") / f"binding-{operation}.json"
        target.write_text(json.dumps({"recordedBy": "tests/integration/test_room_answer_bindings.py::test_record_binding_refusals", "read": read, "gets": gets, "project_id": pid, "path": path, "request": {**body, "binding": read["binding"]}, "missing": missing.json(), "stale": stale.json()}, indent=2) + "\n")


@pytest.mark.parametrize("operation", OPERATIONS)
@pytest.mark.parametrize("case", ("missing", "stale", "good"))
def test_mcp_uses_the_same_saved_binding(hub, operation, case):
    from holdspeak.mcp.tools import dispatch
    path, body, read, _, changed, saved, before, after = scenario(hub, operation)
    binding = read["binding"] if case != "missing" else None
    if case == "stale":
        changed()
        before = saved()
    if operation in ("confirm", "dismiss"):
        name, args = f"proposal.{operation}", {"proposal_id": read["id"]}
    elif operation == "retire":
        name, args = "project.watch.retire", {"watch_id": read["id"]}
    elif operation == "discard":
        name, args = "project.brief.discard", {"brief_id": read["id"]}
    else:
        pid = path.split("/")[3]
        name = "project.accept_review" if operation == "accept" else "project.decide_proposal"
        args = {"project_id": pid, "review_id": "binding-review", **body}
        if operation == "answer":
            args["proposal_id"] = read["id"]
    if binding:
        args["binding"] = binding
    if case == "good":
        dispatch(name, args, OWNER)
    else:
        with pytest.raises(ConflictError, match="Nothing changed. Read again") as refused:
            dispatch(name, args, OWNER)
        assert refused.value.code == "answer_stale"
    assert saved() == (after if case == "good" else before)


@pytest.mark.parametrize("operation", ("confirm", "dismiss"))
def test_proposal_binding_is_checked_again_under_the_write_lock(hub, monkeypatch, operation):
    _, _, read, _, _, saved, _, _ = scenario(hub, operation)
    service = ProposalBridgeService(hub.db)
    original = hub.db.proposals.get_proposal
    once = False

    def edited_after_read(proposal_id):
        nonlocal once
        row = original(proposal_id)
        if not once:
            once = True
            hub.db.proposals.edit_proposal(proposal_id, text="New saved words")
        return row

    monkeypatch.setattr(hub.db.proposals, "get_proposal", edited_after_read)
    with pytest.raises(ConflictError, match="Nothing changed"):
        getattr(service, operation + "_proposal")(OWNER, read["id"], binding=read["binding"])
    assert saved() == "proposed"
    assert original(read["id"]).text == "New saved words"


def test_watch_retirement_still_refuses_an_agent(hub):
    from holdspeak.services.errors import ServiceError
    _, _, read, _, _, saved, before, _ = scenario(hub, "retire")
    agent = Principal(PrincipalKind.AGENT, "room-agent")
    with pytest.raises(ServiceError) as refused:
        WatchService(hub.db).retire_watch(agent, read["id"], binding=read["binding"])
    assert refused.value.code == "owner_principal_required"
    assert saved() == before
