"""The prompt step (2026-11-08): one model call, no repository, a delivered answer.

A Program of one prompt step runs end to end on the real ProgramService and
ProgramRunner over a real database: the engine door runs the call on a fake
engine (the kernel runner at the process edge), the answer is the step's
report, and it is delivered as a project_updates row with its source refs.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.kernel.inference_runner import InvocationOutcome
from holdspeak.services import program_service as programs
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import OWNER, Rig


class _Engine:
    """The kernel runner at the process edge: it answers each call."""

    def __init__(self, output: str = "", outcome: str = "succeeded") -> None:
        self.output, self.outcome = output, outcome
        self.calls: list[Any] = []

    def invoke(self, request: Any, adapter: Any, publish: Any = None) -> InvocationOutcome:
        self.calls.append(request)
        ref = publish({"output": self.output, "model": "fake-model"}) if self.outcome == "succeeded" else ""
        return InvocationOutcome("op-prompt-1", "inv-1", self.outcome, ref, {}, "" if ref else "connection refused")


@pytest.fixture()
def rig(tmp_path, monkeypatch) -> Rig:
    from holdspeak.services import project_update_service

    rig = Rig(tmp_path)
    monkeypatch.setattr(programs, "default_program_service", lambda db=None: rig.service)
    monkeypatch.setattr(project_update_service, "_resolve_for_capability",
                        lambda _broker, job: ("rev-1", "asg-1", "prof-1"))
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-1', 'App')")
    rig.db.notes.upsert(note_id="prompt-note-1", title="Standup", body_markdown="The login page ships Friday.")
    return rig


def _engine(rig: Rig, engine: _Engine) -> None:
    rig.runner._broker = lambda: SimpleNamespace(database=rig.db, inference_runner=engine)


def _make(rig: Rig, **step: Any) -> dict:
    return rig.service.create(OWNER, title="Weekly update", project_id="proj-1", control="yolo", steps=[{
        "title": "Draft the update", "brief": "Write this week's update for the App project.", "kind": "prompt",
        **step}])


def test_a_prompt_step_runs_one_call_and_writes_the_project_update(rig) -> None:
    engine = _Engine("The login page ships Friday.")
    _engine(rig, engine)
    made = _make(rig, deliver="project_updates:proj-1", sources=["note:prompt-note-1"])
    assert rig.service.store.get_program(made["id"])["repo_root"] == ""  # no repository
    assert made["steps"][0]["kind"] == "prompt"

    rig.service.start(OWNER, made["id"])

    program = rig.program(made["id"])
    step = program["steps"][0]
    assert step["state"] == "done", step
    assert program["state"] == "done"
    # One call on the assigned engine, with the brief and the source's text.
    assert len(engine.calls) == 1
    request = engine.calls[0]
    assert request.deployment_revision == "rev-1"
    assert "Write this week's update" in request.payload["user_prompt"]
    assert "The login page ships Friday." in request.payload["user_prompt"]
    # The answer is the step's report; the receipt is on the step.
    assert step["report_text"] == "The login page ships Friday."
    assert [row["line"] for row in step["report"]["claimed"]] == ["The login page ships Friday."]
    assert step["report"]["not_checked"] == []
    raw = rig.service.store.get_step(step["id"])
    assert raw["facts"]["prompt"]["operation_id"] == "op-prompt-1"
    # Delivered once, as the project's update, with the refs it read.
    update_id = raw["facts"]["delivered"]["update_id"]
    update = rig.db.project_updates.get_update(update_id)
    assert update["project_id"] == "proj-1"
    assert "The login page ships Friday." in update["body_md"]
    assert update["generator"] == f"agent:program:{made['id']}"
    assert "note:prompt-note-1" in update["source_manifest_json"]
    assert not step.get("worktree") and not step.get("launch_id")
    assert rig.hand.calls == []  # no agent was handed


def test_a_failed_call_fails_the_step_with_the_engine_words(rig) -> None:
    _engine(rig, _Engine(outcome="failed"))
    made = _make(rig, deliver="inbox")
    rig.service.start(OWNER, made["id"])
    step = rig.program(made["id"])["steps"][0]
    assert step["state"] == "failed"
    assert "connection refused" in (step["last_checkpoint"] or {}).get("line", "")


def test_an_inbox_answer_is_one_note(rig) -> None:
    _engine(rig, _Engine("Three things to read today."))
    made = _make(rig)  # deliver: the Inbox by default
    rig.service.start(OWNER, made["id"])
    raw = rig.service.store.get_step(rig.program(made["id"])["steps"][0]["id"])
    note = rig.db.notes.get(raw["facts"]["delivered"]["note_id"])
    assert note is not None and note.body_markdown.startswith("Three things to read today.")


def test_an_agent_step_still_needs_a_repository(rig) -> None:
    with pytest.raises(ProgramRefused) as caught:
        rig.service.create(OWNER, title="Fix it", steps=[{"title": "Fix", "brief": "Fix the bug."}])
    assert caught.value.code == "repository_required"


# ── Morning prep runs as a Program of one prompt step (PR 2) ──────────


def _morning_prep(rig: Rig):
    from holdspeak.services.workbench_service import WorkbenchService
    from holdspeak.workbench_templates import MORNING_PREP_ID, MORNING_PREP_STARTER, get_starter

    WorkbenchService(rig.db).make_from_starter(OWNER, get_starter(MORNING_PREP_STARTER), workbench_id=MORNING_PREP_ID)
    return rig.db.workbenches.get(MORNING_PREP_ID)


def test_morning_prep_runs_as_a_program_and_today_reads_its_report(rig, monkeypatch) -> None:
    from holdspeak.services import automation_runs
    from holdspeak.services.heartbeat_service import HeartbeatService

    notices: list[tuple] = []
    monkeypatch.setattr(HeartbeatService, "finished_notice", lambda _self, *args: notices.append(args) or {})
    engine = _Engine("## 09:00 Standup\n- Raise: the login page")
    _engine(rig, engine)
    wb = _morning_prep(rig)
    assert automation_runs.runs_as_program(wb)

    ran = automation_runs.run_as_program(rig.db, OWNER, wb, key="schedule:29000000")
    again = automation_runs.run_as_program(rig.db, OWNER, wb, key="schedule:29000000")
    assert again == {**ran, "started": False}  # one Program per due minute

    program = rig.program(ran["program_id"])
    assert program["title"].startswith("Morning prep, ")
    assert program["state"] == "done"
    assert program["automation_id"] == wb.id
    # One answer, then one short lesson call for the automation's next runs.
    answers = [call for call in engine.calls if not call.payload["user_prompt"].startswith("Task: ")]
    assert len(answers) == 1 and len(engine.calls) == 2
    assert "Prepare my day" in answers[0].payload["user_prompt"]
    prepared = automation_runs.prepared_for_today(rig.db, OWNER)
    assert prepared["workbench_id"] == wb.id
    assert prepared["result"]["text"] == "## 09:00 Standup\n- Raise: the login page"
    assert prepared["result"]["program"]["id"] == ran["program_id"]
    assert notices == [(wb.id, "Morning prep", 1)]
    # The automation window lists the run among its results.
    assert automation_runs.results_of(rig.db, wb.id)[0]["item_id"] == program["steps"][0]["id"]
