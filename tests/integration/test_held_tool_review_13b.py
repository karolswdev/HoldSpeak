"""The seven review findings: scope, bounded facts and the actual frozen target."""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from holdspeak import operations
from holdspeak.mcp import tools
from holdspeak.principals import Principal, PrincipalKind, agent_credentials
from holdspeak.services.errors import ServiceError
from holdspeak.services.held_tool_details import held_call_details
from holdspeak.services.thread_tools import ThreadToolExecutor, ToolCallHandle
from tests.unit.test_desk_ask_ai import hub  # noqa: F401

OWNER = Principal(PrincipalKind.OWNER, "review-owner")


def handle(name, args, caller=OWNER):
    return ToolCallHandle("review-held", "review-thread", "review-turn", name, deepcopy(args),
                          "effect_proposal", False, "awaiting_decision", principal=caller)


def meeting(db, identity, title):
    from holdspeak.meeting_session import MeetingState
    state = MeetingState(id=identity, title=title, started_at=datetime.now(timezone.utc))
    db.meetings.save_meeting(state)
    return state


def test_p1_caller_names_take_the_same_project_scope_and_owner_binding(hub, monkeypatch):
    from holdspeak.services.project_service import ProjectService
    from holdspeak.mcp.server import handle_message_for_principal
    project = ProjectService(hub.db).create_project(OWNER, {"name": "Project A"})
    meeting(hub.db, "meeting-a", "Project A planning")
    meeting(hub.db, "meeting-b", "Project B private plan")
    credential = agent_credentials.issue("agent:run:review-scope", palette_name="CONDUCTOR",
                                         launch_id="review-scope", project_id=project["id"])
    try:
        caller = credential.principal
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "meeting.get", "arguments": {"meeting_id": "meeting-b"}}}
        ordinary = handle_message_for_principal(request, caller)
        assert ordinary["result"]["isError"]
        held = handle("meeting.delete", {"meeting_id": "meeting-b"}, caller)
        owner = held_call_details(held, OWNER)
        own_copy = held_call_details(held, caller)
        assert {"label": "Meeting", "value": "Project B private plan"} in owner["facts"]
        assert {"label": "Meeting", "value": "hidden (secret)"} in own_copy["facts"]
        assert "Project B private plan" not in json.dumps(own_copy)
        assert own_copy["binding"] == owner["binding"]
    finally:
        agent_credentials.revoke(caller.identity)


def test_p1_caller_palette_and_response_filter_apply_to_names(hub, monkeypatch):
    from holdspeak.mcp import server
    from holdspeak.services import project_update_policy as policy
    meeting(hub.db, "meeting-filter", "Private title")
    credential = agent_credentials.issue("review-filter", palette=frozenset({"meeting.get"}))
    held = handle("meeting.delete", {"meeting_id": "meeting-filter"}, credential.principal)
    try:
        assert held_call_details(held, credential.principal)["facts"][0]["value"] == "Private title"
        # Use the normal response-filter hook after a scoped read. The lookup
        # must consume its filtered response, not the dispatcher's raw value.
        monkeypatch.setattr(policy, "project_update_scope", lambda p: "a" if p == credential.principal else "")
        monkeypatch.setattr(policy, "project_update_palette", lambda p, palette: palette)
        monkeypatch.setattr(policy, "prepare_project_update_call", lambda p, n, a, project: (a, {"private"}, None))
        def cut(response, *args, **kwargs):
            response["result"]["content"][0]["text"] = json.dumps({"withheld": True})
            return response
        monkeypatch.setattr(policy, "filter_response", cut)
        assert held_call_details(held, credential.principal)["facts"][0]["value"] == "hidden (secret)"
        # An empty palette is restrictive too.
        monkeypatch.setattr(agent_credentials, "for_principal", lambda p: SimpleNamespace(palette=frozenset(), palette_name="ALL"))
        assert held_call_details(held, credential.principal)["facts"][0]["value"] == "hidden (secret)"
    finally:
        agent_credentials.revoke(credential.principal.identity)


@pytest.mark.parametrize("name", ["desk.create", "desk.update"])
def test_p1_bodies_are_lengths_never_body_facts(hub, name):
    args = {"kind": "notes", "data": {"title": "Private note", "body_markdown": "API_KEY=private-value " * 240}}
    if name == "desk.update":
        from holdspeak.services.primitive_service import PrimitiveService
        args["id"] = PrimitiveService(hub.db).create_note(OWNER, title="Private note")["id"]
    details = held_call_details(handle(name, args), OWNER)
    assert {"label": "Text", "value": "240 words"} in details["facts"]
    assert "API_KEY" not in json.dumps(details)
    assert any(f["value"] == "Private note" for f in details["facts"])


def test_p1_every_declaration_is_short_and_hidden_parents_suppress_children(hub, monkeypatch):
    from holdspeak.held_arguments import hidden
    declared = [tool for tool in tools.TOOLS if "x-held-arguments" in tool["inputSchema"]]
    for tool in declared:
        schema = {key: value for key, value in tool["inputSchema"].items() if key != "x-held-target"}
        monkeypatch.setitem(tool, "inputSchema", schema)
        args = {}
        for fact in schema["x-held-arguments"]:
            keys = fact["key"] if isinstance(fact["key"], list) else [fact["key"]]
            for key in keys:
                seat = args
                pieces = key.split(".")
                for piece in pieces[:-1]:
                    if not isinstance(seat.get(piece), dict):
                        seat[piece] = {}
                    seat = seat[piece]
                seat.setdefault(pieces[-1], "private-body " * 500)
        facts = held_call_details(handle(tool["name"], args), OWNER)["facts"]
        assert all(len(f["value"]) <= 160 for f in facts), tool["name"]
    tool = next(t for t in tools.TOOLS if t["name"] == "desk.create")
    monkeypatch.setitem(tool, "inputSchema", {**tool["inputSchema"], "x-held-arguments": [
        *tool["inputSchema"]["x-held-arguments"], hidden("data", "Private fields")]})
    facts = held_call_details(handle("desk.create", {"kind": "notes", "data": {
        "title": "child-must-not-leave", "body_markdown": "body-must-not-leave"}}), OWNER)["facts"]
    assert "child-must-not-leave" not in json.dumps(facts)
    assert not any(f["label"] in {"Title", "Text"} for f in facts)


def test_p1_start_describes_and_starts_the_startable_match_and_freezes_it(tmp_path, monkeypatch):
    from tests.integration.program_rig import Rig, FAKE_CHECK
    from holdspeak.program_operations import PROGRAM_OPERATIONS
    rig = Rig(tmp_path)
    service = rig.service
    running = service.create(OWNER, title="Overnight running", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")["id"]
    draft = service.create(OWNER, title="Overnight draft", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")["id"]
    service.plan(OWNER, running, steps=[{"title": "First"}])
    service.plan(OWNER, draft, steps=[{"title": "Second"}])
    service.start(OWNER, running)
    row = service.store.get_program(running)
    row["updated_at"] = "2099-01-01T00:00:00+00:00"
    service.store.save_program(row)
    registry = operations.bind({"program_service": service}, PROGRAM_OPERATIONS)
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    held = handle("program.start", {"name": "overnight"})
    facts = held_call_details(held, OWNER)
    assert {"label": "Program", "value": "Overnight draft"} in facts["facts"]
    assert held.args["program_id"] == draft
    # A newer matching object must not steal an already-read start.
    service.create(OWNER, title="Overnight newer", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")
    executor = ThreadToolExecutor(rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    outcome = executor.execute(held)
    assert outcome.payload["id"] == draft
    assert service.get(OWNER, draft)["state"] == "running"
    with rig.db._connection() as conn:
        conn.execute("DELETE FROM programs WHERE id=?", (draft,))
    service.create(OWNER, title=draft, repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")
    with pytest.raises(ServiceError):
        registry.invoke(OWNER, "program.start", {"program_id": draft})


def test_p1_stop_names_active_capture_and_refuses_another_id_or_a_changed_capture(hub, monkeypatch):
    from holdspeak.services.meeting_service import MeetingService
    service = MeetingService(hub.db)
    meeting(hub.db, "capture-a", "Planning A")
    meeting(hub.db, "capture-b", "Planning B")
    active = {"id": "capture-b", "title": "Planning B", "meeting_active": True}
    stopped = []
    service.bind_lifecycle(on_stop=lambda **args: stopped.append(args))
    service._capture_state = lambda: dict(active)
    registry = operations.bind({"meeting_service": service}, (operations.MEETING_READ,))
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    with pytest.raises(ServiceError):
        service.stop_capture(OWNER, meeting_id="capture-a")
    assert stopped == []
    held = handle("meeting.stop_capture", {})
    details = held_call_details(held, OWNER)
    assert details["facts"] == [{"label": "Meeting", "value": "Planning B"}]
    assert held.args["meeting_id"] == "capture-b"
    active["title"] = "Renamed planning B"
    renamed = held_call_details(held, OWNER)
    assert renamed["facts"] == [{"label": "Meeting", "value": "Renamed planning B"}]
    assert renamed["binding"] != details["binding"]
    active.update(id="capture-a", title="Planning A")
    with pytest.raises(ServiceError):
        service.stop_capture(OWNER, **held.args)
    assert stopped == []
    active.update(id="capture-b", title="Planning B")
    service.stop_capture(OWNER, **held.args)
    assert stopped == [{"meeting_id": "capture-b"}]


def test_p2_mixed_send_is_refused_by_operation_and_by_details(hub, monkeypatch):
    from holdspeak.channel_operations import CHANNEL_OPERATIONS
    from holdspeak.services.channel_service import ChannelService
    registry = operations.bind({"channel_service": ChannelService(hub.db)}, CHANNEL_OPERATIONS)
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    args = {"send_id": "prepared-a", "document_ref": "note:b", "destination_id": "destination-b", "preview_digest": "b"}
    with pytest.raises(operations.OperationRefused) as refused:
        registry.invoke(OWNER, "channel.send", args)
    assert refused.value.code == "invalid_arguments"
    with pytest.raises(ServiceError):
        held_call_details(handle("channel.send", args), OWNER)


def test_p2_start_does_not_claim_a_title_the_capture_controller_ignores(hub):
    from holdspeak.services.meeting_service import MeetingService
    service = MeetingService(hub.db)
    starts = []
    def start(**kwargs):
        starts.append(kwargs)
        return {"id": "automatic-meeting", "title": "Automatic title"}
    service.bind_lifecycle(on_start=start)
    args = {"config": {"title": "Planning"}}
    assert "Planning" not in json.dumps(held_call_details(handle("meeting.start_capture", args), OWNER))
    service.start_capture(OWNER, **args)
    assert "title" not in starts[0]


def test_p2_argument_dependent_writes_are_in_the_strongest_effect_census():
    from tests.integration.test_held_tool_fact_declarations import held_capable_tools
    assert "monday_brief.get" in held_capable_tools()
    # Derive other conditional-effect candidates from the live schema tree.
    for tool in tools.TOOLS:
        if set(tool["inputSchema"].get("properties", {})) & {"generate", "refresh", "force", "create_if", "fresh"}:
            from holdspeak.services.thread_tools import _ALL_TOOL_CLASSES, EXCLUDED_TOOLS
            assert (tool["name"] in held_capable_tools() or (
                tool["name"] in EXCLUDED_TOOLS and _ALL_TOOL_CLASSES[tool["name"]][0] == "effect_proposal")), tool["name"]


def test_program_shape_uses_its_read_target_when_a_new_match_appears(tmp_path, monkeypatch):
    from tests.integration.program_rig import Rig, FAKE_CHECK
    from holdspeak.program_operations import PROGRAM_OPERATIONS
    rig = Rig(tmp_path)
    service = rig.service
    first = service.create(OWNER, title="Night planning", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")["id"]
    service.create(OWNER, title="Night planning too", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")
    row = service.store.get_program(first)
    row["updated_at"] = "2099-01-01T00:00:00+00:00"
    service.store.save_program(row)
    registry = operations.bind({"program_service": service}, PROGRAM_OPERATIONS)
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    held = handle("program.shape", {"name": "Night", "sentence": "Make the check smaller"})
    details = held_call_details(held, OWNER)
    assert {"label": "Program", "value": "Night planning"} in details["facts"]
    assert held.args["program_id"] == first
    # Remove the original match's name after it was described. The service
    # still receives that original id; the planning adapter is the only fake.
    service.update(OWNER, first, title="Renamed planning")
    shaped = []
    monkeypatch.setattr(service, "shape", lambda p, pid, sentence, **kw: shaped.append(pid) or {"id": pid})
    executor = ThreadToolExecutor(rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    assert executor.execute(held).payload["id"] == first
    assert shaped == [first]


@pytest.mark.parametrize("tool", [t for t in tools.TOOLS if "x-held-arguments" in t["inputSchema"]],
                         ids=lambda t: t["name"])
def test_every_declared_tool_executes_its_approved_payload_not_a_second_object(hub, tmp_path, monkeypatch, tool):
    """Conformance at the dispatch port for every declaration, including new ones.

    Domain selector behavior is proved separately with the real Program and
    capture services above. Here two matching operands prove that the common
    executor hands the write port the exact object/payload the facts bound.
    """
    from holdspeak.program_operations import PROGRAM_OPERATIONS
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.services.program_service import default_program_service
    from holdspeak.services.channel_service import ChannelService
    from holdspeak.channel_operations import CHANNEL_OPERATIONS
    from tests.integration.program_rig import make_repo, FAKE_CHECK
    program_service = default_program_service(hub.db)
    repo = make_repo(tmp_path / "repo")
    program_service.create(OWNER, title="Matching A", repository=str(repo), check_command=f"sh {FAKE_CHECK}")
    selected = program_service.create(OWNER, title="Matching B", repository=str(repo), check_command=f"sh {FAKE_CHECK}")["id"]
    capture = MeetingService(hub.db)
    capture.bind_lifecycle(get_state=lambda: {"id": "B", "title": "Matching B", "meeting_active": True})
    registry = operations.bind({"program_service": program_service, "meeting_service": capture,
                                "channel_service": ChannelService(hub.db)},
                               (*PROGRAM_OPERATIONS, operations.MEETING_READ, *CHANNEL_OPERATIONS))
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    args = {}
    for key, prop in tool["inputSchema"].get("properties", {}).items():
        if key not in tool["inputSchema"].get("required", []) and key not in {"program_id", "meeting_id"}:
            continue
        if prop.get("enum"):
            args[key] = next(value for value in prop["enum"] if value is not None)
        elif prop.get("type") == "object":
            args[key] = {"title": "Matching B"}
        else:
            args[key] = "B"
    if tool["name"] == "channel.send":
        args = {"send_id": "B"}
    if tool["name"].startswith("program."):
        args["program_id"] = selected
    if tool["name"].startswith("desk."):
        args["kind"] = "notes"
    held = handle(tool["name"], args)
    details = held_call_details(held, OWNER)
    approved = deepcopy(held.args)
    assert details["binding"]["revision"]
    acted = []
    executor = ThreadToolExecutor(hub.db, principal=OWNER,
                                  dispatch_fn=lambda name, args, p: acted.append((name, deepcopy(args))) or {"ok": True},
                                  control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    # A later reply carrying another matching object's fields cannot replace
    # the approved operand, including a no-selector create's approved payload.
    held.args = {key: "Matching A" for key in approved}
    executor.execute(held)
    assert acted == [(tool["name"], approved)]


def test_a_missing_program_selector_stays_a_refusal_if_a_match_appears(tmp_path, monkeypatch):
    from tests.integration.program_rig import Rig, FAKE_CHECK
    from holdspeak.program_operations import PROGRAM_OPERATIONS
    rig = Rig(tmp_path)
    registry = operations.bind({"program_service": rig.service}, PROGRAM_OPERATIONS)
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    held = handle("program.start", {"name": "Garden"})
    held_call_details(held, OWNER)
    executor = ThreadToolExecutor(rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    newer = rig.service.create(OWNER, title="Garden", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")["id"]
    rig.service.plan(OWNER, newer, steps=[{"title": "Do the job"}])
    outcome = executor.execute(held)
    assert outcome.payload.get("code") == "program_not_found"
    assert rig.service.get(OWNER, newer)["state"] == "drafting"


def test_an_argument_dependent_write_cannot_be_a_name_lookup(hub, monkeypatch):
    from holdspeak.held_arguments import named
    tool = next(t for t in tools.TOOLS if t["name"] == "desk.delete")
    monkeypatch.setitem(tool, "inputSchema", {**tool["inputSchema"], "x-held-arguments": [
        named("id", "Object", "monday_brief.get", {"generate": "=true"}, "title")]})
    writes = []
    monkeypatch.setattr(tools, "dispatch", lambda *args: writes.append(args) or {"title": "must-not-run"})
    details = held_call_details(handle("desk.delete", {"kind": "notes", "id": "B"}), OWNER)
    assert writes == []
    assert {"label": "Object", "value": "hidden (secret)"} in details["facts"]


def test_calls_freezes_the_missing_target_before_its_noop_answer(hub, tmp_path, monkeypatch):
    from holdspeak.calls.service import DeskTurns
    from holdspeak.services.program_service import default_program_service
    from tests.integration.program_rig import make_repo, FAKE_CHECK
    service = default_program_service(hub.db)
    held = handle("program.start", {"name": "Garden"})
    turns = DeskTurns(hub.db, lambda **kw: None)
    monkeypatch.setattr(turns, "_handle", lambda _: held)
    assert turns.nothing_to_ask(held.call_id, held.name)
    repo = make_repo(tmp_path / "repo")
    service.create(OWNER, title="Garden", repository=str(repo), check_command=f"sh {FAKE_CHECK}")
    details = held_call_details(held, OWNER)
    assert details["facts"] == [{"label": "Program", "value": "not available"}]
    executor = ThreadToolExecutor(hub.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    assert executor.execute(held).payload.get("code") == "program_not_found"


def test_capture_identity_is_checked_under_the_runtime_stop_lock(hub, monkeypatch):
    import threading
    from holdspeak.runtime.meeting_glue import MeetingGlueMixin
    from holdspeak.runtime import meeting_glue
    from holdspeak.services.meeting_service import MeetingService
    class Runtime(MeetingGlueMixin):
        pass
    runtime = Runtime()
    runtime.meeting_lock = threading.Lock()
    runtime.meeting_session = SimpleNamespace(is_active=True, state=SimpleNamespace(id="A"))
    finished = []
    monkeypatch.setattr(meeting_glue, "finish_meeting_stop", lambda *a, **kw: finished.append(a) or {"status": "stopped"})
    service = MeetingService(hub.db)
    # Simulate a stale state read: the controller already owns A, while the
    # service's last state and the approved target still name B.
    service.bind_lifecycle(on_stop=runtime._on_meeting_stop)
    service._capture_state = lambda: {"id": "B", "meeting_active": True}
    with pytest.raises(ServiceError) as refused:
        service.stop_capture(OWNER, "B")
    assert refused.value.code == "capture_target_changed"
    assert finished == []
    assert not getattr(runtime, "_meeting_stop_in_progress", False)


@pytest.mark.parametrize("kind", tools.PRIMITIVE_KINDS)
def test_desk_save_names_the_existing_typed_id_and_changes_only_that_object(hub, kind):
    from holdspeak.services.primitive_service import PrimitiveService
    service = PrimitiveService(hub.db)
    singular = tools._KIND_ALIASES[kind]
    field = "title" if singular in {"note", "decision"} else "name"
    create, get = getattr(service, "create_" + singular), getattr(service, "get_" + singular)
    create(OWNER, **{singular + "_id": "A", field: "Matching A"})
    create(OWNER, **{singular + "_id": "B", field: "Matching B"})
    held = handle("desk.create", {"kind": kind, "data": {singular + "_id": "B", field: "Saved B"}})
    details = held_call_details(held, OWNER)
    assert {"label": "Object", "value": "Matching B"} in details["facts"]
    executor = ThreadToolExecutor(hub.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    held.args["data"][singular + "_id"] = "A"
    outcome = executor.execute(held)
    assert outcome.kind != "tool_execution_failed", outcome.payload
    after_b, after_a = get(OWNER, "B"), get(OWNER, "A")
    assert after_b.get("directory", after_b)[field] == "Saved B"
    assert after_a.get("directory", after_a)[field] == "Matching A"


def test_the_task_facts_and_completion_use_the_same_card_among_two_matches(hub):
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService
    door = DoorService(FollowThroughService(hub.db), RefinementThoughtService(hub.db),
                       hub.db.scheduled_recordings, hub.db.calendar_events, db=hub.db)
    a = door.add_item(OWNER, "Matching task A")
    b = door.add_item(OWNER, "Matching task B")
    held = handle("follow_through.complete", {"card_id": b["id"], "verb": "done"})
    assert {"label": "Task", "value": "Matching task B"} in held_call_details(held, OWNER)["facts"]
    executor = ThreadToolExecutor(hub.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    held.args["card_id"] = a["id"]
    assert executor.execute(held).kind != "tool_execution_failed"
    with hub.db._connection() as conn:
        states = {r["id"]: r["status"] for r in conn.execute("SELECT id, status FROM action_items")}
    assert states[b["id"]] == "done" and states[a["id"]] == "open"


def test_calls_pins_the_program_before_a_preview_can_change_the_name_roster(hub, tmp_path, monkeypatch):
    from holdspeak.calls.service import DeskTurns
    from holdspeak.services.program_service import default_program_service
    from holdspeak.services import program_spoken
    from tests.integration.program_rig import make_repo, FAKE_CHECK
    service = default_program_service(hub.db)
    repo = make_repo(tmp_path / "repo")
    service.create(OWNER, title="Night A", repository=str(repo), check_command=f"sh {FAKE_CHECK}")
    service.create(OWNER, title="Night B", repository=str(repo), check_command=f"sh {FAKE_CHECK}")
    held = handle("program.shape", {"name": "Night", "sentence": "Change the check"})
    chosen = []
    def preview(target, principal, args):
        found = target.find(principal, program_id=args.get("program_id"), name=args.get("name"))
        chosen.append(found)
        service.create(OWNER, title="Night new match", repository=str(repo), check_command=f"sh {FAKE_CHECK}")
        return {"state": "asked", "program_id": found["id"], "title": found["title"], "question": "Apply?"}
    monkeypatch.setattr(program_spoken, "prepare", preview)
    turns = DeskTurns(hub.db, lambda **kw: None)
    monkeypatch.setattr(turns, "_handle", lambda _: held)
    assert not turns.nothing_to_ask(held.call_id, held.name)
    details = held_call_details(held, OWNER)
    assert held.args["program_id"] == chosen[0]["id"]
    assert {"label": "Program", "value": chosen[0]["title"]} in details["facts"]


def test_archived_reads_work_when_the_live_state_callback_has_no_state(hub):
    from holdspeak.services.meeting_service import MeetingService
    meeting(hub.db, "archive-only", "Stored meeting")
    service = MeetingService(hub.db)
    service.bind_lifecycle(get_state=lambda: None)
    assert service.get_meeting(OWNER, "archive-only")["title"] == "Stored meeting"


def test_a_named_start_of_a_running_program_keeps_its_noop_reply(tmp_path, monkeypatch):
    from tests.integration.program_rig import Rig, FAKE_CHECK
    from holdspeak.program_operations import PROGRAM_OPERATIONS
    rig = Rig(tmp_path)
    selected = rig.service.create(OWNER, title="Night running", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}")["id"]
    rig.service.plan(OWNER, selected, steps=[{"title": "First"}])
    rig.service.start(OWNER, selected)
    registry = operations.bind({"program_service": rig.service}, PROGRAM_OPERATIONS)
    monkeypatch.setattr(tools, "runtime_registry", lambda *a: registry)
    held = handle("program.start", {"name": "Night"})
    held_call_details(held, OWNER)
    assert held.args["program_id"] == selected
    executor = ThreadToolExecutor(rig.db, principal=OWNER, dispatch_fn=tools.dispatch, control_mode_fn=lambda: "safe")
    executor.decide(held, "approve")
    outcome = executor.execute(held)
    assert outcome.payload.get("started") is False, outcome.payload
    assert "runs" in outcome.payload["spoken"]


def test_a_bound_stop_refuses_a_controller_that_cannot_take_the_identity(hub):
    from holdspeak.services.meeting_service import MeetingService
    service = MeetingService(hub.db)
    stopped = []
    service.bind_lifecycle(on_stop=lambda: stopped.append("unbound"),
                           get_state=lambda: {"id": "B", "meeting_active": True})
    with pytest.raises(ServiceError) as refused:
        service.stop_capture(OWNER, "B")
    assert refused.value.code == "capture_binding_unavailable"
    assert stopped == []
