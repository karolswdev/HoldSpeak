"""Programs PG14: an automation runs a Program (RECIPE PG14).

The Programs rig (real git, a real database, fakes at the process edge) and
the real WorkbenchService and WorkbenchRunner: each run makes one Program
from the template and the automation's Project, starts it, and leaves one
result that links it; a second run while it still runs starts nothing.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from holdspeak.services import program_service as programs
from holdspeak.services.automation_runs import results_of
from holdspeak.services.workbench_runner import WorkbenchRunner
from holdspeak.services.workbench_service import WorkbenchService
from tests.integration.program_rig import OWNER, Rig


class _Stager:
    def register(self, *_args):
        return None


class _Broker:
    projection_stager = _Stager()


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
    return WorkbenchRunner(rig.db, _Broker())._run_program(OWNER, rig.db.workbenches.get(wb.id))


def test_a_run_makes_one_program_per_source_and_a_second_run_while_it_runs_starts_none(rig) -> None:
    for index in range(2):
        rig.db.notes.upsert(note_id=f"pg14-note-{index}", title=f"Bug {index}", body_markdown="It breaks.")
    wb = _automation(rig, template="fast-cycle", about=["note:pg14-note-0", "note:pg14-note-1"],
                     program_control="yolo", program_runs_on=[{"profile": "codex"}], program_may_handoff=True)
    assert wb.do_kind == "run_program" and wb.instruction == "Fix it."

    first = _run(rig, wb)
    assert first["program_started"] is True and first["status"] == "completed"
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
    item = rig.db.workbench_items.get(result["item_id"], include_parked=True)
    assert json.loads(item.context_json)["run_id"] == first["run_id"]

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
    ran = _run(rig, wb)
    assert ran["status"] == "failed" and ran["program_started"] is False
    assert ran["error"] == "The project has no open action. Nothing started."
    [result] = results_of(rig.db, wb.id)
    assert result["status"] == "failed" and result["error"] == "The project has no open action. Nothing started."
    assert "program" not in result and rig.service.store.list_programs() == []


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

    runner = WorkbenchRunner(rig.db, _configure(rig.db))
    scheduler = Principal(PrincipalKind.SCHEDULER, "local-workbench-conductor")
    tick = dict(delegation=delegation, due_minute=2026103023, request_id=f"schedule:{wb.id}:2026103023")
    ran = asyncio.run(runner.run(scheduler, wb.id, **tick))
    assert ran["terminal_disposition"] == "succeeded" and ran["program_started"] is True
    program = rig.program(ran["program_id"])
    assert [step["origin_ref"] for step in program["steps"]] == ["action:ai_1"]
    assert program["control"] == "yolo" and program["origin_ref"] == f"automation:{wb.id}"
    with pytest.raises(KernelRefused, match="duplicate_tick"):
        asyncio.run(runner.run(scheduler, wb.id, **tick))
    assert len(rig.service.store.list_programs()) == 1
