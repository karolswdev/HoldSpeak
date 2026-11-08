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
