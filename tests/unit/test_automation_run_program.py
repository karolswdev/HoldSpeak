"""Programs PG14: an automation runs a Program (RECIPE PG14).

The Programs rig (real git, a real database, fakes at the process edge) and
the real WorkbenchService and Programs runner: each run makes one Program
from the template and the automation's Project, starts it, and leaves one
result that links it; a second run while it still runs starts nothing.
"""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from holdspeak.services import program_service as programs
from holdspeak.services.automation_runs import results_of
from holdspeak.services.workbench_service import WorkbenchService
from tests.integration.program_rig import OWNER, Rig


@pytest.fixture()
def rig(tmp_path, monkeypatch) -> Rig:
    rig = Rig(tmp_path)
    monkeypatch.setattr(programs, "default_program_service", lambda db=None: rig.service)
    # The project's repository is the rig's repository.
    rig.service._project_source = lambda _project_id: SimpleNamespace(primary_path=str(rig.repo))
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-1', 'App')")
    return rig


def _automation(rig: Rig, *, template: str, about: list[str] | None = None, instruction: str = "Fix it.",
                **fields):
    made = WorkbenchService(rig.db).create_automation(
        OWNER, name="Nightly fixes",
        sentence={"do": "run_program", "about": ["project:proj-1", *(about or [])], "put_in": "today"},
        instruction=instruction, program_template=template, **fields,
    )
    return rig.db.workbenches.get(made["id"])


def _run(rig: Rig, wb) -> dict:
    return asyncio.run(WorkbenchService(rig.db).run(OWNER, wb.id))


def test_a_run_makes_one_program_per_source_and_a_second_run_while_it_runs_starts_none(rig) -> None:
    for index in range(2):
        rig.db.notes.upsert(note_id=f"pg14-note-{index}", title=f"Bug {index}", body_markdown="It breaks.")
    wb = _automation(rig, template="fast-cycle", about=["note:pg14-note-0", "note:pg14-note-1"],
                     program_control="yolo", program_runs_on=[{"profile": "codex"}], program_may_handoff=True)
    assert wb.do_kind == "run_program" and wb.instruction == "Fix it."

    first = _run(rig, wb)
    assert first["program_started"] is True and first["status"] == "running"
    program = rig.program(first["program_id"])
    assert program["origin_ref"] == f"automation:{wb.id}"
    assert program["place"]["origin"]["title"] == "Nightly fixes"  # "From the automation Nightly fixes"
    assert program["project_id"] == "proj-1" and program["goal"] == "Fix it."
    assert program["control"] == "yolo" and program["default"]["profile"] == "codex-default"
    assert program["may_handoff"] is True and program["state"] in ("running", "waiting")
    assert [(step["title"], step["origin_ref"]) for step in program["steps"]] == [
        ("Bug 0", "note:pg14-note-0"), ("Bug 1", "note:pg14-note-1")]
    assert program["steps"][0]["brief"].startswith("Fix it.")

    second = _run(rig, wb)
    assert second["program_started"] is False and second["skipped"] is True
    assert second["program_id"] == first["program_id"]
    assert "is still running. Nothing started." in second["reason"]
    assert len(rig.service.store.list_programs()) == 1

    # The run's one result links the Program; its window is the Program's.
    [result] = results_of(rig.db, wb.id)
    assert result["status"] == "done" and result["text"].startswith("Started the program Nightly fixes")
    assert result["program"]["id"] == first["program_id"]
    assert result["program"]["window"] == f"pullout:program:{first['program_id']}"
    assert rig.db.workbench_items.list_for_workbench(wb.id) == []
    assert WorkbenchService(rig.db).list_runs(OWNER, wb.id)[0]["id"] == first["program_id"]
    with rig.db._connection() as conn:
        assert conn.execute("SELECT * FROM workbench_runs").fetchall() == []

    # Parked by the owner, it is not running: the next run makes a new one.
    rig.service.park(OWNER, first["program_id"])
    third = _run(rig, wb)
    assert third["program_started"] is True and third["program_id"] != first["program_id"]
    assert len(results_of(rig.db, wb.id)) == 2


def test_with_no_sources_the_instruction_is_the_one_step(rig) -> None:
    wb = _automation(rig, template="build-and-review", instruction="Make the hub stop stalling.\n\nKeep it small.")
    ran = _run(rig, wb)
    program = rig.program(ran["program_id"])
    assert [step["title"] for step in program["steps"]] == ["Make the hub stop stalling."]
    assert program["template"] == "build-and-review" and program["reviewer"]["profile"] == "codex-default"


def test_from_the_desk_takes_the_project_and_its_open_actions(rig) -> None:
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES ('m1', '2026-10-27T10:00:00', 'Sync')")
        conn.execute("INSERT INTO meeting_projects (meeting_id, project_id, confidence) VALUES ('m1', 'proj-1', 0.9)")
        conn.execute("INSERT INTO action_items (id, meeting_id, task, owner, status) "
                     "VALUES ('ai_1', 'm1', 'Fix the login timeout', 'Me', 'open')")
        conn.execute("INSERT INTO action_items (id, meeting_id, task, owner, status) "
                     "VALUES ('ai_2', 'm1', 'Done already', 'Me', 'done')")
    wb = _automation(rig, template="from-the-desk")
    ran = _run(rig, wb)
    program = rig.program(ran["program_id"])
    assert [(step["title"], step["origin_ref"]) for step in program["steps"]] == [
        ("Fix the login timeout", "action:ai_1")]
    assert program["project_id"] == "proj-1" and program["state"] in ("running", "waiting")


def test_a_refusal_is_a_failed_result_in_words(rig) -> None:
    wb = _automation(rig, template="from-the-desk")  # the project has no open action
    from holdspeak.services.errors import ServiceError

    with pytest.raises(ServiceError, match="The project has no open action"):
        _run(rig, wb)
    assert results_of(rig.db, wb.id) == []
    assert rig.service.store.list_programs() == []


def test_the_automation_payload_names_the_template_level_and_agent(rig) -> None:
    wb = _automation(rig, template="overnight", program_runs_on=[{"profile": "claude-default"}])
    payload = WorkbenchService(rig.db).get_workbench(OWNER, wb.id)
    assert payload["do_kind"] == "run_program" and payload["program_template"] == "overnight"
    assert payload["program"]["template_name"] == "Overnight on the home box"
    assert payload["program"]["control_word"] == "YOLO"  # the template's own level
    assert payload["program"]["runs_on_words"] == "Claude Code"
    assert payload["assignment_summary"]["status"] == "assigned"


def test_a_bad_template_or_level_is_refused(rig) -> None:
    from holdspeak.services.errors import ValidationError

    with pytest.raises(ValidationError):
        _automation(rig, template="nightly")
    with pytest.raises(ValidationError):
        _automation(rig, template="race", program_control="reckless")


def test_the_overnight_starter_shows_only_with_an_engine_pi_can_run_on(rig, monkeypatch) -> None:
    from holdspeak.delivery import pi_launch
    from holdspeak.program_templates import HOME_ENGINE_PROFILE
    from holdspeak.workbench_templates import list_templates

    assert "overnight-program" not in {starter["id"] for starter in list_templates(rig.db)}

    home = pi_launch.LibraryEngine(HOME_ENGINE_PROFILE, "qwen on karol", pi_launch.PiEngine(
        endpoint="http://karol:8080/v1", model="qwen3.8-27b", context_window=32768, key_slot="",
        host="karol:8080", boundary="private"))
    monkeypatch.setattr(pi_launch, "library_engine", lambda _db, pid: home if pid == HOME_ENGINE_PROFILE else None)
    rig.service._engines = lambda pid: home if pid == HOME_ENGINE_PROFILE else None
    [starter] = [row for row in list_templates(rig.db) if row["id"] == "overnight-program"]
    assert starter["program_runs_on"] == [{"profile": "pi-default", "engine": HOME_ENGINE_PROFILE}]

    made = WorkbenchService(rig.db).instantiate_template(OWNER, "overnight-program")["workbench"]
    wb = rig.db.workbenches.get(made["id"])
    assert (wb.do_kind, wb.program_template, wb.program_control) == ("run_program", "overnight", "yolo")
    assert wb.schedule == "30 23 * * 1-5" and wb.schedule_enabled is False
    assert wb.program_may_call is False
    assert made["program"]["runs_on_words"].startswith("pi · ")


def test_mcp_automation_create_takes_do_run_program_and_its_fields(rig, monkeypatch) -> None:
    from holdspeak.mcp import tools as mcp_tools

    schema = mcp_tools._WORKBENCH_FIELDS_SCHEMA["properties"]
    assert "run_program" in schema["do_kind"]["enum"]
    assert {"program_template", "program_control", "program_runs_on", "program_may_call",
            "program_may_handoff"} <= set(schema)
    monkeypatch.setattr(mcp_tools, "get_database", lambda: rig.db)
    made = mcp_tools.dispatch("automation.create", {
        "name": "Weekly cleanup", "do": "run_program", "about": ["project:proj-1"],
        "fields": {"instruction": "Tidy the store.", "program_template": "race", "program_control": "normal",
                   "program_runs_on": ["claude"]},
    }, OWNER)
    wb = rig.db.workbenches.get(made["id"])
    assert (wb.do_kind, wb.instruction, wb.program_template, wb.program_control) == (
        "run_program", "Tidy the store.", "race", "normal")
    assert json.loads(wb.program_runs_on_json) == [{"profile": "claude-default", "engine": None}]


def test_done_when_a_schedule_starts_a_from_the_desk_program_on_a_project(rig) -> None:
    """RECIPE PG14 Done when: the owner turns the schedule on (a live
    delegation over the Program terms); the scheduler's tick starts one
    From the desk Program; the same tick again is a duplicate."""
    import asyncio

    from holdspeak.kernel.model import KernelRefused
    from holdspeak.kernel.runtime import _configure
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.schedule_delegation import ScheduleDelegationService

    with rig.db._connection() as conn:
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES ('m1', '2026-10-27T10:00:00', 'Sync')")
        conn.execute("INSERT INTO meeting_projects (meeting_id, project_id, confidence) VALUES ('m1', 'proj-1', 0.9)")
        conn.execute("INSERT INTO action_items (id, meeting_id, task, owner, status) "
                     "VALUES ('ai_1', 'm1', 'Fix the login timeout', 'Me', 'open')")
    service = WorkbenchService(rig.db)
    wb = _automation(rig, template="from-the-desk", program_control="normal")
    service.update_workbench(OWNER, wb.id, schedule="30 23 * * 1-5", schedule_enabled=True)
    delegation = ScheduleDelegationService(rig.db).live(wb.id)
    assert delegation is not None and delegation["deployment_revision_id"] == "program:from-the-desk"

    # A changed level is a changed term: the schedule turns off until he approves it again.
    service.update_workbench(OWNER, wb.id, program_control="yolo")
    assert rig.db.workbenches.get(wb.id).schedule_enabled is False
    service.update_workbench(OWNER, wb.id, schedule_enabled=True)
    delegation = ScheduleDelegationService(rig.db).live(wb.id)

    _configure(rig.db)
    scheduler = Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor")
    ran = asyncio.run(service.run_scheduled(scheduler, wb.id, due_minute=2026103023))
    assert ran["terminal_disposition"] == "succeeded" and ran["program_started"] is True
    program = rig.program(ran["program_id"])
    assert [step["origin_ref"] for step in program["steps"]] == ["action:ai_1"]
    assert program["control"] == "yolo" and program["origin_ref"] == f"automation:{wb.id}"
    with pytest.raises(KernelRefused, match="duplicate_tick"):
        asyncio.run(service.run_scheduled(scheduler, wb.id, due_minute=2026103023))
    assert len(rig.service.store.list_programs()) == 1


@pytest.mark.parametrize("transport", ["face", "mcp"])
def test_agent_hand_runs_on_programs_and_result_history_uses_the_program(rig, monkeypatch, transport):
    from holdspeak.mcp import tools
    from tests.integration.test_desk_workbenches import _client

    monkeypatch.setattr(tools, "get_database", lambda: rig.db)
    rig.db.notes.upsert(note_id="fold-hand", title="Fix the header", body_markdown="Make it clear.")
    service = WorkbenchService(rig.db)
    made = service.create_automation(OWNER, name="Hand the fix", sentence={
        "do": "hand_to_agent", "about": ["project:proj-1", "note:fold-hand"],
        "with": "codex-default", "review_by": "none", "put_in": "today"})
    if transport == "face":
        response = _client(rig.db).post(f"/api/workbenches/{made['id']}/run", json={})
        assert response.status_code == 200, response.text
        run = response.json()["run"]
    else:
        run = tools.dispatch("automation.run", {"workbench_id": made["id"]}, OWNER)
    program = rig.program(run["program_id"])
    assert run["run_id"] == program["id"]
    assert program["default"]["profile"] == "codex-default"
    [step] = program["steps"]
    assert step["origin_ref"] == "note:fold-hand"
    assert rig.hand.calls[0][:2] == ("program_step", step["id"])
    result = service.results(OWNER, made["id"])["results"][0]
    assert result["title"] == "Fix the header"
    assert result["program"]["window"] == f"pullout:program:{program['id']}"
    assert service.list_runs(OWNER, made["id"])[0]["program_id"] == program["id"]
    with rig.db._connection() as conn:
        assert conn.execute("SELECT * FROM workbench_runs").fetchall() == []
        assert conn.execute("SELECT * FROM workbench_items").fetchall() == []
    # A finished/parked Program never re-hands the same source item.
    rig.service.park(OWNER, program["id"])
    again = asyncio.run(service.run(OWNER, made["id"]))
    assert again["started"] is False and again["program_id"] == program["id"]
    assert len(rig.hand.calls) == 1


def test_agent_cannot_use_an_automation_to_start_an_owner_agent(rig):
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError

    wb = _automation(rig, template="fast-cycle")
    with pytest.raises(ServiceError, match="Only the owner"):
        asyncio.run(WorkbenchService(rig.db).run(Principal(PrincipalKind.AGENT, "agent:test"), wb.id))
    assert rig.service.store.list_programs() == []


@pytest.mark.parametrize("transport", ["face", "mcp"])
def test_a_finished_automation_exposes_the_program_report_without_a_second_run_record(rig, monkeypatch, transport):
    from holdspeak.mcp import palettes, tools
    from holdspeak.principals import AgentCredentialStore
    from tests.integration.test_desk_workbenches import _client

    wb = _automation(rig, template="fast-cycle", program_control="yolo")
    monkeypatch.setattr(tools, "get_database", lambda: rig.db)
    if transport == "face":
        response = _client(rig.db).post(f"/api/workbenches/{wb.id}/run", json={})
        assert response.status_code == 200, response.text
        run = response.json()["run"]
    else:
        run = tools.dispatch("automation.run", {"workbench_id": wb.id}, OWNER)
    pid = run["program_id"]
    step = rig.step(pid, 1)
    credentials = AgentCredentialStore()
    credential = credentials.issue(f"agent:launch:{step['launch_id']}", palette=palettes.resolve_palette("CONDUCTOR"),
                                   palette_name="CONDUCTOR", launch_id=step["launch_id"])
    monkeypatch.setattr("holdspeak.principals.agent_credentials", credentials)
    rig.service.step_done(credential.principal, pid, step["id"], "Fixed the header. The focused test passed.")
    rig.agent.finish(step["launch_id"], {"header.py": "clear = True\n"})
    rig.tick(6)
    assert rig.program(pid)["state"] == "done", rig.program(pid)
    service = WorkbenchService(rig.db)
    [result] = service.results(OWNER, wb.id)["results"]
    assert result["text"] == "Fixed the header. The focused test passed."
    assert result["program"]["state"] == "done" and result["program"]["done"] == 1
    # A Program link is not an artifact. Do not offer an artifact send for
    # a step id; its retained note is the readable result document.
    assert result["artifact_id"] is None
    assert rig.db.notes.get(result["note_id"]) is not None
    [history] = service.list_runs(OWNER, wb.id)
    assert history["id"] == pid and history["status"] == "completed" and history["items_completed"] == 1
    with rig.db._connection() as conn:
        assert conn.execute("SELECT * FROM workbench_runs").fetchall() == []


def test_replayed_start_keeps_its_program_after_the_owner_parks_it(rig):
    wb = _automation(rig, template="fast-cycle")
    service = WorkbenchService(rig.db)
    first = asyncio.run(service.run(OWNER, wb.id, request_id="event-1"))
    rig.service.park(OWNER, first["program_id"])
    replay = asyncio.run(service.run(OWNER, wb.id, request_id="event-1"))
    assert replay["program_id"] == first["program_id"] and replay["started"] is False
    assert len(rig.service.store.list_programs()) == 1


def test_concurrent_agent_hand_starts_one_program_and_restart_keeps_the_source_claim(rig):
    from concurrent.futures import ThreadPoolExecutor

    rig.db.notes.upsert(note_id="fold-concurrent", title="Fix the header", body_markdown="Clear it up.")
    service = WorkbenchService(rig.db)
    made = service.create_automation(OWNER, name="One hand", sentence={
        "do": "hand_to_agent", "about": ["project:proj-1", "note:fold-concurrent"],
        "with": "codex-default", "review_by": "none", "put_in": "today"})
    with ThreadPoolExecutor(max_workers=2) as pool:
        answers = list(pool.map(lambda _: asyncio.run(service.run(OWNER, made["id"])), range(2)))
    assert answers[0]["program_id"] == answers[1]["program_id"]
    assert sum(answer["started"] for answer in answers) == 1
    assert len(rig.hand.calls) == 1
    rig.service.park(OWNER, answers[0]["program_id"])
    # A new service has no in-memory source claim to consult.
    replay = asyncio.run(WorkbenchService(rig.db).run(OWNER, made["id"]))
    assert replay["started"] is False and len(rig.hand.calls) == 1


def test_finished_hand_keeps_a_new_readable_result_and_delivers_the_frozen_target_once(rig, monkeypatch):
    from holdspeak.services import automation_runs
    from holdspeak.mcp import palettes
    from holdspeak.principals import AgentCredentialStore
    from holdspeak.services.automation_runs import new_results

    delivered = []
    real_deliver = automation_runs.deliver_text

    def deliver(*args, **kwargs):
        delivered.append(kwargs["key"])
        return real_deliver(*args, **kwargs)

    monkeypatch.setattr(automation_runs, "deliver_text", deliver)
    rig.db.notes.upsert(note_id="fold-delivery", title="Fix the header", body_markdown="Clear it up.")
    service = WorkbenchService(rig.db)
    made = service.create_automation(OWNER, name="One hand", sentence={
        "do": "hand_to_agent", "about": ["project:proj-1", "note:fold-delivery"],
        "with": "codex-default", "review_by": "none", "put_in": "inbox"}, program_control="yolo")
    run = asyncio.run(service.run(OWNER, made["id"]))
    # A later definition edit cannot redirect the work already started.
    service.update_workbench(OWNER, made["id"], output_target="needs_you")
    step = rig.step(run["program_id"], 1)
    credentials = AgentCredentialStore()
    credential = credentials.issue(f"agent:launch:{step['launch_id']}", palette=palettes.resolve_palette("CONDUCTOR"),
                                   palette_name="CONDUCTOR", launch_id=step["launch_id"])
    monkeypatch.setattr("holdspeak.principals.agent_credentials", credentials)
    report = "The header is fixed. The focused test passed."
    rig.service.step_done(credential.principal, run["program_id"], step["id"], report)
    rig.agent.finish(step["launch_id"], {"header.py": "clear = True\n"})
    rig.tick(6)
    assert rig.program(run["program_id"])["state"] == "done"
    [result] = service.results(OWNER, made["id"])["results"]
    assert result["new"] is True and result["text"] == report and result["program_run"] is True
    note = rig.db.notes.get(result["note_id"])
    assert note.body_markdown.startswith(report)
    assert f"workbench:{made['id']}" in note.body_markdown
    assert any(row["workbench_id"] == made["id"] for row in new_results(rig.db))
    service.open_result(OWNER, made["id"], result["artifact_id"])
    assert service.results(OWNER, made["id"])["results"][0]["new"] is False
    rig.tick(2)
    assert delivered == [f"program_step:{step['id']}"]
    with rig.db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM notes WHERE id=?", (result["note_id"],)).fetchone()[0] == 1
        assert conn.execute("SELECT * FROM workbench_runs").fetchall() == []


def test_cancel_refuses_a_program_that_changed_after_the_running_read(rig, monkeypatch):
    from holdspeak.services.program_definitions import ProgramRefused

    wb = _automation(rig, template="fast-cycle")
    service = WorkbenchService(rig.db)
    run = asyncio.run(service.run(OWNER, wb.id))
    original = rig.service.park

    def changed_before_park(principal, program_id, **kwargs):
        rig.service.update(OWNER, program_id, title="Changed while the cancel was in flight")
        return original(principal, program_id, **kwargs)

    monkeypatch.setattr(rig.service, "park", changed_before_park)
    with pytest.raises(ProgramRefused, match="Read it again"):
        service.cancel_latest_run(OWNER, wb.id, run["program_id"])
    assert rig.program(run["program_id"])["state"] in {"running", "waiting"}


def test_a_refused_start_does_not_consume_the_hand_source(rig, monkeypatch):
    from holdspeak.services.program_definitions import ProgramRefused

    rig.db.notes.upsert(note_id="fold-retry", title="Fix the header", body_markdown="Clear it up.")
    service = WorkbenchService(rig.db)
    made = service.create_automation(OWNER, name="Retry the hand", sentence={
        "do": "hand_to_agent", "about": ["project:proj-1", "note:fold-retry"],
        "with": "codex-default", "review_by": "none", "put_in": "today"})
    original = rig.service.start
    monkeypatch.setattr(rig.service, "start", lambda *_a, **_k: (_ for _ in ()).throw(
        ProgramRefused("start_unavailable", "Start is unavailable.")))
    with pytest.raises(ProgramRefused, match="Start is unavailable"):
        asyncio.run(service.run(OWNER, made["id"]))
    assert rig.hand.calls == []
    monkeypatch.setattr(rig.service, "start", original)
    again = asyncio.run(service.run(OWNER, made["id"]))
    assert again["started"] is True and len(rig.hand.calls) == 1


def test_agent_cannot_cancel_an_automations_program(rig):
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError

    wb = _automation(rig, template="fast-cycle")
    service = WorkbenchService(rig.db)
    run = asyncio.run(service.run(OWNER, wb.id))
    with pytest.raises(ServiceError, match="Only the owner"):
        service.cancel_latest_run(Principal(PrincipalKind.AGENT, "agent:test"), wb.id, run["program_id"])
    assert rig.program(run["program_id"])["state"] in {"running", "waiting"}


def test_a_hand_refuses_sources_from_a_different_project_before_making_work(rig):
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.program_definitions import ProgramRefused

    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-other', 'Other app')")
    rig.db.notes.upsert(note_id="fold-other", title="Fix the other app", body_markdown="Clear it up.")
    ProjectService(rig.db).add_resource(OWNER, "proj-other", "note:fold-other")
    service = WorkbenchService(rig.db)
    made = service.create_automation(OWNER, name="Mixed projects", sentence={
        "do": "hand_to_agent", "about": ["project:proj-1", "note:fold-other"],
        "with": "codex-default", "review_by": "none", "put_in": "today"})
    with pytest.raises(ProgramRefused, match="one automation for each project"):
        asyncio.run(service.run(OWNER, made["id"]))
    assert rig.service.store.list_programs() == [] and rig.hand.calls == []
    assert rig.db.workbench_items.list_for_workbench(made["id"]) == []


def _review12a_hand(rig, *, template="overnight", control="", sources=None):
    rig.db.notes.upsert(note_id="review12a-note", title="Review fix", body_markdown="Fix it with a test.")
    made = WorkbenchService(rig.db).create_automation(OWNER, name="Review hand", sentence={
        "do": "hand_to_agent", "about": sources or ["project:proj-1", "note:review12a-note"],
        "with": "codex-default", "review_by": "none", "put_in": "today"},
        program_template=template, program_control=control)
    return rig.db.workbenches.get(made["id"])


@pytest.mark.parametrize("entry", ["face", "mcp", "schedule", "event"])
def test_review12a_hand_on_secure_desk_ignores_overnight_and_waits_for_owner(rig, monkeypatch, entry):
    from holdspeak.config import Config
    from holdspeak.mcp import tools
    from holdspeak.principals import Principal, PrincipalKind
    from tests.integration.test_desk_workbenches import _client

    monkeypatch.setattr(Config, "load", classmethod(lambda cls, path=None: Config(control_mode="safe")))
    monkeypatch.setattr(tools, "get_database", lambda: rig.db)
    wb = _review12a_hand(rig)
    service = WorkbenchService(rig.db)
    if entry == "face":
        response = _client(rig.db).post(f"/api/workbenches/{wb.id}/run", json={})
        assert response.status_code == 200, response.text
        ran = response.json()["run"]
    elif entry == "mcp":
        ran = tools.dispatch("automation.run", {"workbench_id": wb.id}, OWNER)
    elif entry == "schedule":
        service.update_workbench(OWNER, wb.id, schedule="* * * * *", schedule_enabled=True)
        ran = asyncio.run(service.run_scheduled(Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor"),
                                               wb.id, due_minute=2026111201))
    else:
        ran = asyncio.run(service.run(OWNER, wb.id, request_id="review12a-event",
                                     source_event={"event_type": "github.pr.merged"}))
    pid = ran["program_id"]
    program = rig.program(pid)
    assert program["control"] == "secure"
    assert not program["template"]
    step = rig.step(pid, 1)
    from holdspeak.services.control_level import mode_for_launch

    assert mode_for_launch(step["launch_id"], db=rig.db, desk=lambda: "yolo") == "safe"
    rig.agent.finish(step["launch_id"], {"review-fix.py": "fixed = True\n"})
    rig.tick(6)
    assert rig.step(pid, 1)["state"] == "merge_ask"
    assert not any(pr["state"] == "merged" for pr in rig.gh.prs.values())
    if entry == "event":
        replay = asyncio.run(service.run(OWNER, wb.id, request_id="review12a-event",
                                        source_event={"event_type": "github.pr.merged"}))
        assert replay["program_id"] == pid and replay["started"] is False
        assert rig.program(pid)["control"] == "secure"


@pytest.mark.parametrize("desk", ["", "unknown", None])
def test_review12a_unspecified_hand_authority_is_secure(rig, monkeypatch, desk):
    from holdspeak.config import Config

    monkeypatch.setattr(Config, "load", classmethod(lambda cls, path=None: Config(control_mode=desk)))
    wb = _review12a_hand(rig)
    ran = asyncio.run(WorkbenchService(rig.db).run(OWNER, wb.id))
    assert rig.program(ran["program_id"])["control"] == "secure"


@pytest.mark.parametrize("field,value", [("program_template", "overnight"), ("program_control", "yolo")])
@pytest.mark.parametrize("transport", ["mcp", "http"])
@pytest.mark.parametrize("verb", ["create", "update"])
def test_review12a_automation_template_and_control_are_owner_only(rig, monkeypatch, field, value, transport, verb):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from holdspeak.mcp import tools
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import ServiceError
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.workbenches import build_workbenches_router

    agent = Principal(PrincipalKind.AGENT, "agent:review12a")
    service = WorkbenchService(rig.db)
    made = service.create_workbench(agent, name="Agent draft", instruction="Read the notes.")
    monkeypatch.setattr(tools, "get_database", lambda: rig.db)
    if transport == "mcp":
        args = {"name": "Escalation"} if verb == "create" else {"workbench_id": made["id"]}
        with pytest.raises(ServiceError) as refused:
            tools.dispatch(f"automation.{verb}", {**args, "fields": {field: value}}, agent)
        assert refused.value.code == "owner_principal_required"
        assert refused.value.context["status"] == 403
        assert refused.value.detail == "Only the owner can choose the agent, the reviewer or the control level"
    else:
        app = FastAPI()

        @app.middleware("http")
        async def agent_principal(request, call_next):
            request.state.principal = agent
            return await call_next(request)

        app.include_router(build_workbenches_router(WebContext(get_state=lambda: {}, workbench_service=service)))
        client = TestClient(app)
        response = (client.post("/api/workbenches", json={"name": "Escalation", field: value}) if verb == "create"
                    else client.put(f"/api/workbenches/{made['id']}", json={field: value}))
        assert response.status_code == 403, response.text
        assert response.json()["error"] == "Only the owner can choose the agent, the reviewer or the control level"
    stored = rig.db.workbenches.get(made["id"])
    assert stored.program_template == "" and stored.program_control == ""
    assert [wb.id for wb in rig.db.workbenches.list()] == [made["id"]]


@pytest.mark.parametrize("kind", ["hand_to_agent", "run_program", "run", "item"])
@pytest.mark.parametrize("declared_project", [True, False])
def test_review12a_folder_of_another_project_is_refused_before_a_program(rig, tmp_path, kind, declared_project):
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.services.automation_runs import run_as_program
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.project_service import ProjectService
    from tests.integration.program_rig import make_repo

    other = make_repo(tmp_path / "other-repository")
    source, _ = DeliveryRegistry().register(str(other), label="Other project")
    rig.db.notes.upsert(note_id="review12a-note", title="A material", body_markdown="Only for A.")
    ProjectService(rig.db).add_resource(OWNER, "proj-1", "note:review12a-note")
    refs = [*( ["project:proj-1"] if declared_project else []), "note:review12a-note", f"repository:{source.source_id}"]
    made = WorkbenchService(rig.db).create_workbench(OWNER, name="Wrong folder", do_kind="run" if kind == "item" else kind,
        agent_profile="codex-default", review_by="none", instruction="Fix this.", sources=[f"repository:{source.source_id}"] if kind == "item" else refs,
        program_template="fast-cycle" if kind == "run_program" else "")
    with pytest.raises(ServiceError) as refused:
        if kind in {"run", "item"}:
            # Watch/resourceful event starts call this same prompt producer.
            run_as_program(rig.db, OWNER, rig.db.workbenches.get(made["id"]), start=False,
                           sources=(["project:proj-1"] if declared_project else refs) if kind == "item" else None)
        else:
            asyncio.run(WorkbenchService(rig.db).run(OWNER, made["id"]))
    assert refused.value.code == "different_projects"
    assert rig.service.store.list_programs() == [] and rig.hand.calls == []
    assert rig.db.workbench_items.list_for_workbench(made["id"]) == []


@pytest.mark.parametrize("legacy", [{}, {"status": "done"}, {"status": "failed"}, {"status": "queued", "queue_id": "kept-queue"},
                                    {"status": "unknown", "launch_id": "kept-launch"}])
def test_review12a_parked_legacy_claim_is_not_handed_again(rig, legacy):
    from holdspeak.services.automation_runs import hand_item_id
    from holdspeak.services.program_definitions import ProgramRefused

    wb = _review12a_hand(rig, template="")
    ident = hand_item_id(wb.id, "note:review12a-note")
    rig.db.workbench_items.upsert(item_id=ident, workbench_id=wb.id, title="Completed before the fold",
        status="done", context={"occurrence": True, "agent_hand": {"source_ref": "note:review12a-note", **legacy}})
    WorkbenchService(rig.db).park_item(OWNER, wb.id, ident)
    with pytest.raises(ProgramRefused) as refused:
        asyncio.run(WorkbenchService(rig.db).run(OWNER, wb.id))
    assert refused.value.code == "steps_required"
    assert rig.service.store.list_programs() == [] and rig.hand.calls == []
    assert rig.db.workbench_items.get(ident, include_parked=True).parked is True


def test_review12a_hand_explicit_control_never_exceeds_the_desk(rig, monkeypatch):
    from holdspeak.config import Config

    monkeypatch.setattr(Config, "load", classmethod(lambda cls, path=None: Config(control_mode="safe")))
    wb = _review12a_hand(rig, control="yolo")
    ran = asyncio.run(WorkbenchService(rig.db).run(OWNER, wb.id))
    assert rig.program(ran["program_id"])["control"] == "secure"


@pytest.mark.parametrize("kind", ["hand_to_agent", "run_program", "run"])
def test_review12a_matching_project_folder_is_kept(rig, kind):
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.services.automation_runs import run_as_program

    source, _ = DeliveryRegistry().register(str(rig.repo), label="App")
    made = WorkbenchService(rig.db).create_workbench(OWNER, name="Matching folder", do_kind=kind,
        agent_profile="codex-default", review_by="none", instruction="Fix this.",
        sources=["project:proj-1", f"repository:{source.source_id}"],
        program_template="fast-cycle" if kind == "run_program" else "")
    rig.db.notes.upsert(note_id="review12a-match", title="Fix it", body_markdown="Use App.")
    WorkbenchService(rig.db).update_workbench(OWNER, made["id"],
        sources=["project:proj-1", "note:review12a-match", f"repository:{source.source_id}"])
    ran = (run_as_program(rig.db, OWNER, rig.db.workbenches.get(made["id"]), start=False) if kind == "run"
           else asyncio.run(WorkbenchService(rig.db).run(OWNER, made["id"])))
    program = rig.service.store.get_program(ran["program_id"])
    if kind != "run":
        assert program["project_id"] == "proj-1" and program["repo_root"] == str(rig.repo.resolve())
    assert len(rig.service.store.list_programs()) == 1


def test_review12a_prompt_rechecks_folder_before_the_engine(rig, tmp_path, monkeypatch):
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.services import engine_door
    from holdspeak.services.automation_runs import run_as_program
    from tests.integration.program_rig import make_repo
    from tests.integration.test_program_prompt_step import _Engine, _engine

    monkeypatch.setattr(engine_door, "_chain",
        lambda _broker, job, _subject=None: ("asg-1", [engine_door.Engine("rev-1", "asg-1", "prof-1")]))
    engine = _Engine("This material must not reach the wrong folder.")
    _engine(rig, engine)
    registry = DeliveryRegistry()
    good, _ = registry.register(str(rig.repo))
    other, _ = registry.register(str(make_repo(tmp_path / "changed-folder")))
    service = WorkbenchService(rig.db)
    made = service.create_workbench(OWNER, name="Later folder edit", instruction="Read the project.",
        sources=["project:proj-1", f"repository:{good.source_id}"])
    ran = run_as_program(rig.db, OWNER, rig.db.workbenches.get(made["id"]), start=False)
    service.update_workbench(OWNER, made["id"], sources=["project:proj-1", f"repository:{other.source_id}"])
    rig.service.start(OWNER, ran["program_id"])
    [step] = rig.service.store.list_steps(ran["program_id"])
    assert step["state"] == "failed"
    assert step["facts"]["prompt"]["outcome"] == "different_projects"
    assert engine.calls == []
